# Hajj Crowd-Risk Prioritization

**CPCS 683 — Advanced AI**  
Arwa Al-Zahrani · Atheer Al-Sharif · Batool Al-Sulami

## Project

Compare Single-Agent and Multi-Agent systems on 36 synthetic cases and 3 seeds (11, 42, 77). Both use the same risk rules.

Model: Gemini 3.5 Flash-Lite (temperature 1.0). **216 saved runs**.

## Run

Python 3.10+:

```bash
cd m5
python3 m5_finalize.py
cd ..
python3 m6/build_m6.py
```

These commands reproduce scores without an API key. New Gemini runs require `GEMINI_API_KEY`. M5 results are in `m5/results/m5_scores/`; M6 results are generated in `m6/`.

## Results

| Metric (mean ± SD) | Single-Agent | Multi-Agent |
|---|---:|---:|
| Coverage | 80.56% ± 0.00 pp | 79.63% ± 1.60 pp |
| Selective accuracy | 100% ± 0.00 pp | 100% ± 0.00 pp |
| Valid outputs | 97.22% ± 0.00 pp | 97.22% ± 2.78 pp |
| Calls per case | 1.05 ± 0.02 | 3.00 ± 0.07 |
| Latency | 3.27 ± 2.65 s | 9.56 ± 7.90 s |

First-attempt component accuracy: Single-Agent 99.31%; Multi-Agent 99.16%.

## Data

- Cases and labels: `m5/m5_data/`. Rules: `m5/m5_policy.json`.
- Model code: `m5/m5_agent.py`. Scoring: `m5/m5_finalize.py` and `m5/scoring.py`.
- Raw results: `m5/results/m5_runs.jsonl`.
- Labels are **team-defined synthetic policy labels**, not expert judgments. Results show policy compliance, not real-world Hajj safety.
- Research basis: [Samrgandi (2026)](https://doi.org/10.14569/IJACSA.2026.0170738). This is not a replication of the original dataset or model.
