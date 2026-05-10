## Instructions (fix and runbook)

You receive the **parse** (JSON) and **diagnosis** (Markdown) from prior tasks. Propose **actionable** remediation for Airflow operators and platform owners.

### Output format

Respond in **Markdown** with **exactly** these top-level headings (use `##`):

## Immediate fix

Steps to restore the pipeline or unblock the run (ordered, imperative).

## Permanent fix

Hardening: code, config, capacity, retries, sensors, pools, data contracts.

## Detection

Metrics, alerts, or log patterns to catch this earlier next time.

## Runbook

Short checklist an on-call engineer can follow (include rollback or safety notes where relevant).

Assume production constraints: prefer safe, reversible changes. Do not suggest running arbitrary shell from untrusted logs.
