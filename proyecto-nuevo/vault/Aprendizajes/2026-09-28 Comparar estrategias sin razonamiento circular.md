---
fecha: 2026-09-28
etiquetas: [metodo, decision, simulacion, negocio]
origen: revisor (segunda revisión de la simulación de Arcend)
---
# Comparar estrategias sin razonamiento circular

- **Qué pasó:** en la simulación de Arcend cada estrategia tenía una probabilidad de cierre (p_cierre) elegida a mano. El ganador dependía de esas elecciones: la conclusión ya estaba metida en los supuestos. Una opción intermedia parecía buena en todo, pero no ganaba en ninguna prueba exigente.
- **Lección:**
  - Comparar estrategias con p_cierre elegidos a mano es **circular**.
  - Antes de dar un ganador, probar siempre tres escenarios: **"p igual"** (misma p_cierre para todas), **"p × ticket constante"** (cuanto más caro, menos se cierra) y **"canal a la mitad"** (el canal rinde la mitad de lo previsto).
  - Una opción **intermedia en todo no es robusta**: suele perder en el peor caso.
  - Para arrancar sin colchón, elegir por **riesgo de caja** (probabilidad de acabar sin caja, p10), no por la mediana.
- **Cómo aplicarla:** cualquier comparación de estrategias (precio, canal, paquete) se presenta con los tres escenarios y con el riesgo de caja al lado de la mediana. Ver [[2026-09-28 Simulación Monte Carlo de estrategias comerciales]] y [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
