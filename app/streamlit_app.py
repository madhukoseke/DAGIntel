import platform
import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
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
)
from dagintel.telemetry import read_gpu_stats


st.set_page_config(
    page_title="DAGIntel",
    page_icon="🔍",
    layout="wide",
)

st.title("DAGIntel")
st.caption("Multi-Agent Airflow log triage. AMD Hackathon 2026 · CrewAI · LiteLLM / Qwen")

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
        row = next((s for s in scenarios if s["id"] == selected_scenario_id), None)
        if row and (row.get("anchoring_context") or "").strip():
            st.caption(row["anchoring_context"])
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
            placeholder='JSON object, e.g. {"dag_id": "my_dag", "task_id": "extract"}, or plain text.',
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
elif log_source == "Paste log":
    raw_logs_display = pasted_logs or ""
    dag_context = parse_dag_context(dag_ctx_text)
else:
    if uploaded is not None:
        raw_logs_display = uploaded.getvalue().decode("utf-8", errors="replace")
    dag_context = parse_dag_context(dag_ctx_text)

with st.expander("Raw Airflow logs (input)", expanded=bool(raw_logs_display)):
    if raw_logs_display.strip():
        st.code(raw_logs_display)
    else:
        st.info("Choose a scenario, paste a log, or upload a file, then run the investigation.")

if run:
    if not (raw_logs_display or "").strip():
        st.warning("Add log text (paste/upload) or pick a sample scenario before running.")
        st.stop()

    ok, rate_msg = investigation_rate_allow()
    if not ok:
        st.warning(rate_msg)
        st.stop()

    raw_logs_display, trunc_ui = truncate_user_log(raw_logs_display)
    if trunc_ui:
        st.info("Log was truncated before investigation (see DAGINTEL_MAX_USER_LOG_CHARS).")

    try:
        with st.spinner("Running 3-agent crew…"):
            result = investigate(raw_logs_display, dag_context)
    except Exception as e:
        st.error(str(e))
        st.stop()

    if result.error_code:
        st.warning(f"{result.error_code}: {result.error or ''}")

    prefix = f"[{result.error_code}] " if result.error_code else ""
    full_parse = prefix + result.task_outputs[0]
    full_root = prefix + result.task_outputs[1]
    full_fix = prefix + result.task_outputs[2]

    report_md = format_investigation_report_md(
        raw_logs_display,
        full_parse,
        full_root,
        full_fix,
        elapsed_seconds=result.elapsed_seconds,
        error_code=result.error_code,
        dagintel_version=dagintel_version,
    )
    st.download_button(
        label="Download full investigation (.md)",
        data=report_md.encode("utf-8"),
        file_name="dagintel_investigation.md",
        mime="text/markdown",
        use_container_width=True,
    )

    disp_p, trunc_p = truncate_for_display(full_parse)
    disp_r, trunc_r = truncate_for_display(full_root)
    disp_f, trunc_f = truncate_for_display(full_fix)
    if trunc_p or trunc_r or trunc_f:
        st.caption(
            "One or more panels are truncated for display. Use the download for the full text "
            "(DAGINTEL_MAX_DISPLAY_CHARS)."
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Log analyzer")
        st.code(disp_p)

    with col2:
        st.markdown("### Root cause")
        st.markdown(disp_r)

    with col3:
        st.markdown("### Fix suggester")
        st.markdown(disp_f)

    st.success(f"Done in **{result.elapsed_seconds:.1f}s**.")
