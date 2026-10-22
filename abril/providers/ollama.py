"""Ollama local chat adapter."""

from __future__ import annotations

from ..config import Settings
from .base import ProviderError
from .http import get_json, post_json


class OllamaProvider:
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model

    def status(self) -> dict[str, str | bool]:
        try:
            response = get_json(f"{self.base_url}/api/tags")
            models = response.get("models", [])
            installed = any(item.get("name") == self.model or item.get("model") == self.model for item in models)
            if not installed:
                return {"ready": False, "status_message": f"Descarga el modelo {self.model} en Ollama"}
            return {"ready": True, "status_message": ""}
        except ProviderError:
            return {"ready": False, "status_message": "Ollama no está iniciado"}

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            response = post_json(
                f"{self.base_url}/api/chat",
                {"model": self.model, "messages": messages, "stream": False, "options": {"num_predict": 512}},
                {},
            )
            answer = response["message"]["content"]
        except ProviderError:
            raise
        except (KeyError, TypeError) as error:
            raise ProviderError("Ollama devolvió una respuesta inesperada.") from error
        if not isinstance(answer, str) or not answer.strip():
            raise ProviderError("El modelo devolvió una respuesta vacía.")
        return answer.strip()
