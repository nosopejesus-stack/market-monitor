---
fecha: 2026-09-28
estado: aceptada
---
# Despliegue seguro en Hetzner con Coolify

- **Contexto:** el stack de `infra/` ([[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]]) necesita un servidor 24/7 endurecido antes de exponer nada a internet.
- **Opciones consideradas:** VPS propio gestionado con Coolify (elegido). Proveedor: Hetzner Cloud en la UE.
- **Decisión:**
  - **Servidor:** Hetzner Cloud (UE), Ubuntu 24.04, 4 vCPU / 16 GB, con Coolify.
  - **Archivos en `infra/server/`:**
    - `bootstrap.sh`: endurecimiento del host (SSH, ufw, fail2ban...).
    - `docker-user-firewall.sh` + `docker-user-firewall.service`: cadena DOCKER-USER que solo deja pasar 80/443 hacia contenedores.
    - `backup.sh` + `stack-backup.service` + `stack-backup.timer`: copia diaria a las 03:30, 14 días de retención, incluye la BD de Coolify (`coolify-db`) y su `.env`.
    - `GUIA.md`: guía paso a paso para el usuario.
  - **Públicos con HTTPS:** n8n, Chatwoot, Umami.
  - **Privados:** panel de Coolify (por túnel SSH a 8000/6001/6002), Ollama, ComfyUI, Postgres, Redis.
  - **2FA** en Coolify, n8n y Chatwoot.
  - **Backups de Hetzner** activados además de los locales.
- **Consecuencias:**
  - Pendiente del usuario (no lo hacen los agentes, ver [[Aprendizajes/2026-09-28 Crear cuentas y credenciales es decisión del usuario]]): contratar el servidor, llave SSH, dominios, cuentas admin y token MCP de n8n.
  - Probado solo en simulación (contenedor y netns aislado), no en un Hetzner real: el comportamiento en el servidor real queda SIN VERIFICAR hasta el primer despliegue.
  - Reglas aprendidas al prepararlo:
    - [[Aprendizajes/2026-09-28 Endurecimiento de SSH con drop-ins]]
    - [[Aprendizajes/2026-09-28 Firewall DOCKER-USER que falla en cerrado]]
    - [[Aprendizajes/2026-09-28 Coolify con SSH, ufw y fail2ban]]
    - [[Aprendizajes/2026-09-28 Backups y restauración de Postgres]]
    - [[Aprendizajes/2026-09-28 Probar infra de servidor en el contenedor cloud]]
