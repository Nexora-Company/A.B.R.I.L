# ADR 0002 — SQLite para memoria y estado local

- **Estado:** aceptado (implementación en Fase 1)
- **Fecha:** 2026-10-23

## Contexto

La memoria actual vive en `data/memory.json` y el historial en
`data/chat_history.json`. Funciona, pero el roadmap necesita perfil de usuario,
memorias, alias, eventos, tareas, cuotas y diario de deshacer. Los archivos JSON
implican reescrituras completas, bloqueos manuales y migraciones frágiles.

## Decisión

Usar SQLite (incluido en la biblioteca estándar) en `data/abril.db`, con
migraciones idempotentes desde los JSON existentes. La API pública de
`MemoryService` se mantiene para no romper `main.py`.

## Consecuencias

- Una sola base local, sin servidor ni dependencias externas.
- Se conservan los JSON como respaldo y exportación.
- La migración copia y valida antes de borrar; nunca destruye datos.
- Los tests usan bases temporales y no tocan `data/`.
