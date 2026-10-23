# ADR 0005: decisiones de Fase 1 y preparación de Fase 2/3

- **Estado:** aceptado
- **Fecha:** 2026-10-23

## Contexto

La Fase 1 quedó implementada con flags apagados por defecto. Antes de avanzar
a tareas en segundo plano, varios modelos y voz local, hacía falta fijar
decisiones que condicionan la arquitectura.

## Decisión

1. **Python mínimo:** se mantiene `>=3.10` para no excluir sistemas LTS.
2. **Modelos locales:** el router elige modelo ligero y pesado según el tier
   de hardware (`recommended_models`). Los flags siguen apagados por defecto.
3. **Migración SQLite:** al activar `sqlite_memory` los JSON históricos se
   importan una sola vez; los archivos originales se conservan como respaldo.
4. **Voz (Fase 3):** push-to-talk y wake word configurables. Push-to-talk será
   el modo por defecto por privacidad y consumo.
5. **UI opcional:** `rich`, por ser más ligera que `textual` y no exigir
   reescribir el bucle de terminal.
6. **Consentimiento NEXO-BRACE:** explícito mediante `/desbloquear` y
   `/desbloquear confirmar`; `/bloquear` revoca el consentimiento y activa el
   bloqueo global de NEXUS-LOCK. El consentimiento no se persiste entre
   sesiones: cada arranque vuelve a LOCKED.
7. **Nube:** sin proxy de Nexora. Cada usuario aporta su propia clave y debe
   activar `cloud_providers`; el consentimiento se solicita en runtime.

## Consecuencias

- Los modelos sugeridos pueden requerir `ollama pull` adicional en hardware
  modesto o con GPU.
- La voz necesita extras opcionales y no forma parte de la instalación base.
- El desbloqueo es conservador: reiniciar Abril vuelve a bloquear capacidades.
