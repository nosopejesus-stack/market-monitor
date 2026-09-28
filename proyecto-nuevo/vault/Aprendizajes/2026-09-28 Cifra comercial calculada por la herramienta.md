---
fecha: 2026-09-28
etiquetas: [arcend, blindaje, ventas, cifras]
origen: arcend/blindaje/reglas.py
---
# Cifra comercial calculada por la herramienta

- **Qué pasó:** La llamada usa la frase "hay N puntos que la normativa de publicidad sanitaria no permite". Contar N a mano mezclaba hallazgos repetidos (la misma frase en el texto y en la descripción) y hallazgos con norma SIN VERIFICAR.
- **Lección:** N = `n_puntos_norma` de `informe.json`: lo calcula la herramienta, con hallazgos ALTA/MEDIA sin nada SIN VERIFICAR, deduplicados por regla y frase. Al marcar normas SIN VERIFICAR, N baja: a 2026-09-28 solo cuentan toxina y promociones (según lo indicado en la sesión; comprobar en `reglas.py` si cambia). Si N = 0, no se usa el anzuelo de la llamada.
- **Cómo aplicarla:**
- Nunca contar N a mano ni redondear al alza.
- Cuando se verifique una norma en el BOE/BOCM y se le quite el SIN VERIFICAR, N sube para esa regla: actualizar tests.
- Ver [[Decisiones/2026-09-28 Arcend - Informe previo y N calculado por la herramienta]].

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
