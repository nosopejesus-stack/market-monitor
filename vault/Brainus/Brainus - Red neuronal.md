---
tipo: proyecto
creada: 2026-11-06
version: 2 (100 % desde cero)
parametros: 13.767.552
codigo: brainus/red_neuronal/
tags: [brainus, red-neuronal, transformer, cs336]
---

# La red neuronal de Brainus (creada desde cero)

Un modelo de lenguaje propio, escrito **pieza a pieza** según las especificaciones de la tarea 1 de [[CS336 - Índice|CS336]]. No usa ningún modelo ajeno ni las capas ya hechas de PyTorch: cada operación está programada a mano y cada peso se aprendió de los datos.

## Piezas (todas programadas a mano)
| Pieza | Detalle | Clase |
|---|---|---|
| Tokenizador BPE de bytes | 4096 tokens, token especial `<\|endoftext\|>`, regex de GPT-2, entrenamiento incremental (19 s frente a 206 s de la versión ingenua) | [[Clase 01 - Panorama y tokenización]] |
| Linear y Embedding | sin bias; inicialización normal truncada (±3σ) | [[Clase 03 - Arquitecturas]] |
| RMSNorm | en float32 y vuelta al tipo original | [[Clase 03 - Arquitecturas]] |
| SwiGLU + SiLU | d_ff ≈ 8/3·d | [[Clase 03 - Arquitecturas]] |
| softmax estable y atención escalada | máscara causal | [[Clase 05 - GPUs y TPUs]] |
| RoPE | rotación por pares, θ = 10000 | [[Clase 03 - Arquitecturas]] |
| Atención multi-cabeza | Q, K y V en una sola multiplicación de matrices | [[Clase 03 - Arquitecturas]] |
| Bloque pre-norm y TransformerLM | 6 capas, d = 384, 6 cabezas, contexto 256 | [[Clase 03 - Arquitecturas]] |
| Cross-entropy | estable con log-sum-exp | [[Clase 02 - PyTorch, einops y contabilidad de recursos]] |
| AdamW | weight decay desacoplado y corrección de sesgo | [[Clase 02 - PyTorch, einops y contabilidad de recursos]] |
| LR coseno con calentamiento, recorte de gradientes | | [[Clase 11 - Leyes de escala (detalles)]] |
| Checkpoints, generación con temperatura y **top-p** | | [[Clase 10 - Inferencia]] |

**Verificación:** 23 tests (`brainus/red_neuronal/test_red.py`) comparan cada pieza con la referencia oficial de PyTorch. Todos pasan.

> No se conectó a los tests oficiales de la tarea: el curso pide a las IAs no resolver las tareas de los alumnos. Brainus es un proyecto propio. Si el dueño quiere hacer la tarea, Claude le hace de tutor.

## Cómo se entrenó (2026-11-06, CPU de 4 núcleos)
1. **Preentrenamiento:** 12 MB de Wikipedia en español + la bóveda (3,8M tokens), 1009 pasos, 22 min. Perplejidad 94.
2. **Preentrenamiento reanudado:** 1119 pasos más, 25 min. **Perplejidad 61, 1,85 bits/byte.**
3. **Mid-training con la bóveda:** 144 pasos. La validación mezcla notas apartadas (que no ve al entrenar) con Wikipedia.
   - El primer intento se **descartó**: medía solo Wikipedia y eligió un punto que casi no había aprendido tus notas.

Los pesos se guardan en **bfloat16** (27,5 MB en vez de 55). Historial completo en `brainus/red_neuronal/pesos/historial.json`.

**Bits por byte** sirve para comparar modelos con tokenizadores distintos: es la pérdida dividida entre ln 2 y entre los bytes por token.

Muestra real después del mid-training:
> "## Leyes de escala de trucos de entrenamiento, cada vez más tarde con los modelos de perdería."

Escribe español y usa tu vocabulario y tu formato (`## Ideas clave`, listas), pero **no razona**. Con 14M parámetros es lo esperable: GPT-2 small tiene 124M y el cerebro diario de Brainus (Qwen3) tiene entre 4.000 y 32.000M.

## Cómo hacerla crecer
| Objetivo | Comando |
|---|---|
| Que aprenda tus notas nuevas | `python brainus/red_neuronal/entrenar.py --continuar` |
| Más español | `python brainus/red_neuronal/descargar_corpus.py --mb 500` y luego `entrenar.py --reanudar` |
| Más grande (CPU potente o GPU) | `entrenar.py --perfil medio --minutos 120` (~45M) |
| Tamaño GPT-2 (GPU) | `entrenar.py --perfil potente --minutos 480` (~125M) |

Según Chinchilla ([[Clase 09 - Leyes de escala]]), lo ideal son unos 20 tokens por parámetro: el perfil `potente` querría unos 2.500M tokens (~7 GB de texto).

Relacionado: [[Brainus - Plan]].
