#!/bin/bash
# Crea una base de datos y un usuario por servicio (solo en el primer arranque).
set -euo pipefail
create() {
  psql -v ON_ERROR_STOP=1 -U postgres <<SQL
CREATE USER $1 WITH PASSWORD '$2';
CREATE DATABASE $1 OWNER $1;
SQL
}
create n8n "$N8N_DB_PASSWORD"
create chatwoot "$CHATWOOT_DB_PASSWORD"
create umami "$UMAMI_DB_PASSWORD"
# Chatwoot necesita pgvector y crear extensiones
psql -v ON_ERROR_STOP=1 -U postgres -d chatwoot -c "CREATE EXTENSION IF NOT EXISTS vector; ALTER USER chatwoot WITH SUPERUSER;"
