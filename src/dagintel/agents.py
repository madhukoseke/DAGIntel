from pathlib import Path
from crewai import Agent
from .llm import get_llm

P = Path(__file__).parent / "prompts"

def build_log_analyzer():
    return Agent(
        role="Senior SRE - Log Analyzer",
        goal="Parse raw Airflow logs into structured JSON",
        backstory="15 years parsing Airflow failures across three companies",
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=2
    )

def build_root_cause_detective():
    return Agent(
        role="Principal Data Engineer - Root Cause Detective",
        goal="Separate proximate cause from true root cause",
        backstory="12 years debugging PayPal-scale data infrastructure",
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )

def build_fix_suggester():
    return Agent(
        role="Staff Engineer - Runbook Author",
        goal="Produce production-ready fixes and runbooks",
        backstory="Writes runbooks the on-call team actually uses",
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=2
    )
