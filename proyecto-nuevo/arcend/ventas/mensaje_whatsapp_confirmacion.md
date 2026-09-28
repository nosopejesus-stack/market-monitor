# Mensajes de WhatsApp (confirmación y envío tras aceptación)

Los envía **el usuario desde su móvil**; el equipo solo los prepara.

## Reglas

- **Solo a números con permiso explícito** para escribir por WhatsApp (pedido en la llamada o en la reunión y
  anotado en `embudo.csv` como `whatsapp_ok`). Nunca al número de la clínica sin ese permiso ni a números
  sacados de internet. Nada de mensajes comerciales no solicitados (LSSI).
- **Cortos**, sin "IA", sin explicar el método, sin alarmismo.
- **El informe y los textos corregidos solo se envían tras la aceptación** (contrato firmado); los textos
  corregidos, además, en 5 días hábiles desde el pago. Antes de firmar, como mucho el resumen de una página
  si lo han pedido.
- No enviar por WhatsApp nada que contenga imágenes de pacientes: en ese caso, email.
- Cifras iguales que el resto del kit: 390 € + IVA (corrección), 190 €/mes + IVA (vigilancia, sin permanencia,
  preaviso 15 días).

## 1. Confirmación de cita (la víspera, a la recepción o al titular)

> Hola {nombre}, soy {tu_nombre}, de Arcend. Le confirmo la cita de mañana {día} a las {hora} con el Dr./la Dra.
> {apellido} en {dirección_clinica}, 10-15 minutos para revisar la publicidad de la clínica. Si necesita
> cambiarla, dígame y buscamos otro hueco. Gracias.

## 2. Recordatorio el mismo día (solo si la cita es por la tarde)

> Buenos días {nombre}. Le recuerdo que hoy a las {hora} paso por la clínica para ver con el Dr./la Dra.
> {apellido} la revisión de su publicidad. Hasta luego.

## 3. Cambio de hora (si lo piden ellos)

> Sin problema. ¿Le va bien el {día_1} a las {hora_1} o el {día_2} a las {hora_2}?

## 4. Tras la firma: datos de pago (solo tras aceptación)

> Dr./Dra. {apellido}, gracias por la confianza. Le dejo los datos para la transferencia de la corrección:
> 390 € + IVA (471,90 €), IBAN {IBAN_prestador}, concepto "{nombre_clinica} corrección". Le envío la factura a
> {email_cliente}. En 5 días hábiles desde que llegue el pago tendrá todos los textos corregidos.

## 5. Envío del informe (solo tras aceptación y por el canal aceptado)

> Dr./Dra. {apellido}, le adjunto el informe de revisión de la publicidad de {nombre_clinica} con fecha
> {fecha_revision}. Recuerde que no es asesoramiento jurídico: si algún punto le genera dudas, conviene
> validarlo con su asesor.

## 6. Entrega de los textos corregidos (en 5 días hábiles desde el pago)

> Dr./Dra. {apellido}, aquí tiene los textos corregidos, ordenados por página y publicación. Cuando usted o su
> agencia los hayan publicado, avíseme y compruebo que ha quedado todo bien y le dejo la constancia fechada.

## 7. Oferta de vigilancia (al entregar la corrección, si no la contrató)

> Una última cosa: si quiere que cada mes revisemos de nuevo la web y las redes y le avisemos de cualquier
> publicación nueva con riesgo, son 190 € + IVA al mes, sin permanencia (baja con 15 días de preaviso).
> ¿Se lo activo?

## Registro

Después de cada mensaje relevante, anota en `embudo.csv` (en `notas` de la fila correspondiente): qué se
envió y cuándo (`conf_whatsapp {fecha}`, `informe_enviado {fecha}`, `textos_entregados {fecha}`).
