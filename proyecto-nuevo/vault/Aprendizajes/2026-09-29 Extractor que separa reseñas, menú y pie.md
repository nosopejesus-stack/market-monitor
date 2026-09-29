---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, extractor, falsos-positivos]
origen: revisión a mano de 996 hallazgos del lote real, 2026-09-29
---
# 2026-09-29 Extractor que separa reseñas, menú y pie

- **Qué pasó:** las reseñas de pacientes (widgets de Trustindex o Google, o textos en primera persona tipo "me hice…") contaban como publicidad de la clínica. Y el menú/pie repetido en todas las páginas multiplicaba hallazgos.
- **Lección:** una web no es un texto único. El extractor debe separar **zonas**: contenido propio, reseñas de terceros y menú/pie. Las reseñas solo cuentan en la regla de testimonios; el menú/pie se lee una vez. Además, deduplicar páginas equivalentes (`/` e `/index.html`).
- **Cómo aplicarla:**
  - Al añadir una regla, decidir en qué zonas aplica.
  - Test con un widget de reseñas y un menú repetido en varias páginas.
  - Relacionado: [[2026-09-29 N por tipos de infracción, no por frases]], [[2026-09-28 Rastreadores robustos - URL final, parámetros y codificación]], [[2026-09-28 Detectores de lenguaje prohibido con negación y contexto]].
