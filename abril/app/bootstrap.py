"""Dependency wiring for the terminal application.

Only core services are built here. UI-bound command handlers stay in
``main.py`` while they are migrated incrementally, so this module never
imports the entrypoint and no circular imports are introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import Settings
from ..providers.base import AIProvider
from ..providers.factory import create_provider
from ..services.actions import ActionsService
from ..services.chat import ChatService
from ..services.cpu_opt import CPUOptimization, apply_optimization, optimize_for_profile
from ..services.hardware import HardwareProfile, get_or_create_profile
from ..services.memory import MemoryService
from ..services.nexo_brace import NEXOBrace, build_nexo_brace
from ..services.nexus_lock import NEXUSLock, build_nexus_lock
from ..services.predictive import PredictiveEngine, build_predictive_engine
from ..services.privacy import enable_local_strict, set_audit_callback
from ..services.sqlite_memory import SQLiteMemory
from .flags import FeatureFlags


@dataclass
class CoreContext:
    settings: Settings
    provider: AIProvider
    chat: ChatService
    actions: ActionsService
    memory: MemoryService
    flags: FeatureFlags
    hardware_profile: HardwareProfile
    cpu_optimization: CPUOptimization
    nexo_brace: NEXOBrace
    sqlite_memory: SQLiteMemory | None = None
    predictive: PredictiveEngine | None = None
    nexus_lock: NEXUSLock | None = None


def build_core(settings: Settings | None = None, provider: AIProvider | None = None) -> CoreContext:
    """Build the services shared by the terminal loop.

    ``provider`` can be injected by tests to avoid contacting Ollama.
    Optional services stay ``None`` while their feature flag is disabled,
    so the default path keeps A.B.R.I.L's current behaviour.
    """
    settings = settings or Settings.load()
    flags = FeatureFlags.load(settings.config_file)

    enable_local_strict(flags.local_strict)

    hardware_profile = get_or_create_profile(settings.data_dir)
    cpu_optimization = optimize_for_profile(hardware_profile)
    if flags.hardware_profiles:
        apply_optimization(cpu_optimization)

    provider = provider or create_provider(settings)

    chat = ChatService(provider, settings)
    actions = ActionsService(settings, chat)
    memory = MemoryService(settings, actions)

    sqlite_memory: SQLiteMemory | None = None
    predictive: PredictiveEngine | None = None
    if flags.sqlite_memory:
        sqlite_memory = SQLiteMemory(settings.data_dir / "abril.db")
        sqlite_memory.migrate_from_json(settings.data_dir)
        if flags.predictive:
            predictive = build_predictive_engine(sqlite_memory)

    def _audit_callback(event: str, data: dict[str, Any]) -> None:
        if sqlite_memory is not None:
            sqlite_memory.add_event("audit", {"event": event, **data})

    set_audit_callback(_audit_callback)

    nexus_lock = build_nexus_lock(audit_callback=_audit_callback) if flags.nexus_lock else None
    nexo_brace = build_nexo_brace(
        hardware_tier=hardware_profile.tier,
        flags=flags.to_dict(),
        policy_level="allow" if flags.policy else "ask",
        user_consent=False,  # Se solicita en runtime antes de desbloquear capacidades
        nexus_locked=True if nexus_lock is None else nexus_lock.is_locked,
    )

    return CoreContext(
        settings=settings,
        provider=provider,
        chat=chat,
        actions=actions,
        memory=memory,
        flags=flags,
        hardware_profile=hardware_profile,
        cpu_optimization=cpu_optimization,
        nexo_brace=nexo_brace,
        sqlite_memory=sqlite_memory,
        predictive=predictive,
        nexus_lock=nexus_lock,
    )
