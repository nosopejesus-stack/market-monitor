#!/usr/bin/env bash
# Docker publica puertos saltándose ufw. Estas reglas, en la cadena DOCKER-USER,
# dejan llegar a los contenedores desde fuera SOLO por 80 y 443 (el proxy de
# Coolify). El panel (8000, 6001, 6002), Traefik (8080) y cualquier puerto
# publicado por error quedan cerrados hacia internet y hacia redes privadas.
# No depende de detectar la interfaz: lo que no viene de una red de Docker
# (docker0 / br-*) se cierra salvo 80/443. Ante la duda, cierra.
set -euo pipefail

apply() {  # iptables | ip6tables
  local ipt="$1"
  command -v "$ipt" >/dev/null || return 0
  "$ipt" -N DOCKER-USER 2>/dev/null || true
  "$ipt" -F DOCKER-USER
  "$ipt" -A DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  "$ipt" -A DOCKER-USER -i docker0 -j RETURN
  "$ipt" -A DOCKER-USER -i br-+ -j RETURN
  "$ipt" -A DOCKER-USER -p tcp -m conntrack --ctorigdstport 80 -j RETURN
  "$ipt" -A DOCKER-USER -p tcp -m conntrack --ctorigdstport 443 -j RETURN
  "$ipt" -A DOCKER-USER -p udp -m conntrack --ctorigdstport 443 -j RETURN
  "$ipt" -A DOCKER-USER -j DROP
}
apply iptables
apply ip6tables
echo "DOCKER-USER: contenedores accesibles desde fuera solo por 80/443"
