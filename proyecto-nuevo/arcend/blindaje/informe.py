"""Genera el informe HTML autocontenido (imprimible en A4) y el JSON.

Dos modos:
- completo (por defecto): entregable de pago, con evidencias y textos corregidos.
- previo (``previo=True``): una página para enseñar antes de vender: N puntos con norma
  concreta, cada punto con su norma y gravedad, y la oferta. SIN textos corregidos.

Regla comercial: el informe no usa la palabra "IA" (hay un test que lo comprueba).
Todo el texto que viene de la web analizada se escapa con html.escape.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from html import escape
from urllib.parse import urlparse

from reglas import ALTA, BAJA, MEDIA, n_puntos_norma

NOTA_METODOLOGICA = ("Revisión basada solo en información pública, sin acceder a ningún sistema. "
                     "No constituye asesoramiento jurídico.")

PRECIO_CORRECCION = "390 €"
PRECIO_VIGILANCIA = "190 €/mes"

# Si no se pasan por línea de comandos, quedan como marcadores para rellenar a mano.
CONTACTO_POR_DEFECTO = {
    "nombre": "{nombre_contacto}",
    "telefono": "{telefono_contacto}",
    "email": "{email_contacto}",
}

NOMBRES_CORTOS = {
    "toxina": "publicidad de toxina botulínica (medicamento con receta)",
    "toxina_revisar": "mención explicativa de la toxina botulínica (revisar a mano)",
    "promesas": "promesas sanitarias prohibidas",
    "registro": "falta el nº de registro sanitario",
    "promociones": "promociones sobre tratamientos",
    "antes_despues": "fotos de antes y después",
    "testimonios": "testimonios de pacientes",
    "aviso_legal": "aviso legal",
    "privacidad": "política de privacidad",
    "cookies": "política de cookies",
    "medico": "identificación del médico",
}


def _plural(n, uno, varios):
    return f"{n} {uno if n == 1 else varios}"


def resumen_titular(clinica, web, fecha, n_paginas, puntos, nota, hallazgos, modo="web", previo=False,
                    lectura_fiable=True):
    """Las 3 líneas del resumen para el titular de la clínica."""
    dominio = urlparse(web).netloc or web
    a = sum(h.gravedad == ALTA for h in hallazgos)
    m = sum(h.gravedad == MEDIA for h in hallazgos)
    b = sum(h.gravedad == BAJA for h in hallazgos)
    n_norma = n_puntos_norma(hallazgos)
    if modo == "local":
        guardadas = _plural(n_paginas, "página guardada", "páginas guardadas")
        origen = f"{guardadas} de {dominio}" if dominio else f"{guardadas} de la web de {clinica}"
    else:
        origen = f"{_plural(n_paginas, 'página pública', 'páginas públicas')} de {dominio}"
    l1 = f"Hemos revisado {origen} el {fecha}: nota {nota} ({puntos}/100)."
    if not hallazgos:
        if not lectura_fiable:
            return [l1, "No se ha podido leer bien el contenido de la web: esta revisión no es fiable.",
                    "Para una revisión fiable, guarde las páginas desde el navegador y repita la revisión."]
        return [l1, "No hemos encontrado puntos de riesgo en las páginas revisadas.",
                "Recomendamos repetir la revisión cada mes y cada vez que publique una campaña."]
    l2 = (f"Hay {_plural(a, 'punto de riesgo alto', 'puntos de riesgo alto')}, {m} medio{'s' if m != 1 else ''} "
          f"y {b} bajo{'s' if b != 1 else ''} ({_plural(n_norma, 'punto', 'puntos')} con norma concreta).")
    principales = []
    for h in hallazgos:
        nombre = NOMBRES_CORTOS.get(h.regla, h.titulo.lower())
        if h.gravedad == (ALTA if a else MEDIA if m else BAJA) and nombre not in principales:
            principales.append(nombre)
    if previo:
        entrega = "con la corrección completa le entregamos los textos corregidos listos para publicar"
    else:
        entrega = "este informe incluye los textos corregidos listos para publicar"
    if a:
        l2 += " Lo más urgente: " + "; ".join(principales) + "."
        l3 = (f"Todo tiene arreglo: {entrega}, y corregir antes de un requerimiento de la Consejería de Sanidad "
              "reduce el riesgo.")
    else:
        l2 += " A revisar: " + "; ".join(principales) + "."
        l3 = f"No hay riesgos altos; {entrega}."
    return [l1, l2, l3]


def _evidencia_html(h):
    ev = h.evidencia
    i, f = h.marca_inicio, h.marca_fin
    if 0 <= i < f <= len(ev):
        return escape(ev[:i]) + "<mark>" + escape(ev[i:f]) + "</mark>" + escape(ev[f:])
    return escape(ev)


CSS = """
@page { size: A4; margin: 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, Helvetica, sans-serif; color: #1d2433; font-size: 10.5pt;
       line-height: 1.45; margin: 0; background: #f3f5f8; }
.hoja { max-width: 210mm; margin: 0 auto; background: #fff; padding: 14mm; }
header { border-bottom: 3px solid #1f3b5c; padding-bottom: 8px; margin-bottom: 14px;
         display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; }
h1 { font-size: 18pt; margin: 0; color: #1f3b5c; }
h2 { font-size: 13pt; color: #1f3b5c; border-bottom: 1px solid #d5dbe5; padding-bottom: 3px; margin-top: 22px; }
h3 { font-size: 11pt; margin: 0 0 6px; }
.meta { color: #56607a; font-size: 9.5pt; }
.nota { text-align: center; min-width: 92px; border-radius: 8px; padding: 6px 10px; color: #fff; }
.nota b { display: block; font-size: 26pt; line-height: 1; }
.nota-A { background: #1e7b4f; } .nota-B { background: #5c9a2c; } .nota-C { background: #c98a06; }
.nota-D { background: #c85a12; } .nota-E { background: #b0232a; }
.resumen { background: #eef3f9; border-left: 4px solid #1f3b5c; padding: 10px 14px; margin: 0; }
.resumen p { margin: 3px 0; }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
th, td { border: 1px solid #d5dbe5; padding: 5px 6px; text-align: left; vertical-align: top; }
th { background: #1f3b5c; color: #fff; }
td.url { word-break: break-all; }
.grav { font-weight: 700; font-size: 8.5pt; padding: 2px 6px; border-radius: 4px; color: #fff; white-space: nowrap; }
.ALTA { background: #b0232a; } .MEDIA { background: #c98a06; } .BAJA { background: #56607a; }
.hallazgo { border: 1px solid #d5dbe5; border-radius: 6px; padding: 10px 12px; margin: 10px 0;
            page-break-inside: avoid; break-inside: avoid; }
.etq { font-size: 8.5pt; text-transform: uppercase; letter-spacing: .04em; color: #56607a; margin: 8px 0 2px; }
.cita { background: #fbf6e9; border-left: 3px solid #c98a06; padding: 6px 9px; font-style: italic; }
mark { background: #ffd966; padding: 0 1px; }
.corregido { background: #eaf6ef; border-left: 3px solid #1e7b4f; padding: 6px 9px; white-space: pre-wrap; }
.sv { color: #8a4b00; font-size: 9pt; }
.pasos li { margin-bottom: 6px; }
.precio { font-weight: 700; color: #1f3b5c; }
.metodo { font-size: 9pt; color: #3b4459; }
.aviso { font-weight: 700; }
.alerta { background: #fdecea; border: 2px solid #b0232a; color: #7a1419; padding: 10px 14px; font-weight: 700;
          margin: 0 0 14px; }
.cifra { font-size: 13pt; font-weight: 700; color: #1f3b5c; margin: 8px 0; }
ul.paginas { font-size: 8.5pt; color: #56607a; word-break: break-all; columns: 2; }
footer { margin-top: 18px; font-size: 8.5pt; color: #56607a; border-top: 1px solid #d5dbe5; padding-top: 6px; }
@media print { body { background: #fff; } .hoja { padding: 0; max-width: none; }
               h2 { page-break-after: avoid; break-after: avoid; } }
"""


def _resumen(datos, hallazgos, previo):
    return resumen_titular(datos["clinica"], datos["web"], datos["fecha"], len(datos["paginas"]),
                           datos["puntuacion"], datos["nota"], hallazgos, modo=datos.get("modo", "web"),
                           previo=previo, lectura_fiable=datos.get("lectura_fiable", True))


def _proximos_pasos(w, c):
    e = escape
    w("<h2>Próximos pasos</h2>\n<ol class=\"pasos\">")
    w(f"<li><b>Corrección completa</b>: revisamos su web y sus redes sociales (publicaciones de los últimos 12 "
      f"meses), le entregamos todos los textos corregidos listos para publicar en un plazo de 5 días hábiles desde "
      f"el cobro y comprobamos que quedan bien publicados. <span class=\"precio\">{PRECIO_CORRECCION}</span>, "
      f"pago único.</li>")
    w(f"<li><b>Vigilancia mensual</b>: una revisión al mes de su web y sus redes (periódica, no en tiempo real); "
      f"le avisamos de las publicaciones nuevas con riesgo y le damos su corrección. "
      f"<span class=\"precio\">{PRECIO_VIGILANCIA}</span>, sin permanencia: baja con 15 días de preaviso.</li>")
    w("</ol>\n<p class=\"meta\">Todos los importes son sin IVA.</p>\n")
    w(f"<p>Contacto: <b>{e(c['nombre'])}</b> · {e(c['telefono'])} · {e(c['email'])}</p>\n")


def generar_html(datos, hallazgos, contacto=None, previo=False):
    c = dict(CONTACTO_POR_DEFECTO)
    c.update({k: v for k, v in (contacto or {}).items() if v})
    e = escape
    resumen = _resumen(datos, hallazgos, previo)
    n_norma = datos.get("n_puntos_norma", n_puntos_norma(hallazgos))
    web = datos["web"] or "copia guardada de la web"
    titulo = "Informe previo de publicidad sanitaria" if previo else "Informe de publicidad sanitaria"
    partes = []
    w = partes.append
    w("<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n")
    w("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n")
    w(f"<title>{titulo} · {e(datos['clinica'])}</title>\n<style>{CSS}</style>\n</head>\n<body>\n<div class=\"hoja\">\n")
    w("<header><div>")
    w(f"<h1>{titulo}</h1>")
    w(f"<div class=\"meta\"><b>{e(datos['clinica'])}</b> · {e(web)}<br>")
    w(f"Fecha de la revisión: {e(datos['fecha'])} · Páginas revisadas: {len(datos['paginas'])}</div></div>")
    w(f"<div class=\"nota nota-{e(datos['nota'])}\"><b>{e(datos['nota'])}</b>{datos['puntuacion']}/100</div></header>\n")

    if not datos.get("lectura_fiable", True):
        w(f"<div class=\"alerta\">{e(datos.get('aviso_lectura', ''))} No se incluyen los puntos que afirman que "
          "falta algo en la web (registro sanitario, páginas legales, médico responsable).</div>\n")

    w("<h2>Resumen para el titular</h2>\n<div class=\"resumen\">")
    for linea in resumen:
        w(f"<p>{e(linea)}</p>")
    w("</div>\n")
    w(f"<p class=\"cifra\">{_plural(n_norma, 'punto', 'puntos')} con norma concreta</p>\n")

    if previo:
        w("<h2>Puntos encontrados</h2>\n")
        if hallazgos:
            w("<table><thead><tr><th>#</th><th>Gravedad</th><th>Qué hemos visto</th><th>Norma</th>"
              "<th>Dónde</th></tr></thead><tbody>")
            for i, h in enumerate(hallazgos, 1):
                norma = e(h.norma or h.base_normativa)
                if h.sin_verificar:
                    norma += " <span class=\"sv\">(SIN VERIFICAR)</span>"
                w(f"<tr><td>{i}</td><td><span class=\"grav {h.gravedad}\">{h.gravedad}</span></td>"
                  f"<td>{e(h.titulo)}</td><td>{norma}</td><td class=\"url\">{e(h.url)}</td></tr>")
            w("</tbody></table>\n")
        else:
            w("<p>No se han encontrado puntos de riesgo en las páginas revisadas.</p>\n")
        _proximos_pasos(w, c)
        w(f"<p class=\"metodo\"><span class=\"aviso\">{e(NOTA_METODOLOGICA)}</span> Los puntos marcados SIN "
          "VERIFICAR dependen de un requisito legal que no hemos confirmado en el texto oficial.</p>\n")
        w(f"<footer>{e(NOTA_METODOLOGICA)} · {e(datos['clinica'])} · {e(datos['fecha'])}</footer>\n")
        w("</div>\n</body>\n</html>\n")
        return "".join(partes)

    w("<h2>Hallazgos</h2>\n")
    if hallazgos:
        w("<table><thead><tr><th>#</th><th>Gravedad</th><th>Qué hemos visto</th><th>Dónde</th></tr></thead><tbody>")
        for i, h in enumerate(hallazgos, 1):
            veces = f" ({h.apariciones} apariciones)" if h.apariciones > 1 else ""
            w(f"<tr><td>{i}</td><td><span class=\"grav {h.gravedad}\">{h.gravedad}</span></td>"
              f"<td>{e(h.titulo)}{e(veces)}</td><td class=\"url\">{e(h.url)}</td></tr>")
        w("</tbody></table>\n")
    else:
        w("<p>No se han encontrado hallazgos en las páginas revisadas.</p>\n")

    if hallazgos:
        w("<h2>Evidencias y textos corregidos</h2>\n")
        for i, h in enumerate(hallazgos, 1):
            w("<div class=\"hallazgo\">")
            w(f"<h3>{i}. <span class=\"grav {h.gravedad}\">{h.gravedad}</span> {e(h.titulo)}</h3>")
            w(f"<div class=\"meta\">Página: {e(h.url)} · Ubicación: {e(h.ubicacion)}</div>")
            w(f"<div class=\"etq\">Evidencia</div><div class=\"cita\">{_evidencia_html(h)}</div>")
            for otra in h.otras_evidencias:
                w(f"<div class=\"cita\" style=\"margin-top:4px\">{e(otra)}</div>")
            w(f"<div class=\"etq\">Por qué es un riesgo</div><div>{e(h.base_normativa)}</div>")
            if h.sin_verificar:
                w(f"<div class=\"sv\">{e(h.sin_verificar)}</div>")
            w(f"<div class=\"etq\">Qué hacer</div><div>{e(h.accion)}</div>")
            w(f"<div class=\"etq\">Texto corregido listo para publicar</div><div class=\"corregido\">{e(h.texto_corregido)}</div>")
            w("</div>\n")
        w("<p class=\"meta\">Sustituya lo que va entre llaves { } por los datos reales de la clínica y quite lo que va "
          "entre corchetes [ ] tras comprobarlo, antes de publicar.</p>\n")

    _proximos_pasos(w, c)

    w("<h2>Nota metodológica</h2>\n<div class=\"metodo\">")
    w(f"<p class=\"aviso\">{e(NOTA_METODOLOGICA)}</p>")
    if datos.get("modo") == "local":
        origen = "Se han analizado copias guardadas de páginas públicas de la web."
    else:
        origen = ("Se han leído solo páginas públicas de la web, como lo haría cualquier visitante, respetando el "
                  "archivo robots.txt y con una petición por segundo como máximo.")
    w(f"<p>{e(origen)} No se han revisado redes sociales, anuncios ni "
      "contenidos que solo aparecen al ejecutar JavaScript. La ausencia de hallazgos en una página no garantiza "
      "que cumpla toda la normativa. Los puntos marcados como SIN VERIFICAR dependen de un requisito legal que "
      "no hemos confirmado en el texto oficial. Recomendamos validar las correcciones con su asesor.</p>")
    w("<p>Puntuación: se parte de 100 y cada hallazgo resta según su gravedad (alta 25, media 10, baja 4; las "
      "repeticiones de un mismo punto restan menos). Con algún punto de riesgo alto la nota es C como máximo. "
      "«Puntos con norma concreta»: riesgos altos y medios con una norma identificada (sin los SIN VERIFICAR), "
      "contando una sola vez la misma frase.</p>")
    w("<div class=\"etq\">Páginas revisadas</div><ul class=\"paginas\">")
    for u in datos["paginas"]:
        w(f"<li>{e(u)}</li>")
    w("</ul>")
    if datos.get("avisos"):
        w("<div class=\"etq\">Incidencias de la descarga</div><ul class=\"paginas\">")
        for a in datos["avisos"]:
            w(f"<li>{e(a)}</li>")
        w("</ul>")
    w("</div>\n")
    w(f"<footer>{e(NOTA_METODOLOGICA)} · {e(datos['clinica'])} · {e(datos['fecha'])}</footer>\n")
    w("</div>\n</body>\n</html>\n")
    return "".join(partes)


# "Texto del testimonio" - Ana  ->  "Texto del testimonio" - [nombre]
_NOMBRE_TRAS_GUION = re.compile(
    r"([\"”»']\s*[-–—]\s*)[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+(\s+[A-ZÁÉÍÓÚÑ](\.|[a-záéíóúñü]+))?")


def anonimizar(texto: str) -> str:
    return _NOMBRE_TRAS_GUION.sub(r"\1[nombre]", texto)


def _hallazgo_json(h):
    d = asdict(h)
    ev, i, f = h.evidencia, h.marca_inicio, h.marca_fin
    if 0 <= i <= f <= len(ev):
        antes, marca, despues = anonimizar(ev[:i]), ev[i:f], anonimizar(ev[f:])
        d["evidencia"] = antes + marca + despues
        d["marca_inicio"], d["marca_fin"] = len(antes), len(antes) + len(marca)
    else:
        d["evidencia"] = anonimizar(ev)
    d["otras_evidencias"] = [anonimizar(o) for o in h.otras_evidencias]
    d["texto_corregido"] = anonimizar(h.texto_corregido)
    return d


def generar_json(datos, hallazgos):
    salida = dict(datos)
    salida["resumen"] = _resumen(datos, hallazgos, datos.get("previo", False))
    salida["n_puntos_norma"] = n_puntos_norma(hallazgos)
    salida["hallazgos"] = [_hallazgo_json(h) for h in hallazgos]
    salida["nota_metodologica"] = NOTA_METODOLOGICA
    return json.dumps(salida, ensure_ascii=False, indent=2)
