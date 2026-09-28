#!/usr/bin/env bash
# Comprueba que cada servicio responde por HTTP. Uso: scripts/smoke-test.sh [host]
H="${1:-localhost}"; fail=0
check() {  # nombre url patrón
  body=$(curl -s -m 10 "$2")
  if echo "$body" | grep -q "$3"; then echo "OK    $1  ($2)"; else echo "FALLA $1  ($2) -> ${body:0:120}"; fail=1; fi
}
check n8n      "http://$H:5678/healthz"            '"status":"ok"'
check chatwoot "http://$H:3000/api"                 'version'
check ollama   "http://$H:11434/api/version"        'version'
check umami    "http://$H:3001/api/heartbeat"       'ok'
check comfyui  "http://$H:8188/system_stats"        'comfyui_version\|python_version'
exit $fail
