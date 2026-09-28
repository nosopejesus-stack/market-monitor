---
fuente: Notion "Proyecto Arcend · Clínicas estéticas Madrid" (https://app.notion.com/p/3cf7bfe6e0dd8113a967e86ebc3331c5), estado a 2026-09-02
---
# Arcend · clínicas de medicina estética de Madrid (no cadenas)

**Proyecto principal del usuario.** Resumen del documento de traspaso de Notion (el original manda).

- **Cliente:** clínicas de medicina estética independientes de Madrid. Valor por paciente 1.500-5.000 €.
- **Oferta y precio:** 1 · Atención: 1.200 € implantación + 890 €/mes. 2 · Atención + Blindaje: 1.900 € + 1.290 €/mes. La implantación se cobra el día de la firma.
- **Aritmética de venta:** ~20 llamadas perdidas/mes → 4 pacientes reales → 8.000 €/mes perdidos vs 890 € de servicio.
- **Embudo previsto:** 40 puertas → 16 conversaciones con decisor → 8 informes → 2 firmas/mes. Previsión: sep 4.180 €, oct 5.960 €, nov 9.830 € (6.230 €/mes recurrentes).
- **risk-scanner v3** (repo en el PC del usuario, `C:\Users\nitrpc\dev\risk-scanner`, perfil CLÍNICA): OSINT pasivo con cumplimiento sanitario (registro del centro, colegiado, publicidad sancionable), reputación, huella tecnológica, DNS, Wayback; puntuación 0-100. Probado con cemestetic.es: 74/100.
- **Límite legal no negociable:** solo comprobación pasiva; nada de escaneo de puertos ni pruebas de vulnerabilidades (art. 197 bis Código Penal). Cada informe declara que solo usó información pública.
- **Ruta inicial (9):** Chamberí: Clínica DA, Blue Moon, Golden Estética, ODA Aesthetic, Templa. Salamanca: IME, Face Clinic, Felicidad Carrera, Cemestetic.
- **Reglas de comunicación:** no decir "IA" al cliente; no explicar cómo está montado; pedir la decisión en la reunión.
- **Autónomo:** alta solo tras el primer sí, fechada el día de la primera factura.

## Riesgos detectados por el equipo (2026-09-28)
- El ciclo 01 de money-engine descartó la "recepcionista IA para clínicas" por estar comoditizada a 29-55 €/mes (Ringuno, Clinicbot, Clara). Si "Atención" se percibe como eso, 890 €/mes no se sostiene: el diferencial tiene que ser el servicio hecho + **Blindaje** (cumplimiento sanitario y riesgo), no el bot.
- Lo investigado hoy para WhatsApp (opt-in, plantillas, cobro de Meta desde 1-oct-2026) y la Ley de IA art. 50.1 (el asistente debe decir que es automático desde 2-ago-2026) aplica igual a las clínicas. Choca con la regla "no decir IA": se puede no hablar de IA en la venta, pero el asistente sí debe identificarse como automático ante el paciente.
