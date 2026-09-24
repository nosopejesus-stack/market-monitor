# A. Informe de verificación XAUUSD — Ciclo 02

## Veredicto final: **NO EDGE. NO OPERARLA.**

La regla literal no tiene ventaja estadística. Su alta tasa de aciertos es la que produce cualquier
camino aleatorio con estas distancias de TP y SL. No sobrevive a costes realistas, y ninguna variante
de parámetros, periodo, régimen o definición de vela produce una ventaja robusta. La verificación
encontró un sesgo, pero juega **a favor** de la estrategia: el resultado real es probablemente algo peor
que el publicado en el ciclo 01.

Todas las cifras salen de `python -m xau.verify` (tablas completas en
[`results/xau_verify.md`](results/xau_verify.md)) y de `python -m xau.study` (ciclo 01). Ninguna cifra
se ha escrito a mano.

---

## 1. Especificación del instrumento: qué está verificado y qué no

**Aviso.** No tengo acceso a tu cuenta MT5. La única fuente de verdad sobre tu instrumento es la
ventana *Especificación del símbolo* de tu terminal. Las páginas de FTMO están bloqueadas desde este
entorno, así que todo lo relativo al bróker viene de fuentes secundarias.

| elemento | valor usado en el backtest | estado | ¿afecta al veredicto? |
|---|---|---|---|
| Símbolo | XAU/USD de Twelve Data (spot compuesto de varias fuentes, precio medio) | **FACT** (fuente de datos) | Un feed compuesto no es el precio de tu bróker; ver §5 |
| Dígitos | El feed trae 5 decimales. En MT5 se asumen 2 dígitos | **Estimación con fuente secundaria** (goldsniper.io, fxnx.com: "para XAUUSD, 0,01 $ = 1 punto") · NO VERIFICADO en tu cuenta | No: §3 V12 |
| Tamaño del punto | 0,01 $ (708 pts = 7,08 $) | Igual que la fila anterior | **No**: con 0,001 $, 0,01 $ o 0,10 $ ninguna lectura da ventaja (V12) |
| Tamaño de contrato | No se usa: todo se mide en R (distancia al SL) | 100 oz/lote habitual (fuente secundaria) | No: solo afecta al tamaño de la posición |
| Tick size / tick value | No se usa (0,01 $ y 1 $/lote para 100 oz habituales) | Fuente secundaria | No |
| Spread | Modelado como medio spread en cada disparo: 0,15 / **0,30** / 0,50 / 1,00 $ | FTMO "0,15-0,30 $ en horas normales" (fuente secundaria). El feed no trae bid/ask | Sí, en contra: más spread, peor resultado |
| Comisión | 0 $ y 0,07 $/oz (≈7 $/lote, cuenta raw) | FTMO: "sin comisión en metales" (fuente secundaria propvator.com) | Poco: −0,004R por operación |
| Swap | No conocido. Sensibilidad −0,60 / 0 / +0,30 $/oz/noche para cortos, triple el miércoles | **UNKNOWN** para tu cuenta | Poco: mediana de 0 noches, el 80% cierra antes del primer rollover |
| Zona horaria del servidor | Días de 17:00 a 17:00 de Nueva York (estándar MT5 UTC+2/+3) | **FACT** para los datos (demostrado, §2). **Asumido** para tu bróker | Probado con UTC 00:00: peor (V5) |
| Apertura/cierre de la vela diaria | 17:00 NY. La señal se evalúa al cierre; la orden vive el día siguiente | Auditado (V2) | — |

**Qué necesito de ti** (sin enviar nada a nadie): abre en MT5 *Observación del mercado → XAUUSD →
Especificación* y dime Dígitos, Tamaño del contrato, Spread, Swap largo/corto y el huso horario del
servidor. Con eso re-ejecuto todo en segundos. El veredicto no depende de esos valores (§3 V6 y V12).

---

## 2. Verificación de la implementación

| comprobación | método | resultado |
|---|---|---|
| **Límites de la vela diaria** | El hueco de mantenimiento del feed H1 cae siempre a las 17:00 NY (demostrado con los cambios de horario de EE. UU. y Australia). Timestamps en Australia/Sydney, convertidos a NY | ✔ Velas diarias correctas; M5 agregado a horas reproduce H1 exactamente (diferencia mediana 0,000 $) |
| **Look-ahead** | Features recalculadas con datos truncados en el día t frente a las calculadas con toda la muestra | ✔ 40/40 días aleatorios idénticos |
| **Entrada solo tras cerrar la vela** | Hora de cada ejecución frente a las 17:00 NY del día de señal | ✔ Todas las ejecuciones ocurren después del cierre |
| **Caducidad de la orden** | Cada ejecución cae en el día siguiente | ✔ 100% |
| **Información futura en la señal** | La señal usa open/close de t; los niveles usan close_t; los terciles del ciclo 01 se ajustaron solo con 2020-2022 | ✔ |
| **Ejecución de SL/TP** | Reimplementación independiente en Python puro desde el texto de la regla, sin compartir código con el motor | ✔ **100% de coincidencia operación a operación** en 921 señales; diferencia máxima de P&L 0,0000 $ |
| **Spread** | Medio spread en cada disparo: el TP exige 1 spread más de recorrido y el SL salta 1 spread antes. Gaps: ejecución en la apertura ± medio spread | ✔ Con tests unitarios; realista para órdenes stop y limit |
| **Velas ausentes** | 7 de 1.722 días con huecos internos >2 h (0,4%); 2 días hábiles descartados por tener <10 velas | ✔ Impacto despreciable |
| **Velas falsas** | **Hallazgo:** desde abril de 2025 el feed incluye 132 "días" de fin de semana (2.517 velas H1, rango mediano 0,28 $ frente a 4,91 $ entre semana), que no existen en MT5 | ✔ Excluidas de señales y de la gestión de posiciones (ya lo estaban; ahora está documentado y comprobado) |
| **Pausa de mantenimiento** | Desde mayo de 2025 el feed trae la hora 17:00-18:00 NY, que MT5 no cotiza | ✔ Quitarla cambia −0,020R → −0,019R |
| **Supuesto intradía (H1)** | Recalculado con velas de 5 minutos en 2026 (47 operaciones con cobertura M5 completa) | ⚠ **H1 sobreestima la estrategia**: H1-PATH +0,040R / 72,3% frente a M5-PATH **−0,021R / 68,1%**. Las operaciones ambiguas pasan del 26,7% (H1) al 6,7% (M5). El resultado de −0,020R de toda la muestra es probablemente **optimista** |

---

## 3. Red team: intentos de encontrar una ventaja

| prueba | resultado | lectura |
|---|---|---|
| **Control de entrada aleatoria** (5.000 subconjuntos de días del mismo tamaño) | Observado −0,020R frente a −0,045R de media aleatoria; p bilateral = 0,17 | La condición "vela alcista" no es distinguible del azar |
| **Dirección aleatoria** (2.000 lanzamientos de moneda, SELL o BUY STOP los mismos días) | −0,027R (5-95%: −0,059 a +0,004) | Vender no es mejor que tirar una moneda |
| **Hipótesis nula geométrica** (40 caminos aleatorios sin deriva con retornos H1 barajados, misma regla y spread) | Tasa de aciertos del paseo aleatorio **68,8%** (66,6-72,0%) frente a la observada **68,8%** | **La tasa de aciertos es una propiedad del TP/SL y el spread, no del oro** |
| **Spreads** 0,15 / 0,30 / 0,50 / 1,00 $ | −0,017 / −0,020 / −0,033 / −0,061R | Empeora de forma monótona |
| **Costes realistas** (spread × comisión × swap, 18 combinaciones) | Siempre negativo: de −0,011R (el mejor caso) a −0,049R | No es rentable después de costes en ningún escenario |
| **Perturbación de parámetros** (125 combinaciones de entrada 500-900, TP 500-900 y SL 1200-2000 puntos) | 19% con media >0; **0% con t > 2**; mediana −0,027R; mejor t = 0,83 | No hay ninguna "zona buena". El mejor de 125 es ruido (el máximo esperado por azar es t ≈ 2,5) |
| **Periodos** 2020-21 / 2022-23 / 2024-26 | −0,078 / +0,025 / −0,012R | Signo inestable, ningún tramo significativo |
| **Regímenes** (tendencia alcista/bajista/lateral; ATR <30 / 30-60 / ≥60 $) | Todos entre −0,047 y −0,002R; ningún IC excluye cero | No hay régimen donde funcione |
| **Definición del día** (NY 17:00 / UTC 00:00 / sin la hora de mantenimiento) | −0,020 / **−0,078 (t −2,5)** / −0,019R | Con velas UTC es claramente perdedora |
| **Walk-forward** (reoptimizar en los 2 años previos y operar el siguiente, 2022-2026) | OOS encadenado **−0,013R (t −0,36)** frente a +0,002R de la regla literal en esos años | Optimizar no la rescata: los ganadores dentro de muestra no se mantienen |
| **Fuera de muestra** (ciclo 01) | IS 2020-22 −0,006R · OOS 2023-26 −0,029R · era independiente 2006-19 entre −0,182 y −0,013R | Negativa en todos los tramos |
| **Monte Carlo por bloques** (bloques de 10 operaciones, conserva rachas) | Con 1% de riesgo: P(drawdown ≥10% en un año) = **27,8%**, mediana anual −1,5%, P(año positivo) 41% | Mala supervivencia en cuenta de fondeo |
| **Posiciones simultáneas** | Máximo 2 a la vez en la historia; peor día real −2% con 1% de riesgo | No hay riesgo de límite diario del 5%, pero hay una deriva negativa |
| **Lectura de "708 puntos"** (V12) | 0,001 $: −0,212R (t −5,0) · 0,01 $: −0,020R · 0,10 $: +0,012R con 53 ejecuciones en 6,7 años (t 0,14) | Ninguna lectura da ventaja. La de 0,10 $ tiene tan pocas operaciones que no permite concluir nada |

---

## 4. La distinción que pediste

| concepto | ¿lo cumple? | evidencia |
|---|---|---|
| **Tasa de aciertos alta** | Sí: 68,8% | Pero es exactamente la de un paseo aleatorio con este TP/SL (68,8%) |
| **Expectativa positiva** | **No** | −0,020R por operación (H1, spread de 0,30 $); probablemente peor con M5 |
| **Significación estadística** | **No** | t = −0,72; IC 95% [−0,076; +0,033]; permutación p = 0,17 |
| **Robustez** | **No** | 0 de 125 variantes con t > 2; el walk-forward es negativo; la señal cambia según el periodo |
| **Rentabilidad tras costes** | **No** | Negativa en las 18 combinaciones de spread, comisión y swap |
| **Supervivencia al drawdown** | **Mala** | 28% de probabilidad anual de tocar −10% con 1% de riesgo; mediana negativa |

Una tasa de aciertos del 69% con un SL 2,28 veces mayor que el TP no es una ventaja: es la aritmética
del ratio. Para ganar dinero harían falta más del 69,5% de aciertos **después de spread**, y no llega.

---

## 5. Incertidumbres que quedan (y por qué no cambian el veredicto)

1. **Feed compuesto frente a tu bróker.** Los máximos y mínimos de tu bróker pueden diferir unos céntimos. Con objetivos de 7,08 $, eso mueve algunas ejecuciones, pero el efecto es simétrico y el spread real solo puede empeorar el resultado.
2. **Especificación de tu cuenta** (dígitos, spread, swap, huso horario): no verificada, pero el veredicto se mantiene en todo el rango probado.
3. **M5 solo para 2026**, con 47 operaciones comparables. Indica que H1 es optimista, pero la magnitud del sesgo en otros años es desconocida.
4. **Antes de 2020 solo hay velas diarias**, así que la era 2006-2019 solo da cotas.
5. **Pruebas múltiples.** En los dos ciclos se han probado unas 200 hipótesis. Cualquier resultado aislado con p ≈ 0,05 sería ruido esperado.

## 6. Qué haría falta para reabrir el caso

Solo una prueba *pre-registrada* con datos de tu propio bróker (ticks o M1) y una hipótesis definida
**antes** de mirar los datos. Nada en estos dos ciclos justifica gastar tiempo ni capital en ello.
**Conclusión: NO EDGE. NO OPERARLA.**

Fuentes de la especificación (secundarias): [goldsniper.io — FTMO gold](https://www.goldsniper.io/brokers/ftmo-gold-trading) ·
[fxnx.com — gold spreads](https://fxnx.com/en/blog/gold-spreads-uncover-your-real-xauusd-cost) ·
[propvator.com — FTMO conditions](https://propvator.com/blog/ftmo-trading-conditions/) ·
[forexvitals.com — XAUUSD lot size](https://forexvitals.com/articles/xauusd-lot-size)
