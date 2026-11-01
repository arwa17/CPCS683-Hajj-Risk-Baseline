# Hajj-AI V7.1 — CPCS 683 M5 / M6 research package

**Research question.** Does blind, domain-factorized multi-agent analysis improve synthetic Hajj risk classification reliability over a strong single-agent baseline, when both use the same model, frozen cases, illustrative policy, and seeds?

**Not a deployed safety/medical system.** Labels come from a proposed classroom simulation policy, NOT independent expert-verified pilgrim risk ground truth. This experiment measures conformity to a known simulated decision policy.

## Conditions and topology

- `single_factorized_v7`: ONE Gemini response assesses seven fields over the Crowd, Health, and Environment domains.
- `multi_factorized_v7`: THREE domain-isolated Gemini responses, one per Crowd/Health/Environment. A deterministic coordinator aggregates those bands. The coordinator is code, NOT a fourth LLM call.
- Both arms use `gemini-3.1-flash-lite`, `temperature=0.4`, identical per-field policy, identical deterministic aggregation, and the exact same cases and seeds.
- Terminal rule: one report per required domain, then aggregate; if evidence quality makes the policy tier ambiguous, issue `ABSTAIN` and request verification; if schema validation fails, safe fallback `ABSTAIN`.
- The multi agents do NOT perform interactive evidence retrieval or dialogue. Extra agents add computational cost; a benefit is not assumed.

## Data

`v7_synthetic_data/test_locked_cases.jsonl`: 36 independently held-out synthetic cases. `test_locked_gold.jsonl`: frozen synthetic policy labels. The manifest records hashes to detect accidental changes. The 12 development cases live in `v7_synthetic_data/dev_*` and MUST NOT be reported as locked-test results. Identical identifiers can occur across dev and test but denote distinct inputs; keep splits separate.

`hajj_challenge_v1/`: 24 extra stress cases for missing/conflicting/noisy/stale and cross-domain evidence. Do not merge stress results into the 36-case test statistics.

## Offline validation (no API calls)

```bash
cd v7_1_m5
python3 -m unittest -q test_v7.py
python3 m5_finalize.py --allow-incomplete
```

Status is initially **72/216 rows**: Seed 11 completed for Single+Multi on 36 locked cases. Output `results/m5_score/REPORT.md` explicitly says PREVIEW ONLY until three seeds complete. Sample standard deviations for one seed are undefined, not zero.

## Finish 42 & 77 with Gemini (only two conditions)

```bash
cd v7_1_m5
read -rs GEMINI_API_KEY; echo; export GEMINI_API_KEY
python3 resume_with_retries.py \
  --cases v7_synthetic_data/test_locked_cases.jsonl \
  --seeds 42 77 \
  --temperature 0.4 \
  --model gemini-3.1-flash-lite \
  --conditions single_factorized_v7 multi_factorized_v7 \
  --case-delay 10 \
  --out results/v71_test_extra_seeds.jsonl \
  --resume
python3 m5_finalize.py
```

Expected successful output: **144 new rows** in `results/v71_test_extra_seeds.jsonl`, **216 total** across all three seeds and both arms. Actual model-generation API calls for these 144 rows: normally **288**, excluding retries. At a 500 requests/day free-tier limit and 15 RPM, avoid unrelated experiments. `--case-delay 10` sleeps **outside** agent inference measurements, so it does not distort per-pass model latency. Check your project's CURRENT quota before starting; `429` daily quota failures will not be fixed by creating another API key in the same project. Resume the exact same command if interrupted; it refuses changes to the run fingerprint.

## Reproducible scoring

`python3 m5_finalize.py` fails if a case, seed, or condition is missing, if any case is duplicated, or if a frozen input file hash changed. It creates CSVs with per-seed metrics, mean AND sample standard deviation, paired comparison, observed-band component-level metric, and trajectory-level metrics (agent calls and valid complete paths). Scoring uses standard Python only and never calls Gemini.

## Prior observed result (only Seed 11)

On 36 locked cases, each arm accepted **29/36** and was correct on **29/29 accepted** (80.56% all-case accuracy). Both abstained on the other seven cases. Single schema valid was **35/36**, Multi **36/36**; one Single case showed a schema error in a non-observed band. Single averaged **1** Gemini call and Multi **3** per case. **Neither demonstrated a measured advantage in decision accuracy.** `ABSTAIN` cases are excluded from selective accuracy; all-case accuracy includes them in denominator.

On the separately labeled 24-case challenge, both arms accepted and correctly classified 10 cases and abstained on the other 14. These results are for seed 11 and are NOT used to inflate the locked-set accuracy.

## M5/M6 alignment

M5: ≥20 gold-labeled cases; automated reproducible scoring; baseline 3 seeds including spread; end-to-end measures and observed-band component accuracy; trajectory completeness and calls. M6: same three seeds/cases for both conditions; latency/call-token cost; per-condition variance; paired failure analysis. The full M5/M6 claim can only be marked complete AFTER the other seeds finish. See `results/m5_score/` after scoring.

## Academic integrity, privacy, and safety

Data and labels are synthetic classroom artifacts. No real pilgrim CCTV, patient data, or crowd telemetry. A conservative `ABSTAIN` is not equivalent to verified clinical safety. The public repository may contain synthetic test labels and text outputs but must NEVER include `GEMINI_API_KEY`, `.env`, credentials, real personnel/pilgrim data, or API billing details. Source code built from team research; cite external papers separately in final M7 draft. Model outputs and cost/latency are empirical; never report unrun seeds as measurements. One potential validity threat is test-label/policy circularity; another is the lack of real-world evidence and the shared Gemini backbone.
