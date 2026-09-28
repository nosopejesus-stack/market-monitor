#!/usr/bin/env bash
# Copia de seguridad diaria de las bases de datos del stack (n8n, Chatwoot, Umami)
# y de la configuración de Coolify (su base de datos y su .env con APP_KEY).
# Guarda un .sql.gz en BACKUP_DIR y borra los de más de KEEP_DAYS días.
# Complementa (no sustituye) los backups del proveedor, que guardan copia FUERA del servidor.
set -euo pipefail
BACKUP_DIR="${BACKUP_DIR:-/var/backups/stack}"
KEEP_DAYS="${KEEP_DAYS:-14}"
umask 077
if [ -n "${POSTGRES_CONTAINER:-}" ]; then
  PG="$POSTGRES_CONTAINER"
else
  # El Postgres del stack es el que usa la imagen construida desde infra/postgres
  mapfile -t found < <(docker ps --filter ancestor=local/postgres-pgvector:17 --format '{{.Names}}')
  if [ "${#found[@]}" -ne 1 ]; then
    echo "Encontrados ${#found[@]} contenedores de Postgres del stack (${found[*]:-ninguno}); define POSTGRES_CONTAINER."
    exit 1
  fi
  PG="${found[0]}"
fi
mkdir -p "$BACKUP_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"
out="$BACKUP_DIR/stack-$stamp.sql.gz"
docker exec "$PG" pg_dumpall -U postgres --clean --if-exists | gzip -9 > "$out.tmp"
gzip -t "$out.tmp" && [ "$(stat -c %s "$out.tmp")" -gt 1024 ] || { rm -f "$out.tmp"; echo "Backup vacío o corrupto"; exit 1; }
mv "$out.tmp" "$out"

# Configuración de Coolify (si está instalado en este servidor)
if docker ps --format '{{.Names}}' | grep -qx coolify-db; then
  docker exec coolify-db pg_dump -U coolify coolify | gzip -9 > "$BACKUP_DIR/coolify-$stamp.sql.gz"
  [ -f /data/coolify/source/.env ] && cp /data/coolify/source/.env "$BACKUP_DIR/coolify-env-$stamp"
fi

find "$BACKUP_DIR" \( -name 'stack-*.sql.gz' -o -name 'coolify-*' \) -mtime +"$KEEP_DAYS" -delete
echo "Backup OK: $out ($(du -h "$out" | cut -f1))"
# Restaurar: PARA antes n8n, chatwoot y umami; luego
#   gunzip -c FICHERO.sql.gz | docker exec -i <postgres> psql -U postgres
# y vuelve a arrancarlos (ver GUIA.md, "Copias de seguridad").
