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
short_description: CrewAI triage for Airflow logs; Qwen via HF Inference.
license: mit
---

# DAGIntel — Airflow Incident Investigator

This **Hugging Face Space** runs the **Gradio** front end for **DAGIntel**: three **CrewAI** agents analyze Airflow-style logs using **Qwen** via the **Hugging Face Inference API**. Full documentation, dependencies, and configuration are in the [GitHub repository](https://github.com/madhukoseke/DAGIntel).

## Operation

Provide logs through **sample scenarios**, **paste**, or **file upload**, then run the investigation. The Space requires secret **`HF_TOKEN`** (Inference-enabled). Optional secret **`HF_MODEL`** selects a different Hub model id.

## License

MIT (see GitHub).
