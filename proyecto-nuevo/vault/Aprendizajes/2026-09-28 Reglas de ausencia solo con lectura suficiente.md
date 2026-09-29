---
fecha: 2026-09-28
etiquetas: [arcend, blindaje, rastreador, javascript]
origen: arcend/blindaje/blindaje.py
---
# Reglas de ausencia solo con lectura suficiente

- **Qué pasó:** Las reglas del tipo "falta X" (nº de registro sanitario, páginas legales, médico responsable) se disparaban en webs hechas con JavaScript (`<div id="root">`) de las que el rastreador sin JS no lee casi nada: el informe acusaba de faltas que quizá no existen.
- **Lección:** No se puede afirmar que algo falta si no se ha leído lo suficiente. Umbral: ≥ 300 caracteres de texto entre todas las páginas y ≥ 2 páginas leídas. Por debajo, el informe sale con aviso en rojo "revisión no fiable" y sin reglas de ausencia.
- **Cómo aplicarla:**
- Toda regla de ausencia comprueba antes la cobertura de lectura.
- Si sale "revisión no fiable", guardar las páginas con el navegador (Ctrl+S) y usar `--html-local CARPETA`.

- **Repetido 2026-09-29:** la regla de registro sanitario marcaba "ausente" ALTA sin haber leído el aviso legal. Corregido: BAJA `registro_sin_lectura`. Ver [[2026-09-29 Filtros de contexto en todas las reglas que cuentan en N]].

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
