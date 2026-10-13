# Hajj Risk Baseline

**Course:** CPCS 683 — Advanced Artificial Intelligence  
**Milestone:** M4 — 14 October 2026  
**Team:** Arwa Al-Zahrani, Atheer Al-Sharif, Batool Al-Sulami

## About

This project demonstrates a **single generalist LLM agent** for prioritizing **synthetic Hajj risk scenarios**. The agent uses **Gemini 3.1 Flash-Lite** through the Google Gemini API. It reviews observations about crowd conditions, health and environment, then returns LOW, MEDIUM, HIGH or ABSTAIN if reliable information is insufficient.

All five cases are handcrafted simulations, not real Hajj data. Model-generated priorities are not validated real-world safety decisions.

## Requirements

- Python 3.10 or later
- Git
- Internet access
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey)

No model download or additional Python packages are required. The Gemini API has usage quotas; check [Google's pricing and free-tier information](https://ai.google.dev/gemini-api/docs/pricing).

## Setup

**1. Clone the project** (Terminal on macOS/Linux or PowerShell on Windows):

```bash
git clone https://github.com/arwa17/CPCS683-Hajj-Risk-Baseline.git
cd CPCS683-Hajj-Risk-Baseline
```

If you already cloned the project, enter your repository folder and run `git pull`.

**2. Set your own Gemini API key.** Do not include your key in any GitHub file, screenshot or shared message.

On **macOS / Linux**:

```bash
export GEMINI_API_KEY="YOUR_KEY_HERE"
```

On **Windows PowerShell**:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
```

**3. Start the application.**

On **macOS / Linux**:

```bash
python3 -m hajj_baseline.webapp
```

On **Windows**:

```powershell
py -m hajj_baseline.webapp
```

**4. Open** http://127.0.0.1:8765 in your browser, select a case and click **Run analysis**.

The browser runs locally; only the synthetic case data is sent to Gemini over the internet. Keep the terminal running while demonstrating the application, and press `Ctrl+C` to stop. If another instance is using port 8765, stop it first.

## Demo

The interface offers five synthetic cases:
- **High indicators**
- **Mixed indicators**
- **Low indicators**
- **Missing information**
- **Conflicting information**

Run a case to display its risk priority or abstention, recommended review action and explanation. Expand **Evidence and run information** to see evidence field paths, model name, one-call trace, response time and JSON output.

## Inputs and outputs

Each case contains seven observations:

| Area | Observations |
| --- | --- |
| Crowd | Crowd density, queue time, distance |
| Health | Fatigue, stress, emergency event |
| Environment | Temperature |

Every observation includes a value, source and quality label. The agent returns **LOW, MEDIUM, HIGH, or ABSTAIN**, a review action, explanation, uncertainty notes where applicable, and supporting field references. A structured trace records one LLM call and its duration.

## Project files

| Path | Purpose |
| --- | --- |
| `hajj_baseline/agent.py` | Runs one generalist agent and records its output |
| `hajj_baseline/providers.py` | Calls the Google Gemini API |
| `hajj_baseline/schema.py` | Validates input and output structure |
| `hajj_baseline/webapp.py` | Serves the local browser demonstration |
| `examples/` | Five synthetic risk scenarios |
| `tests/test_baseline.py` | Offline tests for input, output, API transport and browser behavior |

## Repeated evaluations

The Gemini generation seed defaults to **42**. The planned evaluation seeds are **11, 42, and 77**. Set `HAJJ_SEED` before launching the app; each run records the configured seed in its trace.

**macOS / Linux:**

```bash
export HAJJ_SEED=11
python3 -m hajj_baseline.webapp
```

**Windows PowerShell:**

```powershell
$env:HAJJ_SEED="11"
py -m hajj_baseline.webapp
```

Stop the server before selecting another seed. Re-run the **same cases** for each seed and record the actual decisions, call counts and time in later milestones. Google's seed setting is a best-effort reproducibility aid, **not a guarantee of identical outputs**, and the current five demo examples are not a scored evaluation set.

## Tests

Run the tests without a live API request:

```bash
python3 -m unittest discover -s tests -v
```

On Windows, use `py -m unittest discover -s tests -v`.

The unit tests use simulated model responses; an actual Gemini API call is demonstrated by clicking **Run analysis** with a valid API key. **Output valid** means the JSON structure and evidence references passed validation, not that risk prediction accuracy has been established.

## Evaluation scope

This M4 deliverable is a **single-agent baseline**, not a multi-agent system. Full accuracy evaluation, repeated-run benchmarking and multi-agent comparisons belong to subsequent milestones. Because the baseline model is Gemini, future experimental comparisons must document that model choice consistently.
