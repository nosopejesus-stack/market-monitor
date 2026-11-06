---
tipo: proyecto
estado: v1 funcionando (búsqueda en memoria); falta conectar el modelo en tu ordenador
tags: [mi-ia, proyecto, rag, obsidian, ollama]
---

# Mi IA: plan y arquitectura

## Qué quieres
Tu propia IA funcionando, que **aprenda todo lo que Claude sabe de ti y de tus proyectos** y que tenga acceso a Obsidian como memoria.

## La verdad técnica (para no llevarse sorpresas)
- **Claude no se puede copiar.** Sus "conocimientos" están en sus pesos, que no son públicos. Lo que sí se transfiere es **lo que aprendemos juntos**: notas, decisiones, cursos resumidos y tus datos. Todo eso vive en esta bóveda.
- **Entrenar un modelo desde cero** (lo que enseña [[CS336 - Índice|CS336]]) es posible a escala pequeña. Un modelo de 100M parámetros con TinyStories entrena en horas con una GPU. Pero no se acercará a Claude: la frontera cuesta millones ([[Clase 09 - Leyes de escala]]).
- **El camino que funciona hoy:**

```
   Tú ──pregunta──▶ Mi IA (mi_ia.py)
                       │ 1. busca en tu bóveda (BM25)
                       ▼
               Bóveda de Obsidian (vault/) ◀── Claude y tú escribís notas
                       │ 2. fragmentos relevantes
                       ▼
               Modelo de lenguaje
               ├─ Ollama (local, gratis, privado): qwen3:8b, llama3.1:8b, gemma3...
               └─ API de Claude (de pago, más inteligente)
                       │ 3. respuesta citando [[notas]]
                       ▼
   Tú ◀── respuesta      y "/recordar ..." ──▶ nota nueva en Memoria/Recuerdos
```

Esto se llama **RAG** (generación aumentada con recuperación). Es justo la "memoria persistente en archivos" que usan los agentes ([[Clase 12 - Evaluación]]).

## Fases
1. **v1 (hecha):** bóveda + `mi-ia/mi_ia.py` (búsqueda BM25, chat y recordar). Probado aquí con el motor `ninguno`, que solo busca.
2. **v2 (en tu ordenador):** instalar Ollama y descargar un modelo para tener la IA completa en local. Pasos en `mi-ia/README.md`.
3. **v3:** búsqueda semántica con *embeddings* (por ejemplo `nomic-embed-text` en Ollama) para encontrar por significado y no solo por palabras.
4. **v4:** afinar (LoRA/SFT) un modelo pequeño con tus notas y conversaciones para que hable "a tu manera". Ver [[Clase 15 - Mid y post-training]]: el SFT sirve para **estilo**, no para meter datos (eso lo hace el RAG).
5. **v5:** conectarla a tus herramientas (Agent Desktop, Playwright, MCPs) para que **actúe**, no solo responda.

## Cómo sigue aprendiendo
- Cada vez que trabajes con Claude, pídele: **"guarda lo aprendido en la bóveda"**. Escribirá notas nuevas.
- En el chat de Mi IA: `/recordar <lo que sea>`.
- Tú mismo, escribiendo notas en Obsidian. Mi IA las lee al momento.

## Hardware recomendado para la v2
- Modelo de 7-8B cuantizado (Q4): unos **8 GB de RAM o VRAM**. Va bien en un portátil moderno o en un Mac M1/M2/M3.
- Modelo de 14B: unos 12-16 GB. De 32B: 24 GB o más (GPU buena).
- Sin GPU funciona igual, pero más lento ([[Clase 10 - Inferencia]]: llama.cpp, cuantización).
