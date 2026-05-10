from __future__ import annotations

import os
import socket
from collections.abc import Mapping
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


def _env_str(env: Mapping[str, str], key: str) -> str:
    v = env.get(key)
    if v is None:
        return ""
    return str(v).strip()


def on_huggingface_space_from(env: Mapping[str, str], hostname: str) -> bool:
    """Space detection from explicit env + hostname (test-friendly)."""
    if _env_str(env, "DAGINTEL_FORCE_LOCAL_BACKEND") == "1":
        return False
    if _env_str(env, "SPACE_HOST"):
        return True
    if _env_str(env, "SPACE_ID"):
        return True
    if _env_str(env, "SYSTEM").lower() == "spaces":
        return True
    host = (hostname or "").lower()
    if "hf-space" in host or host.startswith("spaces-"):
        return True
    return False


def on_huggingface_space() -> bool:
    """True when running inside a Hugging Face Space (public or private).

    On Spaces we always use Hugging Face Inference API + HF_TOKEN so visitors cannot
    trigger paid Anthropic (or arbitrary vLLM) usage via repo secrets / env mistakes.
    """
    return on_huggingface_space_from(os.environ, socket.gethostname())


def dagintel_backend(
    environ: Mapping[str, str] | None = None,
    *,
    hostname: str | None = None,
) -> str:
    """
    Resolve which LLM backend DAGIntel uses.

    When ``environ`` is ``None``, reads ``os.environ`` and the real hostname.
    Pass a dict (and optional ``hostname``) in unit tests.
    """
    env = os.environ if environ is None else environ
    hn = socket.gethostname() if hostname is None else hostname
    if on_huggingface_space_from(env, hn):
        return "hf_inference"

    raw = _env_str(env, "DAGINTEL_BACKEND")
    if not raw:
        raw = "hf_inference"
    raw = raw.split("#", 1)[0].strip().lower()
    return _BACKEND_ALIASES.get(raw, raw)


def _backend_name() -> str:
    return dagintel_backend()


def llm_temperature() -> float:
    raw = os.environ.get("DAGINTEL_LLM_TEMPERATURE", "0.3").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.3


def llm_max_tokens() -> int:
    raw = os.environ.get("DAGINTEL_LLM_MAX_TOKENS", "2048").strip()
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return 2048


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    backend = dagintel_backend()
    temperature = llm_temperature()
    max_tokens = llm_max_tokens()

    if backend == "hf_inference":
        api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if not api_key:
            raise RuntimeError(
                "HF_TOKEN not set. On Hugging Face: Space Settings → Repository secrets → "
                "add HF_TOKEN (read token with Inference API access). "
                "Locally: put HF_TOKEN in .env."
            )
        # Use a model your HF account can run on Serverless Inference (see HF_MODEL in .env).
        # QwQ-32B-Preview and other large models are often unavailable on the default router.
        model_id = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct").strip()
        return LLM(
            model=f"huggingface/{model_id}",
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
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
            temperature=temperature,
            max_tokens=max_tokens,
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
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(
        f"Unknown DAGINTEL_BACKEND {backend!r}. "
        f"Use hf_inference (default), vllm, or anthropic (local only)."
    )


# Backward-compatible name for callers that still import the private symbol.
_on_huggingface_space = on_huggingface_space
