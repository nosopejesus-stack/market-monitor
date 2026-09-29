---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, reglas, falsos-positivos]
origen: revisión a mano de 996 hallazgos del lote real (3 revisores en paralelo), 2026-09-29
---
# 2026-09-29 Filtros de contexto en todas las reglas que cuentan en N

- **Qué pasó:** los filtros de negación y contexto ([[2026-09-28 Detectores de lenguaje prohibido con negación y contexto]]) estaban en unas reglas y no en otras. La revisión a mano encontró falsos positivos en todas las reglas que suman a N:
  - **Promociones:** consulta/cita/diagnóstico gratuitos, línea 900, "promoción de la salud", newsletter, catálogo ("amplia oferta"), negaciones, preguntas de blog, bonos con precio sin descuento, tratamientos no médicos (masaje, higiene facial, dermocosmética, aparatología, psicología). "Promociones" sin precio ni descuento → BAJA "revisar a mano", no cuenta.
  - **Toxina:** en el currículum del médico → revisar; "POST-TOXINA" (cosmético) no cuenta.
  - **Garantías:** "garantizar" como consejo, finalidad o referido a la AEMPS no cuenta; "sin dolor" matizado; "dietas milagro" (crítica); "sin riesgo de X" → MEDIA.
  - **Registro "ausente"** marcado ALTA sin haber leído el aviso legal: repetía [[2026-09-28 Reglas de ausencia solo con lectura suficiente]]. Ahora BAJA `registro_sin_lectura`.
- **Lección:** un filtro de contexto que se aprende en una regla se aplica a **todas** las reglas que cuentan en N. Y una lección ya guardada se comprueba en cada regla nueva: la de ausencias se volvió a romper.
- **Cómo aplicarla:**
  - Al añadir una regla que cuenta en N, repasar la lista de filtros de esta nota y añadir un test por cada uno que aplique.
  - Lo dudoso baja a BAJA "revisar a mano" y no cuenta.
  - Tras cada lote real, revisión a mano de una muestra amplia (esta vez 996 hallazgos, 125 tests OK tras las correcciones).
  - Promesas nuevas traídas del risk-scanner: [[2026-09-29 Integrar el risk-scanner antiguo en Blindaje]].
