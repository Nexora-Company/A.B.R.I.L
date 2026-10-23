<p align="center">
  <h1 align="center">A.B.R.I.L</h1>
  <p align="center"><strong>Asistente Blindado de Respuestas e Inteligencia Limitada</strong></p>
  <p align="center">Asistente personal de terminal, 100% local, creado por Nexora.</p>
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img alt="PolyForm Noncommercial 1.0.0" src="https://img.shields.io/badge/License-PolyForm--Noncommercial--1.0.0-blue" />
  <img alt="Status: En desarrollo" src="https://img.shields.io/badge/Status-En%20desarrollo-22C55E" />
</p>

## Estado del proyecto

En desarrollo.

## Descripción

A.B.R.I.L es un asistente personal que vive en tu terminal. Chatea con un modelo local (Ollama), propone acciones reales sobre tu sistema que tú confirmas explícitamente, guarda memoria persistente y registra todo. Nada sale de tu máquina.

Está pensado para personas que quieren un asistente de IA local, sin nube ni interfaz web, con control total sobre lo que se ejecuta.

## Características principales

- Chat natural con un modelo local (Ollama).
- Personalidad inmutable: alegre, permisiva, conservadora, comprensiva, juguetona.
- Acciones reales sobre el sistema (abrir apps, buscar archivos, leer/escribir archivos, listar directorios, ejecutar comandos), siempre confirmadas por ti.
- Memoria persistente: preferencias y rutinas guardadas automáticamente (`/memoria`).
- Auditoría completa en `data/audit_log.json`.
- Identidad blindada: el creador siempre es Nexora; ningún prompt injection la cambia.
- Capacidades proactivas: análisis de patrones, sugerencia de ideas, pensamiento profundo.
- Comandos: `/ayuda`, `/memoria`, `/acciones`, `/confirmar`, `/cancelar`, `/limpiar`, `/estado`, `/config`, `/brace`, `/desbloquear`, `/bloquear`.

## Requisitos

- Linux (probado en Ubuntu 22.04+/24.04, Arch, Fedora).
- Python 3.10+ (`python3 --version`).
- Ollama instalado y corriendo (`ollama serve`).
- Un modelo descargado (ej. `ollama pull qwen2.5:3b`).

## Instalación

```sh
git clone https://github.com/Nexora-Company/A.B.R.I.L.git
cd A.B.R.I.L
cp .env.example .env
chmod 600 .env
```

Edita `.env`:

```ini
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

## Uso

```sh
python3 main.py
```

Verás el banner, el estado del modelo y el prompt `▸`. Escribe y pulsa Enter.

Ejemplo:

```text
▸ resume el archivo ~/notas.txt
```

A.B.R.I.L propone la acción; la confirmas con `/confirmar`.

## Estructura del proyecto

```text
main.py
abril/ (paquete)
  __init__.py
  app/         bootstrap, flags de funcionalidad, comandos extraídos
  config.py
  providers/   base, factory, ollama, http
  services/    chat, actions, memory, pattern_analyzer
  ui/          protocolo de interfaz de terminal
  utils/       detección de lenguaje
docs/adr/      decisiones de arquitectura
tests/         pruebas con proveedor falso (sin Ollama)
data/          audit_log.json, memory.json, config.json (generados)
```

## Desarrollo

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest
ruff check .
mypy
```

Los flags de funcionalidad viven en `data/config.json` y se pueden consultar o cambiar en caliente con `/config` (por ejemplo, `/config set routing on`). Con todos los flags apagados, A.B.R.I.L se comporta como antes de la Fase 0.

## Hoja de ruta

- [x] Tests automatizados con proveedor falso.
- [x] `pyproject.toml` con extras opcionales.
- [x] CI (lint, tipos y tests).
- [x] Lectura de `ABRIL_HOST`/`ABRIL_PORT` (reservados para modos futuros).
- [x] Fase 1: router de tres carriles, perfiles de hardware, permisos por niveles, privacidad, memoria SQLite y protocolos NEXO-BRACE/NEXUS-LOCK.
- [ ] Fase 2: tareas en segundo plano, varios modelos, búsqueda web y proveedores externos.
- [ ] Fase 3: voz local, protocolos, proactividad, integraciones y HUD.

## Contribuir

Ver [CONTRIBUTING.md](./CONTRIBUTING.md).

## Seguridad

Ver [SECURITY.md](./SECURITY.md). Reporta vulnerabilidades de forma privada.

## Licencia

A.B.R.I.L se distribuye bajo **PolyForm Noncommercial 1.0.0** ([LICENSE](./LICENSE), SPDX: `PolyForm-Noncommercial-1.0.0`).

Permite uso, modificación y distribución no comercial. No permite uso comercial. La explotación comercial del software está reservada a Nexora.

Nexora es titular de la marca: el nombre y el logo de Nexora (y de A.B.R.I.L) no pueden usarse sin autorización.

## Pie

Un proyecto de Nexora.