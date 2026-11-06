---
fecha: 2026-11-06
tipo: sesion
con: Claude Code (nube, desde iOS)
tags: [memoria, sesion]
---

# Sesión del 2026-11-06: instalación, CS336 y creación de Brainus

## Qué pidió el dueño
1. Ver 3 TikToks, aprender de todo lo que recomiendan e instalar lo necesario para montar proyectos.
2. Cambiar de entorno si algo no se podía hacer (autorizado).
3. Aprender las clases de Stanford CS336 y guardarlas en Obsidian.
4. Crear **su propia IA**, con acceso a Obsidian, que aprenda de cada uso de Claude (lo bueno y lo malo) y que funcione de forma independiente en su PC.

## Qué se hizo
- 5 skills de diseño + Agent Desktop + Playwright CLI ([[Videos - Aprendizaje de los 3 TikToks]], [[Agent Desktop]]).
- Un entorno cloud nuevo, "market-monitor", con acceso a Hugging Face, YouTube y la web del curso.
- 17 notas de CS336 ([[CS336 - Índice]]).
- **Brainus** ([[Brainus - Plan]]):
  - asistente RAG sobre la bóveda;
  - reglas Hacer / No hacer;
  - feedback /bien y /mal;
  - **una red neuronal propia** (Transformer desde cero, preentrenado con Wikipedia en español y afinado con la bóveda).

## Lecciones
- Bien: entregar cosas funcionando y probadas; buscar otra vía cuando algo está bloqueado.
- Mal: un comando borró líneas sin querer; el modelo de prueba pequeño inventó un dato.
- Las reglas resultantes están en [[Reglas - Hacer]] y [[Reglas - No hacer]].

## Continuación (2026-11-06, tarde): nace Brainus
- El dueño eligió el nombre **Brainus** y pidió la IA "al 100 % como el curso", lo más potente posible, usable con o sin Claude y siempre con Obsidian.
- La red se reescribió **desde cero** (sin capas de PyTorch), con 23 tests contra PyTorch, y se entrenó en tres fases: 14M parámetros, 1,85 bits/byte ([[Brainus - Red neuronal]]).
- El instalador elige el cerebro de Ollama más potente según la RAM/GPU del PC ([[Brainus - Plan]]).
- Decisión: no se resolvió la tarea oficial de CS336, por la norma del curso para IAs; Brainus es un proyecto propio.
