# M6 failure analysis (offline, saved traces)

Each condition has 108 runs: 36 cases repeated over seeds 11, 42 and 77.
Abstention does not imply a wrong accepted risk label.

## single_factorized_v7

- Valid-policy abstentions: 18
- Validation/fallback failures: 3

- Seed 11, V7-0021: single:policy_validation; Observed band violates supplied policy: crowd.distance_between_people_m
- Seed 42, V7-0021: single:policy_validation; Observed band violates supplied policy: crowd.distance_between_people_m
- Seed 77, V7-0021: single:policy_validation; Observed band violates supplied policy: crowd.distance_between_people_m

## multi_factorized_v7

- Valid-policy abstentions: 19
- Validation/fallback failures: 3

- Seed 11, V7-0021: crowd:policy_validation; Observed band violates supplied policy: crowd.distance_between_people_m
- Seed 42, V7-0021: crowd:policy_validation; Observed band violates supplied policy: crowd.distance_between_people_m
- Seed 42, V7-0005: crowd:policy_validation; Observed band violates supplied policy: crowd.distance_between_people_m

Paired comparison: 86 both correct; 1 Single only; 0 Multi only; 21 neither correct, across 108 paired case-seed runs.
The same 36 cases are reused across seeds; paired runs are not 108 independent cases.
Reference labels are synthetic-policy-derived, not externally validated real-world risk labels.
