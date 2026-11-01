# M5 results — V7.1

Status: **COMPLETE**
Golden cases: **36**; evaluated rows: **216/216**; missing: **0**.

Synthetic course-label accuracy is not real-world crowd safety validation. Multi-agent and single-agent must use the same cases and seeds.

| Condition | Seeds | Coverage (mean ± SD) | Selective accuracy (mean ± SD) | Schema validity (mean ± SD) | Calls/case (mean ± SD) | Latency ms (mean ± SD) |
|---|---:|---:|---:|---:|---:|---:|
| multi_factorized_v7 | 3 | 0.7778 ± 0.0278 | 1.0000 ± 0.0000 | 0.9815 ± 0.0160 | 2.9627 ± 0.0323 | 13653.6367 ± 10353.8371 |
| single_factorized_v7 | 3 | 0.7963 ± 0.0160 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 4327.2867 ± 2253.9425 |

Component level: `component_trajectory_per_seed.csv` includes observed-field band accuracy and complete-trajectory rate.
Trajectory metric: calls per case, complete three-specialist reporting with valid schema.

SD across a single seed is **undefined**, not 0. Repeated seeds share the same 36 cases.

The aggregation policy is explicit and synthetic, so high scores measure policy compliance rather than medical/operational validity.
