#!/usr/bin/env bash
# Prepara un servidor Ubuntu 24.04 NUEVO de forma segura e instala Coolify.
# Ejecutar como root, una sola vez:
#   curl -fsSL https://raw.githubusercontent.com/<usuario>/<repo>/<rama>/infra/server/bootstrap.sh -o bootstrap.sh
#   ADMIN_USER=tunombre bash bootstrap.sh
#
# Qué hace:
#   1. Actualiza el sistema y activa las actualizaciones de seguridad automáticas
#   2. Crea un usuario administrador (sudo) con TU llave SSH
#   3. SSH solo con llave: sin contraseñas; root solo con llave (Coolify lo necesita)
#   4. Firewall: entra solo SSH (22), HTTP (80) y HTTPS (443)
#   5. Firewall para Docker: los contenedores solo son accesibles desde fuera por 80/443
#      (el panel de Coolify, puerto 8000, queda privado: se usa con túnel SSH)
#   6. Backup diario de las bases de datos (03:30, se guardan 14 días)
#   7. fail2ban contra ataques de fuerza bruta a SSH
#   8. Swap, zona horaria e instalación de Coolify (script oficial)
set -euo pipefail

ADMIN_USER="${ADMIN_USER:?Define ADMIN_USER, p. ej. ADMIN_USER=ana bash bootstrap.sh}"
TIMEZONE="${TIMEZONE:-Europe/Madrid}"
SWAP_GB="${SWAP_GB:-4}"
INSTALL_COOLIFY="${INSTALL_COOLIFY:-1}"
DRY_RUN="${DRY_RUN:-0}"
HERE="$(cd "$(dirname "$0")" && pwd)"

run() { if [ "$DRY_RUN" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }
log() { printf '\n==> %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta como root."; exit 1; }
. /etc/os-release
[ "${ID:-}" = ubuntu ] || { echo "Pensado para Ubuntu 24.04 (detectado: ${PRETTY_NAME:-?})."; exit 1; }
[[ "$ADMIN_USER" =~ ^[a-z][a-z0-9_-]{1,31}$ ]] || { echo "ADMIN_USER no válido."; exit 1; }

# Seguridad anti-bloqueo: sin llave SSH de root no se desactivan las contraseñas
if ! grep -qsE '^(ssh-(ed25519|rsa)|ecdsa-sha2|sk-)' /root/.ssh/authorized_keys; then
  echo "No hay ninguna llave SSH en /root/.ssh/authorized_keys."
  echo "Crea el servidor con tu llave SSH (panel del proveedor) y vuelve a ejecutar."
  exit 1
fi

log "1. Actualizando el sistema"
export DEBIAN_FRONTEND=noninteractive
run apt-get update -q
run apt-get -y -q -o Dpkg::Options::=--force-confold upgrade
run apt-get -y -q install ufw fail2ban unattended-upgrades curl ca-certificates iptables
run timedatectl set-timezone "$TIMEZONE"
if [ "$DRY_RUN" = 1 ]; then echo "[dry-run] escribir /etc/apt/apt.conf.d/20auto-upgrades"; else
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
CONF
fi

log "2. Usuario administrador: $ADMIN_USER"
if ! id "$ADMIN_USER" >/dev/null 2>&1; then
  run adduser --disabled-password --gecos "" "$ADMIN_USER"
fi
run usermod -aG sudo "$ADMIN_USER"
run install -d -m 700 -o "$ADMIN_USER" -g "$ADMIN_USER" "/home/$ADMIN_USER/.ssh"
run install -m 600 -o "$ADMIN_USER" -g "$ADMIN_USER" /root/.ssh/authorized_keys "/home/$ADMIN_USER/.ssh/authorized_keys"
echo "   (sudo pedirá contraseña: créala con 'passwd $ADMIN_USER' cuando termine)"

log "3. SSH solo con llave"
SSHD_DROPIN=/etc/ssh/sshd_config.d/99-hardening.conf
if [ "$DRY_RUN" = 1 ]; then echo "[dry-run] escribir $SSHD_DROPIN"; else
cat > "$SSHD_DROPIN" <<'CONF'
# Endurecimiento (infra/server/bootstrap.sh)
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitEmptyPasswords no
# Coolify gestiona el servidor como root por SSH con su propia llave
PermitRootLogin prohibit-password
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
AllowAgentForwarding no
CONF
fi
run sshd -t
run systemctl reload ssh

log "4. Firewall del sistema (ufw)"
run ufw default deny incoming
run ufw default allow outgoing
run ufw limit 22/tcp comment 'SSH'
run ufw allow 80/tcp comment 'HTTP'
run ufw allow 443/tcp comment 'HTTPS'
run ufw allow 443/udp comment 'HTTP/3'
run ufw --force enable

log "5. Firewall para contenedores Docker y backups diarios"
run install -m 755 "$HERE/docker-user-firewall.sh" /usr/local/sbin/docker-user-firewall.sh
run install -m 644 "$HERE/docker-user-firewall.service" /etc/systemd/system/docker-user-firewall.service
run systemctl daemon-reload
run systemctl enable docker-user-firewall.service

run install -m 750 "$HERE/backup.sh" /usr/local/sbin/stack-backup.sh
run install -m 644 "$HERE/stack-backup.service" /etc/systemd/system/stack-backup.service
run install -m 644 "$HERE/stack-backup.timer" /etc/systemd/system/stack-backup.timer
run systemctl daemon-reload
run systemctl enable stack-backup.timer

log "6. fail2ban"
if [ "$DRY_RUN" = 1 ]; then echo "[dry-run] escribir /etc/fail2ban/jail.d/sshd.local"; else
cat > /etc/fail2ban/jail.d/sshd.local <<'CONF'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
CONF
fi
run systemctl enable --now fail2ban
run systemctl restart fail2ban

log "7. Swap (${SWAP_GB} GB)"
if ! swapon --show | grep -q /swapfile; then
  run fallocate -l "${SWAP_GB}G" /swapfile
  run chmod 600 /swapfile
  run mkswap /swapfile
  run swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || run sh -c 'echo "/swapfile none swap sw 0 0" >> /etc/fstab'
fi

if [ "$INSTALL_COOLIFY" = 1 ]; then
  log "8. Instalando Coolify (script oficial)"
  if [ "$DRY_RUN" = 1 ]; then echo "[dry-run] curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash"; else
    curl -fsSL https://cdn.coollabs.io/coolify/install.sh -o /root/coolify-install.sh
    bash /root/coolify-install.sh
  fi
  run systemctl restart docker-user-firewall.service
fi

log "Listo"
cat <<MSG
Siguientes pasos (desde TU ordenador, no desde el servidor):
  1. Comprueba que entras con el nuevo usuario ANTES de cerrar esta sesión:
       ssh $ADMIN_USER@<IP>
     y crea su contraseña de sudo:  sudo passwd $ADMIN_USER   (desde root: passwd $ADMIN_USER)
  2. Abre el panel de Coolify por túnel SSH (no está abierto a internet):
       ssh -N -L 8000:localhost:8000 -L 6001:localhost:6001 -L 6002:localhost:6002 $ADMIN_USER@<IP>
     y en el navegador: http://localhost:8000  -> crea tu cuenta AL MOMENTO.
  3. Sigue infra/server/GUIA.md desde el paso 4.
MSG
