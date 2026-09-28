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
  indirectas: "neuromoduladores", siglas, hashtags). ALTA.
- Promesas: RD 1907/1996, art. 4 (garantías de resultado, "sin riesgo",
  ausencia de efectos secundarios...). El apartado exacto de cada supuesto está
  SIN VERIFICAR (boe.es bloqueado al investigar). ALTA.
- Nº de registro sanitario: Decreto 51/2006 de la Comunidad de Madrid. ALTA.
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
- "Dra. Milagros" / "Calle Milagros": nombre propio, no "milagro".
- "eliminar toxinas" (plural, detox) no es toxina botulínica.
- "antes y después del tratamiento evite el sol": sin contexto de foto no es
  una galería de antes/después.
- "parking gratuito", "envío gratis": promociones sin tratamiento cerca.
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
        if tag in _BLOQUES:
            self.partes.append("\n")

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
            self.partes.append("\n")

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
        self.partes.append(data)
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
    lineas = [" ".join(l.split()) for l in "".join(ex.partes).split("\n")]
    texto = "\n".join(l for l in lineas if l)
    return Pagina(
        url=url,
        titulo=" ".join("".join(ex.titulo).split()),
        descripcion=" ".join(ex.descripcion.split()),
        texto=texto,
        enlaces=ex.enlaces,
        imagenes=ex.imagenes,
        atributos=ex.atributos,
    )


def _ruta_legible(url: str) -> str:
    p = urlparse(url)
    ruta = unquote(p.path) + ((" " + unquote(p.query)) if p.query else "")
    return re.sub(r"[-_/.=&+]+", " ", ruta).strip()


def _segmentos(p: Pagina, con_url: bool = False):
    segs = [("texto de la página", p.texto), ("título de la página", p.titulo),
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
    base_normativa=("RD 1416/1994 de publicidad de medicamentos y RDL 1/2015 (Ley de garantías y uso "
                    "racional de los medicamentos): está prohibida la publicidad dirigida al público de "
                    "medicamentos que necesitan receta, como la toxina botulínica, también por alusiones "
                    "indirectas (\"neuromoduladores\", siglas, hashtags) y por ofertas ligadas a ellos."),
    accion=("Retirar de la web el nombre del medicamento y sus marcas, sus siglas, los hashtags, los precios "
            "por zona y cualquier promoción ligada a él. Puede hablarse de la consulta médica, no del medicamento."),
    texto_corregido=("Arrugas de expresión: en una consulta de valoración, el médico estudia su caso y le "
                     "explica las opciones indicadas para usted, con sus beneficios y riesgos."),
)


def regla_toxina(p: Pagina):
    coinc = []
    for ubic, texto in _segmentos(p, con_url=True):
        pl = plegar(texto)
        for patron in PATRONES_TOXINA:
            for m in re.finditer(patron, pl):
                coinc.append((ubic, texto, m.start(), m.end()))
    if not coinc:
        return []
    coinc.sort(key=lambda c: (c[0] != "texto de la página", c[2]))
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
# Matizadores que convierten "sin dolor" en una afirmación no absoluta.
MATIZ_DOLOR = r"(casi|practicamente|apenas|minim\w*|poco|mas o menos|relativamente)\s*(\w+\s+){0,2}$"

PROMESAS = [
    # (id, patrón, exige_contexto, aplica_exclusion)
    ("resultados garantizados", r"resultados?\s+(100\s*%\s*)?garantizad[oa]s?|garantia\s+de\s+(los\s+)?resultados?", False, False),
    ("garantía", r"\bgarantiz\w*|\bgarantias?\b", True, True),
    ("sin riesgo", r"\bsin\s+(ningun\s+)?riesgos?\b", True, True),
    ("sin efectos secundarios", r"\bsin\s+(ningun\s+|ningunos\s+)?efectos?\s+(secundarios?|adversos?)", False, False),
    ("100 % seguro", r"\b100\s*%\s*segur[oa]s?\b|\bcien\s+por\s+cien\s+segur[oa]s?\b", True, True),
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

PROMESA_BASE = dict(
    titulo="Promesa sanitaria prohibida",
    gravedad=ALTA,
    base_normativa=("RD 1907/1996 (publicidad con pretendida finalidad sanitaria), art. 4: prohíbe la publicidad "
                    "que ofrezca garantías de resultado o seguridades de ausencia de riesgos o efectos secundarios."),
    accion="Sustituir la frase por el texto corregido.",
)


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


def _es_promesa(pid, pl, texto, m, exige_ctx, excluir):
    ini, fin = m.start(), m.end()
    if pid == "milagro" and texto[ini:fin] == "Milagros":
        return False  # nombre propio: Dra. Milagros, calle Milagros
    if pid == "sin dolor" and re.search(MATIZ_DOLOR, pl[max(0, ini - 30):ini]):
        return False
    if excluir and _hay(EXCLUSION_PROMESA, _ventana(pl, ini, fin, 40)):
        return False
    if exige_ctx and not _hay(CONTEXTO_RESULTADO, _ventana(pl, ini, fin, 60)):
        return False
    return True


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
                    continue  # ya cubierto por un patrón más específico
                if not _es_promesa(pid, pl, texto, m, ctx, exc):
                    continue
                ocupados.append((m.start(), m.end()))
                ev, mi, mf = fragmento(texto, m.start(), m.end())
                if ev in vistos:
                    h = vistos[ev]
                    h.apariciones += 1
                    if f"«{pid}»" not in h.titulo:
                        h.titulo += f", «{pid}»"
                    continue
                h = Hallazgo(regla="promesas", url=p.url, ubicacion=ubic, evidencia=ev,
                             marca_inicio=mi, marca_fin=mf,
                             texto_corregido=corregir_promesa(ev), **PROMESA_BASE)
                h.titulo = f"Promesa sanitaria prohibida: «{pid}»"
                vistos[ev] = h
                out.append(h)
    return out[:max_por_pagina]


# --------------------------------------------------------------------------
# ALTA 3 (sitio): nº de registro sanitario
# --------------------------------------------------------------------------

FRASE_REGISTRO = (
    r"registro\s+sanitario|n[o0º°]\.?\s*(de\s+)?registro(?!\s+mercantil)|numero\s+de\s+registro(?!\s+mercantil)|"
    r"autorizacion\s+sanitaria|centro\s+sanitario\s+autorizado|registro\s+de\s+centros"
)
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
                if re.search(r"\d{3,}", pl[m.end():m.end() + 60]):
                    return "con_numero", None
                if mencion is None:
                    mencion = (p.url, ubic, texto, m.start(), m.end())
    return ("sin_numero", mencion) if mencion else ("ausente", None)


REGISTRO_BASE = dict(
    base_normativa=("Decreto 51/2006 de la Comunidad de Madrid (autorización y registro de centros sanitarios), "
                    "en relación con el RD 1277/2003: la publicidad del centro debe incluir su número de registro sanitario."),
    accion="Añadir el número de registro sanitario en el pie de todas las páginas y en cada anuncio.",
    texto_corregido=("{razon_social} · Centro sanitario autorizado por la Comunidad de Madrid · "
                     "Nº de registro sanitario: {numero_registro_sanitario}"),
)


def regla_registro(paginas):
    if not paginas:
        return []
    estado, mencion = estado_registro(paginas)
    if estado == "con_numero":
        return []
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
    r"\bpromocion(es)?\b|\bpromo\b|precio\s+especial|rebajas?\b"
)
TRATAMIENTO_MEDICO = (
    r"tratamient(?!os?\s+de\s+(sus\s+|los\s+)?datos)|\bsesion(es)?\b|hialuronico|relleno|\blabios?\b|arrugas|toxina|botox|"
    r"mesoterapia|peeling|laser|hilos\s+tensores|rinomodelacion|bioestimul|\bplasma\b|\bprp\b|radiesse|"
    r"profhilo|lipolisis|carboxiterapia|depilacion|rejuvenecimiento|ojeras|papada|\bvial(es)?\b|"
    r"\d\s*zonas?\b|neuromodulador|medicina\s+estetica|inyecci|vitaminas"
)
EXCLUSION_PROMO = r"envio|parking|aparcamiento|wifi|wi-fi|llamada|telefono|newsletter|suscri|\bcafe\b|descarga|ebook|guia"

PROMO = dict(
    titulo="Promoción o descuento sobre un tratamiento médico",
    gravedad=MEDIA,
    base_normativa=("Publicidad sanitaria (RD 1907/1996 y criterios de la Consejería de Sanidad): las promociones sobre "
                    "actos médicos pueden considerarse un incentivo al consumo. Si afectan a un medicamento con "
                    "receta (toxina), es infracción del RDL 1/2015."),
    accion=("Quitar descuentos, porcentajes, 2x1, bonos, regalos y campañas (Black Friday, etc.) de los tratamientos "
            "médicos. Si publica precios, que sean informativos y sin plazos limitados."),
    texto_corregido=("Primera consulta de valoración médica: el médico estudia su caso y le indica el tratamiento "
                     "adecuado y su precio antes de empezar."),
)


def regla_promociones(p: Pagina):
    if p.es_legal:
        return []
    coinc = []
    for ubic, texto in _segmentos(p):
        pl = plegar(texto)
        for m in re.finditer(PATRON_PROMO, pl):
            if _hay(EXCLUSION_PROMO, _ventana(pl, m.start(), m.end(), 40)):
                continue
            if _hay(TRATAMIENTO_MEDICO, _ventana(pl, m.start(), m.end(), 100)):
                coinc.append((ubic, texto, m.start(), m.end()))
    return [_hallazgo_de_coincidencias("promociones", coinc, p.url, **PROMO)] if coinc else []


# --------------------------------------------------------------------------
# MEDIA 2: imágenes de antes y después
# --------------------------------------------------------------------------

PATRON_ANTES_DESPUES = r"antes\s*(y|e|/|-|&|\+)?\s*despues|before\s*(and|&|/|-|\+)?\s*after"
CONTEXTO_FOTO = r"foto|imagen|imagenes|galeria|resultad|casos?\s+real|pacientes?|ver\s+m"

ANTES_DESPUES = dict(
    titulo="Imágenes de «antes y después» de pacientes",
    gravedad=MEDIA,
    base_normativa=("RGPD y criterio de la AEPD: la imagen de un paciente es un dato de salud; publicarla exige su "
                    "consentimiento expreso y específico para ese uso. Además, puede inducir a pensar que el resultado "
                    "está garantizado (RD 1907/1996)."),
    accion=("Retirar las fotos salvo que tenga el consentimiento expreso y por escrito de cada paciente para uso "
            "publicitario, y guardarlo. Si lo tiene, acompañe cada imagen del texto corregido."),
    texto_corregido=("Imágenes publicadas con el consentimiento expreso y por escrito del paciente. "
                     "Los resultados varían en cada persona y no se garantizan."),
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
        if m:
            coinc.append(("enlace a galería", _ruta_legible(href), m.start(), m.end()))
    # 3) texto: solo con contexto de foto/galería o como encabezado corto
    for ubic, texto in _segmentos(p, con_url=True):
        if ubic == "texto alternativo de imágenes":
            continue
        pl = plegar(texto)
        for m in re.finditer(PATRON_ANTES_DESPUES, pl):
            a = pl.rfind("\n", 0, m.start()) + 1
            b = pl.find("\n", m.end())
            linea = pl[a: len(pl) if b == -1 else b]
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

TESTIMONIOS = dict(
    titulo="Testimonios u opiniones de pacientes en la publicidad",
    gravedad=MEDIA,
    base_normativa=("RD 1907/1996, art. 4: prohíbe usar testimonios de pacientes, reales o supuestos, como medio de "
                    "inducción al consumo en publicidad con finalidad sanitaria."),
    accion=("Retirar de las páginas de tratamientos los testimonios, opiniones y reseñas de pacientes (también los "
            "widgets de reseñas incrustados)."),
    texto_corregido=("¿Quiere saber si este tratamiento es adecuado para usted? Pida una consulta de valoración y "
                     "el médico le explicará sus opciones, beneficios y riesgos."),
    sin_verificar="Apartado concreto del art. 4 del RD 1907/1996: SIN VERIFICAR (texto oficial no consultado).",
)


def regla_testimonios(p: Pagina):
    if p.es_legal:
        return []
    coinc = []
    for ubic, texto in _segmentos(p):
        pl = plegar(texto)
        for m in re.finditer(PATRON_TESTIMONIOS, pl):
            coinc.append((ubic, texto, m.start(), m.end()))
    for valor in p.atributos:
        pl = plegar(valor)
        m = re.search(r"testimon", pl)
        if m:
            coinc.append(("bloque de la página (class/id)", valor, m.start(), m.end()))
            break
    return [_hallazgo_de_coincidencias("testimonios", coinc, p.url, **TESTIMONIOS)] if coinc else []


# --------------------------------------------------------------------------
# BAJA (sitio): páginas legales y médico responsable
# --------------------------------------------------------------------------

# Se buscan en enlaces (texto y href), títulos y URL de las páginas descargadas,
# y en el texto solo con la frase completa (para no contar "garantizamos su privacidad").
LEGALES = [
    ("aviso_legal", "Falta el aviso legal",
     r"aviso[\s\-_]*legal|legal[\s\-_]*notice|nota[\s\-_]*legal|informacion[\s\-_]*legal",
     r"aviso\s+legal",
     "LSSI (Ley 34/2002), art. 10: la web debe identificar al titular (nombre, NIF, domicilio, contacto, registro).",
     ("Aviso legal. Titular: {razon_social}. NIF: {nif}. Domicilio: {domicilio}. Correo: {email}. Teléfono: {telefono}. "
      "Inscrita en {registro_mercantil}. Centro sanitario autorizado por la Comunidad de Madrid, nº de registro "
      "sanitario {numero_registro_sanitario}. Director/a médico/a: {nombre_medico}, nº de colegiado {numero_colegiado}.")),
    ("privacidad", "Falta la política de privacidad",
     r"privacidad|privacy|proteccion[\s\-_]*de[\s\-_]*datos|\brgpd\b|\bgdpr\b",
     r"politica\s+de\s+privacidad|proteccion\s+de\s+datos",
     "RGPD, art. 13: hay que informar de quién trata los datos, para qué, con qué base y cómo ejercer los derechos.",
     ("Política de privacidad. Responsable: {razon_social} ({nif}), {domicilio}, {email}. Tratamos sus datos para "
      "gestionar sus citas y su historia clínica, con base en la prestación de asistencia sanitaria y, para las "
      "comunicaciones, en su consentimiento. Puede ejercer sus derechos de acceso, rectificación, supresión, "
      "oposición, limitación y portabilidad en {email} y reclamar ante la AEPD (www.aepd.es).")),
    ("cookies", "Falta la política de cookies",
     r"cookies?",
     r"politica\s+de\s+cookies|uso\s+de\s+cookies|utiliza(mos)?\s+cookies",
     "LSSI, art. 22.2: si la web usa cookies no técnicas, debe informar y pedir consentimiento.",
     ("Política de cookies. Esta web usa cookies técnicas, necesarias para su funcionamiento, y, solo si usted lo "
      "acepta, cookies de análisis y publicidad: {lista_de_cookies}. Puede aceptarlas, rechazarlas o configurarlas "
      "en el aviso de cookies y cambiar su elección en cualquier momento.")),
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
                marca_inicio=0, marca_fin=0, base_normativa=base,
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
        texto_corregido=("Dirección médica: {nombre_medico}, colegiado/a nº {numero_colegiado} del Ilustre Colegio "
                         "Oficial de Médicos de Madrid."),
        sin_verificar=("Requisito SIN VERIFICAR: no hemos confirmado una norma que exija con carácter general el nº de "
                       "colegiado en la publicidad del centro."))]


# --------------------------------------------------------------------------
# Motor y puntuación
# --------------------------------------------------------------------------

REGLAS_POR_PAGINA = [regla_toxina, regla_promesas, regla_promociones, regla_antes_despues, regla_testimonios]
REGLAS_DE_SITIO = [regla_registro, reglas_legales, regla_medico]
ORDEN_GRAVEDAD = {ALTA: 0, MEDIA: 1, BAJA: 2}


def analizar(paginas):
    """paginas: lista de Pagina. Devuelve los hallazgos ordenados por gravedad."""
    hallazgos = []
    for p in paginas:
        for regla in REGLAS_POR_PAGINA:
            hallazgos.extend(regla(p))
    for regla in REGLAS_DE_SITIO:
        hallazgos.extend(regla(paginas))
    hallazgos.sort(key=lambda h: ORDEN_GRAVEDAD[h.gravedad])
    return hallazgos


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
