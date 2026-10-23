"""Política de permisos tests."""

from __future__ import annotations

from abril.services.policy import (
    PermissionPolicy,
    ActionKind,
    PermissionLevel,
)


def test_default_policy_allows_open_search():
    policy = PermissionPolicy()
    for action in (ActionKind.OPEN, ActionKind.SEARCH, ActionKind.SUMMARIZE, ActionKind.LIST):
        decision = policy.evaluate(action)
        assert decision.allowed is True
        assert decision.level == PermissionLevel.ALLOW
        assert decision.requires_confirmation is False


def test_default_policy_asks_for_read_write():
    policy = PermissionPolicy()
    for action in (ActionKind.READ, ActionKind.WRITE, ActionKind.NETWORK):
        decision = policy.evaluate(action)
        assert decision.allowed is True
        assert decision.level == PermissionLevel.ASK
        assert decision.requires_confirmation is True


def test_default_policy_denies_dangerous():
    policy = PermissionPolicy()
    for action in (ActionKind.DELETE, ActionKind.INSTALL, ActionKind.SYSTEM):
        decision = policy.evaluate(action)
        assert decision.allowed is False
        assert decision.level == PermissionLevel.DENY


def test_policy_respects_path_restrictions():
    policy = PermissionPolicy()
    policy.set_rule(ActionKind.READ, PermissionLevel.ALLOW, paths=["/home/user/**"])

    decision = policy.evaluate(ActionKind.READ, args={"path": "/home/user/document.txt"})
    assert decision.allowed is True

    decision = policy.evaluate(ActionKind.READ, args={"path": "/etc/passwd"})
    assert decision.allowed is False


def test_policy_risk_threshold():
    policy = PermissionPolicy()
    policy.set_rule(ActionKind.EXECUTE, PermissionLevel.ALLOW, max_risk=5)

    decision = policy.evaluate(ActionKind.EXECUTE, risk_score=3)
    assert decision.allowed is True

    decision = policy.evaluate(ActionKind.EXECUTE, risk_score=7)
    assert decision.allowed is False


def test_policy_serialization_roundtrip():
    policy = PermissionPolicy()
    policy.set_rule(ActionKind.WRITE, PermissionLevel.ALLOW, paths=["/tmp/**"])

    data = policy.to_dict()
    restored = PermissionPolicy.from_dict(data)

    decision = restored.evaluate(ActionKind.WRITE, args={"path": "/tmp/test.txt"})
    assert decision.allowed is True
    assert decision.requires_confirmation is False
