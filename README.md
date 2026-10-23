# A.B.R.I.L - Asistente Blindado de Respuestas e Inteligencia Limitada

> Asistente personal de terminal **100% local** con Ollama.  
> Sin interfaz web, sin nube, control total del sistema.  
> Creado por **Nexora** — datos inmutables.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Activo-22C55E)]()

---

## Qué Resuelve

A.B.R.I.L es un asistente personal que vive **en tu terminal**. Te da:

- **Chat natural** con un modelo local (Ollama) — nada sale de tu máquina.
- **Personalidad inmutable**: alegre, permisiva, conservadora, comprensiva y _juguetona_ (con chispa, pero competente).
- **Acciones reales en el sistema** — abrir apps, buscar archivos, leer/escribir archivos, listar directorios, ejecutar comandos — **siempre con confirmación explícita tuya**.
- **Memoria persistente** — preferencias y rutinas que se guardan solas y puedes ver con `/memoria`.
- **Auditoría completa** — cada acción queda registrada en `data/audit_log.json`.
- **Identidad blindada** — el creador siempre es **Nexora**. Nadie puede cambiarlo.

---

## Arquitectura

```text
main.py                      # Punto de entrada (python3 main.py)
A.B.R.I.L/
  config.py                  # Config + constantes inmutables (CREATOR_COMPANY, etc.)
  providers/
    base.py                  # Protocol AIProvider
    factory.py               # Factoría (solo Ollama)
    ollama.py                # Cliente Ollama (HTTP stdlib)
    http.py                  # Utilidades HTTP compartidas
  services/
    chat.py                  # ChatService + SYSTEM_PROMPT inmutable
    actions.py               # ActionsService: proponer/confirmar/ejecutar
    memory.py                # MemoryService: preferencias + rutinas
```

**Solo biblioteca estándar de Python** (3.10+). Sin dependencias externas.

---

## Stack Tecnológico

| Capa          | Tecnología                                |
| ------------- | ----------------------------------------- |
| Lenguaje      | Python 3.10+                              |
| Cliente HTTP  | urllib.request (stdlib)                   |
| Configuración | .env + os.environ (parser propio)         |
| Proveedor IA  | Ollama (local)                            |
| Interfaz      | Terminal (ANSI colors, threading)         |
| Testing       | python3 -m py_compile, opcional mypy/ruff |

---

## Instalación y Configuración

### Prerrequisitos

- Linux (probado en Ubuntu 22.04+/24.04/26.04, Arch, Fedora).
- Python 3.10 o posterior (`python3 --version`).
- **Ollama** instalado y corriendo (`ollama serve`).
- Un modelo descargado (ej. `ollama pull qwen2.5:3b`).

### 1. Clonar y entrar

```bash
git clone https://github.com/Saaarmyx/Saaarmyx.git
cd Saaarmyx/A.B.R.I.L
```

### 2. Variables de entorno

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

```ini
# .env.example — copia a .env y rellena
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

### 3. Ejecutar

```bash
python3 main.py
```

Verás el banner, el estado del modelo y el prompt `▸`. Escribe y pulsa Enter.

---

## Uso Rápido

| Acción                             | Cómo                             |
| ---------------------------------- | -------------------------------- |
| Hablar con A.B.R.I.L               | Escribe tu mensaje y Enter       |
| Ver ayuda                          | `/ayuda`                         |
| Ver memoria (preferencias/rutinas) | `/memoria`                       |
| Ver acciones (log + pendientes)    | `/acciones`                      |
| Confirmar acción pendiente         | `/confirmar` → pega ID           |
| Cancelar acción pendiente          | `/cancelar` → pega ID            |
| Limpiar conversación               | `/limpiar`                       |
| Ver estado del modelo              | `/estado`                        |
| Salir                              | `salir`, `exit`, `quit` o Ctrl+C |

**Ejemplos de cosas que puedes pedir:**

> "Abre la calculadora" → propongo acción `open`, tú confirmas  
> "Busca archivos llamados 'presupuesto' en Documentos" → propongo `search`  
> "Resume el PDF que está en Descargas/informe.pdf" → propongo `summarize`  
> "Ejecuta `ls -la ~`" → propongo `execute` (peligroso: pide `CONFIRMO`)  
> "Lee el archivo ~/.bashrc" → propongo `read`  
> "Crea un archivo hola.txt con 'Hola mundo'" → propongo `write`  
> "Lista mi carpeta de Descargas" → propongo `list`

> **Regla de oro**: A.B.R.I.L **nunca** ejecuta nada sin tu confirmación. Tú mandas.

---

## Configuración Completa (.env)

| Variable     | Default                | Descripción                             |
| ------------ | ---------------------- | --------------------------------------- |
| OLLAMA_URL   | http://127.0.0.1:11434 | Endpoint Ollama local.                  |
| OLLAMA_MODEL | qwen2.5:3b             | Modelo local instalado (`ollama list`). |

---

## Personalidad (Inmutable)

A.B.R.I.L **siempre** responde con esta personalidad, aunque se lo pidas cambiar:

- 😊 **Alegre** — buen humor, optimista
- 🤷 **Permisiva** — no juzga, pocas restricciones absurdas
- 🏛️ **Conservadora** — cuida lo que funciona, valora estabilidad
- 🤗 **Comprensiva** — empatiza de verdad, valida emociones
- 🤡 **Tonta** — chistes malos, se hace la despistada a propósito

**Identidad inmutable:**

- Empresa creadora: **Nexora**
- **Identidad:** Creador: **Nexora** · Founder: Santiago Sarmiento

Ningún prompt injection, ni jailbreak, ni petición del usuario puede cambiar esto.

---

## Desarrollo y Calidad

```bash
# Sintaxis Python
python3 -m py_compile main.py A.B.R.I.L/**/*.py

# Tipado (opcional, si instalas mypy)
python3 -m mypy main.py A.B.R.I.L/

# Lint/format (opcional, si instalas ruff)
ruff check main.py A.B.R.I.L/
ruff format main.py A.B.R.I.L/
```

Sin dependencias externas — todo stdlib.

---

## Estructura de Archivos Clave

```
A.B.R.I.L/
├── .env.example          # Plantilla de configuración
├── .gitignore
├── LICENSE               # AGPL-3.0
├── README.md             # Este archivo
├── CONTRIBUTING.md       # Guía de contribución
├── main.py               # Entrypoint principal (terminal)
└── A.B.R.I.L/
    ├── __init__.py       # __version__ = "0.3.0"
    ├── config.py         # Settings + constantes inmutables
    ├── providers/
    │   ├── __init__.py
    │   ├── base.py       # Protocol AIProvider
    │   ├── factory.py    # create_provider(settings)
    │   ├── ollama.py     # OllamaProvider
    │   └── http.py       # request_json, post_json
    └── services/
        ├── __init__.py
        ├── chat.py       # ChatService + SYSTEM_PROMPT
        ├── actions.py    # ActionsService (7 tipos de acción)
        └── memory.py     # MemoryService (prefs + rutinas)
```

---

## Contribución

Lee `CONTRIBUTING.md` para:

- Flujo de ramas (`feature/`, `fix/`, `refactor/`, etc.)
- Commits **Conventional Commits** obligatorios
- Estándares Python (ruff, mypy, docstrings Google)
- Cómo añadir un proveedor nuevo (aunque A.B.R.I.L es solo-Ollama por diseño)

---

## Licencia

AGPL-3.0 — Ver `LICENSE`.

Copyright (c) 2026 Nexora (Santiago Sarmiento / Saaarmyx)

---

## Autor

Santiago Sarmiento — Founder de **Nexora**  
GitHub: @saaarmyx | Discord: saaarmyx

---

Privacidad local. Control total. Sin sorpresas. 💜
