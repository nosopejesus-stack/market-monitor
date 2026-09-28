---
fecha: 2026-09-28
etiquetas: [coolify, servidor, ssh, ufw, fail2ban]
origen: revisión del agente revisor sobre infra/server/
---
# Coolify con SSH, ufw y fail2ban

- **Qué pasó:** al endurecer el host se vio que Coolify gestiona el propio servidor entrando por SSH desde sus contenedores, y que el panel usa más puertos que el 8000.
- **Lección:**
  - `ufw limit 22` y fail2ban también afectan a Coolify, que entra por SSH al host desde redes Docker (10.0.0.0/8).
  - Coolify necesita root por SSH con llave: `PermitRootLogin prohibit-password` basta (no poner `no`).
  - En servicios docker-compose, el dominio se indica con el puerto interno del contenedor: `https://n8n.dominio.com:5678` (Coolify enruta 443 hacia ese puerto).
  - El panel de Coolify usa 8000 y además 6001 (tiempo real) y 6002 (terminal).
- **Cómo aplicarla:**
  - En ufw, permitir las redes Docker (10.0.0.0/8) al 22 **antes** de la regla `limit`; añadirlas a `ignoreip` de fail2ban.
  - Túnel SSH al panel con los tres puertos: `-L 8000:localhost:8000 -L 6001:localhost:6001 -L 6002:localhost:6002`.

Relacionado: [[Decisiones/2026-09-28 Despliegue seguro en Hetzner con Coolify]], [[Aprendizajes/2026-09-28 Endurecimiento de SSH con drop-ins]], [[Aprendizajes/2026-09-28 Init de Postgres, secretos y Coolify]]
