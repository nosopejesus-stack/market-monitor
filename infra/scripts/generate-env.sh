#!/usr/bin/env bash
# Genera infra/.env con contraseñas aleatorias. No sobrescribe uno existente.
# AVISO: si ya hay volúmenes creados, un .env nuevo NO cambia las contraseñas
# guardadas en Postgres ni la clave de cifrado de n8n (ver README, "Rotar secretos").
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
if [ -f .env ]; then echo ".env ya existe, no se toca."; exit 0; fi
r() { openssl rand -hex "${1:-24}"; }
pg=$(r); n8n_db=$(r); cw_db=$(r); um_db=$(r); redis=$(r)
n8n_key=$(r 32); cw_secret=$(r 64); um_secret=$(r 32)
sed \
  -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$pg|" \
  -e "s|^N8N_DB_PASSWORD=.*|N8N_DB_PASSWORD=$n8n_db|" \
  -e "s|^CHATWOOT_DB_PASSWORD=.*|CHATWOOT_DB_PASSWORD=$cw_db|" \
  -e "s|^UMAMI_DB_PASSWORD=.*|UMAMI_DB_PASSWORD=$um_db|" \
  -e "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$redis|" \
  -e "s|^N8N_ENCRYPTION_KEY=.*|N8N_ENCRYPTION_KEY=$n8n_key|" \
  -e "s|^CHATWOOT_SECRET_KEY_BASE=.*|CHATWOOT_SECRET_KEY_BASE=$cw_secret|" \
  -e "s|^UMAMI_APP_SECRET=.*|UMAMI_APP_SECRET=$um_secret|" \
  .env.example > .env.tmp
for k in POSTGRES_PASSWORD N8N_DB_PASSWORD CHATWOOT_DB_PASSWORD UMAMI_DB_PASSWORD REDIS_PASSWORD \
         N8N_ENCRYPTION_KEY CHATWOOT_SECRET_KEY_BASE UMAMI_APP_SECRET; do
  grep -qE "^$k=.+" .env.tmp || { rm -f .env.tmp; echo "Error: $k quedó vacío"; exit 1; }
done
mv .env.tmp .env
echo "Creado infra/.env (guárdalo en un gestor de contraseñas; NO lo subas a git)."
