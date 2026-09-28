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
5. Anota **al momento** en `proyecto-nuevo/negocio/prospectos/pruebas_respuesta.csv`:
   hora exacta de envío (hh:mm), canal, variante y franja. Cuando respondan: hora exacta de la
   respuesta, por qué canal (email, WhatsApp, llamada) y un resumen de una línea. Si pasan 72 h sin
   respuesta, anota `sin_respuesta`.
6. Haz captura de pantalla del envío y de la respuesta (con la hora visible). En la visita
   puede que te pregunten "¿seguro?"; la captura lo zanja.

Cabecera sugerida para `pruebas_respuesta.csv` (si el fichero aún no existe):

```
id_agencia,agencia,enlace_anuncio,canal_envio,variante,franja,fecha_envio,hora_envio,fecha_respuesta,hora_respuesta,minutos_hasta_respuesta,canal_respuesta,resumen_respuesta,notas
```

## Las 6 variantes

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

**V5 — precio**
> Hola. Me interesa este piso: {enlace}. ¿El precio es negociable o ya está ajustado? Gracias.

**V6 — plazos**
> Buenas. Pregunta rápida sobre {enlace}: ¿el piso está libre ya o hay inquilinos? ¿Para cuándo estaría disponible? Gracias.

Notas:
- Si el anuncio ya indica el dato que preguntas (p. ej. tiene ascensor o los gastos de comunidad), usa otra variante: una pregunta cuya respuesta ya está en el anuncio parece falsa.
- No mandes la misma variante a dos agencias de la misma calle o zona el mismo día.

## Nota ética (léela antes de enviar)

- Son **consultas reales de mercado**: preguntas normales que haría cualquier comprador. No damos datos
  falsos ni pedimos nada fuera de lo habitual.
- **No hagas perder tiempo a la agencia.** Si responden, contesta una sola vez, agradeciendo y
  cerrando con educación. **No pidas visita ni aceptes una que te ofrezcan.** Ejemplo:
  > Muchas gracias por la información, muy amables. De momento lo dejo, si cambia algo os escribo. Un saludo.
- Si te **llaman**, igual: agradece la llamada, di que de momento no vas a seguir adelante y cuelga
  con educación. Anota la hora de la llamada como hora de respuesta.
- **En la visita di la verdad:** que la consulta la enviaste tú para medir su tiempo de respuesta.
  Esconderlo y que lo descubran después destruye la confianza (ver `guion_visita.md`).
- Si una agencia contesta muy rápido (p. ej. en menos de 15 min, a cualquier hora), probablemente no
  necesita el servicio: pásala al final de la lista y no la presiones.
