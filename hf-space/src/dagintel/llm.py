from __future__ import annotations

import os
import socket
from functools import lru_cache

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

# "qwen" on HF Inference is wired the same as hf_inference (litellm huggingface/* provider).
_BACKEND_ALIASES = {
    "qwen": "hf_inference",
    "hf": "hf_inference",
    "huggingface": "hf_inference",
}


def _on_huggingface_space() -> bool:
    """True when running inside a Hugging Face Space (public or private).

    On Spaces we always use Hugging Face Inference API + HF_TOKEN so visitors cannot
    trigger paid Anthropic (or arbitrary vLLM) usage via repo secrets / env mistakes.
    """
    if os.getenv("DAGINTEL_FORCE_LOCAL_BACKEND") == "1":
        return False
    if os.getenv("SPACE_HOST", "").strip():
        return True
    if os.getenv("SPACE_ID", "").strip():
        return True
    if (os.getenv("SYSTEM") or "").lower() == "spaces":
        return True
    host = socket.gethostname().lower()
    if "hf-space" in host or host.startswith("spaces-"):
        return True
    return False


def _backend_name() -> str:
    # Hosted Space: HF Inference only (Qwen / HF_MODEL); never anthropic or vLLM here.
    if _on_huggingface_space():
        return "hf_inference"

    v = os.getenv("DAGINTEL_BACKEND")
    raw = v.split("#")[0].strip().lower() if v else None
    if not raw:
        raw = "hf_inference"
    return _BACKEND_ALIASES.get(raw, raw)


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    backend = _backend_name()

    if backend == "hf_inference":
        api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if not api_key:
            raise RuntimeError(
                "HF_TOKEN not set. On Hugging Face: Space Settings → Repository secrets → "
                "add HF_TOKEN (read token with Inference API access). "
                "Locally: put HF_TOKEN in .env."
            )
        model_id = os.getenv("HF_MODEL", "Qwen/QwQ-32B-Preview").strip()
        return LLM(
            model=f"huggingface/{model_id}",
            api_key=api_key,
            temperature=0.3,
            max_tokens=2048,
        )

    if backend == "vllm":
        model = os.getenv("VLLM_MODEL", "Qwen/Qwen3-32B").strip()
        base = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1").strip().rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1"
        return LLM(
            model=f"openai/{model}",
            base_url=base,
            api_key=os.getenv("VLLM_API_KEY", "not-needed"),
            temperature=0.3,
            max_tokens=2048,
        )

    if backend == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set (DAGINTEL_BACKEND=anthropic).")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514").strip()
        if not model.startswith("anthropic/"):
            model = f"anthropic/{model}"
        return LLM(
            model=model,
            api_key=api_key,
            temperature=0.3,
            max_tokens=2048,
        )

    raise ValueError(
        f"Unknown DAGINTEL_BACKEND {backend!r}. "
        f"Use hf_inference (default), vllm, or anthropic (local only)."
    )
