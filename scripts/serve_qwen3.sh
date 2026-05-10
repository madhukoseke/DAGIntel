#!/usr/bin/env bash
# Start a vLLM OpenAI-compatible server (ROCm/CUDA host). Override model with VLLM_MODEL.
set -euo pipefail

if ! command -v python >/dev/null 2>&1; then
  echo "python not found on PATH" >&2
  exit 1
fi

MODEL="${VLLM_MODEL:-Qwen/Qwen3-32B}"
PORT="${VLLM_SERVE_PORT:-8000}"

if [[ -n "${ROCM_PATH:-}" ]] || command -v rocm-smi >/dev/null 2>&1; then
  echo "ROCm tooling detected (optional)." >&2
fi

echo "Starting vLLM on port ${PORT} with model ${MODEL}" >&2
exec python -m vllm.entrypoints.openai.api_server --model "$MODEL" --dtype bfloat16 --port "$PORT"
