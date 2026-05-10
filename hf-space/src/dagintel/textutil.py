"""Text helpers for crew task prompts: DAG context serialization and log truncation."""

from __future__ import annotations

import json
import os
from typing import Any


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def max_context_json_chars() -> int:
    return _env_int("DAGINTEL_MAX_CONTEXT_JSON_CHARS", 8000)


def max_log_in_prompt_chars() -> int:
    return _env_int("DAGINTEL_MAX_LOG_IN_PROMPT", 120_000)


def serialize_context(ctx: dict[str, Any] | None, max_chars: int | None = None) -> str:
    """Pretty-print DAG context for inclusion in task text. Truncates with a clear marker."""
    if not ctx:
        return "(no DAG context provided; infer only from log text)"
    limit = max_chars if max_chars is not None else max_context_json_chars()
    try:
        text = json.dumps(ctx, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = json.dumps({"_serialization_error": "context was not JSON-serializable"})
    if len(text) <= limit:
        return text
    head = max(0, limit // 2 - 80)
    tail = max(0, limit - head - 120)
    return (
        text[:head]
        + "\n\n[... context JSON truncated by DAGIntel; "
        f"DAGINTEL_MAX_CONTEXT_JSON_CHARS≈{limit} ...]\n\n"
        + text[-tail:]
    )


def truncate_log(logs: str, max_total: int | None = None, head_frac: float = 0.35) -> tuple[str, bool]:
    """
    If logs exceed max_total characters, keep the start and end (Airflow errors often at tail).
    Returns (possibly_truncated_text, was_truncated).
    """
    if not logs:
        return "", False
    limit = max_total if max_total is not None else max_log_in_prompt_chars()
    if len(logs) <= limit:
        return logs, False
    head = max(0, int(limit * head_frac) - 100)
    tail = max(0, limit - head - 150)
    banner = (
        f"\n\n[... log truncated: original {len(logs)} chars; "
        f"showing first ~{head} and last ~{tail}; "
        f"adjust DAGINTEL_MAX_LOG_IN_PROMPT if needed ...]\n\n"
    )
    out = logs[:head] + banner + logs[-tail:]
    return out, True
