# ADR 0001 — Núcleo con biblioteca estándar y dependencias opcionales

- **Estado:** aceptado
- **Fecha:** 2026-10-23

## Contexto

A.B.R.I.L debe poder ejecutarse en equipos modestos y sin conexión. Añadir un
árbol de dependencias obligatorio encarece la instalación y aumenta la
superficie de fallo. A la vez, funciones futuras (voz, HUD, proveedores cloud)
necesitan bibliotecas que no forman parte de la biblioteca estándar.

## Decisión

El núcleo (chat, acciones, memoria, configuración y terminal) usa solo la
biblioteca estándar de Python. Las capacidades futuras se empaquetan como
extras opcionales en `pyproject.toml`: `ui`, `voice` y `cloud`.

## Consecuencias

- La instalación base sigue siendo `python3 main.py`.
- Cada extra se instala solo cuando la persona lo necesita.
- Todo módulo opcional debe degradar con un mensaje claro si falta la
  dependencia, nunca impedir el arranque.
- El CI instala únicamente `.[dev]`; los extras se prueban más adelante.
