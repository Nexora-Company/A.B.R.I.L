"""Command registry tests for /version and /config."""

from __future__ import annotations

from abril.app.commands import CommandContext, build_command_registry
from abril.app.flags import FeatureFlags
from abril.config import Settings
from abril.services.nexo_brace import NEXOBraceState, build_nexo_brace
from abril.services.nexus_lock import build_nexus_lock
from tests.helpers import RecordingUI


def _context(settings: Settings, ui: RecordingUI) -> CommandContext:
    return CommandContext(settings=settings, flags=FeatureFlags(), ui=ui)


def _brace_context(settings: Settings, ui: RecordingUI, *, nexus_locked: bool = True) -> CommandContext:
    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={"routing": True},
        policy_level="allow",
        nexus_locked=nexus_locked,
    )
    return CommandContext(
        settings=settings,
        flags=FeatureFlags(),
        ui=ui,
        nexo_brace=brace,
        nexus_lock=build_nexus_lock(),
    )


def test_ignores_regular_messages(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    assert registry.handle("hola", _context(settings, ui)) is False


def test_unknown_command_returns_false(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    assert registry.handle("/desconocido", _context(settings, ui)) is False


def test_version_command(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    assert registry.handle("/version", _context(settings, ui)) is True
    assert "A.B.R.I.L" in ui.text()
    assert "Nexora" in ui.text()


def test_config_lists_flags(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    registry.handle("/config", _context(settings, ui))

    assert "local_strict = on" in ui.text()
    assert "routing = off" in ui.text()


def test_config_set_persists(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()
    context = _context(settings, ui)

    registry.handle("/config set routing on", context)

    assert context.flags.routing is True
    assert FeatureFlags.load(settings.config_file).routing is True
    assert "routing = on" in ui.text()


def test_config_rejects_unknown_flag(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    registry.handle("/config set inventado on", _context(settings, ui))

    assert "Flag desconocido" in ui.text()


def test_config_rejects_invalid_value(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    registry.handle("/config set routing quizá", _context(settings, ui))

    assert "on' u 'off" in ui.text()


def test_config_reset(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()
    context = _context(settings, ui)
    context.flags.set("routing", True)

    registry.handle("/config reset", context)

    assert context.flags.routing is False
    assert "restaurados" in ui.text()


def test_brace_shows_state_and_capabilities(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()
    context = _brace_context(settings, ui)

    registry.handle("/brace", context)

    assert "NEXO-BRACE: bloqueado" in ui.text()
    assert "router [no]" in ui.text()


def test_unlock_requires_explicit_confirmation(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()
    context = _brace_context(settings, ui)

    registry.handle("/desbloquear", context)

    assert context.nexo_brace is not None
    assert context.nexo_brace.user_consent is False
    assert "/desbloquear confirmar" in ui.text()


def test_unlock_confirm_grants_consent(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()
    context = _brace_context(settings, ui)

    registry.handle("/desbloquear confirmar", context)

    assert context.nexo_brace is not None
    assert context.nexo_brace.user_consent is True
    assert context.nexo_brace.state is NEXOBraceState.PARTIAL
    assert "Consentimiento otorgado" in ui.text()


def test_lock_revokes_consent_and_nexus_access(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()
    context = _brace_context(settings, ui)
    assert context.nexo_brace is not None
    context.nexo_brace.set_user_consent(True)

    registry.handle("/bloquear", context)

    assert context.nexo_brace.user_consent is False
    assert context.nexo_brace.state is NEXOBraceState.LOCKED
    assert context.nexus_lock is not None
    assert context.nexus_lock.is_locked is True


def test_brace_commands_report_missing_service(settings: Settings, ui: RecordingUI) -> None:
    registry = build_command_registry()

    registry.handle("/brace", _context(settings, ui))

    assert "no está disponible" in ui.text()
