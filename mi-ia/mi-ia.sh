#!/usr/bin/env bash
# Abre Mi IA en el navegador (macOS / Linux).
cd "$(dirname "$0")"
( sleep 2; (command -v open >/dev/null && open http://localhost:8765) || xdg-open http://localhost:8765 ) >/dev/null 2>&1 &
python3 mi_ia.py web
