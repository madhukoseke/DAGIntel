# DAGIntel

## Why this exists

Data teams still spend a long time on the same Airflow failures: reading raw scheduler and worker logs, guessing which layer failed, searching Slack and old tickets, and only then writing a fix or runbook. That work is repetitive, but it depends on judgment that usually lives in senior engineers’ heads. **DAGIntel** is a small, end-to-end demo that automates the *first* triage pass so you get structured parsing, a reasoned hypothesis, and suggested remediation faster than starting from a blank editor.

It was built for the **AMD Developer Hackathon 2026** to show **agentic workflows** on realistic infrastructure storylines (OOM, schema drift, connection storms, sensors), using **open-weight Qwen** models and **CrewAI** orchestration—not a chat wrapper around a single prompt.

## Hackathon technology and access

The hackathon positions **AMD’s cloud AI stack** (on-demand **AMD Instinct** GPUs, **ROCm**, credits on **AMD Developer Cloud**) together with **Hugging Face** as the **model hub and deployment surface**, and asks teams to **incorporate Qwen** in a real, end-to-end app. **DAGIntel** is written to match that story: agents and orchestration on the application side, **Qwen weights resolved from the Hugging Face Hub**, a **Gradio Space** under the event organization for judges and the community, and an optional **self-hosted inference** path when you run **vLLM** (or any OpenAI-compatible server) on **ROCm-capable AMD GPU** instances—exactly the kind of workload people prototype on **AMD Developer Cloud** before hardening on-prem.

**AMD Developer Cloud** is the supported way to get cloud **AMD Instinct** capacity without owning hardware: launch a GPU-backed environment, install or pull a ROCm-ready image, and benchmark or serve models there. For this repo, that maps to hosting **Qwen** with **vLLM** (see **`scripts/serve_qwen3.sh`**) and pointing **`DAGINTEL_BACKEND=vllm`** plus **`VLLM_BASE_URL`** / **`VLLM_MODEL`** in **`.env.example`**. Official access, credits, and pay-as-you-go terms are described on AMD’s pages, not duplicated here.

Useful links: [AMD Developer Cloud overview](https://www.amd.com/en/developer/resources/cloud-access/amd-developer-cloud.html) · [How to get started on AMD Developer Cloud](https://www.amd.com/en/developer/resources/technical-articles/2025/how-to-get-started-on-the-amd-developer-cloud-.html) · [AMD AI Academy (training)](https://www.amd.com/en/developer/resources/training/amd-ai-academy.html)

**ROCm** is AMD’s open GPU compute stack—the layer that lets **PyTorch**, **vLLM**, and similar frameworks use **Instinct** hardware in those environments the same way CUDA backs NVIDIA in theirs.

Useful links: [ROCm documentation](https://rocm.docs.amd.com/) · [ROCm installation guide](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/) · [ROCm on GitHub](https://github.com/ROCm/ROCm)

**Hugging Face** is the hackathon’s **Hub + Spaces** workflow: pick a model on the Hub, build or fine-tune with your **AMD Developer Cloud** allocation when your design needs it, then **publish a Space** inside the event org and **submit that Space URL on lablab**. **DAGIntel** follows steps one, three, and four out of the box: it depends on a **Hub** model id (default **Qwen**), ships as a **Space** ([lablab-ai-amd-developer-hackathon / DAGIntel-airflow-investigator](https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/DAGIntel-airflow-investigator)), and you submit the same link per event instructions. Joining the org is required to publish there: [lablab-ai-amd-developer-hackathon on Hugging Face](https://huggingface.co/lablab-ai-amd-developer-hackathon).

Useful links: [Hugging Face Hub documentation](https://huggingface.co/docs/hub) · [Spaces documentation](https://huggingface.co/docs/hub/spaces)

**Qwen** is the incorporated open model family: all three agents call the same LiteLLM-backed configuration, defaulting to **`huggingface/Qwen/QwQ-32B-Preview`** on the public Space (serverless inference with your **`HF_TOKEN`**) or to whatever **`HF_MODEL`** you set. That satisfies the hackathon brief to use Qwen for **reasoning and workflow automation**, not only as a label in the readme.

Useful links: [Qwen on Hugging Face](https://huggingface.co/Qwen) · [Qwen documentation](https://qwen.readthedocs.io/en/latest/)

**Track fit** this submission targets **Track 1 — AI agents and agentic workflows** (CrewAI multi-agent pipeline). It is not a fine-tuning or vision track entry.

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

## Tech stack (implementation)

**CrewAI** coordinates the agents. **LiteLLM** routes completions. On the **Hugging Face Space**, inference is **always** **Qwen** (or your chosen Hub id) via the **Hugging Face Inference API** and repository secret **`HF_TOKEN`**—see **Hackathon technology and access** above. Locally you may instead point **`DAGINTEL_BACKEND=vllm`** at **vLLM** on **ROCm / AMD Instinct** (AMD Developer Cloud or your own host) using **`.env.example`**.

**Gradio** (`app.py`) is what the Space runs; **Streamlit** (`app/streamlit_app.py`) is an alternate local UI.

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
