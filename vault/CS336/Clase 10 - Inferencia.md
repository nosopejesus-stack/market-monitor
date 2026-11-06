---
curso: "[[CS336 - Índice]]"
clase: 10
tema: Inferencia eficiente (KV cache, GQA/MLA, cuantización, decodificación especulativa, vLLM)
video: https://www.youtube.com/watch?v=EfM546A79aM
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_10.py
tags: [cs336, inferencia, kv-cache, cuantizacion, speculative-decoding, vllm]
---

# Clase 10: Inferencia

## Por qué importa
- La inferencia aparece en el uso real (chat, código, **agentes**), en la evaluación y en el **RL**, que genera muchas muestras.
- Entrenar se paga una vez; la inferencia se paga **siempre**. Con agentes, los tokens generados pueden crecer sin límite.
- OpenAI procesa unos 8,6T tokens al día; DeepSeek v4 se entrenó con 32T.
- **Métricas:**
  - **TTFT:** tiempo hasta el primer token.
  - **Latencia:** segundos por token en una consulta.
  - **Rendimiento (throughput):** tokens por segundo sumando muchas consultas.
- **Motores:**
  - **vLLM** (PagedAttention; buena opción por defecto);
  - **SGLang** (RadixAttention; bueno para agentes);
  - TensorRT-LLM (NVIDIA);
  - **llama.cpp** (C++, corre en CPU y en local).

## Por qué la inferencia está limitada por memoria
- Una multiplicación de matrices X(B×D)·W(D×F) solo está limitada por cómputo si el batch es grande: en una H100, **B > 295**. Con B = 1 (matriz × vector) la intensidad es 1.
- **KV cache:** se guardan K y V de cada secuencia, token, capa y cabeza. Pasa de O(T³) a lo razonable.
- **Dos fases:**
  1. **Prefill** (procesar el prompt): en paralelo, **limitado por cómputo**.
  2. **Generación**, token a token: **limitada por memoria**.
- Intensidad aritmética:
  - MLP en prefill: B·S;
  - atención en prefill: S/2;
  - MLP en generación: B (necesita muchas consultas a la vez);
  - **atención en generación: menos de 1**, y no mejora con el batch porque cada secuencia tiene su propia KV cache.
- **Equilibrio:** un batch mayor da **mejor throughput y peor latencia** (más KV cache que leer). Usa batches pequeños en el prefill (mejor TTFT) y grandes en la generación.
- Paralelismo fácil: con M copias del modelo, la latencia es la misma y el throughput se multiplica por M.

## Reducir la KV cache sin perder precisión
- **GQA:** K grupos de K/V compartidos por N/K cabezas de query. La caché se divide por N/K. MHA (K=N) → GQA → MQA (K=1).
- **MLA** (DeepSeek v2): guarda un vector comprimido. Pasa de 16384 a **512 + 64** dimensiones (las 64 son para RoPE). Es incluso **un poco mejor que MHA**.
- **CLA:** compartir K/V entre **capas**.
- **Atención local (ventana deslizante):** la caché no depende de la longitud; se intercala con capas globales.
- **DeepSeek v4:** atención comprimida (CSA, HCA) y dispersa (DSA top-k). Soporta un millón de tokens de contexto.
- Otras vías: atención lineal o SSM (Mamba 2, GDN) y modelos de difusión.

## Atajos con pérdida
- **Cuantización:** bf16 es lo estándar en inferencia; fp8, int8 o int4 son más baratos y menos precisos.
  - **QAT:** el entrenamiento simula la cuantización. Es caro.
  - **PTQ:** cuantización después de entrenar. Es barato.
  - **AWQ:** mantiene en alta precisión el 0,1-1 % de los pesos que tocan las activaciones grandes. De fp16 a int3: 4× menos memoria y 3,2× más velocidad.
  - **GPTQ:** usa la Hessiana para compensar el error.
- **Poda + destilación:** quitar capas, cabezas o dimensiones poco importantes (se miden con unas 1024 muestras) y luego destilar el modelo original en el podado (NVIDIA).

## Atajos que se verifican (sin pérdida)
- **Decodificación especulativa:** un modelo "borrador" barato propone unos 4 tokens y el modelo grande los **verifica en paralelo** (como un prefill).
  - Es muestreo por rechazo modificado: **la muestra es exactamente la del modelo grande.**
  - Combinaciones típicas: 70B con borrador de 8B, u 8B con borrador de 1B.
  - Variantes: Medusa y EAGLE.

## Cargas dinámicas
- **Continuous batching:** las peticiones llegan y terminan en momentos distintos. Se planifica **paso a paso** y se añaden peticiones sobre la marcha. Con *selective batching*, la atención va por secuencia y el resto se concatena.
- **PagedAttention (vLLM):** la KV cache se divide en **bloques no contiguos**, como la paginación de un sistema operativo.
  - Evita la fragmentación.
  - Permite **compartir prefijos**, como el prompt de sistema o varias muestras, con *copy-on-write*.

## Ideas clave
- La inferencia está limitada por memoria y es dinámica.
- Las palancas son la arquitectura, la cuantización, la poda o destilación y la especulación.
- Las ideas vienen de sistemas: ejecución especulativa y paginación.
- Muy relevante para [[Brainus - Plan|montar tu propia IA]]: llama.cpp u Ollama con un modelo cuantizado para correrlo en local.
