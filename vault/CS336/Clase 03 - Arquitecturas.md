---
curso: "[[CS336 - Índice]]"
clase: 3
tema: Arquitecturas e hiperparámetros del Transformer moderno
profesor: Tatsunori Hashimoto
video: https://www.youtube.com/watch?v=lVynu4bo1rY
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_03.pdf
tags: [cs336, transformer, arquitectura, hiperparametros, estabilidad]
---

# Clase 03: Arquitecturas e hiperparámetros

> "La mejor forma de aprender es con experiencia práctica; la segunda mejor, aprender de la experiencia de otros." Esta clase compara decenas de modelos para ver en qué coinciden.

## Del Transformer original al moderno ("tipo LLaMA")

| Pieza | Original (2017) | Moderno (lo que implementas) |
|---|---|---|
| Normalización | post-norm, LayerNorm | **pre-norm, RMSNorm** |
| Posición | senos y cosenos sumados | **RoPE** (rotaciones) |
| FFN | ReLU | **SwiGLU** |
| Sesgos (bias) | sí | **no** |

## Normalización
- **Pre-norm**, con la norma fuera del camino residual: en esto coincide casi todo el mundo (BERT era post-norm). Da gradientes más sanos, menos picos y permite learning rates más altos.
- Tendencia nueva: "doble norma", con una post-norm fuera del flujo residual (Grok, Gemma 2, OLMo 2).
- **RMSNorm** no resta la media ni añade bias. Lo usan LLaMA, PaLM, Chinchilla y T5.
  - **Lección:** los FLOPs no son el tiempo de ejecución. RMSNorm apenas ahorra FLOPs, pero ahorra **movimiento de datos**, y eso sí cuenta.
- Se eliminan los términos de bias por memoria y por estabilidad de la optimización.

## Activaciones
- ReLU (Transformer original, T5, OPT), GeLU (GPT-1/2/3, BLOOM).
- **GLU con compuerta:** `FF(x) = (act(xW1) ⊗ xV) W2`. **SwiGLU** (LLaMA, PaLM, Mistral, OLMo) y **GeGLU** (T5 v1.1, Gemma). Hoy son el consenso y dan ganancias consistentes (Shazeer 2020).
- Con GLU, `d_ff` se reduce a 2/3 para mantener los parámetros: **d_ff ≈ 8/3 · d_model**.
- Capas serie o en paralelo: casi todos usan capas en **serie**. GPT-J, PaLM y Command A las usan en paralelo.

## Posición: RoPE
- Objetivo: que la atención dependa solo de la posición **relativa** (i − j).
- Idea: los productos escalares no cambian al rotar. Se agrupan las coordenadas de dos en dos y se **rotan** según la posición (inspirado en los números complejos).
- No es aditivo ni tiene términos cruzados. Se aplica a Q y K en **cada** capa de atención.
- Lo usan GPT-J, PaLM, LLaMA y casi todos los modelos desde 2024.

## Hiperparámetros de consenso
| Hiperparámetro | Regla | Notas |
|---|---|---|
| `d_ff / d_model` | **4** (o **8/3 ≈ 2,67** con GLU) | buena zona entre 1 y 10; T5 usó 64× y luego volvió a 2,5 |
| `n_heads · head_dim / d_model` | **≈ 1** | algunos modelos de Google lo superan |
| Proporción `d_model / n_layers` | **~100-200** (muchos usan 128) | los modelos muy profundos se paralelizan peor y tienen más latencia |
| Vocabulario | 30-50K monolingüe; **100-250K** multilingüe | GPT-4 usa 100K, Gemma 4 262K |
| Dropout | ya casi nadie lo usa | los modelos nuevos solo usan weight decay |
| Weight decay | ~0,1 | no es para el sobreajuste: interactúa con el LR (programa coseno) |

## Trucos de estabilidad (cuidado con los softmax)
- **z-loss** en el softmax de salida, para que el normalizador no explote (PaLM, OLMo 2/3).
- **QK-norm:** normalizar Q y K antes del softmax de atención (Gemma 2/4, Qwen3, OLMo 3).
- **Soft-capping de logits** con tanh.

## Atención más barata
- En el entrenamiento la atención tiene buena intensidad aritmética.
- En la **generación** se usa la **KV cache** y la intensidad cae: queda limitada por memoria.
- **MQA:** una sola cabeza de K/V para todas las queries. **GQA:** pocas cabezas de K/V; regula el equilibrio entre expresividad e inferencia. **MLA** (DeepSeek): K/V latentes comprimidas.
- **Ventana deslizante o atención dispersa:** se intercalan capas "completas" y "locales". Command A usa una completa cada 4; LLaMA 4, Gemma 3/4 y OLMo 3 hacen algo parecido.

## Ideas clave
- Casi todos los LLM grandes comparten arquitectura. Las diferencias principales están en posición, activaciones y tokenización.
- Sigue en [[Clase 04 - Alternativas a la atención y MoE]].
