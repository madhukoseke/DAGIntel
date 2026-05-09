---
title: DAGIntel — Airflow Incident Investigator
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "4.44.1"
python_version: "3.11"
app_file: app.py
pinned: false
short_description: CrewAI agents triage Airflow logs with Qwen (HF Inference).
license: mit
---

# DAGIntel — Airflow Incident Investigator

**AMD Developer Hackathon 2026** — **Track 1** (agentic workflows): **CrewAI** agents, **Qwen** from the **Hugging Face Hub**, deployed as this **Space** per the event’s Hub → build → publish workflow. Optional **vLLM** on **AMD Instinct + ROCm** (e.g. **AMD Developer Cloud**) for self-hosted inference — see the [GitHub README](https://github.com/madhukoseke/DAGIntel#hackathon-technology-and-access).

## Try it

Use **Sample scenario**, **Paste log**, or **Upload file**, then **Run investigation**.

## Secrets

Add **`HF_TOKEN`** under **Settings → Repository secrets**. Optional **`HF_MODEL`** (Hub repo id). This Space does not use Anthropic keys for public traffic.

## Author

**Madhu Koseke** — [GitHub](https://github.com/madhukoseke/DAGIntel)
