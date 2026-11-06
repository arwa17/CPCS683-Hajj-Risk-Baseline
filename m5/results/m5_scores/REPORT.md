# M5 Evaluation Results

**Golden set:** 36 synthetic cases | **Baseline:** Single-Agent | **Seeds:** 11, 42, 77
**Model:** gemini-3.5-flash-lite | **Temperature:** 1 | **Runs:** 108/108 | **Status:** COMPLETE

| Baseline metric (mean ± SD across seeds) | Result |
|---|---:|
| Coverage | 80.56% ± 0.00 pp |
| Selective accuracy (accepted decisions only) | 100.00% ± 0.00 pp |
| Schema/policy validity | 97.22% ± 0.00 pp |
| Calls per case (trajectory metric) | 1.0467 ± 0.0162 |

**Component/trajectory:** Observed-field band accuracy 100.00% on valid reports; complete trajectories 97.22%.

**Scoring:** python3 m5_finalize.py (offline and reproducible).
**Limitation:** Synthetic policy-based labels; no real-world safety validation.

**First-attempt component evaluation (before validation/retry):** Single-Agent 718/723 correct observed bands (99.31%), 103/108 fully correct first-attempt reports (95.37%); Multi-Agent 705/711 correct observed bands (99.16%), 312/318 fully correct first-attempt specialist reports (98.11%). See component_trajectory_per_seed.csv for seed-level details.

**Interpretation:** Post-validation 100% accuracy is conditional on a validator using the synthetic reference policy, not real-world predictive performance. V7.2 followed inspection of V7.1 test errors; these results are exploratory/post-hoc rather than confirmatory. The stored model/temperature are Gemini 3.5 Flash-Lite/1.0, while runner defaults differ. Offline scoring is reproducible; generation with seeds is best-effort.
