---
fecha: 2026-09-28
estado: aceptada
fuente: proyecto-nuevo/arcend/DECISION.md
---
# Arcend - Blindaje continuo por teléfono

- **Contexto:** Arcend ([[Proyecto/Arcend - clínicas estéticas Madrid]]) se reactivó. Se investigó el mercado (`proyecto-nuevo/arcend/investigacion/mercado.md`) y se compararon estrategias con una simulación Monte Carlo (`proyecto-nuevo/arcend/simulacion/montecarlo.py`, 4.000 ejecuciones por escenario, versiones v1-v3, dos rondas del [[Agentes/Revisor|revisor]]).
- **Opciones consideradas:** vender los paquetes caros del Notion (Atención 1.200 € + 890 €/mes; Atención + Blindaje 1.900 € + 1.290 €/mes) de entrada; opciones intermedias o de menú; canal por email o visita; Blindaje continuo por teléfono (estrategia `S8_continuo_telefono`).
- **Decisión:** **Blindaje continuo para clínicas de medicina estética independientes de Madrid (S8).**
  - Entrada: informe de cumplimiento de la publicidad (web y redes) + textos corregidos, **390 €** pago único (sin IVA).
  - Recurrente: vigilancia mensual, **190 €/mes**, sin permanencia.
  - **Atención solo como subida** (semana 4-8, nunca en la 1.ª llamada), y solo si con ≥ 3 clientes de Blindaje más del 15 % acepta la subida antes de la semana 8.
  - Captación **por teléfono con el informe ya hecho** (Claude lo prepara con el risk-scanner, solo información pública; nada de escaneos, art. 197 bis CP). Nada de emails comerciales en frío (LSSI). Se pide la decisión en la reunión.
  - Motivo: es la opción con **menos riesgo de caja** en todas las pruebas (12-14 % de acabar la semana 4 sin caja frente a 24-39 % de las opciones caras, con cifras de mercado) y el mejor p10; precio dentro de lo que el mercado acepta (150-900 €); no se encontró a nadie vendiendo vigilancia continua a clínicas pequeñas; sin chatbot, así que no aplica la Ley de IA art. 50.1 ni el filtro de la recepcionista. Horas humanas: ~1 h de alta y ~15 min/mes por cliente.
- **Condiciones de muerte (primeras 40 llamadas / 2 semanas):**
  - < 3 reuniones con el titular de 40 llamadas → el teléfono no funciona: visita en persona o cambiar guion.
  - 0 firmas tras 8 reuniones con el informe delante → la oferta no convence: parar y revisar.
  - Caja neta ≤ 0 en la semana 4 → fallida.
- **Sin ilusiones:** **10.000 € en 30 días no es realista** con ninguna estrategia (≤ 10 % con cifras de mercado, y solo en las de más riesgo). Con cifras de mercado: mediana ~4.000-9.000 € de caja neta en 13 semanas; probabilidad de 10k en 13 semanas entre 12 % y 46 %. Con las cifras del Notion (optimistas): mediana ~28.000 € y 93 %. La verdad se sabe midiendo las primeras 40 llamadas.
- **Consecuencias:**
  - Sustituye la oferta de entrada del Notion (paquetes 1 y 2 pasan a ser subida).
  - Cada informe lleva la frase "no es asesoramiento jurídico; valídelo con su asesor si hay dudas".
  - Alta de autónomo tras el primer sí, fechada el día de la primera factura (~80 €/mes, SIN VERIFICAR).
  - SIN VERIFICAR hasta las primeras llamadas: acceso al titular por teléfono, cierre, pago trimestral, referidos. El modelo v3 tiene problemas conocidos (tope de horas, upsell y plazo por paquete, meses de 4 semanas) que afectan sobre todo a las opciones caras y no cambian la elección. Ver [[Aprendizajes/2026-09-28 Simulación Monte Carlo de estrategias comerciales]] y [[Aprendizajes/2026-09-28 Comparar estrategias sin razonamiento circular]].
