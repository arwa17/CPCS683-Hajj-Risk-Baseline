#!/usr/bin/env python3
"""Offline M6 analysis from saved M5 model traces; no Gemini API calls."""
import csv
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M5 = ROOT / "m5"
sys.path.insert(0, str(M5))
from scoring import analyze, paired_comparison, load_gold, read_jsonl

def main():
    manifest = json.loads((M5 / "m5_data/manifest.json").read_text())["test"]
    for filename, key in (("test_locked_cases.jsonl", "cases_sha256"),
                          ("test_locked_gold.jsonl", "gold_sha256")):
        actual = hashlib.sha256((M5 / "m5_data" / filename).read_bytes()).hexdigest()
        if actual != manifest[key]:
            raise ValueError("Frozen input hash mismatch: " + filename)
    cases = list(read_jsonl(M5 / "m5_data/test_locked_cases.jsonl"))
    gold = load_gold(M5 / "m5_data/test_locked_gold.jsonl")
    rows = list(read_jsonl(M5 / "results/m5_runs.jsonl"))
    expected = {(cond, str(seed), c["case_id"])
                for cond in ("single_factorized_v7", "multi_factorized_v7")
                for seed in (11, 42, 77) for c in cases}
    actual = [(r["condition"], str(r["seed"]), r["case_id"]) for r in rows]
    if len(actual) != 216 or len(set(actual)) != 216 or set(actual) != expected:
        raise ValueError("Incomplete or duplicate 216-row experiment")
    identities = {(r["trace"]["model"], r["trace"]["temperature"],
                   r["trace"]["prompt_version"]) for r in rows}
    if len(identities) != 1:
        raise ValueError("Mixed model/prompt/temperature in saved runs")

    per, mean_sd = analyze(rows, gold)
    paired = paired_comparison(rows, gold, "single_factorized_v7", "multi_factorized_v7")
    out_dir = Path(__file__).resolve().parent
    with (out_dir / "results_per_seed.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["condition", "seed", "cases", "coverage", "selective_accuracy",
                "schema_validity", "mean_calls", "mean_input_tokens",
                "mean_output_tokens", "mean_latency_ms", "model_abstains",
                "fallback_or_failure"]
        writer = csv.DictWriter(f, cols)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in cols} for r in per)

    token_cost_by_condition = {}
    for cond in ("single_factorized_v7", "multi_factorized_v7"):
        cost_per_seed = []
        for seed in ("11", "42", "77"):
            subset = [r for r in rows if r["condition"] == cond and str(r["seed"]) == seed]
            cost_per_seed.append(statistics.mean(
                (r["trace"].get("input_tokens") or 0) +
                (r["trace"].get("output_tokens") or 0) for r in subset))
        token_cost_by_condition[cond] = {
            "mean_tokens_per_case": round(statistics.mean(cost_per_seed), 6),
            "sd_tokens_per_case": round(statistics.stdev(cost_per_seed), 6),
        }

    with (out_dir / "results_summary.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["condition", "cases_per_seed", "seeds", "coverage_mean", "coverage_sd",
                "selective_accuracy_mean", "selective_accuracy_sd",
                "schema_validity_mean", "schema_validity_sd",
                "mean_calls_mean", "mean_calls_sd", "mean_input_tokens_mean",
                "mean_input_tokens_sd", "mean_output_tokens_mean", "mean_output_tokens_sd",
                "mean_latency_ms_mean", "mean_latency_ms_sd", "mean_tokens_per_case", "sd_tokens_per_case"]
        writer = csv.DictWriter(f, cols)
        writer.writeheader()
        for r in mean_sd:
            writer.writerow({**r, "cases_per_seed": 36,
                             **token_cost_by_condition[r["condition"]]})

    failures = defaultdict(list)
    model_abstentions = Counter()
    for r in rows:
        tr = r["trace"]
        cond = r["condition"]
        if tr.get("schema_valid") is False:
            failures[cond].append((str(r["seed"]), r["case_id"],
                                   tr.get("failure_stage"), tr.get("schema_error")))
        elif r["decision"]["status"] == "ABSTAIN":
            model_abstentions[cond] += 1
    lines = ["# M6 failure analysis (offline, saved traces)", "",
             "Each condition has 108 runs: 36 cases repeated over seeds 11, 42 and 77.",
             "Abstention does not imply a wrong accepted risk label.", ""]
    for cond in ("single_factorized_v7", "multi_factorized_v7"):
        lines += [f"## {cond}", "",
                  f"- Valid-policy abstentions: {model_abstentions[cond]}",
                  f"- Validation/fallback failures: {len(failures[cond])}", ""]
        for seed, cid, stage, error in failures[cond]:
            lines.append(f"- Seed {seed}, {cid}: {stage}; {error}")
        lines.append("")
    lines += [f"Paired comparison: {paired['both_correct']} both correct; "
              f"{paired.get('reference_only',0)} Single only; "
              f"{paired.get('candidate_only',0)} Multi only; "
              f"{paired['both_not_correct']} neither correct, across 108 paired case-seed runs.",
              "The same 36 cases are reused across seeds; paired runs are not 108 independent cases.",
              "Reference labels are synthetic-policy-derived, not externally validated real-world risk labels."]
    (out_dir / "failure_analysis_generated.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "identity": next(iter(identities)),
                      "paired": paired, "outputs": ["results_per_seed.csv",
                        "results_summary.csv", "failure_analysis_generated.md"]}, indent=2))

if __name__ == "__main__":
    main()
