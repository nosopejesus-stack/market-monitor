# Arquitectura de la instalación real

Lo que enseña la demo (`index.html`), montado de verdad con el stack gratuito de `infra/`
(n8n + Postgres + Ollama y, si se quiere, Chatwoot). Nuestro coste: 0 €. Los costes de WhatsApp y del
servidor los paga el cliente (ver `../PLAN.md`).

> Todo lo marcado **SIN VERIFICAR** hay que comprobarlo en la primera instalación de prueba
> (con un número y una cuenta de Meta propios del usuario) antes de prometerlo a un cliente.

## 0. Modelo de datos (único)

- **Todo corre en un servidor contratado por el cliente, a su nombre** (y pagado por él), siguiendo
  `infra/server/GUIA.md`. Los leads, conversaciones y fichas viven solo ahí. Nosotros no guardamos datos de
  leads en ningún servicio ni equipo propio.
- **Prohibido usar datos reales de leads en el PC de pruebas o detrás del túnel.** El PC del usuario con túnel
  gratuito sirve solo para probar los flujos con **datos ficticios** (comprador y móvil de prueba del propio usuario).
- Las demos (`build_demo.py`) usan pisos publicados que da la agencia con su permiso y un comprador inventado.

## 1. Flujo de extremo a extremo

```
Idealista / Fotocasa / web
        │  (email de aviso de nuevo lead al buzón de la agencia)
        ▼
[n8n] WF1 Lead entrante ── Email Trigger (IMAP) o Webhook (formulario web)
        │  1. Extrae nombre, teléfono (si viene), email, referencia del piso y mensaje (reglas por portal)
        │  2. Descarta duplicados (Postgres, tabla leads)
        │  3. PRIMER CONTACTO = EMAIL automático de respuesta al comprador (objetivo < 2 min):
        │     identifica a la agencia, datos del piso, enlace a la política de privacidad y
        │     botón "Seguir por WhatsApp" = enlace wa.me/<número del asistente>?text=<ref del piso>
        │     (NO se envía WhatsApp saliente como primer mensaje)
        ▼
El comprador pulsa el botón y ABRE ÉL la conversación de WhatsApp
        │  → se abre la ventana de 24 h de mensajes libres, con consentimiento limpio
        ▼
[n8n] WF2 Conversación ── WhatsApp Trigger (webhook de Meta)
        │  primer mensaje: "Soy el asistente automático de <agencia>" + info de privacidad (URL)
        │                  + "Responde BAJA para no recibir más mensajes"
        │  máquina de estados por lead (Postgres): presupuesto → financiación → plazo → zona
        │  - financiación y plazo con botones interactivos (sin texto libre que interpretar)
        │  - presupuesto y zona: primero reglas (regex de importes, lista de barrios);
        │    si no encajan, Ollama (http://ollama:11434/api/chat) devuelve JSON; si duda, pasa a humano
        │  - rama: CALIENTE (presupuesto >= precio) / REVISAR PRESUPUESTO / NO CUALIFICADO (reglas fijas)
        │  - "BAJA" → marca el lead como dado de baja y no se le escribe más
        ▼
[n8n] Google Calendar ── consulta huecos libres del agente → ofrece 2 huecos con botones
        │  el comprador elige → crea el evento en el calendario del agente → confirma por WhatsApp
        │  y pregunta si quiere recordatorio (opt-in explícito: "Responde SÍ")
        ▼
Ficha del lead cualificado al agente (email y/o WhatsApp al móvil del agente) + registro en Postgres

[n8n] WF3 Recordatorios (cron diario) → solo a quien respondió SÍ: dentro de la ventana de 24 h, mensaje libre;
      fuera de ella, plantilla aprobada "recordatorio_visita" (solo con ese opt-in explícito)
[n8n] WF4 Informe mensual (cron) → email al cliente con: leads recibidos, leads respondidos, tiempo medio de
      primera respuesta, % de leads con teléfono, leads cualificados, visitas agendadas y leads por franja
      horaria (dentro / fuera de horario, noches y fines de semana)
```

### Paso a humano (siempre disponible)
- Si el comprador escribe "agente", "llamar", o pregunta algo fuera del guion (negociar precio, reservar, dudas legales),
  el asistente automático deja de responder a ese lead y avisa al agente con el historial.
- Si Ollama no da un JSON válido o la confianza es baja → a humano, nunca inventar respuestas.
- El asistente automático **no** da información que no esté en la ficha del piso (precio, m², habitaciones, dirección aproximada).

### Opción con Chatwoot (bandeja compartida)
Para agencias que quieren ver y contestar las conversaciones desde un panel: el número de WhatsApp se conecta a
Chatwoot (canal WhatsApp Cloud) y n8n recibe los mensajes por el webhook de Chatwoot en vez de directamente de Meta.
Más cómodo para el agente, una pieza más que mantener. **Por defecto: n8n directo** (menos piezas, más rápido de instalar).

## 2. Piezas y dónde corren

| Pieza | Del stack `infra/` | Nota |
|---|---|---|
| n8n | Sí (`docker-compose.yml`) | Flujos WF1-WF4, credenciales cifradas con `N8N_ENCRYPTION_KEY` |
| Postgres 17 | Sí | Tablas `leads`, `mensajes`, `pisos` (base propia, no la de n8n) |
| Ollama | Sí | Modelo pequeño (p. ej. `llama3.2:3b`) solo para extraer datos de texto libre. En CPU tarda segundos: **SIN VERIFICAR** en el hardware del cliente |
| Chatwoot | Sí (opcional) | Solo si el cliente quiere bandeja compartida |
| WhatsApp Business Cloud API | No (Meta) | Lo contrata y paga el cliente |
| Google Calendar | No (Google) | Calendario de cada agente |

**Requisito clave:** Meta tiene que poder llamar al webhook de n8n por **HTTPS público**. El stack local de
`infra/` escucha solo en `127.0.0.1`, así que:
- **Pruebas (0 €):** el PC del usuario con un túnel gratuito (p. ej. Cloudflare Tunnel) delante de n8n,
  **solo con datos ficticios**. Nunca leads reales en el PC ni en el túnel. Si el PC se apaga, no hay respuestas.
- **Cliente (piloto y producción):** servidor contratado por el cliente a su nombre, siguiendo
  `infra/server/GUIA.md` (Coolify, HTTPS, firewall, backups). Exponer **solo** la ruta de webhooks de n8n;
  el panel de n8n, privado.

## 3. Cuentas que necesita el cliente (las crea y paga él; nosotros no creamos cuentas)

1. **Meta Business (Business Manager / portfolio)** de la agencia, idealmente con la empresa verificada.
2. **Cuenta de WhatsApp Business Platform (Cloud API)** con un **número de teléfono** para el asistente automático.
   - Recomendado: número nuevo dedicado. Usar el número que ya tienen en la app de WhatsApp Business
     puede ser posible ("coexistencia") pero con limitaciones: **SIN VERIFICAR**.
   - **Método de pago en Meta** (tarjeta del cliente): según `../PLAN.md`, desde el 1-oct-2026 Meta cobra
     también los mensajes dentro de la ventana de 24 h. Tarifas actuales para España: **SIN VERIFICAR**.
   - **Plantillas aprobadas por Meta**: solo `recordatorio_visita`, y solo se usa con opt-in explícito del
     comprador. No hay plantilla de primer contacto: el primer contacto es el email. La aprobación puede tardar
     de minutos a días: **SIN VERIFICAR**.
3. **Google (Gmail o Workspace)** con el **Google Calendar de cada agente** que haga visitas, y permiso OAuth
   para que n8n lea la disponibilidad y cree eventos.
4. **Buzón donde llegan los avisos de Idealista/Fotocasa**, con acceso IMAP (o reenvío automático a un buzón
   dedicado) y **SMTP para enviar el email automático de respuesta** desde la dirección de la agencia. Formato exacto de los emails de aviso de cada portal: **SIN VERIFICAR** (pedir 3-5 emails reales
   anonimizados al cliente antes de instalar). Si el portal ofrece integración directa por API/CRM para
   profesionales: **SIN VERIFICAR**.
5. **Servidor contratado por el cliente a su nombre**, con Docker. (El PC + túnel es solo para pruebas con datos ficticios.)

## 4. Qué hace el equipo (Claude + agentes) y qué es humano

| Paso | Quién |
|---|---|
| Generar la demo personalizada con sus pisos (`build_demo.py`) | Equipo |
| Enseñar la demo, negociar, firmar contrato y encargo de tratamiento RGPD | **Usuario** + cliente |
| Crear cuentas de Meta, número de WhatsApp, verificación del negocio, método de pago | **Cliente** (con el usuario al lado) |
| Dar acceso OAuth a Google Calendar y al buzón de leads | **Cliente** |
| Pedir 3-5 emails reales de leads (anonimizados) para las reglas de extracción | **Usuario** los pide, equipo los procesa |
| Redactar email automático, plantilla `recordatorio_visita` y guion de preguntas; enviar la plantilla a aprobación en Meta | Equipo redacta, **cliente/usuario** la envía |
| Levantar el stack (`infra/`), crear flujos WF1-WF4 en n8n, tablas en Postgres | Equipo |
| Pruebas extremo a extremo con datos ficticios y un móvil del usuario haciendo de comprador | **Usuario** envía los mensajes, equipo revisa |
| Decidir la puesta en marcha (go-live) | **Cliente** |
| Atender los leads pasados a humano y las visitas | **Agentes del cliente** |
| Informe mensual y ajustes | Equipo prepara, **usuario** lo envía |

## 5. Riesgos y límites (decirlo en la venta)

- **Consentimiento y política de WhatsApp:** un teléfono dejado en un portal no es opt-in para WhatsApp, así que
  no se escribe primero por WhatsApp: el primer contacto es el email y es el comprador quien abre la conversación.
  WhatsApp saliente (plantilla) solo con opt-in explícito. El primer mensaje del asistente lo identifica como
  automático (Ley de IA de la UE, art. 50.1), enlaza la política de privacidad y ofrece BAJA.
- **Tiempo real de respuesta:** depende de cuándo llega el email del portal y de la frecuencia de lectura del buzón.
  La demo lo muestra como "objetivo < 2 min (simulado)". Medirlo en el piloto antes de prometer cifras.
- **Cuántos compradores pulsan "Seguir por WhatsApp":** **SIN VERIFICAR**. Los que no lo pulsan reciben solo el
  email; el WF4 lo mide (leads respondidos frente a cualificados).
- **Calidad de la cualificación:** preguntas fijas + botones reducen errores; el LLM solo extrae datos, no negocia.
- **Dependencia de Meta y Google:** si cambian API o precios, hay que ajustar. Sin permanencia para el cliente.
- **Datos personales:** los leads viven solo en el servidor contratado por el cliente a su nombre; nada en
  servicios ni equipos nuestros (tampoco en el PC de pruebas). Backups de Postgres
  según `infra/server/GUIA.md`.
