import os
from typing import Optional
from google import genai
from google.genai import types
from .base import BaseProvider


class GeminiProvider(BaseProvider):
    default_model = "gemini-2.0-flash"
    known_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    models_url = "https://ai.google.dev/gemini-api/docs/models"

    def __init__(self, model: Optional[str] = None):
        super().__init__(model)
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Neither GEMINI_API_KEY nor GOOGLE_API_KEY environment variable is set."
            )
        self.client = genai.Client(api_key=api_key)

    def complete(self, system: str, user: str, response_format=None) -> str:
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=4096,
                system_instruction=system,
            )
            if response_format:
                config.response_mime_type = "application/json"

            response = self.client.models.generate_content(
                model=self.model,
                contents=user,
                config=config,
            )
            return response.text
        except Exception as e:
            err = str(e).lower()
            if "model" in err and ("not found" in err or "invalid" in err):
                raise RuntimeError(
                    f"Model '{self.model}' not found. "
                    f"Known models: {self.known_models}\n"
                    f"Full list: {self.models_url}"
                ) from e
            raise RuntimeError(f"Gemini error: {e}") from e
