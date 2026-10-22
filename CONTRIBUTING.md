# Guía de Contribución — Abril

Gracias por querer mejorar Abril. Este documento cubre el flujo de trabajo, estándares de código y cómo proponer cambios.

---

## 🔀 Flujo de Trabajo

### 1. Fork y Rama

```bash
# 1. Fork en GitHub (botón Fork)
# 2. Clona TU fork
git clone https://github.com/TU-USUARIO/Saaarmyx.git
cd Saaarmyx/ABRIL

# 3. Añade upstream
git remote add upstream https://github.com/Saaarmyx/Saaarmyx.git

# 4. Rama desde main actualizado
git checkout main
git pull upstream main
git checkout -b feature/mi-mejora   # o fix/, refactor/, docs/, style/, build/, ci/, test/
```

> **Convención**: `feature/`, `fix/`, `refactor/`, `docs/`, `style/`, `build/`, `ci/`, `test/` + `kebab-case` descriptivo.  
> Ejemplos: `feature/providers-anthropic`, `fix/chat-history-limit`, `docs/readme-ollama-setup`.

### 2. Commits — Conventional Commits (Obligatorio)

```text
<tipo>(<ámbito>): <descripción en imperativo y minúsculas>
```

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad (proveedor, endpoint, opción CLI) |
| `fix` | Corrección de bug |
| `refactor` | Reestructuración sin cambio de comportamiento |
| `perf` | Mejora de rendimiento medible |
| `style` | Formato (ruff/black), sin lógica |
| `docs` | Documentación (README, docstrings, comentarios) |
| `build` | `pyproject.toml`, `requirements`, CI, Dockerfile |
| `ci` | GitHub Actions, scripts de automatización |
| `test` | Pruebas unitarias/integración |
| `revert` | Revierte commit anterior |

**Ámbitos Abril**: `providers`, `services`, `web`, `config`, `chat`, `static`.

```bash
# Ejemplos
git add abril/providers/anthropic.py abril/providers/__init__.py
git commit -m "feat(providers): añade proveedor Anthropic Claude"

git add abril/services/chat.py
git commit -m "fix(chat): evita índice fuera de rango al truncar historial"
```

**Reglas**:
- **Un commit = un cambio lógico atómico**.
- **Nunca** `git add .` ni `git commit -a`. Rutas explícitas.
- Mensaje en **español**, **imperativo**, **minúsculas**, **≤ 72 chars** primera línea.
- Cuerpo y pie opcionales para contexto (`Closes #123`).

### 3. Push y Pull Request

```bash
git push origin feature/mi-mejora
```

Abre PR desde tu fork → `Saaarmyx/Saaarmyx:main` (carpeta `ABRIL/`).

**El PR debe incluir**:
1. Título Conventional Commits.
2. Descripción: **qué**, **por qué**, **cómo probaste**.
3. Referencia a issue (`Fixes #42`).
4. Capturas si hay cambios en UI (`index.html`).
5. Checklist verificado (ver abajo).

### 4. Checklist Pre-PR

- [ ] `main` actualizado y rebaseado/mergeado en tu rama
- [ ] Commits atómicos + Conventional Commits
- [ ] `python3 -m py_compile abril/**/*.py` pasa
- [ ] `python3 -m mypy abril/` pasa (si usas mypy)
- [ ] `ruff check abril/` y `ruff format --check abril/` pasan (si usas ruff)
- [ ] Docstrings actualizadas en funciones/clases públicas (Google style)
- [ ] README actualizado si cambia configuración, uso o arquitectura
- [ ] Sin `.env`, `__pycache__`, `*.pyc`, logs, temporales en el diff
- [ ] PR explica **qué y por qué**, no solo **cómo**

---

## 🐍 Estándares Python (Abril)

| Aspecto | Estándar |
|---------|----------|
| **Versión** | Python 3.10+ |
| **Formato** | `ruff format` (equivale a Black, 88 cols) |
| **Lint** | `ruff check` (incluye pyflakes, pycodestyle, isort, etc.) |
| **Tipado** | Type hints en **todas** las funciones públicas; `mypy --strict` opcional |
| **Imports** | Absolutos desde `abril.`; orden: stdlib → third-party → local; `ruff` los ordena |
| **Docstrings** | **Google style** en módulos, clases, funciones públicas |
| **Dataclasses** | `@dataclass(frozen=True)` para inmutabilidad (config, settings, DTOs) |
| **Protocolos** | `typing.Protocol` para interfaces (proveedores) |
| **Stdlib First** | **Sin dependencias externas**. Solo `urllib`, `json`, `http.server`, `dataclasses`, `pathlib`, `os`, `typing`, etc. |
| **Manejo de errores** | Excepciones específicas; `raise ... from err` para encadenar; validación temprana en `config.py` |
| **Testing** | `python3 -m py_compile` como gate mínimo; tests unitarios en `tests/` si se añaden |

### Ejemplo de Docstring (Google Style)

```python
def create_provider(settings: Settings) -> Provider:
    """Crea una instancia de proveedor según configuración.

    Args:
        settings: Configuración validada (provider, api_key, urls, model).

    Returns:
        Instancia concreta de Provider (OpenAIProvider u OllamaProvider).

    Raises:
        ValueError: Si settings.provider no es 'openai' ni 'ollama'.
    """
    ...
```

---

## 🧩 Cómo Añadir un Nuevo Proveedor

1. Crea `abril/providers/nuevo.py` implementando `Provider` (ver `base.py`):

```python
from abril.providers.base import Provider
from abril.config import Settings

class NuevoProvider(Provider):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def chat(self, messages: list[dict], model: str) -> Iterator[str]:
        # yield chunks de texto
        ...

    def list_models(self) -> list[str]:
        ...
```

2. Registra en `abril/providers/factory.py`:

```python
def create_provider(settings: Settings) -> Provider:
    if settings.provider == "openai":
        return OpenAIProvider(settings)
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    if settings.provider == "nuevo":      # ← añade
        return NuevoProvider(settings)     # ← añade
    raise ValueError(...)
```

3. Exporta en `abril/providers/__init__.py`:

```python
from .nuevo import NuevoProvider
__all__ = [..., "NuevoProvider"]
```

4. Documenta en `README.md` (sección "Cambiar a X") y actualiza `.env.example` si hace falta variables nuevas.

5. Ejecuta checks y abre PR.

---

## 🐛 Reportar Issues

Incluye **mínimo**:
- Versión (`git rev-parse --short HEAD` o `__version__` en `abril/__init__.py`)
- Python (`python3 --version`)
- SO (`lsb_release -ds`)
- Proveedor (`openai` u `ollama`) y modelo
- Pasos mínimos para reproducir
- Salida esperada vs real
- Logs relevantes (sin claves API)

---

## 🔒 Seguridad

- **Nunca** subas `.env`, claves API, tokens.
- Si expusiste una clave: **revócala ya** en la plataforma (OpenAI) y genera otra.
- Reporta vulnerabilidades **privadamente** (GitHub Security Advisories).

---

## 📜 Licencia de Contribuciones

Al enviar PR, aceptas que tu código se licencie bajo **Apache-2.0** (misma licencia del proyecto). Ver [LICENSE](./LICENSE).

---

## 🤔 Dudas

- GitHub Discussions para diseño/arquitectura.
- Discord `saaarmyx` o @saaarmyx en GitHub para dudas rápidas.