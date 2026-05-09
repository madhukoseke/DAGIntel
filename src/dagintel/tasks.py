from crewai import Task
def build_parse_logs_task(agent, logs, ctx):
    return Task(description=f"Parse {logs}", expected_output="JSON", agent=agent)
def build_diagnose_task(agent, pt):
    return Task(description="Diagnose", expected_output="MD", agent=agent, context=[pt])
def build_fix_task(agent, pt, dt):
    return Task(description="Fix", expected_output="MD", agent=agent, context=[pt, dt])
