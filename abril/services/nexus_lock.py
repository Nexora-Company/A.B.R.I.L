"""Protocolo NEXUS-LOCK: control de acceso a domótica y dispositivos físicos.

NEXUS-LOCK (Networked EXternal Unlock System - LOCK) gestiona la autorización
para que Abril interactúe con dispositivos IoT, domótica, cerraduras, clima, etc.

Principios:
- Default deny: nada se controla sin consentimiento explícito por dispositivo
- Auditoría inmutable: cada acción en domótica queda registrada
- Revocación instantánea: el usuario puede revocar acceso en cualquier momento
- Aislamiento de red: comunicación solo por protocolo local (Matter/Thread, MQTT local)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utcnow_iso() -> str:
    """Timestamp UTC ISO 8601 sin zona, conservando el formato histórico."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


class DeviceType(Enum):
    LIGHT = "light"
    SWITCH = "switch"
    LOCK = "lock"
    CLIMATE = "climate"
    SENSOR = "sensor"
    CAMERA = "camera"
    SPEAKER = "speaker"
    CUSTOM = "custom"


class AccessLevel(Enum):
    NONE = 0      # Sin acceso
    READ = 1      # Solo lectura de estado
    CONTROL = 2   # Control total (encender/apagar, abrir/cerrar)
    ADMIN = 3     # Configuración del dispositivo


@dataclass
class Device:
    id: str
    name: str
    type: DeviceType
    protocol: str  # matter, mqtt, zigbee, custom
    endpoint: str  # IP, topic MQTT, etc.
    access_level: AccessLevel = AccessLevel.NONE
    metadata: dict[str, Any] = field(default_factory=dict)
    granted_at: str | None = None
    revoked_at: str | None = None

    def is_active(self) -> bool:
        return self.access_level != AccessLevel.NONE and self.revoked_at is None


@dataclass
class DomoticAction:
    device_id: str
    command: str
    params: dict[str, Any]
    timestamp: str = field(default_factory=_utcnow_iso)
    success: bool = False
    error: str | None = None


class NEXUSLock:
    """Gestor de permisos y acciones para domótica."""

    def __init__(self, audit_callback=None) -> None:
        self._devices: dict[str, Device] = {}
        self._audit_callback = audit_callback
        self._lock_state = False  # False = desbloqueado por defecto

    # ── Gestión de dispositivos ────────────────────────────────────

    def register_device(self, device: Device) -> None:
        self._devices[device.id] = device

    def get_device(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def list_devices(self, active_only: bool = False) -> list[Device]:
        devices = list(self._devices.values())
        if active_only:
            devices = [d for d in devices if d.is_active()]
        return devices

    # ── Control de acceso ──────────────────────────────────────────

    def grant_access(self, device_id: str, level: AccessLevel) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False
        device.access_level = level
        device.granted_at = _utcnow_iso()
        device.revoked_at = None
        self._audit("access_granted", {"device_id": device_id, "level": level.name})
        return True

    def revoke_access(self, device_id: str) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False
        device.access_level = AccessLevel.NONE
        device.revoked_at = _utcnow_iso()
        self._audit("access_revoked", {"device_id": device_id})
        return True

    def lock_all(self) -> None:
        """Bloqueo global de emergencia: revoca todo acceso instantly."""
        for device in self._devices.values():
            if device.is_active():
                device.access_level = AccessLevel.NONE
                device.revoked_at = _utcnow_iso()
        self._lock_state = True
        self._audit("global_lock", {"device_count": len(self._devices)})

    def unlock_all(self) -> None:
        """Desbloqueo global (requiere re-otorgar accesos individualmente)."""
        self._lock_state = False
        self._audit("global_unlock", {})

    @property
    def is_locked(self) -> bool:
        return self._lock_state

    # ── Ejecución de acciones ──────────────────────────────────────

    def execute(self, action: DomoticAction) -> DomoticAction:
        """Ejecuta acción si el dispositivo tiene permisos y no está en lock global."""
        if self._lock_state:
            action.success = False
            action.error = "NEXUS-LOCK: bloqueo global activo"
            self._audit("action_blocked_global", {"device_id": action.device_id})
            return action

        device = self._devices.get(action.device_id)
        if not device:
            action.success = False
            action.error = f"Dispositivo no registrado: {action.device_id}"
            self._audit("action_unknown_device", {"device_id": action.device_id})
            return action

        if not device.is_active():
            action.success = False
            action.error = f"Sin acceso al dispositivo: {action.device_id}"
            self._audit("action_no_access", {"device_id": action.device_id, "level": device.access_level.name})
            return action

        if device.access_level == AccessLevel.READ and action.command not in ("get_state", "status"):
            action.success = False
            action.error = f"Solo lectura permitida: {action.device_id}"
            self._audit("action_read_only", {"device_id": action.device_id, "command": action.command})
            return action

        # Aquí iría la ejecución real (Matter, MQTT, etc.)
        # Por ahora solo simulamos éxito y auditamos
        action.success = True
        self._audit("action_executed", {
            "device_id": action.device_id,
            "command": action.command,
            "params": action.params,
        })
        return action

    # ── Auditoría ──────────────────────────────────────────────────

    def _audit(self, event: str, data: dict[str, Any]) -> None:
        if self._audit_callback:
            try:
                self._audit_callback(event, data)
            except Exception:
                pass


def build_nexus_lock(audit_callback=None) -> NEXUSLock:
    return NEXUSLock(audit_callback)


__all__ = [
    "DeviceType",
    "AccessLevel",
    "Device",
    "DomoticAction",
    "NEXUSLock",
    "build_nexus_lock",
]