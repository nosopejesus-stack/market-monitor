#!/usr/bin/env bash
# Copia de seguridad diaria de TODAS las bases de datos (n8n, Chatwoot, Umami).
# Guarda un .sql.gz en BACKUP_DIR y borra los de más de KEEP_DAYS días.
# Complementa (no sustituye) los backups del proveedor, que guardan copia FUERA del servidor.
set -euo pipefail
BACKUP_DIR="${BACKUP_DIR:-/var/backups/stack}"
KEEP_DAYS="${KEEP_DAYS:-14}"
umask 077
PG="${POSTGRES_CONTAINER:-$(docker ps --format '{{.Names}}' | grep -E '(^|[-_])postgres([-_]|$)' | head -1)}"
[ -n "$PG" ] || { echo "No encuentro el contenedor de Postgres (define POSTGRES_CONTAINER)"; exit 1; }
mkdir -p "$BACKUP_DIR"
out="$BACKUP_DIR/stack-$(date +%Y%m%d-%H%M%S).sql.gz"
docker exec "$PG" pg_dumpall -U postgres --clean --if-exists | gzip -9 > "$out.tmp"
gzip -t "$out.tmp" && [ "$(stat -c %s "$out.tmp")" -gt 1024 ] || { rm -f "$out.tmp"; echo "Backup vacío o corrupto"; exit 1; }
mv "$out.tmp" "$out"
find "$BACKUP_DIR" -name 'stack-*.sql.gz' -mtime +"$KEEP_DAYS" -delete
echo "Backup OK: $out ($(du -h "$out" | cut -f1))"
# Restaurar:  gunzip -c FICHERO.sql.gz | docker exec -i <postgres> psql -U postgres
