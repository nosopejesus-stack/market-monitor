# Revisor

Definición: `.claude/agents/revisor.md`. Volver a [[Equipo de agentes]].

## Historial de aprendizajes de este agente
- 2026-09-28 (stack `infra/`): en stacks para servidor revisar exposición de puertos (solo `127.0.0.1` + proxy de Coolify con HTTPS), servicios sin auth (Ollama, ComfyUI), usuarios de Postgres sin SUPERUSER y paneles que regalan el admin al primer visitante (n8n, Chatwoot, Coolify; Umami `admin/umami`). Ver [[Aprendizajes/2026-09-28 Seguridad de stacks en servidor]].
- 2026-09-28 (stack `infra/`): revisar idempotencia de los scripts de `docker-entrypoint-initdb.d`, que `N8N_ENCRYPTION_KEY` no cambie, `set -e` con `$(...)` como argumento, healthcheck de Postgres por TCP, bind mounts en Coolify y claves solo de Coolify (`exclude_from_hc`). Ver [[Aprendizajes/2026-09-28 Init de Postgres, secretos y Coolify]].
