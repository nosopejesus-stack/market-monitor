# Inicio

Memoria compartida del proyecto entre tú y los agentes. **Todo lo importante vive aquí.**

## Cómo se usa
1. Antes de cualquier tarea, los agentes leen esta nota, [[Aprendizajes/Índice de aprendizajes]] y las [[Decisiones/Índice de decisiones|decisiones]].
2. Al terminar, el agente [[Agentes/Bibliotecario|bibliotecario]] guarda lo aprendido, las decisiones y la entrada del [[Diario]].
3. Tú puedes editar cualquier nota desde Obsidian: los agentes la leerán en la próxima sesión.

## Estado del proyecto
- **Nombre:** _(pendiente)_
- **Objetivo:** _(pendiente — definir en [[Proyecto/Visión]])_
- **Fase actual:** arranque
- **Infraestructura:** stack en `infra/` (n8n, Chatwoot, Ollama, Umami, ComfyUI + Postgres 17/pgvector + Redis) probado en el contenedor cloud; pendiente de desplegar 24/7 en un VPS con Coolify. Claude usará los servicios a través del MCP de instancia de n8n. Ver [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]].
- **Pendiente del usuario:** servidor, dominios, cuentas admin y token MCP de n8n.

## Mapa
- [[Proyecto/Visión]] — qué construimos y para quién
- [[Aprendizajes/Índice de aprendizajes]] — lo que ya sabemos (no repetir errores)
- [[Decisiones/Índice de decisiones]] — por qué hicimos las cosas así
- [[Agentes/Equipo de agentes]] — quién hace qué
