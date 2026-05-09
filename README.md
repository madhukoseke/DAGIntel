# DAGIntel

## Why this exists

Data teams still spend a long time on the same Airflow failures: reading raw scheduler and worker logs, guessing which layer failed, searching Slack and old tickets, and only then writing a fix or runbook. That work is repetitive, but it depends on judgment that usually lives in senior engineers’ heads. **DAGIntel** is a small, end-to-end demo that automates the *first* triage pass so you get structured parsing, a reasoned hypothesis, and suggested remediation faster than starting from a blank editor.

It was built for the **AMD Developer Hackathon 2026** to show **agentic workflows** on realistic infrastructure storylines (OOM, schema drift, connection storms, sensors), using **open-weight Qwen** models and **CrewAI** orchestration—not a chat wrapper around a single prompt.

## What it does

**DAGIntel** runs three **CrewAI** agents in order on the log text you provide:

1. **Log analyzer** — Treats messy Airflow-style output as input and aims to extract structured signals (task identifiers, error class, key lines) so the next step is not re-reading the same stack trace from scratch.

2. **Root cause detective** — Separates what failed first from what might be underlying (for example, exit 137 versus memory limits versus the code path that triggered them).

3. **Fix suggester** — Produces actionable notes: mitigations, checks to run, and runbook-style guidance your team can refine—not a replacement for production change management, but a strong draft after one button click.

You can drive it from **sample scenarios** checked into this repo, by **pasting** a log you already have, or by **uploading** a plain-text log file. Optional **DAG context** (JSON or short free text) can be attached for custom runs so the agents are not working only from a naked stack trace.

## Flow (ASCII)

High-level path from input to outputs (all three tasks share one LLM configuration behind CrewAI):

```text
                         +---------------------------+
                         | Gradio or Streamlit       |
                         | scenario / paste / file |
                         +-------------+-------------+
                                       |
                                       v
                            raw_logs + dag_context
                                       |
                                       v
              +------------------------------------------------+
              |              CrewAI sequential crew             |
              +------------------------------------------------+
                    |                    |                    |
                    v                    v                    v
             +-------------+      +-------------+      +-------------+
             | (1) Parse   |----->| (2) Diagnose|----->| (3) Fix     |
             |     logs    |      |     cause   |      |  suggest    |
             +------+------+      +------+------+      +------+------+
                    |                    |                    |
                    +--------------------+--------------------+
                                         |
                                         v
                              +----------+----------+
                              | LiteLLM + model     |
                              | (e.g. Qwen on HF)   |
                              +----------+----------+
                                         |
                                         v
                              +----------+----------+
                              | Analyzer JSON       |
                              | + two markdown      |
                              |   sections          |
                              +---------------------+
```

## What it is not

It does not replace your orchestrator, your on-call rotation, or your data platform’s official runbooks. It does not prove root cause against live metrics unless you wire that in yourself. The bundled scenarios are **illustrative**; production systems should use your own logs, guardrails, and review.

## Tech stack

**CrewAI** coordinates the agents. **LiteLLM** (via CrewAI’s LLM integration) routes inference. Default path for the public **Hugging Face Space** is **Qwen** through the **Hugging Face Inference API** using a repository secret **`HF_TOKEN`**. For local or private setups you can point the same code at an **OpenAI-compatible** endpoint (for example **vLLM** on AMD hardware) using environment variables described in **`.env.example`**.

The UI ships as **Gradio** (`app.py` at the repo root) for the Space, and **Streamlit** (`app/streamlit_app.py`) for a familiar local dashboard.

## Repositories

This GitHub repository is the **source of truth** for application code and scenarios.

The hackathon **Hugging Face Space** lives in a separate git remote: [lablab-ai-amd-developer-hackathon / DAGIntel-airflow-investigator](https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/DAGIntel-airflow-investigator). The Space working copy is intentionally **not** committed here. After you change this repo, run **`./scripts/sync_hf_space.sh`** from the project root, then commit and push inside your HF clone so the Space rebuilds.

## Run locally

Install dependencies, configure secrets from **`.env.example`** (never commit real tokens), then start either UI:

```bash
cd DAGIntel
pip install -r requirements.txt
python app.py
# or
streamlit run app/streamlit_app.py
```

## Project layout

**`src/dagintel/`** holds the Python package: crew wiring, agent definitions, task builders, LLM factory, and prompt stubs. **`scenarios/`** contains JSON fixtures for demo incidents. **`hf-space/`** mirrors the layout expected by Hugging Face for packaging and review. **`scripts/`** includes **`sync_hf_space.sh`** and a helper to serve Qwen with **vLLM** when you are on GPU hosts.

## License

MIT unless you add a different `LICENSE` file at the root.
