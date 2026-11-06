---
curso: "[[CS336 - Índice]]"
clase: 11
tema: Leyes de escala en la práctica (MiniCPM, DeepSeek, WSD, muP, Muon)
video: https://www.youtube.com/watch?v=vTfEyOyzV9E
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_11.pdf
tags: [cs336, leyes-de-escala, mup, wsd, muon, learning-rate, batch]
---

# Clase 11: Leyes de escala en detalle

**Preguntas:**
- ¿Funciona de verdad la receta de Chinchilla?
- ¿Se puede ahorrar cómputo al ajustar las leyes?
- ¿Conviene elegir parametrizaciones que escalen bien?

## Casos reales
### MiniCPM (2024, Tsinghua): modelos de 1 a 2,5B que igualan a muchos de 7B
- **muP** para estabilizar el escalado: se fija la proporción ancho/profundidad y se escala el tamaño. Con muP el LR óptimo se mantiene casi constante.
- **Batch óptimo:** crece de forma polinómica a medida que baja la pérdida, como decía Kaplan.
- **LR WSD (Warmup-Stable-Decay)** en lugar del coseno:
  - fase estable larga y caída final (~10 %) en la que la pérdida baja de golpe;
  - permite **reutilizar una ejecución** para varios presupuestos de datos, relanzando la caída desde la fase estable;
  - así el coste del barrido de Chinchilla pasa de n² a ~n.
- Resultado: ratios datos/modelo **muy altos**.

### DeepSeek (7B y 67B)
- Sin muP: estiman directamente **el batch y el LR óptimos** con barridos pequeños (modelos a menos del 0,25 % del mínimo).
- LR estilo WSD: warmup rápido y dos caídas del 10 %.
- **IsoFLOPs** (método 2 de Chinchilla) para elegir el tamaño. Las predicciones aciertan la pérdida final.

### Otros
| Modelo | Qué hizo |
|---|---|
| Qwen 2.5 / 3 | ajustes de LR y batch frente a la escala |
| Kimi K2 | ley de escala de **dispersión** (MoE) |
| Hunyuan | IsoFLOPs para MoE: **96 tokens por parámetro activo** |
| Llama 3 | IsoFLOPs (**~39:1**) + escalado de cómputo a tareas concretas |
| MiniMax-01 | leyes de escala de **arquitectura** |

## Dos recetas resumidas
- **DeepSeek:** asume que casi todos los hiperparámetros no dependen de la escala, ajusta LR y batch con una ley de escala, elige el tamaño con IsoFLOPs y usa WSD para abaratar.
- **MiniCPM:** usa muP para que arquitectura y LR no dependan de la escala, y WSD para obtener los puntos del método 3.

## Optimizadores y escala
- **StepFun** hizo una búsqueda empírica por rejilla de LR y batch:
  - la pérdida es **convexa** en LR y batch, así que los óptimos son claros;
  - **el batch óptimo depende sobre todo del tamaño del dataset**.
- Cuidado al comparar optimizadores:
  - cada uno necesita sus propios hiperparámetros;
  - las ventajas dependen mucho de la escala;
  - **compara siempre frente al cómputo y al ratio de Chinchilla**;
  - un escalado que parece bueno puede "explotar" a mayor tamaño.
- **Muon:** optimizador para parámetros matriciales que **ortogonaliza** la actualización con Newton-Schulz (B = USVᵀ → UVᵀ). Brilla en el NanoGPT speedrun y funciona a gran escala (Kimi K2).

## muP (Maximal Update Parametrization) explicado
- **Objetivo:** que el LR y la inicialización óptimos **se transfieran** al aumentar el ancho.
- **Supuestos:**
  - A1: las activaciones al inicializar son Θ(1);
  - A2: tras un paso de gradiente, el cambio en las activaciones también es Θ(1).
- **Resultado** para capas de ancho n_entrada → n_salida:
  - inicialización con desviación ~ (1/√n_entrada)·min(1, √(n_salida/n_entrada));
  - LR con Adam ~ **1/n_entrada**.
  - La parametrización estándar usa 1/√n_entrada y LR Θ(1).
- **Dónde falla:**
  - ganancias aprendibles en RMSNorm (se pueden quitar con poca pérdida);
  - optimizadores exóticos basados en signos (Lion);
  - **weight decay fuerte (0,1)**, el fallo más serio.
- Aun así es útil: la parametrización estándar es más inestable (CerebrasGPT lo confirma).

## Ideas clave
Los retos prácticos son tres: fijar la arquitectura, fijar LR y batch, y el cómputo para el barrido de Chinchilla. Las soluciones son, respectivamente:
1. asumir estabilidad o usar muP;
2. buscar LR y batch a escala pequeña y extrapolar;
3. usar WSD.

Base: [[Clase 09 - Leyes de escala]].
