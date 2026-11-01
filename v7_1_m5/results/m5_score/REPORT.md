# M5 results — V7.1

Status: **INCOMPLETE / PREVIEW ONLY**
Golden cases: **36**; evaluated rows: **72/216**; missing: **144**.

Synthetic course-label accuracy is not real-world crowd safety validation. Multi-agent and single-agent must use the same cases and seeds.

| Condition | Seeds | Coverage (mean ± SD) | Selective accuracy (mean ± SD) | Schema validity (mean ± SD) | Calls/case (mean ± SD) | Latency ms (mean ± SD) |
|---|---:|---:|---:|---:|---:|---:|
| multi_factorized_v7 | 1 | 0.8056 ± N/A | 1.0000 ± N/A | 1.0000 ± N/A | 3.0000 ± N/A | 12313.6500 ± N/A |
| single_factorized_v7 | 1 | 0.8056 ± N/A | 1.0000 ± N/A | 0.9722 ± N/A | 1.0000 ± N/A | 5767.0900 ± N/A |

Component level: `component_trajectory_per_seed.csv` includes observed-field band accuracy and complete-trajectory rate.
Trajectory metric: calls per case, complete three-specialist reporting with valid schema.

SD across a single seed is **undefined**, not 0. Repeated seeds share the same 36 cases.

The aggregation policy is explicit and synthetic, so high scores measure policy compliance rather than medical/operational validity.
