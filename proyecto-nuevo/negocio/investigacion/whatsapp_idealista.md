---
fecha: 2026-09-28
autor: investigador
estado: verificación parcial (red bloqueada, ver "Método")
---
# WhatsApp + leads de Idealista/Fotocasa: ¿es viable "respuesta por WhatsApp en <2 min"?

## Método y límites (leer primero)
- Desde el contenedor cloud **no se pudieron abrir** las fuentes primarias: `developers.facebook.com`,
  `business.whatsapp.com`, `whatsapp.com`, `eur-lex.europa.eu`, `artificialintelligenceact.eu`,
  `idealista.com`, `fotocasa.es` y `docs.360dialog.com` devolvieron EGRESS_BLOCKED / 403 del proxy.
- Solo funcionó el **buscador web**. Todo lo marcado "(fragmento del buscador)" procede del extracto que
  el buscador devuelve de la **URL oficial citada**, no de una lectura completa de la página.
  Lo que solo aparece en webs de terceros se marca **SIN VERIFICAR**.
- Antes de firmar con un cliente, alguien con internet normal debe abrir las URL marcadas y confirmar.

## Respuesta directa
**Viable con matices; hay que reformular la promesa.** Lo que sí se puede prometer es *"respuesta en menos
de 2 minutos, 24/7"*; el **canal** depende de qué dato deje el lead y del consentimiento:
- Si el lead dejó **teléfono**, se le puede escribir primero por WhatsApp **solo con una plantilla aprobada
  por Meta** y con un opt-in defendible. Es una zona gris: haber dejado el teléfono en Idealista para
  que "le contacten" no es claramente un opt-in para WhatsApp.
- Si el lead solo dejó **email** o escribió por el **chat del portal**, no hay WhatsApp posible al primer
  contacto: se responde por email en menos de 2 min con un enlace `wa.me` para que **sea él quien abra**
  WhatsApp (así la conversación es iniciada por el usuario, el opt-in está limpio y la ventana de 24 h se abre sola).

## 1. WhatsApp Business Platform (Cloud API)

**¿Puede la empresa escribir primero?** Sí, pero solo con **plantillas** (message templates) aprobadas.
- "Templates are the only message type that can be sent outside of a customer service window" (fragmento del buscador)
  — https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing
- Al escribir el usuario se abre una **ventana de atención de 24 h** en la que se pueden mandar mensajes libres
  (no plantilla) — https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/send-messages (fragmento del buscador)

**Opt-in (Política de mensajería de WhatsApp Business)**:
- "You may only contact people on WhatsApp if: (a) they have given you their mobile phone number [...] and
  (b) you have received opt-in permission from the recipient confirming that they wish to receive subsequent
  messages or calls from you." La empresa es "solely responsible for determining the method of opt-in" y de
  cumplir la ley aplicable. — https://business.whatsapp.com/policy (fragmento del buscador)
- El opt-in debe indicar claramente que la persona acepta recibir mensajes **y el nombre de la empresa**.
  — https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in (fragmento del buscador)
- **Implicación:** el formulario de Idealista/Fotocasa lo gestiona el portal y no incluye (que sepamos) una
  casilla "acepto WhatsApp de la agencia X". **SIN VERIFICAR** si el aviso de privacidad del portal cubre esto.
  Riesgo práctico: bloqueos/denuncias bajan la *quality rating* y Meta limita el número.

**Categorías de plantilla**: marketing, utility, authentication.
- Utility = "follow-up on user actions or requests"; si Meta considera que una plantilla "utility" es de
  marketing, la aprueba como MARKETING. — https://developers.facebook.com/documentation/business-messaging/whatsapp/templates/template-categorization (fragmento del buscador)
- Una plantilla tipo "Hola {{1}}, has pedido información del piso {{2}} en Idealista. ¿Te va bien que te
  hagamos 3 preguntas para organizar la visita?" encaja en utility (respuesta a una petición del usuario).
  **SIN VERIFICAR** que Meta no la recategorice como marketing.

**Precio (lo paga el cliente, no nosotros)**:
- Desde el 1-jul-2025 Meta cobra **por mensaje** (plantilla), no por conversación; varía según categoría y
  país del destinatario. — https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing (fragmento del buscador)
- España, **SIN VERIFICAR** (solo webs de terceros, p. ej. https://blueticks.co/blog/whatsapp-business-pricing-europe-2026):
  marketing ~0,0509 €/msg, utility ~0,0166 €/msg (+21 % IVA). Con 100 leads/mes: ~2-6 €/mes en plantillas.
- **Cambio importante (1-oct-2026, es decir, en 3 días):** Meta pasa a cobrar también los mensajes de
  servicio y las utility dentro de la ventana de 24 h, que eran gratis. Si la cuenta no tiene **método de pago
  antes del 30-sep-2026**, Meta deja de entregar mensajes de servicio.
  — https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/non-template-messages (fragmento del buscador)
  **SIN VERIFICAR:** importe por mensaje de servicio en España y si existe un cupo gratis mensual (terceros hablan de 1.000/número; el extracto oficial no lo confirmó).
- **Política de IA de Meta:** desde el 15-ene-2026 (y desde el 15-oct-2025 para cuentas nuevas) los Business
  Solution Terms prohíben chatbots de IA **de propósito general**; los bots limitados a un proceso de negocio
  (cualificar un lead, agendar visita) siguen permitidos. **SIN VERIFICAR** en la fuente primaria (solo prensa:
  https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform/).
  Nuestro bot debe negarse a hablar de temas ajenos al inmueble.

## 2. Coexistence (mismo número en la app WhatsApp Business y en la API)
- **Sí existe.** Meta lo llama "Onboarding WhatsApp Business app users (aka Coexistence)", vía Embedded Signup.
  — https://developers.facebook.com/docs/whatsapp/embedded-signup/custom-flows/onboarding-business-app-users/ (fragmento del buscador)
- Limitaciones oficiales (fragmento del buscador, misma URL y https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users/):
  - App WhatsApp Business **≥ 2.24.17**.
  - Caudal fijo **20 mensajes/s** (de sobra para una agencia).
  - Al conectar se desvinculan los dispositivos acompañantes; se pueden volver a enlazar **salvo WhatsApp para Windows y WearOS**.
  - Hay webhooks `account_offboarded`/`account_reconnected` (changelog: https://developers.facebook.com/documentation/business-messaging/whatsapp/changelog).
- Según terceros (**SIN VERIFICAR**): beta desde feb-2025; al principio **no disponible en UE/EEE/UK** y
  ampliado a la UE a finales de 2025 (https://chakrahq.com/article/whatsapp-coexistence-live-eu-uk-europe-whatsapp-business-for-api-live/);
  sincroniza hasta 6 meses de historial (sin grupos); sin insignia OBA; la cuenta de la app debe tener cierta
  antigüedad/actividad (https://docs.360dialog.com/docs/resources/phone-numbers/coexistence).
- **SIN VERIFICAR:** si coexistence exige pasar por un *Tech Provider*/BSP (Embedded Signup) o si un
  desarrollador directo (nuestra app de Meta gratuita) puede activarlo sin coste.
- **Valor para la venta:** la agencia conserva su número y su app de siempre; el bot contesta por API y el
  agente ve y continúa la conversación en su móvil. Es un argumento fuerte.

## 3. Leads de Idealista y Fotocasa
**Idealista** (ayuda de idealista/tools, fragmentos del buscador):
- Los contactos llegan por **email, teléfono o chat**; de chat y llamada se envía **copia al email** del contacto
  del anuncio. — https://www.idealista.com/tools/centrodeayuda/articulos/chat/ y https://www.idealista.com/tools/centrodeayuda/articulos/inbox/
- Si el usuario del chat no está registrado, recibe la respuesta en su email. — misma URL de chat.
- Al contactar, el interesado debe dar **email o teléfono** (uno de los dos): el teléfono **no es obligatorio**.
  Fuente secundaria (https://www.tuexpertoapps.com/2018/10/30/como-chatear-con-los-anunciantes-de-pisos-en-idealista-de-forma-segura/) → **SIN VERIFICAR** en el formulario actual.
- Anuncios en alquiler pueden configurarse para recibir contactos **solo por chat** sin mostrar teléfono. — https://www.idealista.com/tools/centrodeayuda/etiquetas/telefono-anuncio/ (fragmento del buscador)
- **Integración:** idealista/tools es su CRM; importa leads de otros portales (Fotocasa, Habitaclia, pisos.com…)
  **reenviando los emails** a una dirección `xxx@toolsleads.com`. — https://www.idealista.com/tools/centrodeayuda/articulos/importacion-de-leads-de-portales-inmobiliarios/
  → Confirma que **el email es el formato universal del lead**: nuestro n8n puede hacer lo mismo (filtro de
  reenvío o lectura IMAP del buzón de la agencia), gratis.
- API oficial pública: `developers.idealista.com` es una **API de búsqueda de anuncios** con acceso por solicitud,
  no una API de leads. **SIN VERIFICAR** que exista una API de leads para partners (lo afirman webs de terceros).
- Uso de datos: la ayuda de idealista/tools recuerda que el RGPD exige consentimiento expreso para
  comunicaciones y ofrece pedirlo por email. — https://www.idealista.com/tools/centrodeayuda/articulos/envio-de-comunicaciones-a-clientes-conforme-al-rgpd/
  **SIN VERIFICAR** el texto actual de los T&C de Idealista sobre el uso de los datos del interesado por el
  profesional (la versión encontrada es un PDF antiguo: https://st1.idealista.com/ayuda/wp-content/uploads/2020/04/2020-En-curso-Terminos-y-condiciones.pdf).

**Fotocasa**:
- Fotocasa Pro dice que los contactos de portales pueden llegar al CRM (https://pro.fotocasa.es/crm-inmobiliario/)
  y hay CRMs integrados (Inmoweb, Witei). Su propio blog aconseja **pedir el teléfono al cliente** al responder
  el email (https://blogprofesional.fotocasa.es/como-responder-peticion-informacion-cliente-comprador/), lo que
  sugiere que **no siempre viene**. **SIN VERIFICAR** si el teléfono es obligatorio en su formulario y qué
  dicen sus condiciones sobre contactar al lead.

## 4. Ley de IA UE, art. 50 (chatbots)
- Art. 50.1: los proveedores deben diseñar los sistemas que interactúan con personas para que se les informe
  de que hablan con una IA, salvo que resulte obvio. Se aplica desde el **2 de agosto de 2026** (art. 113,
  fecha general). — https://eur-lex.europa.eu/legal-content/ES/ALL/?uri=CELEX%3A32024R1689 y texto consolidado
  https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng (no se pudo abrir; confirmado por fragmentos del buscador).
- **Digital Omnibus on AI** = Reglamento (UE) **2026/1744** de 8-jul-2026, publicado en el DOUE el 24-jul-2026,
  en vigor el 27-jul-2026. — https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng ;
  https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force ;
  https://www.consilium.europa.eu/en/press/press-releases/2026/06/29/artificial-intelligence-council-gives-final-green-light-to-simplify-and-streamline-rules/
- Qué aplazó: alto riesgo a 2-dic-2027 (Anexo III) y 2-ago-2028 (Anexo I). Para transparencia solo dio un
  periodo de gracia al **marcado de contenido generado (art. 50.2)** hasta el **2-dic-2026** para sistemas ya
  en el mercado. **El art. 50.1 (avisar de que es un bot) NO se aplazó: ya es exigible.**
  (Consilium, fragmento del buscador; coincide con https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/).
- **Consecuencia práctica:** el primer mensaje debe decir algo como "Soy el asistente automático de
  [Agencia]; un agente te llamará después". Cuesta 0 € y nos cubre.

## 5. Alternativas gratuitas si WhatsApp no sirve para el primer contacto
| Opción | Coste | Pros | Contras |
|---|---|---|---|
| **Email automático <2 min** (n8n lee el buzón IMAP de la agencia y responde desde su SMTP/Gmail) | 0 € | Funciona con el 100 % de leads (todos llegan por email); sin plantillas ni opt-in de Meta; es respuesta a su petición | Menos tasa de lectura que WhatsApp; puede caer en spam si se usa un dominio nuevo |
| **Enlace `wa.me/34XXXXXXXXX?text=...` dentro del email** | 0 € | El lead abre WhatsApp él mismo → opt-in limpio, ventana de 24 h, sin plantilla. Con coexistence cae en el número de siempre | Depende de que el lead haga clic |
| **Plantilla utility por Cloud API** cuando hay teléfono | ~0,02 €/lead (cliente) **SIN VERIFICAR** | Llega al móvil en segundos | Opt-in dudoso; riesgo de recategorización y de baja calidad |
| **Responder en el chat del portal** | 0 € | Es donde escribió el lead | Sin API pública conocida → no automatizable sin scraping (prohibido/frágil) |
| **SMS** | De pago (Twilio da solo crédito de prueba; proveedores españoles por saldo) | Alta lectura | **No es gratis** → descartado por "cero gasto" |
| **Llamada automática** | De pago | — | Coste + desde 2023 la Ley General de Telecomunicaciones restringe llamadas comerciales no consentidas (**SIN VERIFICAR** su aplicación a una respuesta solicitada) → descartado |
| **Aviso al agente** (push/Telegram/WhatsApp interno) para que llame él | 0 € | El humano llama en minutos en horario laboral | No cumple "24/7" |

## Recomendación
1. **Reformular la promesa** (propuesta):
   > "Cada lead de Idealista, Fotocasa o tu web recibe una respuesta en menos de 2 minutos, 24/7: por
   > WhatsApp cuando el cliente ha dejado su móvil y ha aceptado que le escribáis, y por email (con botón
   > para seguir por WhatsApp) en el resto de casos. Un asistente automático identificado como tal
   > cualifica al comprador y le propone hueco en tu agenda."
2. **Arquitectura por defecto (0 € para nosotros):** n8n lee el buzón → responde por email en <2 min con
   enlace `wa.me` → cuando el lead escribe por WhatsApp, el bot (Cloud API + coexistence) cualifica y agenda.
   Plantilla utility al teléfono solo si el cliente acepta el riesgo de opt-in y lo decide su asesor legal.
3. **Medir en la prueba de velocidad** qué % de leads trae teléfono y cuántos hacen clic en `wa.me`.
4. Añadir al contrato/propuesta: los costes de Meta (plantillas y, desde el 1-oct-2026, mensajes de servicio)
   los paga la agencia y exigen tarjeta en su cuenta de WhatsApp Business.
5. Actualizar `PLAN.md` y `ventas/propuesta.md` con la nueva formulación.

## SIN VERIFICAR (resumen)
- Tarifas exactas de España y precio/cupo de mensajes de servicio desde el 1-oct-2026.
- Que una plantilla de seguimiento de lead se acepte como *utility*.
- Si dejar el teléfono en Idealista/Fotocasa vale como opt-in para WhatsApp (probablemente no por sí solo).
- Disponibilidad de coexistence en España hoy y si requiere BSP/Tech Provider.
- Texto primario de los Business Solution Terms sobre chatbots de IA.
- Si el teléfono es obligatorio en los formularios de Idealista y Fotocasa, formato exacto del email de lead
  (¿incluye teléfono?, ¿reply-to del interesado?) y condiciones de uso de datos por el profesional.
- Existencia de una API de leads de Idealista para partners.
