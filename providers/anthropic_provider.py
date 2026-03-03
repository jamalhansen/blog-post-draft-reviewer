import os
from typing import Optional
from anthropic import Anthropic
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    default_model = "claude-haiku-4-5-20251001"
    known_models = [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
        "claude-opus-4-6",
    ]
    models_url = "https://docs.anthropic.com/en/docs/about-claude/models"

    def __init__(self, model: Optional[str] = None):
        super().__init__(model)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
        self.client = Anthropic(api_key=api_key)

    def complete(self, system: str, user: str, response_format=None) -> str:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return message.content[0].text
        except Exception as e:
            err = str(e).lower()
            if "model" in err and ("not found" in err or "invalid" in err):
                raise RuntimeError(
                    f"Model '{self.model}' not found. "
                    f"Known models: {self.known_models}\n"
                    f"Full list: {self.models_url}"
                ) from e
            raise RuntimeError(f"Anthropic error: {e}") from e
