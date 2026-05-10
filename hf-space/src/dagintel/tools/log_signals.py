"""Deterministic extraction of Airflow / platform hints from log text — no network, bounded work."""

from __future__ import annotations

import json
import os
import re
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel, Field


def max_tool_input_chars() -> int:
    raw = os.environ.get("DAGINTEL_LOG_TOOL_MAX_INPUT", "").strip()
    if raw:
        try:
            return max(8_192, min(2_000_000, int(raw)))
        except ValueError:
            pass
    return 200_000


def _uniq_cap(values: list[str], cap: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        v = v.strip()
        if not v or v in seen or len(out) >= cap:
            continue
        seen.add(v)
        out.append(v)
    return out


# Allowlisted patterns only (avoid ReDoS: linear-time friendly).
_PATTERNS: dict[str, re.Pattern[str]] = {
    "dag_ids": re.compile(r"dag_id\s*=\s*([A-Za-z0-9_.\-]+)", re.IGNORECASE),
    "task_ids": re.compile(r"task_id\s*=\s*([A-Za-z0-9_.\-]+)", re.IGNORECASE),
    # run id as key=value or Airflow logical date slug
    "run_ids": re.compile(r"run_id\s*=\s*([^\s,\]\)]+)", re.IGNORECASE),
    "run_scheduled": re.compile(r"(scheduled__\S+)", re.IGNORECASE),
    "try_slash": re.compile(r"\btry\s+(\d+)\s*/\s*(\d+)\b", re.IGNORECASE),
    "try_numbers": re.compile(
        r"\b(?:try\s*number)\s*[:\s]+(\d+)\b",
        re.IGNORECASE,
    ),
    "airflow_exceptions": re.compile(r"airflow\.exceptions\.([A-Za-z_]+)", re.IGNORECASE),
    "kubectl_errors": re.compile(
        r"(OOMKilled|CrashLoopBackOff|ImagePullBackOff|CreateContainerConfigError)",
        re.IGNORECASE,
    ),
    "db_errors": re.compile(
        r"(OperationalError|InterfaceError|DBAPIError|psycopg2\.OperationalError)",
        re.IGNORECASE,
    ),
    "exit_codes": re.compile(r"\b(?:exit\s*code|ExitCode)\s*[:=]\s*(\d+)", re.IGNORECASE),
}


def extract_airflow_log_signals_dict(log_snippet: str) -> dict:
    """Return structured hints extracted with regex (for tests and tooling)."""
    if not log_snippet:
        return {"_truncated_input": False, "patterns": {}, "snippet_timestamps": []}

    max_in = max_tool_input_chars()
    truncated = len(log_snippet) > max_in
    text = log_snippet if not truncated else (
        log_snippet[: max_in // 2 - 120]
        + "\n...[tool input truncated]...\n"
        + log_snippet[-max_in // 2 + 120 :]
    )

    cap = int(os.environ.get("DAGINTEL_LOG_TOOL_LIST_CAP", "12") or "12")
    cap = max(3, min(50, cap))

    dag_ids = _PATTERNS["dag_ids"].findall(text)
    task_ids = _PATTERNS["task_ids"].findall(text)
    run_chunks = [r[:200] for r in _PATTERNS["run_ids"].findall(text)]
    run_chunks.extend(s[:200] for s in _PATTERNS["run_scheduled"].findall(text))

    tries: list[str] = []
    for m in _PATTERNS["try_slash"].finditer(text):
        tries.append(m.group(1))
    for m in _PATTERNS["try_numbers"].finditer(text):
        tries.append(m.group(1))

    airflow_ex = list(_PATTERNS["airflow_exceptions"].findall(text))
    k8s = list(_PATTERNS["kubectl_errors"].findall(text))
    db = list(_PATTERNS["db_errors"].findall(text))
    exits = [f"exit_{x}" for x in _PATTERNS["exit_codes"].findall(text)]

    # Bracket timestamps like Airflow file_task_handler lines
    ts_pat = re.compile(
        r"\[(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?)\]"
    )
    timestamps = _uniq_cap(list(ts_pat.findall(text)), min(cap, 8))

    results = {
        "dag_ids": _uniq_cap(list(dag_ids), cap),
        "task_ids": _uniq_cap(list(task_ids), cap),
        "run_ids": _uniq_cap(run_chunks, cap),
        "try_numbers": _uniq_cap(list(tries), cap),
        "airflow_exceptions": _uniq_cap(airflow_ex, cap),
        "platform_signals": _uniq_cap(k8s + db + exits, cap),
    }
    # Drop empty lists for cleaner JSON
    pruned = {k: v for k, v in results.items() if v}
    return {
        "_truncated_input": truncated,
        "patterns": pruned,
        "snippet_timestamps": timestamps,
    }


class _ExtractSignalsSchema(BaseModel):
    log_snippet: str = Field(
        ...,
        description=(
            "A portion of raw Airflow or worker log text to scan (prefer the error stanza)."
        ),
    )


class ExtractAirflowLogSignalsTool(BaseTool):
    """Regex-only extractor for DAG/task ids and common failure tokens — deterministic, offline."""

    name: str = "extract_airflow_log_signals"
    description: str = (
        "Runs fast, offline regex scans on log text you pass in. "
        "Returns JSON with dag_ids, task_ids, run_ids, try_numbers, airflow_exceptions "
        "(e.g. AirflowSensorTimeout), platform_signals (e.g. OOMKilled, DBAPIError), "
        "and snippet_timestamps from bracketed timestamps. Does not replace your final JSON parse; "
        "use alongside the full log to fill task_id/dag_id or evidence."
    )
    args_schema: type[BaseModel] = _ExtractSignalsSchema

    def _run(self, log_snippet: str) -> str:
        payload = extract_airflow_log_signals_dict(log_snippet)
        return json.dumps(payload, ensure_ascii=False)
