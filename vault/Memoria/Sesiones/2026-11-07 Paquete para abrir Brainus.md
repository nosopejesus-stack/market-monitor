---
fecha: 2026-11-07
tipo: sesion
con: Claude Code (nube, desde iOS)
tags: [memoria, sesion, brainus]
---

# Sesión del 2026-11-07: paquete para abrir Brainus

## Qué pidió el dueño
Un resumen y que Brainus quedara abierta, o lista para abrirla en su PC.

## Qué se hizo
- Su PC no estaba conectado a la sesión (Remote Control), así que no se pudo abrir directamente.
- Se preparó **Brainus.zip** (65 archivos, 23 MB) con:
  - `1 - INSTALAR BRAINUS.bat`, que instala todo;
  - `2 - ABRIR BRAINUS.bat`, que la abre en el navegador;
  - `LEEME - EMPIEZA AQUI.txt`, con los tres pasos;
  - la red con sus pesos y esta bóveda.
- Se corrigieron dos fallos de Windows antes de entregarlo: el `config.json` con BOM y el servicio de Ollama sin arrancar.
- Se probó el ZIP en una carpeta limpia: memoria, búsqueda, 23 tests y generación correctos.

## Pendiente
- Primera instalación real en Windows: el instalador no se ha podido probar en un Windows.

Relacionado: [[Brainus - Plan]], [[Brainus - Red neuronal]], [[2026-11-06 Instalación, CS336 y creación de Brainus]].
