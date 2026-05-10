## Instructions (log parse)

You receive **raw Airflow-style task or scheduler log text** (and optional **DAG context** JSON in the task description). Your job is to extract a **single JSON object** as the final answer.

If **`extract_airflow_log_signals`** is available, call it once on a concise error-focused slice of the log (or on the DAG-context-augmented text) to bootstrap `dag_id` / `task_id` / `run_id` / `try_number` hints and exception class names. Then **always reconcile** against the raw log yourself; regex can miss spans or collide with incidental strings. Your Final Answer remains the single JSON object below, not tool output alone.

### Output rules

- Return **only** valid JSON (no markdown fences, no commentary before or after).
- Use `null` for unknown string fields. Use `[]` for empty lists.
- `evidence_lines` should quote short snippets from the log (each under 240 characters) that support your conclusions.

### Required JSON shape

| Field | Type | Meaning |
|-------|------|--------|
| `task_id` | string \| null | Airflow task id if identifiable |
| `dag_id` | string \| null | DAG id if identifiable |
| `run_id` | string \| null | Run / execution date id if present |
| `try_number` | number \| null | Try number if present |
| `error_class` | string | Short machine label, e.g. `AirflowException`, `Timeout`, `KubernetesOOM`, `DBAPIError`, `SensorTimeout`, `Unknown` |
| `error_category` | string | One of: `operator`, `infrastructure`, `dependency`, `data`, `configuration`, `unknown` |
| `summary` | string | One or two sentences for humans |
| `evidence_lines` | string[] | Supporting excerpts from the log |
| `confidence` | string | `high`, `medium`, or `low` |

When **DAG context** is provided, treat it as authoritative for `dag_id` / `task_id` if the log does not contradict it.
