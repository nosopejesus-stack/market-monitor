---
curso: "[[CS336 - Índice]]"
clase: 5
tema: Cómo funcionan las GPUs y por qué se vuelven lentas; FlashAttention
profesor: Tatsunori Hashimoto
video: https://www.youtube.com/watch?v=izZba4UA7iY
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_05.pdf
tags: [cs336, gpu, tpu, hardware, flashattention, rendimiento]
---

# Clase 05: GPUs y TPUs

**Objetivo:** que CUDA y las GPUs dejen de parecer magia. Saber cuándo se vuelven lentas y cómo escribir algoritmos rápidos.

## Por qué importan
- Más cómputo da mejoras **predecibles** en los LLM (leyes de escala).
- El escalado de Dennard (CPUs cada vez más rápidas) se agotó. Ahora todo es **escalado paralelo**: las GPUs han crecido más de 1000× en 10 años.
- **No hay escalado de LLMs sin escalado de GPUs.**

## CPU frente a GPU
- La **CPU** tiene pocos hilos muy rápidos y optimiza la **latencia**.
- La **GPU** tiene miles de hilos sencillos y optimiza el **rendimiento total** (throughput).

## Anatomía de una GPU
- **SM (Streaming Multiprocessors):** ejecutan *bloques* de forma independiente. Una A100 tiene 108; una B200, 148.
- **Memoria**, cuanto más cerca del SM, más rápida:
  - registros y memoria compartida/L1 (SRAM, dentro del SM);
  - L2 (en el chip);
  - **HBM** (memoria global, la más lenta).
  - La SRAM es unas 8× más rápida que la DRAM, y unas 100× más cara.
- **Modelo de ejecución (SIMT):**
  - **hilos**: todos ejecutan la misma instrucción con datos distintos;
  - **bloques**: grupos de hilos en un SM con memoria compartida;
  - **warps**: grupos de 32 hilos que avanzan juntos.
- Los **tensor cores** son circuitos dedicados a multiplicar matrices: la multiplicación de matrices es **más de 10× más rápida** que el resto de operaciones.
- Las **TPUs** son parecidas a alto nivel: control ligero, una unidad de multiplicación de matrices enorme y memoria rápida. Cambia cómo se conectan entre sí.
- **El cómputo escala más rápido que la memoria**, y cuesta mantener las unidades alimentadas de datos.

## Seis trucos para que vaya rápido
1. **Evitar la divergencia de control:** los `if` dentro de un warp se ejecutan en serie.
2. **Baja precisión:** menos bits que mover, más intensidad aritmética. FP8, MXFP8 (escala por cada 32 valores), MXFP4.
3. **Fusión de operadores:** imagina una fábrica (el cómputo) y un almacén (la memoria). No mandes y devuelvas el material en cada paso. `sin²x + cos²x` lanza 5 kernels si no se fusiona; `torch.compile` lo fusiona en uno.
4. **Recalcular:** tirar activaciones y recalcularlas puede ser *más rápido* porque ahorra lecturas de memoria.
5. **Accesos coalescentes:** la DRAM se lee en ráfagas. Si los 32 hilos de un warp leen la misma ráfaga, basta una transacción.
6. **Tiling (el más importante):** partir las matrices en *tiles*, cargarlos en memoria compartida y reutilizarlos. Reduce las lecturas a memoria global por un factor T (el tamaño del tile).
   - Problemas: tamaños que no dividen la matriz, alineación de memoria, y la **cuantización por oleadas**. Ejemplo: una matriz de 1792 sale en 98 tiles, que caben en los 108 SMs de una A100; una de 1793 sale en 120 tiles, y hace falta una segunda oleada casi vacía.

## FlashAttention, explicado
- La atención son tres multiplicaciones de matrices con un softmax en medio.
- **Tiling** en las multiplicaciones Q·Kᵀ y ·V.
- **Softmax online:** se calcula tile a tile actualizando el máximo con una suma telescópica.
- Todo **fusionado**: la matriz n×n de atención nunca se escribe en HBM. En el backward se recalcula tile a tile.

## Ideas clave
- Hay que pensar siempre en **multiplicación de matrices + movimiento de datos**.
- Coalescencia, tiling y fusión son las claves del rendimiento.
- Sigue en [[Clase 06 - Kernels, Triton y XLA]].
