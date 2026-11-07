"""Prepare a locked M2-aligned test suite from the public Kaggle Hajj/Umrah CSV.

The source dataset is not bundled. Run with the original CSV and review the
data audit: numeric band thresholds below are a disclosed reconstruction,
not author-supplied encoding from Samrgandi (2026).
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

WEIGHTS = {
    "Crowd_Density": .25, "Temperature": .20, "Fatigue_Level": .15,
    "Stress_Level": .15, "Queue_Time_minutes": .10,
    "Emergency_Event": .10, "Distance_Between_People_m": .05,
}
LOW_BOUND, HIGH_BOUND = 1.8, 2.4
SEEDS = [11, 42, 77]
CATEGORIES = {
    "low": 1, "medium": 2, "moderate": 2, "high": 3,
    "normal": 1, "mild": 1, "severe": 3, "very high": 3,
    "minimal": 1, "none": 1,
}
YES = {"yes", "true", "1", "y"}
NO = {"no", "false", "0", "n", "none"}

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = set(WEIGHTS) - headers
        if missing:
            raise ValueError("CSV missing required M2 columns: " + ", ".join(sorted(missing)))
        rows = list(reader)
    if not rows:
        raise ValueError("Empty dataset")
    return rows

def risk_tier(value):
    return "LOW" if value < LOW_BOUND else "MEDIUM" if value <= HIGH_BOUND else "HIGH"

def numeric(values):
    try:
        for v in values:
            if v is None or str(v).strip() == "":
                return False
            float(v)
        return True
    except (ValueError, TypeError):
        return False

def fit_encoding(train):
    """Fit numeric tertile cutoffs on the TRAIN partition only."""
    encoding = {}
    for field in WEIGHTS:
        vals = [r[field].strip() for r in train]
        if field == "Emergency_Event":
            bad = sorted({v for v in vals if v.lower() not in YES | NO})
            if bad:
                raise ValueError(f"Unrecognized Emergency_Event categories: {bad[:10]}")
            encoding[field] = {"type": "boolean"}
        elif numeric(vals):
            nums = sorted(float(v) for v in vals)
            n = len(nums)
            encoding[field] = {
                "type": "numeric_tertiles",
                "one_third": nums[(n - 1) // 3],
                "two_thirds": nums[(2 * (n - 1)) // 3],
                "descending": field == "Distance_Between_People_m",
            }
        else:
            bad = sorted({v for v in vals if v.lower() not in CATEGORIES})
            if bad:
                raise ValueError(f"Unrecognized {field} categories: {bad[:10]}. Audit dataset before scoring.")
            encoding[field] = {"type": "ordinal"}
    return encoding

def band(field, raw, encoding):
    if raw is None or str(raw).strip() == "":
        return None
    rule = encoding[field]
    if rule["type"] == "boolean":
        value = str(raw).strip().lower()
        if value not in YES | NO:
            raise ValueError(f"Invalid boolean {field}: {raw!r}")
        return 3 if value in YES else 1
    if rule["type"] == "ordinal":
        value = str(raw).strip().lower()
        if value not in CATEGORIES:
            raise ValueError(f"Unrecognized ordinal {field}: {raw!r}")
        return CATEGORIES[value]
    v = float(raw)
    a, b = rule["one_third"], rule["two_thirds"]
    result = 1 if v <= a else 2 if v <= b else 3
    return 4 - result if rule["descending"] else result

def reference(row, encoding):
    b = {field: band(field, row[field], encoding) for field in WEIGHTS}
    if any(v is None for v in b.values()):
        raise ValueError("Cannot derive ground truth from a missing clean field")
    score = sum(WEIGHTS[k] * b[k] for k in WEIGHTS)
    return {"bands": b, "score": round(score, 6), "risk": risk_tier(score)}

def prepare(csv_path, destination, seed=42):
    src = Path(csv_path)
    rows = read_csv(src)
    rng = random.Random(seed)
    indices = list(range(len(rows)))
    rng.shuffle(indices)
    test_size = round(len(indices) * .20)
    train_idx, test_idx = indices[test_size:], indices[:test_size]
    encoding = fit_encoding([rows[i] for i in train_idx])
    records = [(i, rows[i], reference(rows[i], encoding)) for i in test_idx]
    buckets = {level: [item for item in records if item[2]["risk"] == level] for level in ("LOW", "MEDIUM", "HIGH")}
    for bucket in buckets.values():
        rng.shuffle(bucket)
    selected = []
    used = set()
    # Eighteen clean and nine corrupted cases, balanced across risk tiers.
    for level in buckets:
        if len(buckets[level]) < 9:
            raise ValueError("Hold-out set has too few " + level + " cases")
        for j, item in enumerate(buckets[level][:9]):
            difficulty = "clean" if j < 6 else ("missing", "noisy", "conflicting")[j - 6]
            selected.append((item, difficulty))
            used.add(item[0])
    # The last three cases are genuinely near the declared class boundaries.
    remaining = [item for item in records if item[0] not in used]
    remaining.sort(key=lambda item: min(abs(item[2]["score"] - LOW_BOUND),
                                        abs(item[2]["score"] - HIGH_BOUND)))
    selected.extend((item, "borderline") for item in remaining[:3])
    cases = []
    for j, ((row_index, row, ref), difficulty) in enumerate(selected):
        field = list(WEIGHTS)[(j // 3) % len(WEIGHTS)]
        observed = {k: {"value": row[k], "quality": "observed"} for k in WEIGHTS}
        if difficulty in ("missing", "noisy", "conflicting"):
            observed[field]["quality"] = difficulty
            if difficulty == "missing":
                observed[field]["value"] = None
            elif difficulty == "conflicting":
                original = row[field]
                observed[field]["alternate_value"] = (
                    str(round(float(original) * 1.7 + 1, 3)) if numeric([original]) and field != "Emergency_Event"
                    else ("High" if str(original).strip().lower() == "low" else "Low")
                )
            else:
                original = row[field]
                observed[field]["value"] = (
                    str(round(float(original) * 1.25 + 1, 3)) if numeric([original]) and field != "Emergency_Event"
                    else ("High" if str(original).strip().lower() == "low" else "Low")
                )
        cases.append({
            "case_id": f"HAJJ-{j+1:03d}", "source_row_index": row_index,
            "difficulty": difficulty, "observations": observed,
            "clean_observations": {k: row[k] for k in WEIGHTS},
            "gold": ref["risk"], "gold_score": ref["score"],
        })
    if len(cases) != 30 or len({c["case_id"] for c in cases}) != 30:
        raise AssertionError("Expected 30 distinct cases")
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    case_path = out / "locked_cases.jsonl"
    case_path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    summary = {
        "dataset": "Hajj and Umrah Crowd Management Dataset (Kaggle, ziya07)",
        "source_url": "https://www.kaggle.com/datasets/ziya07/hajj-and-umrah-crowd-management-dataset",
        "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "source_rows": len(rows), "train_rows": len(train_idx), "holdout_rows": len(test_idx),
        "split_seed": seed, "experiment_seeds": SEEDS,
        "cases": len(cases), "difficulty": {k: sum(c["difficulty"] == k for c in cases)
                                      for k in ("clean", "missing", "noisy", "conflicting", "borderline")},
        "weights": WEIGHTS, "risk_thresholds": {"low_below": LOW_BOUND, "high_above": HIGH_BOUND},
        "encoding": encoding,
        "proxy_note": "Numeric tertiles are a team-defined training-split reconstruction. The paper does not specify the exact encoding; do not claim replication.",
        "cases_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Original public Kaggle CSV (not bundled)")
    ap.add_argument("--out", default="proposal/data")
    args = ap.parse_args()
    print(json.dumps(prepare(args.csv, args.out), indent=2))

if __name__ == "__main__":
    main()
