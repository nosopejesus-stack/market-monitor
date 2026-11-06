---
curso: "[[CS336 - Índice]]"
clase: 2
tema: PyTorch, einops y contabilidad de recursos (FLOPs y memoria)
video: https://www.youtube.com/watch?v=kuYAsz7zspQ
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_02.py
tags: [cs336, pytorch, einops, flops, memoria, precision]
---

# Clase 02: PyTorch, einops y contabilidad de recursos

**Mentalidad:** antes de entrenar, haz siempre las cuentas de memoria y cómputo, a lo "servilleta".

## Preguntas de ejemplo
- ¿Cuánto tarda entrenar un modelo de 70B parámetros con 15T tokens en 1024 H100?
  Respuesta: FLOPs = 6 × N × D, y eso se divide entre (FLOP/s × MFU × número de GPUs).
- ¿Cuál es el modelo más grande que cabe en 8 H100 con AdamW?
  Respuesta: cada parámetro ocupa unos 16 bytes (parámetros, gradientes y estados del optimizador). Es un límite superior porque no cuenta las activaciones.

## Tensores y tipos numéricos
Todo es un tensor: datos, parámetros, gradientes, estados del optimizador y activaciones.

| Tipo | Bytes | Notas |
|---|---|---|
| fp32 | 4 | por defecto y estable |
| fp16 | 2 | rango dinámico pobre: inestabilidad |
| **bf16** | 2 | mismo rango que fp32 con menos resolución; ideal para deep learning (Google Brain, 2018) |
| fp8 | 1 | estándar desde 2022 (E4M3 y E5M2 en H100) |
| nvfp4 | 0,5 | 2025; usa un factor de escala por bloque. Nemotron 3 Super se entrenó en NVFP4 |

**Precisión mixta:** bf16 para parámetros, activaciones y gradientes; fp32 para los estados del optimizador. PyTorch lo automatiza con AMP.

## einops
- Biblioteca para operar con tensores usando **dimensiones con nombre**, inspirada en la notación de Einstein.
- `einsum`: multiplicación de matrices generalizada; las dimensiones que no aparecen en la salida se suman.
- `reduce` (sum, mean, max), `rearrange` (partir o juntar dimensiones, por ejemplo `heads * hidden`).
- Evita errores del tipo "¿qué era la dimensión -2?".

## FLOPs
- **FLOPs** es la cantidad de operaciones; **FLOP/s** es la velocidad del hardware. Se pronuncian igual y se confunden fácilmente.
- Una multiplicación de matrices (B×D) @ (D×K) cuesta **2·B·D·K** FLOPs.
- Entrenar GPT-3 costó 3,14e23 FLOPs; GPT-4 se estima en 2e25.
- **MFU** (Model FLOPs Utilization) = FLOP/s reales / FLOP/s prometidos. Un 50 % o más es bueno.

### Regla de oro del entrenamiento
- Forward: **2 × datos × parámetros**.
- Backward: **4 × datos × parámetros** (el doble que el forward).
- **Total: 6 × datos × parámetros** FLOPs. Vale para MLPs y, con contextos cortos, también para Transformers.

## Intensidad aritmética y roofline
- Un cálculo tarda lo que tarde lo más lento de dos cosas: mover los datos (ancho de banda de memoria) o calcular (FLOP/s).
- **Intensidad aritmética** = FLOPs por byte movido.
- Si la intensidad aritmética es menor que la del acelerador, la operación está **limitada por memoria**; si es mayor, **limitada por cómputo**.
- ReLU, GeLU, producto escalar y matriz × vector están limitados por memoria. Por eso ReLU no es más rápido que GeLU.
- Las multiplicaciones de matrices grandes están **limitadas por cómputo**, y el entrenamiento está lleno de ellas.
- La inferencia hace matriz × vector, por eso **está limitada por memoria** (ver [[Clase 10 - Inferencia]]).
- `MFU = min(1, intensidad aritmética / intensidad del acelerador)`.

## Optimizadores y su memoria
- Momentum = SGD + media exponencial del gradiente.
- AdaGrad = SGD + escalado por gradiente².
- RMSProp = AdaGrad con media exponencial.
- **Adam** = RMSProp + momentum: guarda 8 bytes por parámetro (dos momentos en fp32).

## Trucos para ahorrar memoria
- **Acumulación de gradientes:** calcula el gradiente en *microbatches* y actualiza cada `batch / micro_batch` pasos. Permite batches grandes y estables.
- **Activation checkpointing** (rematerialización): guarda solo algunas capas y recalcula el resto en el backward. Cambia memoria por cómputo. Si se guarda cada √L capas, la memoria es O(√L) y el recálculo O(L).

## Ideas clave
- Entrenar cuesta unos 6·N·D FLOPs.
- Las multiplicaciones de matrices están limitadas por cómputo y las operaciones elemento a elemento, por memoria.
- Siguiente paso: [[Clase 03 - Arquitecturas]].
