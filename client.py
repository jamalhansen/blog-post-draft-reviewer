import os
import json
from typing import Optional
import ollama
from anthropic import Anthropic
from google import genai
from google.genai import types
from groq import Groq
from openai import OpenAI

class ModelClient:
    def __init__(self, backend: str = "ollama", model: str = None):
        self.backend = backend.lower()
        if self.backend == "ollama":
            self.model = model or "phi4-mini"
        elif self.backend == "anthropic":
            self.model = model or "claude-3-haiku-20240307"
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
            self.client = Anthropic(api_key=api_key)
        elif self.backend == "gemini":
            self.model = model or "gemini-2.0-flash"
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY environment variable is set.")
            # Default initialization (uses v1beta) to support system_instruction and response_mime_type
            self.client = genai.Client(api_key=api_key)
        elif self.backend == "groq":
            self.model = model or "llama-3.3-70b-versatile"
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set.")
            self.client = Groq(api_key=api_key)
        elif self.backend == "deepseek":
            self.model = model or "deepseek-chat"
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY environment variable is not set.")
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def complete(self, system: str, user: str, response_format: Optional[dict] = None) -> str:
        if self.backend == "ollama":
            return self._complete_ollama(system, user, response_format)
        elif self.backend == "anthropic":
            return self._complete_anthropic(system, user)
        elif self.backend == "gemini":
            return self._complete_gemini(system, user, response_format)
        elif self.backend == "groq":
            return self._complete_groq(system, user, response_format)
        elif self.backend == "deepseek":
            return self._complete_deepseek(system, user, response_format)
        return ""

    def _complete_ollama(self, system: str, user: str, response_format: Optional[dict]) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            format=response_format,
            options={"num_predict": 4096}
        )
        return response['message']['content']

    def _complete_anthropic(self, system: str, user: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[
                {"role": "user", "content": user}
            ]
        )
        return message.content[0].text

    def _complete_gemini(self, system: str, user: str, response_format: Optional[dict]) -> str:
        # Use types.GenerateContentConfig for type safety and clarity
        config = types.GenerateContentConfig(
            max_output_tokens=4096,
            system_instruction=system,
        )
        if response_format:
            config.response_mime_type = "application/json"

        response = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=config
        )
        return response.text

    def _complete_groq(self, system: str, user: str, response_format: Optional[dict]) -> str:
        # Groq supports JSON mode if specified in the prompt and via the 'type' parameter
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

    def _complete_deepseek(self, system: str, user: str, response_format: Optional[dict]) -> str:
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
