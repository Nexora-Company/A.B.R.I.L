"""Provider construction."""

from ..config import Settings
from .base import AIProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider


def create_provider(settings: Settings) -> AIProvider:
    if settings.provider == "openai":
        return OpenAIProvider(settings)
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    raise ValueError(f"Proveedor no soportado: {settings.provider}")
