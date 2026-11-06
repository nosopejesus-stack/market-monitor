# Aprendizaje: 3 videos sobre IA y Claude Code

Resumen de tres TikToks y de los recursos que recomiendan, con lo que quedó instalado en este repo.

---

## Video 1 — @gonzalo_lopezg: "Claude ya usa cualquier app de tu ordenador"

**Idea:** Claude puede manejar cualquier aplicación del ordenador (hoja de cálculo, calculadora,
visor de PDF) mientras tú sigues trabajando, sin conexiones ni MCPs, y con varias sesiones a la
vez. La herramienta es **[Agent Desktop, de Vercel Labs](https://github.com/vercel-labs/agent-desktop)**
(open source, Apache-2.0, más de 5.000 estrellas). En vez de mirar capturas, lee el *árbol de
accesibilidad* del sistema operativo: devuelve cada botón o campo con una referencia (`ref`) que
Claude puede pulsar o rellenar. Funciona en macOS, Windows y Linux.

**Demo:** tres Claude trabajan a la vez, cada uno con su propio cursor:
- Claude 1 escribe el resumen.
- Claude 2 rellena una tabla de facturas (proveedor, fecha, nº de factura, total) a partir de PDFs.
- Claude 3 suma los totales con la calculadora.

**Lección:** "lo que haces a mano ya lo puede hacer". Pide a Claude un prompt que cubra:
1. Tu trabajo
2. Tus apps
3. Qué delegar

**Lo que monté y probé aquí (funciona):**
- `npm install -g agent-desktop` (versión 1.2.0) y sus skills en `.claude/skills/agent-desktop`
  y `.claude/skills/agent-desktop-linux`.
- Como el contenedor no tiene pantalla, creé un escritorio virtual:
  [`tools/agent-desktop/desk.sh`](../tools/agent-desktop/desk.sh). Usa Xvfb, Openbox y el bus de
  accesibilidad AT-SPI.
- Demo [`tools/agent-desktop/calc_demo.py`](../tools/agent-desktop/calc_demo.py): Claude abre la
  calculadora, pulsa `180+96+242=` botón a botón y lee el resultado, **518**
  ([captura](demo-calculadora.png)).

```bash
# Requisitos (Ubuntu 24.04): apt-get install -y xvfb dbus-x11 at-spi2-core openbox gnome-calculator
tools/agent-desktop/desk.sh "openbox & gnome-calculator & sleep 4; python3 tools/agent-desktop/calc_demo.py '180+96+242='"
```

**En tu propio ordenador** es más sencillo: `npm install -g agent-desktop`, luego
`agent-desktop permissions --guide` (en macOS concede el permiso de Accesibilidad), y le pides
a Claude Code que use la skill `agent-desktop` con tus apps reales: Excel, Numbers, PDFs...

- Si un servicio tiene conector o MCP (Gmail, Drive, Notion, Supabase, Twelve Data...), suele ser
  más rápido y fiable que el control por cursor. Agent Desktop queda para las apps sin API.
- Agent Desktop no automatiza páginas web; para eso está Playwright CLI (video 3).

---

## Video 2 — @midudev: curso gratis de Stanford para crear tu propio modelo de IA

**Recurso:** **Stanford CS336, Language Modeling from Scratch (primavera 2026)**, en el canal
de YouTube *Stanford Online*. Son 18 clases grabadas, de unos 80 minutos cada una, y gratis.
Según el video tienen **audio en español** (doblaje automático de YouTube). Se hace con Python y
Machine Learning. Busca "Stanford CS336".

**Las 4 fases de "tu IA":**
1. **Tokenizar:** convertir texto en tokens (BPE).
2. **Entrenar:** arquitectura Transformer, PyTorch, paralelismo en GPU, leyes de escala y datos.
3. **Inferencia:** generar texto de forma eficiente (KV cache, batching, cuantización).
4. **Post-entreno:** SFT, RLHF/DPO y RL con recompensas verificables, para que el modelo siga
   instrucciones.

**Primeras clases que aparecen en el video:**
- Lecture 1: Overview, Tokenization
- Lecture 2: PyTorch (einops)
- Lecture 3: Architectures
- Lecture 4: Attention Alternatives

**Cómo estudiarlo:** ve las clases en orden y haz las tareas del curso (tokenizador BPE →
Transformer → entrenamiento → alineamiento). La web del curso es cs336.stanford.edu. Necesitas
Python, PyTorch y, para entrenar, una GPU (Colab, o una GPU alquilada).

**Tarea 1 del curso, preparada:** descargué el repo oficial
[stanford-cs336/assignment1-basics](https://github.com/stanford-cs336/assignment1-basics) en la
sesión de Claude Code. Incluye el enunciado en PDF y tests: implementas tu tokenizador BPE, el
Transformer, el optimizador AdamW y el bucle de entrenamiento, y los tests te dicen si va bien.

```bash
git clone https://github.com/stanford-cs336/assignment1-basics.git && cd assignment1-basics
uv sync          # instala PyTorch, einops, tiktoken... (pip install uv si no lo tienes)
uv run pytest    # al principio todos fallan con NotImplementedError: es lo esperado
```

Los datos de entrenamiento (TinyStories y OpenWebText) se bajan de huggingface.co; los comandos
están en el README del repo. La tokenización y los tests corren en CPU; entrenar el modelo
completo pide GPU.

> No he podido ver las 18 horas de clase. Lo de arriba es el temario que se ve en el video y el
> programa público del curso.

---

## Video 3 — @revolutia.ai: "¿Tu app de Claude Code parece de 2006?" — 5 herramientas

Problema: todo lo que genera la IA se parece ("AI slop"). Solución: darle a Claude criterio de
diseño, referencias y una forma de comprobar lo que construye.

| # | Herramienta | Qué hace | Instalado en |
|---|---|---|---|
| 1 | **Taste Skill** ([Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)) | Framework frontend "anti-slop": reglas de diseño, componentes, fondos y un verificador que revisa la página en un navegador real | `.claude/skills/taste-skill` |
| 2 | **Guías de diseño web** ([vercel-labs/agent-skills → web-design-guidelines](https://github.com/vercel-labs/agent-skills)) | Revisa tu UI contra las Web Interface Guidelines de Vercel (accesibilidad, UX) y devuelve los hallazgos como `archivo:línea` | `.claude/skills/web-design-guidelines` |
| 3 | **Awesome Design** ([VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)) | 84 archivos DESIGN.md con el sistema de diseño de marcas como Stripe, Linear, Vercel o Apple. Copias uno al proyecto y Claude sigue su paleta, tipografía y estructura | `.claude/skills/awesome-design-md` |
| 4 | **Image to Code** ([OneWave-AI/claude-skills → screenshot-to-code](https://github.com/OneWave-AI/claude-skills)) | Pasas una captura o un mockup y lo convierte en código (React + Tailwind por defecto); después compara el resultado con la imagen | `.claude/skills/screenshot-to-code` |
| 5 | **Playwright CLI** ([microsoft/playwright-cli](https://github.com/microsoft/playwright-cli)) | `playwright-cli open localhost` abre el navegador, interactúa con tu web, hace capturas y comprueba lo que se ha construido | CLI global `playwright-cli` + `.claude/skills/playwright-cli` |

### Flujo recomendado para montar un proyecto web

1. **Estilo:** elige una marca de `awesome-design-md/design-md/` y cópiala como `DESIGN.md`.
   Para un monitor de mercados encajan `stripe`, `coinbase`, `kraken`, `revolut`, `linear.app`
   o `vercel`.
2. **Construir:** pide a Claude la página. La skill **taste-skill** se activa sola al diseñar
   landings y webs. Si tienes un mockup, pásalo como imagen y usa **screenshot-to-code**.
3. **Verificar:** Claude abre la app con **playwright-cli**, la recorre y hace capturas.
4. **Auditar:** pide "revisa mi UI" y se activa **web-design-guidelines**.

---

## Estado de la instalación

- ✅ Skills copiadas en `.claude/skills/`. Antes de copiarlas revisé el contenido: son Markdown,
  referencias y scripts que automatizan el navegador sobre páginas locales.
- ✅ `@playwright/cli` 0.1.23 instalado globalmente y probado contra una página local.
- ✅ `agent-desktop` 1.2.0 instalado y probado en un escritorio virtual: la demo de la
  calculadora funciona.
- ✅ Transcripción completa del audio de los 3 videos en
  [`transcripciones.txt`](transcripciones.txt), hecha con Whisper en local.
- ✅ Entorno cloud **market-monitor** creado: permite descargar de Hugging Face (modelos y datasets)
  y su script de arranque instala Playwright CLI.
- ⏳ Tarea 1 de CS336: código descargado. Instalar sus dependencias (`uv sync`) necesita tu
  autorización.

## Siguiente paso: bóveda de Obsidian y Mi IA

Todo lo aprendido (los 3 videos, las 17 clases de CS336 y la memoria) está ahora en la bóveda de Obsidian `vault/`, y `mi-ia/` es el asistente que la usa como memoria. Empieza por `vault/00 - Inicio.md` y `mi-ia/README.md`.
