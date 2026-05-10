"""Shared helpers for Gradio and Streamlit entrypoints (also used by tests)."""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def max_user_log_chars() -> int:
    """Max characters accepted from paste or file before sending to `investigate` (UI-level guard)."""
    return _env_int("DAGINTEL_MAX_USER_LOG_CHARS", 500_000)


def max_display_chars() -> int:
    """Cap for on-screen Code/Markdown blocks (full text available via report download)."""
    return _env_int("DAGINTEL_MAX_DISPLAY_CHARS", 80_000)


def truncate_for_display(text: str, limit: int | None = None) -> tuple[str, bool]:
    """Truncate long agent output for UI widgets. Returns (text, was_truncated)."""
    if not text:
        return "", False
    lim = limit if limit is not None else max_display_chars()
    if len(text) <= lim:
        return text, False
    head = max(0, lim // 2 - 120)
    tail = max(0, lim - head - 100)
    banner = (
        f"\n\n[... display truncated: {len(text)} chars; "
        f"download full report .md or raise DAGINTEL_MAX_DISPLAY_CHARS ...]\n\n"
    )
    return text[:head] + banner + text[-tail:], True


def format_investigation_report_md(
    raw_logs: str,
    parse_out: str,
    diagnose_out: str,
    fix_out: str,
    *,
    elapsed_seconds: float | None = None,
    error_code: str | None = None,
    dagintel_version: str = "",
) -> str:
    """Single .md bundle for download (not truncated)."""
    meta = []
    if dagintel_version:
        meta.append(f"**DAGIntel package:** `{dagintel_version}`")
    if elapsed_seconds is not None:
        meta.append(f"**Elapsed:** {elapsed_seconds:.2f}s")
    if error_code:
        meta.append(f"**Error code:** `{error_code}`")
    meta_block = "\n\n".join(meta).strip()
    lead = f"{meta_block}\n\n---\n\n" if meta_block else "---\n\n"

    return (
        f"# DAGIntel investigation report\n\n{lead}"
        "## Raw input logs\n\n```text\n{raw_logs}\n```\n\n"
        f"## Parse (log analyzer)\n\n```json\n{parse_out}\n```\n\n"
        f"## Root cause\n\n{diagnose_out}\n\n"
        f"## Fix / runbook\n\n{fix_out}\n"
    )


def write_temp_report_md(content: str) -> str | None:
    """Write UTF-8 markdown to a temp file; return path for Gradio File, or None if empty."""
    if not (content or "").strip():
        return None
    import tempfile

    fd, path = tempfile.mkstemp(prefix="dagintel_", suffix=".md", text=False)
    with open(fd, "wb") as f:
        f.write(content.encode("utf-8"))
    return path


def parse_dag_context(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else {"value": out}
    except json.JSONDecodeError:
        return {"notes": text}


_inv_lock = threading.Lock()
_inv_times: deque[float] = deque()


def investigation_rate_allow() -> tuple[bool, str]:
    """
    Process-wide sliding window (best-effort, in-memory).
    Set DAGINTEL_RATE_LIMIT_PER_HOUR to a positive integer to enable; unset or 0 = disabled.
    """
    limit = _env_int("DAGINTEL_RATE_LIMIT_PER_HOUR", 0)
    if limit <= 0:
        return True, ""
    now = time.time()
    window = 3600.0
    with _inv_lock:
        while _inv_times and now - _inv_times[0] > window:
            _inv_times.popleft()
        if len(_inv_times) >= limit:
            return False, (
                f"Rate limit: at most {limit} investigations per hour in this session. "
                "Try again later or raise DAGINTEL_RATE_LIMIT_PER_HOUR."
            )
        _inv_times.append(now)
    return True, ""


def truncate_user_log(logs: str) -> tuple[str, bool]:
    """
    If logs exceed the UI limit, keep head and tail (same idea as crew `textutil.truncate_log`).
    Returns (text, was_truncated).
    """
    if not logs:
        return "", False
    limit = max_user_log_chars()
    if len(logs) <= limit:
        return logs, False
    head_frac = 0.35
    head = max(0, int(limit * head_frac) - 100)
    tail = max(0, limit - head - 150)
    banner = (
        f"\n\n[... log truncated at UI: original {len(logs)} chars; "
        f"raise DAGINTEL_MAX_USER_LOG_CHARS if needed ...]\n\n"
    )
    return logs[:head] + banner + logs[-tail:], True
