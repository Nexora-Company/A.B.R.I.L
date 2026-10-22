"""OpenAI Chat Completions adapter."""

from __future__ import annotations

from ..config import Settings
from .base import ProviderError
from .http import post_json


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model = settings.openai_model

    def status(self) -> dict[str, str | bool]:
        if not self.api_key:
            return {"ready": False, "status_message": "Configura OPENAI_API_KEY en el archivo .env"}
        return {"ready": True, "status_message": ""}

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise ProviderError("Configura OPENAI_API_KEY en el archivo .env y reinicia Abril.")
        try:
            response = post_json(
                f"{self.base_url}/chat/completions",
                {"model": self.model, "messages": messages},
                {"Authorization": f"Bearer {self.api_key}"},
            )
            answer = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ProviderError("La API de OpenAI devolvió una respuesta inesperada.") from error
        if not isinstance(answer, str) or not answer.strip():
            raise ProviderError("El modelo devolvió una respuesta vacía.")
        return answer.strip()
