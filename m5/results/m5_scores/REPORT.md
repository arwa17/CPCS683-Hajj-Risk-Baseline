# M5 results

Model: **gemini-3.5-flash-lite**; prompt version: **hajj_ai_v7_2_policy_validation_retry**; temperature: **1.0**.

Status: **COMPLETE**
Golden cases: **36**; evaluated rows: **216/216**; missing: **0**.

Synthetic course-label accuracy is not real-world crowd safety validation. Multi-agent and single-agent must use the same cases and seeds.

| Condition | Seeds | Coverage (mean ± SD) | Selective accuracy (mean ± SD) | Schema validity (mean ± SD) | Calls/case (mean ± SD) | Latency ms (mean ± SD) |
|---|---:|---:|---:|---:|---:|---:|
| multi_factorized_v7 | 3 | 0.7963 ± 0.0160 | 1.0000 ± 0.0000 | 0.9722 ± 0.0278 | 2.9997 ± 0.0735 | 9555.8600 ± 7903.4071 |
| single_factorized_v7 | 3 | 0.8056 ± 0.0000 | 1.0000 ± 0.0000 | 0.9722 ± 0.0000 | 1.0467 ± 0.0162 | 3269.8333 ± 2647.4952 |

Component level: `component_trajectory_per_seed.csv` includes observed-field band accuracy and complete-trajectory rate.
Trajectory metric: calls per case, complete three-specialist reporting with valid schema.

SD across a single seed is **undefined**, not 0. Repeated seeds share the same 36 cases.

The aggregation policy is explicit and synthetic, so high scores measure policy compliance rather than medical/operational validity.
