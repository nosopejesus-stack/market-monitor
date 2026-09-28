---
fecha: 2026-09-28
etiquetas: [arcend, informes, revision]
origen: arcend/blindaje/informe.py
---
# Avisos de verificar visibles, nunca en comentarios HTML

- **Qué pasó:** Avisos del tipo "verificar antes de imprimir" (cifras de sanciones, normas SIN VERIFICAR) quedaban en comentarios HTML: no se ven en el navegador ni en el PDF, así que nadie los lee antes de imprimir.
- **Lección:** Un aviso para el usuario tiene que verse en el documento. Los comentarios HTML son invisibles en la práctica.
- **Cómo aplicarla:**
- Avisos de verificación como texto visible (p. ej. `[VERIFICAR fuente antes de usar]`).
- Al revisar un HTML generado, buscar `<!--` con avisos dentro.

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
