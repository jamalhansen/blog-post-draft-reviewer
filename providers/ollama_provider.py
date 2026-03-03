from typing import Optional
import urllib.request
import json
import ollama
from .base import BaseProvider


class OllamaProvider(BaseProvider):
    default_model = "phi4-mini"
    models_url = "http://localhost:11434"

    @property
    def known_models(self) -> list[str]:
        try:
            with urllib.request.urlopen(f"{self.models_url}/api/tags", timeout=3) as resp:
                data = json.loads(resp.read())
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def complete(self, system: str, user: str, response_format=None) -> str:
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                format=response_format,
                options={"num_predict": 4096},
            )
            return response["message"]["content"]
        except ollama.ResponseError as e:
            if "model" in str(e).lower() and "not found" in str(e).lower():
                installed = self.known_models
                hint = f"Installed models: {installed}" if installed else "No models found — run `ollama pull <model>`"
                raise RuntimeError(
                    f"Model '{self.model}' not found in Ollama. {hint}\n"
                    f"More info: {self.models_url}"
                ) from e
            raise RuntimeError(f"Ollama error: {e}") from e
