---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, lote, python, proceso]
origen: lote real de 48 webs, 2026-09-29
---
# 2026-09-29 Guardar páginas y reanalizar sin descargar

- **Qué pasó:** el lote real de 48 webs tarda ~35 min (39 con frase, 7 errores por robots.txt 4xx o SSL, 2 no legibles). Cada corrección de reglas tras la revisión a mano habría obligado a descargarlo todo otra vez.
- **Lección:** separar descarga y análisis. `lote.py` guarda cada web en `informes/<clínica>/paginas.json` y `--reanalizar` repasa las reglas sin descargar (segundos).
- **Cómo aplicarla:**
  - Tras cambiar `reglas.py`: `python lote.py ..\prospectos\clinicas.csv --reanalizar`.
  - Las webs que no se pudieron leer las guarda el usuario con Ctrl+S.
  - Relacionado: [[2026-09-29 Lote robusto, gancho honesto y acceso al PC]].
