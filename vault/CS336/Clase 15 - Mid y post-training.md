---
curso: "[[CS336 - Índice]]"
clase: 15
tema: Después del preentrenamiento (SFT, mid-training, RLHF, PPO, DPO)
video: https://www.youtube.com/watch?v=2oH6PWPrYFo
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_15.pdf
tags: [cs336, sft, rlhf, dpo, ppo, post-training, instruction-tuning]
---

# Clase 15: Mid-training y post-training (SFT + RLHF)

El preentrenamiento llega hasta un GPT-3. **¿Cómo se pasa a InstructGPT o ChatGPT?**
Seguir instrucciones es una forma notable de **control**. La receta estándar es **imitar (SFT) y luego reforzar (RLHF)**.

## Parte 1: SFT (Supervised Fine-Tuning)
### Cómo han evolucionado los datos abiertos
FLAN → Self-Instruct → **Alpaca** → ShareGPT/Vicuna → OpenAssistant → WizardLM → **Tulu 3** → Nemotron (con **uso de herramientas y agentes**).
- FLAN son tareas de benchmark: válidas, pero nadie quiere hablar con un benchmark.
- Los datasets posteriores son más **conversacionales**, largos y detallados.
- Los recientes incluyen **llamadas a herramientas**, listas de tareas y lectura de AGENTS.md.

### Qué importa
- **Estilo:** la longitud y las viñetas pesan mucho en las evaluaciones por preferencia, de humanos o de GPT-4, pero apenas en los benchmarks.
- **Conocimiento:**
  - afinar con **hechos que el modelo no sabe** le enseña a **alucinar** (Schulman, Gekhman);
  - mejor no hacer SFT con conocimiento de "cola larga";
  - el RL con feedback de corrección podría ayudar.
- **Seguridad:** basta poca cantidad. Con unos **500 ejemplos** mejora mucho; Llama 2 usó unos pocos miles.

**Conclusiones sobre SFT:**
1. Funciona mejor cuando **extrae** comportamientos que ya estaban en el preentrenamiento, no cuando añade nuevos.
2. Añadir datos, aunque sean correctos, a veces empeora el modelo.
3. Poca cantidad del tipo correcto (seguridad, instrucciones, estilo) cambia mucho, aunque hay una cola larga que se beneficia de más datos.

### Mid-training (entrenamiento en dos fases)
1. Preentrenar con la web.
2. **Mezclar datos de instrucciones dentro del preentrenamiento.**
3. Hacer una ronda corta de SFT.

Permite escalar el instruction tuning **sin olvido catastrófico**. Casi todos lo hacen; MiniCPM y JetMoE lo documentaron.

## Parte 2: RLHF
- **Imitar** = ajustar p(y|x) a una distribución de referencia.
- **Optimizar** = maximizar E[R(y, x)]: el LM pasa a ser una **política**.
- **Por qué optimizar:** la brecha entre generar y verificar. A la gente le cuesta **escribir** lo que luego **prefiere** leer.

### Datos de preferencia
- Comparaciones por pares, con guías de anotación (InstructGPT, Bard).
- Crowdsourcing: cuesta conseguir anotadores fiables, hay dilemas éticos y el **perfil demográfico de los anotadores cambia el comportamiento** del modelo.
- **Feedback de IA:** GPT-4 como juez se acerca al acuerdo entre humanos. Datasets: UltraFeedback, Zephyr, Tulu 3. Constitutional AI (Anthropic) usa autocrítica.
- **Efecto longitud:** el RLHF alarga mucho las respuestas.

### Algoritmos
- **PPO:**
  - policy gradient → TRPO → **PPO**, que recorta el ratio entre políticas;
  - necesita un modelo de recompensa y un modelo de valor;
  - es delicado de ajustar.
- **DPO (Direct Preference Optimization):**
  - sin modelo de recompensa y sin *rollouts*;
  - derivación: suponiendo una política no paramétrica, la recompensa implícita es `β·log(π/π_ref)`, y se optimiza con una pérdida supervisada sobre los pares;
  - en la práctica: **subir la probabilidad de lo bueno y bajar la de lo malo**, ponderado por el error;
  - lo usan Llama y muchos modelos abiertos;
  - variantes: SimPO (sin referencia) y DPO normalizado por longitud.
- Los resultados de RL **dependen mucho del montaje**: a veces PPO gana.

### Riesgos
- **Sobreoptimización:** pasado un punto, maximizar la recompensa empeora el modelo, con preferencias humanas o de LM con ruido.
- **Colapso de modos:** tras el RLHF el modelo pierde la **calibración**; deja de ser un modelo probabilístico.

## Ideas clave
- Recoger datos de RLHF es difícil y está lleno de factores de confusión.
- Los algoritmos son más complejos que el SFT, sobre todo PPO.
- Hay que vigilar la sobreoptimización.
- En la tarea 5 se implementan **DPO y GRPO**.
- Siguiente: [[Clase 16 - Post-training con RLVR]].
