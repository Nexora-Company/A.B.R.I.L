"""Pattern analyzer and proactive commands tests.

These tests exist because the module previously referenced names it never
imported, which made /analizar, /ideas and /pensar fail at runtime.
"""

from __future__ import annotations

from pathlib import Path

from abril.config import Settings
from abril.services.actions import ActionsService
from abril.services.chat import ChatService
from abril.services.memory import MemoryService
from abril.services.pattern_analyzer import PatternAnalyzer
from tests.helpers import FakeProvider, RecordingUI


def _analyzer(ui: RecordingUI, chat: ChatService, memory: MemoryService, actions: ActionsService) -> PatternAnalyzer:
    return PatternAnalyzer(ui, chat, memory, actions)


def test_regular_text_is_not_handled(
    settings: Settings, ui: RecordingUI, chat: ChatService, actions: ActionsService
) -> None:
    analyzer = _analyzer(ui, chat, MemoryService(settings, actions), actions)

    assert analyzer.handle("hola") is False


def test_unbalanced_quotes_are_not_handled(
    settings: Settings, ui: RecordingUI, chat: ChatService, actions: ActionsService
) -> None:
    analyzer = _analyzer(ui, chat, MemoryService(settings, actions), actions)

    assert analyzer.handle('/pensar "sin cerrar') is False


def test_pensar_uses_provider(
    settings: Settings,
    ui: RecordingUI,
    chat: ChatService,
    actions: ActionsService,
    fake_provider: FakeProvider,
) -> None:
    analyzer = _analyzer(ui, chat, MemoryService(settings, actions), actions)

    handled = analyzer.handle("/pensar ¿qué es la vida?")

    assert handled is True
    assert fake_provider.calls
    assert any("respuesta falsa" in line for _, line in ui.lines)


def test_analizar_memoria_uses_provider(
    settings: Settings,
    ui: RecordingUI,
    chat: ChatService,
    actions: ActionsService,
    fake_provider: FakeProvider,
) -> None:
    memory = MemoryService(settings, actions)
    memory.set_preference("editor", "helix")
    analyzer = _analyzer(ui, chat, memory, actions)

    handled = analyzer.handle("/analizar memoria")

    assert handled is True
    assert fake_provider.calls


def test_analizar_file_detects_language(
    settings: Settings,
    ui: RecordingUI,
    chat: ChatService,
    actions: ActionsService,
    fake_provider: FakeProvider,
    tmp_path: Path,
) -> None:
    source = tmp_path / "ejemplo.py"
    source.write_text("print('hola')\n", encoding="utf-8")
    analyzer = _analyzer(ui, chat, MemoryService(settings, actions), actions)

    handled = analyzer.handle(f"/analizar {source}")

    assert handled is True
    assert fake_provider.calls
    sent = fake_provider.calls[-1][1]["content"]
    assert "python" in sent
    assert "print('hola')" in sent


def test_ideas_needs_context(
    settings: Settings,
    ui: RecordingUI,
    chat: ChatService,
    actions: ActionsService,
    fake_provider: FakeProvider,
) -> None:
    memory = MemoryService(settings, actions)
    memory.set_preference("lenguaje", "python")
    analyzer = _analyzer(ui, chat, memory, actions)

    handled = analyzer.handle("/ideas")

    assert handled is True
    assert fake_provider.calls
