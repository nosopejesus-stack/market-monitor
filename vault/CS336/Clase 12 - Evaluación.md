---
curso: "[[CS336 - Índice]]"
clase: 12
tema: Evaluación de modelos de lenguaje (perplejidad, exámenes, chat, agentes, seguridad, validez)
video: https://www.youtube.com/watch?v=JpAxdTWQJxM
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_12.py
tags: [cs336, evaluacion, benchmarks, agentes, perplejidad, llm-judge]
---

# Clase 12: Evaluación

**Reto central:** convertir un concepto abstracto ("¿es bueno?") en una **métrica concreta**. ¿Es bueno si saca nota en benchmarks? ¿Si además es barato? ¿Si la gente prefiere sus respuestas? ¿Si la gente lo usa y paga por él?

**Lecciones:**
- No existe **una** evaluación verdadera: depende de lo que quieras medir.
- Hay que dejar claras las reglas del juego: ¿se evalúan métodos, modelos o agentes?
- Hay que fijarse en la dificultad, el realismo y la validez.

## 1. Perplejidad
- `PPL = (1/p(D))^(1/|D|)`. Es lo que se minimiza al preentrenar.
- Datasets clásicos: Penn Treebank, WikiText-103, One Billion Word. GPT-2 se evaluó **zero-shot** fuera de su distribución.
- "La perplejidad es todo lo que necesitas": si p = distribución real, se resuelven todas las tareas. Pero penaliza tokens irrelevantes; mejor usar **perplejidad condicional** p(respuesta | prompt).
- Algunos benchmarks son perplejidad disfrazada: LAMBADA (rellenar huecos), HellaSwag.
- Sigue siendo **muy usada en el desarrollo** porque escala de forma suave.

## 2. Exámenes
| Benchmark | Qué es |
|---|---|
| **MMLU** | 57 materias tipo test; mide **conocimiento** |
| MMLU-Pro | 10 opciones, sin preguntas triviales, con cadena de razonamiento; los modelos bajan entre un 16 y un 33 % |
| **GPQA** | preguntas de nivel doctorado "a prueba de Google": los expertos aciertan el 65 %, los no expertos con Google el 34 %, GPT-4 el 39 % |
| **HLE** (Humanity's Last Exam) | 2500 preguntas multimodales, filtradas con LLMs de frontera; 500.000 $ en premios |

La tendencia: preguntas cada vez más difíciles a medida que los benchmarks se saturan. Pero no reflejan el uso real.

## 3. Chat (respuestas abiertas)
- **Chatbot Arena:** personas comparan dos modelos anónimos y se calcula un **ELO**. Usa prompts reales y es dinámico, pero tiene sesgos: ¿quién vota?, mezcla estilo con corrección, favorece la complacencia.
- **AlpacaEval:** GPT-4 como juez. Los jueces LLM **prefieren respuestas largas**, así que la versión 2.0 corrige con regresión.
- **WildBench:** 1024 conversaciones reales, un juez con **checklist**; correlaciona bien con Arena.
- Lecciones:
  - las comparaciones por pares dan más señal;
  - cuidado con los sesgos de humanos y de jueces LLM;
  - **las rúbricas y checklists mejoran la fiabilidad**.

## 4. Agentes (evaluar lo que *hacen*)
- **Agente = LM + andamiaje** (la lógica que decide cómo usarlo).
- **SWE-Bench:** 2294 issues de 12 repos Python; el agente envía un PR y lo validan los tests.
- **Terminal-Bench:** tareas en terminal (la 2.0 tiene 89).
- **CyBench:** 40 retos de ciberseguridad tipo CTF.
- **MLE-Bench:** 75 competiciones de Kaggle.
- **Técnicas de andamiaje:**
  - lista de tareas explícita;
  - **delegación jerárquica**: subagentes con contexto limpio;
  - **memoria persistente en archivos** (justo lo que hacemos con Obsidian, ver [[Brainus - Plan]]);
  - mucha ingeniería de contexto.
- Evaluar un agente es evaluar **andamiaje + modelo**.

## 5. Razonamiento puro
- **ARC-AGI:** separa el razonamiento del conocimiento. Cada tarea es única, así que memorizar no sirve.
- Versiones: v1 (2019), v2 (2025), **v3 (marzo de 2026), con entornos interactivos**.
- Los LMs preentrenados no avanzaron aquí; los modelos de razonamiento (o1, o3) sí.

## 6. Seguridad
- **HarmBench** (510 comportamientos dañinos) y **AIR-Bench** (314 categorías de riesgo, 5694 prompts).
- *Jailbreaks*: **GCG** optimiza prompts automáticamente y estos se transfieren de modelos abiertos a cerrados.
- La seguridad depende mucho del contexto. **Doble uso:** un agente de ciberseguridad sirve para atacar o para auditar.

## 7. Realismo y validez
- **Validez ecológica:**
  - GDPVal (OpenAI): 44 ocupaciones con tareas de profesionales;
  - MedHELM: 121 tareas clínicas;
  - Clio (Anthropic): analiza el uso real preservando la privacidad.
- **Solapamiento entre entrenamiento y test** (hoy se entrena con internet). Soluciones:
  - inferirlo a partir del modelo;
  - normas de reporte;
  - **evaluaciones frescas** (LiveCodeBench);
  - **evaluaciones privadas**, por ejemplo con tus propios escritos.
- **Calidad del dataset:** SWE-Bench Verified, versiones "Platinum", y **Docent**, que usa un LLM para inspeccionar las trazas de los agentes.

## Ideas clave
- Elige la evaluación según la pregunta: decisión de compra, capacidad bruta, riesgos o feedback para mejorar.
- Evaluar **métodos** (con datos y cómputo fijos, como el NanoGPT speedrun) fomenta la innovación; evaluar **sistemas** sirve a quien los usa.
- Siguiente: [[Clase 13 - Datos (fuentes y datasets)]].
