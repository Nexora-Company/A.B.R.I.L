"""Renderizador de terminal de A.B.R.I.L.

Layout inspirado en los asistentes de terminal modernos: banner centrado,
compositor con acento morado, bloques de conversación y metadatos de
rendimiento. Usa solo la biblioteca estándar y degrada a texto plano cuando
la salida no es una terminal interactiva.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import textwrap
import threading
import time

from .. import __version__
from ..config import ASSISTANT_NAME


# ═════════════════════════════════════════════════════════════════════════════
#  COLORES
# ═════════════════════════════════════════════════════════════════════════════

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[38;5;244m"
    BRIGHT_BLACK = "\033[38;5;238m"
    BRIGHT_WHITE = "\033[38;5;252m"
    BRIGHT_CYAN = "\033[38;5;87m"
    BRIGHT_MAGENTA = "\033[38;5;171m"
    BRIGHT_YELLOW = "\033[38;5;226m"
    BRIGHT_GREEN = "\033[38;5;154m"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        return f"\033[48;2;{r};{g};{b}m"


_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

_PURPLE = Colors.rgb(168, 85, 247)
_PURPLE_DEEP = Colors.rgb(75, 3, 130)
_PURPLE_LIGHT = Colors.rgb(233, 213, 255)
_PURPLE_BG = Colors.bg_rgb(75, 3, 130)
_NEXORA_RED = Colors.rgb(179, 27, 27)
_GREEN = Colors.rgb(74, 222, 128)
_YELLOW = Colors.rgb(250, 204, 21)
_RED = Colors.rgb(248, 113, 113)
_MUTED = Colors.rgb(148, 163, 184)
_FAINT = Colors.rgb(82, 82, 91)

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _style(text: str, *codes: str) -> str:
    if not _COLOR or not codes:
        return text
    return "".join(codes) + text + Colors.RESET


def _visible_width(text: str) -> int:
    return len(_ANSI_RE.sub("", text))


def _blend(start: str, end: str, ratio: float) -> str:
    """Interpola dos colores RGB en formato ANSI truecolor."""
    ratio = max(0.0, min(1.0, ratio))
    a = [int(part) for part in re.findall(r"\d+", start)[-3:]]
    b = [int(part) for part in re.findall(r"\d+", end)[-3:]]
    r, g, bl = (round(a[i] + (b[i] - a[i]) * ratio) for i in range(3))
    return Colors.rgb(r, g, bl)


# Arte original de A.B.R.I.L. No se modifica: solo se colorea y centra.
BANNER_LINES = [
    "██╗       █████╗ ██████╗ ██████╗ ██╗██╗",
    "╚██╗     ██╔══██╗██╔══██╗██╔══██╗██║██║",
    " ╚██╗    ███████║██████╔╝██████╔╝██║██║",
    " ██╔╝    ██╔══██║██╔══██╗██╔══██╗██║██║",
    "██╔╝     ██║  ██║██████╔╝██║  ██║██║███████╗",
    "╚═╝      ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝",
]

_TIPS = [
    "Escribe /ayuda para ver todos los comandos.",
    "Pregunta, pide código o encarga una tarea en lenguaje natural.",
    "Usa /config para activar funciones y /brace para revisar permisos.",
]


# ═════════════════════════════════════════════════════════════════════════════
#  UI DE TERMINAL
# ═════════════════════════════════════════════════════════════════════════════

class TerminalUI:
    """Interfaz de terminal con banner, compositor y bloques de conversación."""

    def __init__(self, width: int | None = None) -> None:
        self.width = width or self._detect_width()
        self._typing = False
        self._typing_thread: threading.Thread | None = None
        self.messages: list[tuple[str, str]] = []  # (role, text)
        self.provider_name = "local"
        self.model = ""
        self.ready = True

    # ── Contexto ─────────────────────────────────────────────────────

    @staticmethod
    def _detect_width() -> int:
        columns = shutil.get_terminal_size((92, 24)).columns
        return max(56, min(columns - 2, 96))

    def set_status(self, provider_name: str, model: str, ready: bool) -> None:
        self.provider_name = provider_name or "local"
        self.model = model or ""
        self.ready = ready

    def _build_label(self) -> str:
        target = f"{self.provider_name}/{self.model}" if self.model else self.provider_name
        return _style("Build", _PURPLE, Colors.BOLD) + _style(f" · {target}", _MUTED)

    def _state_chip(self) -> str:
        target = f"{self.provider_name} · {self.model}" if self.model else self.provider_name
        if self.ready:
            return f"{_style('●', _GREEN)} {_style(f'{target} · listo', _MUTED)}"
        return f"{_style('●', _RED)} {_style(f'{target} · sin conexión', _MUTED)}"

    # ── Pantalla de bienvenida ───────────────────────────────────────

    def clear(self) -> None:
        if not sys.stdout.isatty():
            return
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def print_welcome(
        self,
        provider_name: str | None = None,
        model: str | None = None,
        ready: bool | None = None,
    ) -> None:
        """Dibuja la pantalla inicial con el banner y las pistas principales."""
        if provider_name is not None:
            self.provider_name = provider_name
        if model is not None:
            self.model = model
        if ready is not None:
            self.ready = ready

        self._rule()
        print()
        banner_width = max(_visible_width(line) for line in BANNER_LINES)
        indent = max(0, (self.width - banner_width) // 2)
        for index, line in enumerate(BANNER_LINES):
            color = _blend(_PURPLE_DEEP, _PURPLE_LIGHT, index / max(1, len(BANNER_LINES) - 1))
            print(" " * (indent + 2) + _style(line, color))

        print()
        print(self._center(_style("asistente personal local", _MUTED)))
        brand = _style("Nexora", _NEXORA_RED, Colors.BOLD)
        print(self._center(_style("by ", _FAINT) + brand + _style(" · open core", _FAINT)))
        print()
        print(self._center(self._state_chip()))
        print()
        tip_width = max(len(f"· {tip}") for tip in _TIPS)
        tip_indent = " " * (max(0, (self.width - tip_width) // 2) + 2)
        for tip in _TIPS:
            print(tip_indent + _style("·", _PURPLE) + " " + _style(tip, _FAINT))
        print()
        print(f"  {_style(__version__.rjust(self.width), _FAINT)}")
        print()

    def print_session_header(self) -> None:
        """Cabecera de sesión con pestaña activa y versión."""
        left = _style(" A.B.R.I.L ", _PURPLE_BG, Colors.WHITE, Colors.BOLD)
        left += _style("  nueva sesión", _MUTED)
        right = _style(f"Nexora · {__version__}", _FAINT)
        gap = max(1, self.width - _visible_width(left) - _visible_width(right))
        print()
        print("  " + left + " " * gap + right)
        self._rule()

    # ── Compositor ───────────────────────────────────────────────────

    def print_input_prompt(self) -> str:
        bar = _style("┃", _PURPLE)
        arrow = _style("›", _PURPLE, Colors.BOLD)
        return f"\n  {bar}  {self._build_label()}\n  {bar}  {arrow} "

    def close_composer(self) -> None:
        print(f"  {_style('┗' + '━' * (self.width - 1), _FAINT)}")
        available = self.width - _visible_width(__version__) - 2
        hints = "/ayuda comandos · /config flags · /brace seguridad · salir salir"
        if _visible_width(hints) > available:
            hints = "/ayuda · /config · /brace · salir"
        if _visible_width(hints) > available:
            hints = ""
        left = _style(hints, _FAINT) if hints else ""
        right = _style(__version__, _FAINT)
        gap = max(1, self.width - _visible_width(left) - _visible_width(right))
        print("  " + left + " " * gap + right)

    def read_input(self) -> str:
        """Lee una línea dentro del compositor y cierra el marco al terminar."""
        try:
            return input(self.print_input_prompt()).strip()
        finally:
            if not sys.stdin.isatty():
                print()
            self.close_composer()

    # ── Mensajes ─────────────────────────────────────────────────────

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        lines: list[str] = []
        for raw in text.splitlines() or [""]:
            wrapped = textwrap.wrap(
                raw,
                width=width,
                break_long_words=True,
                break_on_hyphens=False,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            lines.extend(wrapped or [""])
        return lines

    def print_user(self, text: str) -> None:
        bar = _style("▎", _PURPLE)
        print(f"\n  {bar} {_style('Tú', _MUTED, Colors.BOLD)}")
        for line in self._wrap(text, max(20, self.width - 4)):
            print(f"  {bar} {line}")

    def print_assistant(
        self,
        text: str,
        *,
        elapsed: float | None = None,
        tokens_per_second: float | None = None,
    ) -> None:
        self.stop_typing()
        print(f"\n  {_style('●', _PURPLE)} {_style(ASSISTANT_NAME, _PURPLE, Colors.BOLD)}")
        for line in text.splitlines() or [""]:
            print(f"  {line}" if line else "")
        meta = [self.provider_name]
        if self.model:
            meta.append(self.model)
        if elapsed is not None:
            meta.append(f"{elapsed:.1f}s")
        if tokens_per_second:
            speed = f"{tokens_per_second:.0f}" if tokens_per_second >= 10 else f"{tokens_per_second:.1f}"
            meta.append(f"{speed} tok/s")
        print(f"  {_style('Build', _PURPLE)} {_style('· ' + ' · '.join(meta), _FAINT)}")

    def add_message(self, role: str, text: str) -> None:
        self.messages.append((role, text))

    def print_messages(self) -> None:
        if not self.messages:
            print(f"  {_style('Sin conversación todavía.', _FAINT)}")
            return
        for role, text in self.messages[-12:]:
            if role == "user":
                self.print_user(text)
            else:
                print(f"\n  {_style('●', _PURPLE)} {_style(ASSISTANT_NAME, _PURPLE, Colors.BOLD)}")
                for line in text.splitlines():
                    print(f"  {line}")
        print()

    # ── Avisos del sistema ───────────────────────────────────────────

    def print_status_bar(self, provider_name: str, model: str, ready: bool) -> None:
        self.set_status(provider_name, model, ready)
        print(f"  {self._state_chip()}")

    def print_system(self, text: str) -> None:
        print(f"  {_style('·', _FAINT)} {_style(text, _MUTED)}")

    def print_warning(self, text: str) -> None:
        print(f"  {_style('!', _YELLOW, Colors.BOLD)} {_style(text, _YELLOW)}")

    def print_error(self, text: str) -> None:
        print(f"  {_style('✗', _RED, Colors.BOLD)} {_style(text, _RED)}")

    def print_success(self, text: str) -> None:
        print(f"  {_style('✓', _GREEN, Colors.BOLD)} {_style(text, _GREEN)}")

    # ── Animación de espera ──────────────────────────────────────────

    def start_typing(self) -> None:
        self._typing = True
        self._typing_thread = threading.Thread(target=self._animate_typing, daemon=True)
        self._typing_thread.start()

    def stop_typing(self) -> None:
        self._typing = False
        if self._typing_thread:
            self._typing_thread.join(timeout=0.3)
            self._typing_thread = None
        if sys.stdout.isatty():
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

    def _animate_typing(self) -> None:
        if not sys.stdout.isatty():
            return
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        start = time.monotonic()
        index = 0
        while self._typing:
            elapsed = time.monotonic() - start
            line = f"{frames[index % len(frames)]} Pensando · {elapsed:.1f}s"
            sys.stdout.write("\r  " + _style(line, _PURPLE) + "\033[K")
            sys.stdout.flush()
            time.sleep(0.08)
            index += 1

    # ── Ayuda y vistas ───────────────────────────────────────────────

    def _rule(self) -> None:
        print(f"  {_style('─' * self.width, _FAINT)}")

    def _center(self, text: str) -> str:
        pad = max(0, (self.width - _visible_width(text)) // 2)
        return " " * (pad + 2) + text

    @staticmethod
    def _section(title: str) -> None:
        print()
        print(f"  {_style(title.upper(), _PURPLE, Colors.BOLD)}")
        print(f"  {_style('─' * len(title), _FAINT)}")

    @staticmethod
    def _entry(command: str, description: str) -> None:
        print(f"  {_style(command.ljust(28), Colors.BOLD)} {_style(description, _MUTED)}")

    def print_help(self) -> None:
        self._section("Comandos directos")
        self._entry("abre <app>", "Abre una aplicación instalada")
        self._entry("volumen <0-100>", "Ajusta el volumen del sistema")
        self._entry("mover <origen> <destino>", "Mueve un archivo o carpeta")
        self._entry("copiar <origen> <destino>", "Copia un archivo o carpeta")
        self._entry("borrar <archivo>", "Elimina un archivo (con confirmación)")
        self._entry("listar <ruta>", "Lista el contenido de un directorio")
        self._entry("leer <archivo>", "Lee un archivo de texto")
        self._entry("crear <archivo>", "Crea un archivo de texto")

        self._section("Sesión")
        self._entry("/ayuda", "Muestra esta ayuda")
        self._entry("/memoria", "Preferencias y rutinas guardadas")
        self._entry("/acciones", "Historial de acciones y pendientes")
        self._entry("/confirmar", "Confirma una acción pendiente")
        self._entry("/cancelar", "Cancela una acción pendiente")
        self._entry("/limpiar", "Limpia la conversación")
        self._entry("/estado", "Estado del motor y del modelo")
        self._entry("/historial", "Mensajes guardados de la sesión")
        self._entry("/version", "Versión de A.B.R.I.L")

        self._section("Configuración y seguridad")
        self._entry("/config [set|reset]", "Consulta o cambia los flags")
        self._entry("/brace", "Estado y capacidades de NEXO-BRACE")
        self._entry("/desbloquear [confirmar]", "Otorga consentimiento explícito")
        self._entry("/bloquear", "Revoca el consentimiento y bloquea accesos")

        self._section("Código y análisis")
        self._entry("/programar <archivo>", "Revisa código y propone cambios")
        self._entry("/ejecutar <archivo>", "Ejecuta y corrige errores con IA")
        self._entry("/revisar <archivo>", "Análisis detallado de código")
        self._entry("/analizar [qué]", "Analiza patrones de uso")
        self._entry("/ideas", "Sugerencias basadas en tu actividad")
        self._entry("/pensar <tema>", "Reflexión profunda sobre un tema")
        print()
        print(f"  {_style('Todo lo demás se envía al modelo local.', _FAINT)}")

    def print_memory(self, prefs: dict, routines: list) -> None:
        self._section("Memoria")
        if prefs:
            print(f"  {_style('Preferencias', _MUTED, Colors.BOLD)}")
            for key, value in prefs.items():
                print(f"  {_style('·', _PURPLE)} {key} {_style('=', _FAINT)} {value}")
        else:
            print(f"  {_style('Sin preferencias guardadas.', _FAINT)}")
        if routines:
            print(f"  {_style('Rutinas', _MUTED, Colors.BOLD)}")
            for routine in routines:
                state = (
                    _style("confirmada", _GREEN)
                    if routine.get("confirmed")
                    else _style("pendiente", _YELLOW)
                )
                print(f"  {_style('·', _PURPLE)} {routine['name']} — {routine.get('description', '')} [{state}]")
        else:
            print(f"  {_style('Sin rutinas guardadas.', _FAINT)}")
        print()

    def print_actions(self, log: list, pending: list) -> None:
        self._section("Acciones")
        if pending:
            print(f"  {_style('Pendientes', _MUTED, Colors.BOLD)}")
            for item in pending:
                print(f"  {_style('⏳', _YELLOW)} [{item['id'][:8]}] {item['detail']}")
        else:
            print(f"  {_style('Sin acciones pendientes.', _FAINT)}")
        if log:
            print(f"  {_style('Historial', _MUTED, Colors.BOLD)}")
            for entry in log[-10:]:
                print(
                    f"  {_style(entry['time'], _FAINT)} "
                    f"{entry['action']} {_style('—', _FAINT)} {entry['result']}"
                )
        else:
            print(f"  {_style('Sin historial.', _FAINT)}")
        print()

    def confirm_action(self, detail: str, dangerous: bool = False) -> bool:
        prefix = f"{_style('⚠ PELIGROSO', _RED, Colors.BOLD)} " if dangerous else ""
        print(f"  {_style('¿Confirmar?', _YELLOW)} {prefix}{detail}")
        if dangerous:
            note = _style("Escribe 'CONFIRMO' para proceder.", _RED)
            print(f"  {note}")
            response = input(f"  {_style('[CONFIRMO/cancelar]', _PURPLE)} ").strip()
            return response == "CONFIRMO"
        response = input(f"  {_style('[s/N]', _PURPLE)} ").strip().lower()
        return response in {"s", "si", "sí", "y", "yes"}

    def print_pending(self, pending: list) -> None:
        if not pending:
            print(f"  {_style('Sin acciones pendientes.', _FAINT)}")
            return
        print(f"  {_style('Pendientes', _MUTED, Colors.BOLD)}")
        icons = {
            "open": "📱",
            "search": "🔍",
            "summarize": "📄",
            "execute": "⚡",
            "read": "📖",
            "write": "✍️",
            "list": "📁",
            "move": "📦",
            "copy": "📋",
            "delete": "🗑️",
            "volume": "🔊",
        }
        for item in pending:
            icon = icons.get(item.get("kind", ""), "⏳")
            print(
                f"  {_style(icon, _YELLOW)} [{item['id'][:8]}] {item['detail']} "
                f"{_style('(' + item.get('kind', '') + ')', _FAINT)}"
            )


__all__ = ["Colors", "BANNER_LINES", "TerminalUI"]
