"""Servicio de memoria personal: preferencias y rutinas revisables.

La memoria vive en un archivo JSON local bajo el directorio de datos.
Todo es visible, editable y borrable por la persona. Las sugerencias se
presentan como propuestas que el usuario confirma, nunca como decisiones
automáticas.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..services.actions import ActionsService


class MemoryService:
    def __init__(self, settings, actions: ActionsService) -> None:
        self.settings = settings
        self.actions = actions
        self.path = settings.data_dir / "memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = __import__("threading").Lock()
        self.preferences: dict[str, Any] = {}
        self.routines: list[dict[str, Any]] = []
        self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                self.preferences = data.get("preferences", {}) or {}
                self.routines = data.get("routines", []) or []
        except (OSError, json.JSONDecodeError):
            self.preferences = {}
            self.routines = []

    def _save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        payload = {"preferences": self.preferences, "routines": self.routines}
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # ------------------------------------------------------------------ #
    # Preferences
    # ------------------------------------------------------------------ #
    def get_preferences(self) -> dict[str, Any]:
        with self._lock:
            return dict(self.preferences)

    def set_preference(self, key: str, value: Any) -> None:
        with self._lock:
            self.preferences[key] = value
        self._save()

    def delete_preference(self, key: str) -> None:
        with self._lock:
            if key not in self.preferences:
                from ..services.actions import ActionError

                raise ActionError(f"Preferencia no encontrada: {key}.")
            del self.preferences[key]
        self._save()

    # ------------------------------------------------------------------ #
    # Routines
    # ------------------------------------------------------------------ #
    def list_routines(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self.routines]

    def add_routine(self, name: str, description: str, actions: list[dict[str, Any]]) -> dict[str, Any]:
        routine = {
            "id": uuid.uuid4().hex,
            "name": name,
            "description": description,
            "actions": actions,
            "confirmed": False,
            "created_at": datetime.now().astimezone().isoformat(),
        }
        with self._lock:
            self.routines.append(routine)
        self._save()
        return routine

    def update_routine(self, routine_id: str, fields: dict[str, Any]) -> None:
        with self._lock:
            for routine in self.routines:
                if routine["id"] == routine_id:
                    for key, value in fields.items():
                        if key in {"name", "description", "actions"}:
                            routine[key] = value
                    self._save()
                    return
        from ..services.actions import ActionError

        raise ActionError(f"Rutina no encontrada: {routine_id}.")

    def delete_routine(self, routine_id: str) -> None:
        with self._lock:
            for index, routine in enumerate(self.routines):
                if routine["id"] == routine_id:
                    del self.routines[index]
                    self._save()
                    return
        from ..services.actions import ActionError

        raise ActionError(f"Rutina no encontrada: {routine_id}.")

    def confirm_routine(self, routine_id: str) -> None:
        with self._lock:
            for routine in self.routines:
                if routine["id"] == routine_id:
                    routine["confirmed"] = True
                    self._save()
                    return
        from ..services.actions import ActionError

        raise ActionError(f"Rutina no encontrada: {routine_id}.")

    # ------------------------------------------------------------------ #
    # Suggestions (Fase 3: hábitos inferidos como sugerencias, no órdenes)
    # ------------------------------------------------------------------ #
    def suggestions(self) -> list[dict[str, Any]]:
        """Propone rutinas a partir de acciones repetidas en el auditoría.

        Sólo se presentan como sugerencias; la persona debe confirmarlas.
        """
        audit = self.actions.audit_log()
        counts: dict[str, int] = {}
        for entry in audit:
            action = entry.get("action", "")
            detail = entry.get("detail", "")
            key = f"{action}:{detail}"
            counts[key] = counts.get(key, 0) + 1

        proposed: list[dict[str, Any]] = []
        for key, count in counts.items():
            if count >= 3:
                action, _, detail = key.partition(":")
                proposed.append({
                    "name": f"Rutina sugerida: {action}",
                    "description": f"Se detectó que ejecutaste '{detail}' al menos {count} veces. ¿Quieres guardarla como rutina?",
                    "actions": [{"kind": action, "detail": detail}],
                    "suggested": True,
                })
        return proposed
