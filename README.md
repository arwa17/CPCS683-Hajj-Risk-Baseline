# Hajj Crowd-Risk Prioritization

**CPCS 683 — Advanced AI**  
Arwa Al-Zahrani · Atheer Al-Sharif · Batool Al-Sulami

## Experiment

Compare a **Single-Agent** with a **Multi-Agent** system (Crowd, Health, Environment specialists and a coordinator) on the same 36 synthetic cases and three seeds (11, 42, 77). Both use the same risk policy and validation rules.

**Model:** Gemini 3.5 Flash-Lite · Temperature 1.0 · **216 saved runs** (108 per condition).

## Run

Python 3.10+; offline scoring requires no API key.

```bash
cd m5
python3 m5_finalize.py
cd ..
python3 m6/build_m6.py
```

M5 outputs: `m5/results/m5_scores/`. M6 comparison and failure-analysis files are generated in `m6/`.

New model runs require `GEMINI_API_KEY`. The saved experiments can be rescored without calling Gemini; exact new generations are not guaranteed to match. The runner's default model and temperature differ from the saved experiment, so set them explicitly for new runs.

## Results

| Metric (mean ± SD; 3 seeds) | Single-Agent | Multi-Agent |
|---|---:|---:|
| Decision coverage | 80.56% ± 0.00 pp | 79.63% ± 1.60 pp |
| Selective accuracy | 100.00% ± 0.00 pp | 100.00% ± 0.00 pp |
| Schema validity | 97.22% ± 0.00 pp | 97.22% ± 2.78 pp |
| Calls per case | 1.05 ± 0.02 | 3.00 ± 0.07 |
| Latency (s) | 3.27 ± 2.65 | 9.56 ± 7.90 |

**Component evaluation (first attempt):** observed-field accuracy: Single 718/723 (99.31%), Multi 705/711 (99.16%). Post-validation 100% agreement is conditional on the policy validator. Selective accuracy excludes abstentions.

## Data and limitations

- Golden cases: `m5/m5_data/test_locked_cases.jsonl`; labels: `test_locked_gold.jsonl`; integrity: `manifest.json`.
- Labels (12 LOW, 12 MEDIUM, 12 HIGH) come from the team's documented rules in `m5/m5_policy.json`, **not expert or real-world annotations**. This measures policy compliance, not actual Hajj safety.
- Raw outputs: `m5/results/m5_runs.jsonl`. Scoring: `m5/scoring.py` and `m5/m5_finalize.py`. Systems: `m5/m5_agent.py`.
- Research foundation: N. Samrgandi, *Multi-Agent Crowd-Risk Prioritization for Large-Scale Events*, [IJACSA (2026)](https://doi.org/10.14569/IJACSA.2026.0170738). This is an adaptation, not a replication of its dataset or model.
