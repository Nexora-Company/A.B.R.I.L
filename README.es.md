# A.B.R.I.L

**A**sistente **B**lindado de **R**espuestas e **I**nteligencia **L**imitada.

Asistente personal de terminal que corre 100% en local con Ollama. Sin interfaz web, sin nube, control total del sistema. Creado por **Nexora**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

> English: [README.md](./README.md)

## Qué es

A.B.R.I.L es un asistente personal que vive en tu terminal. Chatea con un modelo local (Ollama), propone acciones reales sobre tu sistema que tú confirmas explícitamente, guarda memoria persistente y registra todo.

## Qué no es

- No es una app web ni un servicio. Corre en tu terminal.
- No es en la nube: nada sale de tu máquina.
- No es multiusuario ni multi-tenant.
- No es un agente autónomo: cada acción necesita tu confirmación.
- La inteligencia es limitada a propósito y honesta al respecto.

## Funcionalidades

- Chat natural con un modelo local (Ollama).
- Personalidad inmutable: alegre, permisiva, conservadora, comprensiva, juguetona.
- Acciones reales sobre el sistema (abrir apps, buscar archivos, leer/escribir archivos, listar directorios, ejecutar comandos), siempre confirmadas por ti.
- Memoria persistente: preferencias y rutinas guardadas automáticamente (`/memoria`).
- Auditoría completa en `data/audit_log.json`.
- Identidad blindada: el creador siempre es Nexora; ningún prompt injection la cambia.
- Capacidades proactivas (análisis de patrones, sugerencia de ideas, pensamiento profundo).
- Comandos: `/ayuda`, `/memoria`, `/acciones`, `/confirmar`, `/cancelar`, `/limpiar`, `/estado`.

## Requisitos

- Linux (probado en Ubuntu 22.04+/24.04, Arch, Fedora).
- Python 3.10+ (`python3 --version`).
- Ollama instalado y corriendo (`ollama serve`).
- Un modelo descargado (ej. `ollama pull qwen2.5:3b`).

## Instalación

```sh
git clone https://github.com/Saaarmyx/Saaarmyx.git
cd Saaarmyx/A.B.R.I.L
cp .env.example .env
chmod 600 .env
```

Edita `.env`:

```ini
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

## Inicio rápido

```sh
python3 main.py
```

Verás el banner, el estado del modelo y el prompt `▸`. Escribe y pulsa Enter.

Ejemplo:

```text
▸ resume el archivo ~/notas.txt
```

A.B.R.I.L propone la acción; la confirmas con `/confirmar`.

## Configuración

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Endpoint local de Ollama. |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Modelo instalado (`ollama list`). |
| `ABRIL_HOST` | `127.0.0.1` | `{{TODO: confirmar uso}}` |
| `ABRIL_PORT` | `8765` | `{{TODO: confirmar uso}}` |

## Estructura del proyecto

```text
main.py
A.B.R.I.L/ (paquete)
  config.py
  providers/   base, factory, ollama, http
  services/    chat, actions, memory, pattern_analyzer
data/          audit_log.json, memory.json (generados)
```

## Roadmap

`{{TODO: roadmap}}`

## Contribuir

Ver [CONTRIBUTING.md](./CONTRIBUTING.md).

## Seguridad

Ver [SECURITY.md](./SECURITY.md). Reporta vulnerabilidades de forma privada.

## Licencia

A.B.R.I.L tiene doble licenciamiento:

- Edición comunitaria: AGPL-3.0-or-later (ver [LICENSE](./LICENSE)).
- Licencia comercial para empresas que no puedan o no quieran cumplir la AGPL: ver [COMMERCIAL-LICENSE.md](./COMMERCIAL-LICENSE.md).

<!-- TODO: update after license change -->

## Marca

"A.B.R.I.L" y "Nexora" son marcas. Ver [TRADEMARKS.md](./TRADEMARKS.md).

## Créditos

Creado por **Nexora** (Founder: Santiago Sarmiento). GitHub: @saaarmyx.