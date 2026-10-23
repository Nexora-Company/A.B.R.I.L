"""Shared test doubles."""

from __future__ import annotations


class FakeProvider:
    """In-memory provider that never touches Ollama."""

    name = "fake"
    model = "fake-model"

    def __init__(self, reply: str = "respuesta falsa") -> None:
        self.reply_text = reply
        self.calls: list[list[dict[str, str]]] = []
        self.ready = True

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.reply_text

    def status(self) -> dict[str, str | bool]:
        return {"ready": self.ready, "status_message": ""}


class RecordingUI:
    """Captures what the terminal UI would print."""

    def __init__(self) -> None:
        self.lines: list[tuple[str, str]] = []
        self.typing = False

    def _add(self, level: str, text: str) -> None:
        self.lines.append((level, text))

    def print_system(self, text: str) -> None:
        self._add("system", text)

    def print_warning(self, text: str) -> None:
        self._add("warning", text)

    def print_error(self, text: str) -> None:
        self._add("error", text)

    def print_success(self, text: str) -> None:
        self._add("success", text)

    def print_assistant(self, text: str) -> None:
        self._add("assistant", text)

    def start_typing(self) -> None:
        self.typing = True

    def stop_typing(self) -> None:
        self.typing = False

    def text(self) -> str:
        return "\n".join(line for _, line in self.lines)
