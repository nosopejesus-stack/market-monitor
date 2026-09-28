---
fecha: 2026-09-28
etiquetas: [simulacion, montecarlo, negocio, revision]
origen: revisor (dos revisiones de proyecto-nuevo/arcend/simulacion/montecarlo.py, v1-v3)
---
# Simulación Monte Carlo de estrategias comerciales

- **Qué pasó:** en la simulación de Arcend el [[Agentes/Revisor|revisor]] encontró fallos de modelado: cuotas que no se cobraban desde el alta de cada cliente, churn aplicado antes del primer cobro, parámetros iguales para paquetes de precio muy distinto, horas sin tope real, métricas que salían 0 % o 100 % por cómo estaba construido el modelo y parámetros comunes sorteados de forma distinta en cada estrategia. En v3 quedan problemas conocidos (tope de horas, upsell y plazo por paquete, meses de 4 semanas); según el revisor no cambian la elección.
- **Lección:**
  - Cobrar las cuotas **desde el alta de cada cliente**, y el churn solo **después del primer cobro**.
  - Los parámetros que dependen del precio (**plazo de decisión, horas por cliente, tasa de upsell, filtro del decisor**) van **por paquete**, no globales.
  - Las horas son un **presupuesto que se consume**: tope real, no una cifra informativa.
  - Comprobar que **ninguna métrica sale 0 % o 100 % por construcción**. Si sale así, es un fallo del modelo hasta que se demuestre lo contrario.
  - Añadir **sensibilidad** (correlación de Spearman o tornado) para saber qué supuesto manda.
  - Sortear los **parámetros comunes una vez por ejecución** y compartirlos entre estrategias, para comparar con el mismo mundo.
- **Cómo aplicarla:** antes de sacar conclusiones de una simulación, repasar esta lista y pedir una ronda del revisor. Relacionada: [[2026-09-28 Comparar estrategias sin razonamiento circular]] y [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]].
