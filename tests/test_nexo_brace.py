"""NEXO-BRACE tests."""

from __future__ import annotations

from abril.services.nexo_brace import NEXOBraceState, build_nexo_brace


def test_nexo_brace_locked_by_default():
    brace = build_nexo_brace(
        hardware_tier="low",
        flags={},
        nexus_locked=True,
        user_consent=False,
    )
    assert brace.state == NEXOBraceState.LOCKED


def test_nexo_brace_partial_when_unlocked_no_consent():
    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={},
        nexus_locked=False,
        user_consent=False,
    )
    assert brace.state == NEXOBraceState.PARTIAL


def test_nexo_brace_full_when_unlocked_with_consent():
    brace = build_nexo_brace(
        hardware_tier="high",
        flags={},
        nexus_locked=False,
        user_consent=True,
    )
    assert brace.state == NEXOBraceState.FULL


def test_nexo_brace_router_unlocked_in_partial():
    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={"routing": True},
        policy_level="allow",
        nexus_locked=False,
        user_consent=False,
    )
    assert brace.is_unlocked("router") is True


def test_nexo_brace_router_locked_if_flag_off():
    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={"routing": False},
        policy_level="allow",
        nexus_locked=False,
        user_consent=False,
    )
    assert brace.is_unlocked("router") is False


def test_nexo_brace_voice_requires_full_and_consent():
    brace = build_nexo_brace(
        hardware_tier="high",
        flags={"voice": True},
        policy_level="allow",
        nexus_locked=False,
        user_consent=True,
    )
    assert brace.is_unlocked("voice") is True

    brace = build_nexo_brace(
        hardware_tier="high",
        flags={"voice": True},
        policy_level="allow",
        nexus_locked=False,
        user_consent=False,
    )
    assert brace.is_unlocked("voice") is False


def test_nexo_brace_domotics_requires_nexus_lock():
    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={"nexus_lock": True},
        policy_level="allow",
        nexus_locked=True,
        user_consent=True,
    )
    assert brace.is_unlocked("domotics") is False

    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={"nexus_lock": True},
        policy_level="allow",
        nexus_locked=False,
        user_consent=True,
    )
    assert brace.is_unlocked("domotics") is True


def test_nexo_brace_hardware_tier_blocks_low():
    brace = build_nexo_brace(
        hardware_tier="low",
        flags={"policy": True},
        policy_level="allow",
        nexus_locked=False,
        user_consent=False,
    )
    assert brace.is_unlocked("policy") is False  # requiere mid

    brace = build_nexo_brace(
        hardware_tier="mid",
        flags={"policy": True},
        policy_level="allow",
        nexus_locked=False,
        user_consent=False,
    )
    assert brace.is_unlocked("policy") is True


def test_nexo_brace_set_user_consent_refreshes_state():
    brace = build_nexo_brace(hardware_tier="mid", flags={}, nexus_locked=True)
    assert brace.state == NEXOBraceState.LOCKED

    brace.set_user_consent(True)
    assert brace.state == NEXOBraceState.PARTIAL

    brace.set_user_consent(False)
    assert brace.state == NEXOBraceState.LOCKED


def test_nexo_brace_set_nexus_locked_refreshes_state():
    brace = build_nexo_brace(hardware_tier="mid", flags={}, nexus_locked=True, user_consent=True)
    assert brace.state == NEXOBraceState.PARTIAL

    brace.set_nexus_locked(False)
    assert brace.state == NEXOBraceState.FULL
