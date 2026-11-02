# Hajj-AI — CPCS 683 M5 / M6

## Current code: V7.2 reliability repair

The code in this directory implements **V7.2**, the repaired version of the Hajj risk simulation. The older V7.1 source is preserved in Git history, and its measured outputs remain in `results/`. The live repaired implementation should **not** be described as the exact code that generated the historical V7.1 results.

This is a **synthetic classroom simulation**, not a deployed safety or clinical system. All final interventions require human authorization.

### Architecture

- `single_factorized_v7`: one Gemini model call produces bands for the Crowd, Health, and Environment domains.
- `multi_factorized_v7`: three independently prompted, domain-restricted Gemini specialists produce separate band reports; a deterministic coordinator aggregates them. There is no fourth model call.
- Both conditions share identical aggregation, input quality checks, thresholds, policy-conformity checks, structured output contracts, and a maximum of **one extra generation per failed report**.
- A nonconforming report is rejected. If its regeneration also fails, the system abstains instead of issuing an unvalidated risk decision.
- `agent_calls_this_pass`, token counts, latency, `report_attempts` and `correction_events` capture any regeneration overhead. This matters when comparing cost and reliability.
- The validated classroom policy is supplied to the model and used for deterministic band checking; this measures policy adherence, not independent reasoning or real-world medical/crowd risk performance.

### Repair verification

Local unit tests cover the fixed-schema requirement, specialist isolation, incorrect but syntactically valid bands, retry recovery, repeat-failure abstention, and deterministic aggregation. The user also ran Gemini 3.5 Flash-Lite against the **two previously problematic cases** (`V7-0013` and `V7-0123`) on Seeds 42 and 77. The resulting 8/8 outputs matched the expected risk tiers (`LOW` and `HIGH` respectively); some needed a retry. This is a **post-hoc diagnostic**, not a new unbiased benchmark, and the raw diagnostic result file is not stored in this repository.

Run local tests with no API key:

```bash
cd v7_1_m5
python3 -m unittest -q test_v7.py
python3 run_experiment.py --cases v7_synthetic_data/test_locked_cases.jsonl --seeds 11 42 77 --temperature 1.0 --model gemini-3.5-flash-lite --conditions single_factorized_v7 multi_factorized_v7 --dry-run
```

## Completed V7.2 locked-test evaluation

The repaired V7.2 experiment has been completed on the same 36 frozen synthetic test cases, both agent conditions, and Seeds 11, 42, and 77. Results are available at `results/v72_35_all_seeds.jsonl`. The strict finalizer reports **216/216 complete**, with no missing rows, model `gemini-3.5-flash-lite`, requested temperature `1.0`, and prompt version `hajj_ai_v7_2_policy_validation_retry`.

| V7.2 mean ± sample SD across 3 seeds | Single-Agent | Multi-Agent |
|---|---:|---:|
| Coverage | 80.56% ± 0.00 pp | 79.63% ± 1.60 pp |
| Selective accuracy among accepted decisions | 100% ± 0.00 pp | 100% ± 0.00 pp |
| Schema/policy validity | 97.22% ± 0.00 pp | 97.22% ± 2.78 pp |
| Gemini calls per case | 1.0467 ± 0.0162 | 2.9997 ± 0.0735 |
| Inference latency per case | 3.27 ± 2.65 s | 9.56 ± 7.90 s |

Across 216 runs: **173 accepted, correct synthetic-policy classifications; 37 abstentions caused by the policy's uncertainty interval; and 6 abstentions from exhausted model-output validation retries**. There were **5 successfully repaired reports** after a second model call. All six final validation failures involved the model's band for `crowd.distance_between_people_m`.

A total of **five** validation failures occurred on case `V7-0021`, where the observed interpersonal distance was 0.46 m but the model repeatedly returned a band other than the required 2. Because crowd density was noisy, a policy-valid report for this case would still abstain. The remaining validation failure was Multi-Agent on case `V7-0005` at Seed 42. Its observed 0.73 m distance also requires band 2; unlike `V7-0021`, all fields were observed and the model failure caused an **avoidable fallback abstention** rather than the valid MEDIUM policy decision.

The Multi-Agent condition did not outperform Single-Agent in this experiment. The 100% selective accuracy applies to accepted outputs only, and the synthetic gold labels are policy-derived rather than independent expert ground truth. `results/m5_v72_score/` contains all per-seed scores, sample SDs, component/trajectory measurements, paired comparison and final report. See `results/m5_v72_score/FAILURE_AUDIT.md` for the audit of all 216 saved traces.

Reproduce the **completed V7.2 scoring** without API calls:

```bash
python3 m5_finalize.py --results results/v72_35_all_seeds.jsonl --out results/m5_v72_score
```

This evaluation is post-hoc relative to the previously inspected V7.1 failure cases. Do not present a comparison of the two versions on this same test set as an unbiased performance improvement.

## Existing complete M5 / M6 evaluation: V7.1 (historical baseline)

The actual 216/216 **prior V7.1** Gemini runs (36 frozen synthetic cases, two arms, Seeds 11/42/77) are preserved under `results/v71_35_all_seeds.jsonl`, scored in `results/m5_35_score/`. The final model was `gemini-3.5-flash-lite`, requested temperature `1.0`. The separate earlier Gemini 3.1 Flash-Lite Seed 11 experiment is in `results/v71_test_seed11.jsonl` and is **not** pooled with the 3.5 results.

| Historical V7.1 mean ± sample SD over 3 seeds | Single-Agent | Multi-Agent |
|---|---:|---:|
| Coverage | 79.63% ± 1.60 pp | 77.78% ± 2.78 pp |
| Selective accuracy on accepted decisions | 100% ± 0.00 pp | 100% ± 0.00 pp |
| Schema validity | 100% ± 0.00 pp | 98.15% ± 1.60 pp |
| API calls per case | 1.00 ± 0.00 | 2.96 ± 0.03 |
| Mean latency per case | 4.33 ± 2.25 seconds | 13.65 ± 10.35 seconds |

The Multi-Agent did **not** outperform the Single-Agent on this benchmark; higher latency and a small number of schema/policy mistakes were observed. A selective accuracy of 100% excludes abstentions. These synthetic labels come from the simulation policy, not independent expert-reviewed real-world ground truth.

To reproduce the **historical V7.1** scores locally without Gemini:

```bash
python3 m5_finalize.py --results results/v71_35_all_seeds.jsonl --out results/m5_35_score
```

The scorer checks frozen case/label hashes, the full 216-case-seed-condition grid, duplicates, and consistent model/prompt version/temperature. It reports per-seed metrics, mean and sample SD, paired accuracy, observed-band component accuracy, and trajectory completeness. It rejects accidentally mixed V7.1/V7.2 runs.

### Test V7.2 on the two diagnosed cases

```bash
read -rs GEMINI_API_KEY; echo; export GEMINI_API_KEY
python3 resume_with_retries.py \
  --cases v7_synthetic_data/repair_smoke_cases.jsonl \
  --seeds 42 77 \
  --temperature 1.0 \
  --model gemini-3.5-flash-lite \
  --conditions single_factorized_v7 multi_factorized_v7 \
  --case-delay 25 \
  --out results/v72_repair_smoke.jsonl \
  --resume
```

A repeat of these eight diagnosed-case outputs is not an independent evaluation. No need to rerun it if the diagnostic test already succeeded on your machine.

Transient Gemini HTTP errors and temporary connection failures (including remote disconnects and read timeouts) are retried with bounded backoff in `resume_with_retries.py`. If all attempts fail, saved JSONL rows remain intact and the same `--resume` command continues from the next unfinished case. This retry-wrapper update does not change the model, prompts, policy or experiment fingerprint.

### Reproduce the completed V7.2 experiment if required

The V7.2 live experiment **has already completed**. Its original 216 model outputs and final scoring are saved in this repository. Re-running Gemini is unnecessary for scoring and may produce different outputs or incur additional usage. If a separate reproduction is required, use a fresh output file and do not overwrite or combine historical and current versions.

```bash
python3 resume_with_retries.py \
  --cases v7_synthetic_data/test_locked_cases.jsonl \
  --seeds 11 42 77 \
  --temperature 1.0 \
  --model gemini-3.5-flash-lite \
  --conditions single_factorized_v7 multi_factorized_v7 \
  --case-delay 25 \
  --out results/v72_35_all_seeds.jsonl \
  --resume
python3 m5_finalize.py --results results/v72_35_all_seeds.jsonl --out results/m5_v72_score
```

Do **not** claim that V7.2 improves full-set accuracy, coverage, cost or Multi-Agent superiority until this new experiment completes; the eight selected repairs do not establish that. Comparing V7.1 with V7.2 on the same cases after inspecting failures is exploratory/post-hoc.

## Files

- `factorized_v7.py`: current V7.2 model integration, policy checking, regeneration, and coordinator
- `test_v7.py`: local correctness and failure-path tests
- `run_experiment.py`, `resume_with_retries.py`: reproducible live runner and transient-request retry
- `m5_finalize.py`, `scoring.py`: automated evaluation and mean/SD computation
- `v7_synthetic_data/`: locked synthetic test cases and gold, manifest, and separate post-hoc smoke cases
- `hajj_challenge_v1/`: separate stress dataset (not part of the 36-case main test)
- `results/v71_35_all_seeds.jsonl`: historical V7.1 final model outputs
- `results/m5_35_score/`: historical V7.1 result tables

## Reproducibility and privacy

The seed, temperature, model, inputs and policy are set explicitly. A source-code edit changes the experiment fingerprint so that earlier partial runs cannot silently resume with a different implementation. The locked test labels are synthetic classroom labels and do not establish real-world safety. Do not commit API keys, local `.env` files, real CCTV feeds, identifying participant information, or account details.
