---
curso: "[[CS336 - Índice]]"
clase: 16
tema: RL con recompensas verificables (PPO → GRPO; DeepSeek R1, Kimi 1.5, Qwen 3)
video: https://www.youtube.com/watch?v=dIFAi87Ws4E
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_16.pdf
tags: [cs336, rlvr, grpo, ppo, razonamiento, deepseek-r1, kimi, qwen3]
---

# Clase 16: Post-training con RLVR (RL con recompensas verificables)

Preentrenamiento + RLHF llevan a un GPT-3.5. **Esta clase llega hasta o1/R1** (modelos de razonamiento).
- El RLHF no escala bien por la **sobreoptimización**.
- La solución es aplicar RL en dominios donde se puede **verificar** la respuesta: matemáticas, código con tests. Ahí se optimiza exactamente lo que se quiere.

## De PPO a GRPO
- **PPO en LMs:** las acciones son tokens y la recompensa llega al final. Se añade una penalización KL por token frente a la referencia. Ventajas con GAE (en este problema tipo *bandit*, γ = λ = 1 funciona).
  - Problemas: implementación compleja, y el **modelo de valor** consume mucha memoria y hay que ajustarlo.
- **¿Por qué no DPO?** Los datos no vienen en pares y es *offline*.
- **GRPO (Group Relative Policy Optimization):**
  - es PPO **sin función de valor**;
  - para cada prompt se generan **G respuestas** y la **ventaja = z-score de la recompensa dentro del grupo**: (r − media) / desviación;
  - muy sencillo: hay implementaciones mínimas como `nano-aha-moment`.
  - Pasos: recompensa por muestra → normalizar por grupo → término KL → gradiente.
- **Defectos de GRPO** (artículo "Dr. GRPO", Liu 2025):
  - dividir entre la desviación **no es una línea base válida** (introduce sesgo) y da más peso a las preguntas demasiado fáciles o difíciles;
  - la normalización por longitud provoca **sesgo de longitud**: las respuestas incorrectas se alargan;
  - la versión corregida se acerca a REINFORCE con *leave-one-out*.

## Casos reales
### DeepSeek R1
- Superó a o1 con una receta **abierta y sencilla**. Acabó con las especulaciones de que hacían falta MCTS o PRMs: los dos están en su sección de "intentos fallidos".
- **R1-Zero:** GRPO directo sobre DeepSeek-V3, con recompensas de **acierto** y de **formato** (etiquetas de pensamiento).
  - Las cadenas de razonamiento se alargan durante el entrenamiento.
  - Aparece un "momento ajá", aunque posiblemente exagerado: el modelo base ya lo tenía y la longitud puede venir del sesgo del objetivo.
- **R1 completo:**
  1. SFT con cadenas largas de razonamiento (unas **1000 muestras** bastan para arrancar).
  2. GRPO + recompensa de **consistencia de idioma** (el RL tiende a mezclar idiomas).
  3. SFT general (600.000 de razonamiento con V3 como juez + 200.000 de otro tipo).
  4. RLHF.
- **Destilación:** R1 genera 800.000 trazas con las que se enseña a razonar a Qwen 2.5.

### Kimi K1.5
- **Curación:** se excluyen las preguntas tipo test o verdadero/falso (falsos positivos) y se dejan solo las que el modelo **falla con best-of-8**.
- **RL:** derivado al estilo DPO; policy gradient con línea base y pérdida cuadrática.
- **Control de longitud:** las respuestas correctas se incentivan a ser cortas. Se activa tarde porque afecta al rendimiento.
- **Currículo:** de fácil a difícil, muestreando con probabilidad proporcional a (1 − tasa de acierto).
- **Recompensas:** para código, nuevos tests generados; para matemáticas, un modelo de recompensa que comprueba si dos respuestas equivalen (800.000 muestras).
- **Infraestructura de RL:** los *rollouts* son inferencia lenta, se cambia entre frameworks, y las cadenas largas desequilibran los batches.

### Qwen 3
- Filtrado por dificultad con best-of-n. Se quitan las preguntas que acierta sin razonar y las parecidas a la validación.
- **GRPO con solo 3995 ejemplos.**
- **Fusión de modos:** mezcla datos con y sin razonamiento usando etiquetas, para controlar la longitud del razonamiento.
- El RLHF general **baja un poco** matemáticas y STEM.
- **Qwen 3 Coder Next (RL agéntico):**
  - mid-training con 600B tokens a nivel de repositorio, PRs con contexto recuperado y trayectorias de agentes;
  - modelos expertos (web, UX, SWE) que luego se destilan;
  - **800.000 entornos tipo SWE-bench** generados automáticamente.

## Ideas clave
- La sobreoptimización se evita con **RL en dominios verificables**.
- **GRPO** es simple (con defectos) y hace posible el RLVR.
- Recetas probadas: R1, Kimi 1.5 y Qwen 3.
- Antes: [[Clase 15 - Mid y post-training]].
