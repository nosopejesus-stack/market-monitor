---
tipo: herramienta
repo: https://github.com/vercel-labs/agent-desktop
licencia: Apache-2.0
tags: [herramientas, computer-use, automatizacion, vercel]
---

# Agent Desktop (Vercel Labs)

Le da a un agente IA **control de las apps de escritorio** (macOS, Windows, Linux) leyendo el **árbol de accesibilidad** del sistema, no capturas de pantalla.
- `snapshot` devuelve los elementos con una referencia (`ref`).
- `click`, `type` o `set-value` actúan sobre esa referencia.
- Después se vuelve a leer la pantalla para comprobar el resultado.

## Instalar en tu ordenador
```bash
npm install -g agent-desktop
agent-desktop status
agent-desktop permissions --guide   # macOS: dar permiso de Accesibilidad
```
Luego pídele a Claude Code: "usa agent-desktop para pasar las facturas de este PDF a Excel".

## Probado
En la sesión del 2026-11-06 Claude lo probó en un escritorio Linux virtual: abrió la calculadora, pulsó `180+96+242=` y leyó **518**.

## Límites
- No ve las apps que no exponen accesibilidad.
- No automatiza webs; para eso está Playwright.
- Las capturas y lecturas pueden contener datos privados.

Relacionado: [[Videos - Aprendizaje de los 3 TikToks]], [[Brainus - Plan]] (fase v5: que tu IA actúe).
