---
curso: "[[CS336 - Índice]]"
clase: 7
tema: Paralelismo entre varias GPUs (operaciones colectivas, datos, tensores, pipeline)
video: https://www.youtube.com/watch?v=SzpOcwdIL0Y
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_07.py
tags: [cs336, paralelismo, distribuido, nccl, fsdp, zero]
---

# Clase 07: Paralelismo (parte 1)

**Tema unificador:** el cómputo está lejos de los datos, así que hay que orquestarlo para no atascarse en las transferencias.

Jerarquía de velocidad, de más rápida a más lenta:
1. Memoria compartida/L1.
2. HBM.
3. NVLink/NVSwitch, dentro del nodo.
4. InfiniBand/Ethernet, entre nodos.

**Por qué usar varias GPUs:**
1. Parámetros, gradientes, estados del optimizador y activaciones no caben en una sola.
2. Más GPUs, más FLOPs, se entrena antes.

## Operaciones colectivas (vienen de la computación paralela de los años 80)
- **Rank:** cada GPU. **World size:** el número total de GPUs.
- **Broadcast, scatter, gather, reduce:** las básicas.
- **All-gather:** todos reciben todo. Uso: juntar trozos de parámetros para el forward.
- **Reduce-scatter:** se suma y se reparte. Uso: sumar gradientes guardando cada uno solo su trozo.
- **All-reduce = reduce-scatter + all-gather.** Uso: sumar gradientes y que todos tengan la copia completa.
- **All-to-all:** cada uno envía algo a cada uno. Uso: los **MoE**, para enviar tokens a los expertos.
- Cómo recordarlo: *reduce* = operación asociativa (suma, máx...); *scatter* es lo inverso de *gather*; *all* = el destino son todos.

## Hardware de comunicación
- En casa: Ethernet a ~200 MB/s.
- En un centro de datos:
  - **8 GPUs por nodo** con NVLink/NVSwitch (B200: 1,8 TB/s);
  - 256 nodos por *pod* con **InfiniBand** (~50 GB/s);
  - **RDMA:** una GPU lee la memoria de otra sin pasar por la CPU.
  - GB200/GB300 **NVL72**: 72 GPUs en un único dominio NVLink.
  - **RoCE:** RDMA sobre Ethernet, más barato (lo usa Meta).
- **NCCL** (librería de NVIDIA) detecta la topología, optimiza rutas y lanza kernels de comunicación. `torch.distributed` ofrece las colectivas con backends gloo (CPU) y nccl (GPU).

## Estrategias de paralelismo
| Tipo | Qué se reparte | Comunicación | Notas |
|---|---|---|---|
| **Datos (DDP)** | el batch | all-reduce de gradientes | cada GPU tiene el modelo entero |
| **FSDP / ZeRO** | datos + parámetros, gradientes y estados del optimizador | all-gather + reduce-scatter | ahorra mucha memoria |
| **Tensor** | parte de cada capa (el ancho) | activaciones en cada capa | necesita interconexión **muy** rápida (NVLink) |
| **Pipeline** | grupos de capas (la profundidad) | activaciones entre etapas | sirve con conexiones lentas, pero hay que reducir las "burbujas" |
| Secuencia | la longitud | | contexto largo |
| Expertos | los expertos de un MoE | all-to-all | ver [[Clase 04 - Alternativas a la atención y MoE]] |

- Siempre hay tres opciones: **recalcular**, **guardar en memoria**, o **guardar en otra GPU y comunicarlo**.
- Con JAX y TPUs defines el modelo y la estrategia de *sharding*, y el compilador hace el resto.

## Ideas clave
- El hardware mejora, pero siempre querremos modelos más grandes, así que la jerarquía de memoria seguirá ahí.
- En la tarea 2 se implementan DDP y *sharding* del optimizador.
- Sigue en [[Clase 08 - Paralelismo (parte 2)]].
