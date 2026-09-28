---
fecha: 2026-09-28
etiquetas: [arcend, blindaje, reglas, falsos-positivos]
origen: arcend/blindaje/reglas.py
---
# Detectores de lenguaje prohibido con negación y contexto

- **Qué pasó:** El detector de Blindaje cazaba falsos positivos delante de un médico: frases negadas ("no garantizamos resultados"), textos que explican la prohibición, "no invasivo" o "no espere más" confundidos con negación, una coincidencia específica descartada ("efecto botox", "botox capilar") que luego volvía a cazar un patrón genérico, y "Milagros" como nombre propio solo se excluía en minúsculas ("DRA. MILAGROS PÉREZ" sí saltaba).
- **Lección:** Un detector de lenguaje prohibido debe mirar la frase entera: negación y contexto explicativo en la misma frase rebajan el hallazgo (toxina negada → BAJA "revisar a mano"; promesa negada → no cuenta). La negación necesita lista blanca de expresiones que empiezan por "no" pero no niegan ("no invasivo", "no espere"). Las exclusiones específicas deben consumir su tramo de texto. Los nombres propios se excluyen sin distinguir mayúsculas.
- **Cómo aplicarla:**
- Al descartar una coincidencia, marcar su tramo como ocupado para que ningún patrón genérico lo vuelva a cazar.
- Cada falso positivo conocido va documentado al principio de `reglas.py` y con un test (fixture de falsos positivos).
- Probar siempre variantes en MAYÚSCULAS y con tratamiento ("Dra. Milagros", "DRA. MILAGROS PÉREZ").

Relacionado: [[Proyecto/Arcend - clínicas estéticas Madrid]], [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
