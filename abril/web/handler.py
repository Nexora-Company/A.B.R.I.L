"""HTTP routes and static frontend delivery."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from ..providers.base import ProviderError
from ..services.chat import ChatService, InvalidConversation


class AbrilRequestHandler(BaseHTTPRequestHandler):
    server_version = "Abril/0.2"
    chat_service: ChatService
    static_dir: Path
    max_request_bytes: int
    actions_service: object
    memory_service: object

    def log_message(self, fmt: str, *args: object) -> None:
        # HTTP method/path only; never print prompt text or provider credentials.
        print(f"[{self.log_date_time_string()}] {args[0] if args else fmt}")

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/status":
            self._send_json(200, self.chat_service.status())
            return
        if path == "/api/apps":
            self._send_json(200, {"apps": self.actions_service.list_apps()})
            return
        if path == "/api/actions/roots":
            self._send_json(200, {"roots": self.actions_service.list_roots()})
            return
        if path == "/api/actions/log":
            self._send_json(200, {"entries": self.actions_service.audit_log()})
            return
        if path == "/api/actions/pending":
            self._send_json(200, {"pending": self.actions_service.list_pending()})
            return
        if path == "/api/memory/preferences":
            self._send_json(200, {"preferences": self.memory_service.get_preferences()})
            return
        if path == "/api/memory/routines":
            self._send_json(200, {"routines": self.memory_service.list_routines()})
            return
        if path.startswith("/api/memory/suggestions"):
            self._send_json(200, {"suggestions": self.memory_service.suggestions()})
            return
        if path.startswith("/api/memory/preferences/"):
            key = path.rsplit("/", 1)[-1]
            self.memory_service.delete_preference(key)
            self._send_json(200, {"message": "Preferencia eliminada."})
            return
        if path.startswith("/api/memory/routines/") and path.count("/") > 3:
            routine_id = path.rsplit("/", 1)[-1]
            self.memory_service.delete_routine(routine_id)
            self._send_json(200, {"message": "Rutina eliminada."})
            return
        if path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        page = (self.static_dir / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        allowed = {
            "/api/chat",
            "/api/actions/search",
            "/api/actions/propose",
            "/api/actions/confirm",
            "/api/actions/cancel",
            "/api/memory/preferences",
            "/api/memory/routines",
            "/api/memory/routines/",
        }
        if route not in allowed and not route.startswith("/api/memory/routines/") and not route.startswith("/api/memory/suggestions"):
            self.send_error(404)
            return
        try:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise InvalidConversation("Tamaño de solicitud inválido.") from error
            if length < 1 or length > self.max_request_bytes:
                self._send_json(413, {"error": "El mensaje excede el tamaño permitido (1.5 MB)."})
                return
            try:
                data = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise InvalidConversation("El cuerpo debe ser JSON válido.") from error
            if not isinstance(data, dict):
                raise InvalidConversation("El cuerpo debe ser un objeto JSON.")
            if route == "/api/chat":
                answer = self.chat_service.reply(data.get("messages"))
                self._send_json(200, {"answer": answer})
            elif route == "/api/actions/propose":
                kind = data.get("kind")
                detail = data.get("detail")
                args = data.get("args") or {}
                if not isinstance(kind, str) or not isinstance(detail, str):
                    raise InvalidConversation("kind y detail son obligatorios.")
                action_id = self.actions_service.propose_action(kind, detail, args)
                self._send_json(200, {"action_id": action_id, "status": "pending"})
            elif route == "/api/actions/search":
                root = data.get("root")
                query = data.get("query")
                if not isinstance(root, str) or not isinstance(query, str):
                    raise InvalidConversation("root y query son obligatorios.")
                results = self.actions_service.search(root, query)
                self._send_json(200, {"results": results})
            elif route == "/api/actions/confirm":
                action_id = data.get("action_id")
                if not isinstance(action_id, str):
                    raise InvalidConversation("action_id es obligatorio.")
                result = self.actions_service.confirm_action(action_id)
                self._send_json(200, {"message": result})
            elif route == "/api/actions/cancel":
                action_id = data.get("action_id")
                if not isinstance(action_id, str):
                    raise InvalidConversation("action_id es obligatorio.")
                self.actions_service.cancel_action(action_id)
                self._send_json(200, {"message": "Acción cancelada."})
            elif route == "/api/memory/preferences":
                key = data.get("key")
                value = data.get("value")
                if not isinstance(key, str) or not key:
                    raise InvalidConversation("key es obligatorio.")
                self.memory_service.set_preference(key, value)
                self._send_json(200, {"message": "Preferencia guardada."})
            elif route == "/api/memory/routines":
                self._handle_routines_post(data)
            elif route.startswith("/api/memory/routines/"):
                self._handle_routine_by_id(route, data)
            elif route.startswith("/api/memory/suggestions"):
                self._send_json(200, {"suggestions": self.memory_service.suggestions()})
        except InvalidConversation as error:
            self._send_json(400, {"error": str(error)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except ProviderError as error:
            self._send_json(502, {"error": str(error)})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            self._send_json(500, {"error": "Ocurrió un error interno al procesar la solicitud."})

    def _handle_routines_post(self, data: dict) -> None:
        name = data.get("name")
        description = data.get("description", "")
        actions = data.get("actions", [])
        if not isinstance(name, str) or not name:
            raise InvalidConversation("name es obligatorio.")
        if not isinstance(description, str):
            raise InvalidConversation("description debe ser texto.")
        if not isinstance(actions, list):
            raise InvalidConversation("actions debe ser una lista.")
        routine = self.memory_service.add_routine(name, description, actions)
        self._send_json(201, {"routine": routine, "message": "Rutina creada. Confírmala para activarla."})

    def _handle_routine_by_id(self, route: str, data: dict) -> None:
        routine_id = route.rsplit("/", 1)[-1]
        method_like = data.get("_method")
        if method_like == "PUT":
            self._update_routine(routine_id, data)
        elif method_like == "CONFIRM":
            self.memory_service.confirm_routine(routine_id)
            self._send_json(200, {"message": "Rutina confirmada."})
        else:
            raise InvalidConversation("Operación de rutina no soportada.")

    def _update_routine(self, routine_id: str, data: dict) -> None:
        fields = {}
        for field in ("name", "description", "actions"):
            if field in data:
                fields[field] = data[field]
        if not fields:
            raise InvalidConversation("No hay campos para actualizar.")
        self.memory_service.update_routine(routine_id, fields)
        self._send_json(200, {"message": "Rutina actualizada."})
