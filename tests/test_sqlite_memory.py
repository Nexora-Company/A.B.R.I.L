"""Memoria SQLite tests."""

from __future__ import annotations

from pathlib import Path

from abril.services.sqlite_memory import SQLiteMemory


def test_sqlite_memory_creates_tables(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    prefs = db.get_preferences()
    assert prefs == {}
    routines = db.list_routines()
    assert routines == []


def test_sqlite_preferences_crud(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    db.set_preference("editor", "helix")
    assert db.get_preferences() == {"editor": "helix"}

    db.set_preference("editor", "vim")
    assert db.get_preferences() == {"editor": "vim"}

    db.delete_preference("editor")
    assert db.get_preferences() == {}


def test_sqlite_delete_missing_preference_raises(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    try:
        db.delete_preference("no-existe")
        assert False, "Debió lanzar"
    except Exception:
        pass


def test_sqlite_routines_lifecycle(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    routine = db.add_routine("Mañana", "Abrir apps", [{"kind": "open", "detail": "Discord"}])
    assert routine.name == "Mañana"
    assert routine.confirmed is False

    routines = db.list_routines()
    assert len(routines) == 1

    db.confirm_routine(routine.id)
    routines = db.list_routines()
    assert routines[0]["confirmed"] is True

    db.update_routine(routine.id, {"name": "Mañana editada"})
    routines = db.list_routines()
    assert routines[0]["name"] == "Mañana editada"

    db.delete_routine(routine.id)
    assert db.list_routines() == []


def test_sqlite_chat_history(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    db.add_chat_message("user", "hola")
    db.add_chat_message("assistant", "¡Hola!")
    history = db.get_chat_history(limit=10)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_sqlite_audit_log(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    db.add_audit_entry("write", "archivo.txt", "ok", {"size": 100})
    log = db.get_audit_log(limit=10)
    assert len(log) == 1
    assert log[0]["action"] == "write"
    assert log[0]["metadata"]["size"] == 100


def test_sqlite_events(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    db.add_event("alias", {"trigger": "gh", "expansion": "git status"})
    events = db.get_events(kind="alias", limit=10)
    assert len(events) == 1
    assert events[0]["kind"] == "alias"
    assert events[0]["payload"]["trigger"] == "gh"


def test_sqlite_migrate_from_json(tmp_path: Path):
    # Crear JSON legacy
    (tmp_path / "memory.json").write_text('{"preferences": {"tema": "oscuro"}}', encoding="utf-8")
    (tmp_path / "chat_history.json").write_text('[{"role": "user", "content": "hola"}]', encoding="utf-8")
    (tmp_path / "audit_log.json").write_text('[{"action": "open", "detail": "app", "result": "ok"}]', encoding="utf-8")

    db = SQLiteMemory(tmp_path / "test.db")
    counts = db.migrate_from_json(tmp_path)

    assert counts["prefs"] == 1
    assert db.get_preferences() == {"tema": "oscuro"}
    assert counts["chat"] == 1
    assert counts["audit"] == 1
    assert len(db.get_chat_history()) == 1
    assert len(db.get_audit_log()) == 1

    # Una segunda llamada no debe duplicar entradas
    second = db.migrate_from_json(tmp_path)
    assert second == {"prefs": 0, "routines": 0, "chat": 0, "audit": 0}
    assert len(db.get_chat_history()) == 1
    assert len(db.get_audit_log()) == 1


def test_sqlite_close(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    db.close()
    # No debe lanzar al cerrar dos veces
    db.close()