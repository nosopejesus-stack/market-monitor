---
fecha: 2026-09-29
etiquetas: [entorno, bash, python, regex]
origen: parches a reglas.py en el PC del usuario, 2026-09-29
---
# 2026-09-29 Heredoc de bash y barras invertidas

- **Qué pasó:** en este entorno (Git Bash en Windows), los scripts de parche escritos con heredoc convertían `\\` en `\` y rompían las expresiones regulares de `reglas.py`.
- **Lección:** no pasar por heredoc texto con barras invertidas (regex, rutas de Windows).
- **Cómo aplicarla:**
  - Para parches con barras invertidas, escribir el script con la herramienta Write (o editar con Edit) y ejecutarlo después.
  - Tras parchear regex, pasar los tests (hoy 125) antes de dar nada por bueno.
  - Relacionado: [[2026-09-28 Init de Postgres, secretos y Coolify]] (otras trampas de bash).
