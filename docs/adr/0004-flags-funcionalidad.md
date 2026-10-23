# ADR 0004 — Flags de funcionalidad para cambios incrementales

- **Estado:** aceptado
- **Fecha:** 2026-10-23

## Contexto

El roadmap añade muchas capacidades sobre un código que ya funciona. Un cambio
global puede romper el flujo diario sin forma sencilla de volver atrás.

## Decisión

Cada capacidad nueva se controla con un flag booleano en `data/config.json`,
gestionado por `abril.app.flags.FeatureFlags`. Los valores por defecto
reproducen el comportamiento actual. `/config` permite consultarlos y cambiarlos
en caliente.

## Consecuencias

- Se puede desactivar una función sin revertir código.
- Los tests pueden activar solo lo necesario.
- Los flags desconocidos o corruptos se ignoran y vuelven al valor por defecto.
- Los flags son temporales: cuando una función se estabiliza, se puede fijar su
  valor y retirar el flag.
