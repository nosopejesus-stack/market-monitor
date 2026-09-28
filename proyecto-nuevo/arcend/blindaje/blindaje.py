#!/usr/bin/env python3
"""Blindaje: revisión de la publicidad sanitaria de la web pública de una clínica.

Uso:
    python blindaje.py https://www.clinica.es --nombre "Clínica X" [--max-paginas 25]
    python blindaje.py --html-local carpeta/ --nombre "Clínica X"

Genera informes/<slug>/informe.html e informe.json.

Solo comprobación PASIVA de información pública: descarga páginas HTML como un
visitante (inicio + enlaces internos del mismo dominio), respeta robots.txt,
hace como máximo 1 petición por segundo y se identifica con su User-Agent.
No escanea puertos, no prueba contraseñas ni busca vulnerabilidades.
Solo biblioteca estándar de Python 3.10+.
"""

from __future__ import annotations

import argparse
import heapq
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import date
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import informe  # noqa: E402
import reglas  # noqa: E402

VERSION = "1.0"
AGENTE = "BlindajeRevisionPublicidad"
USER_AGENT = (f"Mozilla/5.0 (compatible; {AGENTE}/{VERSION}; revision pasiva de publicidad sanitaria, "
              "solo paginas publicas)")
ESPERA_MINIMA = 1.0          # segundos entre peticiones
TAMANO_MAXIMO = 3_000_000    # bytes por página
TIEMPO_MAXIMO = 20           # segundos por petición

EXTENSIONES_NO_HTML = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tif", ".tiff", ".avif",
    ".mp4", ".mov", ".avi", ".webm", ".mp3", ".wav", ".ogg", ".zip", ".rar", ".7z", ".gz", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".css", ".js", ".json", ".xml", ".txt", ".woff", ".woff2", ".ttf",
    ".eot", ".exe", ".dmg", ".apk", ".ics", ".rss",
}
# Rutas que conviene visitar primero (tratamientos, precios, páginas legales, equipo).
PRIORIDAD = re.compile(
    r"tratamiento|toxina|botox|bótox|arruga|labio|facial|precio|tarifa|promo|oferta|antes|despues|después|"
    r"galeria|galería|testimonio|opinion|equipo|doctor|medic|nosotros|quienes|aviso|legal|privacidad|"
    r"cookies|contacto", re.I)
EVITAR = re.compile(r"/(wp-admin|wp-login|login|admin|carrito|cart|checkout|mi-cuenta|my-account|feed)(/|$)|"
                    r"[?&](replytocom|share|add-to-cart)=", re.I)


# --------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------

def obtener_urllib(url, user_agent=USER_AGENT):
    """Devuelve (estado, url_final, content_type, bytes). Lanza OSError si no hay conexión."""
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
        "Accept-Language": "es-ES,es;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIEMPO_MAXIMO) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), r.read(TAMANO_MAXIMO)
    except urllib.error.HTTPError as err:
        cuerpo = b""
        try:
            cuerpo = err.read(TAMANO_MAXIMO)
        except Exception:
            pass
        return err.code, url, err.headers.get("Content-Type", "") if err.headers else "", cuerpo


def decodificar(datos: bytes, content_type: str = "") -> str:
    m = re.search(r"charset=([\w-]+)", content_type or "", re.I)
    candidatos = [m.group(1)] if m else []
    m2 = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", datos[:4096], re.I)
    if m2:
        candidatos.append(m2.group(1).decode("ascii", "ignore"))
    candidatos += ["utf-8", "cp1252"]
    for cod in candidatos:
        try:
            return datos.decode(cod)
        except (LookupError, UnicodeDecodeError):
            continue
    return datos.decode("utf-8", errors="replace")


def normalizar_url(url: str) -> str:
    url, _ = urldefrag(url.strip())
    p = urlparse(url)
    esquema = p.scheme.lower()
    host = (p.hostname or "").lower()
    puerto = p.port
    netloc = host
    if puerto and not ((esquema == "http" and puerto == 80) or (esquema == "https" and puerto == 443)):
        netloc = f"{host}:{puerto}"
    return urlunparse((esquema, netloc, p.path or "/", "", p.query, ""))


def _sin_www(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def mismo_sitio(url: str, host_base: str) -> bool:
    return _sin_www((urlparse(url).hostname or "").lower()) == _sin_www(host_base)


def _es_candidata(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return False
    ext = Path(p.path).suffix.lower()
    return ext not in EXTENSIONES_NO_HTML and not EVITAR.search(url)


class Rastreador:
    """Descarga pasiva y educada de las páginas públicas de un sitio."""

    def __init__(self, url_inicio, max_paginas=25, obtener=None, dormir=time.sleep, reloj=time.monotonic,
                 user_agent=USER_AGENT, log=print):
        if "://" not in url_inicio:
            url_inicio = "https://" + url_inicio
        self.inicio = normalizar_url(url_inicio)
        self.host = (urlparse(self.inicio).hostname or "").lower()
        self.max_paginas = max(1, max_paginas)
        self.obtener = obtener or (lambda u: obtener_urllib(u, user_agent))
        self.dormir, self.reloj, self.log = dormir, reloj, log
        self.espera = ESPERA_MINIMA
        self._ultima = None
        self.robots = None
        self.avisos: list[str] = []
        self.peticiones: list[str] = []

    # -- cortesía --------------------------------------------------------
    def _pedir(self, url):
        if self._ultima is not None:
            falta = self.espera - (self.reloj() - self._ultima)
            if falta > 0:
                self.dormir(falta)
        self.peticiones.append(url)
        try:
            return self.obtener(url)
        finally:
            self._ultima = self.reloj()

    def _cargar_robots(self, url_base):
        p = urlparse(url_base)
        url_robots = f"{p.scheme}://{p.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser(url_robots)
        try:
            estado, _, _, cuerpo = self._pedir(url_robots)
        except Exception as err:  # sin conexión: mejor no descargar nada
            self.avisos.append(f"No se pudo leer robots.txt ({err}); no se descarga nada del sitio.")
            rp.disallow_all = True
            return rp
        if estado == 200:
            rp.parse(decodificar(cuerpo).splitlines())
            rp.modified()
        elif estado in (401, 403):
            rp.disallow_all = True
            self.avisos.append(f"robots.txt responde {estado}: se interpreta como prohibido descargar.")
        elif estado >= 500:
            rp.disallow_all = True
            self.avisos.append(f"robots.txt responde {estado}: se interpreta como prohibido descargar.")
        else:
            rp.allow_all = True
        retraso = None
        try:
            retraso = rp.crawl_delay(AGENTE) or rp.crawl_delay("*")
        except Exception:
            pass
        if retraso:
            self.espera = max(ESPERA_MINIMA, float(retraso))
        return rp

    def permitido(self, url) -> bool:
        return self.robots is not None and self.robots.can_fetch(AGENTE, url)

    # -- rastreo ---------------------------------------------------------
    def rastrear(self):
        """Devuelve lista de (url, html)."""
        self.robots = self._cargar_robots(self.inicio)
        cola = [(0, 0, 0, self.inicio)]
        vistos = {self.inicio}
        orden = 0
        paginas = []
        primera = True
        while cola and len(paginas) < self.max_paginas:
            prof, _, _, url = heapq.heappop(cola)
            if not self.permitido(url):
                self.avisos.append(f"robots.txt no permite {url}: no se descarga.")
                continue
            try:
                estado, final, ctype, cuerpo = self._pedir(url)
            except Exception as err:
                self.avisos.append(f"No se pudo descargar {url}: {err}")
                continue
            final = normalizar_url(final or url)
            if primera:
                primera = False
                host_final = (urlparse(final).hostname or "").lower()
                if _sin_www(host_final) != _sin_www(self.host):
                    self.avisos.append(f"La web redirige a {host_final}; se revisa ese dominio.")
                    self.host = host_final
                    self.robots = self._cargar_robots(final)
                    if not self.permitido(final):
                        self.avisos.append(f"robots.txt no permite {final}: no se descarga.")
                        break
            elif not mismo_sitio(final, self.host):
                continue
            if estado != 200:
                self.avisos.append(f"{url} respondió {estado}.")
                continue
            if "html" not in (ctype or "").lower() and ctype:
                continue
            html = decodificar(cuerpo, ctype)
            paginas.append((final, html))
            vistos.add(final)
            self.log(f"  [{len(paginas)}/{self.max_paginas}] {final}")
            for href, texto in reglas.extraer(final, html).enlaces:
                if not href or href.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
                    continue
                nueva = normalizar_url(urljoin(final, href))
                if nueva in vistos or not mismo_sitio(nueva, self.host) or not _es_candidata(nueva):
                    continue
                vistos.add(nueva)
                orden += 1
                prio = 0 if PRIORIDAD.search(nueva + " " + texto) else 1
                heapq.heappush(cola, (prof + 1, prio, orden, nueva))
        return paginas


def cargar_local(carpeta):
    """Lee los .html/.htm de una carpeta (recursivo). Devuelve lista de (url, html)."""
    base = Path(carpeta)
    if not base.is_dir():
        raise SystemExit(f"No existe la carpeta {carpeta}")
    archivos = sorted(p for p in base.rglob("*") if p.suffix.lower() in (".html", ".htm") and p.is_file())
    # index.html primero: hace de página de inicio
    archivos.sort(key=lambda p: (p.name.lower() not in ("index.html", "index.htm"), len(p.parts), str(p)))
    return [(p.relative_to(base).as_posix(), decodificar(p.read_bytes())) for p in archivos]


# --------------------------------------------------------------------------
# Programa
# --------------------------------------------------------------------------

def slug(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", reglas.plegar(texto)).strip("-")
    return s[:60] or "clinica"


def ejecutar(paginas_html, clinica, web, salida, avisos=None, contacto=None, fecha=None, modo="web"):
    paginas = [reglas.extraer(u, h) for u, h in paginas_html]
    hallazgos = reglas.analizar(paginas)
    puntos, nota = reglas.puntuar(hallazgos)
    datos = {
        "clinica": clinica,
        "web": web,
        "fecha": fecha or date.today().strftime("%d/%m/%Y"),
        "paginas": [p.url for p in paginas],
        "puntuacion": puntos,
        "nota": nota,
        "avisos": list(avisos or []),
        "modo": modo,
        "herramienta": f"blindaje {VERSION}",
    }
    carpeta = Path(salida) / slug(clinica)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "informe.html").write_text(informe.generar_html(datos, hallazgos, contacto), encoding="utf-8")
    (carpeta / "informe.json").write_text(informe.generar_json(datos, hallazgos), encoding="utf-8")
    return carpeta, datos, hallazgos


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="Revisión pasiva de la publicidad sanitaria de la web pública de una clínica.")
    ap.add_argument("url", nargs="?", help="web de la clínica, p. ej. https://www.clinica.es")
    ap.add_argument("--nombre", required=True, help='nombre de la clínica, p. ej. "Clínica X"')
    ap.add_argument("--max-paginas", type=int, default=25, help="páginas como máximo (por defecto 25)")
    ap.add_argument("--html-local", metavar="CARPETA", help="analizar HTML guardado en una carpeta, sin red")
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent / "informes"),
                    help="carpeta de informes (por defecto ./informes)")
    ap.add_argument("--contacto-nombre", default="", help="tu nombre para el informe")
    ap.add_argument("--contacto-telefono", default="", help="tu teléfono para el informe")
    ap.add_argument("--contacto-email", default="", help="tu email para el informe")
    args = ap.parse_args(argv)

    if not args.url and not args.html_local:
        ap.error("indica la web de la clínica o --html-local CARPETA")

    avisos = []
    if args.html_local:
        paginas_html = cargar_local(args.html_local)
        web = args.url or f"(HTML guardado: {Path(args.html_local).name})"
        print(f"Analizando {len(paginas_html)} archivo(s) HTML de {args.html_local}")
    else:
        web = args.url if "://" in args.url else "https://" + args.url
        print(f"Descargando páginas públicas de {web} (máx. {args.max_paginas}, 1 petición/segundo)...")
        r = Rastreador(web, max_paginas=args.max_paginas)
        paginas_html = r.rastrear()
        avisos = r.avisos
        for a in avisos:
            print("  aviso:", a)
    if not paginas_html:
        print("No se ha podido leer ninguna página. Si la web bloquea la descarga, guarde las páginas desde "
              "el navegador (Ctrl+S) en una carpeta y use --html-local CARPETA.")
        return 2

    contacto = {"nombre": args.contacto_nombre, "telefono": args.contacto_telefono, "email": args.contacto_email}
    carpeta, datos, hallazgos = ejecutar(paginas_html, args.nombre, web, args.salida, avisos, contacto,
                                         modo="local" if args.html_local else "web")
    print(f"\nNota {datos['nota']} ({datos['puntuacion']}/100) · {len(hallazgos)} hallazgo(s)")
    for h in hallazgos:
        print(f"  [{h.gravedad}] {h.titulo} · {h.url}")
    print(f"\nInforme: {carpeta / 'informe.html'}\nDatos:   {carpeta / 'informe.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
