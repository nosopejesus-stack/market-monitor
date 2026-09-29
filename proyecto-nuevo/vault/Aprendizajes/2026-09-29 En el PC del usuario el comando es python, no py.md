---
fecha: 2026-09-29
etiquetas: [entorno, python, windows, documentacion]
origen: sesión en el PC del usuario, 2026-09-29
---
# 2026-09-29 En el PC del usuario el comando es python, no py

- **Qué pasó:** `PASO_A_PASO.md` y el README decían `py lote.py …`. En el PC del usuario está Python 3.12.10, pero el lanzador `py` no existe: el comando es `python`.
- **Lección:** no suponer el lanzador de Windows. Las guías para el usuario se escriben con el comando que se ha comprobado en su equipo.
- **Cómo aplicarla:**
  - Usar `python …` en toda guía (corregidos `PASO_A_PASO.md` y README).
  - Ante una guía nueva, comprobar con `python --version` en su PC antes de documentar.
  - Relacionado: [[2026-09-28 Front matter YAML y documentar opciones que existen]].
