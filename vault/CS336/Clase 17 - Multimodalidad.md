---
curso: "[[CS336 - Índice]]"
clase: 17
tema: Modelos multimodales (CLIP, SigLIP, LLaVA, Qwen-VL, Chameleon)
video: https://www.youtube.com/watch?v=26FtD08ZpOU
material: https://github.com/stanford-cs336/lectures/blob/main/lecture_17.py
tags: [cs336, multimodal, vision, clip, siglip, llava, qwen-vl]
---

# Clase 17: Modelos multimodales

**Objetivo final:** un **modelo omni**, que entienda y genere cualquier combinación de modalidades.
Los Transformers hablan en **tokens**, así que todo hay que convertirlo en tokens. Con el texto ya pasaba ([[Clase 01 - Panorama y tokenización]]); con el resto es más difícil.

## Entender imágenes (codificadores)
### CLIP (OpenAI)
- Aprendizaje **contrastivo** con 400M pares (imagen, texto): cada imagen debe preferir su texto frente al resto del batch (32.768), y viceversa.
- ViT-L/14 a 336 px para la imagen y un Transformer tipo GPT-2 para el texto.
- **Zero-shot en ImageNet** igualó a un ResNet-50 entrenado con 1,2M imágenes.
- Predecir el texto directamente era mucho menos eficiente.
- Captura la semántica, pero de grano grueso. Necesita batches grandes.

### SigLIP (Google)
- Cambia el softmax sobre todo el batch por una **clasificación binaria** (¿están alineados?).
- Separa el tamaño del batch de la pérdida y es más barato: 5 días en 32 TPUv4, frente a 10 días en 256 TPUv3 de CLIP.
- Datos de WebLI, con OCR; 100 idiomas.

## Plantilla VLM: codificador de visión + proyector + LM
- **LLaVA:**
  - CLIP + **proyección lineal** + Vicuna;
  - 158.000 conversaciones generadas con GPT-4 a partir de las anotaciones de COCO;
  - fase 1: solo se entrena el proyector; fase 2: proyector + LM.
- **LLaVA OneVision:**
  - SigLIP + MLP de 2 capas + Qwen-2 72B;
  - **AnyRes:** parte la imagen en trozos para conservar la resolución (clave para el OCR);
  - equilibra imagen única, varias imágenes y vídeo para que produzcan una cantidad de tokens parecida;
  - filosofía: **calidad antes que cantidad** y **de fácil a difícil**;
  - hay transferencia entre modalidades, por ejemplo de gráficos a agentes con GUI.
- **Qwen-VL:** adaptador de *cross-attention* a 256 tokens y tokens especiales `<img>`, `<box>`, `<ref>`. Tres fases de entrenamiento.
- **Qwen2-VL:**
  - **resolución dinámica**;
  - vídeo a 2 fotogramas por segundo;
  - **MRoPE**: RoPE multimodal para tiempo, alto y ancho.
- **Qwen3-VL:**
  - MRoPE intercalado;
  - marcas de tiempo explícitas en el vídeo;
  - **pérdida normalizada por raíz cuadrada** para que el vídeo no domine;
  - SigLIP-2 + **DeepStack** (inyecta lo visual en varias capas);
  - contexto de 256K y MoE hasta 235B-A22B.

## Generar imágenes: Chameleon (Meta)
- Todo se convierte en **tokens discretos** con un VQ-VAE: una imagen de 512×512 da 1024 tokens de un *codebook* de 8192.
- Entiende y genera imágenes de forma **uniforme**, como pura autorregresión.
- **Inestabilidad:** los tokens de texto tienen poca entropía y los de imagen mucha, así que crecen las normas. Se arregla con **QK-norm + z-loss** ([[Clase 03 - Arquitecturas]]).
- Pierde información al discretizar (sufre en OCR).
- La alternativa actual: codificadores continuos + Transformer + **difusión** para generar.

## Ideas clave
- Los modelos de frontera son **multimodales de forma nativa**.
- El reto es codificar lo que no es texto. Entender pide semántica; generar pide detalle fino.
- Hay que equilibrar imagen y vídeo (menos densos en información) frente al texto para que el entrenamiento sea estable.
