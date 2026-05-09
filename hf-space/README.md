---

## title: DAGIntel - Airflow Incident Investigator  
emoji: 🔍  
colorFrom: blue  
colorTo: green  
sdk: gradio  
sdk_version: "4.44.1"  
python_version: "3.11"  
app_file: [app.py](http://app.py)  
pinned: false

# DAGIntel - Multi-Agent Airflow Incident Investigator

**Goal:** shorten first-pass Airflow triage with three CrewAI agents (log parse → root cause → fixes).

Built for **AMD Developer Hackathon 2026** · **Tech:** CrewAI, litellm, Gradio (LLM via your Space secrets / `.env`).

## How it works

1. **Log Analyzer** - structured extraction from raw logs
2. **Root Cause Detective** - proximate vs root cause, evidence, confidence
3. **Fix Suggester** - immediate / longer-term fixes and runbook-style notes

## Try it

1. Pick a scenario (e.g. OOM, schema drift).
2. Click **Run investigation**.
3. Review the three outputs in the tabs.

## Secrets

**Hugging Face Space (public or private):** the app **always** uses **Hugging Face Inference API** with your `HF_TOKEN` - it does **not** use Anthropic or vLLM there, so random visitors cannot spend third-party LLM keys.

Add `**HF_TOKEN`** (read token with Inference access) under **Settings → Repository secrets**. Optional secret `**HF_MODEL`** overrides the default `**Qwen/QwQ-32B-Preview**`.

**Local development only:** you may set `**DAGINTEL_BACKEND=vllm`** or `**anthropic**` in `.env`. On the Space, `ANTHROPIC_API_KEY` **is never used** - leave it out of Space secrets so nothing accidental gets exposed.

**Advanced:** set `**DAGINTEL_FORCE_LOCAL_BACKEND=1`** only when simulating Space detection incorrectly on a non-Space machine.

## Author

**Madhu Koseke** · Team OneDev - [LinkedIn](https://linkedin.com/in/madhukoseke) · [GitHub](https://github.com/madhukoseke)

## License

MIT