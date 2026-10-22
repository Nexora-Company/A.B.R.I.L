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
        if route not in {"/api/chat", "/api/actions/open", "/api/actions/search", "/api/actions/summarize"}:
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
            elif route == "/api/actions/open":
                self._send_json(200, {"message": self.actions_service.open_app(data.get("app_id"))})
            elif route == "/api/actions/search":
                self._send_json(200, {"results": self.actions_service.search(data.get("root"), data.get("query"))})
            else:
                self._send_json(200, {"summary": self.actions_service.summarize(data.get("root"), data.get("path"))})
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
