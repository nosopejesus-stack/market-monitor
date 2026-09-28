---
fecha: 2026-09-28
etiquetas: [postgres, bash, coolify, n8n, docker]
origen: revisión del agente revisor sobre infra/
---
# Init de Postgres, secretos y Coolify

- **Qué pasó:** el [[Agentes/Revisor|revisor]] encontró varios fallos sutiles en los scripts de init, el generador de secretos y el compose del stack de `infra/`.
- **Lección:**
  - Los scripts de `docker-entrypoint-initdb.d` solo se ejecutan con el volumen de datos vacío.
  - Si se cambia `N8N_ENCRYPTION_KEY` después del primer arranque, n8n ya no puede descifrar las credenciales guardadas.
  - En bash, `set -e` no captura fallos de `$(...)` usados como argumentos de otro comando.
  - Un healthcheck de Postgres por socket puede dar "healthy" durante el init (servidor temporal).
  - Coolify no garantiza bind mounts de archivos del repo.
  - `exclude_from_hc` es solo de Coolify; `docker compose` lo rechaza.
- **Cómo aplicarla:**
  - Scripts de init idempotentes: `\gexec` + `NOT EXISTS` para crear roles/bases, y `ALTER ROLE ... PASSWORD` para sincronizar contraseñas.
  - Generar `N8N_ENCRYPTION_KEY` una vez y no tocarla nunca más.
  - Generar los secretos primero en variables (`x=$(...)`) y usarlas después, para que `set -e` corte si fallan.
  - Healthcheck de Postgres por TCP: `pg_isready -h 127.0.0.1 ...`.
  - Meter los archivos de config/init en una imagen propia (con `build`) en vez de montarlos.
  - No usar `exclude_from_hc` en el compose que se prueba con `docker compose`.

Relacionado: [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]]
