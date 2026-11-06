---
curso: "[[CS336 - Índice]]"
clase: 14
tema: Datos II (transformación, filtrado, deduplicación, mezcla y datos de post-training)
video: https://www.youtube.com/watch?v=5sxHosTLPF8
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_14.py
tags: [cs336, datos, filtrado, minhash, deduplicacion, mezcla-de-datos, datos-sinteticos]
---

# Clase 14: Datos (filtrado, deduplicación y mezcla)

## 1. Transformación
- Los datos no llegan como texto: llegan como HTML, PDF o repositorios.
- **De HTML a texto:** quitar el *boilerplate* (menús, anuncios) y extraer el contenido. Siempre hay pérdida. Herramientas: trafilatura, resiliparse, jusText.
- **PDF** (FinePDFs): volver a descargar los PDF truncados, **OCR con modelos de visión** (RolmOCR, Docling) y mucha limpieza. La precisión importa.

## 2. Filtrado
**Esquema general:** con unos datos objetivo **T** ("cómo es lo bueno") y muchos datos en bruto **R**, encuentra el subconjunto de R que se parece a T. Debe **generalizar** y ser **rapidísimo**.

| Clasificador | Puntuación |
|---|---|
| Generativo (**KenLM**, n-gramas) | p_T(x) |
| Discriminativo (**fastText**) | p(T \| x) |

Se conservan los ejemplos con puntuación ≥ umbral, a veces de forma estocástica.

**Aplicaciones:**
- **Idioma:** fastText detecta 176 idiomas. Dolma se queda con p(inglés) ≥ 0,5.
- **Calidad:**
  - GPT-3: positivos de Wiki, WebText y libros frente a Common Crawl.
  - LLaMA: páginas **citadas** por Wikipedia.
  - **phi-1:** datos "de libro de texto" + sintéticos de GPT. Un modelo de 1,3B mejora de 12 % a **17,7 % en HumanEval** con menos pasos.
- **Dominio:** OpenWebMath combina reglas (LaTeX), KenLM y fastText. Con 14,7B tokens, sus modelos superan a otros entrenados con **20× más datos**.
- **Toxicidad:** el dataset Jigsaw (comentarios de Wikipedia).

**El efecto depende de la escala:** no hay un umbral óptimo único.
- Si vas a entrenar más tiempo, quieres **más datos** (aunque sean peores).
- Si vas a entrenar poco, quieres **menos datos y mejores**.

## 3. Deduplicación
- Hay duplicados exactos (mirrors, forks) y **casi duplicados** (plantillas, copias con cambios de formato). En C4, una descripción de producto aparecía **61.036 veces**.
- Deduplicar permite entrenar más eficientemente y **memorizar menos** (mitiga problemas de copyright y privacidad).
- Decisiones de diseño:
  - qué es un elemento: frase, párrafo o documento;
  - cómo se compara: exacto, subelemento común o fracción común;
  - qué se hace: borrar todos o dejar uno.
- **Hashes:** SHA-256 resiste colisiones pero es lento; MurmurHash es rápido.
- **Exacta:** con MapReduce. C4 usa tramos de 3 frases (cuidado, puede romper la coherencia del documento).
- **Aproximada:**
  - **Jaccard** = |A ∩ B| / |A ∪ B|.
  - **MinHash:** una función de hash aleatoria con P[h(A) = h(B)] = Jaccard(A, B).
  - **LSH:** n = b·r hashes en *b bandas* de *r*. A y B colisionan si **alguna** banda coincide **entera**.
    - Subir r afila el umbral y lo hace más estricto; subir b lo relaja.
    - Ejemplo: n = 9000, b = 20, r = 450.

## 4. Mezcla de datos
¿Qué peso le das a cada fuente (web, código, Wikipedia...)?
- **Líneas base:** a ojo (lo más común), uniforme, o proporcional al número de tokens.
- Intuición: dar más peso a lo bueno. **Pero:**
  - hay que mantener la diversidad;
  - las fuentes son finitas: repetir 50 épocas datos de calidad provoca **sobreajuste**.
- **UniMax:** muestreo uniforme con un **tope de épocas** por fuente.
- **Mezcla por regresión:**
  1. Muestrear mezclas (por ejemplo con una Dirichlet).
  2. Entrenar modelos pequeños.
  3. Ajustar una regresión mezcla → pérdida y optimizar. Es análogo a las leyes de escala.
- **Épocas simuladas:** se submuestrean todas las fuentes en proporción para que la escala pequeña "se parezca" a la grande. **Que lo pequeño imite a lo grande es un tema recurrente del curso.**

## 5. Datos de post-training
**Receta:** definir entornos → definir tareas o prompts → generar respuestas con un **modelo maestro** fuerte.
- **OpenThoughts:**
  - 1,2M ejemplos con QwQ-32B como maestro, 16 respuestas por prompt;
  - **un mejor modelo no es necesariamente mejor maestro**;
  - filtrar respuestas no ayudó;
  - fuentes pequeñas de calidad ganan a las grandes y diversas.
- **SWE-smith:** a partir de 128 repos, un LM **introduce bugs** y genera 50.000 tareas.
- Los entornos de código son una pesadilla de infraestructura (miles de imágenes Docker).
  - **SWE-Zero:** los modelos fuertes tienen un "modelo del mundo" del código, así que se generan 300.000 trayectorias **sin ejecutar** (12M en la versión escalada).
  - **SWE-Hero:** 13.000 trayectorias con ejecución.
  - SWE-rebench: 21.000 tareas Python interactivas.

## Ideas clave
- **Filtrar:** define qué es "bueno" y extrapólalo a los datos en bruto.
- **Deduplicar:** hashing (MinHash + LSH) que escala linealmente.
- **Mezclar:** prueba mezclas a escala pequeña y extrapola, cuidando las épocas.
- El trabajo de datos es muy específico de cada dominio: **mira los ejemplos**.
- En la tarea 4 se pasa HTML de Common Crawl a texto, se entrenan clasificadores y se aplica MinHash.
