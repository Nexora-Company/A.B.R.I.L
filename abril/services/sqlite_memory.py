"""Memoria persistente en SQLite (reemplaza JSON files).

Migración idempotente desde `data/memory.json`, `data/chat_history.json`,
`data/audit_log.json`. API compatible con `MemoryService` actual.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .actions import ActionError


SCHEMA_VERSION = 1


def _utcnow_iso() -> str:
    """Timestamp UTC ISO 8601 sin zona, conservando el formato histórico."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

_MIGRATIONS = [
    # v1: esquema inicial
    """
    CREATE TABLE IF NOT EXISTS prefs (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS routines (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        steps TEXT NOT NULL,  -- JSON array
        confirmed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        detail TEXT,
        result TEXT,
        timestamp TEXT NOT NULL,
        metadata TEXT  -- JSON
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,      -- alias, quota, task, undo, etc.
        payload TEXT NOT NULL,   -- JSON
        timestamp TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
]


@dataclass
class RoutineRecord:
    id: str
    name: str
    description: str
    steps: list[dict[str, Any]]
    confirmed: bool
    created_at: str
    updated_at: str


class SQLiteMemory:
    """Memoria respaldada por SQLite con migraciones automáticas."""

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute("PRAGMA busy_timeout=5000;")
        self._run_migrations()

    def _run_migrations(self) -> None:
        assert self._conn is not None
        cur = self._conn.cursor()
        # Verificar si la tabla meta existe
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta'")
        if cur.fetchone() is None:
            current = 0
        else:
            cur.execute("SELECT value FROM meta WHERE key='schema_version'")
            row = cur.fetchone()
            current = int(row[0]) if row else 0

        for i, sql in enumerate(_MIGRATIONS[current:], start=current + 1):
            cur.executescript(sql)
            cur.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)", (str(i),))
        self._conn.commit()

    @contextmanager
    def _tx(self):
        assert self._conn is not None
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    # ── Preferencias ────────────────────────────────────────────────

    def get_preferences(self) -> dict[str, str]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute("SELECT key, value FROM prefs")
            return {row[0]: row[1] for row in cur.fetchall()}

    def set_preference(self, key: str, value: str) -> None:
        now = _utcnow_iso()
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO prefs (key, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, value, now),
            )

    def delete_preference(self, key: str) -> None:
        with self._tx() as conn:
            cur = conn.execute("DELETE FROM prefs WHERE key=?", (key,))
            if cur.rowcount == 0:
                raise ActionError(f"Preferencia no encontrada: {key}")

    # ── Rutinas ────────────────────────────────────────────────────

    def list_routines(self) -> list[dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, name, description, steps, confirmed, created_at, updated_at FROM routines ORDER BY created_at"
            )
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "steps": json.loads(row[3]),
                    "confirmed": bool(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6],
                }
                for row in cur.fetchall()
            ]

    def add_routine(self, name: str, description: str, steps: list[dict[str, Any]]) -> RoutineRecord:
        import uuid
        now = _utcnow_iso()
        rid = str(uuid.uuid4())[:8]
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO routines (id, name, description, steps, confirmed, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 0, ?, ?)",
                (rid, name, description, json.dumps(steps), now, now),
            )
        return RoutineRecord(rid, name, description, steps, False, now, now)

    def confirm_routine(self, routine_id: str) -> None:
        now = _utcnow_iso()
        with self._tx() as conn:
            cur = conn.execute(
                "UPDATE routines SET confirmed=1, updated_at=? WHERE id=?", (now, routine_id)
            )
            if cur.rowcount == 0:
                raise ActionError(f"Rutina no encontrada: {routine_id}")

    def update_routine(self, routine_id: str, changes: dict[str, Any]) -> None:
        now = _utcnow_iso()
        allowed = {"name", "description", "steps"}
        updates = {k: v for k, v in changes.items() if k in allowed}
        if not updates:
            return
        if "steps" in updates:
            updates["steps"] = json.dumps(updates["steps"])
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [now, routine_id]
        with self._tx() as conn:
            cur = conn.execute(f"UPDATE routines SET {set_clause}, updated_at=? WHERE id=?", values)
            if cur.rowcount == 0:
                raise ActionError(f"Rutina no encontrada: {routine_id}")

    def delete_routine(self, routine_id: str) -> None:
        with self._tx() as conn:
            cur = conn.execute("DELETE FROM routines WHERE id=?", (routine_id,))
            if cur.rowcount == 0:
                raise ActionError(f"Rutina no encontrada: {routine_id}")

    # ── Historial de chat ──────────────────────────────────────────

    def add_chat_message(self, role: str, content: str) -> None:
        now = _utcnow_iso()
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO chat_history (role, content, timestamp) VALUES (?, ?, ?)",
                (role, content, now),
            )

    def get_chat_history(self, limit: int = 100) -> list[dict[str, str]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def clear_chat_history(self) -> None:
        with self._tx() as conn:
            conn.execute("DELETE FROM chat_history")

    # ── Auditoría ──────────────────────────────────────────────────

    def add_audit_entry(self, action: str, detail: str, result: str, metadata: dict[str, Any] | None = None) -> None:
        now = _utcnow_iso()
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO audit_log (action, detail, result, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                (action, detail, result, now, json.dumps(metadata or {})),
            )

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.execute(
                "SELECT action, detail, result, timestamp, metadata FROM audit_log ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [
                {
                    "action": row[0],
                    "detail": row[1],
                    "result": row[2],
                    "timestamp": row[3],
                    "metadata": json.loads(row[4]) if row[4] else {},
                }
                for row in cur.fetchall()
            ]

    # ── Eventos (para alias, tareas, quotas, undo) ─────────────────

    def add_event(self, kind: str, payload: dict[str, Any]) -> None:
        now = _utcnow_iso()
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO events (kind, payload, timestamp) VALUES (?, ?, ?)",
                (kind, json.dumps(payload), now),
            )

    def get_events(self, kind: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            if kind:
                cur = self._conn.execute(
                    "SELECT kind, payload, timestamp FROM events WHERE kind=? ORDER BY id DESC LIMIT ?",
                    (kind, limit),
                )
            else:
                cur = self._conn.execute(
                    "SELECT kind, payload, timestamp FROM events ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            return [
                {"kind": row[0], "payload": json.loads(row[1]), "timestamp": row[2]}
                for row in cur.fetchall()
            ]

    # ── Migración desde JSON legacy ────────────────────────────────

    def migrate_from_json(self, data_dir: Path) -> dict[str, int]:
        """Migra archivos JSON legacy a SQLite una sola vez por base de datos."""
        counts = {"prefs": 0, "routines": 0, "chat": 0, "audit": 0}
        assert self._conn is not None
        with self._lock:
            done = self._conn.execute("SELECT 1 FROM meta WHERE key='json_migrated'").fetchone()
        if done is not None:
            return counts

        # prefs
        prefs_file = data_dir / "memory.json"
        if prefs_file.exists():
            try:
                data = json.loads(prefs_file.read_text(encoding="utf-8"))
                prefs = data.get("preferences", {})
                for k, v in prefs.items():
                    self.set_preference(k, v)
                counts["prefs"] = len(prefs)
            except Exception:
                pass

        # chat_history
        chat_file = data_dir / "chat_history.json"
        if chat_file.exists():
            try:
                history = json.loads(chat_file.read_text(encoding="utf-8"))
                for msg in history[-500:]:  # últimos 500
                    self.add_chat_message(msg["role"], msg["content"])
                counts["chat"] = len(history)
            except Exception:
                pass

        # audit_log
        audit_file = data_dir / "audit_log.json"
        if audit_file.exists():
            try:
                log = json.loads(audit_file.read_text(encoding="utf-8"))
                for entry in log[-500:]:
                    self.add_audit_entry(
                        entry.get("action", ""),
                        entry.get("detail", ""),
                        entry.get("result", ""),
                        entry.get("metadata"),
                    )
                counts["audit"] = len(log)
            except Exception:
                pass

        with self._tx() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('json_migrated', ?)",
                (_utcnow_iso(),),
            )

        return counts

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


__all__ = ["SQLiteMemory", "RoutineRecord", "SCHEMA_VERSION"]