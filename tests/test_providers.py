import pytest
from unittest.mock import patch, MagicMock
from providers import PROVIDERS
from providers.base import BaseProvider
from providers.ollama_provider import OllamaProvider
from providers.anthropic_provider import AnthropicProvider
from providers.groq_provider import GroqProvider
from providers.deepseek_provider import DeepSeekProvider


class TestProvidersRegistry:
    def test_all_expected_keys_present(self):
        expected = {"ollama", "anthropic", "gemini", "groq", "deepseek"}
        assert expected == set(PROVIDERS.keys())

    def test_all_values_are_base_provider_subclasses(self):
        for name, cls in PROVIDERS.items():
            assert issubclass(cls, BaseProvider), f"{name} is not a BaseProvider subclass"


class TestOllamaProvider:
    def test_default_model(self):
        provider = OllamaProvider()
        assert provider.model == "phi4-mini"

    def test_model_override(self):
        provider = OllamaProvider(model="llama3.2")
        assert provider.model == "llama3.2"

    def test_complete_calls_ollama_chat(self):
        provider = OllamaProvider()
        mock_response = {"message": {"content": '{"result": "ok"}'}}
        with patch("providers.ollama_provider.ollama.chat", return_value=mock_response) as mock_chat:
            result = provider.complete("system", "user")
        mock_chat.assert_called_once()
        assert result == '{"result": "ok"}'

    def test_complete_passes_response_format(self):
        provider = OllamaProvider()
        mock_response = {"message": {"content": "[]"}}
        fmt = {"type": "object"}
        with patch("providers.ollama_provider.ollama.chat", return_value=mock_response) as mock_chat:
            provider.complete("sys", "usr", response_format=fmt)
        call_kwargs = mock_chat.call_args.kwargs
        assert call_kwargs["format"] == fmt

    def test_known_models_fetched_from_api(self):
        mock_data = b'{"models": [{"name": "phi4-mini"}, {"name": "llama3.2"}]}'
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("providers.ollama_provider.urllib.request.urlopen", return_value=mock_resp):
            provider = OllamaProvider()
            models = provider.known_models
        assert "phi4-mini" in models
        assert "llama3.2" in models

    def test_known_models_returns_empty_on_error(self):
        with patch("providers.ollama_provider.urllib.request.urlopen", side_effect=Exception("connection refused")):
            provider = OllamaProvider()
            assert provider.known_models == []


class TestAnthropicProvider:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            AnthropicProvider()

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        with patch("providers.anthropic_provider.Anthropic"):
            provider = AnthropicProvider()
        assert provider.model == AnthropicProvider.default_model

    def test_model_override(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        with patch("providers.anthropic_provider.Anthropic"):
            provider = AnthropicProvider(model="claude-sonnet-4-6")
        assert provider.model == "claude-sonnet-4-6"

    def test_complete_returns_text(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="response text")]
        with patch("providers.anthropic_provider.Anthropic", return_value=mock_client):
            provider = AnthropicProvider()
            result = provider.complete("system", "user")
        assert result == "response text"


class TestGroqProvider:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            GroqProvider()

    def test_complete_with_json_format(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content='{"ok": true}'))
        ]
        with patch("providers.groq_provider.Groq", return_value=mock_client):
            provider = GroqProvider()
            result = provider.complete("sys", "usr", response_format={"type": "json_object"})
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}
        assert result == '{"ok": true}'


class TestDeepSeekProvider:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
            DeepSeekProvider()

    def test_uses_deepseek_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        with patch("providers.deepseek_provider.OpenAI") as mock_openai:
            DeepSeekProvider()
        _, kwargs = mock_openai.call_args
        assert "deepseek.com" in kwargs.get("base_url", "")
