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
