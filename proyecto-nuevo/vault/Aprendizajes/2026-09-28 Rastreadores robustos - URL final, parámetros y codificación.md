---
fecha: 2026-09-28
etiquetas: [arcend, blindaje, rastreador, python]
origen: arcend/blindaje/blindaje.py
---
# Rastreadores robustos - URL final, parámetros y codificación

- **Qué pasó:** En el rastreador de Blindaje había que evitar descargar la misma página varias veces (`/botox` y `/botox/`, redirecciones, `utm_*`, `fbclid`, `gclid`), no alterar la URL al limpiar parámetros, que un enlace mal formado no tumbara el rastreo y que el texto no saliera roto en webs que declaran mal el charset.
- **Lección:** un rastreador debe tolerar la web real:
  - Deduplicar por la URL final tras la redirección.
  - Quitar `utm_*`, `fbclid` y `gclid` sin recodificar el resto de la query.
  - `try/except` por enlace: uno mal formado se salta, no para el rastreo.
  - Decodificar primero con UTF-8 estricto y después con lo declarado.
- **Cómo aplicarla:**
- Aplicarlo en cualquier rastreador del proyecto; cubrir cada caso con el servidor simulado de los tests.

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
