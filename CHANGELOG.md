# Registro de cambios

Todos los cambios notables de este proyecto se documentan aquí. Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) y [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Añadido

- Fase 0: fundación del proyecto (`pyproject.toml`, tests, CI, flags y bootstrap).
- Comandos `/version` y `/config` para consultar y cambiar flags en caliente.
- Pruebas con proveedor falso que no requieren Ollama.
- ADRs iniciales en `docs/adr/`.

### Cambiado

- `main.py` construye los servicios mediante `abril.app.bootstrap`.
- `Settings` lee `ABRIL_HOST` y `ABRIL_PORT` (reservados para modos futuros).
- Analizador de patrones y sugeridor de ideas (Fase C).
- Asistente de programación local (Fase B).
- Contexto persistente entre sesiones (Fase A).
- Servicio de memoria personal con preferencias y rutinas.
- 7 tipos de acción con confirmación: open, search, summarize, execute, read, write, list.
- Identidad inmutable (Nexora/Santiago) y personalidad fija.

### Corregido

- `pattern_analyzer` ahora importa sus dependencias; `/analizar`, `/ideas` y `/pensar` se despachan correctamente.
- El lector de `.env` maneja comillas con comentarios en línea.

### Eliminado

- Frontend web; documentación actualizada.

[Unreleased]: https://github.com/Nexora-Company/A.B.R.I.L/commits/main