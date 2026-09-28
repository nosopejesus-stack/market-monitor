---
fecha: 2026-09-28
etiquetas: [arcend, blindaje, textos, legal]
origen: arcend/blindaje/reglas.py
---
# Textos corregidos sin afirmar hechos del cliente

- **Qué pasó:** Los textos corregidos "listos para publicar" afirmaban hechos que la herramienta no conoce del cliente: que el centro está inscrito, el colegio o nº de colegiado del médico, o que los pacientes han dado su consentimiento para fotos y testimonios.
- **Lección:** Un texto corregido nunca afirma hechos del cliente. Lo que depende de la clínica va como condicional entre corchetes `[Solo si…]` (se comprueba con la clínica y se quita antes de publicar) y los datos como marcadores `{...}` para rellenar.
- **Cómo aplicarla:**
- Revisar cada plantilla de texto corregido buscando afirmaciones sobre inscripción, colegiación o consentimiento.
- Las plantillas legales (aviso legal, privacidad, cookies) son borrador mínimo para validar con el asesor.

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
