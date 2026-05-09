# DAGIntel

Multi-agent Airflow incident triage (**CrewAI** + **Qwen** via Hugging Face Inference or local vLLM).

**Repos**

- **GitHub:** [github.com/madhukoseke/DAGIntel](https://github.com/madhukoseke/DAGIntel) (this source tree)
- **Hugging Face Space (hackathon org):** [lablab-ai-amd-developer-hackathon / DAGIntel-airflow-investigator](https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/DAGIntel-airflow-investigator)

The HF Space directory is **not** committed here (it uses its own `git` remote). After editing this repo, run `./scripts/sync_hf_space.sh` from the project root, then commit and push inside your HF clone.

## Run locally

```bash
cd DAGIntel
pip install -r requirements.txt
# Gradio (root app.py)
python app.py
# or Streamlit
streamlit run app/streamlit_app.py
```

## Hugging Face Space

- Tab title and in-app copy come from this repo’s `app.py` / README frontmatter (**DAGIntel**).
- If the **Space name** at the top of huggingface.co still says something else (e.g. an old name), change it under **Space Settings → Space name** — that label is **not** controlled by git.

## Layout

- `src/dagintel/` — Python package (crew, agents, LLM routing).
- `app/streamlit_app.py` — Streamlit UI.
- `app.py` — Gradio UI (used by HF Spaces in this layout).
- `hf-space/` — mirror for Space deploys.
