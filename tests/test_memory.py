"""JSON memory service tests."""

from __future__ import annotations

import pytest

from abril.config import Settings
from abril.services.actions import ActionError, ActionsService
from abril.services.memory import MemoryService


def test_preferences_roundtrip(settings: Settings, actions: ActionsService) -> None:
    memory = MemoryService(settings, actions)

    memory.set_preference("editor", "helix")

    assert memory.get_preferences() == {"editor": "helix"}
    memory.delete_preference("editor")
    assert memory.get_preferences() == {}


def test_delete_missing_preference_raises(settings: Settings, actions: ActionsService) -> None:
    memory = MemoryService(settings, actions)

    with pytest.raises(ActionError):
        memory.delete_preference("no-existe")


def test_preferences_persist_across_instances(settings: Settings, actions: ActionsService) -> None:
    first = MemoryService(settings, actions)
    first.set_preference("tema", "oscuro")

    second = MemoryService(settings, actions)

    assert second.get_preferences() == {"tema": "oscuro"}


def test_routine_lifecycle(settings: Settings, actions: ActionsService) -> None:
    memory = MemoryService(settings, actions)

    routine = memory.add_routine("Mañana", "Abrir lo de siempre", [{"kind": "open", "detail": "Discord"}])
    assert memory.list_routines()[0]["name"] == "Mañana"

    memory.confirm_routine(routine["id"])
    assert memory.list_routines()[0]["confirmed"] is True

    memory.update_routine(routine["id"], {"name": "Mañana editada"})
    assert memory.list_routines()[0]["name"] == "Mañana editada"

    memory.delete_routine(routine["id"])
    assert memory.list_routines() == []


def test_missing_routine_raises(settings: Settings, actions: ActionsService) -> None:
    memory = MemoryService(settings, actions)

    with pytest.raises(ActionError):
        memory.confirm_routine("no-existe")


def test_suggestions_from_repeated_actions(settings: Settings, actions: ActionsService, monkeypatch: pytest.MonkeyPatch) -> None:
    memory = MemoryService(settings, actions)
    audit = [
        {"action": "open", "detail": "Discord", "result": "ok"},
        {"action": "open", "detail": "Discord", "result": "ok"},
        {"action": "open", "detail": "Discord", "result": "ok"},
    ]
    monkeypatch.setattr(actions, "audit_log", lambda: audit)

    suggestions = memory.suggestions()

    assert len(suggestions) == 1
    assert suggestions[0]["suggested"] is True
