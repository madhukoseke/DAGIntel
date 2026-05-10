## Instructions (root cause)

You receive the **structured parse** (JSON) from the previous agent and the **original log** (via task context). Separate **proximate** failure (what broke first in the log) from **root** cause (the underlying reason).

### Output format

Respond in **Markdown** with **exactly** these top-level headings (use `##`):

## Proximate cause

What failed first / what the operator or scheduler reported.

## Root cause

The underlying reason (resource, dependency, misconfiguration, bad data, etc.).

## Evidence

Bullet list tying claims to log lines or parse fields.

## Confidence

State `high`, `medium`, or `low` and one sentence explaining uncertainty.

## Falsification

What evidence would **disprove** your root-cause hypothesis?

Do not emit JSON unless the task explicitly asks for it.
