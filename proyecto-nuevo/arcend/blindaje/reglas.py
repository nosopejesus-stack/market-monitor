"""Reglas de revisión de la publicidad sanitaria de una web de clínica estética.

Todo lo de este archivo trabaja sobre HTML ya descargado: no hace peticiones.

Cómo están escritos los patrones
--------------------------------
- El texto se "pliega" antes de buscar: minúsculas y sin tildes (``plegar``),
  carácter a carácter, de modo que las posiciones coinciden con el texto
  original. Por eso los patrones van en minúsculas y sin tildes
  ("despues", "resenas", "botulinica").
- Para ajustar una regla basta con tocar las listas/regex de este archivo y
  volver a pasar los tests (``python -m unittest discover -s tests -v``).

Normativa en la que se apoya cada regla (fuente: arcend/investigacion/mercado.md)
- Toxina botulínica y marcas: RD 1416/1994 + RDL 1/2015 (prohibida la
  publicidad al público de medicamentos con receta, también por alusiones
  indirectas: "neuromoduladores", siglas, hashtags). ALTA. Si la frase niega o
  explica la prohibición ("no anunciamos...", "la ley prohíbe...") pasa a BAJA
  de revisión manual ("toxina_revisar").
- Promesas: RD 1907/1996, art. 4 (garantías de resultado, "sin riesgo",
  ausencia de efectos secundarios...). El apartado exacto de cada supuesto está
  SIN VERIFICAR (boe.es bloqueado al investigar). ALTA. "Sin dolor"/"indoloro"
  y "milagro" son MEDIA ("puede considerarse...").
- Nº de registro sanitario: Decreto 51/2006 de la Comunidad de Madrid. ALTA
  (artículo concreto SIN VERIFICAR).
- Promociones sobre actos médicos: criterio de riesgo (incentivo al consumo);
  si afectan a toxina, entra en la infracción del RDL 1/2015. MEDIA.
- Antes/después: RGPD/AEPD (consentimiento del paciente). No está prohibido
  per se en Madrid (SIN VERIFICAR la postura escrita de la Consejería). MEDIA.
- Testimonios de pacientes: RD 1907/1996, art. 4 (apartado SIN VERIFICAR). MEDIA.
- Aviso legal / privacidad / cookies: LSSI art. 10 y 22.2, RGPD art. 13. BAJA.
- Médico responsable y nº de colegiado: buena práctica; norma general que lo
  exija en la publicidad del centro SIN VERIFICAR. BAJA.

Falsos positivos evitados (cada uno tiene test)
- "garantizamos su privacidad", "pago 100 % seguro", "sin riesgo para sus
  datos": las promesas genéricas exigen contexto de tratamiento/resultado y
  ninguna palabra de exclusión (datos, pago, privacidad...).
- "tratamiento de datos" no cuenta como tratamiento médico.
- "casi sin dolor" / "prácticamente indoloro": no es una promesa absoluta.
- Negaciones: "no garantizamos resultados", "ningún médico serio le ofrecerá
  resultados garantizados", "no hace milagros", "no existe un tratamiento sin
  riesgo", "el láser no es indoloro".
- "Dra. Milagros" / "Calle Milagros" / "DRA. MILAGROS PÉREZ": nombre propio.
- "eliminar toxinas" (plural, detox), "botox capilar", "efecto botox" no son
  toxina botulínica.
- "antes y después del tratamiento evite el sol", "cuidados antes y después
  del tratamiento": sin contexto de foto no es una galería de antes/después.
- "parking gratuito", "envío gratis", "nuestra oferta de tratamientos".
- Textos que explican que la ley prohíbe los testimonios.
- Registro: un teléfono, una calle o un código postal cerca de "registro
  sanitario" no cuentan como número de registro.
- "El resultado definitivo se aprecia a las dos semanas": no es una promesa
  (por eso "definitivo" no está en la regla; sí "resultados permanentes",
  "para siempre" y "cura definitiva").

Revisión manual del lote real (2026-09-29, 996 hallazgos de 39 webs; cada caso tiene test)
- Reseñas de pacientes (widgets con class/id review, testimon, trustindex, ti-...
  o frases en primera persona "me puse bótox", "llevo viniendo"): no son
  publicidad redactada por la clínica; solo cuentan en la regla de testimonios,
  y una clase CSS sin texto visible no basta.
- Promociones: consulta/cita/diagnóstico/asesoramiento gratuitos, línea 900,
  "promoción de la salud", "5 promociones médicas", newsletter, "amplia/nuestra
  oferta", negaciones ("incompatibles con ese tipo de ofertas"), preguntas de
  blog, bonos con precio sin descuento y tratamientos no médicos (masaje,
  higiene facial, dermocosmética, aparatología, psicología). "Promociones" sin
  precio ni descuento queda como BAJA "promociones_revisar" (no cuenta en N).
- Toxina en el currículum del médico ("formación en neuromoduladores") o en una
  reseña: pasa a "toxina_revisar". "POST-TOXINA" (cosmético) no es el medicamento.
- Promesas: "garantizar" como consejo, finalidad o dicho de la AEMPS; "sin
  dolor" matizado (suelen ser, generalmente, la mayoría, significativo) o como
  síntoma; "dietas milagro", "La Milagrosa"; "sin riesgo de rechazo" es MEDIA.
- Antes/después sin fotos: cuidados, preguntas frecuentes.
- Registro: no se afirma que falte si no se ha leído el aviso legal
  ("registro_sin_lectura", BAJA); "asegúrese de que la clínica cuente con
  autorización" es un consejo, no una mención.
- N = tipos de infracción distintos, no frases: el menú repetido en 15 páginas
  inflaba la cifra.

Traído del risk-scanner antiguo (2026-09-29)
- Promesas "100 % eficaz/efectivo", "resultados permanentes", "cura
  definitiva" (sanitario.py). Sus superlativos ("el mejor de Madrid") NO se
  han traído: no hay norma sanitaria concreta verificada que los prohíba.
- Detector de posible cadena (chain_detector.py) como dato interno del lote.
- No traído: comprobar si los enlaces legales acaban en la portada (solo
  evitaría falsos negativos) ni la valoración schema (va en <script>).
- Las páginas legales (aviso legal, privacidad, cookies) no se revisan con
  las reglas de promesas, promociones ni testimonios.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

ALTA, MEDIA, BAJA = "ALTA", "MEDIA", "BAJA"

# --------------------------------------------------------------------------
# Utilidades de texto
# --------------------------------------------------------------------------


def _plegar_car(c: str) -> str:
    bajo = c.lower()
    if len(bajo) != 1:  # p. ej. "İ" -> "i̇": nos quedamos con el primero
        bajo = bajo[0]
    descompuesto = unicodedata.normalize("NFD", bajo)
    return descompuesto[0] if descompuesto else c


def plegar(texto: str) -> str:
    """Minúsculas y sin tildes, con la MISMA longitud que el original."""
    return "".join(_plegar_car(c) for c in texto)


def _hay(patron: str, texto_plegado: str) -> bool:
    return re.search(patron, texto_plegado) is not None


def _frase(plegado: str, ini: int, fin: int) -> str:
    """Frase (entre puntos o saltos de línea) que contiene la coincidencia, en texto plegado."""
    a = max(plegado.rfind(c, 0, ini) for c in ".!?\n") + 1
    fins = [i for i in (plegado.find(c, fin) for c in ".!?\n") if i != -1]
    return plegado[a:min(fins) if fins else len(plegado)]


def _ventana(plegado: str, ini: int, fin: int, ancho: int) -> str:
    return plegado[max(0, ini - ancho): fin + ancho]


def fragmento(texto: str, ini: int, fin: int, max_len: int = 280):
    """Devuelve (frase que contiene la coincidencia, inicio_rel, fin_rel)."""
    a = texto.rfind("\n", 0, ini) + 1
    b = texto.find("\n", fin)
    b = len(texto) if b == -1 else b
    linea = texto[a:b]
    ri, rf = ini - a, fin - a
    s = 0
    for m in re.finditer(r"[.!?]\s+", linea[:ri]):
        s = m.end()
    e = len(linea)
    m = re.search(r"[.!?](?=\s|$)", linea[rf:])
    if m:
        e = rf + m.end()
    pre = post = ""
    if e - s > max_len:
        mitad = max(40, (max_len - (rf - ri)) // 2)
        s2, e2 = max(s, ri - mitad), min(e, rf + mitad)
        if s2 > s:
            esp = linea.find(" ", s2, ri)
            s2 = esp + 1 if esp != -1 else s2
            pre = "…"
        if e2 < e:
            esp = linea.rfind(" ", rf, e2)
            e2 = esp if esp != -1 else e2
            post = "…"
        s, e = s2, e2
    trozo = linea[s:e]
    izq = len(trozo) - len(trozo.lstrip())
    trozo = trozo.strip()
    mi = ri - s - izq
    return pre + trozo + post, mi + len(pre), mi + len(pre) + (rf - ri)


# --------------------------------------------------------------------------
# Extracción de HTML (solo biblioteca estándar)
# --------------------------------------------------------------------------

_BLOQUES = {
    "p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
    "tr", "td", "th", "table", "section", "article", "header", "footer",
    "nav", "aside", "main", "form", "button", "blockquote", "figure",
    "figcaption", "dd", "dt", "hr", "option", "label",
}
_OMITIR = {"script", "style", "noscript", "template", "svg"}
_VACIAS = {"img", "br", "hr", "input", "meta", "link", "source", "area", "col", "embed", "wbr", "base", "track"}
# Bloques de reseñas o testimonios (widgets de Google, Trustindex, Elementor...): su texto lo escribe
# un paciente, no la clínica, y nunca cuenta como publicidad redactada por la clínica.
ATRIBUTO_RESENA = (r"testimon|review|resena|trustindex|\bti-|elfsight|grw-|google-reviews|"
                   r"opiniones-clientes|valoraciones")
# Menú, migas y pie: el mismo texto se repite en todas las páginas.
ATRIBUTO_MENU = r"(^|[\s_-])(menu|navbar|nav|navigation|breadcrumbs?|migas|footer|pie)([\s_-]|$)"


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self.titulo: list[str] = []
        self.descripcion = ""
        self.enlaces: list[tuple[str, str]] = []
        self.imagenes: list[tuple[str, str, str]] = []
        self.atributos: list[str] = []
        self._omitir = 0
        self._en_titulo = False
        self._enlace = None
        self.resenas: list[str] = []
        self.menu: list[str] = []
        self._zona = None          # [tipo, etiqueta, profundidad]

    def handle_starttag(self, tag, attrs):
        if self._omitir:
            if tag in _OMITIR:
                self._omitir += 1
            return
        if tag in _OMITIR:
            self._omitir = 1
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._en_titulo = True
        elif tag == "meta":
            nombre = (a.get("name") or a.get("property") or "").lower()
            if nombre in ("description", "og:description") and not self.descripcion:
                self.descripcion = a.get("content", "")
        elif tag == "a":
            self._cerrar_enlace()
            self._enlace = [a.get("href", ""), []]
        elif tag == "img":
            src = a.get("src") or a.get("data-src") or a.get("data-lazy-src") or ""
            self.imagenes.append((src, a.get("alt", ""), a.get("title", "")))
        for k in ("class", "id"):
            if a.get(k):
                self.atributos.append(a[k])
        if self._zona is not None:
            if tag == self._zona[1]:
                self._zona[2] += 1
        elif tag not in _VACIAS:
            attr = " ".join(a.get(k, "") for k in ("class", "id")).lower()
            if re.search(ATRIBUTO_RESENA, attr):
                self._zona = ["resena", tag, 1]
            elif tag in ("nav", "footer") or re.search(ATRIBUTO_MENU, attr):
                self._zona = ["menu", tag, 1]
        if tag in _BLOQUES:
            self._anadir("\n")

    def _anadir(self, texto):
        self.partes.append(texto)
        if self._zona is not None:
            (self.resenas if self._zona[0] == "resena" else self.menu).append(texto)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in _OMITIR and self._omitir:
            self._omitir -= 1

    def handle_endtag(self, tag):
        if tag in _OMITIR:
            if self._omitir:
                self._omitir -= 1
            return
        if self._omitir:
            return
        if tag == "title":
            self._en_titulo = False
        elif tag == "a":
            self._cerrar_enlace()
        if tag in _BLOQUES:
            self._anadir("\n")
        if self._zona is not None and tag == self._zona[1]:
            self._zona[2] -= 1
            if self._zona[2] <= 0:
                self._zona = None

    def _cerrar_enlace(self):
        if self._enlace is not None:
            href, textos = self._enlace
            self.enlaces.append((href, " ".join("".join(textos).split())))
            self._enlace = None

    def handle_data(self, data):
        if self._omitir:
            return
        if self._en_titulo:
            self.titulo.append(data)
            return
        self._anadir(data)
        if self._enlace is not None:
            self._enlace[1].append(data)


@dataclass
class Pagina:
    url: str
    titulo: str
    descripcion: str
    texto: str
    enlaces: list
    imagenes: list
    atributos: list
    resenas: str = ""        # texto de bloques de reseñas/testimonios (lo escribe un paciente)
    menu: str = ""           # texto de menú, migas y pie (se repite en todas las páginas)

    @property
    def es_legal(self) -> bool:
        ruta = plegar(unquote(urlparse(self.url).path))
        cabecera = plegar(self.titulo)
        patron = r"aviso.?legal|privacidad|privacy|cookies|legal.?notice|proteccion.?de.?datos|condiciones.?de.?uso|terminos"
        return _hay(patron, ruta) or _hay(patron, cabecera)


def extraer(url: str, html: str) -> Pagina:
    ex = _Extractor()
    try:
        ex.feed(html)
        ex.close()
    except Exception:  # HTML muy roto: nos quedamos con lo que haya salido
        pass
    ex._cerrar_enlace()
    def limpio(partes):
        lineas = [" ".join(l.split()) for l in "".join(partes).split("\n")]
        return "\n".join(l for l in lineas if l)

    texto = limpio(ex.partes)
    return Pagina(
        url=url,
        titulo=" ".join("".join(ex.titulo).split()),
        descripcion=" ".join(ex.descripcion.split()),
        texto=texto,
        enlaces=ex.enlaces,
        imagenes=ex.imagenes,
        atributos=ex.atributos,
        resenas=limpio(ex.resenas),
        menu=limpio(ex.menu),
    )


def _ruta_legible(url: str) -> str:
    p = urlparse(url)
    ruta = unquote(p.path) + ((" " + unquote(p.query)) if p.query else "")
    return re.sub(r"[-_/.=&+]+", " ", ruta).strip()


def _sin_zona(texto: str, zona: str) -> str:
    """Quita del texto las líneas que pertenecen a una zona (reseñas o menú)."""
    if not zona:
        return texto
    fuera = set(zona.split("\n"))
    return "\n".join(l for l in texto.split("\n") if l not in fuera)


def _segmentos(p: Pagina, con_url: bool = False, con_menu: bool = True):
    """Textos escritos por la clínica. Las reseñas de pacientes nunca se incluyen."""
    segs = [("texto de la página", _sin_zona(_sin_zona(p.texto, p.resenas), p.menu))]
    if con_menu:
        segs.append(("menú o pie de la web", _sin_zona(p.menu, p.resenas)))
    segs += [("título de la página", p.titulo),
            ("descripción para buscadores", p.descripcion),
            ("texto alternativo de imágenes", "\n".join(alt for _, alt, _ in p.imagenes if alt.strip()))]
    if con_url:
        segs.append(("dirección (URL) de la página", _ruta_legible(p.url)))
    return [(u, t) for u, t in segs if t]


# --------------------------------------------------------------------------
# Hallazgo
# --------------------------------------------------------------------------


@dataclass
class Hallazgo:
    regla: str
    gravedad: str
    titulo: str
    url: str
    ubicacion: str
    evidencia: str
    marca_inicio: int
    marca_fin: int
    accion: str
    texto_corregido: str
    base_normativa: str
    sin_verificar: str = ""
    apariciones: int = 1
    otras_evidencias: list = field(default_factory=list)
    norma: str = ""          # referencia corta (para el informe previo)


def _hallazgo_de_coincidencias(regla, coincidencias, url, **kw):
    """Agrupa las coincidencias de una regla en una página en un hallazgo."""
    ubic, texto, ini, fin = coincidencias[0]
    ev, mi, mf = fragmento(texto, ini, fin)
    otras = []
    for u, t, i, f in coincidencias[1:]:
        fr = fragmento(t, i, f)[0]
        if fr != ev and fr not in otras and len(otras) < 3:
            otras.append(fr)
    return Hallazgo(regla=regla, url=url, ubicacion=ubic, evidencia=ev,
                    marca_inicio=mi, marca_fin=mf, apariciones=len(coincidencias),
                    otras_evidencias=otras, **kw)


# --------------------------------------------------------------------------
# ALTA 1: toxina botulínica (medicamento con receta)
# --------------------------------------------------------------------------

# (?<![a-z]) en vez de \b para cazar también hashtags pegados: #botoxmadrid
PATRONES_TOXINA = [
    r"toxinas?\s+botulinicas?",
    r"\btoxina\b(?!s)(?!\s+botul)",       # "la toxina" (singular); "toxinas" = detox
    r"(?<![a-z])botox",                   # bótox / Botox / #botox
    r"(?<![a-z])vistabel",
    r"(?<![a-z])azzalure",
    r"(?<![a-z])bocouture",
    r"(?<![a-z])dysport",
    r"(?<![a-z])xeomin",
    r"(?<![a-z])letybo",
    r"(?<![a-z])alluzience",              # marca añadida: toxina de Galderma (SIN VERIFICAR en AEMPS)
    r"\bneuromodulador(es|a|as)?\b",
    r"\bbtx\b",                           # siglas
]

TOXINA = dict(
    titulo="Publicidad de un medicamento con receta (toxina botulínica)",
    gravedad=ALTA,
    norma="RD 1416/1994 y RDL 1/2015 (publicidad de medicamentos con receta)",
    base_normativa=("RD 1416/1994 de publicidad de medicamentos y RDL 1/2015 (Ley de garantías y uso "
                    "racional de los medicamentos): está prohibida la publicidad dirigida al público de "
                    "medicamentos que necesitan receta, como la toxina botulínica, también por alusiones "
                    "indirectas (\"neuromoduladores\", siglas, hashtags) y por ofertas ligadas a ellos."),
    accion=("Retirar de la web el nombre del medicamento y sus marcas, sus siglas, los hashtags, los precios "
            "por zona y cualquier promoción ligada a él. Puede hablarse de la consulta médica, no del medicamento."),
    texto_corregido=("Arrugas de expresión: en una consulta de valoración, el médico estudia su caso y le "
                     "explica las opciones indicadas para usted, con sus beneficios y riesgos."),
)


# No es el medicamento: tratamientos capilares y el "efecto bótox" de cosméticos.
EXCLUSION_TOXINA = r"post.?toxina|botox\s*capilar|efecto\s+(tipo\s+)?botox|botox\s+(para\s+el\s+)?(pelo|cabello)"
# Texto que explica la prohibición: no es publicidad del medicamento, pero hay que revisarlo a mano.
# Currículum o formación del médico ("formación avanzada en toxina botulínica"): no ofrece el tratamiento.
CV_TOXINA = r"\b(formacion|formado|formada|master|curso|cursos|congreso|experto|experta|diploma|acreditad)\b"
EXPLICATIVO_TOXINA = r"prohib|\bno\s+(anunciamos|publicitamos|podemos\s+anunciar|se\s+puede\s+anunciar)"

TOXINA_REVISAR = dict(
    titulo="Mención de la toxina botulínica en un texto explicativo o negativo: revisar a mano",
    gravedad=BAJA,
    norma="RD 1416/1994 y RDL 1/2015 (publicidad de medicamentos con receta)",
    base_normativa=("La frase parece explicar o negar el uso del medicamento, no anunciarlo. Aun así, nombrarlo "
                    "(o sus marcas) en la web puede interpretarse como alusión publicitaria."),
    accion="Revisar la frase a mano; si no es imprescindible, hablar de la consulta médica sin nombrar el medicamento.",
    texto_corregido=TOXINA["texto_corregido"],
    sin_verificar="Criterio de la Consejería sobre menciones explicativas o informativas: SIN VERIFICAR.",
)


def regla_toxina(p: Pagina):
    coinc, revisar = [], []
    for ubic, texto in _segmentos(p, con_url=True):
        pl = plegar(texto)
        for patron in PATRONES_TOXINA:
            for m in re.finditer(patron, pl):
                ini, fin = m.start(), m.end()
                if _hay(EXCLUSION_TOXINA, _ventana(pl, ini, fin, 20)):
                    continue
                c = (ubic, texto, ini, fin)
                frase = _frase(pl, ini, fin)
                if _negado(pl, ini, fin, 25) or _hay(EXPLICATIVO_TOXINA, _ventana(pl, ini, fin, 80)) or \
                        _hay(CV_TOXINA, frase) or _hay(VOZ_PACIENTE, frase):
                    revisar.append(c)
                else:
                    coinc.append(c)
    orden = lambda c: (c[0] != "texto de la página", c[2])  # noqa: E731
    if not coinc:
        if not revisar:
            return []
        revisar.sort(key=orden)
        return [_hallazgo_de_coincidencias("toxina_revisar", revisar, p.url, **TOXINA_REVISAR)]
    coinc.sort(key=orden)
    kw = dict(TOXINA)
    if any(c[0].startswith("dirección") for c in coinc):
        kw["accion"] += (" La dirección de la página también nombra el medicamento: cámbiela por una neutra "
                         "(p. ej. /arrugas-de-expresion) y redirija la antigua.")
    return [_hallazgo_de_coincidencias("toxina", coinc, p.url, **kw)]


# --------------------------------------------------------------------------
# ALTA 2: promesas prohibidas
# --------------------------------------------------------------------------

# Palabras que dan contexto sanitario/de resultado (para las promesas que lo exigen).
CONTEXTO_RESULTADO = (
    r"resultad|tratamient(?!os?\s+de\s+(sus\s+|los\s+)?datos)|efecto|arruga|piel|rejuvenec|rostro|\bcara\b|labio|"
    r"eficacia|eficaz|mejora|elimin|\bcura|botox|toxina|relleno|hialuronico|cicatri|ojera|flacidez|grasa|"
    r"celulitis|intervencion|sesion|aspecto|bellez|juventud|lifting|papada|manchas|acne|depilacion|laser"
)
# Si aparece cerca, la frase no es una promesa sanitaria.
EXCLUSION_PROMESA = (
    r"privacidad|\bdatos\b|confidencial|\bpago|compra|tarjeta|cookies|envio|devolu|reembolso|dinero|"
    r"conexion|\bssl\b|navegacion|\bweb\b|informacion personal|cancelac"
)
# "Garantizar" solo es promesa si lo garantizado es el resultado o su eficacia, y no es una
# finalidad ("para garantizar su comodidad", "elija un médico para garantizar resultados").
GARANTIA_OBJETO = (r"resultad|eficacia|eficaz|efectiv|\bexito|sin\s+(ningun\s+)?(riesgo|dolor|efecto)|desaparec|"
                   r"\belimin|\bquitar|\bborrar")
GARANTIA_FINALIDAD = r"\bpara\s+(asi\s+|poder\s+)?$|\ba\s+fin\s+de\s+$|\bcon\s+el\s+(fin|objetivo)\s+de\s+$"

# Matizadores que convierten "sin dolor" en una afirmación no absoluta.
MATIZ_DOLOR = (r"(casi|practicamente|apenas|minim\w*|poco|mas o menos|relativamente|suelen?\s+ser|suelen?|"
               r"generalmente|normalmente|habitualmente|por\s+lo\s+general|la\s+mayoria(\s+de\s+los\s+casos)?(\s+son)?|"
               r"algunas\s+personas(\s+\w+){0,4})\s*(\w+\s+){0,2}$")
# Matiz detrás: "sin dolor significativo", "indoloros o ligeramente molestos".
MATIZ_DOLOR_DETRAS = r"^\s*(significativ|importante|intenso|excesivo|o\s+(ligeramente|poco|apenas)\s+molest)"
# "Sin dolor" como síntoma que se trata ("una vida sin dolor ni molestias provocadas por el bruxismo").
DOLOR_SINTOMA = r"vida\s+sin\s+dolor|sin\s+dolor\s+ni\s+molestias\s+(provocad|causad)|dolor\s+(provocad|causad)"
# "Milagro" despectivo o nombre propio: "sin dietas milagro", "Vithas La Milagrosa".
MILAGRO_NO_PROMESA = r"dietas?\s*\W?\s*milagr|\bla\s+milagrosa\b|\bsin\s+(\w+\s+)?\W?milagr|productos?\s+milagro"
# Consejo o autoridad que garantiza ("es importante... para garantizar", "la AEMPS se encarga de garantizar").
GARANTIA_CONSEJO = (r"\b(debe|deben|importante|fundamental|clave|elegir|seguir\s+las|recomendable|esencial|conviene)\b"
                    r"[^.]{0,80}$|\b(aemps|agencia|ministerio|ley|normativa|fabricante)\b[^.]{0,60}$")

PROMESAS = [
    # (id, patrón, exige_contexto, aplica_exclusion)
    ("resultados garantizados", r"resultados?\s+(100\s*%\s*)?garantizad[oa]s?|garantia\s+de\s+(los\s+)?resultados?", False, False),
    ("garantía", r"\bgarantiz\w*", True, True),
    ("sin riesgo", r"\bsin\s+(ningun\s+)?riesgos?\b", True, True),
    ("sin efectos secundarios", r"\bsin\s+(ningun\s+|ningunos\s+)?efectos?\s+(secundarios?|adversos?)", False, False),
    ("100 % seguro", r"\b100\s*%\s*segur[oa]s?\b|\bcien\s+por\s+cien\s+segur[oa]s?\b", True, True),
    ("100 % eficaz", r"\b100\s*%\s*(efectiv|eficaz)\w*|\bcien\s+por\s+cien\s+(efectiv|eficaz)\w*", True, True),
    ("resultados permanentes", r"resultados?\s+(permanentes?|para\s+siempre)|\bcura\s+definitiva", False, False),
    ("sin dolor", r"\bsin\s+(ningun\s+)?dolor\b|\bindolor[oa]s?\b", False, False),
    ("milagro", r"\bmilagr(o|os|oso|osa|osos|osas)\b", False, False),
]

SUSTITUCIONES_PROMESA = [
    (r"resultados?\s+(100\s*%\s*)?garantizad[oa]s?", "resultados que varían en cada paciente"),
    (r"garantia\s+de\s+(los\s+)?resultados?", "seguimiento de los resultados"),
    (r"\bgarantizamos\b", "buscamos"),
    (r"\s*\b(100\s*%\s*)?garantizad[oa]s?\b", ""),
    (r"\bgarantiza\b", "busca"),
    (r"\bsin\s+(ningun\s+|ningunos\s+)?efectos?\s+(secundarios?|adversos?)", "con posibles efectos secundarios, que le explicamos antes"),
    (r"\bsin\s+(ningun\s+)?riesgos?\b", "con valoración médica previa"),
    (r"\b100\s*%\s*segur[oa]s?\b|\bcien\s+por\s+cien\s+segur[oa]s?\b", "realizado por personal médico"),
    (r"\b100\s*%\s*(efectiv|eficaz)\w*|\bcien\s+por\s+cien\s+(efectiv|eficaz)\w*", "indicado tras valoración médica"),
    (r"\bsin\s+(ningun\s+)?dolor\b", "con mínimas molestias"),
    (r"\bindolor[oa]s?\b", "con mínimas molestias"),
    (r"\b(efecto|resultado)(s?)\s+milagro(s[oa]s?)?\b", r"\1\2 natural"),
    (r"\bmilagros[oa]s?\b", "eficaz"),
    (r"\bmilagros?\b", "cambio"),
]

# Si, tras sustituir, la frase sigue prometiendo plazos o resultados, se propone un texto genérico.
PROMESA_RESIDUAL = (r"desaparec|para siempre|definitiv|\ben\s+(una|un|\d+)\s+(semana|dia|mes|sesion)|"
                    r"\beliminar(a|an|emos)\b|\bquitar(a|an|emos)\b|\bconseguir(a|as|emos)\b")
TEXTO_PROMESA_GENERICO = "En la consulta de valoración le explicamos qué resultados puede esperar en su caso."

AVISO_RESULTADOS = ("Los resultados varían en cada persona; el médico le explicará en la consulta "
                    "los posibles riesgos y efectos secundarios.")

SV_ART4 = "Apartado concreto del art. 4 del RD 1907/1996: SIN VERIFICAR (texto oficial no consultado)."

PROMESA_BASE = dict(
    titulo="Promesa sanitaria prohibida",
    gravedad=ALTA,
    norma="RD 1907/1996, art. 4",
    base_normativa=("RD 1907/1996 (publicidad con pretendida finalidad sanitaria), art. 4: prohíbe la publicidad "
                    "que ofrezca garantías de resultado o seguridades de ausencia de riesgos o efectos secundarios."),
    accion="Sustituir la frase por el texto corregido.",
    sin_verificar=SV_ART4,
)
# Afirmaciones que no son una garantía expresa: riesgo medio, redactado como "puede considerarse".
PROMESA_MEDIA = {
    "sin dolor": dict(
        titulo="Afirmación absoluta sobre dolor o riesgo",
        base_normativa=("Puede considerarse una seguridad de ausencia de molestias o riesgos, que el RD 1907/1996 "
                        "(art. 4) no permite en la publicidad con finalidad sanitaria."),
    ),
    "sin riesgo de…": dict(
        titulo="Afirmación de ausencia de un riesgo concreto",
        base_normativa=("Puede considerarse una seguridad de ausencia de riesgos, que el RD 1907/1996 (art. 4) no "
                        "permite en la publicidad con finalidad sanitaria."),
    ),
    "milagro": dict(
        titulo="Posible promesa de resultado",
        base_normativa=("Puede considerarse una promesa o garantía de resultado, que el RD 1907/1996 (art. 4) no "
                        "permite en la publicidad con finalidad sanitaria."),
    ),
}


def sustituir(texto: str, reglas) -> str:
    """Aplica sustituciones buscando en el texto plegado y cambiando el original."""
    for patron, repl in reglas:
        for _ in range(20):
            pl = plegar(texto)
            m = re.search(patron, pl)
            if not m:
                break
            nuevo = repl
            if "\\" in repl:
                # conservamos las palabras originales de los grupos (con tildes)
                for g in range(1, (m.lastindex or 0) + 1):
                    val = texto[m.start(g):m.end(g)] if m.start(g) != -1 else ""
                    nuevo = nuevo.replace(f"\\{g}", val)
            orig = texto[m.start():m.end()].lstrip()
            if nuevo and orig[:1].isupper():
                nuevo = nuevo[0].upper() + nuevo[1:]
            texto = texto[:m.start()] + nuevo + texto[m.end():]
    texto = re.sub(r"\s+([.,;:!?])", r"\1", texto)
    texto = re.sub(r"\s{2,}", " ", texto).strip()
    return texto


def corregir_promesa(frase: str) -> str:
    base = frase.strip("… ").strip()
    corregido = sustituir(base, SUSTITUCIONES_PROMESA)
    if _hay(PROMESA_RESIDUAL, plegar(corregido)):
        corregido = TEXTO_PROMESA_GENERICO
    if corregido and corregido[-1] not in ".!?":
        corregido += "."
    corregido = re.sub(r"!+", ".", corregido)
    corregido = re.sub(r"¡", "", corregido)
    if "varian" in plegar(corregido):
        return corregido
    return f"{corregido} {AVISO_RESULTADOS}".strip()


# Negación o contexto explicativo: "no garantizamos", "ningún médico le garantizará...",
# "no existe un tratamiento sin riesgo", "la medicina estética no hace milagros".
NEGACION = r"\b(no|ningun\w*|nunca|ni|sin\s+que|jamas|imposible|nadie)\b"
NEGACION_DETRAS = r"^\W{0,3}\s*(no|nunca)\s+(hacen?|existen?|hay|son|es)\b"
PREFIJO_NOMBRE = r"(\bdra?\.?|\bdoctora?|\bcalle|\bc/|\bavda?\.?|\bavenida|\bplaza|\bsanta|\bvirgen|\bnuestra\s+senora)\s+(de\s+(los?\s+|las?\s+)?)?$"


# Voz de un paciente (reseña pegada como texto normal): no es publicidad redactada por la clínica.
VOZ_PACIENTE = (r"\b(me\s+hice|me\s+hizo|me\s+hicieron|me\s+puse|ponerme|poniendome|lleve\s+a\s+mi|llevo\s+viniendo|"
                r"mi\s+experiencia|os\s+recomiendo|la\s+recomiendo|lo\s+recomiendo|recomiendo\s+(100|totalmente|la|el|a)|"
                r"empece\s+con|me\s+atend|me\s+trat(o|aron)|acudi|volvere|repetire|super\s*bien)\b")


def _negado(pl: str, ini: int, fin: int, ancho: int = 60) -> bool:
    """True si la coincidencia está negada en su misma frase (hasta ``ancho`` caracteres antes)."""
    antes = pl[max(0, ini - ancho):ini]
    corte = max(antes.rfind(c) for c in ".!?¡¿:;\n")
    if corte != -1:
        antes = antes[corte + 1:]
    # "no invasivo", "no espere más"... no niegan la promesa
    antes = re.sub(r"\bno\s+(invasiv|quirurgic|agresiv|esper|dud|lo\s+dud|te\s+lo\s+pierd)\w*", " ", antes)
    if _hay(NEGACION, antes):
        return True
    return _hay(NEGACION_DETRAS, pl[fin:fin + 20]) or _hay(r"\bno\s+hacen?\s+$", antes)


def _es_nombre_propio(texto: str, pl: str, ini: int, fin: int) -> bool:
    """"Milagros" como nombre de persona o calle: Dra. Milagros, calle de los Milagros, MILAGROS PÉREZ."""
    if pl[ini:fin] != "milagros" or not texto[ini:ini + 1].isupper():
        return False
    if re.search(PREFIJO_NOMBRE, pl[max(0, ini - 30):ini]):
        return True
    siguiente = re.match(r"\s+(\w+)", texto[fin:])
    if siguiente and siguiente.group(1)[:1].isupper():
        return True       # Milagros Pérez / MILAGROS PÉREZ
    inicio_frase = not texto[:ini].strip() or texto[:ini].rstrip()[-1:] in ".!?¡¿:\n"
    return texto[ini:fin] == "Milagros" and not inicio_frase   # "...en Milagros" a mitad de frase


def _es_promesa(pid, pl, texto, m, exige_ctx, excluir):
    ini, fin = m.start(), m.end()
    if pid == "milagro" and _es_nombre_propio(texto, pl, ini, fin):
        return False
    if pid == "milagro" and _hay(MILAGRO_NO_PROMESA, pl[max(0, ini - 25):fin + 5]):
        return False
    if pid == "sin dolor" and (re.search(MATIZ_DOLOR, pl[max(0, ini - 60):ini]) or
                               re.search(MATIZ_DOLOR_DETRAS, pl[fin:fin + 40]) or
                               _hay(DOLOR_SINTOMA, pl[max(0, ini - 20):fin + 40])):
        return False
    if pid == "resultados permanentes" and re.search(r"\bsin\s+(\w+\s+){0,2}$", pl[max(0, ini - 30):ini]):
        return False          # "sin obtener unos resultados permanentes"
    frase = _frase(pl, ini, fin)
    if _hay(VOZ_PACIENTE, frase) or _hay(NO_MEDICO, frase):
        return False          # reseña de un paciente o tratamiento que no es médico
    if _negado(pl, ini, fin):
        return False
    if pid == "garantía" and (re.search(GARANTIA_FINALIDAD, pl[max(0, ini - 25):ini]) or
                              re.search(GARANTIA_CONSEJO, pl[max(0, ini - 90):ini]) or
                              not _hay(GARANTIA_OBJETO, pl[fin:fin + 35])):
        return False
    if excluir and _hay(EXCLUSION_PROMESA, _ventana(pl, ini, fin, 40)):
        return False
    if exige_ctx and not _hay(CONTEXTO_RESULTADO, _ventana(pl, ini, fin, 60)):
        return False
    return True


def _ajustar_promesa(h: Hallazgo, pids: list):
    """Título, gravedad y norma según los tipos de promesa de la frase (manda el más grave)."""
    altas = [x for x in pids if x not in PROMESA_MEDIA]
    if altas:
        h.gravedad, h.base_normativa = ALTA, PROMESA_BASE["base_normativa"]
        titulo = PROMESA_BASE["titulo"]
    else:
        media = PROMESA_MEDIA[pids[0]]
        h.gravedad, h.base_normativa = MEDIA, media["base_normativa"]
        titulo = media["titulo"] if len({PROMESA_MEDIA[x]["titulo"] for x in pids}) == 1 else \
            "Afirmación absoluta o posible promesa de resultado"
    h.titulo = f"{titulo}: " + ", ".join(f"«{x}»" for x in pids)


def regla_promesas(p: Pagina, max_por_pagina: int = 8):
    if p.es_legal:
        return []
    vistos, out = {}, []
    for ubic, texto in _segmentos(p):
        pl = plegar(texto)
        ocupados = []
        for pid, patron, ctx, exc in PROMESAS:
            for m in re.finditer(patron, pl):
                if any(a <= m.start() < b for a, b in ocupados):
                    continue  # ya cubierto (aceptado o descartado) por un patrón más específico
                ocupados.append((m.start(), m.end()))
                if not _es_promesa(pid, pl, texto, m, ctx, exc):
                    continue
                if pid == "sin riesgo" and re.match(r"\s+de\s+\w", pl[m.end():]):
                    pid = "sin riesgo de…"          # "sin riesgo de rechazo": riesgo concreto, MEDIA
                ev, mi, mf = fragmento(texto, m.start(), m.end())
                if ev in vistos:
                    h, pids = vistos[ev]
                    h.apariciones += 1
                    if pid not in pids:
                        pids.append(pid)
                        _ajustar_promesa(h, pids)
                    continue
                h = Hallazgo(regla="promesas", url=p.url, ubicacion=ubic, evidencia=ev,
                             marca_inicio=mi, marca_fin=mf,
                             texto_corregido=corregir_promesa(ev), **PROMESA_BASE)
                vistos[ev] = (h, [pid])
                _ajustar_promesa(h, [pid])
                out.append(h)
    out.sort(key=lambda h: ORDEN_GRAVEDAD[h.gravedad])
    return out[:max_por_pagina]


# --------------------------------------------------------------------------
# ALTA 3 (sitio): nº de registro sanitario
# --------------------------------------------------------------------------

FRASE_REGISTRO = (
    r"registro\s+sanitario|n[o0º°]\.?\s*(de\s+)?registro(?!\s+mercantil)|numero\s+de\s+registro(?!\s+mercantil)|"
    r"autorizacion\s+sanitaria|centro\s+sanitario\s+autorizado|registro\s+de\s+centros|"
    r"inscripcion\s+en\s+el\s+registro(?!\s+mercantil)"
)
# Número "pegado" a la frase: como mucho 15 caracteres entre medias, sin teléfono ni dirección.
NUMERO_TRAS_FRASE = r"^(?P<hueco>[^\d\n]{0,15}?)(?P<num>\d[\d/.\-]{2,})"
HUECO_NO_VALIDO = r"\btel|\bmovil|\bfax|\bc/|\bcalle|\bavda|\bavenida|\bplaza|\bcp\b|\bwhatsapp"


def _numero_pegado(pl: str, fin: int) -> bool:
    m = re.match(NUMERO_TRAS_FRASE, pl[fin:fin + 40])
    if not m or _hay(HUECO_NO_VALIDO, m.group("hueco")):
        return False
    resto = pl[fin + m.end():fin + m.end() + 12]
    if re.fullmatch(r"\d{5}", m.group("num")) and re.match(r"\s*,?\s*(madrid|\()", resto):
        return False      # código postal: 28001 Madrid
    return True
# Consejo al paciente ("asegúrese de que la clínica cuente con autorización sanitaria").
CONSEJO_REGISTRO = r"que\s+la\s+clinica\s+(cuente|tenga|este)|asegur|comprueb|verific|fijate|debe\s+contar"
NUMERO_REGISTRO = r"(?<![a-z])(cs|nica)\s*[-:.º°n]*\s*\d{3,}"


def estado_registro(paginas):
    """'con_numero', 'sin_numero' (se menciona sin número) o 'ausente'."""
    mencion = None
    for p in paginas:
        for ubic, texto in _segmentos(p):
            pl = plegar(texto)
            if _hay(NUMERO_REGISTRO, pl):
                return "con_numero", None
            for m in re.finditer(FRASE_REGISTRO, pl):
                if _hay(CONSEJO_REGISTRO, pl[max(0, m.start() - 60):m.start()]):
                    continue      # "que la clínica cuente con la autorización sanitaria": consejo al lector
                if _numero_pegado(pl, m.end()):
                    return "con_numero", None
                if mencion is None:
                    mencion = (p.url, ubic, texto, m.start(), m.end())
    return ("sin_numero", mencion) if mencion else ("ausente", None)


CONDICION_REGISTRO = ("[Solo si el centro está inscrito en el Registro de centros sanitarios de la Comunidad de "
                      "Madrid — comprobar antes de publicar]")

REGISTRO_BASE = dict(
    norma="Decreto 51/2006 de la Comunidad de Madrid",
    base_normativa=("Decreto 51/2006 de la Comunidad de Madrid (autorización y registro de centros sanitarios), "
                    "en relación con el RD 1277/2003: la publicidad del centro debe incluir su número de registro sanitario."),
    accion="Añadir el número de registro sanitario en el pie de todas las páginas y en cada anuncio.",
    texto_corregido=(CONDICION_REGISTRO + "\n{razon_social} · Centro sanitario inscrito en el Registro de centros "
                     "sanitarios de la Comunidad de Madrid · Nº de registro sanitario: {numero_registro_sanitario}"),
    sin_verificar=("Artículo concreto del Decreto 51/2006 que exige el nº de registro en la publicidad: SIN VERIFICAR "
                   "(texto oficial no consultado)."),
)


def regla_registro(paginas, ausencias=True):
    if not paginas:
        return []
    estado, mencion = estado_registro(paginas)
    if estado == "con_numero" or (estado == "ausente" and not ausencias):
        return []
    if estado == "ausente" and not any(p.es_legal for p in paginas):
        # Sin aviso legal leído no se puede afirmar que falte: el número suele estar ahí.
        n = len(paginas)
        return [Hallazgo(regla="registro_sin_lectura", gravedad=BAJA,
                         titulo="No se ha leído el aviso legal: comprobar a mano si publica el nº de registro sanitario",
                         url=paginas[0].url, ubicacion="páginas revisadas (sin aviso legal)",
                         evidencia=(f"No se encontró el nº de registro en {n} página{'s' if n != 1 else ''}, pero ninguna "
                                    "era el aviso legal o la política de privacidad."),
                         marca_inicio=0, marca_fin=0, **REGISTRO_BASE)]
    if estado == "sin_numero":
        url, ubic, texto, i, f = mencion
        ev, mi, mf = fragmento(texto, i, f)
        return [Hallazgo(regla="registro", gravedad=MEDIA,
                         titulo="Se menciona el registro sanitario, pero no se ve el número",
                         url=url, ubicacion=ubic, evidencia=ev, marca_inicio=mi, marca_fin=mf, **REGISTRO_BASE)]
    n = len(paginas)
    return [Hallazgo(regla="registro", gravedad=ALTA,
                     titulo="No aparece el número de registro sanitario del centro",
                     url=paginas[0].url, ubicacion="todas las páginas revisadas",
                     evidencia=f"No se encontró «registro sanitario», «nº de registro», «CS» + número ni «autorización sanitaria» en {n} página{'s' if n != 1 else ''}.",
                     marca_inicio=0, marca_fin=0, **REGISTRO_BASE)]


# --------------------------------------------------------------------------
# MEDIA 1: promociones sobre tratamientos médicos
# --------------------------------------------------------------------------

PATRON_PROMO = (
    r"\bofertas?\b|\bdescuentos?\b|\d{1,2}\s*%\s*(de\s+)?(dto|descuento)|%\s*dto\b|\bdto\.?(?=\s|$)|"
    r"\b2\s*x\s*1\b|\b3\s*x\s*2\b|\bgratis\b|\bgratuit[oa]s?\b|\bbonos?\b|black\s*friday|cyber\s*monday|"
    r"\bpromocion(es)?\b|\bpromo\b|precio\s+especial|rebajas?\b|"
    r"\b(ahora|antes)\s*:?\s*\d[\d.,]*\s*(€|eur)"          # "Ahora: 385 € Antes: 505 €"
)
TRATAMIENTO_MEDICO = (
    r"tratamient(?!os?\s+de\s+(sus\s+|los\s+)?datos)|\bsesion(es)?\b|hialuronico|relleno|\blabios?\b|arrugas|toxina|botox|"
    r"mesoterapia|peeling|laser|hilos\s+tensores|rinomodelacion|bioestimul|\bplasma\b|\bprp\b|radiesse|"
    r"profhilo|lipolisis|carboxiterapia|depilacion|rejuvenecimiento|ojeras|papada|\bvial(es)?\b|"
    r"\d\s*zonas?\b|neuromodulador|medicina\s+estetica|inyecci|vitaminas"
)
EXCLUSION_PROMO = (r"envio|parking|aparcamiento|wifi|wi-fi|llamada|telefono|\blinea\b|\b[89]00[\s.]?\d{3}|newsletter|"
                   r"suscri|comunicaciones\s+comerciales|\bcafe\b|descarga|ebook|guia|se\s+reintegra")

# Catálogo, no promoción: "nuestra oferta de tratamientos", "la mejor oferta posible de tratamientos",
# "amplia oferta", "nuestra oferta incluye", "promoción de la salud", "5 promociones médicas" (cursos).
NO_PROMO = (r"ofertas?(\s+\w+){0,3}\s+de\s+(tratamientos|servicios|soluciones|especialidades)|"
            r"(nuestra|amplia|completa)\s+oferta\b|oferta\s+(incluye|asistencial|formativa)|"
            r"promocion\s+(y\s+prevencion\s+)?(de\s+la\s+|en\s+|de\s+)?salud|\d+\s+promociones\s+(medicas|de\s+)")
# La consulta, cita, valoración o diagnóstico gratuitos no son un descuento sobre un tratamiento.
CONSULTA_GRATIS = (r"\b(citas?|consultas?|valoracion(es)?|diagnosticos?|asesoramiento|asesoria|estudio|visitas?|"
                   r"revision(es)?|evaluacion|presupuestos?|dudas)\b[^.|\n]{0,40}\b(gratis|gratuit[oa]s?|sin\s+coste|"
                   r"sin\s+compromiso)\b|\b(gratis|gratuit[oa]s?)\b[^.|\n]{0,15}\b(cita|consulta|valoracion|diagnostic|"
                   r"asesor|estudio|visita)")
# Negación o consejo sobre ofertas: "incompatibles con ese tipo de ofertas", "evite dejarse llevar por ofertas".
NEGACION_PROMO = r"incompatib|desconfi|evit[ae]|cuidado\s+con|dejar(te|se)\s+llevar"
# Promoción de algo que no es un acto médico (estética sin medicamento ni aparato sanitario, psicología).
NO_MEDICO = (r"maderoterapia|masaje|drenaje|drenoredux|higiene\s+facial|limpieza\s+facial|hydra\s*(facial|glow)|"
             r"facial(es)?\s+corean|\bfhos\b|gym\s*face|presoterapia|psicolog|\bemdr\b|\britual|manicura|pedicura|"
             r"pestanas|cejas|peluqueria|ersus|sculpt|suelo\s+pelvico|dermo.?cosmetic|terapia\s+led|korean|aquapure|"
             r"cavitacion|peeling\s+ultrasonico")
# Promoción con contenido concreto: precio, porcentaje, "antes/ahora", 2x1, campaña o bono con precio.
PROMO_CONCRETA = (r"\d\s*(€|eur\b|euros)|€\s*\d|\d{1,2}\s*%|\bdto\b|descuento|\bantes\b[^.\n]{0,25}\d|"
                  r"\bahora\b[^.\n]{0,25}\d|2\s*x\s*1|3\s*x\s*2|precio\s+especial|black\s*friday|cyber\s*monday|"
                  r"precio\s+sin\s+(oferta|promocion)|rebajas")

PROMO_DESCUENTO = (r"\d{1,2}\s*%|\bdto\b|descuento|\bantes\b[^.\n]{0,25}\d|\bahora\b[^.\n]{0,25}\d|ahorr|"
                   r"\bgratis\b|regalo|precio\s+sin\s+(oferta|promocion)")

PROMO = dict(
    titulo="Promoción o descuento sobre un tratamiento médico",
    gravedad=MEDIA,
    norma="RD 1907/1996 y criterio de la Consejería de Sanidad; RDL 1/2015 si afecta a la toxina",
    base_normativa=("Publicidad sanitaria (RD 1907/1996 y criterios de la Consejería de Sanidad): las promociones sobre "
                    "actos médicos pueden considerarse un incentivo al consumo. Si afectan a un medicamento con "
                    "receta (toxina), es infracción del RDL 1/2015."),
    accion=("Quitar descuentos, porcentajes, 2x1, bonos, regalos y campañas (Black Friday, etc.) de los tratamientos "
            "médicos. Si publica precios, que sean informativos y sin plazos limitados."),
    texto_corregido=("Primera consulta de valoración médica: el médico estudia su caso y le indica el tratamiento "
                     "adecuado y su precio antes de empezar."),
)
PROMO_REVISAR = dict(
    PROMO,
    titulo="Apartado o mención de promociones sin precio ni descuento visible: revisar a mano",
    gravedad=BAJA,
    sin_verificar=("Solo se ha leído la palabra (menú, botón o título), no la promoción concreta: comprobar en la "
                   "web qué tratamiento y qué descuento anuncia antes de mencionarlo."),
)


def regla_promociones(p: Pagina):
    if p.es_legal:
        return []
    concretas, genericas = [], []
    for ubic, texto in _segmentos(p):
        pl = plegar(texto)
        for m in re.finditer(PATRON_PROMO, pl):
            a, b = m.start(), m.end()
            if re.match(NO_PROMO, pl[a:b + 40]) or _hay(NO_PROMO, pl[max(0, a - 20):b + 40]):
                continue
            if _hay(r"gratis|gratuit", pl[a:b]) and _hay(CONSULTA_GRATIS, _ventana(pl, a, b, 45)):
                continue
            if _negado(pl, a, b, 40) or _hay(NEGACION_PROMO, pl[max(0, a - 50):a]):
                continue            # "no participamos en promociones"
            if _hay(VOZ_PACIENTE, _ventana(pl, a, b, 80)):
                continue            # "empecé con la oferta de groupon": lo cuenta un paciente
            if _hay(EXCLUSION_PROMO, _frase(pl, a, b)) or _hay(NO_MEDICO, _ventana(pl, a, b, 80)):
                continue
            if not _hay(TRATAMIENTO_MEDICO, _ventana(pl, a, b, 100)):
                continue
            c = (ubic, texto, a, b)
            frase = _frase(pl, a, b)
            if "?" in frase or "¿" in frase:
                genericas.append(c)           # título-pregunta de un artículo: "Descuento del bótox ¿es posible?"
                continue
            if re.fullmatch(r"bonos?", pl[a:b]) and not _hay(PROMO_DESCUENTO, _ventana(pl, a, b, 60)):
                genericas.append(c)           # un bono con su precio es una tarifa, no un descuento
                continue
            if _hay(PROMO_CONCRETA, frase):
                concretas.append((2,) + c)
            elif _hay(PROMO_CONCRETA, pl[b:b + 40]):          # precio en la línea siguiente: Promoción / 280 € / Neuromoduladores
                concretas.append((1,) + c)
            else:
                genericas.append(c)
    if concretas:
        # Evidencia: la más concreta (precio en la misma frase), del texto propio de la página, el menú al final.
        concretas.sort(key=lambda c: (-c[0], c[1] != "texto de la página", c[3]))
        concretas = [c[1:] for c in concretas]
        return [_hallazgo_de_coincidencias("promociones", concretas + genericas, p.url, **PROMO)]
    if genericas:
        return [_hallazgo_de_coincidencias("promociones_revisar", genericas, p.url, **PROMO_REVISAR)]
    return []


# --------------------------------------------------------------------------
# MEDIA 2: imágenes de antes y después
# --------------------------------------------------------------------------

PATRON_ANTES_DESPUES = r"antes\s*(y|e|/|-|&|\+)?\s*despues|before\s*(and|&|/|-|\+)?\s*after"
CONTEXTO_FOTO = r"foto|imagen|imagenes|galeria|resultad|casos?\s+real|ver\s+m"
# Consejos de cuidados: "cuidados antes y después del tratamiento" no es una galería.
CUIDADOS_ANTES_DESPUES = r"(cuidados|instrucciones|recomendaciones|consejos|indicaciones)\s+(\w+\s+){0,2}$"
ENLACE_GALERIA = r"galeria|casos|resultados"
# Prosa que habla de las fotos de antes/después en general o en futuro: no es una galería publicada.
PROSA_ANTES_DESPUES = r"\b(pondre|pondremos|subire|subiremos|publicaremos)\b|muchas\s+personas|en\s+redes\s+sociales|\bconocen\b"

ANTES_DESPUES = dict(
    titulo="Imágenes de «antes y después» de pacientes",
    gravedad=MEDIA,
    base_normativa=("RGPD y criterio de la AEPD: la imagen de un paciente es un dato de salud; publicarla exige su "
                    "consentimiento expreso y específico para ese uso. Además, puede inducir a pensar que el resultado "
                    "está garantizado (RD 1907/1996)."),
    accion=("Retirar las fotos salvo que tenga el consentimiento expreso y por escrito de cada paciente para uso "
            "publicitario, y guardarlo. Si lo tiene, acompañe cada imagen del texto corregido."),
    norma="RGPD (consentimiento del paciente) y RD 1907/1996",
    texto_corregido=("[Solo si es cierto] Imágenes publicadas con el consentimiento expreso y por escrito del "
                     "paciente. Los resultados varían en cada persona y no se garantizan."),
    sin_verificar=("La exigencia de consentimiento es cierta (RGPD); que la Consejería prohíba en sí las fotos de "
                   "antes/después en Madrid está SIN VERIFICAR."),
)


def regla_antes_despues(p: Pagina):
    coinc = []
    # 1) imágenes (src/alt/title)
    for src, alt, tit in p.imagenes:
        for campo, ubic in ((alt, "texto alternativo de imágenes"), (tit, "título de imagen"),
                            (_ruta_legible(src), "nombre del archivo de imagen")):
            pl = plegar(campo)
            m = re.search(PATRON_ANTES_DESPUES, pl)
            if m:
                coinc.append((ubic, campo, m.start(), m.end()))
                break
    # 2) enlaces a una galería de antes/después
    for href, txt in p.enlaces:
        pl = plegar(_ruta_legible(href))
        m = re.search(PATRON_ANTES_DESPUES, pl)
        if m and _hay(ENLACE_GALERIA, pl + " " + plegar(txt)):
            coinc.append(("enlace a galería", _ruta_legible(href), m.start(), m.end()))
    # 3) texto: solo con contexto de foto/galería o como encabezado corto
    for ubic, texto in _segmentos(p, con_url=True):
        if ubic == "texto alternativo de imágenes":
            continue
        pl = plegar(texto)
        for m in re.finditer(PATRON_ANTES_DESPUES, pl):
            if re.search(CUIDADOS_ANTES_DESPUES, pl[max(0, m.start() - 40):m.start()]) and \
                    re.match(r"\s*(del|de\s+la|de\s+los|de\s+las)\b", pl[m.end():]):
                continue
            a = pl.rfind("\n", 0, m.start()) + 1
            b = pl.find("\n", m.end())
            linea = pl[a: len(pl) if b == -1 else b]
            if _hay(PROSA_ANTES_DESPUES, linea):
                continue
            if not _hay(r"foto|imagen|galeria|caso", linea) and (
                    _hay(r"precaucion|cuidado|recomendacion|\bdebo\b|que\s+hacer|que\s+esperar|\?", linea) or
                    re.match(r"\s*(del?|de\s+la)\s+(tratamiento|procedimiento|sesion|intervencion)", pl[m.end():])):
                continue
            titular = len(linea) <= 40 and not re.search(r"\b(del|de la|de los)\s*$", pl[m.end():m.end() + 8] + " ")
            if titular or _hay(CONTEXTO_FOTO, _ventana(pl, m.start(), m.end(), 60)):
                coinc.append((ubic, texto, m.start(), m.end()))
    if not coinc:
        return []
    prioridad = ["texto de la página", "título de la página", "texto alternativo de imágenes"]
    coinc.sort(key=lambda c: prioridad.index(c[0]) if c[0] in prioridad else len(prioridad))
    return [_hallazgo_de_coincidencias("antes_despues", coinc, p.url, **ANTES_DESPUES)]


# --------------------------------------------------------------------------
# MEDIA 3: testimonios de pacientes
# --------------------------------------------------------------------------

_QUIEN = r"(nuestr[oa]s\s+)?(pacientes|clientes|clientas)"
PATRON_TESTIMONIOS = (
    r"\btestimonios?\b|\btestimoniales?\b|opiniones\s+de\s+" + _QUIEN + r"|lo\s+que\s+dicen\s+" + _QUIEN +
    r"|experiencias?\s+de\s+" + _QUIEN + r"|valoraciones\s+de\s+" + _QUIEN + r"|\bresenas\b|\breviews?\b"
)

# Texto que explica que la ley los prohíbe: no es un testimonio.
EXPLICA_TESTIMONIOS = r"prohib|no\s+(publicamos|mostramos|incluimos|usamos|utilizamos)|no\s+se\s+permite"
# Consejo al lector ("revisa referencias, opiniones de pacientes..."): no es un testimonio publicado.
CONSEJO_TESTIMONIOS = r"\b(revisa|revise|consulta|consulte|lee|lea|busca|busque|mira|mire|compara|compare)\b"

TESTIMONIOS = dict(
    titulo="Testimonios u opiniones de pacientes en la publicidad",
    gravedad=MEDIA,
    norma="RD 1907/1996, art. 4",
    base_normativa=("RD 1907/1996, art. 4: prohíbe usar testimonios de pacientes, reales o supuestos, como medio de "
                    "inducción al consumo en publicidad con finalidad sanitaria."),
    accion=("Retirar de las páginas de tratamientos los testimonios, opiniones y reseñas de pacientes (también los "
            "widgets de reseñas incrustados)."),
    texto_corregido=("¿Quiere saber si este tratamiento es adecuado para usted? Pida una consulta de valoración y "
                     "el médico le explicará sus opciones, beneficios y riesgos."),
    sin_verificar=SV_ART4,
)


def regla_testimonios(p: Pagina):
    if p.es_legal:
        return []
    coinc = []
    for ubic, texto in _segmentos(p):
        pl = plegar(texto)
        for m in re.finditer(PATRON_TESTIMONIOS, pl):
            if _hay(EXPLICA_TESTIMONIOS, _ventana(pl, m.start(), m.end(), 60)):
                continue
            if _hay(CONSEJO_TESTIMONIOS, pl[max(0, m.start() - 40):m.start()]):
                continue
            coinc.append((ubic, texto, m.start(), m.end()))
    # Bloque de reseñas o testimonios con texto visible (una clase CSS sola no basta: puede ser
    # solo una hoja de estilos o un contenedor vacío).
    resenas = p.resenas.strip()
    if len(resenas) >= 20:
        pl = plegar(resenas)
        m = re.search(PATRON_TESTIMONIOS, pl)
        if m:
            coinc.append(("bloque de reseñas o testimonios", resenas, m.start(), m.end()))
        else:
            linea = resenas.split("\n")[0]
            coinc.append(("bloque de reseñas o testimonios", resenas, 0, min(len(linea), 120)))
    return [_hallazgo_de_coincidencias("testimonios", coinc, p.url, **TESTIMONIOS)] if coinc else []


# --------------------------------------------------------------------------
# BAJA (sitio): páginas legales y médico responsable
# --------------------------------------------------------------------------

# Se buscan en enlaces (texto y href), títulos y URL de las páginas descargadas,
# y en el texto solo con la frase completa (para no contar "garantizamos su privacidad").
BORRADOR = "[Borrador mínimo: completar y validar con su asesor]"
NORMAS_LEGALES = {"aviso_legal": "LSSI (Ley 34/2002), art. 10", "privacidad": "RGPD, art. 13",
                  "cookies": "LSSI, art. 22.2 (autoridad: AEPD)"}

LEGALES = [
    ("aviso_legal", "Falta el aviso legal",
     r"aviso[\s\-_]*legal|legal[\s\-_]*notice|nota[\s\-_]*legal|informacion[\s\-_]*legal",
     r"aviso\s+legal",
     "LSSI (Ley 34/2002), art. 10: la web debe identificar al titular (nombre, NIF, domicilio, contacto, registro).",
     ("Aviso legal. Titular: {razon_social}. NIF: {nif}. Domicilio: {domicilio}. Correo: {email}. Teléfono: {telefono}. "
      "Inscrita en {registro_mercantil}. " + CONDICION_REGISTRO + " Centro sanitario inscrito en el Registro de "
      "centros sanitarios de la Comunidad de Madrid, nº de registro sanitario {numero_registro_sanitario}. "
      "Director/a médico/a: {nombre_medico}, nº de colegiado {numero_colegiado} del {colegio}.")),
    ("privacidad", "Falta la política de privacidad",
     r"privacidad|privacy|proteccion[\s\-_]*de[\s\-_]*datos|\brgpd\b|\bgdpr\b",
     r"politica\s+de\s+privacidad|proteccion\s+de\s+datos",
     "RGPD, art. 13: hay que informar de quién trata los datos, para qué, con qué base y cómo ejercer los derechos.",
     (BORRADOR + "\nPolítica de privacidad. Responsable: {razon_social} ({nif}), {domicilio}, {email}. Tratamos sus "
      "datos para gestionar sus citas y su historia clínica, con base en la prestación de asistencia sanitaria y, "
      "para las comunicaciones, en su consentimiento. Conservamos los datos durante {plazos_conservacion}. "
      "Destinatarios: {destinatarios}. Puede ejercer sus derechos de acceso, rectificación, supresión, "
      "oposición, limitación y portabilidad en {email} y reclamar ante la AEPD (www.aepd.es).")),
    ("cookies", "Falta la política de cookies",
     r"cookies?",
     r"politica\s+de\s+cookies|uso\s+de\s+cookies|utiliza(mos)?\s+cookies",
     ("LSSI, art. 22.2: si la web usa cookies no técnicas, debe informar y pedir consentimiento. En cookies, el "
      "organismo competente es la Agencia Española de Protección de Datos (AEPD), no la Consejería de Sanidad."),
     (BORRADOR + "\nPolítica de cookies. Cookies que usa esta web: {lista_de_cookies} (para cada una: nombre, "
      "titular, finalidad y duración). {cookies_no_tecnicas_y_como_se_aceptan} Puede cambiar su elección en "
      "cualquier momento desde {enlace_configuracion_cookies}.")),
]


def reglas_legales(paginas):
    if not paginas:
        return []
    out = []
    for rid, titulo, patron_enlace, patron_texto, base, texto in LEGALES:
        encontrado = False
        for p in paginas:
            campos = [plegar(_ruta_legible(p.url)), plegar(p.titulo)]
            campos += [plegar(t + " " + _ruta_legible(h)) for h, t in p.enlaces]
            if any(_hay(patron_enlace, c) for c in campos) or _hay(patron_texto, plegar(p.texto)):
                encontrado = True
                break
        if not encontrado:
            n = len(paginas)
            out.append(Hallazgo(
                regla=rid, gravedad=BAJA, titulo=titulo, url=paginas[0].url,
                ubicacion="enlaces y textos de las páginas revisadas",
                evidencia=f"No se encontró enlace ni texto de esta página legal en {n} página{'s' if n != 1 else ''}.",
                marca_inicio=0, marca_fin=0, base_normativa=base, norma=NORMAS_LEGALES[rid],
                accion="Publicar la página y enlazarla desde el pie de todas las páginas.",
                texto_corregido=texto,
                sin_verificar=("El aviso de cookies suele cargarse con JavaScript y esta revisión no lo ejecuta: "
                               "comprobarlo a mano.") if rid == "cookies" else ""))
    return out


PATRON_COLEGIADO = (
    r"(n[o0º°]\.?|num\.?|numero)\s*(de\s+)?colegiad[oa]|colegiad[oa]\s*(n[o0º°]\.?|num\.?|numero)?\s*:?\s*\d{3,}|"
    r"\bcol\.\s*(n[o0º°]\.?)?\s*:?\s*\d{3,}"
)
PATRON_RESPONSABLE = (
    r"direct(or|ora)\s+medic[oa]|direccion\s+medica|medic[oa]\s+responsable|responsable\s+medic[oa]|"
    r"direct(or|ora)\s+asistencial"
)


def regla_medico(paginas):
    if not paginas:
        return []
    todo = "\n".join(plegar(p.texto) for p in paginas)
    colegiado = _hay(PATRON_COLEGIADO, todo)
    responsable = _hay(PATRON_RESPONSABLE, todo)
    if colegiado:
        return []
    falta = "el médico responsable ni su nº de colegiado" if not responsable else "el nº de colegiado del médico responsable"
    return [Hallazgo(
        regla="medico", gravedad=BAJA, titulo="No se identifica " + falta,
        url=paginas[0].url, ubicacion="todas las páginas revisadas",
        evidencia=f"No se encontró {falta} en las páginas revisadas.",
        marca_inicio=0, marca_fin=0,
        base_normativa=("Buena práctica y códigos deontológicos médicos; la LSSI (art. 10) pide los datos colegiales "
                        "cuando se ejerce una profesión regulada."),
        accion="Identificar al director/a médico/a con su nº de colegiado en la página del equipo y en el aviso legal.",
        norma="Buena práctica; LSSI art. 10 (datos colegiales)",
        texto_corregido="Dirección médica: {nombre_medico}, colegiado/a nº {numero_colegiado} del {colegio}.",
        sin_verificar=("Requisito SIN VERIFICAR: no hemos confirmado una norma que exija con carácter general el nº de "
                       "colegiado en la publicidad del centro."))]


# --------------------------------------------------------------------------
# Prospección (uso interno, NO va al informe de la clínica): posible cadena
# --------------------------------------------------------------------------
# Traído del risk-scanner antiguo (checks/chain_detector.py, caso Face Clinic): Arcend es solo
# para clínicas independientes. Se quitaron sus señales demasiado genéricas ("clínicas en",
# "centros en", "únete a"), que salen en el SEO de cualquier clínica de una sede.

LENGUAJE_CADENA = (
    r"\bnuestr[oa]s\s+(clinicas|centros|sedes)\b|\btodas\s+nuestras\s+clinicas\b|"
    r"\b(elige|selecciona|escoge)\s+tu\s+(clinica|centro|sede)\b|\bfranquicias?\b"
)
CIUDADES_FUERA = [
    "barcelona", "valencia", "sevilla", "malaga", "marbella", "bilbao", "zaragoza", "murcia", "alicante",
    "palma", "valladolid", "granada", "coruna", "vigo", "gijon", "oviedo", "pamplona", "san sebastian",
    "santander", "cordoba", "badajoz", "ibiza", "tenerife", "las palmas", "lisboa", "miami",
]


def senales_cadena(paginas) -> list[str]:
    """Señales de que la clínica es una cadena o tiene varias sedes (para verificar a mano).

    Una sola señal no descarta la clínica: solo pide mirarlo antes de llamar.
    """
    senales = []
    lenguaje, registros, ciudades = [], set(), set()
    for p in paginas:
        for _, texto in _segmentos(p):
            pl = plegar(texto)
            for m in re.finditer(LENGUAJE_CADENA, pl):
                if m.group(0) not in lenguaje:
                    lenguaje.append(m.group(0))
            for m in re.finditer(NUMERO_REGISTRO, pl):
                registros.add(re.sub(r"\D", "", m.group(0)))
            for c in CIUDADES_FUERA:
                if re.search(r"\b" + c + r"\b", pl):
                    ciudades.add(c)
    if lenguaje:
        senales.append("lenguaje de varias sedes: " + ", ".join(f"«{x}»" for x in lenguaje[:3]))
    if len(registros) >= 2:
        senales.append(f"{len(registros)} números de registro sanitario distintos")
    if ciudades and senales:   # sola no vale: el CV del médico nombra ciudades ("formado en Barcelona")
        senales.append("menciona otras ciudades: " + ", ".join(sorted(ciudades)[:4]))
    return senales


# --------------------------------------------------------------------------
# Motor y puntuación
# --------------------------------------------------------------------------

REGLAS_POR_PAGINA = [regla_toxina, regla_promesas, regla_promociones, regla_antes_despues, regla_testimonios]
REGLAS_DE_SITIO = [regla_registro, reglas_legales, regla_medico]
ORDEN_GRAVEDAD = {ALTA: 0, MEDIA: 1, BAJA: 2}


def analizar(paginas, ausencias=True):
    """paginas: lista de Pagina. Devuelve los hallazgos ordenados por gravedad.

    Con ``ausencias=False`` (web que no se ha podido leer bien) no se emiten las reglas que
    afirman que algo FALTA (registro ausente, páginas legales, médico): no sería fiable.
    """
    hallazgos = []
    for p in paginas:
        for regla in REGLAS_POR_PAGINA:
            hallazgos.extend(regla(p))
    if ausencias:
        for regla in REGLAS_DE_SITIO:
            hallazgos.extend(regla(paginas))
    else:
        hallazgos.extend(regla_registro(paginas, ausencias=False))
    hallazgos.sort(key=lambda h: ORDEN_GRAVEDAD[h.gravedad])
    return hallazgos


# Web no legible: poco texto (se carga con JavaScript) o una sola página.
MIN_CARACTERES = 300
MIN_PAGINAS = 2
AVISO_NO_LEGIBLE = ("No se ha podido leer el contenido (probablemente se carga con JavaScript); revisión no fiable. "
                    "Guarde las páginas desde el navegador (Ctrl+S) y use --html-local CARPETA.")
AVISO_UNA_PAGINA = ("Solo se ha podido leer {n} página; revisión no fiable para afirmar que falta algo en la web. "
                    "Guarde más páginas desde el navegador (Ctrl+S) y use --html-local CARPETA.")


def evaluar_lectura(paginas):
    """Devuelve (fiable, aviso). No fiable si hay poco texto o menos de 2 páginas."""
    total = sum(len(p.texto) for p in paginas)
    if total < MIN_CARACTERES:
        return False, AVISO_NO_LEGIBLE
    if len(paginas) < MIN_PAGINAS:
        return False, AVISO_UNA_PAGINA.format(n=len(paginas))
    return True, ""


def _clave_evidencia(h) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", plegar(h.evidencia)).split())


def n_puntos_norma(hallazgos) -> int:
    """Puntos con norma concreta: reglas distintas con algún hallazgo ALTA/MEDIA sin SIN VERIFICAR.

    Un punto = un tipo de infracción (p. ej. "publicidad de la toxina"), aunque aparezca en muchas
    páginas o con frases distintas: así la cifra que se dice al médico no se infla con el menú o con
    la misma mención repetida (revisión manual del lote real, 29-09-2026). El detalle de páginas y
    frases está en el informe.
    """
    return len({h.regla for h in hallazgos if h.gravedad in (ALTA, MEDIA) and not h.sin_verificar})


def n_puntos_revisar(hallazgos) -> int:
    """Puntos a revisar: reglas distintas con algún ALTA/MEDIA, INCLUIDAS las SIN VERIFICAR.

    Siempre es >= n_puntos_norma. Sirve para el gancho de la llamada cuando no hay puntos con
    norma concreta ("conviene revisar", nunca "no permite").
    """
    return len({h.regla for h in hallazgos if h.gravedad in (ALTA, MEDIA)})


def frase_llamada(n_norma: int, n_revisar: int, lectura_fiable: bool = True) -> str:
    """Frase para abrir la llamada, calculada por la herramienta (nunca a mano).

    - con puntos con norma concreta: "... no permite";
    - si solo hay puntos a revisar (incluye SIN VERIFICAR): "... conviene revisar";
    - sin puntos o con lectura no fiable: "" (no hay gancho honesto).
    """
    if not lectura_fiable:
        return ""
    inicio = "He revisado la publicidad de su web y hay"
    if n_norma > 0:
        que = "punto que la normativa de publicidad sanitaria no permite" if n_norma == 1 else \
            "puntos que la normativa de publicidad sanitaria no permite"
        return f"{inicio} {n_norma} {que}."
    if n_revisar > 0:
        que = "punto que conviene revisar" if n_revisar == 1 else "puntos que conviene revisar"
        return f"{inicio} {n_revisar} {que} según la normativa de publicidad sanitaria."
    return ""


# Resta por hallazgo: el primero de cada regla resta el peso completo, cada uno
# de más +25 %, con tope de 2 veces el peso por regla (para que una web con el
# mismo fallo en 20 páginas no quede peor que una con fallos de todo tipo).
PESOS = {ALTA: 25, MEDIA: 10, BAJA: 4}
NOTAS = [(90, "A"), (75, "B"), (55, "C"), (35, "D"), (0, "E")]


def puntuar(hallazgos):
    """Devuelve (puntuación 0-100, nota A-E). Con algún ALTA, la nota es C como mucho."""
    por_regla = {}
    for h in hallazgos:
        por_regla.setdefault((h.regla, h.gravedad), 0)
        por_regla[(h.regla, h.gravedad)] += 1
    resta = 0.0
    for (_, grav), n in por_regla.items():
        base = PESOS[grav]
        resta += min(base * (1 + 0.25 * (n - 1)), 2 * base)
    puntos = max(0, min(100, round(100 - resta)))
    nota = next(letra for minimo, letra in NOTAS if puntos >= minimo)
    if any(h.gravedad == ALTA for h in hallazgos) and nota in ("A", "B"):
        nota = "C"
    return puntos, nota
