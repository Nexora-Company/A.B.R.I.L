#!/usr/bin/env python3
"""Abril — Asistente personal en terminal. 100% local, control total."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from abril.config import Settings, CREATOR_COMPANY, CREATOR_DEVELOPER, ASSISTANT_NAME
from abril.providers.factory import create_provider
from abril.services.actions import ActionsService
from abril.services.chat import ChatService, InvalidConversation
from abril.services.memory import MemoryService


class TerminalUI:
    """Interfaz de terminal con colores y animaciones sutiles."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[38;5;113m"
    YELLOW = "\033[38;5;221m"
    CYAN = "\033[38;5;117m"
    MAGENTA = "\033[38;5;177m"
    RED = "\033[38;5;204m"
    GRAY = "\033[38;5;244m"
    BLUE = "\033[38;5;75m"

    def __init__(self) -> None:
        self._typing = False
        self._typing_thread: threading.Thread | None = None

    def print_banner(self) -> None:
        print(f"""
{self.CYAN}╔══════════════════════════════════════════════════════════╗
║  {self.MAGENTA}{ASSISTANT_NAME}{self.CYAN}  —  Asistente personal local                   ║
║  {self.GRAY}Creado por {CREATOR_DEVELOPER} @ {CREATOR_COMPANY}{self.CYAN}              ║
║  {self.GREEN}100% local · Ollama · Sin nube · Tú mandas{self.CYAN}          ║
╚══════════════════════════════════════════════════════════╝{self.RESET}
""")

    def print_status(self, provider_name: str, model: str, ready: bool) -> None:
        status = f"{self.GREEN}● Listo{self.RESET}" if ready else f"{self.RED}● {model} no disponible{self.RESET}"
        print(f"  {self.BLUE}Motor:{self.RESET} {provider_name}  |  {self.BLUE}Modelo:{self.RESET} {model}  |  {status}")
        print(f"  {self.GRAY}Escribe 'salir', 'exit' o Ctrl+C para terminar.{self.RESET}")
        print(f"  {self.GRAY}Comandos: /memoria, /acciones, /ayuda{self.RESET}\n")

    def print_user_prompt(self) -> str:
        return f"{self.YELLOW}▸{self.RESET} "

    def print_assistant_prefix(self) -> str:
        return f"{self.MAGENTA}{ASSISTANT_NAME}{self.RESET} {self.GRAY}›{self.RESET} "

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
            sys.stdout.write(f"\r{self.MAGENTA}{dots[i % len(dots)]}{self.RESET}  ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def print_assistant(self, text: str) -> None:
        self.stop_typing()
        prefix = self.print_assistant_prefix()
        print(f"{prefix}{text}")

    def print_system(self, text: str) -> None:
        print(f"{self.GRAY}[sistema] {text}{self.RESET}")

    def print_error(self, text: str) -> None:
        print(f"{self.RED}[error] {text}{self.RESET}")

    def print_warning(self, text: str) -> None:
        print(f"{self.YELLOW}[aviso] {text}{self.RESET}")

    def print_help(self) -> None:
        print(f"""
{self.CYAN}Comandos disponibles:{self.RESET}
  {self.YELLOW}/ayuda{self.RESET}       — Muestra esta ayuda
  {self.YELLOW}/memoria{self.RESET}     — Ver preferencias y rutinas guardadas
  {self.YELLOW}/acciones{self.RESET}    — Ver log de acciones y pendientes
  {self.YELLOW}/confirmar{self.RESET}   — Confirmar una acción pendiente
  {self.YELLOW}/cancelar{self.RESET}    — Cancelar una acción pendiente
  {self.YELLOW}/limpiar{self.RESET}     — Limpiar conversación actual
  {self.YELLOW}/estado{self.RESET}      — Estado del motor y modelo
  {self.YELLOW}salir / exit{self.RESET}   — Salir de Abril

{self.GRAY}Acciones soportadas (se proponen, tú confirmas):
  📱 open       — Abrir app instalada
  🔍 search     — Buscar archivos
  📄 summarize  — Resumir archivo/PDF
  ⚡ execute    — Ejecutar comando en terminal
  📖 read       — Leer archivo de texto
  ✍️ write      — Crear/escribir archivo
  📁 list       — Listar directorio

Todo lo demás se envía al modelo. Yo propongo, tú confirmas.{self.RESET}
""")

    def print_memory(self, prefs: dict, routines: list) -> None:
        print(f"\n{self.CYAN}═══ MEMORIA ═══{self.RESET}")
        if prefs:
            print(f"  {self.BLUE}Preferencias:{self.RESET}")
            for k, v in prefs.items():
                print(f"    {self.GREEN}•{self.RESET} {k} = {v}")
        else:
            print(f"  {self.GRAY}Sin preferencias guardadas.{self.RESET}")

        if routines:
            print(f"  {self.BLUE}Rutinas:{self.RESET}")
            for r in routines:
                estado = f"{self.GREEN}confirmada{self.RESET}" if r.get("confirmed") else f"{self.YELLOW}pendiente{self.RESET}"
                print(f"    {self.GREEN}•{self.RESET} {r['name']} — {r.get('description', '')} [{estado}]")
        else:
            print(f"  {self.GRAY}Sin rutinas guardadas.{self.RESET}")
        print()

    def print_actions(self, log: list, pending: list) -> None:
        print(f"\n{self.CYAN}═══ ACCIONES ═══{self.RESET}")
        self.print_pending_actions(pending)

        if log:
            print(f"  {self.BLUE}Historial reciente:{self.RESET}")
            for entry in log[:15]:
                print(f"    {self.GRAY}{entry['time']}{self.RESET} {entry['action']} — {entry['result']}")
        else:
            print(f"  {self.GRAY}Sin historial de acciones.{self.RESET}")
        print()

    def confirm_action(self, detail: str, kind: str = "", dangerous: bool = False) -> bool:
        prefix = f"{self.RED}⚠ PELIGROSO{self.RESET} " if dangerous else ""
        print(f"{self.YELLOW}¿Confirmas?{self.RESET} {prefix}{detail}")
        if dangerous:
            print(f"  {self.RED}Esta acción puede modificar el sistema. Escribe 'CONFIRMO' para proceder.{self.RESET}")
            resp = input(f"  {self.CYAN}[CONFIRMO/cancelar]{self.RESET} ").strip()
            return resp == "CONFIRMO"
        resp = input(f"  {self.CYAN}[s/N]{self.RESET} ").strip().lower()
        return resp in {"s", "si", "sí", "y", "yes"}

    def print_pending_actions(self, pending: list) -> None:
        if not pending:
            print(f"  {self.GRAY}Sin acciones pendientes.{self.RESET}")
            return
        print(f"  {self.BLUE}Pendientes de confirmación:{self.RESET}")
        for p in pending:
            kind_label = p.get('kind', '')
            icon = {"open": "📱", "search": "🔍", "summarize": "📄", "execute": "⚡", "read": "📖", "write": "✍️", "list": "📁"}.get(kind_label, "⏳")
            print(f"    {self.YELLOW}{icon}{self.RESET} [{p['id'][:8]}] {p['detail']} {self.GRAY}({kind_label}){self.RESET}")


def main() -> int:
    try:
        settings = Settings.load()
    except Exception as e:
        print(f"\033[31m[error] Configuración inválida: {e}\033[0m")
        print("  Copia .env.example a .env y ajusta OLLAMA_URL / OLLAMA_MODEL")
        return 1

    ui = TerminalUI()
    ui.print_banner()

    provider = create_provider(settings)
    chat = ChatService(provider, settings)
    actions = ActionsService(settings, chat)
    memory = MemoryService(settings, actions)

    # Estado inicial
    st = provider.status()
    ui.print_status(provider.name, provider.model, st.get("ready", False))

    if not st.get("ready"):
        ui.print_warning("Ollama no responde o el modelo no está descargado.")
        ui.print_system(f"Ejecuta: ollama pull {settings.ollama_model}")
        ui.print_system("Y asegúrate de que 'ollama serve' esté corriendo.\n")

    history: list[dict[str, str]] = []

    while True:
        try:
            user_input = input(ui.print_user_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{ui.GRAY}Chao. Hasta la próxima.{ui.RESET}")
            return 0

        if not user_input:
            continue

        # Comandos internos
        if user_input.lower() in {"salir", "exit", "quit", "q"}:
            print(f"{ui.GRAY}Chao. Hasta la próxima.{ui.RESET}")
            return 0

        if user_input == "/ayuda":
            ui.print_help()
            continue

        if user_input == "/memoria":
            ui.print_memory(memory.get_preferences(), memory.list_routines())
            continue

        if user_input == "/acciones":
            ui.print_actions(actions.audit_log(), actions.list_pending())
            continue

        if user_input == "/limpiar":
            history.clear()
            ui.print_system("Conversación limpiada. Memoria y acciones se mantienen.")
            continue

        if user_input == "/estado":
            st = provider.status()
            ui.print_status(provider.name, provider.model, st.get("ready", False))
            continue

        if user_input == "/confirmar":
            pending = actions.list_pending()
            if not pending:
                ui.print_system("No hay acciones pendientes.")
                continue
            ui.print_pending_actions(pending)
            # Pedir ID a confirmar
            action_id = input(f"  {ui.CYAN}ID de acción a confirmar (o Enter para cancelar): {ui.RESET}").strip()
            if not action_id:
                ui.print_system("Cancelado.")
                continue
            # Buscar coincidencia por prefijo
            matches = [p for p in pending if p['id'].startswith(action_id)]
            if not matches:
                ui.print_error(f"No hay acción pendiente que empiece por '{action_id}'")
                continue
            if len(matches) > 1:
                ui.print_error(f"Múltiples coincidencias. Usa más caracteres.")
                continue
            item = matches[0]
            dangerous = item['kind'] in {'execute', 'write', 'delete'}
            if ui.confirm_action(item['detail'], item['kind'], dangerous):
                try:
                    result = actions.confirm_action(item['id'])
                    ui.print_system(f"✓ Ejecutada: {result}")
                except Exception as e:
                    ui.print_error(f"Falló: {e}")
            else:
                actions.cancel_action(item['id'])
                ui.print_system("Acción cancelada.")
            continue

        if user_input == "/cancelar":
            pending = actions.list_pending()
            if not pending:
                ui.print_system("No hay acciones pendientes.")
                continue
            ui.print_pending_actions(pending)
            action_id = input(f"  {ui.CYAN}ID de acción a cancelar (o Enter para cancelar): {ui.RESET}").strip()
            if not action_id:
                ui.print_system("Cancelado.")
                continue
            matches = [p for p in pending if p['id'].startswith(action_id)]
            if not matches:
                ui.print_error(f"No hay acción pendiente que empiece por '{action_id}'")
                continue
            if len(matches) > 1:
                ui.print_error(f"Múltiples coincidencias. Usa más caracteres.")
                continue
            actions.cancel_action(matches[0]['id'])
            ui.print_system("Acción cancelada.")
            continue

        # Mensaje normal al modelo
        history.append({"role": "user", "content": user_input})

        ui.start_typing()
        try:
            answer = chat.reply(history)
            ui.stop_typing()
            ui.print_assistant(answer)
            history.append({"role": "assistant", "content": answer})
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