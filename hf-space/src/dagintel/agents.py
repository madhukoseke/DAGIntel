import os
from pathlib import Path

from crewai import Agent

from .llm import get_llm

P = Path(__file__).parent / "prompts"


def _log_signals_tools_enabled() -> bool:
    raw = os.environ.get("DAGINTEL_ENABLE_LOG_TOOLS", "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _prompt_md(name: str) -> str:
    path = P / name
    return path.read_text(encoding="utf-8").strip()


def build_log_analyzer():
    instructions = _prompt_md("log_analyzer.md")
    max_iter = 2
    tool_list = None
    if _log_signals_tools_enabled():
        from .tools.log_signals import ExtractAirflowLogSignalsTool

        tool_list = [ExtractAirflowLogSignalsTool()]
        raw_mi = os.environ.get("DAGINTEL_LOG_ANALYZER_MAX_ITER", "6").strip()
        try:
            max_iter = max(6, int(raw_mi))
        except ValueError:
            max_iter = 6

    return Agent(
        role="Senior SRE - Log Analyzer",
        goal="Parse raw Airflow logs into structured JSON exactly matching the task contract.",
        backstory=(
            "15 years parsing Airflow failures across three companies. "
            "You never wrap JSON in markdown fences.\n\n"
            + instructions
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=max_iter,
        **({"tools": tool_list} if tool_list else {}),
    )


def build_root_cause_detective():
    instructions = _prompt_md("root_cause.md")
    return Agent(
        role="Principal Data Engineer - Root Cause Detective",
        goal="Separate proximate cause from true root cause with testable reasoning.",
        backstory=(
            "12 years debugging PayPal-scale data infrastructure. "
            "You cite evidence and state falsifiable hypotheses.\n\n"
            + instructions
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def build_fix_suggester():
    instructions = _prompt_md("fix_suggester.md")
    return Agent(
        role="Staff Engineer - Runbook Author",
        goal="Produce production-ready fixes and runbooks with clear headings.",
        backstory=(
            "Writes runbooks the on-call team actually uses. "
            "You prefer reversible, safe changes.\n\n"
            + instructions
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )
