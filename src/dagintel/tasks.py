from __future__ import annotations

from typing import Any

from crewai import Task

from .textutil import serialize_context, truncate_log

_PARSE_EXPECTED = """\
A single JSON object only (no markdown code fences). Fields:
- task_id (string or null)
- dag_id (string or null)
- run_id (string or null)
- try_number (number or null)
- error_class (string)
- error_category (string: operator | infrastructure | dependency | data | configuration | unknown)
- summary (string)
- evidence_lines (array of strings)
- confidence (string: high | medium | low)
"""

_DIAGNOSE_EXPECTED = """\
Markdown with these exact ## headings: Proximate cause, Root cause, Evidence, Confidence, Falsification.
"""

_FIX_EXPECTED = """\
Markdown with these exact ## headings: Immediate fix, Permanent fix, Detection, Runbook.
"""


def build_parse_logs_task(agent, logs: str, ctx: dict[str, Any] | None):
    ctx = ctx or {}
    log_body, truncated = truncate_log(logs or "")
    ctx_block = serialize_context(ctx)
    trunc_note = "\n\nNote: log text was truncated for prompt size; prioritize visible head and tail.\n" if truncated else ""

    description = f"""\
## Role
You are the log analyzer for an Airflow incident. Follow the instructions in your backstory.

## DAG context (JSON)
{ctx_block}

## Raw log text
{log_body}
{trunc_note}
## Task
Produce the JSON object specified in Expected output. Use DAG context when the log omits ids but context supplies them.
"""
    return Task(
        description=description.strip(),
        expected_output=_PARSE_EXPECTED.strip(),
        agent=agent,
    )


def build_diagnose_task(agent, pt: Task):
    return Task(
        description="""\
## Role
You are the root-cause detective. Follow the instructions in your backstory.

## Task
Using the prior agent's JSON parse (in context) and the same incident context, write the diagnosis in the Markdown structure specified in Expected output.
""".strip(),
        expected_output=_DIAGNOSE_EXPECTED.strip(),
        agent=agent,
        context=[pt],
    )


def build_fix_task(agent, pt: Task, dt: Task):
    return Task(
        description="""\
## Role
You are the fix and runbook author. Follow the instructions in your backstory.

## Task
Using the parse (JSON) and diagnosis (Markdown) in context, produce remediation in the Markdown structure specified in Expected output.
""".strip(),
        expected_output=_FIX_EXPECTED.strip(),
        agent=agent,
        context=[pt, dt],
    )
