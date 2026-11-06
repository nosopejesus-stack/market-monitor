---
curso: "[[CS336 - Índice]]"
clase: 1
tema: Panorama del curso y tokenización
video: https://www.youtube.com/watch?v=JuoVZkPBiKk
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_01.py
tags: [cs336, tokenizacion, bpe, fundamentos]
---

# Clase 01: Panorama y tokenización

## Por qué existe el curso
- Los investigadores se están **desconectando** de la tecnología: en 2016 entrenaban sus modelos, en 2018 descargaban BERT y lo afinaban, y hoy hacen *prompts* a modelos por API.
- Esas abstracciones "gotean": para investigar de verdad hay que entender toda la pila.
- Filosofía: **entender construyendo**.
- Lo que se transfiere a modelos de frontera:
  - **Mecánica:** qué es un Transformer, cómo funciona el paralelismo. Se enseña bien.
  - **Mentalidad:** exprimir el hardware y tomarse en serio el escalado. Se enseña bien.
  - **Intuiciones:** qué datos y decisiones dan buena precisión. Solo en parte; no siempre se transfieren entre escalas.

## La lección amarga (bien entendida)
- Interpretación errónea: "solo importa la escala".
- Interpretación correcta: **importan los algoritmos que escalan**.
- `precisión = eficiencia × recursos`. La eficiencia importa todavía más a gran escala.
- Pregunta central del curso: ¿cuál es el mejor modelo posible con un presupuesto dado de cómputo y datos?

## Historia rápida
- **Pre-neural:** Shannon mide la entropía del inglés; modelos de n-gramas.
- **Ingredientes neuronales (años 2010):** LSTM, seq2seq, Adam, atención, Transformer (2017), *mixture of experts*, paralelismo de modelos.
- **Primeros modelos fundacionales:** ELMo, BERT, T5, GPT-2.
- **Escalado:** leyes de escala (Kaplan), GPT-3 (aprendizaje en contexto), PaLM y Chinchilla (escalado óptimo en cómputo).
- **Modelos abiertos:** Llama, Mistral, DeepSeek, Qwen, Kimi, GLM, OLMo (abierto del todo: pesos, código y datos), Marin.
- Evolución de qué es un LM: 2018 algo que afinas → 2020 algo a lo que le haces *prompts* → 2022 algo con lo que conversas → 2026 **agentes** que actúan solos.

## Estructura del curso (5 tareas)
1. **Básico:** [[Clase 01 - Panorama y tokenización|tokenizador BPE]], Transformer, *cross-entropy*, AdamW y bucle de entrenamiento. Se entrena con TinyStories y OpenWebText.
2. **Sistemas:** kernel RMSNorm en Triton, entrenamiento distribuido y *sharding* del optimizador. Ver [[Clase 05 - GPUs y TPUs]], [[Clase 06 - Kernels, Triton y XLA]] y [[Clase 07 - Paralelismo]].
3. **Leyes de escala:** ajustar curvas con experimentos pequeños y predecir el resultado grande. Ver [[Clase 09 - Leyes de escala]].
4. **Datos:** HTML de Common Crawl → texto, clasificadores de calidad, deduplicación con MinHash. Ver [[Clase 13 - Datos (fuentes y datasets)]].
5. **Alineamiento:** DPO, GRPO y PPO. Ver [[Clase 15 - Mid y post-training]] y [[Clase 16 - Post-training con RLVR]].

Principio general: equilibrar **expresividad**, **estabilidad** y **eficiencia**.
Hoy el límite es el cómputo; mañana lo serán los datos.

## Tokenización
- Un **tokenizador** convierte texto (bytes) ↔ secuencias de enteros (tokens).
- **Ratio de compresión** = bytes por token. Cuanto mayor, más cortas las secuencias, y eso importa porque la atención es cuadrática en la longitud.

| Enfoque | Vocabulario | Compresión | Problema |
|---|---|---|---|
| Caracteres (Unicode) | ~150K | baja | vocabulario enorme, caracteres raros desperdiciados |
| Bytes (UTF-8) | 256 | 1 byte/token, malísima | secuencias larguísimas |
| Palabras | enorme, abierto | buena | palabras raras, token `UNK` |
| **BPE** | fijo, se elige | buena | heurístico, pero funciona |

### BPE (Byte Pair Encoding)
1. Empieza con cada byte como token.
2. Cuenta los pares adyacentes más frecuentes.
3. Fusiona el par más común en un token nuevo.
4. Repite hasta llegar al tamaño de vocabulario deseado.

- Gage lo inventó en 1994 para compresión; Sennrich lo llevó a la traducción automática en 2016; GPT-2 lo popularizó.
- En la tarea 1 hay que hacerlo rápido, conservar tokens especiales (`<|endoftext|>`) y usar pre-tokenización con la regex de GPT-2.
- Observaciones con el tokenizador de GPT-5:
  - el espacio va pegado a la palabra (`" world"`);
  - la misma palabra se tokeniza distinto al inicio y en medio de la frase;
  - los números se parten cada pocos dígitos.
- El sueño: modelos **sin tokenizador** que trabajen sobre bytes (MegaByte, BLT, H-Net). Aún no han llegado a la frontera.

## Ideas clave
- Todo el curso gira en torno a la **eficiencia** con recursos fijos.
- La tokenización es un paso aparte que algún día podría aprenderse de extremo a extremo.
- Recomendado: el video de Andrej Karpathy sobre tokenización.
