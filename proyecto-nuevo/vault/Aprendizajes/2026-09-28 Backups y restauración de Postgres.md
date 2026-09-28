---
fecha: 2026-09-28
etiquetas: [backup, postgres, bash, servidor]
origen: revisión del agente revisor y prueba de restauración de infra/server/backup.sh
---
# Backups y restauración de Postgres

- **Qué pasó:** se probó `backup.sh` y la restauración del volcado en un Postgres vacío: se recuperaron las 3 BDs completas, con 2 errores normales relacionados con el rol `postgres` (ya existe). Además, el revisor vio que `bootstrap.sh` usaba archivos hermanos sin comprobarlos antes.
- **Lección:**
  - Restaurar un `pg_dumpall --clean` con las apps conectadas mezcla datos.
  - Un script que usa archivos hermanos (p. ej. la unidad systemd o el script de firewall junto a `bootstrap.sh`) debe comprobar que existen **antes** de hacer cambios irreversibles; si no, deja el servidor a medio configurar.
  - Los errores de "role postgres already exists" al restaurar un `pg_dumpall` son esperables.
- **Cómo aplicarla:**
  - Antes de restaurar: parar n8n, Chatwoot, Umami (y cualquier app conectada); restaurar; volver a arrancar.
  - Al inicio de cada script: validar todas las dependencias (archivos, comandos) y salir antes de tocar nada.
  - Verificar backups restaurándolos de verdad, no solo comprobando que el archivo existe.

Relacionado: [[Decisiones/2026-09-28 Despliegue seguro en Hetzner con Coolify]]
