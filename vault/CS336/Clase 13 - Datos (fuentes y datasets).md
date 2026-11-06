---
curso: "[[CS336 - Índice]]"
clase: 13
tema: Datos I (fuentes, copyright y la historia de los datasets de preentrenamiento)
video: https://www.youtube.com/watch?v=-qm0ln33G24
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_13.py
tags: [cs336, datos, common-crawl, copyright, datasets, preentrenamiento]
---

# Clase 13: Datos (fuentes y datasets)

> **Los datos no caen del cielo.** Son lo más importante y lo que más diferencia a un modelo de otro. Las empresas publican su arquitectura pero no sus datos, por competencia y por riesgo de copyright.

## Etapas
1. **Preentrenamiento:** mucho texto en bruto de la web.
2. **Mid-training:** datos de más calidad para reforzar capacidades.
3. **Post-training:** chats, RL.

A lo largo del entrenamiento se pasa de **mucho dato de baja calidad** a **poco dato de alta calidad**.
Modelo **base** = después del preentrenamiento y el mid-training. Modelo **instruct/chat** = después del post-training.

## "Se entrena con todo internet"... no exactamente
- Hace falta un **crawler**: descubre y descarga páginas. Políticas de selección, de cortesía (`robots.txt`, no saturar el servidor) y de revisita.
- Obstáculos:
  - contenido dinámico (las apps);
  - **login** (Facebook, X, NYT);
  - `robots.txt`, Cloudflare, límites de peticiones;
  - **términos de servicio**.
- Las restricciones van **en aumento**: el consentimiento a ser rastreado está en declive.
- **Bibliotecas en la sombra** (LibGen, Sci-Hub, Anna's Archive): son piratería.

## Copyright, en resumen
- Casi **todo lo que hay en internet tiene copyright**: el listón es bajísimo y no hace falta registrarlo.
- Protege la **expresión**, no las ideas: quicksort no tiene copyright, el código concreto sí.
- Formas de usarlo:
  1. con una **licencia** (por ejemplo Creative Commons: Wikipedia, Khan Academy);
  2. por **fair use**, que pesa cuatro factores:
     - propósito: lo transformativo y educativo pesa a favor;
     - naturaleza de la obra: los hechos más que la ficción;
     - cantidad usada;
     - efecto en el mercado.
- Los **términos de servicio** pueden prohibir lo que la licencia permite. YouTube prohíbe descargar vídeos aunque sean CC.
- **Demandas:**
  - NYT contra OpenAI.
  - Autores contra Anthropic: entrenar con los libros se consideró *fair use*, pero **piratearlos no**. Acuerdo de **1.500 millones de dólares**.
  - Autores contra Meta: pendiente.
- Acuerdos de licencia: Google con Reddit, OpenAI con StackExchange y Shutterstock.

## Fuentes principales
| Fuente | Datos |
|---|---|
| **Common Crawl** | ONG desde 2007; un crawl cada mes (3-5 mil millones de páginas). Formatos WARC (HTML) y WET (texto, con pérdidas). **La conversión de HTML a texto importa** (trafilatura, resiliparse, jusText) |
| Wikipedia | 67M artículos en 361 idiomas; volcados periódicos. Riesgo de **envenenamiento** justo antes de un volcado |
| GitHub | 420M+ repos; solo licencias permisivas; muchos duplicados |
| arXiv | ~3M artículos, LaTeX; descarga masiva desde S3 |
| StackExchange | formato pregunta-respuesta, cercano al *instruction tuning* |
| Project Gutenberg | ~75K libros de dominio público |

## Historia de los datasets
| Dataset | Idea principal | Tamaño |
|---|---|---|
| BERT | Wikipedia + BooksCorpus, **documentos** en vez de frases | |
| WebText (GPT-2) | enlaces de Reddit con ≥ 3 de karma como señal de calidad | 40 GB |
| CCNet | dedupe + identificación de idioma + "parecido a Wikipedia" (KenLM) | |
| **C4** (T5) | reglas manuales: líneas acabadas en puntuación, sin `{`, sin "lorem ipsum" | 156B tokens |
| GPT-3 | clasificador de calidad (WebText/Wiki/Books frente al resto) + dedupe difuso | 400B |
| **The Pile** | 22 dominios curados por voluntarios | 275B |
| MassiveText (Gopher) | reglas manuales + SafeSearch | 10,5 TB |
| LLaMA | CCNet, C4, GitHub, Wikipedia, libros, arXiv, StackExchange | 1,2T (RedPajama lo replicó) |
| RefinedWeb / **FineWeb** | "basta con la web"; trafilatura, MinHash, anonimización | 15T |
| Dolma (OLMo) | Reddit, PeS2o, toxicidad con Jigsaw, filtros Bloom | 3T |
| **DCLM** | clasificador fastText (OpenHermes + ELI5 frente a RefinedWeb), **gana a los filtros por reglas** | 3,8T (de 240T) |
| **Nemotron-CC** | conjunto de clasificadores + **reescritura sintética** con LLM; no filtrar en exceso | 6,3T |
| The Stack v1/v2 | código con licencia permisiva, PRs, documentación | 3,1 TB |
| Common Pile | **solo datos con licencia permisiva** | 8 TB |

Como referencia, Llama 3 se entrenó con 15T tokens y Qwen3 con 36T.

## Ideas clave
- El flujo es: servicio en vivo → datos en bruto → datos procesados (transformación, filtrado, dedupe).
- Mucho de esto es **heurístico**: hay mucho margen de mejora.
- Siguiente: [[Clase 14 - Datos (filtrado y deduplicación)]].
