# Guía de despliegue seguro (de cero a funcionando)

Tiempo estimado: 1 hora. Solo tienes que copiar y pegar comandos.
Lo que está marcado con 🔐 lo haces tú: son cuentas, pagos o claves, que nadie más debe crear.

## La opción elegida y por qué

| Decisión | Elección | Por qué |
|---|---|---|
| Proveedor | **Hetzner Cloud**, centro de datos en Alemania o Finlandia | UE (RGPD), buena relación precio/rendimiento, backups automáticos integrados |
| Servidor | **Ubuntu 24.04**, 4 vCPU, **16 GB RAM**, 160 GB disco, x86 | Chatwoot + n8n + Postgres usan unos 4 GB; el resto queda para Ollama (modelos de 3B) y ComfyUI en CPU |
| Acceso al servidor | Solo con **llave SSH**, sin contraseñas | Los ataques de contraseñas dejan de funcionar |
| Abierto a internet | Solo **80 y 443** (web con HTTPS) y 22 (SSH, con límite de intentos + fail2ban) | Todo lo demás queda cerrado, también los puertos de Docker |
| Panel de Coolify | **Privado**, solo por túnel SSH | El panel que controla todo no es visible desde internet |
| Públicos (con HTTPS) | n8n, Chatwoot, Umami | Necesitan recibir webhooks, chats y visitas |
| Privados | Ollama, ComfyUI, Postgres, Redis | No tienen login propio o no lo necesitan fuera |
| Copias de seguridad | Diarias en el servidor (14 días) **+** Backups de Hetzner (fuera del servidor) | Si se rompe una base de datos o el servidor entero, se recupera |
| Actualizaciones | Parches de seguridad del sistema automáticos | Sin mantenimiento manual |

Sin GPU, Ollama va bien con modelos pequeños (3B) y ComfyUI tarda varios minutos por imagen.
Si necesitas imágenes rápidas, más adelante se añade un servidor con GPU (ver `docker-compose.gpu.yml`).

---

## Paso 1 🔐 — Crear tu llave SSH (en tu ordenador, una vez)
Windows (PowerShell), macOS o Linux:
```bash
ssh-keygen -t ed25519 -C "servidor-stack"
```
Pulsa Enter en todo y pon una frase de paso. Tu llave pública está en `~/.ssh/id_ed25519.pub`.

## Paso 2 🔐 — Contratar el servidor
1. Crea cuenta en https://console.hetzner.cloud y un proyecto nuevo.
2. **Add Server**:
   - Location: Falkenstein / Nuremberg / Helsinki
   - Image: **Ubuntu 24.04**
   - Type: **Shared vCPU x86, 4 vCPU / 16 GB RAM** (consulta el precio actual en la web)
   - Networking: IPv4 + IPv6
   - **SSH keys: pega el contenido de `~/.ssh/id_ed25519.pub`** (imprescindible)
   - **Backups: actívalo** (copia diaria fuera del servidor, cuesta un 20 % extra)
3. Apunta la IP del servidor.

## Paso 3 — Preparar el servidor (un comando)
Desde tu ordenador:
```bash
ssh root@IP_DEL_SERVIDOR
```
Ya dentro del servidor (cambia `ana` por el usuario que quieras):
```bash
git clone --depth 1 -b claude/tender-cannon-ui4ixl https://github.com/nosopejesus-stack/market-monitor.git /opt/stack-repo
ADMIN_USER=ana bash /opt/stack-repo/infra/server/bootstrap.sh
```
Si el repositorio es privado, GitHub te pedirá acceso: usa un *token* de solo lectura, o copia la
carpeta `infra/server` al servidor con `scp -r infra/server root@IP:/opt/`.

Tarda unos 5-10 minutos. Al terminar:
- **Sin cerrar esa ventana**, abre otra terminal y comprueba: `ssh ana@IP_DEL_SERVIDOR`
- 🔐 Crea la contraseña de sudo de tu usuario (desde la sesión de root): `passwd ana`

## Paso 4 🔐 — Abrir el panel de Coolify (privado)
En tu ordenador, deja esto abierto mientras usas el panel:
```bash
ssh -N -L 8000:localhost:8000 -L 6001:localhost:6001 -L 6002:localhost:6002 ana@IP_DEL_SERVIDOR
```
Abre http://localhost:8000 y **crea tu cuenta de administrador en ese momento**.
Después, en tu perfil, activa **2FA** (autenticación en dos pasos).

## Paso 5 🔐 — Dominios
En tu proveedor de dominio crea 3 registros **A** que apunten a la IP del servidor:

| Nombre | Para |
|---|---|
| `n8n.tudominio.com` | n8n |
| `chat.tudominio.com` | Chatwoot |
| `stats.tudominio.com` | Umami |

(Si no tienes dominio, cualquier registrador vale: unos 10 €/año.)

## Paso 6 — Desplegar el stack en Coolify
1. En Coolify: **Projects → + Add → Production → + New Resource**.
2. Elige **Public/Private Repository (GitHub)**, este repositorio, rama `main` (o `claude/tender-cannon-ui4ixl`).
3. **Build Pack: Docker Compose**, *Docker Compose Location*: `/infra/docker-compose.yml`.
4. **Environment Variables → Developer view**: pega el `.env` generado en tu ordenador con
   `infra/scripts/generate-env.sh`, y cambia estas líneas:
   ```
   N8N_HOST=n8n.tudominio.com
   N8N_URL=https://n8n.tudominio.com/
   N8N_PROTOCOL=https
   N8N_PROXY_HOPS=1
   N8N_SECURE_COOKIE=true
   CHATWOOT_URL=https://chat.tudominio.com
   ```
   🔐 Guarda ese `.env` en tu gestor de contraseñas. **Nunca** cambies después `N8N_ENCRYPTION_KEY`.
5. En la lista de servicios, pon dominio **solo** a estos (con el puerto interno):

   | Servicio | Domains |
   |---|---|
   | n8n | `https://n8n.tudominio.com:5678` |
   | chatwoot-web | `https://chat.tudominio.com:3000` |
   | umami | `https://stats.tudominio.com:3000` |
   | ollama, comfyui, postgres, redis, chatwoot-worker | **sin dominio** |

6. **Deploy**. La primera vez tarda 15-25 min (construye ComfyUI y descarga imágenes).

## Paso 7 🔐 — Reclamar los paneles AL MOMENTO
Nada más terminar el despliegue, en este orden:
1. **n8n** → https://n8n.tudominio.com → crea tu cuenta → *Settings → Personal → 2FA*.
2. **Chatwoot** → https://chat.tudominio.com → crea tu cuenta → activa 2FA en el perfil.
3. **Umami** → https://stats.tudominio.com → entra con `admin` / `umami` y **cámbiala ya**.

## Paso 8 🔐 — Conectar Claude con n8n
1. En n8n: **Settings → Instance-level MCP → activar**, copia *Server URL* y el token.
2. En Claude (claude.ai): **Settings → Connectors → Add custom connector** con esa URL y el token.
   En Claude Code: `claude mcp add --transport http n8n https://n8n.tudominio.com/mcp-server/http --header "Authorization: Bearer TU_TOKEN"`

Desde ese momento puedo crear y ejecutar flujos en n8n, y a través de ellos usar Chatwoot, Ollama, Umami y ComfyUI.

## Paso 9 — Modelos de IA y comprobación
En el servidor (`ssh ana@IP`):
```bash
# Descargar un modelo para Ollama (el nombre del contenedor lo ves con: docker ps)
docker exec $(docker ps --format '{{.Names}}' | grep -m1 '^ollama') ollama pull llama3.2:3b

# Comprobar los servicios públicos
N8N_BASE=https://n8n.tudominio.com CHATWOOT_BASE=https://chat.tudominio.com \
UMAMI_BASE=https://stats.tudominio.com bash /opt/stack-repo/infra/scripts/smoke-test.sh
```

## Uso diario de lo privado (túnel SSH)
```bash
ssh -N -L 8000:localhost:8000 -L 6001:localhost:6001 -L 6002:localhost:6002 -L 8188:localhost:8188 ana@IP_DEL_SERVIDOR
```
Coolify en http://localhost:8000 y ComfyUI en http://localhost:8188.

## Copias de seguridad
- Automáticas cada noche a las 03:30 en `/var/backups/stack/` (se guardan 14 días).
- Probar ahora: `sudo systemctl start stack-backup && ls -lh /var/backups/stack/`
- Restaurar: `gunzip -c FICHERO.sql.gz | docker exec -i <contenedor-postgres> psql -U postgres`
  (salen 2 errores sobre el rol `postgres`: son normales).
- Además, los **Backups de Hetzner** (paso 2) guardan el servidor entero fuera de él.

## Resumen de seguridad
- ✅ Sin contraseñas por SSH; root solo con llave (Coolify lo necesita); fail2ban
- ✅ Firewall: solo 22/80/443; los puertos de Docker también cerrados (`docker-user-firewall`)
- ✅ Panel de Coolify, Ollama y ComfyUI no accesibles desde internet
- ✅ HTTPS automático (Let's Encrypt, vía Coolify)
- ✅ 2FA en Coolify, n8n y Chatwoot
- ✅ Contraseñas aleatorias únicas por servicio; usuarios de BD sin privilegios de superusuario
- ✅ Parches de seguridad automáticos; backups diarios dentro y fuera del servidor
