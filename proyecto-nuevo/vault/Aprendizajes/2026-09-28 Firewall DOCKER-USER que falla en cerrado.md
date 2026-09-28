---
fecha: 2026-09-28
etiquetas: [seguridad, servidor, docker, iptables, firewall]
origen: revisión del agente revisor sobre infra/server/docker-user-firewall.sh
---
# Firewall DOCKER-USER que falla en cerrado

- **Qué pasó:** la primera versión del firewall detectaba la interfaz de red y, si fallaba, salía con error sin aplicar reglas; además se aplicaba después de arrancar Docker.
- **Lección:**
  - Un firewall que depende de detectar la interfaz y sale con error **falla en abierto**: los puertos publicados por Docker quedan accesibles (Docker se salta ufw).
  - Aplicar DOCKER-USER con `After=docker.service` deja puertos abiertos unos segundos en cada arranque.
  - Ante la duda, cerrar.
- **Cómo aplicarla:**
  - Reglas en DOCKER-USER **sin `-i`**: `RETURN` para tráfico de `docker0`/`br-+`, `RETURN` para 80/443, `RETURN` para `ESTABLISHED,RELATED`; `DROP` para el resto.
  - Unidad systemd con `Before=docker.service`: Docker conserva la cadena DOCKER-USER existente al arrancar.
  - Probarlo en un netns aislado (ver [[Aprendizajes/2026-09-28 Probar infra de servidor en el contenedor cloud]]).

Relacionado: [[Decisiones/2026-09-28 Despliegue seguro en Hetzner con Coolify]], [[Aprendizajes/2026-09-28 Seguridad de stacks en servidor]]
