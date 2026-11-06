---
fecha: 2026-11-06
tipo: aprendizaje
fuente: 3 TikToks enviados a Claude (transcritos con Whisper)
tags: [herramientas, claude-code, diseño, computer-use, cursos]
---

# Lo aprendido de 3 TikToks

## 1. @gonzalo_lopezg: Claude usa cualquier app de tu ordenador
- Herramienta: **[[Agent Desktop]]** (Vercel Labs, open source).
- Varias sesiones a la vez, cada una con su cursor, mientras tú trabajas.
- Ejemplo: una pasa 10 facturas de un PDF a una hoja de cálculo, otra hace el resumen y otra suma en la calculadora.
- Consejo: pedirle a Claude un prompt que cubra **tu trabajo, tus apps y qué delegar**.

## 2. @midudev: curso gratis de Stanford para crear tu propia IA
- **Stanford CS336**: 18 vídeos con audio en español (doblaje de YouTube), con Python y Machine Learning.
- Enseña a tokenizar, entrenar, inferencia y post-entrenamiento.
- Notas completas: [[CS336 - Índice]].

## 3. @revolutia.ai: 5 herramientas para que tu app no parezca de 2006
1. **Taste Skill:** criterio estético ("si veo otro degradado morado con tres tarjetas redondeadas, llamo a la policía").
2. **Guías de diseño web** (Vercel): audita lo ya construido contra guías reales.
3. **Awesome Design:** sistemas de diseño de marcas (tipografía, colores, espaciado). "Se acabó pasarte 45 minutos eligiendo entre dos azules."
4. **Image to Code:** de una captura (de Pinterest, por ejemplo) a código.
5. **Playwright CLI:** Claude abre el navegador, prueba la web y hace capturas. "Lo construye, lo abre y lo mira."

Todas están instaladas como skills en el repo `market-monitor` (`.claude/skills/`).

## Flujo para montar una web
**Estilo** (Awesome Design → DESIGN.md) → **construir** (Taste Skill / Image to Code) → **verificar** (Playwright) → **auditar** (Guías de diseño).
