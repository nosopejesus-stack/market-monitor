#!/usr/bin/env bash
# Comprueba que cada servicio responde. URLs base configurables por variable:
#   N8N_BASE=https://n8n.midominio.com scripts/smoke-test.sh
H="${HOST:-localhost}"; fail=0
N8N_BASE="${N8N_BASE:-http://$H:${N8N_PORT:-5678}}"
CHATWOOT_BASE="${CHATWOOT_BASE:-http://$H:${CHATWOOT_PORT:-3000}}"
OLLAMA_BASE="${OLLAMA_BASE:-http://$H:${OLLAMA_PORT:-11434}}"
UMAMI_BASE="${UMAMI_BASE:-http://$H:${UMAMI_PORT:-3001}}"
COMFYUI_BASE="${COMFYUI_BASE:-http://$H:${COMFYUI_PORT:-8188}}"
check() {  # nombre url patrón
  if body=$(curl -fsS -m 10 "$2" 2>&1) && echo "$body" | grep -q "$3"; then
    echo "OK    $1  ($2)"
  else
    echo "FALLA $1  ($2) -> ${body:0:120}"; fail=1
  fi
}
check n8n      "$N8N_BASE/healthz"           '"status":"ok"'
check chatwoot "$CHATWOOT_BASE/api"          '"version"'
check ollama   "$OLLAMA_BASE/api/version"    '"version"'
check umami    "$UMAMI_BASE/api/heartbeat"   '"ok":true'
check comfyui  "$COMFYUI_BASE/system_stats"  '"python_version"'
exit $fail
