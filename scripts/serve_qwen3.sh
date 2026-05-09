#!/bin/bash
set -e
MODEL="${VLLM_MODEL:-Qwen/Qwen3-32B}"
python -m vllm.entrypoints.openai.api_server --model "$MODEL" --dtype bfloat16 --port 8000
