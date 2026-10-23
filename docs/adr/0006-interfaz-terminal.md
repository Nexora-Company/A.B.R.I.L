# ADR 0006: rediseño de la interfaz de terminal

- **Estado:** aceptado
- **Fecha:** 2026-10-23

## Contexto

La interfaz anterior era funcional pero plana: banner sin centrar, mensajes
en una sola línea y sin contexto de rendimiento. Se buscó un layout similar a
los asistentes de terminal modernos (banner centrado, compositor con acento,
bloques de conversación y metadatos), manteniendo el arte y la identidad de
A.B.R.I.L.

## Decisión

- Renderizador propio con ANSI y biblioteca estándar en `abril/ui/terminal.py`.
  No se añade una dependencia obligatoria.
- Layout *inline*: se conserva el scrollback del terminal en lugar de usar
  pantalla alternativa. Cada turno añade su bloque y un compositor nuevo.
- Ancho adaptable al terminal (56–96 columnas) y versión alineada a la derecha.
- Colores de marca: morado `#4B0382`/`#A855F7` para acentos y rojo Nexora
  `#B31B1B` para la firma.
- Sin color cuando `NO_COLOR` está definido o la salida no es una TTY.
- Arte ASCII original intacto: solo se colorea con un degradado y se centra.
- Métricas por respuesta: latencia y tokens por segundo estimados.

## Consecuencias

- La interfaz sigue funcionando en terminales sin truecolor (los códigos se
  ignoran o degradan) y en entornos no interactivos.
- El formato es más vistoso, pero el texto del compositor se dibuja antes de
  `input()`; por eso el borde inferior se cierra justo después de enviar.
- Cambios de ancho a mitad de sesión no redibujan los bloques ya impresos.
