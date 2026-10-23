"""Incremental command registry for slash commands.

Existing commands remain in ``main.py`` for now; new or extracted commands are
registered here so the terminal loop can dispatch them without growing.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable
from dataclasses import dataclass

from .. import __version__
from ..config import Settings
from ..services.nexo_brace import NEXOBrace, NEXOBraceState
from ..services.nexus_lock import NEXUSLock
from ..ui.protocol import UIPort
from .flags import FeatureFlags


@dataclass
class CommandContext:
    settings: Settings
    flags: FeatureFlags
    ui: UIPort
    nexo_brace: NEXOBrace | None = None
    nexus_lock: NEXUSLock | None = None


Handler = Callable[[list[str], CommandContext], None]


class CommandRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, name: str, handler: Handler) -> None:
        self._handlers[name.lower()] = handler

    def handle(self, text: str, context: CommandContext) -> bool:
        """Run the matching handler and return ``True`` when handled."""
        if not text.startswith("/"):
            return False
        try:
            parts = shlex.split(text)
        except ValueError:
            return False
        if not parts:
            return False
        handler = self._handlers.get(parts[0].lower())
        if handler is None:
            return False
        handler(parts[1:], context)
        return True

    @property
    def names(self) -> list[str]:
        return sorted(self._handlers)


def _version(args: list[str], context: CommandContext) -> None:
    context.ui.print_system(f"A.B.R.I.L {__version__} — Nexora")


def _config(args: list[str], context: CommandContext) -> None:
    flags = context.flags

    if not args:
        context.ui.print_system("Flags de A.B.R.I.L:")
        for name in flags.names:
            state = "on" if getattr(flags, name) else "off"
            context.ui.print_system(f"  {name} = {state}")
        context.ui.print_system(f"Archivo: {context.settings.config_file}")
        return

    action = args[0].lower()

    if action == "reset":
        flags.reset()
        flags.save(context.settings.config_file)
        context.ui.print_success("Flags restaurados a los valores por defecto.")
        return

    if action == "set":
        if len(args) != 3:
            context.ui.print_error("Uso: /config set <flag> <on|off>")
            return
        name, raw_value = args[1].lower(), args[2].lower()
        if name not in flags.names:
            context.ui.print_error(f"Flag desconocido: {name}. Disponibles: {', '.join(flags.names)}")
            return
        if raw_value not in {"on", "off"}:
            context.ui.print_error("El valor debe ser 'on' u 'off'.")
            return
        flags.set(name, raw_value == "on")
        flags.save(context.settings.config_file)
        context.ui.print_success(f"{name} = {raw_value}")
        return

    context.ui.print_error("Uso: /config [set <flag> <on|off> | reset]")


_STATE_LABELS = {
    NEXOBraceState.LOCKED: "bloqueado",
    NEXOBraceState.PARTIAL: "parcial",
    NEXOBraceState.FULL: "completo",
}


def _require_brace(context: CommandContext) -> NEXOBrace | None:
    if context.nexo_brace is None:
        context.ui.print_error("NEXO-BRACE no está disponible en esta sesión.")
        return None
    return context.nexo_brace


def _brace(args: list[str], context: CommandContext) -> None:
    brace = _require_brace(context)
    if brace is None:
        return
    status = brace.get_status()
    context.ui.print_system(f"NEXO-BRACE: {_STATE_LABELS[brace.state]}")
    context.ui.print_system(
        f"  hardware={status['hardware_tier']}  "
        f"política={status['policy_level']}  "
        f"consentimiento={'sí' if status['user_consent'] else 'no'}  "
        f"nexus_lock={'bloqueado' if status['nexus_locked'] else 'desbloqueado'}"
    )
    for name, info in status["capabilities"].items():
        mark = "sí" if info["unlocked"] else "no"
        context.ui.print_system(f"  {name} [{mark}] — {info['description']}")


def _unlock(args: list[str], context: CommandContext) -> None:
    brace = _require_brace(context)
    if brace is None:
        return

    action = args[0].lower() if args else ""
    if not action:
        if brace.user_consent:
            context.ui.print_system("El consentimiento ya está otorgado. Usa /bloquear para revocarlo.")
            return
        context.ui.print_warning(
            "Esto habilita capacidades de Abril según el hardware, los flags activos y NEXUS-LOCK."
        )
        context.ui.print_system("Escribe /desbloquear confirmar para otorgar el consentimiento.")
        return
    if action != "confirmar":
        context.ui.print_error("Uso: /desbloquear [confirmar]")
        return

    brace.set_user_consent(True)
    context.ui.print_success(f"NEXO-BRACE: {_STATE_LABELS[brace.state]}. Consentimiento otorgado.")
    if brace.state is NEXOBraceState.PARTIAL and brace.nexus_locked:
        context.ui.print_system("NEXUS-LOCK sigue bloqueado: las capacidades completas requieren desbloquearlo.")


def _lock(args: list[str], context: CommandContext) -> None:
    brace = _require_brace(context)
    if brace is None:
        return
    brace.set_user_consent(False)
    if context.nexus_lock is not None:
        context.nexus_lock.lock_all()
        brace.set_nexus_locked(True)
    context.ui.print_success("NEXO-BRACE: bloqueado. Consentimiento revocado.")


def build_command_registry() -> CommandRegistry:
    registry = CommandRegistry()
    registry.register("/version", _version)
    registry.register("/config", _config)
    registry.register("/flags", _config)
    registry.register("/brace", _brace)
    registry.register("/desbloquear", _unlock)
    registry.register("/bloquear", _lock)
    return registry
