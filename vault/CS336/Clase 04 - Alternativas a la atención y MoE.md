---
curso: "[[CS336 - Índice]]"
clase: 4
tema: Alternativas a la atención (lineal, Mamba, GDN) y Mixture of Experts
profesor: Tatsunori Hashimoto
video: https://www.youtube.com/watch?v=cKSwj_qZ8Jg
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_04.pdf
tags: [cs336, atencion-lineal, mamba, moe, deepseek, contexto-largo]
---

# Clase 04: Alternativas a la atención y Mixture of Experts

## El problema
El coste de la atención crece de forma **cuadrática** con la longitud del contexto. Hay soluciones básicas (atención local + global, ingeniería de sistemas) y otras más radicales.

## Atención lineal y modelos recurrentes
- Si se quita el softmax: `(QKᵀ)V = Q(KᵀV)`. Pasa de O(n²·d) a **O(n·d²)**.
- **Forma recurrente:** `S_t = S_{t-1} + k_t v_tᵀ`, `y_t = q_tᵀ S_t`. Es como una RNN.
  - **Dualidad:** se entrena en forma paralela y se infiere en forma recurrente, con memoria constante.
  - Con un factor de decaimiento γ fijo sale RetNet.
- **Mamba-2:** γ_t depende de la entrada (una compuerta). "La compuerta es buena".
- **Gated DeltaNet (GDN):** añade β_t y **borra** del estado lo que hay en la dirección de la clave actual: `S_t = γ_t (I − β_t k_t k_tᵀ) S_{t-1} + β_t k_t v_tᵀ`.
- **Híbridos en producción:**
  - MiniMax M1: 7 capas lineales por cada capa completa.
  - Nemotron 3: Mamba + atención, aproximadamente 3:1.
  - **Qwen 3.5 / Qwen Next:** GDN + atención en proporción 3:1.
- **Atención dispersa (DSA)** de DeepSeek v3.2 y GLM-5: un "indexador" ligero elige qué tokens mirar. Se puede añadir después del preentrenamiento.

## Mixture of Experts (MoE)
- Se cambia la gran FFN por **muchas FFN (expertos)** más un **router** que elige unos pocos por token.
- Se pueden añadir expertos **sin aumentar los FLOPs** por token. Con los mismos FLOPs, más parámetros dan mejor modelo.
- Entrenan más rápido, compiten con los modelos densos y se paralelizan bien entre dispositivos.
- La mayoría de los mejores modelos abiertos son MoE: DeepSeek v3, Qwen, Mixtral, Llama 4 y probablemente GPT-4.
- **Pegas:** infraestructura compleja, objetivos de entrenamiento heurísticos y a veces inestables.

### Routing
- Casi todos usan **top-k "token elige experto"**: Switch k=1; Mixtral y Grok k=2; Qwen y DBRX k=4; DeepSeek k=7-8.
- **Expertos finos + expertos compartidos** siempre activos (DeepSeek, Qwen). DeepSeek v3 tiene 256 expertos enrutados, 8 activos y 1 compartido.
- Las decisiones discretas no son diferenciables. Opciones: RL (funciona pero es complejo), ruido estocástico o, lo que de verdad se usa, **pérdidas heurísticas de balanceo**.
  - **Balanceo** por experto y por dispositivo (Switch, DeepSeek v1-2).
  - DeepSeek v3: **"aux-loss-free"**, un sesgo por experto que se ajusta online.

### Problemas típicos
- **Estabilidad:** el router se calcula en fp32 y se usa z-loss en él.
- **Fine-tuning:** los MoE sobreajustan con pocos datos. Soluciones: afinar solo las MLP densas, o usar muchos datos (DeepSeek usó 1,4M ejemplos de SFT).
- **No determinismo:** el descarte de tokens se decide por batch, así que las consultas de otros usuarios pueden afectar a la tuya.
- **Upcycling:** inicializar un MoE a partir de un modelo denso ya entrenado (MiniCPM, Qwen MoE).

### La receta de DeepSeek v3 (671B totales, 37B activos)
- MoE con expertos finos y compartidos, router sigmoid y balanceo sin pérdida auxiliar.
- **MLA (Multi-head Latent Attention):** Q, K y V salen de un vector latente pequeño, y en la KV cache solo se guarda ese latente. Para no chocar con RoPE se dejan unas pocas dimensiones de K "rotables".
- **MTP (Multi-Token Prediction):** cabezas ligeras que predicen tokens futuros (DeepSeek predice uno más).

## Ideas clave
- Los MoE aprovechan la **dispersión**: no todas las entradas necesitan todo el modelo.
- Los híbridos (lineal + atención completa) son la apuesta actual para contextos largos.
- Relación: [[Clase 03 - Arquitecturas]] y [[Clase 07 - Paralelismo]] (paralelismo de expertos).
