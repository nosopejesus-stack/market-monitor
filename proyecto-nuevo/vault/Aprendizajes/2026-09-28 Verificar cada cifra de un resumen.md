---
fecha: 2026-09-28
etiquetas: [error, revision, cifras]
origen: Claude principal (error propio, corregido en la sesión de Arcend)
---
# Verificar cada cifra de un resumen

- **Qué pasó:** Claude principal escribió en un resumen de la simulación de Arcend que la probabilidad de 10.000 € en 30 días era "≤ 7 %" sin comprobarla contra la tabla de resultados. El dato real era **10 %**. Se corrigió (`proyecto-nuevo/arcend/DECISION.md` dice "≤ 10 %").
- **Lección:** una cifra de resumen se escribe **después** de mirarla en los datos, nunca de memoria ni redondeando a ojo.
- **Cómo aplicarla:** antes de publicar un resumen, cotejar cada número con la tabla o el JSON de origen (p. ej. `resultados.json`) usando tools, y pedir al [[Agentes/Revisor|revisor]] que compruebe las cifras del resumen contra los datos. Relacionada: [[2026-09-28 Coherencia comercial en el kit de ventas]].
