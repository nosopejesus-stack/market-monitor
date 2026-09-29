---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, risk-scanner, reglas]
origen: revisión de C:\Users\nitrpc\dev\risk-scanner, 2026-09-29
---
# 2026-09-29 Integrar el risk-scanner antiguo en Blindaje

- **Qué pasó:** se revisó el risk-scanner antiguo (`C:\Users\nitrpc\dev\risk-scanner`). `modulos_osint_v3.py` ya no existe como fuente (solo el `.pyc`) y su parte sanitaria está superada por Blindaje.
- **Lección:** de un proyecto previo se trae solo lo que tiene norma o utilidad comprobada:
  - **Traído:** promesas "100 % eficaz/efectivo", "resultados permanentes/para siempre", "cura definitiva" (no "resultado definitivo", que suele ser "se aprecia a las dos semanas"); detector de posible cadena (`senales_cadena`, columna `posible_cadena` del lote, uso interno, no sale en el informe).
  - **No traído:** superlativos ("el mejor de Madrid"), porque no hay norma sanitaria verificada; enlaces legales que acaban en portada (solo evitan falsos negativos).
- **Cómo aplicarla:** cada regla importada entra con test y con los filtros de [[2026-09-29 Filtros de contexto en todas las reglas que cuentan en N]]. Relacionado: [[2026-09-28 Revisar proyectos previos antes de proponer negocio]].
