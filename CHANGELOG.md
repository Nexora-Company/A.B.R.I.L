# Registro de cambios

Todos los cambios notables de este proyecto se documentan aquí. Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/) y [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Añadido

- Fase 0: fundación del proyecto (`pyproject.toml`, tests, CI, flags y bootstrap).
- Fase 1: router de tres carriles, perfiles de hardware y optimización CPU.
- Motor de políticas por niveles, privacidad `local-strict` y manejo de contenido no confiable.
- Plantillas de personalidad opcionales y motor predictivo de alias.
- Memoria persistente en SQLite con migración desde los JSON históricos.
- Protocolo NEXO-BRACE para limitar capacidades y NEXUS-LOCK para domótica.
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
- La migración de JSON a SQLite se ejecuta una sola vez y no duplica historial ni auditoría.
- Timestamps UTC sin la API obsoleta `datetime.utcnow()`.

### Eliminado

- Frontend web; documentación actualizada.

[Unreleased]: https://github.com/Nexora-Company/A.B.R.I.L/commits/main