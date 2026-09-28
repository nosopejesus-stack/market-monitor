---
fecha: 2026-09-28
etiquetas: [ventas, negocio, revision]
origen: revisor (dos revisiones del kit de negocio)
---
# Coherencia comercial en el kit de ventas

- **Qué pasó:** el revisor encontró cifras distintas (tiempos de respuesta, precios, plazos, "0 €") entre `PLAN.md`, propuesta, guion, contrato, demo y `ARQUITECTURA.md`, cuentas de ingresos que no respetaban el calendario de cobro del contrato y el alta de autónomo puesta "antes del primer cobro".
- **Lección:**
  - Cada cifra debe aparecer **igual** en plan, propuesta, guion, contrato, demo y arquitectura.
  - Si depende de terceros o no se ha medido → "**objetivo, se mide en el piloto**", nunca garantía.
  - Las previsiones de ingresos deben seguir el **calendario de cobro del contrato**.
  - El alta de autónomo va **antes de facturar** (antes del primer contrato), no "antes del primer cobro".
  - Consultas de prueba a agencias: **pretexto mínimo**, se revela en la visita y **nunca** se saca información sensible del vendedor.
- **Cómo aplicarla:** al cambiar una cifra, buscarla con Grep en todo `proyecto-nuevo/negocio/` y actualizar todas las apariciones; pedir al [[Agentes/Revisor|revisor]] una pasada de coherencia antes de dar el kit por cerrado.
