"""Integration-style test: `investigate` with mocked Crew.kickoff (no live LLM)."""

from importlib import import_module

import pytest

from dagintel import llm as llm_mod
from dagintel.crew import investigate


def _fake_kickoff(self):
    for i, task in enumerate(self.tasks):
        task.output = ("parse-json", "diag-md", "fix-md")[i]
    return "mock_final"


@pytest.mark.integration
def test_investigate_mock_kickoff(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test_placeholder_for_unit_tests_only")
    monkeypatch.setenv("DAGINTEL_FORCE_LOCAL_BACKEND", "1")
    llm_mod.get_llm.cache_clear()

    crew_mod = import_module("crewai")
    monkeypatch.setattr(crew_mod.Crew, "kickoff", _fake_kickoff)

    result = investigate("sample log line", {"dag_id": "d"})
    assert result.task_outputs == ["parse-json", "diag-md", "fix-md"]
    assert result.final_output == "mock_final"
    assert result.error is None
