---
fecha: 2026-09-28
etiquetas: [demo, seguridad, negocio]
origen: revisor + constructor (negocio/demo/)
---
# Demos comerciales seguras y honestas

- **Qué pasó:** la demo por agencia (`negocio/demo/build_demo.py` → `salida/<agencia>/index.html`) necesitó correcciones del revisor.
- **Lección:**
  - Banner **"SIMULACIÓN"** siempre visible.
  - Los textos que dependen de datos (contadores, tiempos, nombres) se **calculan a partir de los datos**, no se escriben a mano.
  - El generador lleva **tests**.
  - Los datos van en `<script type="application/json">` **escapados** y se pintan con `textContent` (nunca `innerHTML`).
  - **No extraer datos de portales automáticamente** (condiciones de uso de Idealista/Fotocasa): datos de la agencia a mano o de fuentes permitidas.
- **Cómo aplicarla:** checklist del [[Agentes/Constructor|constructor]] antes de entregar cualquier demo.
