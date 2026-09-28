# Consultas de prueba (velocidad de respuesta)

Objetivo: medir cuánto tarda cada agencia en contestar a un interesado real. Ese dato es el
argumento de apertura de la visita (ver `guion_visita.md`).

**Las envías tú desde tu móvil / tu cuenta.** El equipo solo prepara los textos y registra los datos.

## Cómo usarlas

1. Elige un piso concreto de la agencia en Idealista/Fotocasa y copia el enlace.
2. Elige una variante (rótalas; no uses siempre la misma) y sustituye `{enlace}`.
   - Por el **formulario del portal** no hace falta el enlace (el mensaje ya va asociado al anuncio): quita esa línea.
   - Por **WhatsApp de la agencia**, pega el enlace.
3. Usa tus datos reales (nombre, email, teléfono). No inventes circunstancias (hipoteca aprobada,
   venta de otra vivienda, etc.): los textos están escritos para no necesitarlo.
4. **Una sola consulta por agencia.** Reparte las agencias entre tres franjas, más o menos a partes iguales:
   - **A — laborable mañana** (martes a jueves, 10:00-12:00).
   - **B — laborable noche** (lunes a jueves, 20:00 o más tarde).
   - **C — sábado** (cualquier hora; mejor por la tarde).
5. Anota **al momento** en `proyecto-nuevo/negocio/prospectos/pruebas_respuesta.csv` (fuente única
   de estos datos): envío con fecha y hora exactas, canal, variante y franja. Cuando respondan: fecha y
   hora exactas de la respuesta, por qué canal, si trae teléfono y la calidad. Si pasan 72 h sin
   respuesta, anota `sin_respuesta` en `calidad_respuesta` y deja vacíos `fecha_hora_respuesta` y `minutos`.
6. Haz captura de pantalla del envío y de la respuesta (con la hora visible). En la visita
   puede que te pregunten "¿seguro?"; la captura lo zanja.

Cabecera de `pruebas_respuesta.csv` (la misma que tiene el fichero; no la cambies aquí sin cambiarla allí):

```
id_agencia,canal,variante,franja,fecha_hora_envio,fecha_hora_respuesta,minutos,canal_respuesta,trae_telefono,calidad_respuesta,notas
```

- `id_agencia`: el mismo id que en `prospectos/agencias_madrid.csv`.
- `canal`: por dónde enviaste la consulta (`idealista`, `fotocasa`, `web`, `whatsapp`, `email`).
- `variante`: `V1`-`V5`. `franja`: `A`, `B` o `C` (ver punto 4).
- `fecha_hora_envio` / `fecha_hora_respuesta`: `AAAA-MM-DD hh:mm`.
- `minutos`: minutos entre envío y primera respuesta.
- `canal_respuesta`: `email`, `whatsapp`, `llamada`, `portal`.
- `trae_telefono`: `si` / `no`, si la respuesta de la agencia incluye un teléfono de contacto.
- `calidad_respuesta`: `buena` (responde a la pregunta), `generica` (plantilla sin responder), `sin_respuesta`.
- `notas`: resumen de una línea de la respuesta.

## Las 5 variantes

**V1 — disponibilidad (corta)**
> Hola, buenas. Me interesa este piso: {enlace}
> ¿Sigue disponible? Gracias.

**V2 — gastos**
> Hola. He visto este piso ({enlace}) y me gusta. ¿Me podríais decir cuánto son los gastos de comunidad y el IBI aproximado? Gracias.

**V3 — cómo son las visitas**
> Buenas tardes. Estoy interesado/a en el piso de {enlace}. ¿Qué días soléis enseñarlo? Gracias, un saludo.

**V4 — estado del piso**
> Hola, sobre este anuncio: {enlace}
> ¿El piso está para entrar a vivir o necesita reforma? ¿Tiene ascensor? Gracias.

**V5 — plazos**
> Buenas. Pregunta rápida sobre {enlace}: ¿el piso está libre ya o hay inquilinos? ¿Para cuándo estaría disponible? Gracias.

Notas:
- Si el anuncio ya indica el dato que preguntas (p. ej. tiene ascensor o los gastos de comunidad), usa otra variante: una pregunta cuya respuesta ya está en el anuncio parece falsa.
- No mandes la misma variante a dos agencias de la misma calle o zona el mismo día.

## Nota ética (léela antes de enviar)

- Seamos honestos: es una **consulta con pretexto mínimo** (no vas a comprar ese piso), **que se revela
  en la visita**. Para que el pretexto sea el mínimo posible: preguntas normales de comprador, tus datos
  reales, ninguna circunstancia inventada, **no se piden visitas ni información sensible del vendedor**
  (nada de precio mínimo, motivo de venta, situación del propietario, etc.).
- **No hagas perder tiempo a la agencia.** Si responden, contesta una sola vez, agradeciendo y
  cerrando con educación. **No pidas visita ni aceptes una que te ofrezcan.** Ejemplo:
  > Muchas gracias por la información, muy amables. De momento lo dejo, si cambia algo os escribo. Un saludo.
- Si te **llaman**, igual: agradece la llamada, di que de momento no vas a seguir adelante y cuelga
  con educación. Anota la hora de la llamada como hora de respuesta.
- **En la visita di la verdad:** que la consulta la enviaste tú para medir su tiempo de respuesta.
  Esconderlo y que lo descubran después destruye la confianza (ver `guion_visita.md`).
- Si una agencia contesta muy rápido (p. ej. en menos de 15 min, a cualquier hora), probablemente no
  necesita el servicio: pásala al final de la lista y no la presiones.
