# Arcend · Decisión tras la simulación Monte Carlo (2026-09-28)

## Lo que montamos
**Blindaje continuo para clínicas de medicina estética independientes de Madrid.**

| | Qué | Precio (sin IVA) |
|---|---|---|
| Entrada | Informe de cumplimiento de la publicidad (web y redes) + textos corregidos listos para publicar | **390 €** pago único |
| Recurrente | Vigilancia mensual: se revisa de nuevo la web y las redes, aviso de cualquier publicación de riesgo y corrección | **190 €/mes**, sin permanencia |
| Subida (después, no en la 1.ª llamada) | Atención (paquete 1) o Atención + Blindaje (paquete 2) | 1.200 + 890/mes · 1.900 + 1.290/mes |

**Por qué este y no otro** (`simulacion/montecarlo.py`, 4.000 ejecuciones por escenario, dos rondas del revisor):
- Es el que **menos riesgo de caja** tiene en todas las pruebas: con cifras de mercado, 12-14 % de acabar la semana 4 sin caja, frente al 24-39 % de las opciones con paquetes caros; y el mejor peor caso (p10).
- El precio encaja con lo que el mercado acepta (150-900 €), y el dolor es real: sanciones de hasta 90.001 € por publicidad de medicamentos con receta (toxina), y el caso de una multa rebajada a 6.000 € por haber corregido antes (`investigacion/mercado.md`).
- **No hay nadie** vendiendo vigilancia continua de publicidad sanitaria a clínicas pequeñas (no se encontraron tarifas públicas).
- No amenaza a la recepcionista ni lleva chatbot: desaparecen el problema del filtro en la llamada y la obligación de la Ley de IA art. 50.1.
- Casi todo el trabajo lo hace Claude con el risk-scanner: informe, textos corregidos y revisión mensual. Horas humanas por cliente: ~1 h de alta y ~15 min/mes.

## Sin ilusiones
- **10.000 € en 30 días no es realista** con ninguna estrategia (≤ 10 % con cifras de mercado, y solo en las opciones de más riesgo).
- Con cifras de mercado y supuestos prudentes: mediana de ~4.000-9.000 € de caja neta en 13 semanas; probabilidad de llegar a 10k en 13 semanas entre el 12 % y el 46 % según rinda el teléfono.
- Con las cifras de tu Notion (optimistas): mediana ~28.000 € en 13 semanas y 93 % de pasar de 10k.
- **La verdad está entre las dos y se sabe en 2 semanas** midiendo las primeras 40 llamadas.

## Cómo se vende (tú)
1. Claude prepara el informe de cada clínica **antes** de llamar (solo información pública; nada de escaneos de sistemas, art. 197 bis CP).
2. **Llamas** a la clínica: "He revisado la publicidad de su web y he encontrado N puntos que la Consejería sanciona; ¿me da 10 minutos el Dr./la Dra. esta semana para enseñárselo?". Nada de emails comerciales en frío (LSSI).
3. En la reunión enseñas el informe, ofreces la entrada de 390 € y **pides la decisión en la reunión**.
4. Al entregar la corrección, ofreces la vigilancia mensual (190 €). La Atención, solo cuando ya confían (semana 4-8).

## Condiciones de muerte (primeras 40 llamadas / 2 semanas)
- **< 3 reuniones con el titular** de 40 llamadas → el teléfono no funciona: pasar a visita en persona o cambiar el guion.
- **0 firmas tras 8 reuniones** con el informe delante → la oferta no convence: parar y revisar.
- **Caja neta ≤ 0 en la semana 4** → se da por fallida.
- Solo se sube a los paquetes de Atención si, con ≥ 3 clientes de Blindaje, más del 15 % acepta la subida antes de la semana 8.

## Límites y avisos
- El informe **no es asesoramiento jurídico**: revisión basada en normativa pública, con la recomendación de validarlo con su asesor si hay dudas. Esta frase va en cada informe.
- Alta de autónomo solo tras el primer sí, fechada el día de la primera factura (~80 €/mes, SIN VERIFICAR).
- Supuestos del modelo aún SIN VERIFICAR (se miden en las primeras llamadas): tasa de acceso al titular por teléfono, cierre, pago trimestral, referidos. El modelo v3 tiene problemas conocidos que el revisor listó (tope de horas, upsell y plazo por paquete, meses de 4 semanas); afectan sobre todo a las opciones caras y **no cambian la elección**.
