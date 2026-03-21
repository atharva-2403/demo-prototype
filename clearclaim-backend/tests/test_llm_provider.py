import pytest
import os
from ai.llm_provider import get_llm_provider, AnthropicProvider, OpenAIProvider, GeminiProvider

def test_factory_returns_anthropic_default(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    provider = get_llm_provider()
    assert isinstance(provider, AnthropicProvider)

def test_factory_returns_correct_providers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_key")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_key")

    assert isinstance(get_llm_provider("anthropic"), AnthropicProvider)
    assert isinstance(get_llm_provider("openai"), OpenAIProvider)
    assert isinstance(get_llm_provider("gemini"), GeminiProvider)

def test_factory_respects_env_variable(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    
    provider = get_llm_provider() # no arg, uses env
    assert isinstance(provider, OpenAIProvider)

def test_anthropic_missing_key_raises_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable is not set"):
        get_llm_provider("anthropic")

def test_openai_missing_key_raises_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is not set"):
        get_llm_provider("openai")

def test_gemini_missing_key_raises_error(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is not set"):
        get_llm_provider("gemini")