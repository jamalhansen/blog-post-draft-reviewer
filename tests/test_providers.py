import pytest
from unittest.mock import patch, MagicMock
from local_first_common.providers import PROVIDERS
from local_first_common.providers.base import BaseProvider
from local_first_common.providers.ollama import OllamaProvider
from local_first_common.providers.anthropic import AnthropicProvider
from local_first_common.providers.groq import GroqProvider
from local_first_common.providers.deepseek import DeepSeekProvider


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

    def test_complete_calls_httpx(self):
        provider = OllamaProvider()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": '{"result": "ok"}'}
        mock_response.raise_for_status = MagicMock()
        with patch("local_first_common.providers.ollama.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client
            result = provider.complete("system", "user")
        assert result == '{"result": "ok"}'

    def test_known_models_fetched_from_api(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": [{"name": "phi4-mini"}, {"name": "llama3.2"}]}
        mock_response.raise_for_status = MagicMock()
        with patch("local_first_common.providers.ollama.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client
            provider = OllamaProvider()
            models = provider._get_installed_models()
        assert "phi4-mini" in models
        assert "llama3.2" in models

    def test_known_models_returns_empty_on_error(self):
        import httpx as _httpx
        with patch("local_first_common.providers.ollama.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = Exception("connection refused")
            mock_client_cls.return_value = mock_client
            provider = OllamaProvider()
            assert provider._get_installed_models() == []


class TestAnthropicProvider:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            AnthropicProvider()

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider()
        assert provider.model == AnthropicProvider.default_model

    def test_model_override(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider(model="claude-sonnet-4-6")
        assert provider.model == "claude-sonnet-4-6"

    def test_complete_returns_text(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="response text")]
        with patch("local_first_common.providers.anthropic._Anthropic") as mock_anthropic_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_message
            mock_anthropic_cls.return_value = mock_client
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
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        mock_response.raise_for_status = MagicMock()
        with patch("local_first_common.providers.groq.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client
            provider = GroqProvider()
            result = provider.complete("sys", "usr")
        assert result == '{"ok": true}'


class TestDeepSeekProvider:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
            DeepSeekProvider()

    def test_uses_deepseek_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        provider = DeepSeekProvider()
        assert "deepseek.com" in provider._api_url
