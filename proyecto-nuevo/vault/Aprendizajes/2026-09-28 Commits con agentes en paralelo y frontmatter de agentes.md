---
fecha: 2026-09-28
etiquetas: [proceso, git, agentes]
origen: Claude principal
---
# Commits con agentes en paralelo y frontmatter de agentes

- **Qué pasó:**
  - El hook de git obligó a hacer commit mientras varios agentes en paralelo seguían escribiendo, y se subieron archivos a medio hacer.
  - Error propio: la definición del agente `ventas` se rompió porque la descripción tenía ":" y el script que la generaba partía la línea por ahí.
- **Lección:**
  - Con agentes en paralelo: **commit solo de carpetas terminadas**, o commit marcado "**WIP, pendiente de revisión**".
  - Validar el **frontmatter** (`name`, `description`, `tools`) de cada agente de `.claude/agents/` tras crearlo; evitar ":" sin comillas en la descripción.
- **Cómo aplicarla:** antes de `git add`, comprobar qué agentes siguen activos; tras crear un agente, releer su cabecera YAML.
