from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    default_model: str
    known_models: list[str]
    models_url: str

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.default_model

    @abstractmethod
    def complete(self, system: str, user: str, response_format=None) -> str:
        """Call the LLM and return the response text."""
        ...
