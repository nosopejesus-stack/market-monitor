---
fecha: 2026-09-28
etiquetas: [entorno, docker]
origen: stack infra (n8n, Chatwoot, Ollama, Umami, ComfyUI)
---
# Docker en el contenedor cloud

- **Qué pasó:** al probar el stack de `infra/` en el contenedor cloud de Claude:
  - `dockerd` no arranca solo.
  - Docker Hub responde 429 (límite de pulls anónimos).
  - ghcr.io descarga los blobs desde `pkg-containers.githubusercontent.com`, que está bloqueado.
  - Durante `docker build` los contenedores no pasan por el proxy: fallan `apt`, `git` y `pip` dentro del build.
  - Dominios bloqueados: `download.pytorch.org`, `registry.ollama.ai`, `huggingface.co`, `codeload.github.com`, `pkg-containers.githubusercontent.com`.
  - Funcionan: PyPI y `git clone` de github.com desde el host.
- **Lección:** Docker funciona en el contenedor, pero hay que sortear el proxy y los registros bloqueados.
- **Cómo aplicarla:**
  - Arrancar el daemon con `dockerd &`.
  - Descargar imágenes de Docker Hub por el mirror `mirror.gcr.io/<imagen>` y re-etiquetarlas con el nombre original.
  - Evitar ghcr.io: usar la imagen de Docker Hub si existe (p. ej. Umami: `umamisoftware/umami`).
  - Las imágenes con build que necesitan red (p. ej. ComfyUI) se validan fuera de Docker (instalando en el host con PyPI / git clone).
  - No se pueden descargar modelos (Ollama, Hugging Face, PyTorch) aquí: eso se prueba en el servidor.

Relacionado: [[Aprendizajes/2026-09-28 El contenedor cloud no tiene internet libre]], [[Decisiones/2026-09-28 Stack de servicios en infra con n8n como puerta de Claude]]
