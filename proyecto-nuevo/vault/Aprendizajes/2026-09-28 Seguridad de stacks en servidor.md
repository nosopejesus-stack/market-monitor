---
fecha: 2026-09-28
etiquetas: [seguridad, servidor, coolify, postgres]
origen: revisión del agente revisor sobre infra/
---
# Seguridad de stacks en servidor

- **Qué pasó:** el [[Agentes/Revisor|revisor]] revisó el docker-compose de `infra/` antes de llevarlo a un VPS.
- **Lección:**
  - Ollama y ComfyUI no tienen autenticación: nunca exponerlos a internet directamente.
  - Los usuarios de las apps en Postgres nunca deben ser SUPERUSER.
  - En n8n, Chatwoot y Coolify el primer visitante del panel se queda de admin; Umami trae `admin/umami` por defecto.
- **Cómo aplicarla:**
  - Publicar puertos solo en `127.0.0.1` y salir a internet por el proxy de Coolify con HTTPS.
  - Crear las extensiones (pgvector, etc.) con el usuario `postgres` en el script de init; los usuarios de apps, sin privilegios de superusuario.
  - Tras desplegar, reclamar de inmediato los paneles de admin (n8n, Chatwoot, Coolify) y cambiar la contraseña por defecto de Umami. Esto lo hace el usuario ([[Aprendizajes/2026-09-28 Crear cuentas y credenciales es decisión del usuario]]).

Relacionado: [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]]
