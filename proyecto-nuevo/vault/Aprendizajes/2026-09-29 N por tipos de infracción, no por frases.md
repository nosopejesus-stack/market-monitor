---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, reglas, cifras, revision]
origen: revisión a mano de 996 hallazgos del lote real (48 webs), 2026-09-29
---
# 2026-09-29 N por tipos de infracción, no por frases

- **Qué pasó:** en el lote real, `n_puntos_norma` contaba frases distintas. El menú repetido en 15 páginas y cada frase que mencionaba bótox inflaban N: IME llegó a N = 22. Delante de un médico, "22 puntos" que son el mismo menú repetido destruye la credibilidad. `PASO_A_PASO.md` ya decía "tipos de infracción", pero el código no lo hacía.
- **Lección:** N = número de **tipos de infracción distintos con norma concreta** (hoy: publicidad de toxina, promoción sobre acto médico), no número de frases ni de páginas. Las frases son evidencia del tipo, no puntos nuevos. Si la guía y el código dicen cosas distintas, manda la guía y se corrige el código con test.
- **Cómo aplicarla:**
  - En `reglas.py`, agrupar por tipo antes de contar; varias frases del mismo tipo = 1 punto con varias evidencias.
  - Cualquier cifra comercial se coteja contra lo que dice la guía de venta ([[Aprendizajes/2026-09-28 Cifra comercial calculada por la herramienta]], [[Aprendizajes/2026-09-28 Verificar cada cifra de un resumen]]).
  - Decisión: [[Decisiones/2026-09-29 Arcend - N por tipos y grupos del mismo titular]].
  - Relacionado: [[2026-09-29 Evidencia más concreta en cada punto]], [[2026-09-29 Filtros de contexto en todas las reglas que cuentan en N]].
