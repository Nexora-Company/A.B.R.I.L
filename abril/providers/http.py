"""Small JSON-over-HTTP helper shared by the provider adapters."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .base import ProviderError


def _http_error_message(error: urllib.error.HTTPError) -> str:
    """Translate common OpenAI errors without exposing raw response bodies."""
    payload: dict = {}
    try:
        decoded = json.loads(error.read().decode("utf-8", "replace"))
        if isinstance(decoded, dict):
            payload = decoded
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    detail = payload.get("error", {})
    if not isinstance(detail, dict):
        detail = {}
    code = detail.get("code")
    error_type = detail.get("type")
    safe_code = "".join(ch for ch in str(code or "") if ch.isalnum() or ch in "_- ")[:60]

    if error.code == 429:
        quota_codes = {
            "insufficient_quota",
            "credit_balance_exhausted",
            "organization_spend_limit_reached",
            "project_spend_limit_reached",
            "organization_usage_limit_reached",
        }
        if code in quota_codes or error_type == "insufficient_quota":
            return (
                "OpenAI indica que la cuota o el límite de gasto está agotado. "
                "Revisa la facturación, los créditos y los límites de tu proyecto u organización."
                + (f" Código: {safe_code}." if safe_code else "")
            )
        retry_after = error.headers.get("Retry-After", "") if error.headers else ""
        if code in {"rate_limit_exceeded", "slow_down"} or error_type == "rate_limit_error":
            wait_note = f" Espera al menos {retry_after} segundos antes de volver a intentar." if retry_after.isdigit() else " Espera un momento antes de volver a intentar."
            return "OpenAI limitó temporalmente la frecuencia de solicitudes." + wait_note + (f" Código: {safe_code}." if safe_code else "")
        return (
            "OpenAI respondió HTTP 429. Puede ser un límite temporal o un problema de cuota; "
            "revisa el panel de uso y facturación."
            + (f" Código: {safe_code}." if safe_code else "")
        )
    if error.code == 401:
        return "OpenAI rechazó la clave API. Revisa OPENAI_API_KEY en .env y reinicia Abril."
    return f"La API del proveedor respondió con HTTP {error.code}." + (f" Código: {safe_code}." if safe_code else "")


def get_json(url: str, timeout: float = 2.0) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise ProviderError(f"El proveedor respondió con HTTP {error.code}.") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderError("No se pudo conectar con el proveedor de IA.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ProviderError("El proveedor devolvió una respuesta inválida.") from error


def post_json(url: str, payload: dict, headers: dict[str, str], timeout: float = 180.0) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # Never return the provider's raw body: it may include internal diagnostics.
        raise ProviderError(_http_error_message(error)) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderError("No se pudo conectar con el proveedor de IA.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ProviderError("El proveedor devolvió una respuesta inválida.") from error
