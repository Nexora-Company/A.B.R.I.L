"""Terminal layout tests."""

from __future__ import annotations

import re

from abril.ui.terminal import BANNER_LINES, TerminalUI

_ANSI = re.compile(r"\033\[[0-9;]*m")


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


def test_welcome_shows_banner_status_and_version(capsys) -> None:
    ui = TerminalUI(width=80)

    ui.print_welcome("ollama", "qwen2.5:3b", True)

    out = _plain(capsys.readouterr().out)
    for line in BANNER_LINES:
        assert line in out
    assert "asistente personal local" in out
    assert "by Nexora" in out
    assert "ollama · qwen2.5:3b · listo" in out
    assert "0.2.0" in out


def test_welcome_marks_offline_provider(capsys) -> None:
    ui = TerminalUI(width=80)

    ui.print_welcome("ollama", "qwen2.5:3b", False)

    out = _plain(capsys.readouterr().out)
    assert "sin conexión" in out


def test_session_header_and_user_block(capsys) -> None:
    ui = TerminalUI(width=80)
    ui.set_status("ollama", "qwen2.5:3b", True)

    ui.print_session_header()
    ui.print_user("hola mundo")

    out = _plain(capsys.readouterr().out)
    assert "nueva sesión" in out
    assert "Nexora" in out
    assert "▎ Tú" in out
    assert "hola mundo" in out


def test_assistant_block_includes_metrics(capsys) -> None:
    ui = TerminalUI(width=80)
    ui.set_status("ollama", "qwen2.5:3b", True)

    ui.print_assistant("respuesta", elapsed=1.25, tokens_per_second=42.0)

    out = _plain(capsys.readouterr().out)
    assert "● Abril" in out
    assert "respuesta" in out
    assert "Build · ollama · qwen2.5:3b · 1.2s · 42 tok/s" in out


def test_help_lists_key_commands(capsys) -> None:
    ui = TerminalUI(width=80)

    ui.print_help()

    out = _plain(capsys.readouterr().out)
    for command in ("/ayuda", "/config", "/brace", "/desbloquear", "/programar"):
        assert command in out


def test_status_messages_use_distinct_badges(capsys) -> None:
    ui = TerminalUI(width=80)

    ui.print_system("sistema")
    ui.print_warning("aviso")
    ui.print_error("error")
    ui.print_success("éxito")

    out = _plain(capsys.readouterr().out)
    assert "· sistema" in out
    assert "! aviso" in out
    assert "✗ error" in out
    assert "✓ éxito" in out


def test_composer_lines_fit_width(capsys) -> None:
    ui = TerminalUI(width=60)
    ui.set_status("ollama", "qwen2.5:3b", True)

    print(ui.print_input_prompt())
    ui.close_composer()

    lines = [line for line in _plain(capsys.readouterr().out).splitlines() if line]
    assert any("Build · ollama/qwen2.5:3b" in line for line in lines)
    assert any(line.startswith("  ┗") for line in lines)
    assert max(len(line) for line in lines) <= 62
