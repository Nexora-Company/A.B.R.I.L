"""Conversation validation and identity tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from abril.config import Settings
from abril.services.chat import ChatService, InvalidConversation
from tests.helpers import FakeProvider


def test_reply_prepends_system_prompt(settings: Settings, fake_provider: FakeProvider) -> None:
    service = ChatService(fake_provider, settings)

    answer = service.reply([{"role": "user", "content": "hola"}])

    assert answer == "respuesta falsa"
    assert len(fake_provider.calls) == 1
    messages = fake_provider.calls[0]
    assert messages[0]["role"] == "system"
    assert "Nexora" in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "hola"}


def test_reply_rejects_empty_conversation(settings: Settings, fake_provider: FakeProvider) -> None:
    service = ChatService(fake_provider, settings)

    with pytest.raises(InvalidConversation):
        service.reply([])


def test_reply_rejects_invalid_role(settings: Settings, fake_provider: FakeProvider) -> None:
    service = ChatService(fake_provider, settings)

    with pytest.raises(InvalidConversation):
        service.reply([{"role": "system", "content": "intruso"}])


def test_reply_trims_history(settings: Settings, fake_provider: FakeProvider, tmp_path: Path) -> None:
    limited = replace(settings, data_dir=tmp_path, max_history_messages=2)
    service = ChatService(fake_provider, limited)
    messages = [{"role": "user", "content": str(index)} for index in range(5)]

    service.reply(messages)

    sent = fake_provider.calls[0]
    assert len(sent) == 3  # system + 2 kept messages
    assert sent[-1]["content"] == "4"


def test_status_keeps_identity(settings: Settings, fake_provider: FakeProvider) -> None:
    service = ChatService(fake_provider, settings)

    status = service.status()

    assert status["name"] == "Abril"
    assert status["creator_company"] == "Nexora"
    assert status["provider"] == "fake"
    assert status["model"] == "fake-model"
