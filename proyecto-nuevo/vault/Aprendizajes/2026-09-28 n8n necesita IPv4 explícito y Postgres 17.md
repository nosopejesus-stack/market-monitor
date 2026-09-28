---
fecha: 2026-09-28
etiquetas: [n8n, postgres, docker]
origen: stack infra
---
# n8n necesita IPv4 explícito y Postgres 17

- **Qué pasó:** n8n falló al arrancar con `address '::' is not available` en un entorno sin IPv6. Además, n8n 2.40 avisa de que Postgres 16 ya no tiene soporte completo.
- **Lección:** n8n escucha en `::` por defecto; sin IPv6 no arranca. Postgres 16 se queda corto para n8n actual.
- **Cómo aplicarla:** fijar `N8N_LISTEN_ADDRESS=0.0.0.0` y usar Postgres 17 (con pgvector) en el stack.

Relacionado: [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]]
