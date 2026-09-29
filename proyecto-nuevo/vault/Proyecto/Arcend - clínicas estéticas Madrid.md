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

## Estado 2026-09-28
**Decisión vigente:** [[Decisiones/2026-09-28 Arcend - Blindaje continuo por teléfono]]. Se entra con el Blindaje (informe 390 € + vigilancia 190 €/mes, sin permanencia), captado por teléfono con el informe ya hecho. Atención (paquetes 1 y 2 de arriba) queda solo como subida para la semana 4-8. 10.000 € en 30 días no es realista; se decide con las primeras 40 llamadas (condiciones de muerte en la decisión).

**Blindaje construido (2026-09-28):** herramienta `arcend/blindaje/` (79 tests; es la que usa `PASO_A_PASO.md` para los informes previos; si sustituye del todo al risk-scanner: SIN VERIFICAR), kit de ventas y 49 clínicas. Ruta corregida: IME en Vallehermoso 9 (Lagasca 95 es Clínica Londres, cadena); Face Clinic es un grupo de 4 centros. Ver [[Decisiones/2026-09-28 Arcend - Informe previo y N calculado por la herramienta]] y `arcend/PASO_A_PASO.md`.

**Datos de mercado** (`proyecto-nuevo/arcend/investigacion/mercado.md`; extractos del buscador, SIN VERIFICAR salvo que se diga):
- **Código correcto: U.48 "Medicina estética"** (RD 1277/2003), no U.90.
- **Tamaño:** ~350-550 clínicas cuyo negocio principal es la medicina estética en Madrid capital (extrapolación propia desde 6.305 centros U.48 en España en 2021; dato oficial por municipio pendiente del registro de la Comunidad). 80-90 % independientes (SIN VERIFICAR).
- **Sanciones:** publicidad de medicamentos con receta (toxina) = muy grave **desde 90.001 €**; TSJ Madrid confirmó 90.000 € a una clínica. ~~Caso de una multa rebajada a 6.000 € porque la clínica había corregido antes~~ **(corregido 2026-09-29):** fue una multa impuesta de 90.001 € rebajada a 6.000 € en recurso de reposición, con abogado, porque la clínica acreditó que había ido retirando contenidos y consultado a la Consejería; nunca decir que corregir evita la multa. Ver [[Aprendizajes/2026-09-29 Sanciones verificadas y el matiz del recurso]]. Frecuencia baja (~13 propuestas de sanción en ~3 años en Madrid): se vende como seguro, con captura de su propia web.
- **Competencia:** recepcionistas automáticas/bots **29-55 €/mes** (hasta ~100 €); agencias de marketing para clínicas **950-2.000 €/mes**. No se encontró ninguna tarifa pública de vigilancia continua de publicidad sanitaria.
- **Valor del paciente:** gasto medio **~1.027 €/año** (mujer, SEME). Ticket de primera visita 250-600 €. **La cifra de "8.000 €/mes perdidos" (y "1.500-5.000 € por paciente") de arriba no se sostiene con datos públicos**: el recálculo da ~600-4.000 €/mes de primer ticket.
- **Embudo realista:** 40 puertas × 20 % decisor × 8 % cierre ≈ 0,6 firmas/mes (rango 0,1-2,1), frente a las 2 del plan de Notion.
- Pendiente de verificar en el PC del usuario: contar U.48 en el registro, tramos exactos del RDL 1/2015, página de vigilancia de publicidad de la Consejería, Orden 1158/2018 (puede no existir).
