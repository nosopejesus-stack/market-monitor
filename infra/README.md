# infra — servicios que trabajan junto a Claude

| Servicio | Para qué | Puerto local | Cómo lo usa Claude |
|---|---|---|---|
| **n8n** | Automatizaciones | 5678 | Servidor MCP en `/mcp-server/http`: Claude ejecuta, crea y edita flujos |
| **Chatwoot** | Atención al cliente (web, WhatsApp, email…) | 3000 | Webhooks → n8n → respuesta con Ollama o Claude |
| **Ollama** | Modelos de IA locales y gratuitos | 11434 | API `/api/chat`, desde n8n o directamente |
| **Umami** | Analytics web (sin cookies) | 3001 | API de estadísticas, desde n8n |
| **ComfyUI** | Generación de imágenes | 8188 | API `/prompt`, desde n8n |
| **Coolify** | Panel que despliega y mantiene todo 24/7 | 8000 (en el servidor) | — |

Comparten un Postgres 17 (con pgvector) y Redis. Todo está en `docker-compose.yml`.

## 1. Probar en local (o en cualquier máquina con Docker)
```bash
cd infra
./scripts/generate-env.sh          # crea .env con contraseñas aleatorias (no se sube a git)
docker compose up -d               # la primera vez tarda: descarga imágenes y construye ComfyUI
./scripts/smoke-test.sh            # comprueba que los 5 servicios responden
```
Para descargar modelos de Ollama: `OLLAMA_MODELS="llama3.2:3b"` en `.env` y `docker compose --profile pull up ollama-pull`.

Los puertos solo escuchan en `127.0.0.1` (variable `BIND_ADDRESS`): no quedan abiertos a internet.

## 2. Siempre encendido: servidor + Coolify

> **Guía completa y segura paso a paso: [`server/GUIA.md`](server/GUIA.md)** (servidor, endurecimiento con `server/bootstrap.sh`, firewall, panel privado, dominios, 2FA, backups). El resumen de abajo es solo orientativo.
Este stack tiene que vivir en un servidor propio (el contenedor de Claude en la nube se borra al cerrar la sesión).

**Servidor recomendado:** Ubuntu 24.04, 4 vCPU, 16 GB RAM y 150 GB de disco. Sin GPU, Ollama usa modelos pequeños y ComfyUI va lento (minutos por imagen); con GPU NVIDIA, usa `docker-compose.gpu.yml`.

1. Instala Coolify en el servidor (script oficial):
   ```bash
   curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
   ```
   Abre `http://IP-DEL-SERVIDOR:8000` y crea tu cuenta.
2. En Coolify: **Projects → New → Resource → Docker Compose** desde este repositorio de GitHub,
   con ruta `infra/docker-compose.yml`.
3. En **Environment Variables** del recurso, pega el contenido de tu `.env`
   (generado con `scripts/generate-env.sh`) y cambia las URLs por tus dominios con https.
   Para HTTPS pon además `N8N_PROTOCOL=https`, `N8N_PROXY_HOPS=1` y `N8N_SECURE_COOKIE=true`.
4. Asigna un dominio a cada servicio **incluyendo el puerto interno** (si no, da error 502):
   `https://n8n.tudominio.com:5678`, `https://chat.tudominio.com:3000`,
   `https://umami.tudominio.com:3000`, `https://comfy.tudominio.com:8188`.
   **No** pongas dominio a Ollama: n8n lo usa por dentro en `http://ollama:11434`.
   A ComfyUI (no tiene login) ponle *Basic Auth* en Coolify o no lo publiques.
5. Despliega. Coolify gestiona los certificados HTTPS y reinicia los servicios si caen.
6. **Inmediatamente**, antes de compartir los dominios, crea las cuentas de administrador:
   n8n, Chatwoot (`/installation/onboarding`) y Coolify dan el control al primer visitante,
   y Umami arranca con `admin` / `umami`: cambia esa contraseña en cuanto entres.

Con GPU en Coolify: Coolify usa un único archivo compose, así que copia el bloque
`deploy.resources` de `docker-compose.gpu.yml` dentro de `docker-compose.yml`.

## 3. Conectar n8n con Claude (una sola vez)
1. Abre n8n y crea tu cuenta de administrador.
2. **Settings → Instance-level MCP**: activa el acceso y copia la *Server URL* y el token.
3. En Claude Code:
   ```bash
   claude mcp add --transport http n8n https://n8n.TU-DOMINIO.com/mcp-server/http \
     --header "Authorization: Bearer TU_TOKEN"
   ```
   o copia `claude/mcp.json.example` como `.mcp.json` en la raíz del repo y define `N8N_MCP_TOKEN`.
4. En Claude web (claude.ai): **Settings → Connectors → Add custom connector** con la misma URL.

Desde ese momento Claude puede crear y ejecutar flujos de n8n, y a través de ellos usar Chatwoot, Ollama, Umami y ComfyUI.

## Rotar secretos
Las contraseñas de las bases de datos se guardan en el volumen de Postgres la primera vez.
Si cambias `.env` (o pegas otro en Coolify) después del primer despliegue:
1. Cambia las contraseñas de BD en `.env` y aplica con
   `docker compose exec postgres bash /docker-entrypoint-initdb.d/10-init-databases.sh`.
2. **Nunca** cambies `N8N_ENCRYPTION_KEY`: n8n no arrancará y perderás sus credenciales guardadas.

## Notas
- `.env` contiene todas las contraseñas: guárdalo en un gestor de contraseñas y **nunca** lo subas a git.
- En producción fija versiones concretas (`N8N_VERSION`, `CHATWOOT_VERSION`…) en vez de `latest`.
- ComfyUI: los volúmenes `models` y `custom_nodes` conservan su contenido al actualizar la imagen.
- Copias de seguridad: en Coolify, activa los backups programados del volumen `postgres_data`.
