# Abril

> Asistente personal para Ubuntu: conversación por texto/voz, análisis de archivos y proveedores intercambiables (OpenAI / Ollama local).  
> Sin pantalla observada, sin memoria entre sesiones, sin control del equipo.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-D22128?logo=apache&logoColor=white)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Activo-22C55E)]()

---

## Qué Resuelve

Abril pone un asistente de IA en tu escritorio Ubuntu sin depender de la nube obligatoriamente. Permite:

- Chat por texto y dictado por voz (Web Speech API del navegador).
- Lectura en voz alta de respuestas (SpeechSynthesis).
- Análisis de archivos que arrastras: .txt, .md, .csv, .json, .log (hasta 500 KB c/u).
- Proveedor intercambiable: OpenAI (remoto) u Ollama (100% local) cambiando una variable.
- Privacidad por diseño: el servidor escucha solo en localhost, sin autenticación, sin persistencia, sin telemetría.

---

## Arquitectura

```text
run.py                       # Punto de entrada (python3 run.py)
abril/
  config.py                  # Carga .env + validación (stdlib only)
  providers/                 # Interfaz común + adaptadores OpenAI / Ollama
    base.py                  # Protocol Provider
    factory.py               # Factoría por ABRIL_PROVIDER
    openai.py                # Cliente OpenAI (HTTP stdlib)
    ollama.py                # Cliente Ollama (HTTP stdlib)
    http.py                  # Utilidades HTTP compartidas
  services/chat.py           # Validación, historial (máx. 30), límites
  web/
    handler.py               # Rutas HTTP: /api/chat, /api/files, static
    server.py                # Servidor HTTP (stdlib http.server)
    static/index.html        # Interfaz SPA (vanilla JS, sin build)
```

Principio clave: los proveedores implementan el mismo Protocol; cambiar de OpenAI a Ollama no toca la lógica de chat ni la UI. El proyecto usa solo la biblioteca estándar de Python.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.10+ |
| Servidor HTTP | http.server (stdlib) |
| Cliente HTTP | urllib.request (stdlib) |
| Configuración | .env + os.environ (parser propio, sin python-dotenv) |
| Frontend | HTML5 + ES6 vanilla + Web Speech API + SpeechSynthesis |
| Proveedores IA | OpenAI API / Ollama (local) |
| Testing | bash -n, python3 -m py_compile, opcional mypy/ruff |

---

## Instalación y Configuración

### Prerrequisitos

- Ubuntu 22.04 LTS o superior (probado en 24.04/26.04).
- Python 3.10 o posterior (python3 --version).
- Navegador moderno (Chrome/Edge/Firefox/Safari) con soporte Web Speech API.
- Clave OpenAI API (para proveedor por defecto) u Ollama instalado localmente.

### 1. Clonar y entrar

```bash
git clone https://github.com/Saaarmyx/Saaarmyx.git
cd Saaarmyx/ABRIL
```

### 2. Variables de entorno

```bash
cp .env.example .env
chmod 600 .env
nano .env   # o tu editor preferido
```

Edita .env y pon tu clave en OPENAI_API_KEY=. El archivo queda con permisos 600 (solo tu usuario). Nunca lo subas a Git.

```ini
# .env.example — copia a .env y rellena
ABRIL_HOST=127.0.0.1
ABRIL_PORT=8765
ABRIL_PROVIDER=openai          # openai | ollama

# OpenAI
OPENAI_API_KEY=                # OBLIGATORIO si provider=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.6-terra

# Ollama (solo si ABRIL_PROVIDER=ollama)
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
```

### 3. Ejecutar

```bash
python3 run.py
```

Abre http://127.0.0.1:8765 en tu navegador.

---

## Cambiar a Ollama (100% Local)

```bash
# 1. Instala Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Descarga un modelo
ollama pull qwen3:8b

# 3. Cambia el proveedor en .env
# ABRIL_PROVIDER=ollama
# OLLAMA_MODEL=qwen3:8b

# 4. Reinicia el servidor
python3 run.py
```

Abril usará OLLAMA_URL y OLLAMA_MODEL del mismo .env. Sin claves, sin nube.

---

## Uso Rápido

| Acción | Cómo |
|--------|------|
| Preguntar | Escribe en el input y pulsa Enter o el botón Enviar. |
| Dictar | Pulsa el micrófono, habla, suelta. |
| Adjuntar archivo | Arrastra .txt, .md, .csv, .json, .log (≤ 500 KB) al chat. |
| Escuchar respuesta | Pulsa «Escuchar» bajo cualquier respuesta. |
| Limpiar conversación | Botón «Limpiar conversación» (solo pestaña actual). |
| Recargar = nueva sesión | Al recargar la página, el historial desaparece (sin persistencia). |

---

## Configuración Completa (.env)

| Variable | Default | Descripción |
|----------|---------|-------------|
| ABRIL_HOST | 127.0.0.1 | Interfaz de escucha (solo localhost por seguridad). |
| ABRIL_PORT | 8765 | Puerto del servidor HTTP. |
| ABRIL_PROVIDER | openai | openai \| ollama. |
| OPENAI_API_KEY | "" | Requerido para OpenAI. Solo en .env. |
| OPENAI_BASE_URL | https://api.openai.com/v1 | Endpoint compatible OpenAI. |
| OPENAI_MODEL | gpt-5.6-terra | Modelo remoto a usar. |
| OLLAMA_URL | http://127.0.0.1:11434 | Endpoint Ollama local. |
| OLLAMA_MODEL | qwen3:4b | Modelo local instalado (ollama list). |

Seguridad: el servidor solo escucha en localhost. No pongas ABRIL_HOST=0.0.0.0 sin añadir autenticación real (TLS, tokens, VPN). El dictado requiere permiso de micrófono del navegador.

---

## Desarrollo y Calidad

```bash
# Sintaxis Python
python3 -m py_compile abril/**/*.py

# Tipado (opcional, si instalas mypy)
python3 -m mypy abril/

# Lint/format (opcional, si instalas ruff)
ruff check abril/
ruff format abril/
```

Sin dependencias externas — todo stdlib.

---

## Estructura de Archivos Clave

```
ABRIL/
├── .env.example          # Plantilla de configuración
├── .gitignore
├── LICENSE               # Apache-2.0
├── README.md             # Este archivo
├── CONTRIBUTING.md       # Guía de contribución
├── run.py                # Entrypoint principal
├── server.py             # Compatibilidad (usa run.py)
└── abril/
    ├── __init__.py       # __version__ = "0.2.0"
    ├── config.py         # Settings (dataclass, frozen, validador)
    ├── providers/
    │   ├── __init__.py   # Exporta Provider, create_provider
    │   ├── base.py       # Protocol Provider (chat, list_models)
    │   ├── factory.py    # create_provider(settings)
    │   ├── openai.py     # OpenAIProvider
    │   ├── ollama.py     # OllamaProvider
    │   └── http.py       # request_json, stream_json
    ├── services/
    │   ├── __init__.py
    │   └── chat.py       # ChatService (validación, límites, historial)
    └── web/
        ├── __init__.py
        ├── server.py     # HTTPServer + rutas + static
        ├── handler.py    # RequestHandler (POST /api/chat, /api/files)
        └── static/
            └── index.html  # SPA: chat, micrófono, TTS, adjuntos
```

---

## Contribución

Lee CONTRIBUTING.md para:
- Flujo de ramas (feature/, fix/, refactor/)
- Commits Conventional Commits obligatorios
- Estándares Python (ruff, mypy, docstrings Google)
- Cómo añadir un proveedor nuevo

---

## Licencia

Apache-2.0 — Ver LICENSE.

Copyright (c) 2026 Santiago Sarmiento (Saaarmyx)

---

## Autor

Santiago Sarmiento — Founder de Nexora  
GitHub: @saaarmyx | Discord: saaarmyx

---

Privacidad local. Control total. Sin sorpresas.