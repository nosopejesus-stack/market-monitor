---
tipo: proyecto
creada: 2026-11-06
parametros: 5.344.512
codigo: mi-ia/red_neuronal/
tags: [mi-ia, red-neuronal, transformer, cs336]
---

# Mi red neuronal (creada desde cero)

Un modelo de lenguaje propio construido con lo aprendido en [[CS336 - Índice|CS336]]. No usa ningún modelo ajeno: cada peso se aprendió de los datos.

## Arquitectura
| Pieza | Elección | Por qué ([[Clase 03 - Arquitecturas]]) |
|---|---|---|
| Tokenizador | BPE de bytes, 2048 tokens (2,79 bytes por token) | [[Clase 01 - Panorama y tokenización]] |
| Capas | 6 bloques Transformer, d = 256, 8 cabezas | proporción ancho/profundidad razonable para su tamaño |
| Normalización | **pre-norm RMSNorm** | estabilidad y menos movimiento de datos |
| Posición | **RoPE** | depende solo de la posición relativa |
| FFN | **SwiGLU**, d_ff ≈ 8/3·d | el consenso moderno |
| Bias | ninguno | memoria y estabilidad |
| Optimizador | **AdamW** (β = 0,9 / 0,95, weight decay 0,1), warmup + coseno | [[Clase 02 - PyTorch, einops y contabilidad de recursos]] |
| Pesos de entrada y salida | compartidos | menos parámetros |

## Cómo se entrenó (2026-11-06, CPU de 4 núcleos)
1. **Preentrenamiento:** 12 MB de Wikipedia en español (4,4M tokens), 1878 pasos y unos 16 minutos. La pérdida de validación bajó de **7,66 a 3,43**.
2. **Mid-training:** la bóveda (×2) mezclada con Wikipedia, 83 pasos.
   - Un primer intento más largo **sobreajustó**: la pérdida con la bóveda bajó a 0,68, pero en español general subió a 4,45. Es la lección de la [[Clase 14 - Datos (filtrado y deduplicación)]].
   - Se repitió más corto, y ahora el script guarda siempre **la mejor versión**.

Muestra real después del mid-training:
> "## Leyes de escala (SubSH) es un fp53 íbola para la atención (el lento de los modelos invadidos). ### **GRU** … el gradiente de **entender más grande** … **GPU** (sin tensor…"

Escribe español con tu vocabulario y tu formato de notas, pero **no razona** ni dice cosas ciertas. Es lo esperable con 5M parámetros: GPT-2 pequeño tenía 124M y qwen3:8b tiene 8000M.

## Cómo hacerla crecer
- `python mi-ia/red_neuronal/entrenar.py --continuar --minutos 10`: aprende tus notas nuevas, guardando la mejor versión.
- Con GPU puedes probar `--d 512 --capas 8 --contexto 512 --minutos 60` y más texto en `red_neuronal/corpus/`.
- Siguiente nivel: afinar un modelo abierto con tus 👍 y 👎 (`mi-ia/datos/preferencias.jsonl`) usando **DPO**: [[Clase 15 - Mid y post-training]].

Relacionado: [[Mi IA - Plan]].
