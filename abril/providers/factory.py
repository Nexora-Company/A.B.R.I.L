"""Provider construction."""

from ..config import Settings
from .base import AIProvider
from .ollama import OllamaProvider


def create_provider(settings: Settings) -> AIProvider:
    return OllamaProvider(settings)
