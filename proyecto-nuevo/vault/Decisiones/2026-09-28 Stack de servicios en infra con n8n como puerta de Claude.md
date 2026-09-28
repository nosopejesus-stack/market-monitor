---
fecha: 2026-09-28
estado: aceptada
---
# Stack de servicios en infra con n8n como puerta de Claude

- **Contexto:** queremos automatizaciones, atención al cliente, IA local, analítica web y generación de imágenes funcionando 24/7. El contenedor cloud de Claude es efímero (se borra al acabar la sesión y no tiene internet libre, ver [[Aprendizajes/2026-09-28 El contenedor cloud no tiene internet libre]]), así que no puede alojar servicios.
- **Opciones consideradas:** servicios alojados en el contenedor de Claude (descartado: efímero); stack propio en un VPS con Coolify (elegido). Para "analytics" se eligió Umami.
- **Decisión:**
  - Stack en `infra/` (docker-compose) con **n8n, Chatwoot, Ollama, Umami y ComfyUI**, compartiendo **Postgres 17 + pgvector** y **Redis**.
  - Se despliega 24/7 en un **VPS propio con Coolify**.
  - Claude se conecta a **n8n por su MCP de instancia** (`/mcp-server/http`, token Bearer) y, a través de n8n, usa el resto de servicios.
- **Consecuencias:**
  - Pendiente (lo crea el usuario, no los agentes): servidor, dominios, cuentas admin y token MCP. Ver [[Aprendizajes/2026-09-28 Crear cuentas y credenciales es decisión del usuario]].
  - Reglas de seguridad y despliegue a respetar: [[Aprendizajes/2026-09-28 Seguridad de stacks en servidor]], [[Aprendizajes/2026-09-28 Init de Postgres, secretos y Coolify]], [[Aprendizajes/2026-09-28 n8n necesita IPv4 explícito y Postgres 17]].
  - El token MCP nunca se guarda en el vault ni en el repo.
