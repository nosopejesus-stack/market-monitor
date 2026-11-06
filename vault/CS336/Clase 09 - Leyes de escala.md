---
curso: "[[CS336 - Índice]]"
clase: 9
tema: Leyes de escala básicas (datos, modelo, cómputo, Chinchilla)
video: https://www.youtube.com/watch?v=Q15rhEWZPQ4
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_09.pdf
tags: [cs336, leyes-de-escala, chinchilla, kaplan, isoflop, hiperparametros]
---

# Clase 09: Leyes de escala

**Escenario:** te regalan 10.000 B200 durante un mes para crear un buen LM abierto.
- La infraestructura sale de la tarea 2 y los datos de la tarea 4.
- Queda la pregunta: **¿qué modelo entrenas?**
- Antes se ajustaban hiperparámetros en el modelo grande, lo que es carísimo. Ahora se **ajustan en modelos pequeños y se extrapola**.

## Leyes de escala de datos
- El error frente al tamaño del dataset es una **recta en escala log-log**: una ley de potencias, "sin escala".
- **Por qué:** el error de estimación cae de forma polinómica.
  - Ejemplo: estimar una media tiene error σ²/n, y `log(error) = −log n + cte`.
  - Los modelos clásicos dan pendiente −1; las redes neuronales dan pendientes **mucho menores**.
  - Explicación: el aprendizaje no paramétrico en d dimensiones tiene error ~ n^(−1/d), y la pendiente estaría ligada a la **dimensión intrínseca** de los datos.
- La **composición** de los datos cambia el desplazamiento de la recta, no su pendiente. Por eso importa la diversidad.
- **Repetir datos:** las repeticiones valen cada vez menos (datos efectivos). La selección de datos debe **adaptarse a la escala**.

## Leyes de escala para diseñar modelos
- Transformer frente a LSTM, Adam frente a SGD, profundidad: se comparan **curvas de escalado** en lugar de entrenar el modelo gigante.
- Pasar de 1 a 2 capas importa mucho; más capas tienen rendimientos decrecientes.
- Los parámetros de *embedding* no cuentan igual que el resto.
- **Batch crítico:** a partir de cierto tamaño de batch, los rendimientos caen. Cuanto más baja es la pérdida objetivo, **mayor es el batch crítico**.
- **Learning rate:** el óptimo depende de la escala. **muP** da una inicialización y unos LR que se transfieren entre escalas.
- Cuidado: el rendimiento en tareas concretas (*downstream*) escala de forma **menos predecible** que la pérdida.

**Procedimiento:**
1. Entrena varios modelos pequeños.
2. Ajusta una ley de escala.
3. Elige los hiperparámetros con su predicción.

## ¿Más datos o modelo más grande?
- Ley conjunta: `Error = n^(−α) + m^(−β) + C` (Rosenfeld; Kaplan).
- **Kaplan (2020):** N_opt ∝ C^0,73 y D_opt ∝ C^0,27, es decir, priorizar el modelo.
- **Chinchilla (Hoffmann 2022)** lo corrige con tres métodos:
  1. mínimo sobre todas las curvas de entrenamiento;
  2. **IsoFLOPs**: para cada presupuesto se varía N, y los mínimos siguen una ley de potencias;
  3. ajuste conjunto. Este método tenía errores; un reanálisis posterior lo corrigió.
- **Resultado: unos 20 tokens por parámetro.** C ≈ 6·N·D.
- La discrepancia con Kaplan vino de contar o no los parámetros de *embedding* y de un *warmup* mal ajustado en presupuestos pequeños.

## Lo óptimo para entrenar no es lo que quieres
Lo que más cuesta de un modelo desplegado es la **inferencia**, así que conviene **sobre-entrenar** modelos más pequeños:

| Modelo | Tokens por parámetro |
|---|---|
| GPT-3 | 2 |
| Chinchilla | 20 |
| LLaMA 65B | 22 |
| Llama 2 70B | 29 |
| Mistral 7B | 110 |
| Llama 3 70B | 215 |

## Ideas clave
- Las leyes de escala permiten **predecir la pérdida antes de entrenar** y elegir arquitectura, optimizador y tamaños con poco cómputo.
- Son **cotas inferiores**: aplicarlas a ciegas puede fallar.
- Continúa en [[Clase 11 - Leyes de escala (detalles)]]. En la tarea 3 se ajustan leyes de escala con un presupuesto de FLOPs.
