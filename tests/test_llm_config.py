from dagintel.llm import dagintel_backend, llm_max_tokens, llm_temperature, on_huggingface_space_from


def test_space_forces_hf_inference():
    env = {"SPACE_ID": "x/y", "DAGINTEL_BACKEND": "anthropic"}
    assert dagintel_backend(env, hostname="localhost") == "hf_inference"


def test_force_local_allows_backend_choice():
    env = {"DAGINTEL_FORCE_LOCAL_BACKEND": "1", "DAGINTEL_BACKEND": "vllm"}
    assert dagintel_backend(env, hostname="spaces-123") == "vllm"


def test_backend_aliases():
    env = {"DAGINTEL_FORCE_LOCAL_BACKEND": "1", "DAGINTEL_BACKEND": "qwen"}
    assert dagintel_backend(env, hostname="my-laptop") == "hf_inference"


def test_default_backend():
    env = {"DAGINTEL_FORCE_LOCAL_BACKEND": "1"}
    assert dagintel_backend(env, hostname="dev") == "hf_inference"


def test_on_huggingface_space_from_hostname():
    env = {}
    assert on_huggingface_space_from(env, "spaces-abc-1") is True
    assert on_huggingface_space_from(env, "hf-space-foo") is True
    assert on_huggingface_space_from(env, "my-macbook") is False


def test_llm_temperature_max_tokens_defaults(monkeypatch):
    monkeypatch.delenv("DAGINTEL_LLM_TEMPERATURE", raising=False)
    monkeypatch.delenv("DAGINTEL_LLM_MAX_TOKENS", raising=False)
    assert llm_temperature() == 0.3
    assert llm_max_tokens() == 2048
