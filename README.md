# Hajj Crowd-Risk Prioritization

**CPCS 683 — Advanced AI**  
Arwa Al-Zahrani · Atheer Al-Sharif · Batool Al-Sulami

## Study

Compare a Single-Agent with three domain specialists (Crowd, Health, Environment) using the same rules, 36 cases, and seeds 11, 42, 77. A shared **code-based** coordinator combines the reports.

**Gemini 3.5 Flash-Lite**, temperature 1.0; 216 saved runs.

## Run

Python 3.10+; no API key needed to rescore saved results:

```bash
cd m5
python3 m5_finalize.py
cd ..
python3 m6/build_m6.py
```

M5 tables: `m5/results/m5_scores/`. M6 analysis is generated in `m6/`. New Gemini inference requires `GEMINI_API_KEY`.

## Results (mean ± SD, three seeds)

| Metric | Single-Agent | Multi-Agent |
|---|---:|---:|
| Coverage | 80.56% ± 0.00 pp | 79.63% ± 1.60 pp |
| Selective accuracy | 100% ± 0.00 pp | 100% ± 0.00 pp |
| Valid reports | 97.22% ± 0.00 pp | 97.22% ± 2.78 pp |
| Calls/case | 1.05 ± 0.02 | 3.00 ± 0.07 |
| Latency (s) | 3.27 ± 2.65 | 9.56 ± 7.90 |

## Data and changes from M2/M3

- **M2 planned:** Kaggle Hajj/Umrah data (10,000 synthetic records), a weighted risk proxy, and an 80% coverage target.
- **M4 used:** Five hand-written synthetic demo cases (not Kaggle).
- **M5 used:** 36 team-written synthetic cases with an equal-weight policy (not Kaggle or expert labels). Cases and labels: `m5/m5_data/`; policy: `m5/m5_policy.json`; raw runs: `m5/results/m5_runs.jsonl`.
- **Limitations:** Coverage was measured, not fixed at 80%. Calibration, the original XGBoost model, and independent evidence verification were not implemented. Each report may be retried once.
- Scores measure agreement with our policy, not real-world safety. Selective accuracy excludes abstentions.

**Research basis:** [N. Samrgandi (2026)](https://doi.org/10.14569/IJACSA.2026.0170738). This project is not a replication of that paper's dataset or model.
