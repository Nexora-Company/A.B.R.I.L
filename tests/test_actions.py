"""Actions propose / confirm / cancel flow tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from abril.services.actions import ActionError, ActionsService


def test_propose_unknown_kind_raises(actions: ActionsService) -> None:
    with pytest.raises(ActionError):
        actions.propose_action("teleport", "teletransportar", {})


def test_propose_and_confirm_writes_file(actions: ActionsService, tmp_path: Path) -> None:
    target = tmp_path / "nota.txt"

    action_id = actions.propose_action("write", "Crear nota", {"path": str(target), "content": "hola"})
    result = actions.confirm_action(action_id)

    assert target.read_text(encoding="utf-8") == "hola"
    assert "Archivo escrito" in result


def test_cancel_prevents_execution(actions: ActionsService, tmp_path: Path) -> None:
    target = tmp_path / "no-debe-existir.txt"
    action_id = actions.propose_action("write", "Crear nota", {"path": str(target), "content": "x"})

    actions.cancel_action(action_id)

    assert not target.exists()
    with pytest.raises(ActionError, match="cancelled"):
        actions.confirm_action(action_id)


def test_read_outside_roots_is_rejected(actions: ActionsService) -> None:
    action_id = actions.propose_action("read", "Leer archivo del sistema", {"path": "/etc/hostname"})

    with pytest.raises(ActionError, match="alcance"):
        actions.confirm_action(action_id)


def test_audit_log_records_actions(actions: ActionsService, tmp_path: Path) -> None:
    target = tmp_path / "audit.txt"
    action_id = actions.propose_action("write", "Crear audit", {"path": str(target), "content": "x"})
    actions.confirm_action(action_id)

    log = actions.audit_log()

    assert any(entry["action"] == "write" and "Ejecutada" in entry["result"] for entry in log)


def test_list_apps_uses_discovered_apps(actions: ActionsService) -> None:
    assert actions.list_apps() == [{"id": "discord.desktop", "name": "Discord"}]
