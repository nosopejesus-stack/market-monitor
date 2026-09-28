#!/usr/bin/env bash
# Docker publica puertos saltándose ufw. Esta regla, en la cadena DOCKER-USER,
# deja entrar desde la interfaz pública SOLO a los puertos 80 y 443 de los
# contenedores (el proxy de Coolify). Todo lo demás (panel 8000, 6001, 6002,
# y cualquier puerto publicado por error) queda cerrado hacia internet.
set -euo pipefail
IFACE="${PUBLIC_IFACE:-$(ip -o route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')}"
[ -n "$IFACE" ] || { echo "No se detectó la interfaz pública"; exit 1; }

apply() {  # iptables | ip6tables
  local ipt="$1"
  command -v "$ipt" >/dev/null || return 0
  "$ipt" -N DOCKER-USER 2>/dev/null || true
  "$ipt" -F DOCKER-USER
  "$ipt" -A DOCKER-USER -i "$IFACE" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
  "$ipt" -A DOCKER-USER -i "$IFACE" -p tcp -m conntrack --ctorigdstport 80 -j RETURN
  "$ipt" -A DOCKER-USER -i "$IFACE" -p tcp -m conntrack --ctorigdstport 443 -j RETURN
  "$ipt" -A DOCKER-USER -i "$IFACE" -p udp -m conntrack --ctorigdstport 443 -j RETURN
  "$ipt" -A DOCKER-USER -i "$IFACE" -j DROP
  "$ipt" -A DOCKER-USER -j RETURN
}
apply iptables
apply ip6tables
echo "DOCKER-USER: solo 80/443 abiertos en $IFACE"
