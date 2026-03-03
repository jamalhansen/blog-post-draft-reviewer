import os
from typing import Optional
from groq import Groq
from .base import BaseProvider


class GroqProvider(BaseProvider):
    default_model = "llama-3.3-70b-versatile"
    known_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]
    models_url = "https://console.groq.com/docs/models"

    def __init__(self, model: Optional[str] = None):
        super().__init__(model)
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        self.client = Groq(api_key=api_key)

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

            chat_completion = self.client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            err = str(e).lower()
            if "model" in err and ("not found" in err or "invalid" in err):
                raise RuntimeError(
                    f"Model '{self.model}' not found. "
                    f"Known models: {self.known_models}\n"
                    f"Full list: {self.models_url}"
                ) from e
            raise RuntimeError(f"Groq error: {e}") from e
