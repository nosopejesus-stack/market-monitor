#!/bin/bash
# Crea (o actualiza) un usuario y una base de datos por servicio.
# Idempotente: se puede re-ejecutar para rotar contraseñas tras cambiar .env:
#   docker compose exec postgres bash /docker-entrypoint-initdb.d/10-init-databases.sh
set -euo pipefail
PSQL=(psql -v ON_ERROR_STOP=1 -U postgres)

ensure() {  # usuario contraseña
  "${PSQL[@]}" -v u="$1" -v pw="$2" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN', :'u') WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'u')\gexec
ALTER ROLE :"u" WITH LOGIN NOSUPERUSER PASSWORD :'pw';
SELECT format('CREATE DATABASE %I OWNER %I', :'u', :'u') WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'u')\gexec
SQL
}
ensure n8n "$N8N_DB_PASSWORD"
ensure chatwoot "$CHATWOOT_DB_PASSWORD"
ensure umami "$UMAMI_DB_PASSWORD"

# Extensiones que piden las migraciones de Chatwoot, creadas por postgres
# (así el usuario chatwoot no necesita SUPERUSER).
"${PSQL[@]}" -d chatwoot <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SQL
"${PSQL[@]}" -d postgres -c "SELECT 1" >/dev/null
echo "[init-databases] usuarios y bases de datos listos"
