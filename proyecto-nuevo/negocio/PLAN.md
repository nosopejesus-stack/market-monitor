# Plan: respuesta inmediata a leads para inmobiliarias de Madrid

## Qué vendemos
A inmobiliarias pequeñas y medianas de Madrid (1-15 agentes): **cada lead de Idealista/Fotocasa/web
recibe respuesta por WhatsApp en menos de 2 minutos, 24/7**, se cualifica (presupuesto, zona,
financiación, plazo) y se le agenda la visita en el calendario del agente. El agente solo ve leads cualificados.

## Por qué aquí hay dinero (hipótesis a verificar en las primeras 20 conversaciones)
- Un piso vendido en Madrid deja miles de euros de comisión; perder un lead por responder tarde cuesta más que el servicio.
- Muchas agencias responden en horas o al día siguiente, sobre todo fines de semana y noches. **Lo medimos nosotros:** antes de visitarlas, les mandamos una consulta real como comprador y cronometramos su respuesta. Ese dato es el argumento de venta.

## El edge real (y sus límites)
- **Edge:** coste de entrega casi cero y velocidad. Claude construye la demo personalizada de cada agencia (con sus pisos reales) ANTES de la reunión, y la instalación en 48 h. Una agencia tradicional tarda semanas.
- **No es un moat:** otros pueden copiarlo. Se defiende con velocidad, precio fijo, resultados medidos y relación local.

## Precio
- **1.900 € instalación + 290 €/mes** (mantenimiento, ajustes, informe mensual).
- Pago de la instalación: 50 % al firmar, 50 % a la entrega. Sin permanencia.
- Los costes de WhatsApp Business API y del servidor los paga el cliente (unos 15-40 €/mes, según volumen). **Nosotros: 0 €.**

## Matemática de los 10.000 €
- 5 clientes × (1.900 + 290) = **10.950 €**.
- Con un cierre del 10 % hacen falta ~50 conversaciones con decisores en 4 semanas → **~12 por semana**.
- **Estimación honesta:** llegar a 10k en el mes 1 es posible pero no lo más probable (~20-30 %). Lo más probable: 2-3 clientes el mes 1 (4-6k) y 10k acumulados en el mes 2. Si tras 25 conversaciones hay 0 interesados de verdad, se mata y se pivota.

## Reparto
| Claude + equipo de agentes | Tú (parte humana) |
|---|---|
| Lista de agencias de Madrid con decisor, zona y datos | Visitar/llamar a ~12 decisores por semana (2-3 h/día) |
| Prueba de velocidad de respuesta de cada agencia (el mensaje lo envías tú) | Enviar los mensajes de prueba desde tu móvil |
| Demo personalizada por agencia antes de la visita | Enseñar la demo, negociar, cerrar |
| Propuesta, contrato y contrato de encargo de tratamiento (RGPD) | Firmar y cobrar (transferencia) |
| Montaje: n8n + WhatsApp + calendario, pruebas, informe mensual | Darte de alta como autónomo antes del primer cobro |

## Criterios de muerte
- 25 conversaciones con decisores y 0 que quieran una segunda reunión → se mata.
- Tras 3 instalaciones, más de 6 h humanas por cliente → se rediseña.
- Clientes que se van en el mes 2 por no ver leads cualificados → se mata.

## Semana 1
1. Claude: lista de 150 agencias de Madrid (prioridad: Chamberí, Salamanca, Retiro, Chamartín, Centro).
2. Tú: enviar 30 consultas de prueba como comprador; Claude registra los tiempos de respuesta.
3. Claude: demo funcional + 5 demos personalizadas para las agencias más lentas.
4. Tú: primeras 10 visitas con el dato de su tiempo de respuesta y la demo en el móvil.
