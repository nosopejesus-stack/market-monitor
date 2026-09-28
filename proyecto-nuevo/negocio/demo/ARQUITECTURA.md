# Arquitectura de la instalación real

Lo que enseña la demo (`index.html`), montado de verdad con el stack gratuito de `infra/`
(n8n + Postgres + Ollama y, si se quiere, Chatwoot). Nuestro coste: 0 €. Los costes de WhatsApp y del
servidor los paga el cliente (ver `../PLAN.md`).

> Todo lo marcado **SIN VERIFICAR** hay que comprobarlo en la primera instalación de prueba
> (con un número y una cuenta de Meta propios del usuario) antes de prometerlo a un cliente.

## 1. Flujo de extremo a extremo

```
Idealista / Fotocasa / web
        │  (email de aviso de nuevo lead al buzón de la agencia)
        ▼
[n8n] WF1 Lead entrante ── Email Trigger (IMAP) o Webhook (formulario web)
        │  1. Extrae nombre, teléfono, email, referencia del piso y mensaje (reglas por portal)
        │  2. Normaliza teléfono a +34…, descarta duplicados (Postgres, tabla leads)
        │  3. Envía PLANTILLA aprobada de WhatsApp "primer_contacto" (nombre + dirección del piso)
        ▼
WhatsApp Business Cloud API (Meta) ──► móvil del comprador
        │  el comprador contesta → se abre la ventana de 24 h de mensajes libres
        ▼
[n8n] WF2 Conversación ── WhatsApp Trigger (webhook de Meta)
        │  máquina de estados por lead (Postgres): presupuesto → financiación → plazo → zona
        │  - financiación y plazo con botones interactivos (sin texto libre que interpretar)
        │  - presupuesto y zona: primero reglas (regex de importes, lista de barrios);
        │    si no encajan, Ollama (http://ollama:11434/api/chat) devuelve JSON; si duda, pasa a humano
        │  - puntuación: CALIENTE / TEMPLADO / NO CUALIFICADO (reglas fijas, explicables al cliente)
        ▼
[n8n] Google Calendar ── consulta huecos libres del agente → ofrece 2 huecos con botones
        │  el comprador elige → crea el evento en el calendario del agente → confirma por WhatsApp
        ▼
Ficha del lead cualificado al agente (email y/o WhatsApp al móvil del agente) + registro en Postgres

[n8n] WF3 Recordatorios (cron diario) → plantilla "recordatorio_visita" el día antes
[n8n] WF4 Informe mensual (cron) → leads, tiempo medio de 1.ª respuesta, visitas agendadas → email al cliente
```

### Paso a humano (siempre disponible)
- Si el comprador escribe "agente", "llamar", o pregunta algo fuera del guion (negociar precio, reservar, dudas legales),
  el bot deja de responder a ese lead y avisa al agente con el historial.
- Si Ollama no da un JSON válido o la confianza es baja → a humano, nunca inventar respuestas.
- El bot **no** da información que no esté en la ficha del piso (precio, m², habitaciones, dirección aproximada).

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
- **Piloto / pruebas (0 €):** el PC del usuario con un túnel gratuito (p. ej. Cloudflare Tunnel) delante de n8n.
  Solo para pruebas: si el PC se apaga, no hay respuestas.
- **Producción:** servidor del cliente (o pagado por el cliente) siguiendo `infra/server/GUIA.md`
  (Coolify, HTTPS, firewall, backups). Exponer **solo** la ruta de webhooks de n8n; el panel de n8n, privado.

## 3. Cuentas que necesita el cliente (las crea y paga él; nosotros no creamos cuentas)

1. **Meta Business (Business Manager / portfolio)** de la agencia, idealmente con la empresa verificada.
2. **Cuenta de WhatsApp Business Platform (Cloud API)** con un **número de teléfono** para el bot.
   - Recomendado: número nuevo dedicado. Usar el número que ya tienen en la app de WhatsApp Business
     puede ser posible ("coexistencia") pero con limitaciones: **SIN VERIFICAR**.
   - **Método de pago en Meta**: los mensajes con plantilla (el primer contacto y los recordatorios) se cobran;
     las respuestas dentro de la ventana de 24 h tras un mensaje del cliente, en principio no. Modelo y tarifas
     actuales para España: **SIN VERIFICAR** (Meta los ha cambiado varias veces).
   - **Plantillas aprobadas por Meta**: `primer_contacto`, `recordatorio_visita`. La aprobación puede tardar
     de minutos a días: **SIN VERIFICAR**.
3. **Google (Gmail o Workspace)** con el **Google Calendar de cada agente** que haga visitas, y permiso OAuth
   para que n8n lea la disponibilidad y cree eventos.
4. **Buzón donde llegan los avisos de Idealista/Fotocasa**, con acceso IMAP (o reenvío automático a un buzón
   dedicado). Formato exacto de los emails de aviso de cada portal: **SIN VERIFICAR** (pedir 3-5 emails reales
   anonimizados al cliente antes de instalar). Si el portal ofrece integración directa por API/CRM para
   profesionales: **SIN VERIFICAR**.
5. **Servidor** (o PC encendido 24/7 + túnel, solo piloto) con Docker.

## 4. Qué hace el equipo (Claude + agentes) y qué es humano

| Paso | Quién |
|---|---|
| Generar la demo personalizada con sus pisos (`build_demo.py`) | Equipo |
| Enseñar la demo, negociar, firmar contrato y encargo de tratamiento RGPD | **Usuario** + cliente |
| Crear cuentas de Meta, número de WhatsApp, verificación del negocio, método de pago | **Cliente** (con el usuario al lado) |
| Dar acceso OAuth a Google Calendar y al buzón de leads | **Cliente** |
| Pedir 3-5 emails reales de leads (anonimizados) para las reglas de extracción | **Usuario** los pide, equipo los procesa |
| Redactar plantillas de WhatsApp y guion de preguntas; enviarlas a aprobación en Meta | Equipo redacta, **cliente/usuario** las envía |
| Levantar el stack (`infra/`), crear flujos WF1-WF4 en n8n, tablas en Postgres | Equipo |
| Pruebas extremo a extremo con un móvil real haciendo de comprador | **Usuario** envía los mensajes, equipo revisa |
| Decidir la puesta en marcha (go-live) | **Cliente** |
| Atender los leads pasados a humano y las visitas | **Agentes del cliente** |
| Informe mensual y ajustes | Equipo prepara, **usuario** lo envía |

## 5. Riesgos y límites (decirlo en la venta)

- **Consentimiento y política de WhatsApp:** el comprador dejó su teléfono en el portal para ser contactado
  sobre ese piso; si eso basta como consentimiento para escribirle por WhatsApp desde una plantilla: **SIN VERIFICAR**
  (revisar política de Meta y RGPD). El primer mensaje debe identificar a la agencia y permitir darse de baja.
- **Tiempo real de respuesta:** depende de cuándo llega el email del portal y de la frecuencia de lectura del buzón.
  La demo muestra 40 s; el objetivo del plan es < 2 min. Medirlo en el piloto antes de prometer cifras.
- **Calidad de la cualificación:** preguntas fijas + botones reducen errores; el LLM solo extrae datos, no negocia.
- **Dependencia de Meta y Google:** si cambian API o precios, hay que ajustar. Sin permanencia para el cliente.
- **Datos personales:** los leads viven en el servidor del cliente; nada en servicios nuestros. Backups de Postgres
  según `infra/server/GUIA.md`.
