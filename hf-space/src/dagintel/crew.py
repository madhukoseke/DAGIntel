import concurrent.futures
import os
import time
from dataclasses import dataclass, field

from crewai import Crew, Process

from .agents import build_fix_suggester, build_log_analyzer, build_root_cause_detective
from .llm import on_huggingface_space
from .tasks import build_diagnose_task, build_fix_task, build_parse_logs_task


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return default


def crew_verbose() -> bool:
    """CrewAI `verbose` flag: env override, else quiet on HF Space, verbose elsewhere."""
    default = not on_huggingface_space()
    return _env_bool("DAGINTEL_CREW_VERBOSE", default)


def kickoff_timeout_seconds() -> float | None:
    """Optional wall-clock limit for `crew.kickoff()` (best-effort via thread pool). Unset = no limit."""
    raw = os.environ.get("DAGINTEL_KICKOFF_TIMEOUT_SEC", "").strip()
    if not raw:
        return None
    try:
        sec = float(raw)
        return sec if sec > 0 else None
    except ValueError:
        return None


def _classify_exception(exc: BaseException) -> tuple[str, str]:
    """Return (error_code, friendly_one_liner)."""
    msg = str(exc).lower()
    if isinstance(exc, TimeoutError):
        return "E_TIMEOUT", "Investigation timed out. Try a shorter log or increase DAGINTEL_KICKOFF_TIMEOUT_SEC."
    if "timeout" in msg or "timed out" in msg:
        return "E_TIMEOUT", "The model or network timed out. Retry or use a shorter log snippet."
    if "hf_token" in msg or "api_key" in msg or "authentication" in msg or "401" in msg:
        return "E_AUTH", "Authentication failed. Check HF_TOKEN / API keys in your environment."
    if "429" in msg or "rate limit" in msg:
        return "E_UPSTREAM", "The inference provider rate-limited this request. Wait and retry."
    if "connection" in msg or "connect" in msg or "name or service not known" in msg:
        return "E_UPSTREAM", "Could not reach the model endpoint. Check network and base URL settings."
    return "E_UNKNOWN", f"Investigation failed: {exc}"


@dataclass
class CrewResult:
    final_output: str
    task_outputs: list = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: str | None = None
    error_code: str | None = None


def _kickoff(crew: Crew):
    return crew.kickoff()


def investigate(raw_logs, dag_context=None):
    ctx = dag_context if isinstance(dag_context, dict) else {}
    verbose = crew_verbose()
    agents = [
        build_log_analyzer(),
        build_root_cause_detective(),
        build_fix_suggester(),
    ]
    for a in agents:
        a.verbose = verbose

    parse_task = build_parse_logs_task(agents[0], raw_logs, ctx)
    diagnose_task = build_diagnose_task(agents[1], parse_task)
    fix_task = build_fix_task(agents[2], parse_task, diagnose_task)
    tasks = [parse_task, diagnose_task, fix_task]

    crew = Crew(
        name="DAGIntel",
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
    )
    start = time.perf_counter()
    timeout = kickoff_timeout_seconds()
    try:
        if timeout:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(_kickoff, crew)
                output = fut.result(timeout=timeout)
        else:
            output = crew.kickoff()
    except TimeoutError as e:
        code, friendly = _classify_exception(e)
        elapsed = time.perf_counter() - start
        return CrewResult(
            final_output=friendly,
            task_outputs=[friendly, friendly, friendly],
            elapsed_seconds=elapsed,
            error=friendly,
            error_code=code,
        )
    except Exception as e:
        code, friendly = _classify_exception(e)
        elapsed = time.perf_counter() - start
        return CrewResult(
            final_output=friendly,
            task_outputs=[friendly, friendly, friendly],
            elapsed_seconds=elapsed,
            error=friendly,
            error_code=code,
        )

    elapsed = time.perf_counter() - start
    return CrewResult(
        final_output=str(output),
        task_outputs=[str(t.output) for t in tasks],
        elapsed_seconds=elapsed,
    )
