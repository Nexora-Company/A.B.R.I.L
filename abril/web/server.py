"""Local HTTP server bootstrap."""

from __future__ import annotations

from http.server import ThreadingHTTPServer

from ..config import Settings
from ..providers.factory import create_provider
from ..services.chat import ChatService
from ..services.actions import ActionsService
from .handler import AbrilRequestHandler


def serve(settings: Settings) -> None:
    provider = create_provider(settings)
    service = ChatService(provider, settings)
    actions = ActionsService(settings, service)
    handler = type(
        "ConfiguredAbrilRequestHandler",
        (AbrilRequestHandler,),
        {
            "chat_service": service,
            "static_dir": settings.project_root / "abril" / "web" / "static",
            "max_request_bytes": settings.max_request_bytes,
            "actions_service": actions,
        },
    )
    server = ThreadingHTTPServer((settings.host, settings.port), handler)
    server.daemon_threads = True
    print(f"Abril disponible en http://{settings.host}:{settings.port}")
    print(f"Proveedor: {provider.name} | Modelo: {provider.model}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Cerrando Abril…")
    finally:
        server.server_close()
