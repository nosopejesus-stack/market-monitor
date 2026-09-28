# Revisor

Definición: `.claude/agents/revisor.md`. Volver a [[Equipo de agentes]].

## Historial de aprendizajes de este agente
- 2026-09-28 (stack `infra/`): en stacks para servidor revisar exposición de puertos (solo `127.0.0.1` + proxy de Coolify con HTTPS), servicios sin auth (Ollama, ComfyUI), usuarios de Postgres sin SUPERUSER y paneles que regalan el admin al primer visitante (n8n, Chatwoot, Coolify; Umami `admin/umami`). Ver [[Aprendizajes/2026-09-28 Seguridad de stacks en servidor]].
- 2026-09-28 (stack `infra/`): revisar idempotencia de los scripts de `docker-entrypoint-initdb.d`, que `N8N_ENCRYPTION_KEY` no cambie, `set -e` con `$(...)` como argumento, healthcheck de Postgres por TCP, bind mounts en Coolify y claves solo de Coolify (`exclude_from_hc`). Ver [[Aprendizajes/2026-09-28 Init de Postgres, secretos y Coolify]].
- 2026-09-28 (`infra/server/`): en sshd manda el **primer** valor: drop-in `00-*.conf` (un `99-*` pierde frente a `50-cloud-init.conf`) y validar con `sshd -T | grep` (`sshd -t` solo valida sintaxis). `MaxAuthTries` bajo + fail2ban bloquea a quien tiene varias llaves: `MaxAuthTries 6` e `IdentitiesOnly yes`. Ver [[Aprendizajes/2026-09-28 Endurecimiento de SSH con drop-ins]].
- 2026-09-28 (`infra/server/`): un firewall que sale con error al no detectar la interfaz falla en abierto; DOCKER-USER sin `-i` (RETURN docker0/br-+, 80/443, ESTABLISHED; DROP el resto) y aplicado `Before=docker.service` (con `After=` quedan puertos abiertos segundos en cada arranque). Ante la duda, cerrar. Ver [[Aprendizajes/2026-09-28 Firewall DOCKER-USER que falla en cerrado]].
- 2026-09-28 (`infra/server/`): `ufw limit 22` y fail2ban afectan a Coolify, que entra por SSH desde redes Docker (10.0.0.0/8): permitirlas antes del limit y en `ignoreip`. Ver [[Aprendizajes/2026-09-28 Coolify con SSH, ufw y fail2ban]].
- 2026-09-28 (`infra/server/`): restaurar `pg_dumpall --clean` con apps conectadas mezcla datos: pararlas antes. Un script que usa archivos hermanos debe comprobar que existen antes de cambios irreversibles. Ver [[Aprendizajes/2026-09-28 Backups y restauración de Postgres]].
