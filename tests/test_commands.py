"""Command registry tests for /version and /config."""

from __future__ import annotations

from abril.app.commands import CommandContext, build_command_registry
from abril.app.flags import FeatureFlags
from abril.config import Settings
from tests.helpers import RecordingUI


def _context(settings: Settings, ui: RecordingUI) -> CommandContext:
    return CommandContext(settings=settings, flags=FeatureFlags(), ui=ui)


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
