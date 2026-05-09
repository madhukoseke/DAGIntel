import json
import os
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dagintel.crew import investigate
from dagintel.scenarios import list_scenarios, load_scenario


def _parse_dag_context(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else {"value": out}
    except json.JSONDecodeError:
        return {"notes": text}


def run_investigation(log_source, scenario_id, pasted_logs, uploaded_path, dag_context_text):
    """Run investigation from a sample scenario, pasted log, or uploaded file."""
    try:
        dag_context_text = dag_context_text or ""
        if log_source == "Sample scenario":
            scenario = load_scenario(scenario_id)
            raw_logs = scenario["raw_logs"]
            dag_context = scenario.get("dag_context") or {}
        elif log_source == "Paste log":
            raw_logs = pasted_logs or ""
            dag_context = _parse_dag_context(dag_context_text)
        else:
            raw_logs = ""
            if uploaded_path:
                p = uploaded_path[0] if isinstance(uploaded_path, (list, tuple)) else uploaded_path
                raw_logs = Path(str(p)).read_text(encoding="utf-8", errors="replace")
            dag_context = _parse_dag_context(dag_context_text)

        if not (raw_logs or "").strip():
            msg = "No log text: paste a log, upload a file, or choose a sample scenario."
            return msg, msg, msg, msg

        result = investigate(raw_logs, dag_context)
        return (
            raw_logs,
            result.task_outputs[0],
            result.task_outputs[1],
            result.task_outputs[2],
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return error_msg, error_msg, error_msg, error_msg


scenarios = list_scenarios()
scenario_choices = [(s["title"], s["id"]) for s in scenarios]
_default_scenario = scenario_choices[0][1] if scenario_choices else None

with gr.Blocks(
    theme=gr.themes.Monochrome(),
    title="DAGIntel",
) as demo:
    gr.Markdown(
        """
# DAGIntel - Multi-Agent Airflow Incident Investigator

**Compresses 4+ hours of debugging into 90 seconds using AI agents**

Built for AMD Developer Hackathon 2026
Tech: Qwen + CrewAI + AMD MI300X + ROCm 6.2
"""
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Log input")
            log_source = gr.Radio(
                choices=["Sample scenario", "Paste log", "Upload file"],
                value="Sample scenario",
                label="Log source",
            )
            scenario_dropdown = gr.Dropdown(
                choices=scenario_choices,
                label="Scenario",
                value=_default_scenario,
                visible=True,
            )
            paste_box = gr.Textbox(
                label="Airflow / task log",
                lines=14,
                placeholder="Paste scheduler, worker, or task logs here…",
                visible=False,
            )
            upload_box = gr.File(
                label="Log file (.log, .txt, …)",
                file_count="single",
                type="filepath",
                file_types=[".log", ".txt", ".out", ".err"],
                visible=False,
            )
            dag_context_box = gr.Textbox(
                label="DAG context (optional)",
                lines=2,
                placeholder='JSON e.g. {"dag_id":"…"} or short free text',
                visible=False,
            )

            def _toggle_inputs(src):
                is_sample = src == "Sample scenario"
                return (
                    gr.update(visible=is_sample),
                    gr.update(visible=src == "Paste log"),
                    gr.update(visible=src == "Upload file"),
                    gr.update(visible=not is_sample),
                )

            log_source.change(
                fn=_toggle_inputs,
                inputs=[log_source],
                outputs=[scenario_dropdown, paste_box, upload_box, dag_context_box],
            )

            investigate_btn = gr.Button(
                "Run investigation",
                variant="primary",
                size="lg",
            )

            gr.Markdown(
                """
### How it works

**3 AI agents collaborate sequentially:**

1. **Log Analyzer** (Senior SRE) - Parses raw Airflow logs into structured JSON

2. **Root Cause Detective** (Principal DE) - Proximate vs root cause, evidence, confidence

3. **Fix Suggester** (Staff Engineer) — Immediate fix, permanent fix, detection, runbook-style guidance

Ideal deployment: Qwen-class models on AMD MI300X; CrewAI uses your configured LLM (via litellm; see `.env`).
"""
            )

            gr.Markdown(
                """
---
**Built by**: Madhu Koseke | **Team**: OneDev
**LinkedIn**: [madhukoseke](https://linkedin.com/in/madhukoseke)
**GitHub**: [madhukoseke](https://github.com/madhukoseke)
"""
            )

        with gr.Column(scale=2):
            with gr.Accordion("Raw Airflow logs (input)", open=True):
                raw_logs = gr.Code(label="", language="markdown", lines=12)

            with gr.Tabs():
                with gr.TabItem("Log Analyzer"):
                    gr.Markdown("*Structured error extraction*")
                    analyzer_output = gr.Code(label="", language="json", lines=20)

                with gr.TabItem("Root Cause Detective"):
                    gr.Markdown("*Root cause analysis*")
                    detective_output = gr.Markdown()

                with gr.TabItem("Fix Suggester"):
                    gr.Markdown("*Production-ready runbooks*")
                    fixer_output = gr.Markdown()

    investigate_btn.click(
        fn=run_investigation,
        inputs=[log_source, scenario_dropdown, paste_box, upload_box, dag_context_box],
        outputs=[raw_logs, analyzer_output, detective_output, fixer_output],
    )

    gr.Markdown(
        """
---
### Tech stack

**LLM**: Qwen (or whatever model you configure for CrewAI / litellm)
**Framework**: CrewAI + litellm
**Infrastructure**: AMD Instinct MI300X (optional local / cloud)
**Platform**: AMD Developer Cloud + ROCm 6.2
**UI**: Gradio

### Why this matters

When data pipelines fail at 2am, on-call engineers typically spend a long time on logs,
search, and write-ups. **DAGIntel** shortens the first response loop: parse, hypothesize root cause,
and suggest fixes in one run—grounded in agent roles and tasks you can tune for your org.

---

If this helps you, please like this Space — it helps the Hugging Face visibility for the hackathon.
"""
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
