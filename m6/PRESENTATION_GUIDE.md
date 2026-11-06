# M6 — Team presentation guide

**Purpose:** Show the complete implemented system and defend a controlled comparison. These notes are a guide, not a fixed presentation duration; follow the instructor's announced in-class time limit.

## Suggested slide sequence

**1 — Research question and controlled factor**

Question: Does splitting one generalist into three domain-specific interpreters improve policy-based crowd-risk decisions?
Controlled: identical 36 synthetic cases, reference policy, scoring, model, temperature and seeds.
Manipulated: one generalist interpretation vs three independent domain-specialist interpretations.

**2 — Architecture and termination**

Single: all seven observations → generalist Gemini report → shared policy validator → deterministic aggregation → tier or abstention.

Multi: crowd / health / environment observations → three *independent, domain-blind* specialist Gemini reports → same validator → same deterministic aggregation → tier or abstention.

Each report may be tried twice maximum. A second invalid report causes safe abstention. The specialists do not debate or message each other. No operational actuation.

**3 — Dataset and experimental setup**

36 synthetic locked cases; seeds 11, 42 and 77; 108 case-seed runs per condition, 216 total. Ground truth follows documented classroom policy. Saved model is Gemini 3.5 Flash-Lite, requested temperature 1.0. Explain that seeds do not guarantee identical regeneration.

**4 — Main results and resource costs**

| Metric | Single | Multi |
|---|---:|---:|
| Coverage mean | 80.56% | 79.63% |
| Selective policy accuracy | 100.00% | 100.00% |
| Mean API calls/task | 1.05 | 3.00 |
| **Mean token cost/task** | **902.86 tokens** | **1288.43 tokens** |
| Mean latency/task | 3.27 s | 9.56 s |

State cost **in tokens**, not currency. Variance across seeds: coverage SD 0.00 pp vs 1.60 pp; latency SD 2.65 vs 7.90 s. Token totals include input + output.

**5 — Failure analysis**

Six repeatedly uncertain cases per seed appropriately abstain. Wrong distance-to-band mappings produced three validation failures in each condition. Multi seed 42, case `V7-0005`, accounts for the one paired Single-only accepted decision. Show the raw recorded trace if asked.

**6 — Conclusion and limitations**

The evidence does not show a Multi-Agent performance gain in this small controlled synthetic benchmark. Multi costs more and has more specialist failure opportunities. The 100% figure is selective policy agreement after validation, not an independently validated risk predictor. Avoid real-world safety claims.

## Short live demonstration (no quota required)

From the repository root:

```bash
python3 m6/build_m6.py
```

Then open `m6/results_summary.csv`, `m6/results_per_seed.csv`, and `m6/failure_analysis_generated.md`. Show `m5/m5_agent.py` to demonstrate the actual Single/Multi routing and deterministic aggregation. This is an **offline evaluation replay**; do not present it as a new live Gemini run.

If the instructor specifically requires a **live model inference** demonstration rather than a working saved-results demonstration, it requires a configured API key, network access and quota. That is distinct from the offline reproducible M6 analysis.

## Team Q&A preparation

- **Why three agents?** They map to crowd, health and environment; each sees only its assigned domain.
- **What changed?** LLM role and information partition; aggregation and policy stay the same.
- **Why is Multi not better?** The observed data show no gain; one extra validation fallback and substantially more calls.
- **Why 100% selective accuracy?** It excludes abstentions; validator filters policy-inconsistent reports.
- **Why tokens, not SAR/USD?** The acceptance criteria explicitly allow tokens, and actual billed prices were not retained.
- **Are the 108 pairs independent?** No. They repeat the same 36 cases across seeds.
- **Is it safe for pilgrims?** No; this is synthetic coursework, not real operational validation.
