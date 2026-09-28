---
fecha: 2026-09-28
etiquetas: [permisos, seguridad, agentes]
origen: stack infra (n8n)
---
# Crear cuentas y credenciales es decisión del usuario

- **Qué pasó:** el clasificador del auto mode bloqueó crear la cuenta admin de n8n con el email del usuario y generar el token MCP de n8n, por "Unauthorized Persistence".
- **Lección:** crear cuentas o credenciales persistentes (admins, tokens, API keys) es una decisión del usuario, no de los agentes.
- **Cómo aplicarla:** preparar todo lo demás y dejar al usuario instrucciones paso a paso para crear la cuenta y el token él mismo. No reintentar ni buscar rodeos. Los tokens nunca se guardan en el vault.

Relacionado: [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]]
