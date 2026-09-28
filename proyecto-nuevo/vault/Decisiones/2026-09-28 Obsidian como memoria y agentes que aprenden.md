---
fecha: 2026-09-28
estado: aceptada
---
# Obsidian como memoria y agentes que aprenden

- **Contexto:** cada sesión de Claude empieza sin memoria; el contenedor se borra.
- **Decisión:** la memoria vive en este vault de Obsidian (Markdown en git). Los agentes de `.claude/agents/` lo leen al empezar y escriben al terminar.
- **Consecuencias:** hay que hacer commit y push del vault al acabar cada sesión; tú lo sincronizas en tu PC con Obsidian (plugin *Obsidian Git*).
