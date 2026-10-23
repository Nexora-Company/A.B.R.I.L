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
- Comandos: `/ayuda`, `/memoria`, `/acciones`, `/confirmar`, `/cancelar`, `/limpiar`, `/estado`.

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
  config.py
  providers/   base, factory, ollama, http
  services/    chat, actions, memory, pattern_analyzer
data/          audit_log.json, memory.json (generados)
```

## Hoja de ruta

- [ ] Añadir tests automatizados (`{{TODO}}`).
- [ ] Añadir `pyproject.toml` o `requirements.txt` (`{{TODO}}`).
- [ ] Configurar CI (`{{TODO}}`).
- [ ] Documentar uso de `ABRIL_HOST`/`ABRIL_PORT` (`{{TODO}}`).

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