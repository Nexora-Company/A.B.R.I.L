"""Dependency wiring for the terminal application.

Only core services are built here. UI-bound command handlers stay in
``main.py`` while they are migrated incrementally, so this module never
imports the entrypoint and no circular imports are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
from ..providers.base import AIProvider
from ..providers.factory import create_provider
from ..services.actions import ActionsService
from ..services.chat import ChatService
from ..services.memory import MemoryService
from .flags import FeatureFlags


@dataclass
class CoreContext:
    settings: Settings
    provider: AIProvider
    chat: ChatService
    actions: ActionsService
    memory: MemoryService
    flags: FeatureFlags


def build_core(settings: Settings | None = None, provider: AIProvider | None = None) -> CoreContext:
    """Build the services shared by the terminal loop.

    ``provider`` can be injected by tests to avoid contacting Ollama.
    """
    settings = settings or Settings.load()
    provider = provider or create_provider(settings)
    chat = ChatService(provider, settings)
    actions = ActionsService(settings, chat)
    memory = MemoryService(settings, actions)
    flags = FeatureFlags.load(settings.config_file)
    return CoreContext(
        settings=settings,
        provider=provider,
        chat=chat,
        actions=actions,
        memory=memory,
        flags=flags,
    )
