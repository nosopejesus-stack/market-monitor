---
fecha: 2026-09-28
etiquetas: [seguridad, servidor, ssh, fail2ban]
origen: revisión del agente revisor sobre infra/server/bootstrap.sh
---
# Endurecimiento de SSH con drop-ins

- **Qué pasó:** el [[Agentes/Revisor|revisor]] detectó que la configuración de SSH de `bootstrap.sh` podía no aplicarse y que la combinación de límites podía dejar fuera al propio usuario.
- **Lección:**
  - `sshd` usa el **primer** valor que encuentra para cada opción. Un drop-in `99-*.conf` pierde frente a `50-cloud-init.conf`. (Qué valores trae exactamente ese archivo en la imagen de Hetzner: SIN VERIFICAR.)
  - `sshd -t` solo valida la sintaxis; no dice qué valor queda efectivo.
  - Un `MaxAuthTries` bajo junto con fail2ban bloquea a quien tiene varias llaves cargadas en el agente SSH (cada llave probada cuenta como intento).
- **Cómo aplicarla:**
  - Nombrar el drop-in `00-*.conf` en `/etc/ssh/sshd_config.d/`.
  - Validar el valor efectivo con `sshd -T | grep -i <opción>`.
  - Usar `MaxAuthTries 6` y, en el cliente, `IdentitiesOnly yes` (con `IdentityFile`) en `~/.ssh/config`.

Relacionado: [[Decisiones/2026-09-28 Despliegue seguro en Hetzner con Coolify]], [[Aprendizajes/2026-09-28 Coolify con SSH, ufw y fail2ban]]
