# Hajj Crowd-Risk Prioritization

**Course:** CPCS 683 — Advanced Artificial Intelligence  
**Team:** Arwa Al-Zahrani, Atheer Al-Sharif, Batool Al-Sulami  
**Current deliverable:** M5 — Evaluation Harness

## Study and dataset

The goal is to measure a **single-agent baseline** that assigns LOW, MEDIUM or HIGH priority to synthetic Hajj crowd-risk cases or abstains when evidence or model output is unreliable. The study is an illustrative classroom simulation, **not** validated real-world Hajj safety guidance.

The frozen golden set contains **36 synthetic cases** with **36 policy-derived reference labels**. Each case describes seven observations: crowd density, queue time, distance between people, fatigue, stress, emergency event and temperature. Every observation includes its quality and simulated source. The team-defined thresholds are in `v7_1_m5/policy_v7.json`; reference labels are *not* independent expert judgments.

The baseline was evaluated on the **same 36 cases across three seeds** (11, 42 and 77), for **108 completed Single-Agent runs**. The full saved experiment file also contains 108 Multi-Agent runs. The strict scoring program checks the entire **216-row** experimental grid, but only the **Single-Agent rows** are required for this M5 baseline result.

## M5 required deliverables

| Required item | Location |
|---|---|
| Golden set (36 cases) | `v7_1_m5/v7_synthetic_data/test_locked_cases.jsonl` |
| Reference labels | `v7_1_m5/v7_synthetic_data/test_locked_gold.jsonl` |
| Frozen-set integrity | `v7_1_m5/v7_synthetic_data/manifest.json` |
| Automated scoring code | `v7_1_m5/m5_finalize.py` and `scoring.py` |
| Actual model outputs | `v7_1_m5/results/v72_35_all_seeds.jsonl` |
| Baseline score for each seed | `v7_1_m5/results/m5_v72_score/per_seed.csv` |
| Mean and sample standard deviation | `v7_1_m5/results/m5_v72_score/mean_sd.csv` |
| Component and trajectory metrics | `v7_1_m5/results/m5_v72_score/component_trajectory_per_seed.csv` |
| Evaluation status and report | `v7_1_m5/results/m5_v72_score/status.json` and `REPORT.md` |

## Baseline results (three seeds)

**Model:** Gemini 3.5 Flash-Lite; **requested temperature:** 1.0.

| Measure | Seed 11 | Seed 42 | Seed 77 | Mean ± sample SD |
|---|---:|---:|---:|---:|
| Correct accepted decisions | 29/36 | 29/36 | 29/36 | 29.00 ± 0.00 |
| Decision coverage / all-case accuracy | 80.56% | 80.56% | 80.56% | **80.56% ± 0.00 pp** |
| Selective accuracy (accepted decisions) | 100.00% | 100.00% | 100.00% | **100.00% ± 0.00 pp** |
| Schema/policy validation success | 97.22% | 97.22% | 97.22% | **97.22% ± 0.00 pp** |
| Mean model calls per case | 1.056 | 1.028 | 1.056 | **1.0467 ± 0.0162** |
| Mean evaluation latency | 6.28 s | 1.32 s | 2.21 s | **3.27 ± 2.65 s** |

**Metric definitions:** Coverage = valid accepted decisions / all runs. Selective accuracy = correct accepted decisions / valid accepted decisions (excludes abstentions). All-case accuracy = correct accepted decisions / all runs. Schema/policy validity = successful report validation / all runs. The reported variance uses the **sample SD over three seed-level scores**, not across 108 independent cases. The same 36 cases are reused across seeds.

**Component/trajectory evaluation:** The complete, policy-valid Single-Agent reporting trajectory rate was **35/36 (97.22%) for each seed**. Observed-field band accuracy was 100% *among successfully validated reports only*; this conditional metric cannot establish real-world accuracy.

**Failure analysis:** Each seed produced 29 correct accepted decisions and seven abstentions: six because unreliable observations could affect the final risk tier, and one because repeated invalid model reports triggered safe fallback (`V7-0021`). No incorrect accepted label occurred relative to the synthetic policy. The limitations are the illustrative, policy-derived labels, a modest synthetic test set and dependence on a commercial model.

## Reproduce the scores (offline, no API calls)

Python **3.10+** is required; the scoring scripts use the standard library. From the cloned repository:

```bash
cd v7_1_m5
python3 m5_finalize.py
cat results/m5_v72_score/REPORT.md
```

The scorer verifies the golden-set SHA-256 hashes, 36-case coverage per seed/condition, no duplicate rows, and consistent model/parameter identifiers. Expected results: `complete: true`, `missing_rows: 0`, `completed_rows: 216`. The baseline has **108** of these saved rows; the other 108 preserve the controlled follow-on comparison.

## Minimal code and data

```text
README.md
.gitignore
v7_1_m5/
  factorized_v7.py
  policy_v7.json
  hajj_baseline/
    __init__.py
    providers.py
    schema.py
  hajj_agent_inputs_v2.jsonl
  run_experiment.py
  resume_with_retries.py
  m5_finalize.py
  scoring.py
  v7_synthetic_data/
    manifest.json
    test_locked_cases.jsonl
    test_locked_gold.jsonl
  results/
    v72_35_all_seeds.jsonl
    m5_v72_score/
      REPORT.md
      mean_sd.csv
      per_seed.csv
      component_trajectory_per_seed.csv
      paired.json
      status.json
```

The supplied `hajj_agent_inputs_v2.jsonl` supports the runner's default example input. For a new frozen-test run, pass `--cases v7_synthetic_data/test_locked_cases.jsonl` explicitly and provide `GEMINI_API_KEY` privately in your environment. New model calls can consume quota or incur cost; they are **not** necessary to reproduce the saved M5 baseline score. The original code and raw measured results have not been changed by repository cleanup.

**Responsible use:** Data are team-authored synthetic scenarios rather than records from SAR, real CCTV, clinical observations or identifiable pilgrims. All intervention suggestions are advisory, and real operational decisions would require qualified human oversight. The final paper and presentation are separate course deliverables and are **not included** in this M5 repository cleanup.
