#!/usr/bin/env python3
"""Abril — Asistente personal en terminal. 100% local, control total por Nexora."""

from __future__ import annotations

import json
import os
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from abril.config import Settings, CREATOR_COMPANY, ASSISTANT_NAME
from abril.providers.factory import create_provider
from abril.services.actions import ActionsService, ActionError
from abril.services.chat import ChatService, InvalidConversation
from abril.services.memory import MemoryService


# ═════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE APARIENCIA (conservadora, estilo terminal)
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

# Arte ASCII para la palabra "ABRIL" (color indigo)
_INDIGO = Colors.rgb(75, 0, 130)
BANNER_ASCII = f"""{_INDIGO}
██╗       █████╗ ██████╗ ██████╗ ██╗██╗     
╚██╗     ██╔══██╗██╔══██╗██╔══██╗██║██║     
 ╚██╗    ███████║██████╔╝██████╔╝██║██║     
 ██╔╝    ██╔══██║██╔══██╗██╔══██╗██║██║     
██╔╝     ██║  ██║██████╔╝██║  ██║██║███████╗
╚═╝      ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝
{Colors.RESET}"""


TIPS = [
    # "Escribe 'abre <app>' para abrir una aplicación instalada.",
    # "Escribe 'volumen <0-100>' para ajustar el volumen del sistema.",
    # "Escribe 'mover <origen> <destino>' para mover un archivo o carpeta.",
    # "Escribe 'copiar <origen> <destino>' para copiar un archivo.",
    # "Escribe 'borrar <archivo>' para eliminar un archivo (requiere confirmación).",
    # "Escribe 'listar <ruta>' para ver el contenido de un directorio.",
    # "Escribe 'leer <archivo>' para leer un archivo de texto.",
    # "Escribe 'crear <archivo>' para crear un nuevo archivo de texto.",
    # "Usa '/memoria' para ver preferencias y rutinas guardadas.",
    # "Usa '/acciones' para ver el historial de acciones ejecutadas.",
    # "Escribe 'salir' o presiona Ctrl+C para terminar.",

    "Escribe '/ayuda' para obtener mas informacion.",
    "Escribe codigo, preguntas o comandos y te ayudare a resolverlos.",
    "Se especifico para mejores resultados."
]


# ═════════════════════════════════════════════════════════════════════════════
#  UI DE TERMINAL
# ═════════════════════════════════════════════════════════════════════════════

class TerminalUI:
    """Interfaz de terminal con layout conservador."""

    def __init__(self, width: int = 90) -> None:
        self.width = width
        self._typing = False
        self._typing_thread: threading.Thread | None = None
        self.messages: list[tuple[str, str]] = []  # (role, text)

    def clear(self) -> None:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def print_banner(self) -> None:
        print(BANNER_ASCII)
        print(f"  {Colors.GRAY}Tips para empezar:{Colors.RESET}")
        for tip in TIPS[:3]:
            print(f"  {Colors.DIM}•{Colors.RESET} {tip}")
        print()

    def print_status_bar(self, provider_name: str, model: str, ready: bool) -> None:
        status_text = f"{Colors.GREEN}● Listo{Colors.RESET}" if ready else f"{Colors.RED}● No disponible{Colors.RESET}"
        line = (
            f"{Colors.DIM}Motor:{Colors.RESET} {provider_name}  │  "
            f"{Colors.DIM}Modelo:{Colors.RESET} {model}  │  "
            f"{Colors.DIM}Estado:{Colors.RESET} {status_text}"
        )
        print(f"{Colors.BRIGHT_BLACK}─" * self.width + f"{Colors.RESET}")
        print(line)
        print(f"{Colors.BRIGHT_BLACK}─" * self.width + f"{Colors.RESET}")

    def print_messages(self) -> None:
        if not self.messages:
            print(f"  {Colors.DIM}Sin conversación todavía. Escribe algo para empezar.{Colors.RESET}")
            return
        for role, text in self.messages[-12:]:
            if role == "user":
                print(f"{Colors.BRIGHT_CYAN}> {text}{Colors.RESET}")
            else:
                print(f"{Colors.BRIGHT_MAGENTA}{ASSISTANT_NAME}{Colors.RESET} {text}")
        print()

    def print_input_prompt(self) -> str:
        return f"{Colors.BRIGHT_GREEN}>{Colors.RESET} "

    def print_system(self, text: str) -> None:
        print(f"{Colors.GRAY}[sistema] {text}{Colors.RESET}")

    def print_warning(self, text: str) -> None:
        print(f"{Colors.YELLOW}[aviso] {text}{Colors.RESET}")

    def print_error(self, text: str) -> None:
        print(f"{Colors.RED}[error] {text}{Colors.RESET}")

    def print_success(self, text: str) -> None:
        print(f"{Colors.GREEN}[ok] {text}{Colors.RESET}")

    def print_help(self) -> None:
        print(f"""
{Colors.BRIGHT_CYAN}Comandos directos (sin IA):{Colors.RESET}
  {Colors.BRIGHT_GREEN}abre <app>{Colors.RESET}         — Abre una aplicación instalada
  {Colors.BRIGHT_GREEN}volumen <0-100>{Colors.RESET}    — Ajusta el volumen del sistema
  {Colors.BRIGHT_GREEN}mover <origen> <destino>{Colors.RESET} — Mueve archivo/carpeta
  {Colors.BRIGHT_GREEN}copiar <origen> <destino>{Colors.RESET}  — Copia archivo/carpeta
  {Colors.BRIGHT_GREEN}borrar <archivo>{Colors.RESET}     — Elimina un archivo
  {Colors.BRIGHT_GREEN}listar <ruta>{Colors.RESET}        — Lista contenido de directorio
  {Colors.BRIGHT_GREEN}leer <archivo>{Colors.RESET}       — Lee un archivo de texto
  {Colors.BRIGHT_GREEN}crear <archivo>{Colors.RESET}      — Crea un archivo de texto

{Colors.BRIGHT_CYAN}Comandos del sistema:{Colors.RESET}
  {Colors.BRIGHT_GREEN}/ayuda{Colors.RESET}       — Muestra esta ayuda
  {Colors.BRIGHT_GREEN}/memoria{Colors.RESET}     — Ver preferencias y rutinas
  {Colors.BRIGHT_GREEN}/acciones{Colors.RESET}    — Ver historial de acciones
  {Colors.BRIGHT_GREEN}/confirmar{Colors.RESET}   — Confirmar acción pendiente
  {Colors.BRIGHT_GREEN}/cancelar{Colors.RESET}    — Cancelar acción pendiente
  {Colors.BRIGHT_GREEN}/limpiar{Colors.RESET}     — Limpiar conversación
  {Colors.BRIGHT_GREEN}/estado{Colors.RESET}      — Estado del motor
  {Colors.BRIGHT_GREEN}/historial{Colors.RESET}   — Ver mensajes del historial cargado

{Colors.DIM}Todo lo demás se envía al modelo local para responder.{Colors.RESET}
""")

    def start_typing(self) -> None:
        self._typing = True
        self._typing_thread = threading.Thread(target=self._animate_typing, daemon=True)
        self._typing_thread.start()

    def stop_typing(self) -> None:
        self._typing = False
        if self._typing_thread:
            self._typing_thread.join(timeout=0.3)
        sys.stdout.write("\r" + " " * 20 + "\r")
        sys.stdout.flush()

    def _animate_typing(self) -> None:
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while self._typing:
            sys.stdout.write(f"\r{Colors.BRIGHT_MAGENTA}{dots[i % len(dots)]}{Colors.RESET}  ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def print_assistant(self, text: str) -> None:
        self.stop_typing()
        print(f"{Colors.BRIGHT_MAGENTA}{ASSISTANT_NAME}{Colors.RESET} {text}")

    def add_message(self, role: str, text: str) -> None:
        self.messages.append((role, text))

    def print_memory(self, prefs: dict, routines: list) -> None:
        print(f"\n{Colors.BRIGHT_CYAN}═══ MEMORIA ═══{Colors.RESET}")
        if prefs:
            print(f"  {Colors.BLUE}Preferencias:{Colors.RESET}")
            for k, v in prefs.items():
                print(f"    {Colors.GREEN}•{Colors.RESET} {k} = {v}")
        else:
            print(f"  {Colors.DIM}Sin preferencias guardadas.{Colors.RESET}")
        if routines:
            print(f"  {Colors.BLUE}Rutinas:{Colors.RESET}")
            for r in routines:
                estado = f"{Colors.GREEN}confirmada{Colors.RESET}" if r.get("confirmed") else f"{Colors.YELLOW}pendiente{Colors.RESET}"
                print(f"    {Colors.GREEN}•{Colors.RESET} {r['name']} — {r.get('description', '')} [{estado}]")
        else:
            print(f"  {Colors.DIM}Sin rutinas guardadas.{Colors.RESET}")
        print()

    def print_actions(self, log: list, pending: list) -> None:
        print(f"\n{Colors.BRIGHT_CYAN}═══ ACCIONES ═══{Colors.RESET}")
        if pending:
            print(f"  {Colors.BLUE}Pendientes:{Colors.RESET}")
            for p in pending:
                print(f"    {Colors.YELLOW}⏳{Colors.RESET} [{p['id'][:8]}] {p['detail']}")
        else:
            print(f"  {Colors.DIM}Sin acciones pendientes.{Colors.RESET}")
        if log:
            print(f"  {Colors.BLUE}Historial:{Colors.RESET}")
            for entry in log[-10:]:
                print(f"    {Colors.GRAY}{entry['time']}{Colors.RESET} {entry['action']} — {entry['result']}")
        else:
            print(f"  {Colors.DIM}Sin historial.{Colors.RESET}")
        print()

    def confirm_action(self, detail: str, dangerous: bool = False) -> bool:
        prefix = f"{Colors.RED}⚠ PELIGROSO{Colors.RESET} " if dangerous else ""
        print(f"{Colors.YELLOW}¿Confirmar?{Colors.RESET} {prefix}{detail}")
        if dangerous:
            print(f"  {Colors.RED}Escribe 'CONFIRMO' para proceder.{Colors.RESET}")
            resp = input(f"  {Colors.CYAN}[CONFIRMO/cancelar]{Colors.RESET} ").strip()
            return resp == "CONFIRMO"
        resp = input(f"  {Colors.CYAN}[s/N]{Colors.RESET} ").strip().lower()
        return resp in {"s", "si", "sí", "y", "yes"}

    def print_pending(self, pending: list) -> None:
        if not pending:
            print(f"  {Colors.DIM}Sin acciones pendientes.{Colors.RESET}")
            return
        print(f"  {Colors.BLUE}Pendientes:{Colors.RESET}")
        for p in pending:
            icon = {"open": "📱", "search": "🔍", "summarize": "📄", "execute": "⚡", "read": "📖", "write": "✍️", "list": "📁", "move": "📦", "copy": "📋", "delete": "🗑️", "volume": "🔊"}.get(p.get("kind", ""), "⏳")
            print(f"    {Colors.YELLOW}{icon}{Colors.RESET} [{p['id'][:8]}] {p['detail']} {Colors.DIM}({p.get('kind','')}){Colors.RESET}")


# ═════════════════════════════════════════════════════════════════════════════
#  COMANDOS DIRECTOS (sin IA)
# ═════════════════════════════════════════════════════════════════════════════

# Aliases comunes de aplicaciones (español → términos de búsqueda)
APP_ALIASES = {
    "calculadora": ["calculator", "calc"],
    "calculator": ["calculator", "calc"],
    "terminal": ["terminal", "console", "konsole", "gnome-terminal"],
    "firefox": ["firefox", "navegador"],
    "navegador": ["firefox", "chrome", "chromium", "browser"],
    "editor": ["gedit", "text editor", "editor"],
    "archivos": ["files", "nautilus", "dolphin", "thunar", "file manager"],
    "configuración": ["settings", "control center", "gnome-control-center"],
    "ajustes": ["settings", "control center", "gnome-control-center"],
    "captura": ["screenshot", "captura de pantalla"],
}


def resolve_app_id(actions: ActionsService, query: str) -> str | None:
    """Busca app_id por nombre parcial usando aliases."""
    query = query.lower()
    search_terms = [query]
    if query in APP_ALIASES:
        search_terms.extend(APP_ALIASES[query])
    for app_id, info in actions.apps.items():
        app_id_lower = app_id.lower()
        name_lower = info["name"].lower()
        for term in search_terms:
            if term in app_id_lower or term in name_lower:
                return app_id
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  HISTORIAL DE CONVERSACIÓN PERSISTENTE (Fase A)
# ═════════════════════════════════════════════════════════════════════════════

CHAT_HISTORY_FILE = "chat_history.json"
MAX_HISTORY_MESSAGES = 100  # máximo de mensajes a guardar en disco


def load_chat_history(data_dir: Path) -> list[dict[str, str]]:
    """Carga el historial de conversación desde disco."""
    path = data_dir / CHAT_HISTORY_FILE
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, list):
            return data[-MAX_HISTORY_MESSAGES:]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_chat_history(data_dir: Path, history: list[dict[str, str]]) -> None:
    """Persiste el historial de conversación en disco."""
    path = data_dir / CHAT_HISTORY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(history[-MAX_HISTORY_MESSAGES:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(path)


class DirectCommands:
    """Comandos directos que se ejecutan sin pasar por la IA."""

    def __init__(self, ui: TerminalUI, actions: ActionsService) -> None:
        self.ui = ui
        self.actions = actions

    def handle(self, user_input: str) -> bool:
        """Devuelve True si el comando fue manejado directamente."""
        text = user_input.strip()
        if not text:
            return False

        parts = shlex.split(text)
        if not parts:
            return False
        cmd = parts[0].lower()

        if cmd == "abre":
            return self._cmd_open(parts[1:])
        if cmd == "volumen":
            return self._cmd_volume(parts[1:])
        if cmd == "mover":
            return self._cmd_move(parts[1:])
        if cmd == "copiar":
            return self._cmd_copy(parts[1:])
        if cmd == "borrar":
            return self._cmd_delete(parts[1:])
        if cmd == "listar":
            return self._cmd_list(parts[1:])
        if cmd == "leer":
            return self._cmd_read(parts[1:])
        if cmd == "crear":
            return self._cmd_create(parts[1:])
        return False

    # ── open ──
    def _cmd_open(self, args: list[str]) -> bool:
        if not args:
            self.ui.print_error("Uso: abre <nombre de aplicación>")
            return True
        query = " ".join(args)
        # Búsqueda directa primero
        matches = []
        q_lower = query.lower()
        for app_id, info in self.actions.apps.items():
            if q_lower in app_id.lower() or q_lower in info["name"].lower():
                matches.append((app_id, info["name"]))
        # Si no hay coincidencia directa, usar aliases
        if not matches:
            app_id = resolve_app_id(self.actions, query)
            if app_id:
                matches = [(app_id, self.actions.apps[app_id]["name"])]
        if not matches:
            self.ui.print_warning(f"No encontré apps que coincidan con '{query}'")
            return True
        if len(matches) == 1:
            app_id, name = matches[0]
            self._propose("open", f"Abrir aplicación '{name}'", {"app_id": app_id})
        else:
            self.ui.print_system(f"Se encontraron {len(matches)} apps:")
            for i, (app_id, name) in enumerate(matches[:10], 1):
                print(f"  {i}. {name} ({app_id})")
            sel = input(f"  {Colors.CYAN}Selecciona número (1-{len(matches)}):{Colors.RESET} ").strip()
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(matches):
                    app_id, name = matches[idx]
                    self._propose("open", f"Abrir aplicación '{name}'", {"app_id": app_id})
                else:
                    self.ui.print_error("Selección inválida.")
            except ValueError:
                self.ui.print_error("Entrada inválida.")
        return True

    # ── volume ──
    def _cmd_volume(self, args: list[str]) -> bool:
        if not args:
            self.ui.print_error("Uso: volumen <0-100>")
            return True
        try:
            level = int(args[0])
            if not 0 <= level <= 100:
                raise ValueError
        except ValueError:
            self.ui.print_error("El volumen debe ser un número entre 0 y 100.")
            return True
        self._propose("volume", f"Ajustar volumen al {level}%", {"level": level})
        return True

    # ── move ──
    def _cmd_move(self, args: list[str]) -> bool:
        if len(args) < 2:
            self.ui.print_error("Uso: mover <origen> <destino>")
            return True
        src, dst = args[0], args[1]
        self._propose("move", f"Mover '{src}' → '{dst}'", {"src": src, "dst": dst})
        return True

    # ── copy ──
    def _cmd_copy(self, args: list[str]) -> bool:
        if len(args) < 2:
            self.ui.print_error("Uso: copiar <origen> <destino>")
            return True
        src, dst = args[0], args[1]
        self._propose("copy", f"Copiar '{src}' → '{dst}'", {"src": src, "dst": dst})
        return True

    # ── delete ──
    def _cmd_delete(self, args: list[str]) -> bool:
        if not args:
            self.ui.print_error("Uso: borrar <archivo>")
            return True
        target = args[0]
        self._propose("delete", f"Borrar '{target}'", {"target": target})
        return True

    # ── list ──
    def _cmd_list(self, args: list[str]) -> bool:
        path = args[0] if args else "."
        self._propose("list", f"Listar directorio '{path}'", {"path": path})
        return True

    # ── read ──
    def _cmd_read(self, args: list[str]) -> bool:
        if not args:
            self.ui.print_error("Uso: leer <archivo>")
            return True
        self._propose("read", f"Leer archivo '{args[0]}'", {"path": args[0]})
        return True

    # ── create ──
    def _cmd_create(self, args: list[str]) -> bool:
        if not args:
            self.ui.print_error("Uso: crear <archivo>")
            return True
        content = input(f"  {Colors.CYAN}Contenido del archivo:{Colors.RESET} ").strip()
        self._propose("write", f"Crear archivo '{args[0]}'", {"path": args[0], "content": content})
        return True

    # ── execute helper (sin confirmación) ──
    def _propose(self, kind: str, detail: str, args: dict[str, Any]) -> None:
        try:
            action_id = self.actions.propose_action(kind, detail, args)
            result = self.actions.confirm_action(action_id)
            self.ui.print_success(f"✓ Ejecutado: {result}")
        except ActionError as e:
            self.ui.print_error(str(e))


# ═════════════════════════════════════════════════════════════════════════════
#  APLICACIÓN PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════


def main() -> int:
    try:
        settings = Settings.load()
    except Exception as e:
        print(f"{Colors.RED}[error] Configuración inválida: {e}{Colors.RESET}")
        print("  Copia .env.example a .env y ajusta OLLAMA_URL / OLLAMA_MODEL")
        return 1

    ui = TerminalUI()
    ui.clear()
    ui.print_banner()

    provider = create_provider(settings)
    chat = ChatService(provider, settings)
    actions = ActionsService(settings, chat)
    memory = MemoryService(settings, actions)
    direct = DirectCommands(ui, actions)

    # Fase A: cargar historial persistente
    history: list[dict[str, str]] = load_chat_history(settings.data_dir)

    st = provider.status()
    ui.print_status_bar(provider.name, provider.model, st.get("ready", False))
    if not st.get("ready"):
        ui.print_warning(f"Ollama no responde o el modelo '{settings.ollama_model}' no está descargado.")
        ui.print_system(f"Ejecuta: ollama pull {settings.ollama_model}")
        ui.print_system("Y asegúrate de que 'ollama serve' esté corriendo.\n")

    if history:
        ui.print_system(f"Historial cargado: {len(history)} mensaje(s) recuperado(s) de la sesión anterior.")

    while True:
        try:
            user_input = input(ui.print_input_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.GRAY}Chao.{Colors.RESET}")
            return 0

        if not user_input:
            continue

        # Comandos de salida
        if user_input.lower() in {"salir", "exit", "quit", "q"}:
            save_chat_history(settings.data_dir, history)
            print(f"{Colors.GRAY}Chao. Historial guardado.{Colors.RESET}")
            return 0

        # Comandos directos (sin IA)
        if direct.handle(user_input):
            # Mostrar acciones pendientes después de ejecutar
            ui.print_pending(actions.list_pending())
            continue

        # Comandos del sistema (con /)
        if user_input.startswith("/"):
            if user_input == "/ayuda":
                ui.print_help()
                continue
            if user_input == "/memoria":
                ui.print_memory(memory.get_preferences(), memory.list_routines())
                continue
            if user_input == "/acciones":
                ui.print_actions(actions.audit_log(), actions.list_pending())
                continue
            if user_input == "/historial":
                ui.print_system(f"Mensajes en historial: {len(history)}")
                if history:
                    for i, m in enumerate(history[-10:], 1):
                        role = "Tú" if m["role"] == "user" else ASSISTANT_NAME
                        print(f"  {i}. {role}: {m['content'][:80]}")
                continue
            if user_input == "/confirmar":
                pending = actions.list_pending()
                if not pending:
                    ui.print_system("No hay acciones pendientes.")
                    continue
                ui.print_pending(pending)
                action_id = input(f"  {Colors.CYAN}ID de acción a confirmar:{Colors.RESET} ").strip()
                if not action_id:
                    ui.print_system("Cancelado.")
                    continue
                matches = [p for p in pending if p["id"].startswith(action_id)]
                if not matches:
                    ui.print_error(f"No hay acción que empiece por '{action_id}'")
                    continue
                if len(matches) > 1:
                    ui.print_error("Múltiples coincidencias. Usa más caracteres.")
                    continue
                item = matches[0]
                dangerous = item.get("args", {}).get("dangerous", item["kind"] in {"execute", "write", "move", "delete"})
                if ui.confirm_action(item["detail"], dangerous):
                    try:
                        result = actions.confirm_action(item["id"])
                        ui.print_success(f"Ejecutada: {result}")
                    except Exception as e:
                        ui.print_error(f"Falló: {e}")
                else:
                    actions.cancel_action(item["id"])
                    ui.print_system("Acción cancelada.")
                continue
            if user_input == "/cancelar":
                pending = actions.list_pending()
                if not pending:
                    ui.print_system("No hay acciones pendientes.")
                    continue
                ui.print_pending(pending)
                action_id = input(f"  {Colors.CYAN}ID de acción a cancelar:{Colors.RESET} ").strip()
                if not action_id:
                    ui.print_system("Cancelado.")
                    continue
                matches = [p for p in pending if p["id"].startswith(action_id)]
                if not matches:
                    ui.print_error(f"No hay acción que empiece por '{action_id}'")
                    continue
                if len(matches) > 1:
                    ui.print_error("Múltiples coincidencias. Usa más caracteres.")
                    continue
                actions.cancel_action(matches[0]["id"])
                ui.print_system("Acción cancelada.")
                continue
            if user_input == "/limpiar":
                history.clear()
                save_chat_history(settings.data_dir, history)
                ui.print_system("Conversación limpiada y historial guardado.")
                continue
            if user_input == "/estado":
                st = provider.status()
                ui.print_status_bar(provider.name, provider.model, st.get("ready", False))
                continue
            ui.print_error(f"Comando desconocido: {user_input}")
            continue

        # Mensaje normal al modelo
        ui.add_message("user", user_input)
        history.append({"role": "user", "content": user_input})

        ui.start_typing()
        try:
            answer = chat.reply(history)
            ui.stop_typing()
            ui.print_assistant(answer)
            ui.add_message("assistant", answer)
            history.append({"role": "assistant", "content": answer})
            # Fase A: guardar historial después de cada intercambio
            save_chat_history(settings.data_dir, history)
        except InvalidConversation as e:
            ui.stop_typing()
            ui.print_error(str(e))
            history.pop()
        except Exception as e:
            ui.stop_typing()
            ui.print_error(f"Error: {e}")
            history.pop()


if __name__ == "__main__":
    sys.exit(main())
