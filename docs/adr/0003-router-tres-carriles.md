# ADR 0003 — Router de tres carriles

- **Estado:** aceptado (implementación en Fase 1)
- **Fecha:** 2026-10-23

## Contexto

Enviar cada mensaje al modelo grande es lento y caro en CPU. Muchas peticiones
son comandos directos, alias o variaciones con errores de escritura que no
necesitan un modelo.

## Decisión

Clasificar cada entrada en tres carriles:

1. Reglas y coincidencia aproximada, sin IA.
2. Modelo ligero para intención y respuestas cortas.
3. Modelo pesado para código, análisis y razonamiento.

El router devuelve una decisión explícita (`lane`, `intent`, `confidence`,
`model`, `reason`). Si el flag `routing` está apagado, todo va al carril 3 como
hoy.

## Consecuencias

- Los comandos directos responden en milisegundos.
- Se reduce el uso de CPU y el consumo de contexto.
- El router debe ser testeable sin Ollama.
- Un fallo de clasificación nunca bloquea: cae al carril 3.
