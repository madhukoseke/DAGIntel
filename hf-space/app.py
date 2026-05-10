import os
import sys
from pathlib import Path

import gradio as gr

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "src"))

from dagintel import __version__ as dagintel_version
from dagintel.crew import investigate
from dagintel.scenarios import list_scenarios, load_scenario
from dagintel.ui_helpers import (
    format_investigation_report_md,
    investigation_rate_allow,
    parse_dag_context,
    truncate_for_display,
    truncate_user_log,
    write_temp_report_md,
)

# Minimal dark theme: readable sans + crisp mono for logs.
_THEME = gr.themes.Monochrome(
    font=(
        gr.themes.GoogleFont("DM Sans"),
        "ui-sans-serif",
        "system-ui",
        "sans-serif",
    ),
    font_mono=(
        gr.themes.GoogleFont("IBM Plex Mono"),
        "ui-monospace",
        "monospace",
    ),
    spacing_size="md",
    radius_size="md",
)

# Light layout polish (Gradio injects into page).
_APP_CSS = """
:root {
  --neutral-900: #0d0d0d;
}
.gradio-container h1 {
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-bottom: 0.35rem;
}
.gradio-container .prose, .gradio-container .markdown p {
  line-height: 1.55;
}
.gradio-container .block-label {
  font-weight: 500;
  letter-spacing: 0.01em;
}
footer .built-with { opacity: 0.55; }
"""

# Persisted appearance (readable on load: see demo.load js return value).
_THEME_LS_KEY = "dagintel-theme"

_JS_THEME_ON_LOAD = f"""
() => {{
    let mode = "dark";
    try {{
        mode = localStorage.getItem("{_THEME_LS_KEY}") || "dark";
    }} catch (e) {{}}
    const label = mode === "light" ? "Light" : "Dark";
    const dark = label !== "Light";
    if (dark) {{
        document.body.classList.add("dark");
        document.documentElement.style.colorScheme = "dark";
    }} else {{
        document.body.classList.remove("dark");
        document.documentElement.style.colorScheme = "light";
    }}
    return label;
}}
"""

_JS_THEME_ON_CHANGE = f"""
(choice) => {{
    const dark = choice !== "Light";
    try {{
        localStorage.setItem("{_THEME_LS_KEY}", dark ? "dark" : "light");
    }} catch (e) {{}}
    if (dark) {{
        document.body.classList.add("dark");
        document.documentElement.style.colorScheme = "dark";
    }} else {{
        document.body.classList.remove("dark");
        document.documentElement.style.colorScheme = "light";
    }}
}}
"""


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
            dag_context = parse_dag_context(dag_context_text)
        else:
            raw_logs = ""
            if uploaded_path:
                p = uploaded_path[0] if isinstance(uploaded_path, (list, tuple)) else uploaded_path
                raw_logs = Path(str(p)).read_text(encoding="utf-8", errors="replace")
            dag_context = parse_dag_context(dag_context_text)

        if not (raw_logs or "").strip():
            msg = "No log text: paste a log, upload a file, or choose a sample scenario."
            return msg, msg, msg, msg, None

        ok, rate_msg = investigation_rate_allow()
        if not ok:
            return rate_msg, rate_msg, rate_msg, rate_msg, None

        raw_logs, _trunc_ui = truncate_user_log(raw_logs)
        result = investigate(raw_logs, dag_context)
        prefix = f"[{result.error_code}] " if result.error_code else ""
        full_a = prefix + result.task_outputs[0]
        full_b = prefix + result.task_outputs[1]
        full_c = prefix + result.task_outputs[2]

        report_md = format_investigation_report_md(
            raw_logs,
            full_a,
            full_b,
            full_c,
            elapsed_seconds=result.elapsed_seconds,
            error_code=result.error_code,
            dagintel_version=dagintel_version,
        )
        report_path = write_temp_report_md(report_md)

        raw_disp, _ = truncate_for_display(raw_logs)
        d_a, _ = truncate_for_display(full_a)
        d_b, _ = truncate_for_display(full_b)
        d_c, _ = truncate_for_display(full_c)
        return raw_disp, d_a, d_b, d_c, report_path
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return error_msg, error_msg, error_msg, error_msg, None


scenarios = list_scenarios()
scenario_choices = [(s["title"], s["id"]) for s in scenarios]
_default_scenario = scenario_choices[0][1] if scenario_choices else None

HEADER_MD = """# DAGIntel

### Multi-Agent Airflow Incident Investigator

AI-assisted parse, root cause notes, and fix ideas from task logs.

*AMD Developer Hackathon 2026 · Qwen · CrewAI · ROCm / MI300X (optional host)*"""

SIDEBAR_HELP_MD = """
#### Flow

Three steps, one after the other:

1. **Log analyzer** parses the log toward structured JSON.
2. **Root cause** separates proximate vs deeper cause where possible.
3. **Fix suggester** drafts immediate checks and longer-term hardening ideas.

Uses your configured LLM (see `.env` and `dagintel.llm`).
"""

SIDEBAR_CREDIT_MD = """
**Madhu Koseke** · OneDev  
[LinkedIn](https://linkedin.com/in/madhukoseke) · [GitHub](https://github.com/madhukoseke)
"""


with gr.Blocks(
    theme=_THEME,
    css=_APP_CSS,
    title="DAGIntel",
) as demo:
    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown(HEADER_MD)
        with gr.Column(scale=1, min_width=140):
            appearance = gr.Radio(
                choices=["Dark", "Light"],
                value="Dark",
                label="Appearance",
                container=False,
            )

    demo.load(None, None, [appearance], js=_JS_THEME_ON_LOAD, show_api=False)
    appearance.change(
        None,
        inputs=[appearance],
        outputs=None,
        js=_JS_THEME_ON_CHANGE,
        show_api=False,
    )

    with gr.Row():
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("#### Input")
            log_source = gr.Radio(
                choices=["Sample scenario", "Paste log", "Upload file"],
                value="Sample scenario",
                label="Source",
                container=False,
            )
            scenario_dropdown = gr.Dropdown(
                choices=scenario_choices,
                label="Scenario",
                value=_default_scenario,
                visible=True,
            )
            scenario_hint = gr.Markdown(elem_classes=["hint"])

            paste_box = gr.Textbox(
                label="Task or scheduler log",
                lines=12,
                placeholder="Paste logs here.",
                visible=False,
            )
            upload_box = gr.File(
                label="Plain text (.log / .txt)",
                file_count="single",
                type="filepath",
                file_types=[".log", ".txt", ".out", ".err"],
                visible=False,
            )
            dag_context_box = gr.Textbox(
                label="DAG context (optional)",
                lines=2,
                placeholder='JSON {"dag_id":"..."} or short notes',
                visible=False,
            )

            def _scenario_hint(sid: str | None, src: str):
                if src != "Sample scenario" or not sid:
                    return gr.update(value="", visible=False)
                row = next((s for s in scenarios if s["id"] == sid), None)
                ac = str((row or {}).get("anchoring_context") or "").strip()
                if not ac:
                    return gr.update(value="", visible=False)
                return gr.update(value=f"*{ac}*", visible=True)

            def _toggle_inputs(src, sid):
                is_sample = src == "Sample scenario"
                hint = _scenario_hint(sid if is_sample else None, src)
                return (
                    gr.update(visible=is_sample),
                    hint,
                    gr.update(visible=src == "Paste log"),
                    gr.update(visible=src == "Upload file"),
                    gr.update(visible=not is_sample),
                )

            log_source.change(
                fn=_toggle_inputs,
                inputs=[log_source, scenario_dropdown],
                outputs=[scenario_dropdown, scenario_hint, paste_box, upload_box, dag_context_box],
            )
            scenario_dropdown.change(
                fn=_scenario_hint,
                inputs=[scenario_dropdown, log_source],
                outputs=[scenario_hint],
            )
            demo.load(
                fn=_scenario_hint,
                inputs=[scenario_dropdown, log_source],
                outputs=[scenario_hint],
            )

            investigate_btn = gr.Button("Run investigation", variant="primary", size="lg")

            gr.Markdown(SIDEBAR_HELP_MD)
            gr.Markdown(SIDEBAR_CREDIT_MD)

        with gr.Column(scale=2, min_width=400):
            with gr.Accordion("Input log (verbatim)", open=True):
                raw_logs = gr.Code(label="", language=None, lines=14, elem_id="raw-logs")

            with gr.Tabs():
                with gr.TabItem("Parse"):
                    analyzer_output = gr.Code(label="", language="json", lines=18)

                with gr.TabItem("Diagnosis"):
                    detective_output = gr.Markdown()

                with gr.TabItem("Fix"):
                    fixer_output = gr.Markdown()

            gr.Markdown("**Export** Full `.md` if the tabs above look clipped.")
            report_download = gr.File(label="Download report", interactive=False)

    investigate_btn.click(
        fn=run_investigation,
        inputs=[log_source, scenario_dropdown, paste_box, upload_box, dag_context_box],
        outputs=[raw_logs, analyzer_output, detective_output, fixer_output, report_download],
    )

    FOOTER_MD = f"""
#### Stack

- **LLM:** any provider you wire through LiteLLM (e.g. Qwen)
- **Agents:** CrewAI
- **GPU:** AMD MI300X + ROCm (optional)
- **UI:** Gradio

#### Why DAGIntel exists

Late-night failures mean long hours in logs before anyone writes clear next steps.
DAGIntel is a faster first pass: structure the error, sanity-check hypotheses, and draft remediation text you still review before acting.

**If this Space was useful, leave a rating on Hugging Face.**

*`dagintel` package version {dagintel_version}*
"""

    gr.Markdown(FOOTER_MD)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
