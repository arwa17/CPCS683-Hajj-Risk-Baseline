# M6 — Failure Analysis

**Source:** `m5/results/m5_runs.jsonl`, 216 saved case-seed-condition evaluations. Here, a *failure* means a schema/policy validation failure that leads to safe fallback; an *abstention* can also be an intended, correct outcome when the input is uncertain. A 100% selective accuracy must not be interpreted as perfect performance on all 36 cases.

## 1. Outcomes by condition (across three seeds)

| Outcome | Single-Agent (108) | Multi-Agent (108) |
|---|---:|---:|
| Accepted, policy-correct decision | 87 | 86 |
| Valid-policy abstention due to uncertain evidence | 18 | 19 |
| Invalid report / exhausted retry → safe fallback | 3 | 3 |
| Accepted decision inconsistent with synthetic policy | 0 | 0 |
| Total | 108 | 108 |

The six repeatedly uncertainty-sensitive cases in each seed include `V7-0003`, `V7-0012`, `V7-0018`, `V7-0019`, `V7-0026`, and `V7-0069`. Their observed evidence does not narrow the interval to one policy tier. Such abstentions are intentional, not an unreported prediction error.

## 2. Concrete model-output validation failures

| Condition | Seed | Case | Recorded failure | Consequence |
|---|---|---|---|---|
| Single | 11 | `V7-0021` | `single:policy_validation`; wrong `crowd.distance_between_people_m` band | Safe fallback |
| Single | 42 | `V7-0021` | Same band policy violation | Safe fallback |
| Single | 77 | `V7-0021` | Same band policy violation | Safe fallback |
| Multi | 11 | `V7-0021` | `crowd:policy_validation`; wrong distance band | Safe fallback |
| Multi | 42 | `V7-0021` | Same distance band violation | Safe fallback |
| Multi | 42 | `V7-0005` | `crowd:policy_validation`; wrong distance band | Safe fallback |

For Multi seed 77, `V7-0021` is recorded as an abstention with a valid trace, not as a schema failure. Do not count it as an invalid output. These failures are about conversion of distance observations to policy bands, not a demonstrated failure of real-world crowd-risk recognition.

## 3. Paired comparison and explanation

Across **108 matched case × seed pairs**, both conditions make the correct accepted decision in **86**, only Single does so in **1**, only Multi in **0**, and neither in **21**. The single Single-only case is `V7-0005`, seed 42, when Multi's crowd specialist exhausts validation retries.

The extra Multi-Agent call structure creates more specialist reports that must pass the same policy validator. The treatment has roughly three times the model calls and latency. This is a design trade-off, not evidence that the Single-Agent is universally better. The sample consists of only 36 unique synthetic cases reused over three seeds; differences this small do not justify statistical superiority claims.

## 4. First-attempt component errors

| Metric before retry | Single-Agent | Multi-Agent |
|---|---:|---:|
| Correct observed field bands | 718 / 723 (99.31%) | 705 / 711 (99.16%) |
| Entire initial report correct | 103 / 108 (95.37%) | 312 / 318 (98.11%) |

Different denominators matter: each Multi run may contain three specialist reports. These metrics are calculated on raw first-attempt model responses and reflect report-level policy adherence. After validation, accepted bands must match the policy, so post-validation band accuracy is conditional by construction.

## 5. Limitations and responsible use

- The reference labels derive from the same illustrative policy used to check outputs. Conditional accepted accuracy cannot validate real-world risk detection.
- The same cases appear across three seeds; mean ± SD summarize repeated runs, not independent samples.
- Gemini seed and timing are not guaranteed reproducible across hosted-model runs; the saved records can be scored offline.
- Multi has three specialist reports and up to one retry per report, while Single has one generalist report and up to one retry. This structural difference can affect failure opportunities, API calls and latency.
- These simulated outputs are advisory; they are not real Hajj crowd-management instructions. No live crowd data, train control or automated operational decisions are involved.

**Conclusion:** Both systems are highly policy-consistent when a decision is accepted, but the saved evidence shows **no Multi-Agent advantage** in coverage. Multi incurs higher resource cost, and the difference in accepted coverage is one matched run.
