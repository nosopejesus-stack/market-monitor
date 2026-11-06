---
tipo: indice
curso: Stanford CS336 - Language Modeling from Scratch (primavera 2026)
web: https://cs336.stanford.edu/
youtube: buscar "Stanford CS336" (canal Stanford Online)
material: https://github.com/stanford-cs336/lectures
tags: [cs336, indice, curso]
---

# CS336: Crear tu propio modelo de lenguaje desde cero

Curso gratuito de Stanford recomendado por @midudev ([[Videos - Aprendizaje de los 3 TikToks]]).
Las notas salen del **material oficial de cada clase**: el código narrado (`lecture_XX.py`) y las diapositivas (`lecture_XX.pdf`) del repo `stanford-cs336/lectures`.
No vienen del audio: YouTube bloquea las descargas desde servidores en la nube.

## Idea central del curso
> Todo gira en torno a la **eficiencia**: ¿cuál es el mejor modelo posible con un presupuesto fijo de cómputo y datos?
> Filosofía: **entender construyendo**. `precisión = eficiencia × recursos`.

## Clases
| # | Clase | Bloque |
|---|---|---|
| 1 | [[Clase 01 - Panorama y tokenización]] | Básico |
| 2 | [[Clase 02 - PyTorch, einops y contabilidad de recursos]] | Básico |
| 3 | [[Clase 03 - Arquitecturas]] | Básico |
| 4 | [[Clase 04 - Alternativas a la atención y MoE]] | Básico |
| 5 | [[Clase 05 - GPUs y TPUs]] | Sistemas |
| 6 | [[Clase 06 - Kernels, Triton y XLA]] | Sistemas |
| 7 | [[Clase 07 - Paralelismo]] | Sistemas |
| 8 | [[Clase 08 - Paralelismo (parte 2)]] | Sistemas |
| 9 | [[Clase 09 - Leyes de escala]] | Escalado |
| 10 | [[Clase 10 - Inferencia]] | Sistemas |
| 11 | [[Clase 11 - Leyes de escala (detalles)]] | Escalado |
| 12 | [[Clase 12 - Evaluación]] | Datos |
| 13 | [[Clase 13 - Datos (fuentes y datasets)]] | Datos |
| 14 | [[Clase 14 - Datos (filtrado y deduplicación)]] | Datos |
| 15 | [[Clase 15 - Mid y post-training]] | Alineamiento |
| 16 | [[Clase 16 - Post-training con RLVR]] | Alineamiento |
| 17 | [[Clase 17 - Multimodalidad]] | Extra |
| — | Charla invitada: Dan Fu ([video](https://www.youtube.com/watch?v=9EEm4iMAF5s)) | sin material publicado; pendiente |

## Las 5 tareas
1. **Básico:** tokenizador BPE, Transformer, AdamW y entrenamiento con TinyStories y OpenWebText. Ya descargada en la sesión de Claude Code: `cs336-assignment1`.
2. **Sistemas:** RMSNorm en Triton, DDP y *sharding* del optimizador.
3. **Leyes de escala:** ajustarlas con un presupuesto de FLOPs.
4. **Datos:** HTML a texto, clasificadores y MinHash.
5. **Alineamiento:** DPO y GRPO.

## Resumen en 10 frases
1. Un **tokenizador BPE** fusiona los pares de bytes más frecuentes. La compresión importa porque la atención es cuadrática.
2. Entrenar cuesta **≈ 6·N·D FLOPs** (N = parámetros, D = tokens).
3. El Transformer moderno usa **pre-norm, RMSNorm, RoPE, SwiGLU y sin bias**; con `d_ff ≈ 8/3·d_model`.
4. Los **MoE** añaden parámetros sin añadir FLOPs; los **híbridos** lineales + atención sirven para contexto largo.
5. La GPU está casi siempre **limitada por la memoria**: tiling, fusión y baja precisión son las claves (FlashAttention).
6. Para entrenar en muchas GPUs se combinan paralelismo de **datos (ZeRO/FSDP) + tensor (≤ 8) + pipeline + expertos**.
7. **Leyes de escala:** se ajustan en pequeño y se extrapola. **Chinchilla ≈ 20 tokens por parámetro**, pero conviene sobre-entrenar por el coste de la inferencia.
8. La **inferencia** está limitada por memoria: KV cache, GQA/MLA, cuantización, decodificación especulativa y PagedAttention.
9. **Los datos son lo más importante:** filtrar con clasificadores, deduplicar con MinHash y mezclar con cuidado de no repetir demasiadas épocas.
10. **Post-training:** SFT (extrae, no añade conocimiento) → RLHF/DPO → **RLVR con GRPO** (razonamiento tipo R1).

## Relación con [[Brainus - Plan]]
El curso enseña a crear un modelo **desde cero**, y eso exige GPUs y millones de dólares para llegar a la frontera.
El camino práctico para tener **tu propia IA funcionando** es otro:
- usar un modelo abierto ya entrenado (Qwen, Llama, Gemma) en local;
- darle tu **memoria** (esta bóveda) con RAG;
- más adelante, **afinarlo** con tus datos (SFT, [[Clase 15 - Mid y post-training]]).
