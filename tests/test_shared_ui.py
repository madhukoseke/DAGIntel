from dagintel.ui_helpers import (
    investigation_rate_allow,
    parse_dag_context,
    truncate_for_display,
    truncate_user_log,
)


def test_parse_dag_context():
    assert parse_dag_context("") == {}
    assert parse_dag_context('{"a": 1}') == {"a": 1}
    assert "notes" in parse_dag_context("not json")


def test_truncate_user_log(monkeypatch):
    monkeypatch.setenv("DAGINTEL_MAX_USER_LOG_CHARS", "300")
    long = "x" * 2000
    out, t = truncate_user_log(long)
    assert t is True
    assert len(out) < len(long)


def test_rate_limit_disabled(monkeypatch):
    monkeypatch.delenv("DAGINTEL_RATE_LIMIT_PER_HOUR", raising=False)
    ok, msg = investigation_rate_allow()
    assert ok and msg == ""


def test_truncate_for_display(monkeypatch):
    monkeypatch.setenv("DAGINTEL_MAX_DISPLAY_CHARS", "200")
    text = "y" * 500
    out, truncated = truncate_for_display(text)
    assert truncated and len(out) < len(text)
    assert "display truncated" in out
