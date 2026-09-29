"""Escáner pasivo de cumplimiento de la web: certificado, cookies, formularios, enlaces legales y nº de registro.

Solo mira lo que cualquier visitante ve: el HTML ya descargado (con robots.txt y 1 petición/segundo) y el
certificado que la web entrega al abrirla en un navegador (una conexión TLS normal al puerto 443).
No escanea puertos, no prueba rutas ocultas ni vulnerabilidades (límite: art. 197 bis del Código Penal).

Sus hallazgos llevan regla "web_..." y NO cuentan en la cifra de la llamada (n_puntos_norma), que habla
solo de publicidad sanitaria: van en el informe como incumplimientos de la web (RGPD, LSSI).
"""

from __future__ import annotations

import re
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

import reglas
from reglas import BAJA, MEDIA, Hallazgo, plegar

# Gestores de consentimiento de cookies conocidos (y el modo de consentimiento de Google).
GESTOR_COOKIES = (
    r"cookiebot|cookieyes|cky-consent|complianz|cmplz|cookie-law-info|cookielawinfo|borlabs|iubenda|onetrust|"
    r"didomi|usercentrics|quantcast|axeptio|tarteaucitron|cookie-notice|cookie-consent|cookieconsent|gdpr-cookie|"
    r"moove_gdpr|real-cookie-banner|termly|consentmanager|klaro|osano|cookiefirst|cookiehub|cookie-script|"
    r"gtag\(\s*['\"]consent['\"]|cookie_notice|cookies-eu-banner|pum-cookie|eu-cookie-law|wpl-cookie|"
    r"cookies?[-_ ]?(consent|banner|notice|bar|popup|aviso|law)|aceptar\s+(todas\s+)?(las\s+)?cookies|"
    r"rechazar\s+(todas\s+)?(las\s+)?cookies|configurar\s+cookies|cookiename"
)
RASTREADORES = [
    ("Google Analytics / Google Tag Manager", r"googletagmanager\.com|google-analytics\.com|\bgtag\(\s*['\"]config"),
    ("el píxel de Meta (Facebook)", r"connect\.facebook\.net|\bfbq\(\s*['\"]init"),
    ("el píxel de TikTok", r"analytics\.tiktok\.com"),
    ("Hotjar", r"static\.hotjar\.com"),
    ("Microsoft Clarity", r"clarity\.ms"),
]
RE_FORM = re.compile(r"<form\b[^>]*>(.*?)</form>", re.I | re.S)
RE_INPUT = re.compile(r"<(input|textarea|select)\b([^>]*)>", re.I)
AVISO_PRIVACIDAD = r"privacidad|proteccion\s+de\s+datos|\brgpd\b|\bgdpr\b|datos\s+personales|acepto|consentimiento|responsable"
RUTA_LEGAL = r"aviso.?legal|privacidad|privacy|cookies|legal"
AVISO_ERROR = re.compile(r"^(\S+) respondió (\d{3})\.$")

CAMPOS_DATOS = {"email": "correo", "tel": "teléfono"}


def _h(regla, gravedad, titulo, url, evidencia, norma, base, accion, texto="", sv=""):
    return Hallazgo(regla=regla, gravedad=gravedad, titulo=titulo, url=url, ubicacion="web (cumplimiento)",
                    evidencia=evidencia, marca_inicio=0, marca_fin=0, accion=accion, texto_corregido=texto,
                    base_normativa=base, sin_verificar=sv, norma=norma)


# --------------------------------------------------------------------------
# Certificado (conexión TLS normal, como un navegador)
# --------------------------------------------------------------------------

def comprobar_certificado(host: str, puerto: int = 443, timeout: float = 8.0, ahora=None) -> dict:
    """Devuelve {"estado": "ok"|"caduca_pronto"|"caducado"|"no_valido"|"sin_conexion", "dias": int|None, "detalle": str}."""
    ahora = ahora or datetime.now(timezone.utc)
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, puerto), timeout=timeout) as s:
            with ctx.wrap_socket(s, server_hostname=host) as t:
                cert = t.getpeercert()
    except ssl.SSLCertVerificationError as err:
        motivo = (getattr(err, "verify_message", "") or str(err)).lower()
        if "expired" in motivo:
            return {"estado": "caducado", "dias": None, "detalle": "el certificado ha caducado"}
        return {"estado": "no_valido", "dias": None, "detalle": motivo}
    except (OSError, ssl.SSLError) as err:
        return {"estado": "sin_conexion", "dias": None, "detalle": str(err)}
    fin = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), timezone.utc)
    dias = (fin - ahora).days
    return {"estado": "caduca_pronto" if dias <= 21 else "ok", "dias": dias, "detalle": fin.strftime("%d/%m/%Y")}


def regla_certificado(web: str, certificado: dict | None):
    if not web:
        return []
    url = web if "://" in web else "https://" + web
    if urlparse(url).scheme == "http" and (certificado or {}).get("estado") != "ok":
        return [_h("web_https", MEDIA, "La web no usa conexión segura (https)", url,
                   f"La web se sirve como {url} y no ofrece un certificado válido.",
                   "RGPD, art. 32 (seguridad del tratamiento)",
                   "Si la web recoge datos (formularios, citas), deben viajar cifrados; el navegador la marca como «No segura».",
                   "Instalar un certificado (gratuito, p. ej. Let's Encrypt) y redirigir todo a https.")]
    if not certificado:
        return []
    est = certificado.get("estado")
    if est == "caducado":
        return [_h("web_certificado", MEDIA, "Certificado de seguridad (https) caducado", url,
                   "Al abrir la web, el navegador avisa de que la conexión no es segura: el certificado ha caducado.",
                   "RGPD, art. 32 (seguridad del tratamiento)",
                   "Los pacientes ven un aviso de «sitio no seguro» y los datos de los formularios no van protegidos.",
                   "Renovar el certificado y activar la renovación automática.")]
    if est == "no_valido":
        return [_h("web_certificado", MEDIA, "Certificado de seguridad (https) no válido", url,
                   f"El navegador rechaza el certificado de la web ({certificado.get('detalle', '')}).",
                   "RGPD, art. 32 (seguridad del tratamiento)",
                   "Los pacientes ven un aviso de «sitio no seguro».",
                   "Instalar un certificado válido para este dominio.")]
    if est == "caduca_pronto":
        return [_h("web_certificado", BAJA, "El certificado de seguridad (https) caduca en breve", url,
                   f"Caduca el {certificado.get('detalle')} (en {certificado.get('dias')} días).",
                   "RGPD, art. 32 (seguridad del tratamiento)",
                   "Si caduca, el navegador mostrará «sitio no seguro».",
                   "Comprobar que la renovación automática está activa.")]
    return []


# --------------------------------------------------------------------------
# Sobre el HTML descargado
# --------------------------------------------------------------------------

def regla_cookies(paginas_html):
    """Carga analítica o píxeles y no hay ningún gestor de consentimiento reconocible."""
    if not paginas_html:
        return []
    todo = "\n".join(h for _, h in paginas_html)
    if re.search(GESTOR_COOKIES, todo, re.I):
        return []
    vistos = [nombre for nombre, patron in RASTREADORES if re.search(patron, todo, re.I)]
    if not vistos:
        return []
    return [_h("web_cookies", BAJA, "Posibles cookies de analítica o publicidad sin consentimiento: comprobar a mano",
               paginas_html[0][0],
               f"La web carga {', '.join(vistos)} y no se detecta ningún banner o gestor de consentimiento de cookies.",
               "LSSI, art. 22.2 (autoridad: AEPD)",
               "Las cookies que no son técnicas (analítica, publicidad) exigen consentimiento previo del visitante.",
               "Instalar un gestor de consentimiento que bloquee esas cookies hasta que el visitante acepte.",
               sv=("El banner puede cargarse después (p. ej. desde Google Tag Manager) y no verse en el HTML: "
                   "comprobar abriendo la web en una ventana privada antes de mencionarlo."))]


def regla_formularios(paginas_html):
    """Formularios que piden correo o teléfono sin ninguna información de privacidad junto a ellos."""
    malos = []
    for url, html in paginas_html:
        for m in RE_FORM.finditer(html):
            cuerpo = m.group(1)
            campos = set()
            for _, attrs in RE_INPUT.findall(cuerpo):
                a = attrs.lower()
                tipo = re.search(r"type\s*=\s*['\"]?(\w+)", a)
                tipo = tipo.group(1) if tipo else "text"
                if tipo in ("search", "hidden", "submit", "button"):
                    continue
                nombre = re.search(r"name\s*=\s*['\"]?([\w\-\[\]]+)", a)
                nombre = nombre.group(1) if nombre else ""
                if tipo in CAMPOS_DATOS:
                    campos.add(CAMPOS_DATOS[tipo])
                elif re.search(r"mail", nombre):
                    campos.add("correo")
                elif re.search(r"tel|phone|movil", nombre):
                    campos.add("teléfono")
            if not campos or re.search(r"type\s*=\s*['\"]?search", cuerpo, re.I):
                continue
            if re.search(r"<script", cuerpo, re.I):
                continue          # formulario montado con JavaScript (Tilda...): el aviso puede añadirse al cargar
            cerca = plegar(reglas.extraer(url, cuerpo + html[m.end():m.end() + 600]).texto)
            if re.search(AVISO_PRIVACIDAD, cerca):
                continue
            malos.append((url, sorted(campos)))
    if not malos:
        return []
    url, campos = malos[0]
    paginas = sorted({u for u, _ in malos})
    return [_h("web_formulario", MEDIA, "Formulario que recoge datos sin informar de la privacidad", url,
               f"Formulario que pide {' y '.join(campos)} sin ninguna mención a la política de privacidad ni casilla "
               f"de aceptación ({len(paginas)} página{'s' if len(paginas) != 1 else ''}: {', '.join(paginas[:3])}).",
               "RGPD, art. 13",
               "Al recoger datos hay que informar de quién los trata, para qué y cómo ejercer los derechos.",
               "Añadir bajo el botón una primera capa informativa con enlace a la política de privacidad y, si hay "
               "comunicaciones comerciales, una casilla de consentimiento sin marcar.",
               sv=("Comprobar en el navegador que al rellenar el formulario no aparece ningún texto o casilla de "
                   "privacidad antes de mencionarlo."),
               texto=("Responsable: {razon_social}. Finalidad: atender su solicitud y gestionar su cita. Derechos: "
                      "acceso, rectificación, supresión y otros, en {email}. Más información en nuestra Política de "
                      "privacidad."))]


def regla_enlaces_legales(avisos):
    """Páginas legales enlazadas que devuelven error (el rastreador lo anota como "URL respondió 404.")."""
    rotas = []
    for a in avisos or []:
        m = AVISO_ERROR.match(a.strip())
        if m and m.group(2).startswith(("4", "5")) and re.search(RUTA_LEGAL, plegar(m.group(1))):
            rotas.append(f"{m.group(1)} (error {m.group(2)})")
    if not rotas:
        return []
    return [_h("web_legal_roto", BAJA, "Enlace a una página legal que da error", rotas[0].split(" ")[0],
               "La web enlaza páginas legales que no cargan: " + "; ".join(rotas[:3]) + ".",
               "LSSI, art. 10 / RGPD, art. 13",
               "A efectos prácticos es como no tener esa página.",
               "Arreglar el enlace o publicar la página.")]


def regla_registro_distinto(paginas, registro_csv: str):
    """El nº de registro que publica la web no coincide con el del Registro de la CAM para esa dirección."""
    oficial = re.fullmatch(r"\s*(CS|SS|C)\s*-?\s*(\d{3,6})\s*", registro_csv or "", re.I)
    if not oficial:
        return []           # sin dato oficial seguro ("probable", "SIN VERIFICAR"...): no se compara
    num_oficial = oficial.group(2).lstrip("0")
    publicados = set()
    for p in paginas:
        for _, texto in reglas._segmentos(p):
            for m in re.finditer(reglas.NUMERO_REGISTRO, plegar(texto)):
                publicados.add(re.sub(r"\D", "", m.group(0)).lstrip("0"))
    if not publicados or num_oficial in publicados:
        return []
    return [_h("web_registro_distinto", MEDIA,
               "El nº de registro sanitario publicado no coincide con el del Registro de la Comunidad de Madrid",
               paginas[0].url,
               f"La web publica {', '.join('CS' + n for n in sorted(publicados))}; en el Registro de centros sanitarios, "
               f"el centro de esta dirección figura como {registro_csv.strip().upper()}.",
               "Decreto 51/2006 de la Comunidad de Madrid",
               "El número que se publica debe ser el de la autorización del centro que se anuncia.",
               "Publicar el número de registro de este centro.",
               sv="Artículo concreto del Decreto 51/2006: SIN VERIFICAR. El dato del Registro se consultó en su buscador público.")]


def analizar(paginas_html, paginas, web="", avisos=None, certificado=None, registro_csv=""):
    """Todos los hallazgos del escáner. ``paginas`` son las Pagina ya extraídas de ``paginas_html``."""
    out = []
    out += regla_certificado(web, certificado)
    out += regla_cookies(paginas_html)
    out += regla_formularios(paginas_html)
    out += regla_enlaces_legales(avisos)
    out += regla_registro_distinto(paginas, registro_csv)
    return out
