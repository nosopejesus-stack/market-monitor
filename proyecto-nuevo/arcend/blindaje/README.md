# Blindaje · revisión de la publicidad sanitaria de una web

Herramienta para preparar, **antes de llamar a una clínica**, el informe de cumplimiento de la
publicidad de su web (ver `../DECISION.md`). Se ejecuta en tu PC, con Python y sin instalar nada más.

```
python blindaje.py https://www.clinica.es --nombre "Clínica X" --previo
```

Dos informes (se imprimen en A4):

- **`--previo`** → `informes/<nombre-de-la-clinica>/informe_previo.html`: **una página para enseñar antes de
  vender**. Dice cuántos puntos hay con norma concreta (`n_puntos_norma` en `informe.json`), cada punto con su
  norma y gravedad, y la oferta. **No incluye los textos corregidos.**
- **Sin `--previo`** → `informe.html`: el **informe completo, entregable de pago** (evidencias, qué hacer y
  textos corregidos listos para publicar). Se genera cuando la clínica ha pagado.

En los dos casos se guarda también `informe.json` (datos internos; los nombres de pacientes tras un guion en
los testimonios salen como `[nombre]`).

## Qué hace y qué NO hace

- **Solo comprobación pasiva de información pública**: descarga la página de inicio y los enlaces
  internos del mismo dominio, como un visitante normal.
- Respeta `robots.txt` (si prohíbe algo, no se descarga), hace **como máximo 1 petición por segundo**
  (o más lento si la web lo pide con `Crawl-delay`) y se identifica con un User-Agent propio
  (`BlindajeRevisionPublicidad/1.0`). Si pasas `--contacto-email`, el User-Agent añade
  `(+contacto: tu@correo.es)` para que la web sepa a quién escribir.
- Descarga cada página una sola vez aunque se enlace de varias formas (`/botox` y `/botox/`, o con
  `utm_*`, `fbclid`, `gclid`).
- **No** escanea puertos, **no** prueba contraseñas, **no** busca vulnerabilidades, **no** entra en
  ninguna zona privada (art. 197 bis del Código Penal). No envía nada a nadie.
- No ejecuta JavaScript: lo que la web carga dinámicamente (algunos banners de cookies, widgets de
  reseñas) puede no verse. Revísalo a mano si hace falta.
- **Web no legible**: si entre todas las páginas hay menos de ~300 caracteres de texto (webs hechas con
  JavaScript, tipo `<div id="root">`) o solo se ha leído 1 página, el informe sale con un aviso en rojo
  ("revisión no fiable") y **no** incluye los puntos que dicen que falta algo (registro sanitario, páginas
  legales, médico). En ese caso usa `--html-local` (abajo).

## Instalación en Windows (paso a paso, una sola vez)

**1. Descargar la herramienta**

1. Abre https://github.com/nosopejesus-stack/market-monitor/tree/claude/tender-cannon-ui4ixl (esta rama; cuando se pase a `main`, usa `main`) y pulsa el botón verde **Code** → **Download ZIP**.
2. Ve a la carpeta **Descargas**, pulsa con el botón derecho sobre el ZIP → **Extraer todo…** → **Extraer**.
   No trabajes dentro del ZIP sin extraer: no funciona.
3. Dentro de lo extraído, la herramienta está en
   `market-monitor-main\proyecto-nuevo\arcend\blindaje` (si descargaste otra rama, la primera carpeta se
   llama `market-monitor-<rama>`). Copia la carpeta **`arcend`** entera (contiene `blindaje` y `prospectos`) a `Documentos` y trabaja en `Documentos\arcend\blindaje`.

> **Aviso OneDrive:** si tu carpeta Documentos está sincronizada con OneDrive, las rutas pueden ser
> `C:\Users\TU_USUARIO\OneDrive\Documentos\...` y a veces los archivos quedan "solo en la nube". Si algo
> falla, copia la carpeta a una ruta sin OneDrive, por ejemplo `C:\blindaje`.

**2. Instalar Python (gratis)**

- Opción A: entra en <https://www.python.org/downloads/> y pulsa **Download Python 3.x** (sirve 3.10 o
  superior). Abre el instalador y, **antes de pulsar "Install Now"**, marca la casilla
  **"Add python.exe to PATH"**.
- Opción B (Windows 10/11): abre PowerShell y escribe
  ```powershell
  winget install Python.Python.3.12
  ```
  Cierra y vuelve a abrir PowerShell al terminar.

**3. Abrir PowerShell dentro de la carpeta**

Abre la carpeta `blindaje` en el Explorador de archivos, haz clic en la **barra de direcciones** (arriba,
donde pone la ruta), escribe `powershell` y pulsa Intro. Se abre PowerShell ya situado en esa carpeta.

**4. Comprobar Python**

```powershell
py --version
```

Debe salir `Python 3.10` o superior. Si `py` no existe, prueba `python --version` y usa `python` en lugar
de `py` en los comandos siguientes. Si se abre la Microsoft Store, vuelve al paso 2.

No hace falta instalar ningún paquete: solo usa la biblioteca estándar de Python.

## Uso

Con PowerShell abierto en la carpeta `blindaje` (paso 3), informe previo de una web (máximo 25 páginas
por defecto):

```powershell
py blindaje.py https://www.clinica.es --nombre "Clínica X" --previo
```

Informe completo (entregable de pago), mismo comando sin `--previo`:

```powershell
py blindaje.py https://www.clinica.es --nombre "Clínica X"
```

Con tus datos de contacto en el informe (si no, quedan como `{nombre_contacto}`, `{telefono_contacto}`,
`{email_contacto}` para rellenar a mano):

```powershell
py blindaje.py https://www.clinica.es --nombre "Clínica X" --max-paginas 40 `
  --contacto-nombre "Tu Nombre" --contacto-telefono "600 000 000" --contacto-email "tu@correo.es"
```

Abrir el informe:

```powershell
start .\informes\clinica-x\informe_previo.html
start .\informes\clinica-x\informe.html
```

Para PDF: en el navegador, **Ctrl+P → Guardar como PDF** (ya está maquetado para A4).

### Todas las clínicas de una vez: `lote.py`

Hace el informe previo (`--previo`) de todas las clínicas de `..\prospectos\clinicas.csv` y una tabla con el
orden en que conviene llamarlas. Necesita la carpeta `prospectos` al lado de `blindaje` (si en la instalación
copiaste solo `blindaje` a Documentos, copia también `market-monitor-...\proyecto-nuevo\arcend\prospectos` a
Documentos, junto a `blindaje`).

Con PowerShell abierto en la carpeta `blindaje`, **un solo comando**:

```powershell
python lote.py ..\prospectos\clinicas.csv --contacto-nombre "Tu Nombre" --contacto-telefono "600 000 000"
```

Y al terminar:

```powershell
start .\informes\RESUMEN.html
```

- Salta las filas **sin web**, con **`cadena` = si** o con **`no_llamar`** en `notas`.
- Revisa como máximo 15 páginas por clínica (`--max-paginas 25` para más). Con 1 petición por segundo, unas
  50 clínicas tardaron unos 35 minutos en la primera pasada real (29-09-2026). Solo algunas:
  `--solo ARC-001,ARC-002`. Opcional: `--contacto-email "tu@correo.es"` (también va en el User-Agent).
- Si una clínica falla (certificado SSL, tiempo de espera, web que no responde) se anota en su fila y el lote
  **sigue** con la siguiente. El resumen se reescribe tras cada clínica: si cierras la ventana a mitad, lo hecho
  queda en `RESUMEN.html`.
- Cada clínica deja su `informes\<nombre-de-la-clinica>\informe_previo.html` + `informe.json`, igual que
  `blindaje.py --previo`. En `RESUMEN.html` el nombre de la clínica enlaza a su informe.
- `informes\RESUMEN.csv` (separado por `;`, se abre con doble clic en Excel) y `informes\RESUMEN.html`, con:
  id, nombre, teléfono, web, lectura fiable, puntos con norma, puntos a revisar, nota, hallazgo principal
  (el alto o medio más grave), **frase para la llamada** y estado.
- **Orden**: primero las que tienen más puntos con norma concreta, después más puntos a revisar, después peor
  nota. Al final las no legibles (estado `revisar a mano: usar --html-local`) y las que dieron error.
- **Frase para la llamada** (la calcula la herramienta, no se escribe a mano):
  - con puntos con norma concreta: *"He revisado la publicidad de su web y hay N puntos que la normativa de
    publicidad sanitaria no permite."*
  - si solo hay puntos a revisar: *"He revisado la publicidad de su web y hay M puntos que conviene revisar
    según la normativa de publicidad sanitaria."*
  - si no hay ninguno: vacía, estado `ok: sin gancho` (no llamar con esa frase).
  - si la web no se ha leído bien: vacía, estado `revisar a mano: usar --html-local`. Guarda sus páginas y
    pasa esa clínica sola con `python blindaje.py ... --html-local ... --previo` (sección siguiente).
- Antes de llamar, abre el informe previo de la clínica y comprueba en su web el hallazgo principal.
- **Copia de cada web y `--reanalizar`:** cada web descargada se guarda en `informes\<clínica>\paginas.json`.
  Para volver a generar todos los informes sin descargar nada (tras corregir una regla, o para poner tu nombre y
  teléfono en los informes): `python lote.py ..\prospectos\clinicas.csv --reanalizar --contacto-nombre "…"
  --contacto-telefono "…"`. Tarda segundos.
- **Columna `posible_cadena`** (uso interno, no sale en el informe de la clínica): señales de varias sedes
  («nuestras clínicas», «franquicia», varios nº de registro, otras ciudades). Si sale algo, mira antes de llamar.
- **Qué no cuenta en N** (revisión manual del lote real): reseñas de pacientes (widgets de Google/Trustindex o
  frases en primera persona), consulta/cita/diagnóstico gratuitos, teléfonos gratuitos, «Promociones» del menú
  sin precio ni descuento (sale como BAJA «revisar a mano»), bonos con precio pero sin descuento, promociones de
  tratamientos no médicos (masajes, higiene facial, aparatología estética), currículum del médico («formación en
  toxina»), y la falta del nº de registro si no se ha leído el aviso legal.

### Si la web bloquea la descarga, da error de certificado (SSL) o sale "revisión no fiable": `--html-local`

1. Abre la web en el navegador y guarda cada página importante con **Ctrl+S** ("Página web, solo HTML")
   en una carpeta, por ejemplo `C:\Users\TU_USUARIO\Documents\clinica-x-html\`
   (inicio, tratamientos, precios/promociones, antes y después, equipo, aviso legal, privacidad, cookies).
2. Ejecuta:
   ```powershell
   py blindaje.py https://www.clinica.es --html-local "$HOME\Documents\clinica-x-html" --nombre "Clínica X" --previo
   ```
   La URL es opcional en este modo (solo sirve para que aparezca en el informe). Sin URL, el informe dice
   "Hemos revisado N páginas guardadas de la web de Clínica X".

## Escáner de cumplimiento de la web (`escaner.py`)

Además de la publicidad sanitaria, el informe incluye incumplimientos de la web. Solo mira lo que ve cualquier
visitante (el HTML descargado y el certificado que entrega la web al abrirla); nada de puertos ni pruebas:

| Regla | Qué detecta | Gravedad |
|---|---|---|
| `web_certificado` / `web_https` | certificado caducado o no válido, o web sin https | MEDIA (caduca en ≤ 21 días: BAJA) |
| `web_formulario` | formulario que pide correo o teléfono sin texto ni casilla de privacidad (RGPD art. 13) | MEDIA, comprobar en el navegador |
| `web_registro_distinto` | el nº de registro que publica la web no es el del Registro de la CAM para esa dirección (columna `registro_sanitario` del CSV) | MEDIA |
| `web_legal_roto` | enlace a aviso legal / privacidad / cookies que da error | BAJA |
| `web_cookies` | analítica o píxel sin gestor de consentimiento reconocible | BAJA, comprobar a mano (el banner puede cargarse con JavaScript) |

No cuentan en la frase de la llamada (que habla de publicidad sanitaria); salen en la columna
`incumplimientos_web` del resumen. Con `blindaje.py`, el nº oficial se pasa con `--registro CS12345`.

## Qué revisa (reglas en `reglas.py`)

| Gravedad | Regla |
|---|---|
| ALTA | Menciones de toxina botulínica o marcas (Botox/bótox, Vistabel, Azzalure, Bocouture, Dysport, Xeomin, Letybo, Alluzience, "neuromodulador", BTX, hashtags): publicidad de medicamento con receta (RD 1416/1994 + RDL 1/2015). Si la frase la niega o explica la prohibición, pasa a BAJA "revisar a mano". "Botox capilar" y "efecto botox" no cuentan. |
| ALTA | Promesas: "resultados garantizados", "garantizamos…" (con contexto de tratamiento/resultado), "sin riesgo(s)", "sin efectos secundarios", "100 % seguro" (RD 1907/1996, apartado SIN VERIFICAR). Las frases negadas ("no garantizamos…") no cuentan. |
| MEDIA | "Sin dolor"/"indoloro" absolutos (afirmación absoluta sobre dolor o riesgo) y "milagro" (posible promesa de resultado). |
| ALTA / MEDIA | No aparece el nº de registro sanitario del centro (ALTA) o se menciona sin número (MEDIA) (Decreto 51/2006 de Madrid, artículo SIN VERIFICAR). Un teléfono, una calle o un código postal cerca no cuentan como número. |
| MEDIA | Promociones (oferta, descuento, % dto, 2x1, gratis, bono, Black Friday…) cerca de un tratamiento médico. |
| MEDIA | Imágenes de antes y después (texto, texto alternativo, nombre del archivo, enlaces a galería): consentimiento RGPD/AEPD. |
| MEDIA | Testimonios, opiniones o reseñas de pacientes. |
| BAJA | Falta aviso legal, política de privacidad o política de cookies (en cookies, la autoridad es la AEPD). Las plantillas son un borrador mínimo para completar y validar con el asesor. |
| BAJA | No se identifica al médico responsable ni su nº de colegiado (requisito legal **SIN VERIFICAR**). |

Cada hallazgo lleva URL, fragmento de evidencia, norma, qué hacer y **texto corregido listo para publicar**
(en el informe completo). Lo que va entre corchetes `[Solo si…]` hay que comprobarlo con la clínica y quitarlo
antes de publicar.

**Puntos con norma concreta** (`n_puntos_norma`): hallazgos ALTA o MEDIA sin nada SIN VERIFICAR, contando una
sola vez cada tipo de punto (p. ej. la publicidad de la toxina cuenta 1 aunque salga en 15 páginas o en el menú). Es la cifra que se usa en la oferta.

**Puntos a revisar** (`n_puntos_revisar`): lo mismo pero **incluyendo** los ALTA/MEDIA que dependen de algo
SIN VERIFICAR (siempre ≥ puntos con norma). Sale en el informe previo ("Puntos a revisar") y en `informe.json`
junto con `frase_llamada`. Solo se usa para decir "conviene revisar", nunca "no permite".
Los falsos positivos conocidos ("garantizamos su privacidad", "pago 100 % seguro", "casi sin dolor",
"Dra. Milagros"/"DRA. MILAGROS PÉREZ", negaciones como "no garantizamos resultados", "eliminar toxinas",
"botox capilar", "antes y después del tratamiento evite el sol", "cuidados antes y después del tratamiento",
"parking gratuito", "nuestra oferta de tratamientos", textos que explican que la ley prohíbe los testimonios,
páginas legales) están documentados al principio de `reglas.py` y cubiertos por tests.

**Puntuación**: se parte de 100; cada hallazgo resta según su gravedad (ALTA 25, MEDIA 10, BAJA 4; las
repeticiones de una misma regla restan un 25 % más cada una, con tope del doble). Nota: A ≥ 90, B ≥ 75,
C ≥ 55, D ≥ 35, E < 35. Con algún ALTA la nota es C como máximo.

## Tests (sin red)

```powershell
py -m unittest discover -s tests -v
```

El modo lote se prueba en `tests/test_lote.py` (sin red: webs que no responden y HTML local por id).
Los fixtures son HTML sintéticos en `tests/fixtures/` (uno por regla, falsos positivos, un sitio con
todos los fallos y un sitio limpio). El rastreador se prueba con un servidor simulado.

## Avisos

- El informe **no es asesoramiento jurídico** (la frase va en cada informe). Normas y apartados marcados
  SIN VERIFICAR en `reglas.py` e `../investigacion/mercado.md` deben confirmarse en el BOE/BOCM.
- Los informes de clínicas reales se guardan en `informes/`, que está en `.gitignore`: no se suben al repo.
- Tú decides a quién llamar y qué enseñar; la herramienta no contacta con nadie.
