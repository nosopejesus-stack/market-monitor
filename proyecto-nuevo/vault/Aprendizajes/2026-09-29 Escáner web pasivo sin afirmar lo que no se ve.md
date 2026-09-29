---
fecha: 2026-09-29
etiquetas: [arcend, blindaje, escaner, rgpd, lssi, falsos-positivos]
origen: blindaje/escaner.py (integración del risk-scanner en el informe)
---
# Escáner web pasivo sin afirmar lo que no se ve

- **Qué pasó:** se añadió a Blindaje un escáner de cumplimiento de la web (certificado https, cookies, formularios, enlaces legales rotos y nº de registro distinto del Registro de la CAM) para subir el ticket. En la primera pasada real, "cookies sin gestor de consentimiento" salía en webs que sí tenían banner (Oquendo: `cookies-consent`; otras lo cargan desde Google Tag Manager y no aparece en el HTML), y un formulario de Tilda se daba por "sin privacidad" aunque se monta con JavaScript.
- **Lección:** lo que se carga con JavaScript no se ve sin navegador: no se puede afirmar que falta. Cookies → BAJA "comprobar a mano" (no cuenta); formularios montados con `<script>` → no se evalúan; formularios estáticos → MEDIA con aviso de comprobar en el navegador. Lo que sí se afirma es lo objetivo: certificado caducado (conexión TLS normal), enlace legal con error 404 y nº de registro publicado distinto del que da el Registro (solo si el dato oficial del CSV es seguro, sin "probable").
- **Cómo aplicarla:**
  - Los hallazgos del escáner llevan regla `web_...` y NO cuentan en la frase de la llamada (que habla de publicidad sanitaria); van en la columna `incumplimientos_web` y en el informe.
  - Antes de mencionar uno a un médico, comprobarlo en el navegador (hecho con López-Linares: formulario de nombre y teléfono sin casilla ni texto de privacidad, confirmado en vivo).
  - Límite legal: solo lo que ve cualquier visitante; nada de puertos ni rutas ocultas ([[Aprendizajes/2026-09-29 Integrar el risk-scanner antiguo en Blindaje]]).

Relacionado: [[Aprendizajes/2026-09-28 Reglas de ausencia solo con lectura suficiente]], [[Aprendizajes/2026-09-29 Filtros de contexto en todas las reglas que cuentan en N]].
