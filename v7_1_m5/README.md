# Hajj-AI V7.1 — CPCS 683 M5 and M6

## Study

**Question:** Does a domain-factorized multi-agent system improve classification reliability over a strong single-agent baseline under the same synthetic Hajj risk policy?

The data, case labels, thresholds, and recommended actions are illustrative classroom artifacts. No real pilgrim, CCTV, patient, or operational records were used. The system is not suitable for deployment or autonomous safety decisions.

### Experimental conditions

| Condition | Model inference topology | Aggregation |
|---|---|---|
| `single_factorized_v7` | One Gemini call assesses all seven fields across three domains | Deterministic policy |
| `multi_factorized_v7` | Three separate, domain-isolated Gemini calls for Crowd, Health, and Environment | The same deterministic policy |

The coordinator is code, not a fourth LLM call. Multi-agent execution does not involve live communication, interactive evidence retrieval, or autonomous intervention. Both conditions use the same validation rules and policy-based abstention.

### Final locked-test configuration

- **Model:** `gemini-3.5-flash-lite`
- **Requested temperature:** `1.0`
- **Seeds:** `11`, `42`, `77`
- **Locked test cases:** 36, identical for both conditions and all three seeds
- **Completed output rows:** 216/216
- **Source:** `results/v71_35_all_seeds.jsonl`
- **Scores:** `results/m5_35_score/`
- **Status:** `results/m5_35_score/status.json` reports `complete: true`

The earlier Gemini 3.1 Flash-Lite experiment used `temperature=0.4` and only Seed 11; it is preserved separately as `results/v71_test_seed11.jsonl`. **Do not combine its metrics with the final 3.5 runs.**

## Final results

Metrics below are mean ± **sample standard deviation across three seeds**, not a confidence interval. Each seed uses the same 36 cases.

| Metric | Single-Agent | Multi-Agent |
|---|---:|---:|
| Coverage | **79.63% ± 1.60 pp** | 77.78% ± 2.78 pp |
| Selective accuracy on issued decisions | 100.00% ± 0.00 pp | 100.00% ± 0.00 pp |
| Schema validity | **100.00% ± 0.00 pp** | 98.15% ± 1.60 pp |
| API calls per case | **1.00 ± 0.00** | 2.96 ± 0.03 |
| Mean latency per case | **4.33 ± 2.25 s** | 13.65 ± 10.35 s |

Selective accuracy excludes abstentions. Coverage counts valid final risk decisions out of all cases. The 100% selective accuracy applies only to the decisions accepted under this synthetic policy; it is not 100% accuracy across all cases or evidence of real-world safety.

**Observed result:** The multi-agent topology did not improve decision accuracy or coverage. Single-Agent had slightly higher coverage, higher output validity, and lower latency and API calls. Do not claim a multi-agent performance advantage on this benchmark.

### Per-seed accepted decisions

| Seed | Single | Multi |
|---|---:|---:|
| 11 | 28/36 | 29/36 |
| 42 | 29/36 | 28/36 |
| 77 | 29/36 | 27/36 |

Across all three seeds, the paired evaluation records 83 both-correct case-seed pairs, 3 reference-only successes, 1 candidate-only success, and 21 pairs in which neither produced a correct accepted decision. Repeated seeds of the same cases are not independent test cases.

### Failure analysis and limitations

- **Multi-Agent schema failures:** Two of the 108 Multi-Agent case-seed runs had invalid observed-band output in the Crowd specialist, resulting in safe fallback abstention. Both were for `V7-0013`, Seeds 42 and 77.
- **Additional abstentions:** The Multi-Agent also abstained on `V7-0123` for Seed 77, whereas the Single-Agent issued a HIGH decision. This is a failure-analysis case, not a reason to override abstention rules post hoc.
- **Conservative policy abstentions:** Some cases are indeterminate because unreliable fields can change the risk category. These should not be counted as arbitrary model mistakes.
- **Higher overhead:** The three specialist calls cost more requests and, in the observed runs, longer wall-clock inference time than the single call.
- **Synthetic labels:** The gold labels are derived from a proposed classroom decision policy, not independent expert ground truth. Testing policy conformity cannot establish Hajj crowd-safety effectiveness.
- **No post-test tuning:** Preserve the final V7.1 measurements. The optional V7.2 schema-constraint idea has not been evaluated on an independent holdout and is not included as a final result.

## Data and evaluation

- `v7_synthetic_data/test_locked_cases.jsonl`: frozen 36-case locked test set
- `v7_synthetic_data/test_locked_gold.jsonl`: frozen synthetic gold labels
- `v7_synthetic_data/manifest.json`: source-file hash checks
- `v7_synthetic_data/dev_*`: separate development cases; do not merge into locked-test metrics
- `hajj_challenge_v1/`: separate 24-case stress suite; its available Seed 11 result used the earlier model and is not part of the 216-row final evaluation
- `results/m5_35_score/per_seed.csv`: per-seed metrics
- `results/m5_35_score/mean_sd.csv`: per-condition means and standard deviations
- `results/m5_35_score/component_trajectory_per_seed.csv`: observed-band and trajectory metrics
- `results/m5_35_score/paired.json`: paired comparison
- `results/m5_35_score/REPORT.md`: generated result summary

### Reproduce the evaluation without API calls

Run from inside `v7_1_m5`:

```bash
python3 -m unittest -q test_v7.py
python3 m5_finalize.py --results results/v71_35_all_seeds.jsonl --out results/m5_35_score
```

Both steps use the Python standard library and do not contact Gemini. The strict finalizer checks the frozen files, missing rows, duplicates, and expected case/seed/condition combinations.

### Reproduce the Gemini 3.5 experiment

An API key, available quota, and live Gemini service are required. Results are nondeterministic even with specified seeds. Use a new output path to avoid replacing the original measurements.

```bash
read -rs GEMINI_API_KEY; echo; export GEMINI_API_KEY
python3 resume_with_retries.py \
  --cases v7_synthetic_data/test_locked_cases.jsonl \
  --seeds 11 42 77 \
  --temperature 1.0 \
  --model gemini-3.5-flash-lite \
  --conditions single_factorized_v7 multi_factorized_v7 \
  --case-delay 25 \
  --out results/new_reproduction.jsonl \
  --resume
```

The `--case-delay` setting excludes deliberate idle time between completed cases from measured model-pass latency.

## Academic and privacy notes

The final comparison uses the same model, seeds, frozen cases, policies, and aggregation across conditions. All listed results are actual saved model outputs; no unrun seeds are represented as data. The shared model backbone and deterministic policy constrain the claims we can make. The public repository must not include API keys, `.env` files, service-account secrets, or identifying participant information.
