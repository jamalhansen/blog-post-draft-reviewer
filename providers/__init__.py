from .ollama_provider import OllamaProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .deepseek_provider import DeepSeekProvider

PROVIDERS: dict = {
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "deepseek": DeepSeekProvider,
}
