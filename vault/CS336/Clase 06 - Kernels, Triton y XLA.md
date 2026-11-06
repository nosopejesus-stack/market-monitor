---
curso: "[[CS336 - Índice]]"
clase: 6
tema: Benchmarking, profiling y escribir kernels en Triton
video: https://www.youtube.com/watch?v=xnDHaNUvHBg
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_06.py
tags: [cs336, triton, cuda, kernels, profiling]
---

# Clase 06: Kernels, Triton y XLA

## Hardware de referencia
| | A100 | H100 | B200 |
|---|---|---|---|
| SMs | 108 | 132 | 148 |
| Memoria compartida/L1 por SM | 192 KB | 256 KB | 256 KB |
| L2 | 40 MB | 50 MB | 96-126 MB |
| HBM | 80 GB | 80 GB | 192 GB |
| Ancho de banda HBM | 2 TB/s | 3,35 TB/s | 8 TB/s |
| Ancho de banda de memoria compartida | ~19 TB/s | ~33 TB/s | ~40 TB/s |

## Modelo de programación
**grid** (HBM) → **bloque de hilos** (memoria compartida, un SM) → **hilo** (registros).
- Para operaciones elemento a elemento basta con hilos. Para softmax o multiplicación de matrices los hilos deben comunicarse, y para eso existe el **bloque**.

## Detalles de hardware que deciden el rendimiento
- **Warps de 32 hilos:** se ejecutan al unísono; la divergencia (`if`/`else`) se serializa. El SM alterna entre warps sin coste mientras uno espera a la HBM.
- **Ocupación:** más registros por hilo significa menos hilos simultáneos. No siempre es malo: con *thread coarsening*, cada hilo procesa varios elementos.
- **Conflictos de banco:** la memoria compartida tiene 32 bancos. Si varios hilos acceden al mismo banco, se serializan. Se resuelve con *swizzling*.
- **Coalescencia:** las lecturas de un warp se agrupan en líneas de 128 bytes.
- **Oleadas:** si lanzas 160 bloques en una B200 (148 SMs), la segunda oleada lleva solo 12. Conviene que el número de bloques sea múltiplo del número de SMs.

## Medir antes de optimizar
1. Benchmark y profiling.
2. Haz cambios.
3. Vuelve a medir.

- **Benchmark:** tiempo total, útil para comparar y ver cómo escala.
- **Profiling** (profiler de PyTorch, nsight): en qué se va el tiempo y qué kernels se ejecutan de verdad.
  - El nombre del kernel da pistas. Por ejemplo, `cutlass3x_sm100_..._f32_64x64x16` indica librería CUTLASS, arquitectura Blackwell, fp32 y tiles de 64×64×16.
- GeLU ingenuo frente a GeLU integrado o compilado: el ingenuo lanza varios kernels con muchas lecturas y escrituras; el compilado es **un solo kernel fusionado**, generado en Triton.

## Triton (de OpenAI)
- En **CUDA** se programa qué hace cada **hilo**: control fino, pero más gestión manual.
- En **Triton** se programa qué hace cada **bloque**: cargar a memoria compartida, operar (fusión) y escribir en HBM. Compila a **PTX**, el ensamblador de las GPUs.
- Ejemplos de la clase:
  - **GeLU** (elemento a elemento; cada hilo procesa 8 elementos).
  - **Softmax** (por filas, cabe en un bloque).
  - **Suma por filas** con tiles, cuando la fila no cabe.
  - **Multiplicación de matrices + ReLU** con tiling y fusión.
- Multiplicación de matrices:
  - ingenua: intensidad O(1);
  - con tiles: intensidad **O(tamaño del tile)**;
  - además se fusiona la activación, con `GeLU(A@B)` en el mismo kernel.

## Ideas clave
- El modelo de programación garantiza que el resultado sea correcto; el hardware decide la velocidad.
- En la tarea 2 se escribe un kernel **RMSNorm fusionado en Triton**.
- Sigue en [[Clase 07 - Paralelismo]].
