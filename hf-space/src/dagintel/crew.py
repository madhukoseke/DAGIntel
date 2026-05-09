import time
from dataclasses import dataclass, field
from crewai import Crew, Process
from .agents import build_log_analyzer, build_root_cause_detective, build_fix_suggester
from .tasks import build_parse_logs_task, build_diagnose_task, build_fix_task

@dataclass
class CrewResult:
    final_output: str
    task_outputs: list = field(default_factory=list)
    elapsed_seconds: float = 0.0

def investigate(raw_logs, dag_context):
    agents = [build_log_analyzer(), build_root_cause_detective(), build_fix_suggester()]
    parse_task = build_parse_logs_task(agents[0], raw_logs, dag_context)
    diagnose_task = build_diagnose_task(agents[1], parse_task)
    fix_task = build_fix_task(agents[2], parse_task, diagnose_task)
    tasks = [parse_task, diagnose_task, fix_task]

    crew = Crew(
        name="DAGIntel",
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    start = time.perf_counter()
    output = crew.kickoff()
    return CrewResult(
        final_output=str(output),
        task_outputs=[str(t.output) for t in tasks],
        elapsed_seconds=time.perf_counter() - start
    )

