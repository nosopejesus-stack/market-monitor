---
fecha: 2026-09-28
etiquetas: [entorno, prospeccion, negocio]
origen: prospector + investigador
---
# Prospección desde el contenedor cloud

- **Qué pasó:** al construir `negocio/prospectos/agencias_madrid.csv` (111 agencias, 54 prospectables) e investigar WhatsApp.
- **Lección:**
  - **WebSearch funciona**; **WebFetch y curl están bloqueados** para portales, Meta, EUR-Lex y webs de agencias (amplía [[2026-09-28 El contenedor cloud no tiene internet libre]]).
  - La prospección desde aquí da nombre/dirección/teléfono **SIN VERIFICAR**; verificar y sacar el decisor desde el PC del usuario.
  - En los 5 distritos prioritarios **~la mitad son franquicias** (Tecnocasa, Redpiso...), que suelen decidir en central.
  - Playwright (node) disponible en `/opt/node22/lib/node_modules/playwright` con `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` (útil para probar demos en local).
- **Cómo aplicarla:** marcar siempre la columna de verificación en el CSV; priorizar agencias independientes; no prometer datos verificados salidos del contenedor.
