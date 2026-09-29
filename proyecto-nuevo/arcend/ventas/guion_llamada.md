# Guion de llamada a recepción (60-90 s)

Objetivo único: **10-15 minutos con el/la titular (médico/a propietario/a) esta semana o la siguiente.**
No se vende por teléfono, no se da precio, no se explica el método.

Cifras del kit (iguales en todos los documentos de `arcend/ventas/`): **390 €** corrección (pago único),
**190 €/mes** vigilancia, sin permanencia, preaviso 15 días; entrega de la corrección en 5 días hábiles
desde el cobro. Precios sin IVA.

## Reglas (no negociables)

- **Nunca** decir "IA", "automático", "herramienta", "escáner" ni explicar cómo se hace la revisión.
  Si preguntan: "Revisamos la publicidad contra la normativa pública de publicidad sanitaria; el método es nuestro".
- **No mentir ni exagerar.** Solo se llama con el informe PREVIO de esa clínica ya hecho
  (`python blindaje.py URL --nombre "X" --previo`), y **N = el campo `n_puntos_norma` de `informe.json`**:
  lo calcula la herramienta (reglas distintas con norma concreta, deduplicadas: toxina/medicamento con
  receta, falta del nº de registro sanitario, promesas de resultado o "sin riesgo", etc.). No se cuenta a
  mano. Si `n_puntos_norma` es 0 (solo recomendaciones de buena práctica), no se usa este anzuelo: se dice
  "puntos de mejora", o no se llama.
- **No alarmista:** nada de "le van a multar", "está en peligro", "la Consejería sanciona". Nunca se
  afirma que habrá sanción; como mucho, que esos puntos "pueden dar lugar a un requerimiento".
  Tono de profesional que avisa.
- **No se envía nada que no pidan.** Nada de email comercial en frío (LSSI).
- **SIN VERIFICAR:** llamadas comerciales a una clínica. A una sociedad (S.L.) es comunicación entre
  empresas; si la clínica es de un profesional persona física, la Ley 11/2022 General de Telecomunicaciones
  (art. 66) puede limitar las llamadas comerciales no consentidas. Hasta confirmarlo: si dicen "no nos llamen",
  se anota `no_llamar` y no se vuelve a llamar nunca.

## Antes de marcar (1 min)

- Comprueba que la clínica figura inscrita en el Registro de centros sanitarios de la Comunidad de Madrid
  (si no aparece, no se llama hasta aclararlo).
- Abre el informe previo de la clínica: nombre del/de la titular (si figura en su web), N (`n_puntos_norma`)
  y los 3 hallazgos principales (norma y gravedad).
- Ten a mano el calendario con 3 huecos concretos (días y horas).
- Crea la fila en `embudo.csv` si no existe.

## Guion

**1. Saludo y a quién buscas (10 s)**
> "Buenos días, soy {tu_nombre}, de Arcend. ¿Me podría ayudar? Quería hablar un momento con el Dr./la Dra.
> {apellido_titular}, o saber cuándo le viene bien."

**2. Motivo (20 s) — el anzuelo**
> "Le explico para que usted se lo pueda trasladar: he revisado la publicidad de su web y hay **{N} puntos**
> que la normativa de publicidad sanitaria no permite.
> Tengo el informe impreso con cada punto, la norma y su gravedad. Me bastan 10 o 15 minutos con el Dr./la Dra.
> para enseñárselo."
- Si preguntan "¿y qué pasa si no se corrige?": "Son puntos que pueden dar lugar a un requerimiento; por eso
  conviene verlos." Nada más.

**3. Pedir la cita con dos opciones cerradas (15 s)**
> "¿Le vendría mejor el {día_1} a las {hora_1} o el {día_2} a las {hora_2}? Puede ser en la clínica, entre
> pacientes, o a primera o última hora."

**4. Confirmar y cerrar (15 s)**
> "Perfecto, apunto el {día} a las {hora} con el Dr./la Dra. {apellido}. ¿Le importa que le confirme la
> víspera por WhatsApp a este número o a otro que me diga?"
- Solo si dice que sí → anota el número y el permiso en `notas` (`whatsapp_ok`). Mensajes en
  `mensaje_whatsapp_confirmacion.md`.
- Si no quiere WhatsApp → confirmas la víspera por teléfono.

> "Muchas gracias, {nombre_recepcion}. Hasta el {día}."

## Si pasa esto

**"¿De qué empresa? ¿Qué venden?"**
> "Arcend. Revisamos la publicidad de clínicas de medicina estética para que cumpla la normativa sanitaria
> y la corregimos. Por eso he mirado su web antes de llamar."

**"Mándelo por email" / "envíeme información"**
- Es consentimiento para ese envío (LSSI: comunicación solicitada). Pide el email **y di qué vas a enviar**:
> "Claro. ¿A qué email se lo envío? Le mando un resumen con los {N} puntos, la norma y la gravedad de
> cada uno. Las correcciones se las explico al Dr./la Dra. en 10 minutos; ¿le propongo ya el {día_1}
> a las {hora_1} en el mismo email?"
- Envía **solo** a esa dirección, **solo** lo acordado: el informe PREVIO (`--previo`: los N puntos con
  norma y gravedad; **sin** textos corregidos ni precios salvo que los pidan). Lo envías tú desde tu correo.
  El informe completo con textos corregidos es el entregable de los 390 € y solo se genera tras el cobro.
- Anota en `notas`: `email_solicitado: {email}, fecha, qué se envió`. Llama a los 2 días hábiles:
  "¿Pudo verlo el Dr./la Dra.? ¿Le va bien el {día}?"

**"No le interesa"** (la recepción)
> "Lo entiendo. Solo le pido que se lo comente: son {N} puntos concretos de su web. Si el Dr./la Dra.
> prefiere no verlo, no insisto. ¿Le llamo el {día} para saber qué le ha dicho?"
- Si repiten que no → "Gracias por su tiempo, que tenga buen día." Etapa `perdido`, motivo literal en notas.
- Si dicen "no vuelvan a llamar" → `perdido` + `no_llamar`. No se insiste nunca.

**"No le interesa"** (el/la titular al teléfono)
> "Entendido. Una sola cosa y le dejo: uno de los puntos es {hallazgo_mas_grave, en una frase}.
> Si quiere, le envío el resumen por email y lo mira cuando pueda." — Si dice que no: gracias y `perdido`.

**El/la titular no está / está con pacientes**
> "¿Cuándo suele estar más tranquilo/a, a primera hora o al final del día? ¿Le puedo dejar reservada una cita
> de 10 minutos en su agenda el {día} a las {hora}? Si no le viene bien, que me llamen al {tu_telefono}."
- Si la recepción puede agendar → cierra la cita como en el paso 4.
- Si no → pide la mejor franja para volver a llamar y anótala en `notas` (`rellamar: {día} {franja}`).
  Máximo 3 intentos; después, `perdido` (motivo: `sin_acceso_titular`).

**El/la titular se pone al teléfono**
> "Gracias por atenderme, Dr./Dra. Seré breve: he revisado la publicidad de su web y hay {N} puntos que la
> normativa de publicidad sanitaria no permite. Tengo el informe con cada punto, la norma y su gravedad.
> ¿Me da 10 minutos el {día_1} o el {día_2}?"
- Si pregunta el precio: "390 € la corrección completa, sin IVA; se lo explico con el informe delante."
  No negociar por teléfono.

**"¿Cómo han sacado esto?" / "¿Quién les ha mandado?"**
> "Nadie. Es información pública: su web y sus redes, revisadas contra la normativa de publicidad sanitaria.
> No hemos entrado en ningún sistema."

**"¿Son de la Consejería / inspección?"**
> "No, en absoluto. Arcend es un servicio privado; no tenemos ninguna relación con la Administración."

## Registro en `embudo.csv` (el mismo día)

Columnas: `id,clinica,telefono,web,fecha,etapa,importe,notas`.
- `id`: `C001`, `C002`… (uno por clínica, fijo). **Una fila por cambio de etapa**, repitiendo el `id`.
- `fecha`: AAAA-MM-DD. `importe`: solo en `firmado` y `cobrado`, en euros **sin IVA** (390 o 190).
- `notas`: sin comas (usar `;`), o entre comillas.

| etapa | Cuándo |
|---|---|
| `llamada` | Llamada hecha (resultado en notas: `cita`, `email_solicitado`, `rellamar`, `no_interesa`) |
| `reunion_agendada` | Cita con el/la titular fijada (fecha y hora en notas; `whatsapp_ok` si lo aceptó) |
| `reunion` | Reunión hecha con el informe delante (resultado y objeción principal en notas) |
| `firmado` | Contrato firmado (`importe` 390; en notas si incluye vigilancia) |
| `cobrado` | Pago recibido (`importe` 390 o 190; en notas qué pago: `corrección` o `vigilancia {mes}`) |
| `perdido` | Descartado; motivo literal en notas (y `no_llamar` si lo pidieron) |

Métrica de las condiciones de muerte (`DECISION.md`): de las primeras 40 filas `llamada`, ¿cuántas llegan a
`reunion`? Si son < 3 → cambiar guion o pasar a visita en persona.


## Frase del gancho (la da la herramienta, columna `frase_llamada` de RESUMEN.csv)
- Si hay puntos con norma concreta: "He revisado la publicidad de su web y hay {N} puntos que la normativa de publicidad sanitaria no permite."
- Si solo hay puntos a revisar: "He revisado la publicidad de su web y hay {M} puntos que conviene revisar según la normativa de publicidad sanitaria."
- Si la columna está vacía: no se usa gancho (o se revisa a mano antes de llamar).
