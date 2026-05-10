# DAGIntel

Documentation for the **DAGIntel** source repository: a small Python application that assists with **Apache Airflow**–style log triage using multiple LLM-backed agents.

---

## Overview

**DAGIntel** accepts **raw task or scheduler log text** (plus optional structured context), runs a **fixed sequence of three agents**, and returns three text artifacts: a structured-style parse, a root-cause style analysis, and suggested remediation notes. It is intended as a **prototype** for first-pass triage, not as a certified incident management system.

The same codebase supports:

- **Local or private** execution with configurable LLM routing.
- **Hugging Face Spaces** deployment via **Gradio**, with inference constrained to **Hugging Face Inference API** credentials supplied as Space secrets.

---

## Features

- **Three sequential agents** (CrewAI): log analysis, root-cause reasoning, fix / runbook suggestions.
- **Input modes**: built-in JSON **scenarios**, **pasted** log text, or **uploaded** plain-text files (Gradio UI).
- **Optional DAG context** for custom runs: JSON object or free-text notes, parsed in application code.
- **Dual UI**: **Gradio** (`app.py`) and **Streamlit** (`app/streamlit_app.py`).
- **Script** to run **Qwen** behind an OpenAI-compatible **vLLM** server (`scripts/serve_qwen3.sh`) when you host the model yourself (for example on AMD GPU hosts with ROCm).

---

## How it works

1. The UI collects **log text** and optional **context**.
2. `dagintel.crew.investigate()` builds three **CrewAI** `Agent` instances sharing one **LLM** instance from `dagintel.llm.get_llm()`.
3. Three **CrewAI** `Task` objects are chained: parse → diagnose → fix; each later task receives prior task outputs as **context**.
4. `Crew.kickoff()` runs tasks **sequentially**. Results are surfaced as strings in the UI.

On **Hugging Face Spaces**, `get_llm()` detects the Space runtime and **only** instantiates the **Hugging Face Inference** backend (`huggingface/<model_id>` via LiteLLM). Other backends are available **outside** that environment (see Configuration).

### Architecture (ASCII)

Execution path from user input through the crew to UI output (monospace; read left-to-right, top-to-bottom):

```text
  +---------------------------+
  | Gradio or Streamlit       |
  | scenario | paste | file  |
  +-------------+-------------+
                |
                v        raw_logs + optional dag_context
  +-----------------------------+
  | dagintel.crew.investigate() |
  | Crew(process=sequential)    |
  +-----------------------------+
                |
    +-----------+-----------+-----------+
    v           v           v           v
 +------+   +------+   +------+   +------------------+
 |Agent |   |Task 1|   |Task 2|   | Task 3           |
 | x 3  |   |parse |-->|diagnose|-->| fix            |
 +---+--+   +---+--+   +---+--+   +---+--------------+
     |          |          |          |
     +----------+----------+----------+
                |
                v
     +-------------------------+
     | LiteLLM -> configured   |
     | model (e.g. Qwen on HF  |
     | Inference, or vLLM API) |
     +-------------------------+
                |
                v
     +-------------------------+
     | UI: three result strings|
     | (parse, diagnose, fix)  |
     +-------------------------+
```

---

## Repository layout

- **`src/dagintel/`** — Python package: `crew`, `agents`, `tasks`, `textutil`, `ui_helpers`, `llm`, `scenarios`, `telemetry`, and `prompts/`.
- **`scenarios/`** — JSON fixtures for the sample scenario picker.
- **`app.py`** — Gradio entrypoint (used by Hugging Face Spaces).
- **`app/streamlit_app.py`** — Streamlit entrypoint.
- **`hf-space/`** — Supplementary files for Hugging Face packaging; the canonical application code lives at the paths above.
- **`scripts/serve_qwen3.sh`** — Example command line to start a **vLLM** OpenAI-compatible server.
- **`scripts/sync_hf_space.sh`** — Copies selected artifacts into a local clone of the Space repository (see Hugging Face Space).
- **`.env.example`** — Documented environment variables for local configuration.
- **`pyproject.toml`** — Ruff lint configuration (per-file ignores for `app.py` path bootstrap).

---

## System requirements

- **Python** 3.11 or newer (3.11 is the version used in the Hugging Face Space metadata).
- Network access to whichever **LLM endpoint** you configure.
- For the **Space**: a **Hugging Face** account with permission to push to the target Space, and a **read token** with **Inference API** scope stored as secret **`HF_TOKEN`**.

---

## Dependencies

Pinned or lower-bounded versions are listed in **`requirements.txt`**. Principal libraries:

- **crewai** 0.95.0 — multi-agent orchestration.
- **crewai-tools** 0.25.8 — transitive tooling for CrewAI.
- **langchain-openai** 0.2.14 — OpenAI-compatible client surface used by the stack.
- **litellm** ≥ 1.55.0 — provider routing for completions (Hugging Face, OpenAI-compatible servers, etc.).
- **streamlit** 1.40.2 — optional local UI.
- **gradio** ≥ 4.44.1, &lt; 6 — Space UI.
- **pydantic** 2.10.4 — configuration models (CrewAI / tooling).
- **python-dotenv** 1.0.1 — load `.env` in development.
- **huggingface-hub** 0.27.0 — Hub client utilities.
- **fastapi** 0.115.6 / **uvicorn** 0.34.0 — pulled as dependencies; not required for the core demo path.
- **rich** 13.9.4, **requests** 2.32.3 — supporting libraries.

---

## Configuration

Copy **`.env.example`** to **`.env`** for local work. Important variables:

- **`DAGINTEL_BACKEND`** — `hf_inference` (default), `vllm`, or `anthropic` (local only; ignored on Hugging Face Spaces).
- **`HF_TOKEN`** / **`HUGGING_FACE_HUB_TOKEN`** — required for `hf_inference`.
- **`HF_MODEL`** — Hub model id for the text model (default: `Qwen/Qwen2.5-7B-Instruct`). Must be **enabled for Inference** on your plan; large or preview models often return `model_not_supported` on serverless — pick a smaller model from the model card or [HF Models](https://huggingface.co/models) with inference available.
- **`VLLM_BASE_URL`**, **`VLLM_MODEL`** — when `DAGINTEL_BACKEND=vllm`.
- **`ANTHROPIC_API_KEY`**, **`ANTHROPIC_MODEL`** — when `DAGINTEL_BACKEND=anthropic` (local only).
- **`DAGINTEL_MAX_LOG_IN_PROMPT`** — max characters of raw log embedded in the parse task (default `120000`); longer logs keep head and tail with a marker.
- **`DAGINTEL_MAX_CONTEXT_JSON_CHARS`** — max characters for serialized optional DAG context JSON in the parse task (default `8000`).
- **`DAGINTEL_CREW_VERBOSE`** — `true` / `false` to force CrewAI verbose logging; default is quiet on Hugging Face Spaces and verbose elsewhere.
- **`DAGINTEL_KICKOFF_TIMEOUT_SEC`** — optional wall-clock timeout for the whole crew `kickoff()` (thread pool; best-effort). Unset = no limit.
- **`DAGINTEL_MAX_USER_LOG_CHARS`** — max characters Gradio/Streamlit accept from paste or file before calling `investigate` (default `500000`).
- **`DAGINTEL_MAX_DISPLAY_CHARS`** — max characters shown in each result panel before head/tail truncation (default `80000`); use the **Download** report for the full text.
- **`DAGINTEL_RATE_LIMIT_PER_HOUR`** — optional process-wide cap on investigation runs per hour (`0` or unset = disabled).
- **`DAGINTEL_LLM_TEMPERATURE`** — float passed to CrewAI `LLM` (default `0.3`).
- **`DAGINTEL_LLM_MAX_TOKENS`** — integer max tokens per completion (default `2048`).
- **`DAGINTEL_ENABLE_LOG_TOOLS`** — set to `1`/`true` to give the **log analyzer** agent an offline **`extract_airflow_log_signals`** regex tool (`0`/unset = disabled, default latency-friendly on Spaces).
- **`DAGINTEL_LOG_ANALYZER_MAX_ITER`** — when log tools are on, CrewAI **`max_iter`** for that agent (default `6`).
- **`DAGINTEL_LOG_TOOL_MAX_INPUT`** / **`DAGINTEL_LOG_TOOL_LIST_CAP`** — cap tool input bytes and extracted list sizes (defaults `200000` and `12`).

See **`src/dagintel/llm.py`** for authoritative behavior, including Space detection and backend forcing (`dagintel_backend()` is testable with an explicit env mapping).

### Makefile shortcuts

From the repo root (after `make install-dev`):

- **`make test`** — `pytest`
- **`make lint`** — `ruff check`
- **`make run-gradio`** / **`make run-streamlit`** — local UIs
- **`make sync-space`** — copy into `hf-space/DAGIntel-airflow-investigator/` (requires that clone; see Hugging Face Space section)
- **`make sync-space-dry`** / **`./scripts/sync_hf_space.sh --dry-run`** — rsync plan only, no writes

### Parse task JSON contract

The first crew task asks the log analyzer for **one JSON object** (no markdown fences) with:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string or null | Airflow task id if found |
| `dag_id` | string or null | DAG id if found |
| `run_id` | string or null | Run id if found |
| `try_number` | number or null | Try number if found |
| `error_class` | string | Short label (e.g. `KubernetesOOM`, `SensorTimeout`) |
| `error_category` | string | `operator`, `infrastructure`, `dependency`, `data`, `configuration`, or `unknown` |
| `summary` | string | Short human summary |
| `evidence_lines` | string[] | Short supporting excerpts from the log |
| `confidence` | string | `high`, `medium`, or `low` |

Optional **DAG context** from the UI is included in the parse task prompt; ids there are treated as authoritative when the log does not contradict them.

### Editable install (optional)

For tooling that expects a package root:

```bash
pip install -e ".[dev]"
```

Runtime dependencies still come from **`requirements.txt`**; the `[project]` section in **`pyproject.toml`** documents **`dagintel`** metadata and optional **`dev`** extras.

---

## Installation

```bash
cd DAGIntel
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys and endpoints.
```

---

## Running the application

**Gradio (default for Hugging Face Spaces):**

```bash
python app.py
```

By default the server listens on port **7860**, or the process environment variable **`PORT`** if set.

**Streamlit:**

```bash
streamlit run app/streamlit_app.py
```

---

## Hugging Face Space

The public demo is maintained in a **separate Git repository** (Hugging Face remote), not as a subdirectory of this GitHub tree:

[lablab-ai-amd-developer-hackathon / DAGIntel-airflow-investigator](https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/DAGIntel-airflow-investigator)

To refresh that clone from this monorepo after local edits:

```bash
./scripts/sync_hf_space.sh
cd hf-space/DAGIntel-airflow-investigator
git add -A && git commit -m "Sync from monorepo" && git push
```

The sync script expects the Space repository to exist at **`hf-space/DAGIntel-airflow-investigator/`** with its own **`.git`** directory.

---

## Limitations

- Bundled **scenarios** are short **illustrations**; they do not replace production log corpora.
- **Model compliance** with the JSON contract is best-effort; validate parse output before automation.
- **No authentication** in the demo UI; optional in-memory **rate limit** when `DAGINTEL_RATE_LIMIT_PER_HOUR` is set.
- **No guarantee** of factual root cause: outputs are model-generated and must be reviewed by humans before operational action.

---

## License

MIT. Add a `LICENSE` file at the repository root if you require explicit license text in-tree.

---

## Source

Primary development repository: [github.com/madhukoseke/DAGIntel](https://github.com/madhukoseke/DAGIntel).

This project was initially developed in the context of the **AMD Developer Hackathon 2026**; runtime and sponsorship details are outside the scope of this document.
