# Plan: respuesta inmediata a leads para inmobiliarias de Madrid
> **APARCADO (2026-09-28):** el proyecto principal es Arcend (clínicas estéticas). Este plan se conserva por si se reutilizan piezas.

## Qué vendemos
A inmobiliarias pequeñas y medianas de Madrid (1-15 agentes): **cada lead de Idealista, Fotocasa o su web
recibe una primera respuesta automática en minutos, 24/7 (objetivo < 2 min, se mide en el piloto).** La primera respuesta va por email (el formato en que llegan
todos los leads) con un botón para seguir por WhatsApp; cuando el comprador escribe por WhatsApp, un asistente
**identificado como automático** cualifica (presupuesto, zona, financiación, plazo) y agenda la visita en el
calendario del agente. El agente solo ve leads cualificados.

Por qué así (ver `investigacion/whatsapp_idealista.md`):
- WhatsApp solo deja a la empresa escribir primero con plantilla aprobada y consentimiento explícito; un teléfono dejado en un portal no lo es. Si el comprador abre él el WhatsApp desde el botón, el consentimiento es limpio y la conversación es gratis de iniciar.
- El teléfono del lead no siempre viene; el email sí.
- Ley de IA de la UE, art. 50.1: desde el 2-ago-2026 el asistente debe decir que es automático.
- Desde el 1-oct-2026 Meta cobra también los mensajes dentro de la ventana de 24 h: coste pequeño, **a cargo del cliente, con su tarjeta**.

## Por qué aquí hay dinero (hipótesis a verificar en las primeras 20 conversaciones)
- Un piso vendido en Madrid deja miles de euros de comisión; perder un lead por responder tarde cuesta más que el servicio.
- Muchas agencias responden en horas o al día siguiente, sobre todo fines de semana y noches. **Lo medimos nosotros:** antes de visitarlas, les mandamos una consulta real como comprador y cronometramos su respuesta. Ese dato es el argumento de venta.

## El edge real (y sus límites)
- **Edge:** coste de entrega casi cero y velocidad. Claude construye la demo personalizada de cada agencia ANTES de la reunión (con su nombre y pisos ficticios de su zona y rango de precio, marcados como simulación; sus pisos reales solo tras su permiso), y la instalación en 48 h laborables desde que llegan los accesos y Meta aprueba las plantillas. Una agencia tradicional tarda semanas.
- **No es un moat:** otros pueden copiarlo. Se defiende con velocidad, precio fijo, resultados medidos y relación local.

## Precio
- **1.900 € instalación + 290 €/mes** (mantenimiento, ajustes, informe mensual).
- Pago de la instalación: 50 % al firmar, 50 % a la aceptación. Sin permanencia.
- Los costes de WhatsApp (Meta, con la tarjeta del cliente) y del servidor (contratado a nombre del cliente) los paga el cliente. Importe exacto: SIN VERIFICAR, se mide en el piloto. Nuestro coste de herramientas: 0 € (ver cuota de autónomo abajo).

## Matemática de los 10.000 € (ingresos brutos, sin IVA)
- Cobro por cliente: 950 € a la firma + 950 € a la aceptación + 290 €/mes desde la entrega.
- **Mes 1:** 5 clientes firmados y entregados = 5 × (1.900 + 290) = **10.950 €**. Un cliente firmado en la semana 4 y aún no entregado aporta solo 950 € ese mes.
- Con un cierre del 10 % hacen falta ~50 conversaciones con decisores en 4 semanas → **~12 por semana**.
- **Estimación honesta:** 10k en el mes 1 es posible pero no lo más probable (~20-30 %). Lo más probable: 2-3 clientes el mes 1 (4-6k) y 10k acumulados en el mes 2. Si tras 25 conversaciones no hay ninguna segunda reunión, se mata y se pivota.
- **Único gasto propio:** el alta de autónomo es obligatoria **antes de firmar el primer contrato** (modelo 036/037 + RETA). Cuota con tarifa plana: del orden de 80 €/mes (importe 2026 SIN VERIFICAR). Es decisión tuya: se da de alta cuando haya el primer "sí" verbal, y se paga con el primer cobro.

## Reparto
| Claude + equipo de agentes | Tú (parte humana) |
|---|---|
| Lista de agencias de Madrid con decisor, zona y datos | Visitar/llamar a ~12 decisores por semana (2-3 h/día) |
| Prueba de velocidad de respuesta de cada agencia (el mensaje lo envías tú) | Enviar los mensajes de prueba desde tu móvil |
| Demo personalizada por agencia antes de la visita | Enseñar la demo, negociar, cerrar |
| Propuesta, contrato y contrato de encargo de tratamiento (RGPD) | Firmar y cobrar (transferencia) |
| Montaje: n8n + WhatsApp + calendario, pruebas, informe mensual | Darte de alta como autónomo antes de firmar el primer contrato |

## Criterios de muerte
- 25 conversaciones con decisores y 0 que quieran una segunda reunión → se mata.
- Tras 3 instalaciones, más de 6 h humanas por cliente → se rediseña.
- Clientes que se van en el mes 2 por no ver leads cualificados → se mata.

## Semana 1
1. Claude: lista de 150 agencias de Madrid (prioridad: Chamberí, Salamanca, Retiro, Chamartín, Centro).
2. Tú: enviar 30 consultas de prueba como comprador; Claude registra los tiempos de respuesta.
3. Claude: demo funcional + 5 demos personalizadas para las agencias más lentas.
4. Tú: primeras 10 visitas con el dato de su tiempo de respuesta y la demo en el móvil.
