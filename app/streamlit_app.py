import json
import platform
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dagintel.crew import investigate
from dagintel.scenarios import list_scenarios, load_scenario
from dagintel.telemetry import read_gpu_stats


def _parse_dag_context(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else {"value": out}
    except json.JSONDecodeError:
        return {"notes": text}


st.set_page_config(
    page_title="DAGIntel",
    page_icon="🔍",
    layout="wide",
)

st.title("DAGIntel")
st.caption("AMD Developer Hackathon 2026 · CrewAI + Qwen (HF Inference / local)")

with st.sidebar:
    st.markdown("### Environment")
    stats = read_gpu_stats()
    for label, value in stats.display.items():
        st.metric(label, value)
    st.caption(platform.platform()[:120])

    st.markdown("---")
    st.markdown("### Logs")
    log_source = st.radio(
        "Log source",
        ("Sample scenario", "Paste log", "Upload file"),
        horizontal=False,
    )

    scenarios = list_scenarios()
    selected_scenario_id = None
    pasted_logs = ""
    uploaded = None

    if log_source == "Sample scenario":
        selected_scenario_id = st.radio(
            "Incident",
            [s["id"] for s in scenarios],
            format_func=lambda i: next(s["title"] for s in scenarios if s["id"] == i),
        )
    elif log_source == "Paste log":
        pasted_logs = st.text_area(
            "Airflow / task log",
            height=220,
            placeholder="Paste scheduler / worker / task logs here…",
        )
    else:
        uploaded = st.file_uploader(
            "Log file",
            type=["log", "txt", "out", "err"],
            help="Plain-text log (UTF-8).",
        )

    if log_source != "Sample scenario":
        dag_ctx_text = st.text_area(
            "DAG context (optional)",
            height=80,
            placeholder='JSON object, e.g. {"dag_id": "my_dag", "task_id": "extract"} — or free text.',
        )
    else:
        dag_ctx_text = ""

    run = st.button("Run investigation", type="primary", use_container_width=True)

# Resolve logs + context for preview + run
raw_logs_display = ""
dag_context: dict = {}

if log_source == "Sample scenario":
    scenario = load_scenario(selected_scenario_id)
    raw_logs_display = scenario["raw_logs"]
    dag_context = scenario.get("dag_context") or {}
    if scenario.get("anchoring_context"):
        st.caption(scenario["anchoring_context"])
elif log_source == "Paste log":
    raw_logs_display = pasted_logs or ""
    dag_context = _parse_dag_context(dag_ctx_text)
else:
    if uploaded is not None:
        raw_logs_display = uploaded.getvalue().decode("utf-8", errors="replace")
    dag_context = _parse_dag_context(dag_ctx_text)

with st.expander("Raw Airflow logs (input)", expanded=bool(raw_logs_display)):
    if raw_logs_display.strip():
        st.code(raw_logs_display)
    else:
        st.info("Choose a scenario, paste a log, or upload a file — then run the investigation.")

if run:
    if not (raw_logs_display or "").strip():
        st.warning("Add log text (paste/upload) or pick a sample scenario before running.")
        st.stop()

    try:
        with st.spinner("Running 3-agent crew…"):
            result = investigate(raw_logs_display, dag_context)
    except Exception as e:
        st.error(str(e))
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Log analyzer")
        st.code(result.task_outputs[0])

    with col2:
        st.markdown("### Root cause")
        st.markdown(result.task_outputs[1])

    with col3:
        st.markdown("### Fix suggester")
        st.markdown(result.task_outputs[2])

    st.success(f"Done in **{result.elapsed_seconds:.1f}s**.")
