#!/usr/bin/env bash
# Genera infra/.env con contraseñas aleatorias. No sobrescribe uno existente.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then echo ".env ya existe, no se toca."; exit 0; fi
r() { openssl rand -hex "${1:-24}"; }
cp .env.example .env
sed -i \
  -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(r)|" \
  -e "s|^N8N_DB_PASSWORD=.*|N8N_DB_PASSWORD=$(r)|" \
  -e "s|^CHATWOOT_DB_PASSWORD=.*|CHATWOOT_DB_PASSWORD=$(r)|" \
  -e "s|^UMAMI_DB_PASSWORD=.*|UMAMI_DB_PASSWORD=$(r)|" \
  -e "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$(r)|" \
  -e "s|^N8N_ENCRYPTION_KEY=.*|N8N_ENCRYPTION_KEY=$(r 32)|" \
  -e "s|^CHATWOOT_SECRET_KEY_BASE=.*|CHATWOOT_SECRET_KEY_BASE=$(r 64)|" \
  -e "s|^UMAMI_APP_SECRET=.*|UMAMI_APP_SECRET=$(r 32)|" \
  .env
chmod 600 .env
echo "Creado infra/.env (guárdalo en un gestor de contraseñas; NO lo subas a git)."
