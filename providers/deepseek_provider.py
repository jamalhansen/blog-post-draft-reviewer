import os
from typing import Optional
from openai import OpenAI
from .base import BaseProvider


class DeepSeekProvider(BaseProvider):
    default_model = "deepseek-chat"
    known_models = [
        "deepseek-chat",
        "deepseek-reasoner",
    ]
    models_url = "https://api-docs.deepseek.com/quick_start/pricing"

    def __init__(self, model: Optional[str] = None):
        super().__init__(model)
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def complete(self, system: str, user: str, response_format=None) -> str:
        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 4096,
            }
            if response_format:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            err = str(e).lower()
            if "model" in err and ("not found" in err or "invalid" in err):
                raise RuntimeError(
                    f"Model '{self.model}' not found. "
                    f"Known models: {self.known_models}\n"
                    f"Full list: {self.models_url}"
                ) from e
            raise RuntimeError(f"DeepSeek error: {e}") from e
