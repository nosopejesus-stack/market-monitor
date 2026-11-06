---
tipo: proyecto
estado: v3 lista (red 100 % desde cero y verificada; el instalador elige el cerebro más potente); falta instalarla en tu PC
tags: [brainus, proyecto, rag, obsidian, ollama]
---

# Brainus: plan y arquitectura

> **Brainus** es el nombre que el dueño eligió para su IA el 2026-11-06 (antes se llamaba "Mi IA").

## Qué quieres
Tu propia IA funcionando, que **aprenda todo lo que Claude sabe de ti y de tus proyectos** y que tenga acceso a Obsidian como memoria.

## La verdad técnica (para no llevarse sorpresas)
- **Claude no se puede copiar.** Sus "conocimientos" están en sus pesos, que no son públicos. Lo que sí se transfiere es **lo que aprendemos juntos**: notas, decisiones, cursos resumidos y tus datos. Todo eso vive en esta bóveda.
- **Entrenar un modelo desde cero** (lo que enseña [[CS336 - Índice|CS336]]) es posible a escala pequeña. Un modelo de 100M parámetros con TinyStories entrena en horas con una GPU. Pero no se acercará a Claude: la frontera cuesta millones ([[Clase 09 - Leyes de escala]]).
- **El camino que funciona hoy:**

```
   Tú ──pregunta──▶ Brainus (brainus.py)
                       │ 1. busca en tu bóveda (BM25)
                       ▼
               Bóveda de Obsidian (vault/) ◀── Claude y tú escribís notas
                       │ 2. fragmentos relevantes
                       ▼
               Modelo de lenguaje
               ├─ Ollama (local, gratis, privado): el qwen3 más grande que aguante tu PC
               ├─ red propia de Brainus (desde cero, experimental)
               └─ API de Claude (de pago, más inteligente)
                       │ 3. respuesta citando [[notas]]
                       ▼
   Tú ◀── respuesta      y "/recordar ..." ──▶ nota nueva en Memoria/Recuerdos
```

Esto se llama **RAG** (generación aumentada con recuperación). Es justo la "memoria persistente en archivos" que usan los agentes ([[Clase 12 - Evaluación]]).

## Fases
1. ✅ **v1:** bóveda + búsqueda BM25 + chat + `/recordar`.
2. ✅ **v2 (2026-11-06):**
   - **reglas Hacer / No hacer** que siempre se cumplen;
   - **👍/👎 que crean reglas**;
   - búsqueda **por significado** (embeddings);
   - **página web local**;
   - historial de conversaciones;
   - **[[Brainus - Red neuronal]]** propia creada desde cero.
3. ✅ **v3 (2026-11-06):**
   - red neuronal reescrita **100 % desde cero** según CS336 y verificada con 23 tests;
   - el instalador **elige el cerebro más potente** según tu RAM/GPU (de `qwen3:4b` a `qwen3:32b`);
   - nombre definitivo: **Brainus**.
4. ⏳ **En tu PC:** ejecutar `brainus/instalar_windows.ps1`.
5. **v4:** afinar un modelo abierto con tus 👍/👎 (DPO, [[Clase 15 - Mid y post-training]]) para que responda a tu gusto.
6. **v5:** darle manos con [[Agent Desktop]] y Playwright, para que actúe en tu PC y no solo responda.

## Cómo sigue aprendiendo
- **Automático con Claude Code:** el instalador añade a `~/.claude/CLAUDE.md` unas instrucciones. Con ellas, Claude lee tus reglas al empezar y, al terminar cada tarea, escribe en la bóveda lo bueno (Hacer), lo malo (No hacer) y un resumen de la sesión. En este repo lo dice el `CLAUDE.md` de la raíz.
- En Brainus: 👍/`/bien`, 👎/`/mal <por qué>` (crea una regla), `/hacer`, `/evitar`.
- En el chat de Brainus: `/recordar <lo que sea>`.
- Tú mismo, escribiendo notas en Obsidian. Brainus las lee al momento.

## Qué cerebro elige el instalador
| Tu PC | Cerebro | Notas |
|---|---|---|
| GPU de 24 GB | `qwen3:32b` | el más listo que cabe en una sola GPU de consumo |
| GPU de 16 GB | `qwen3:14b` | |
| 32 GB de RAM | `qwen3:30b-a3b` | MoE: 30B parámetros pero solo 3B activos por token, rápido en CPU ([[Clase 04 - Alternativas a la atención y MoE]]) |
| 16 GB de RAM o GPU de 8 GB | `qwen3:8b` | |
| menos | `qwen3:4b` | |

Van todos cuantizados (Q4), que reduce la memoria unas 4 veces ([[Clase 10 - Inferencia]]).
