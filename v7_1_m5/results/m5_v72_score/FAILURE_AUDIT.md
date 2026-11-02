# V7.2 M5/M6 failure audit

## Scope and integrity

Source: `results/v72_35_all_seeds.jsonl`, final `results/m5_v72_score/` and frozen `v7_synthetic_data/test_locked_cases.jsonl`. Complete grid: 36 synthetic cases × Seeds 11/42/77 × Single/Multi = 216 saved rows. This is a descriptive audit of the exact finished runs; it does not modify results, thresholds, gold labels or model responses.

## Final outcomes

| Outcome | Single (108) | Multi (108) | Total |
|---|---:|---:|---:|
| Valid accepted decisions matching synthetic gold | 87 | 86 | 173 |
| Policy-justified abstentions | 18 | 19 | 37 |
| Validation-failure fallback abstentions | 3 | 3 | 6 |
| Total | 108 | 108 | 216 |

Every accepted decision was consistent with the frozen synthetic policy label. Therefore selective accuracy is 100% **among accepted decisions only**. All-case accuracy equals coverage in this run. These are not independent real-world risk labels.

## All six final validation failures

| Case | Seed | Condition | Failed stage | Cause |
|---|---:|---|---|---|
| V7-0021 | 11 | Single | single:policy_validation | Incorrect observed-distance band after regeneration |
| V7-0021 | 11 | Multi | crowd:policy_validation | Incorrect observed-distance band after regeneration |
| V7-0021 | 42 | Single | single:policy_validation | Incorrect observed-distance band after regeneration |
| V7-0021 | 42 | Multi | crowd:policy_validation | Incorrect observed-distance band after regeneration |
| V7-0021 | 77 | Single | single:policy_validation | Incorrect observed-distance band after regeneration |
| V7-0005 | 42 | Multi | crowd:policy_validation | Incorrect observed-distance band after regeneration |

All failures concern `crowd.distance_between_people_m`. Per `policy_v7.json`, the correct band is 2 for values strictly below 0.75 m and 1 for 0.75 m to below 1.5 m.

- `V7-0021`: observed distance = 0.46 m; density is noisy. Even after correcting its band to 2, the missing-density uncertainty interval crosses the LOW/MEDIUM boundary, so a valid system should still abstain. Five failures affect reported validation reliability and extra calls but do **not** cause extra missed decisions relative to the policy.
- `V7-0005`: observed distance = 0.73 m; all seven fields are observed. The correct band is 2; the expected deterministic aggregate is MEDIUM. Multi on Seed 42 returned band 1 in both attempts, creating one **avoidable validation-fallback abstention**. This is the only failure that decreased final coverage relative to the policy.

The `V7-0005` fallback uses `REQUEST_HUMAN_REVIEW` because no observation is unreliable and there is no field to request re-measurement from. This is a separately flagged system-validation failure, **not** a policy-valid uncertainty abstention.

## Five successful report repairs

| Case | Seed | Condition | Outcome |
|---|---:|---|---|
| V7-0005 | 11 | Single | Accepted MEDIUM after corrected second generation |
| V7-0005 | 77 | Multi | Accepted MEDIUM after corrected Crowd report |
| V7-0113 | 77 | Multi | Accepted HIGH after corrected Crowd report |
| V7-0123 | 77 | Single | Accepted HIGH after corrected second generation |
| V7-0123 | 77 | Multi | Accepted HIGH after corrected Crowd report |

The bounded retry prevents unvalidated outputs from being accepted, but does not guarantee that Gemini will produce a policy-compliant report. If both attempts fail, the system returns a traceable fallback abstention. API/network-level retries are a separate mechanism.

## Policy-valid abstentions

Six distinct case IDs are policy-uncertain in both conditions and all three seeds: `V7-0003`, `V7-0012`, `V7-0018`, `V7-0019`, `V7-0026`, `V7-0069` (36 runs). The remaining policy-valid abstention is `V7-0021` in Multi Seed 77 (one run). Thus **37 policy-valid abstentions**, separate from the **six** final validation failures.

## Paired comparison and limitations

Across 108 paired case-seed observations, both systems made an accepted correct decision in 86 pairs; Single-Agent alone succeeded in one pair; neither made an accepted correct decision in 21 pairs. No pair favored Multi-Agent alone. Observations from three seeds reuse the same 36 cases and are not independent cases.

The baseline comparison on this frozen synthetic set is informative for policy adherence and software behavior only. The reference labels come from the same classroom policy used by the agents and validator, not external expert annotations. Do not infer deployed Hajj operational safety, model generalization or a demonstrated Multi-Agent advantage. The V7.2 repair was targeted after earlier test failures were inspected, so version-to-version results on this set are exploratory rather than a fresh, unbiased holdout.

## Reproducible files

- `results/v72_35_all_seeds.jsonl`: original model outputs, per-run traces, raw reports, validation failures and correction attempts
- `results/m5_v72_score/per_seed.csv`: per-seed score details
- `results/m5_v72_score/mean_sd.csv`: averages and sample standard deviations
- `results/m5_v72_score/component_trajectory_per_seed.csv`: band and trajectory coverage
- `results/m5_v72_score/paired.json`: paired comparison
- `results/m5_v72_score/status.json`: complete 216/216 verified

The values above were checked against the full saved JSONL. No additional Gemini calls are required to repeat the scoring.
