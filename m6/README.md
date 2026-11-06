# M6 — Experimental Condition and Results

**Course:** CPCS683 Advanced Artificial Intelligence  
**Milestone:** M6 (5 marks)  
**Evidence:** Existing 216 saved Gemini runs; no new model generation.

## Required deliverables and acceptance criteria

| Requirement | Evidence |
|---|---|
| Complete treatment implementation | `m5/m5_agent.py`, `m5/run_experiment.py`, `m5/hajj_baseline/` |
| Same frozen golden set and seeds | 36 cases × seeds 11, 42, 77 × 2 conditions = 216 saved runs |
| Results table comparing conditions | `m6/results_summary.csv`, `m6/results_per_seed.csv` |
| Variance and latency per condition | Mean ± sample SD across three seed-level scores and mean measured latency |
| Cost per task in tokens | Average input, output and combined tokens per case in the results table |
| Failure analysis | `m6/FAILURE_ANALYSIS.md` and `m6/failure_analysis_generated.md` |
| Team presentation | `m6/PRESENTATION_GUIDE.md` |

## C6.1 — Treatment implementation and manipulated design factor

**Question:** Does splitting domain interpretation among specialist agents improve policy-based crowd-risk decisions relative to a single generalist, under the same evaluation policy?

**Manipulated factor:** Organization of LLM interpretation: one generalist call for all seven fields versus three domain-restricted specialists. The synthetic cases, policy thresholds, output requirements, validation method, maximum retry attempts per report, deterministic aggregator, and abstention rule are shared.

| Design component | Single-Agent baseline | Multi-Agent treatment |
|---|---|---|
| Agent roles | One generalist sees all crowd, health, environment observations | Three specialists: crowd, health, environment; each receives only its own domain |
| Topology | Single interpreter → shared aggregator | Independent specialist interpreters → shared aggregator |
| Interaction protocol | One structured `bands` JSON report | Three structured `bands` JSON reports, joined by field path |
| Decision support | Deterministic, equal-weight domain aggregator | Exactly the same deterministic aggregator |
| Termination | One initial generation + at most one retry if report violates schema/policy; otherwise fail-safe abstention | One initial generation + at most one retry **per specialist report**; otherwise fail-safe abstention |
| Actuation | Advisory-only, no real control | Advisory-only, no real control |

This is **sequential execution of independent specialist calls**, not an agent debate or direct specialist-to-specialist conversation. The policy applies the same crowd/health/environment banding to both conditions. A missing, noisy, stale, or conflicting observation is treated as unknown. The shared aggregator computes an interval of possible risk tiers, returns LOW/MEDIUM/HIGH when stable, and requests verification otherwise.

**Why this design?** Domain restriction tests whether splitting evidence interpretation affects accepted decision coverage and costs. The shared deterministic aggregation keeps final decision logic controlled. Because Multi-Agent requires three specialist reports, it has more opportunities for a report failure/retry and necessarily more base API calls. These are consequences of the treatment and limitations when interpreting cost and failure rates.

## C6.2 — Paired experimental conditions

- The exact same 36 frozen synthetic cases and policy-derived labels are used for each condition and seed.
- Seeds: `11`, `42`, `77`; each condition has 108 evaluated case-seed runs.
- Stored trace identity: `gemini-3.5-flash-lite`; requested temperature `1.0`; prompt version `hajj_ai_v7_2_policy_validation_retry`.
- There are 216 unique case × seed × condition records, with 0 missing according to M5 status and strict scoring.
- The measured statistics are descriptive of these **three repeated seed runs on the same 36 cases**, not 108 independent cases or confidence intervals.

## C6.3 — Results: variance, cost and latency

| Metric, mean ± sample SD across 3 seeds | Single-Agent | Multi-Agent |
|---|---:|---:|
| Decision coverage / all-case policy accuracy | **80.56% ± 0.00 pp** | **79.63% ± 1.60 pp** |
| Selective policy accuracy (accepted cases only) | 100.00% ± 0.00 pp | 100.00% ± 0.00 pp |
| Schema/policy validity | 97.22% ± 0.00 pp | 97.22% ± 2.78 pp |
| Model API calls per case | 1.0467 ± 0.0162 | 2.9997 ± 0.0735 |
| Input tokens per case | 813.36 ± 13.47 | 1188.69 ± 30.03 |
| Output tokens per case | 89.50 ± 0.71 | 99.74 ± 3.42 |
| **Total tokens per case (input + output)** | **902.86** | **1288.43** |
| Observed latency per case | 3.27 ± 2.65 s | 9.56 ± 7.90 s |

**Token cost is the chosen cost-per-task unit**, as permitted by the acceptance criteria. It is not a monetary price: model tariff rates and billed currency were not recorded. Total tokens per case are computed from the means of saved per-case `input_tokens` and `output_tokens`; do not assume they are dollar amounts. Latency measures the current recorded evaluation passes, not deployment end-to-end service guarantees.

**Observed comparison:** Multi-Agent used approximately **1.43×** the tokens, **2.87×** the API calls, and **2.92×** the latency per case. Multi-Agent did not improve decision coverage in this experiment (86/108 paired runs both accepted correctly, 1/108 Single-only, 0/108 Multi-only, 21/108 neither). The 100% conditional accuracy is affected by a validator that uses the same policy as the synthetic reference labels, so **coverage, failures and operating cost** are the informative outcomes.

| Seed | Single coverage | Multi coverage | Single calls/case | Multi calls/case |
|---|---:|---:|---:|---:|
| 11 | 80.56% | 80.56% | 1.056 | 2.972 |
| 42 | 80.56% | 77.78% | 1.028 | 2.944 |
| 77 | 80.56% | 80.56% | 1.056 | 3.083 |

Source of all numerical results: `m5/results/m5_runs.jsonl`, `m5/results/m5_scores/per_seed.csv`, `mean_sd.csv`, and `paired.json`. Detailed machine-readable tables are in this folder.

## C6.4 — Failures and explanations

See `FAILURE_ANALYSIS.md` for observed case-level causes, repeated abstentions and validation failures. This separates policy-driven abstention (appropriate when uncertain evidence changes the tier) from generation/validation failure and distinguishes accepted-decision accuracy from all-case coverage.

## Reproduce M6 analysis offline (no API key needed)

From the repository root, with Python 3.10+:

```bash
python3 m6/build_m6.py
```

This checks dataset hashes and verifies the full 216-record grid, then regenerates `m6/results_per_seed.csv`, `m6/results_summary.csv`, and `m6/failure_analysis_generated.md` from the saved raw results. It does not call Gemini or modify M5. The saved model output is the fixed evidence for this analysis; Gemini's seed is best-effort and exact re-generation is not guaranteed.

## Scope and interpretation

The 36 cases and reference labels are authored synthetic cases based on a classroom policy. This project is a controlled simulation, not a validated real-world crowd-safety decision system. The same policy is available to the agents, and the validator rejects policy-inconsistent reports, which limits how selective accuracy can be interpreted. Results are descriptive and do not demonstrate a Multi-Agent advantage or real-world predictive performance.
