---
fecha: 2026-09-28
etiquetas: [error, markdown, yaml, proceso]
origen: Claude principal, sesión Arcend
---
# Front matter YAML y documentar opciones que existen

- **Qué pasó:** Error de Claude principal: insertó una nota con `sed` en la línea 2 de `arcend/investigacion/mercado.md`, dentro del front matter YAML, y lo rompió. Además, se documentaron opciones de la herramienta sin comprobar que existían (otro agente las estaba programando en paralelo).
- **Lección:** En Markdown con cabecera `---`, insertar siempre después del cierre `---`, nunca por número de línea fijo. Antes de documentar opciones de una herramienta, comprobar con grep que existen en el código o coordinar con el agente que las programa.
- **Cómo aplicarla:**
- Para insertar: localizar el segundo `---` y escribir detrás (o usar Edit con ancla de texto).
- `grep -n -- "--opcion" script.py` antes de escribir en README o PASO_A_PASO.

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
