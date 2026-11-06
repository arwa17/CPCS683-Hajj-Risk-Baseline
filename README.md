# Hajj Crowd-Risk Prioritization

**Course:** CPCS 683 — Advanced Artificial Intelligence  
**Team:** Arwa Al-Zahrani, Atheer Al-Sharif, Batool Al-Sulami  
**Current deliverables:** M5 — Evaluation Harness; M6 — Experimental Condition and Results

## M6 submission

See [M6 — Experimental Condition and Results](m6/README.md) for the implemented treatment architecture, paired comparison, token cost per task, latency with variance, case-level failure analysis, offline analysis script, and presentation guide. M5 source results remain unchanged.

## Study and dataset

The goal is to measure a **single-agent baseline** that assigns LOW, MEDIUM or HIGH priority to synthetic Hajj crowd-risk cases or abstains when evidence or model output is unreliable. The study is an illustrative classroom simulation, **not** validated real-world Hajj safety guidance.

The frozen golden set contains **36 synthetic cases** with **36 policy-derived reference labels**. Each case describes seven observations: crowd density, queue time, distance between people, fatigue, stress, emergency event and temperature. Every observation includes its quality and simulated source. The team-defined thresholds are in `m5/m5_policy.json`; reference labels are *not* independent expert judgments.

The baseline was evaluated on the **same 36 cases across three seeds** (11, 42 and 77), for **108 completed Single-Agent runs**. The full saved experiment file also contains 108 Multi-Agent runs. The strict scoring program checks the entire **216-row** experimental grid, but only the **Single-Agent rows** are required for this M5 baseline result.

## Ground-truth construction and validity

**Provenance.** The 36 cases and their reference labels were created for this course, not taken from SAR, clinical records, or the published study. The set contains 12 LOW, 12 MEDIUM and 12 HIGH reference labels by design; this balanced sample does **not** estimate the prevalence of real Hajj risk levels. No expert has independently validated these labels.

**Predefined labeling rule.** Each of seven fields is mapped to an ordinal band (0, 1, or 2) by the explicit rules in `m5/m5_policy.json`. For numeric values, the *illustrative* cutoffs are queue time 20/50 minutes, distance below 1.5/0.75 metres, and temperature 33/39°C. The three domain means (crowd, health, environment) receive equal weight. The aggregate score is mapped to LOW below 0.7, MEDIUM from 0.7 to below 1.35, and HIGH from 1.35. These numerical cutoffs were selected for a controlled classroom benchmark; **they are not evidence-based Hajj operational thresholds**. Reference labels were fixed independently of Gemini outputs, and dataset hashes are recorded in `m5/m5_data/manifest.json`.

**What is measured.** The scoring measures how faithfully the system follows this declared policy when observation quality can be unreliable. The same policy is available to the agent, so high conditional policy agreement is **not independent evidence of real-world risk prediction**. Abstentions and invalid model responses are reported separately; selective accuracy excludes them. An independent expert review or a separately labeled real-world set would be needed before claims about actual crowd safety.

**Related research.** The crowd, health and environment domain framing is informed by Najwa Samrgandi, *Multi-Agent Crowd-Risk Prioritization for Large-Scale Events: A Hybrid ML–Agent Approach*, IJACSA 17(7), 2026, DOI: [10.14569/IJACSA.2026.0170738](https://doi.org/10.14569/IJACSA.2026.0170738). This coursework implementation is **not** a replication of that study's XGBoost model, dataset or published scores.

## M5 required deliverables

| Required item | Location |
|---|---|
| Golden set (36 cases) | `m5/m5_data/test_locked_cases.jsonl` |
| Reference labels | `m5/m5_data/test_locked_gold.jsonl` |
| Frozen-set integrity | `m5/m5_data/manifest.json` |
| Automated scoring code | `m5/m5_finalize.py` and `scoring.py` |
| Actual model outputs | `m5/results/m5_runs.jsonl` |
| Baseline score for each seed | `m5/results/m5_scores/per_seed.csv` |
| Mean and sample standard deviation | `m5/results/m5_scores/mean_sd.csv` |
| Component and trajectory metrics | `m5/results/m5_scores/component_trajectory_per_seed.csv` |
| Evaluation status and report | `m5/results/m5_scores/status.json` and `REPORT.md` |

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


## First-attempt component evaluation

The raw first-attempt reports in `m5/results/m5_runs.jsonl` allow a component-level assessment **before** validation and retry. For observed fields represented in parseable first-attempt band reports, Single-Agent classified **718/723 (99.31%)** correctly and Multi-Agent **705/711 (99.16%)** correctly. Complete first-attempt reports were **103/108 (95.37%)** for Single-Agent and **312/318 (98.11%)** for Multi-Agent. These are pooled descriptive counts; the number of Multi-Agent specialist reports differs from the number of cases. Per-seed metrics are generated in `component_trajectory_per_seed.csv`.

The post-validation observed-band accuracy of 100% is **conditional by construction**: the validator rejects bands that disagree with the same synthetic policy used to derive the reference labels. Therefore, neither 100% selective accuracy nor the validated band rate demonstrates independent real-world prediction performance. The informative measures are first-attempt errors, decision coverage, fallbacks, and costs.

## Execution settings and comparison limitations

The saved traces report model `gemini-3.5-flash-lite` and temperature `1.0`. The defaults in `m5/run_experiment.py` differ (`gemini-3.1-flash-lite` and `0`), and the exact original invocation was not preserved. Seeds are best-effort for hosted Gemini generation: exact re-generation cannot be guaranteed, whereas `python3 m5_finalize.py` reproduces the offline scoring.

The Single-Agent and Multi-Agent coverage rates are **80.56% and 79.63%**, respectively, with no demonstrated Multi-Agent advantage. Multi-Agent uses about three times as many model calls. Both conditions use the same policy and validator, but Multi-Agent has more specialist-report opportunities to fail or retry.

## Reproduce the scores (offline, no API calls)

Python **3.10+** is required; the scoring scripts use the standard library. From the cloned repository:

```bash
cd m5
python3 m5_finalize.py
cat results/m5_scores/REPORT.md
```

The scorer verifies the golden-set SHA-256 hashes, 36-case coverage per seed/condition, no duplicate rows, and consistent model/parameter identifiers. Expected results: `complete: true`, `missing_rows: 0`, `completed_rows: 216`. The baseline has **108** of these saved rows; the other 108 preserve the controlled follow-on comparison.

## Minimal code and data

```text
README.md
.gitignore
m5/
  m5_agent.py
  m5_policy.json
  hajj_baseline/
    __init__.py
    providers.py
    schema.py
  m5_inputs.jsonl
  run_experiment.py
  resume_with_retries.py
  m5_finalize.py
  scoring.py
  m5_data/
    manifest.json
    test_locked_cases.jsonl
    test_locked_gold.jsonl
  results/
    m5_runs.jsonl
    m5_scores/
      REPORT.md
      mean_sd.csv
      per_seed.csv
      component_trajectory_per_seed.csv
      paired.json
      status.json
```

The supplied `m5_inputs.jsonl` supports the runner's default example input. For a new frozen-test run, pass `--cases m5_data/test_locked_cases.jsonl` explicitly and provide `GEMINI_API_KEY` privately in your environment. New model calls can consume quota or incur cost; they are **not** necessary to reproduce the saved M5 baseline score. The saved evaluation records are available in `m5/results/m5_runs.jsonl`.

**Responsible use:** Data are team-authored synthetic scenarios rather than records from SAR, real CCTV, clinical observations or identifiable pilgrims. All intervention suggestions are advisory, and real operational decisions would require qualified human oversight. The final paper and presentation are separate course deliverables and are **not included** in this M5 repository cleanup.
