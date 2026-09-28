---
fecha: 2026-09-28
etiquetas: [entorno, pruebas, iptables, docker]
origen: sesión de preparación de infra/server/
---
# Probar infra de servidor en el contenedor cloud

- **Qué pasó:** para validar `bootstrap.sh` y el firewall sin un servidor real se hicieron pruebas en el contenedor cloud de Claude.
- **Lección:**
  - `unshare -n` crea un network namespace aislado: sirve para probar reglas de iptables sin tocar la red del contenedor.
  - El comando `ip` no está instalado en el contenedor.
  - La imagen `ubuntu:24.04` no trae iptables ni sshd, y `apt` está bloqueado (sin red, ver [[Aprendizajes/2026-09-28 El contenedor cloud no tiene internet libre]]).
  - `dockerd` puede pararse entre turnos.
- **Cómo aplicarla:**
  - Probar iptables con `unshare -n bash -c '...'`.
  - Si Docker no responde, relanzar con `dockerd &` (ver [[Aprendizajes/2026-09-28 Docker en el contenedor cloud]]).
  - Lo que no se pueda probar aquí (sshd real, cloud-init, systemd en arranque) queda SIN VERIFICAR hasta el servidor real.

Relacionado: [[Decisiones/2026-09-28 Despliegue seguro en Hetzner con Coolify]]
