"""NEXUS-LOCK tests."""

from __future__ import annotations

from abril.services.nexus_lock import (
    Device,
    DeviceType,
    AccessLevel,
    DomoticAction,
    build_nexus_lock,
)


def test_nexus_lock_register_and_list():
    lock = build_nexus_lock()
    device = Device(
        id="light_1",
        name="Salón",
        type=DeviceType.LIGHT,
        protocol="matter",
        endpoint="192.168.1.50",
    )
    lock.register_device(device)

    devices = lock.list_devices()
    assert len(devices) == 1
    assert devices[0].id == "light_1"


def test_nexus_lock_grant_revoke_access():
    lock = build_nexus_lock()
    device = Device(id="lock_1", name="Puerta", type=DeviceType.LOCK, protocol="mqtt", endpoint="topic/door")
    lock.register_device(device)

    assert lock.grant_access("lock_1", AccessLevel.CONTROL) is True
    assert lock.get_device("lock_1").access_level == AccessLevel.CONTROL

    assert lock.revoke_access("lock_1") is True
    assert lock.get_device("lock_1").access_level == AccessLevel.NONE


def test_nexus_lock_execute_action_success():
    lock = build_nexus_lock()
    device = Device(id="light_1", name="Luz", type=DeviceType.LIGHT, protocol="matter", endpoint="...")
    lock.register_device(device)
    lock.grant_access("light_1", AccessLevel.CONTROL)

    action = DomoticAction(device_id="light_1", command="turn_on", params={"brightness": 80})
    result = lock.execute(action)

    assert result.success is True
    assert result.error is None


def test_nexus_lock_execute_blocked_by_global_lock():
    lock = build_nexus_lock()
    device = Device(id="light_1", name="Luz", type=DeviceType.LIGHT, protocol="matter", endpoint="...")
    lock.register_device(device)
    lock.grant_access("light_1", AccessLevel.CONTROL)

    lock.lock_all()

    action = DomoticAction(device_id="light_1", command="turn_on", params={})
    result = lock.execute(action)

    assert result.success is False
    assert "bloqueo global" in result.error


def test_nexus_lock_execute_denied_no_access():
    lock = build_nexus_lock()
    device = Device(id="lock_1", name="Puerta", type=DeviceType.LOCK, protocol="mqtt", endpoint="...")
    lock.register_device(device)
    # Sin grant_access

    action = DomoticAction(device_id="lock_1", command="unlock", params={})
    result = lock.execute(action)

    assert result.success is False
    assert "Sin acceso" in result.error


def test_nexus_lock_read_only_device():
    lock = build_nexus_lock()
    device = Device(id="sensor_1", name="Temp", type=DeviceType.SENSOR, protocol="mqtt", endpoint="...")
    lock.register_device(device)
    lock.grant_access("sensor_1", AccessLevel.READ)

    # Lectura permitida
    action = DomoticAction(device_id="sensor_1", command="get_state", params={})
    result = lock.execute(action)
    assert result.success is True

    # Control denegado
    action = DomoticAction(device_id="sensor_1", command="set_config", params={})
    result = lock.execute(action)
    assert result.success is False
    assert "Solo lectura" in result.error


def test_nexus_lock_unknown_device():
    lock = build_nexus_lock()
    action = DomoticAction(device_id="no-existe", command="test", params={})
    result = lock.execute(action)

    assert result.success is False
    assert "no registrado" in result.error