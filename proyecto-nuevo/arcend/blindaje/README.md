# Blindaje · revisión de la publicidad sanitaria de una web

Herramienta para preparar, **antes de llamar a una clínica**, el informe de cumplimiento de la
publicidad de su web (ver `../DECISION.md`). Se ejecuta en tu PC, con Python y sin instalar nada más.

```
python blindaje.py https://www.clinica.es --nombre "Clínica X" [--max-paginas 25]
```

Genera `informes/<nombre-de-la-clinica>/informe.html` (para enseñar e imprimir en A4) e `informe.json`.

## Qué hace y qué NO hace

- **Solo comprobación pasiva de información pública**: descarga la página de inicio y los enlaces
  internos del mismo dominio, como un visitante normal.
- Respeta `robots.txt` (si prohíbe algo, no se descarga), hace **como máximo 1 petición por segundo**
  (o más lento si la web lo pide con `Crawl-delay`) y se identifica con un User-Agent propio
  (`BlindajeRevisionPublicidad/1.0`).
- **No** escanea puertos, **no** prueba contraseñas, **no** busca vulnerabilidades, **no** entra en
  ninguna zona privada (art. 197 bis del Código Penal). No envía nada a nadie.
- No ejecuta JavaScript: lo que la web carga dinámicamente (algunos banners de cookies, widgets de
  reseñas) puede no verse. Revísalo a mano si hace falta.

## Instalación en Windows (paso a paso, una sola vez)

1. Entra en <https://www.python.org/downloads/> y pulsa **Download Python 3.x** (sirve 3.10 o superior).
2. Abre el instalador y, **antes de pulsar "Install Now"**, marca la casilla
   **"Add python.exe to PATH"**. Termina la instalación.
3. Copia la carpeta `blindaje` a tu PC (por ejemplo a `C:\Users\TU_USUARIO\Documents\blindaje`).
4. Abre **PowerShell**: tecla Windows, escribe `PowerShell` y pulsa Intro.
5. Comprueba Python:
   ```powershell
   python --version
   ```
   Debe salir `Python 3.10` o superior. Si sale un error o se abre la Microsoft Store, repite el paso 2
   (casilla "Add python.exe to PATH") o prueba con `py --version` y usa `py` en lugar de `python` en
   los comandos siguientes.

No hace falta instalar ningún paquete: solo usa la biblioteca estándar de Python.

## Uso

En PowerShell, entra en la carpeta:

```powershell
cd "$HOME\Documents\blindaje"
```

Revisar una web (máximo 25 páginas por defecto):

```powershell
python blindaje.py https://www.clinica.es --nombre "Clínica X"
```

Con tus datos de contacto en el informe (si no, quedan como `{nombre_contacto}`, `{telefono_contacto}`,
`{email_contacto}` para rellenar a mano):

```powershell
python blindaje.py https://www.clinica.es --nombre "Clínica X" --max-paginas 40 `
  --contacto-nombre "Tu Nombre" --contacto-telefono "600 000 000" --contacto-email "tu@correo.es"
```

Abrir el informe:

```powershell
start .\informes\clinica-x\informe.html
```

Para PDF: en el navegador, **Ctrl+P → Guardar como PDF** (ya está maquetado para A4).

### Si la web bloquea la descarga: `--html-local`

1. Abre la web en el navegador y guarda cada página importante con **Ctrl+S** ("Página web, solo HTML")
   en una carpeta, por ejemplo `C:\Users\TU_USUARIO\Documents\clinica-x-html\`
   (inicio, tratamientos, precios/promociones, antes y después, equipo, aviso legal, privacidad, cookies).
2. Ejecuta:
   ```powershell
   python blindaje.py https://www.clinica.es --html-local "$HOME\Documents\clinica-x-html" --nombre "Clínica X"
   ```
   La URL es opcional en este modo (solo sirve para que aparezca en el informe).

## Qué revisa (reglas en `reglas.py`)

| Gravedad | Regla |
|---|---|
| ALTA | Menciones de toxina botulínica o marcas (Botox/bótox, Vistabel, Azzalure, Bocouture, Dysport, Xeomin, Letybo, Alluzience, "neuromodulador", BTX, hashtags): publicidad de medicamento con receta (RD 1416/1994 + RDL 1/2015). |
| ALTA | Promesas: "resultados garantizados", "garantizamos…" (con contexto de tratamiento/resultado), "sin riesgo(s)", "sin efectos secundarios", "100 % seguro", "sin dolor"/"indoloro" absolutos, "milagro". (RD 1907/1996). |
| ALTA / MEDIA | No aparece el nº de registro sanitario del centro (ALTA) o se menciona sin número (MEDIA) (Decreto 51/2006 de Madrid). |
| MEDIA | Promociones (oferta, descuento, % dto, 2x1, gratis, bono, Black Friday…) cerca de un tratamiento médico. |
| MEDIA | Imágenes de antes y después (texto, texto alternativo, nombre del archivo, enlaces a galería): consentimiento RGPD/AEPD. |
| MEDIA | Testimonios, opiniones o reseñas de pacientes. |
| BAJA | Falta aviso legal, política de privacidad o política de cookies. |
| BAJA | No se identifica al médico responsable ni su nº de colegiado (requisito legal **SIN VERIFICAR**). |

Cada hallazgo lleva URL, fragmento de evidencia, norma, qué hacer y **texto corregido listo para publicar**.
Los falsos positivos conocidos ("garantizamos su privacidad", "pago 100 % seguro", "casi sin dolor",
"Dra. Milagros", "eliminar toxinas", "antes y después del tratamiento evite el sol", "parking gratuito",
páginas legales) están documentados al principio de `reglas.py` y cubiertos por tests.

**Puntuación**: se parte de 100; cada hallazgo resta según su gravedad (ALTA 25, MEDIA 10, BAJA 4; las
repeticiones de una misma regla restan un 25 % más cada una, con tope del doble). Nota: A ≥ 90, B ≥ 75,
C ≥ 55, D ≥ 35, E < 35. Con algún ALTA la nota es C como máximo.

## Tests (sin red)

```powershell
python -m unittest discover -s tests -v
```

Los fixtures son HTML sintéticos en `tests/fixtures/` (uno por regla, falsos positivos, un sitio con
todos los fallos y un sitio limpio). El rastreador se prueba con un servidor simulado.

## Avisos

- El informe **no es asesoramiento jurídico** (la frase va en cada informe). Normas y apartados marcados
  SIN VERIFICAR en `reglas.py` e `../investigacion/mercado.md` deben confirmarse en el BOE/BOCM.
- Los informes de clínicas reales se guardan en `informes/`, que está en `.gitignore`: no se suben al repo.
- Tú decides a quién llamar y qué enseñar; la herramienta no contacta con nadie.
