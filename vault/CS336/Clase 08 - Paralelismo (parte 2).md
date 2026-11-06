---
curso: "[[CS336 - Índice]]"
clase: 8
tema: Paralelismo a gran escala (ZeRO, FSDP, pipeline, tensor, expertos, 3D)
profesor: Tatsunori Hashimoto
video: https://www.youtube.com/watch?v=6-cXp-aOmdg
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_08.pdf
tags: [cs336, paralelismo, zero, fsdp, pipeline, tensor-parallel, megatron]
---

# Clase 08: Paralelismo (parte 2)

La nueva unidad de cómputo es **el centro de datos**. Lo que se busca:
- **memoria lineal:** el tamaño máximo del modelo crece con el número de GPUs;
- **cómputo lineal:** los FLOPs crecen con el número de GPUs.

## Redes
- **TPU:** malla toroidal; barata, sirve para paralelismo de tensores.
- **GPU:** todos con todos, hasta 256 GPUs; mejor para comunicaciones poco estructuradas como los expertos de un MoE.
- All-reduce = reduce-scatter + all-gather. Con el ancho de banda como límite, es lo mejor que se puede hacer.

## Paralelismo de datos y el problema de la memoria
Cada parámetro necesita unos **16 bytes**:
- 2 de parámetros bf16;
- 2 de gradientes bf16;
- 4 de pesos maestros fp32;
- 4 + 4 de los dos momentos de Adam.

### ZeRO (fases)
| Fase | Qué se reparte | Comunicación | ¿Gratis? |
|---|---|---|---|
| DDP ingenuo | nada | 2×parámetros (all-reduce) | |
| **ZeRO-1** | estados del optimizador | 2×parámetros (reduce-scatter + all-gather) | **sí: úsalo siempre** |
| **ZeRO-2** | + gradientes | 2×parámetros | casi |
| **ZeRO-3 / FSDP** | + parámetros | 3×parámetros (1,5×) | bastante barato |

- **FSDP:** se piden los parámetros justo antes de usarlos y se liberan después. La comunicación se **solapa** con el cómputo.
- Ejemplo con 8 A100 de 80 GB y 12 bytes por parámetro: sin ZeRO caben 6,6B parámetros; con ZeRO-1, 16B; con ZeRO-2, 24,6B; con **ZeRO-3, 53B**.
- Límites: el número de máquinas no puede superar el batch, el batch tiene rendimientos decrecientes, y ZeRO no reduce la memoria de **activaciones**.

## Paralelismo de modelo (reparte parámetros y comunica activaciones)
- **Pipeline (profundidad):** grupos de capas por GPU, con *microbatches* para tapar huecos.
  - Fracción de **burbuja** ≈ (etapas − 1) / microbatches, así que hace falta un batch grande.
  - Ventajas: ahorra memoria y la comunicación es punto a punto y pequeña. Se usa **entre nodos** con conexiones lentas.
  - "Zero bubble": se separa el backward de activaciones del de pesos.
- **Tensor (ancho):** se parten las multiplicaciones de matrices por columnas (QKV, up-projection) y por filas (salida de la atención, down-projection).
  - No hay burbuja ni hace falta batch grande, pero **comunica mucho** en cada capa.
  - Solo **dentro de un nodo**: tensor parallel = 8 suele ser lo óptimo.
- **Secuencia:** reparte LayerNorm y dropout a lo largo de la secuencia. Junto al de tensor, la memoria de activaciones queda **lineal**.
- **Expertos (EP):** reparte los expertos y enruta las activaciones con all-to-all. Megatron separa el paralelismo de la atención (TP/CP/DP) del de las MLP (ETP/EP/EDP).
- **Contexto / Ring attention:** para secuencias muy largas.

## Reglas para el paralelismo 3D (4D)
1. **Hasta que el modelo quepa:** paralelismo de tensor o de expertos dentro de la máquina (≤ 8) y pipeline entre máquinas, o ZeRO-3, según el ancho de banda.
2. **Después, hasta acabar las GPUs:** paralelismo de datos.
3. Con batch pequeño: acumulación de gradientes.
- Recalcular activaciones puede **salir rentable**: libera memoria y permite batches mayores.

## Qué hacen los modelos reales
| Modelo | DP | TP | EP | PP | CP |
|---|---|---|---|---|---|
| DeepSeek v3 | ZeRO-1 | 1 | 64 | 16 | |
| Llama 3 405B | 128 | 8 | | 16 | 1 |
| Gemma 2 | 768 (ZeRO-3) | 8 | | | |
| Qwen 3 | | 2 | 32 | 8 | 1 |
| Nemotron 3 (contexto largo) | | 2 | 64 | | 64 |

Patrones: **TP ≤ 8**, EP puede ser grande (pero es difícil) y las fases de contexto largo usan mucho CP. A esta escala **fallan muchas GPUs** (lo cuenta el informe de Llama 3).

## Ideas clave
- No hay una solución única: se combinan las tres familias, con reglas sencillas.
- Ver también [[Clase 07 - Paralelismo]].
