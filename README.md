# A.B.R.I.L

**A**sistente **B**lindado de **R**espuestas e **I**nteligencia **L**imitada.

A personal terminal assistant that runs 100% locally with Ollama. No web UI, no cloud, full control of your system. Created by **Nexora**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

> Español: [README.es.md](./README.es.md)

## What it is

A.B.R.I.L is a terminal-based personal assistant. It chats with a local model (Ollama), proposes real actions on your system that you confirm explicitly, keeps persistent memory and logs everything.

## What it is not

- Not a web app or a service. It runs in your terminal.
- Not cloud-based: nothing leaves your machine.
- Not multi-user or multi-tenant.
- Not a general-purpose autonomous agent: every action needs your confirmation.
- Intelligence is intentionally limited and honest about it.

## Features

- Natural chat with a local model (Ollama).
- Immutable personality: cheerful, permissive, conservative, empathetic, playful.
- Real system actions (open apps, search files, read/write files, list directories, run commands), always confirmed by you.
- Persistent memory: preferences and routines saved automatically (`/memoria`).
- Full audit log in `data/audit_log.json`.
- Shielded identity: creator is always Nexora; no prompt injection changes it.
- Proactive capabilities (pattern analysis, idea suggestions, deep thinking).
- Commands: `/ayuda`, `/memoria`, `/acciones`, `/confirmar`, `/cancelar`, `/limpiar`, `/estado`.

## Requirements

- Linux (tested on Ubuntu 22.04+/24.04, Arch, Fedora).
- Python 3.10+ (`python3 --version`).
- Ollama installed and running (`ollama serve`).
- A downloaded model (e.g. `ollama pull qwen2.5:3b`).

## Installation

```sh
git clone https://github.com/Saaarmyx/Saaarmyx.git
cd Saaarmyx/A.B.R.I.L
cp .env.example .env
chmod 600 .env
```

Edit `.env`:

```ini
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

## Quick start

```sh
python3 main.py
```

You will see the banner, model status and the `▸` prompt. Type and press Enter.

Example:

```text
▸ resume el archivo ~/notas.txt
```

A.B.R.I.L proposes the action; you confirm with `/confirmar`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint. |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Installed model (`ollama list`). |
| `ABRIL_HOST` | `127.0.0.1` | `{{TODO: confirm usage}}` |
| `ABRIL_PORT` | `8765` | `{{TODO: confirm usage}}` |

## Project structure

```text
main.py
A.B.R.I.L/ (package)
  config.py
  providers/   base, factory, ollama, http
  services/    chat, actions, memory, pattern_analyzer
data/          audit_log.json, memory.json (generated)
```

## Roadmap

`{{TODO: roadmap}}`

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Security

See [SECURITY.md](./SECURITY.md). Report vulnerabilities privately.

## License

A.B.R.I.L is dual-licensed:

- Community edition: AGPL-3.0-or-later (see [LICENSE](./LICENSE)).
- Commercial license for companies that cannot or do not want to comply with the AGPL: see [COMMERCIAL-LICENSE.md](./COMMERCIAL-LICENSE.md).

<!-- TODO: update after license change -->

## Trademark

"A.B.R.I.L" and "Nexora" are trademarks. See [TRADEMARKS.md](./TRADEMARKS.md).

## Credits

Created by **Nexora** (Founder: Santiago Sarmiento). GitHub: @saaarmyx.