#!/usr/bin/env python3
"""Blindaje en lote: informe previo de todas las clínicas de un CSV con UN comando.

Uso (desde la carpeta blindaje):
    python lote.py ../prospectos/clinicas.csv [--solo ARC-001,ARC-002] [--max-paginas 15]
                   [--contacto-nombre "Tu Nombre" --contacto-telefono "600 000 000" --contacto-email tu@correo.es]

Para cada clínica hace lo mismo que ``blindaje.py URL --nombre ... --previo`` (misma descarga pasiva,
robots.txt y 1 petición/segundo) y escribe informes/<slug>/informe_previo.html + informe.json.
Al final (y tras cada clínica, por si se corta) escribe informes/RESUMEN.csv y informes/RESUMEN.html,
ordenados por prioridad de llamada.

Cada web descargada se guarda en informes/<slug>/paginas.json; con --reanalizar se vuelven a pasar
las reglas sobre esa copia sin descargar nada (útil tras corregir una regla).

Salta las filas sin web, con cadena=si o con "no_llamar" en notas. Un error en una clínica
(SSL, tiempo de espera, web no legible) se anota en su fila y el lote sigue.
No contacta con nadie: solo prepara la lista; las llamadas las hace el usuario.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import date
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import blindaje  # noqa: E402
import escaner  # noqa: E402
import reglas  # noqa: E402

COLUMNAS = ["id", "nombre", "telefono", "web", "lectura_fiable", "n_puntos_norma", "n_puntos_revisar", "nota",
            "hallazgo_principal", "frase_llamada", "incumplimientos_web", "posible_cadena", "estado", "informe"]
ESTADO_NO_LEGIBLE = "revisar a mano: usar --html-local"
ESTADO_SIN_GANCHO = "ok: sin gancho"


# --------------------------------------------------------------------------
# Lectura del CSV y filtro
# --------------------------------------------------------------------------

def leer_clinicas(ruta) -> list[dict]:
    """Lee el CSV (UTF-8 con o sin BOM; si falla, cp1252 de Excel). Admite ',' o ';'."""
    datos = Path(ruta).read_bytes()
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = datos.decode("cp1252", errors="replace")
    primera = texto.splitlines()[0] if texto else ""
    sep = ";" if primera.count(";") > primera.count(",") else ","
    filas = []
    for fila in csv.DictReader(texto.splitlines(), delimiter=sep):
        filas.append({(k or "").strip().lower(): (v or "").strip() for k, v in fila.items() if k is not None})
    return filas


def motivo_salto(fila: dict) -> str:
    """Motivo para no procesar la fila ("" si se procesa)."""
    if not fila.get("web"):
        return "sin web"
    if reglas.plegar(fila.get("cadena", "")).strip() in ("si", "s", "yes", "true", "1"):
        return "cadena"
    if "no_llamar" in reglas.plegar(fila.get("notas", "")) or "no_llamar" in reglas.plegar(fila.get("estado", "")):
        return "no_llamar"
    return ""


def seleccionar(filas, solo=None):
    """Devuelve (a_procesar, saltadas[(fila, motivo)], ids_desconocidos)."""
    ids = [i.strip() for i in (solo or "").split(",") if i.strip()]
    desconocidos = []
    if ids:
        existentes = {f.get("id") for f in filas}
        desconocidos = [i for i in ids if i not in existentes]
        filas = [f for f in filas if f.get("id") in ids]
    procesar, saltadas = [], []
    for f in filas:
        motivo = motivo_salto(f)
        if motivo:
            saltadas.append((f, motivo))
        else:
            procesar.append(f)
    return procesar, saltadas, desconocidos


# --------------------------------------------------------------------------
# Una clínica
# --------------------------------------------------------------------------

def hallazgo_principal(hallazgos) -> str:
    """Título del ALTA/MEDIA más grave (a igual gravedad, antes el que no es SIN VERIFICAR)."""
    graves = [h for h in hallazgos if h.gravedad in (reglas.ALTA, reglas.MEDIA)]
    if not graves:
        return ""
    graves.sort(key=lambda h: (reglas.ORDEN_GRAVEDAD[h.gravedad], bool(h.sin_verificar)))
    h = graves[0]
    return h.titulo + (" (SIN VERIFICAR)" if h.sin_verificar else "")


def _una_linea(texto: str, maximo: int = 300) -> str:
    t = " ".join(str(texto).split())
    return t if len(t) <= maximo else t[: maximo - 1] + "…"


CACHE = "paginas.json"


def guardar_cache(carpeta, web, paginas_html, avisos):
    """Guarda lo descargado (URL + HTML) para volver a analizar sin descargar otra vez (--reanalizar)."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = {"web": web, "fecha": date.today().isoformat(), "avisos": list(avisos),
             "paginas": [{"url": u, "html": h} for u, h in paginas_html]}
    (carpeta / CACHE).write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def leer_cache(carpeta):
    """Devuelve (paginas_html, avisos) de la descarga guardada, o None si no hay."""
    ruta = Path(carpeta) / CACHE
    if not ruta.is_file():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return [(p["url"], p["html"]) for p in datos.get("paginas", [])], list(datos.get("avisos", []))


def procesar_clinica(fila, salida, max_paginas=15, contacto=None, html_local=None, obtener=None,
                     dormir=time.sleep, log=print, subcarpeta=None, fecha=None, reanalizar=False,
                     comprobar_cert=None) -> dict:
    """Informe previo de una clínica. Nunca lanza excepción: los errores van a la columna estado.

    Lo descargado se guarda en informes/<slug>/paginas.json; con ``reanalizar`` se usa esa copia
    (si existe) en vez de descargar otra vez: sirve para volver a pasar las reglas tras corregirlas.
    """
    nombre = fila.get("nombre") or fila.get("id") or "clinica"
    web = fila.get("web", "")
    if web and "://" not in web:
        web = "https://" + web
    res = {"id": fila.get("id", ""), "nombre": nombre, "telefono": fila.get("telefono_publico", ""),
           "web": web, "lectura_fiable": "", "n_puntos_norma": "", "n_puntos_revisar": "", "nota": "",
           "hallazgo_principal": "", "frase_llamada": "", "incumplimientos_web": "", "posible_cadena": "", "estado": "", "informe": "", "_puntuacion": None}
    contacto = contacto or {}
    carpeta_clinica = Path(salida) / (subcarpeta or blindaje.slug(nombre))
    try:
        avisos = []
        cache = leer_cache(carpeta_clinica) if reanalizar and not html_local else None
        if html_local:
            paginas_html = blindaje.cargar_local(html_local)
            modo = "local"
        elif cache is not None:
            paginas_html, avisos = cache
            modo = "web"
            log(f"  (copia guardada: {len(paginas_html)} página(s), sin descargar)")
        else:
            r = blindaje.Rastreador(web, max_paginas=max_paginas, obtener=obtener, dormir=dormir,
                                    user_agent=blindaje.crear_user_agent(contacto.get("email", "")), log=log)
            paginas_html = r.rastrear()
            avisos = r.avisos
            modo = "web"
            if paginas_html:
                guardar_cache(carpeta_clinica, web, paginas_html, avisos)
        if not paginas_html:
            # El aviso de conexión (SSL, timeout...) explica más que "robots.txt no permite".
            conexion = [a for a in avisos if a.startswith("No se pudo")]
            motivo = (conexion or avisos or ["la web no devolvió ninguna página HTML."])[0]
            if "--html-local" not in motivo:
                motivo += " Guarde las páginas (Ctrl+S) y use blindaje.py --html-local CARPETA."
            res["estado"] = "error: " + _una_linea(f"no se pudo leer ninguna página. {motivo}", 400)
            res["lectura_fiable"] = "no"
            return res
        certificado = None
        if comprobar_cert and web and modo == "web":
            certificado = comprobar_cert(blindaje._host(web))
        carpeta, datos, hallazgos = blindaje.ejecutar(paginas_html, nombre, web, salida, avisos, contacto,
                                                      fecha=fecha, modo=modo, previo=True, subcarpeta=subcarpeta,
                                                      certificado=certificado,
                                                      registro_csv=fila.get("registro_sanitario", ""))
    except (Exception, SystemExit) as err:  # SSL, timeout, URL mal formada, carpeta inexistente...
        res["estado"] = "error: " + _una_linea(blindaje.describir_error(err) or type(err).__name__)
        res["lectura_fiable"] = "no"
        return res
    fiable = datos["lectura_fiable"]
    res.update({
        "lectura_fiable": "si" if fiable else "no",
        "n_puntos_norma": datos["n_puntos_norma"],
        "n_puntos_revisar": datos["n_puntos_revisar"],
        "nota": f"{datos['nota']} ({datos['puntuacion']}/100)",
        "hallazgo_principal": hallazgo_principal(hallazgos),
        "frase_llamada": datos["frase_llamada"],
        "posible_cadena": "; ".join(datos.get("senales_cadena", [])),
        "incumplimientos_web": "; ".join(h.titulo for h in hallazgos
                                         if h.regla.startswith("web_") and h.gravedad in (reglas.ALTA, reglas.MEDIA)),
        "informe": f"{carpeta.name}/informe_previo.html",
        "_puntuacion": datos["puntuacion"],
    })
    if not fiable:
        res["estado"] = ESTADO_NO_LEGIBLE
    elif not datos["frase_llamada"]:
        res["estado"] = ESTADO_SIN_GANCHO
    else:
        res["estado"] = "ok"
    return res


# --------------------------------------------------------------------------
# Resumen
# --------------------------------------------------------------------------

def clave_prioridad(r):
    """Primero las legibles con más puntos con norma, luego más puntos a revisar, luego peor nota.
    Después las no legibles y al final los errores."""
    if r["estado"].startswith("error"):
        grupo = 2
    elif r["lectura_fiable"] != "si":
        grupo = 1
    else:
        grupo = 0
    n_norma = r["n_puntos_norma"] if isinstance(r["n_puntos_norma"], int) else 0
    n_rev = r["n_puntos_revisar"] if isinstance(r["n_puntos_revisar"], int) else 0
    punt = r["_puntuacion"] if r["_puntuacion"] is not None else 101
    return (grupo, -n_norma, -n_rev, punt, r["id"])


def ordenar(resultados):
    return sorted(resultados, key=clave_prioridad)


def escribir_csv(resultados, ruta):
    """CSV con ';' y BOM: se abre bien con doble clic en Excel en español."""
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in ordenar(resultados):
            w.writerow(r)


CSS = """
body { font-family: "Segoe UI", Arial, sans-serif; color: #1d2433; font-size: 10pt; margin: 16px; }
h1 { color: #1f3b5c; font-size: 16pt; } h2 { color: #1f3b5c; font-size: 12pt; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #d5dbe5; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #1f3b5c; color: #fff; position: sticky; top: 0; }
td.web { word-break: break-all; max-width: 180px; }
tr.norma td:first-child { border-left: 4px solid #b0232a; }
tr.revisar td:first-child { border-left: 4px solid #c98a06; }
tr.nolegible { background: #fdf6e3; } tr.error { background: #fdecea; }
.frase { font-style: italic; }
.meta { color: #56607a; }
"""


def _clase(r):
    if r["estado"].startswith("error"):
        return "error"
    if r["lectura_fiable"] != "si":
        return "nolegible"
    if isinstance(r["n_puntos_norma"], int) and r["n_puntos_norma"] > 0:
        return "norma"
    if isinstance(r["n_puntos_revisar"], int) and r["n_puntos_revisar"] > 0:
        return "revisar"
    return ""


def generar_html(resultados, saltadas=(), fecha=None, completo=True):
    e = escape
    filas = ordenar(resultados)
    fecha = fecha or date.today().strftime("%d/%m/%Y")
    n_ok = sum(r["estado"] == "ok" for r in filas)
    p = []
    w = p.append
    w("<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n")
    w(f"<title>Resumen de clínicas · {e(fecha)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n")
    w(f"<h1>Resumen de clínicas por prioridad de llamada</h1>\n<p class=\"meta\">{e(fecha)} · "
      f"{len(filas)} revisada(s) · {n_ok} con frase para la llamada · {len(saltadas)} saltada(s)"
      f"{'' if completo else ' · LOTE EN CURSO O INTERRUMPIDO: faltan clínicas'}</p>\n")
    w("<p class=\"meta\">La frase la calcula la herramienta: «no permite» solo con puntos con norma concreta; "
      "«conviene revisar» si solo hay puntos que dependen de algo SIN VERIFICAR. Sin frase: no llamar con gancho. "
      "Antes de llamar, abra el informe previo y compruebe el punto principal en la web. "
      "El informe no es asesoramiento jurídico.</p>\n")
    w("<table><thead><tr><th>#</th><th>Id</th><th>Clínica</th><th>Teléfono</th><th>Web</th><th>Lectura fiable</th>"
      "<th>Puntos con norma</th><th>Puntos a revisar</th><th>Nota</th><th>Hallazgo principal</th>"
      "<th>Frase para la llamada</th><th>Incumplimientos de la web</th><th>Posible cadena (verificar)</th><th>Estado</th></tr></thead><tbody>\n")
    for i, r in enumerate(filas, 1):
        nombre = e(r["nombre"])
        if r["informe"]:
            nombre = f"<a href=\"{e(r['informe'])}\">{nombre}</a>"
        w(f"<tr class=\"{_clase(r)}\"><td>{i}</td><td>{e(r['id'])}</td><td>{nombre}</td>"
          f"<td>{e(r['telefono'])}</td><td class=\"web\">{e(r['web'])}</td><td>{e(r['lectura_fiable'])}</td>"
          f"<td>{e(str(r['n_puntos_norma']))}</td><td>{e(str(r['n_puntos_revisar']))}</td><td>{e(r['nota'])}</td>"
          f"<td>{e(r['hallazgo_principal'])}</td><td class=\"frase\">{e(r['frase_llamada'])}</td>"
          f"<td>{e(r.get('incumplimientos_web', ''))}</td><td>{e(r.get('posible_cadena', ''))}</td><td>{e(r['estado'])}</td></tr>\n")
    w("</tbody></table>\n")
    if saltadas:
        w("<h2>Saltadas</h2>\n<table><thead><tr><th>Id</th><th>Clínica</th><th>Motivo</th></tr></thead><tbody>\n")
        for f, motivo in saltadas:
            w(f"<tr><td>{e(f.get('id', ''))}</td><td>{e(f.get('nombre', ''))}</td><td>{e(motivo)}</td></tr>\n")
        w("</tbody></table>\n")
    w("</body>\n</html>\n")
    return "".join(p)


def escribir_resumen(resultados, saltadas, salida, fecha=None, completo=True):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    escribir_csv(resultados, salida / "RESUMEN.csv")
    (salida / "RESUMEN.html").write_text(generar_html(resultados, saltadas, fecha, completo), encoding="utf-8")


# --------------------------------------------------------------------------
# Programa
# --------------------------------------------------------------------------

def _html_local_por_id(valores):
    mapa = {}
    for v in valores or []:
        if "=" not in v:
            raise SystemExit(f"--html-local-id espera ID=CARPETA, no {v!r}")
        i, carpeta = v.split("=", 1)
        mapa[i.strip()] = carpeta.strip()
    return mapa


def ejecutar_lote(ruta_csv, salida, solo=None, max_paginas=15, contacto=None, html_local_id=None, obtener=None,
                  dormir=time.sleep, log=print, fecha=None, reanalizar=False):
    """Procesa el CSV y escribe los informes y el resumen. Devuelve (resultados, saltadas)."""
    filas = leer_clinicas(ruta_csv)
    procesar, saltadas, desconocidos = seleccionar(filas, solo)
    for i in desconocidos:
        log(f"aviso: el id {i} de --solo no está en el CSV")
    for f, motivo in saltadas:
        log(f"Saltada {f.get('id', '')} {f.get('nombre', '')}: {motivo}")
    html_local_id = html_local_id or {}
    resultados, usadas = [], set()
    try:
        for n, fila in enumerate(procesar, 1):
            nombre = fila.get("nombre") or fila.get("id") or "clinica"
            sub = blindaje.slug(nombre)
            if sub in usadas:                       # dos sedes con el mismo nombre
                sub = blindaje.slug(f"{nombre} {fila.get('id', n)}")
            usadas.add(sub)
            log(f"\n[{n}/{len(procesar)}] {fila.get('id', '')} {nombre} · {fila.get('web', '')}")
            r = procesar_clinica(fila, salida, max_paginas, contacto, html_local=html_local_id.get(fila.get("id")),
                                 obtener=obtener, dormir=dormir, log=log, subcarpeta=sub, fecha=fecha,
                                 reanalizar=reanalizar,
                                 comprobar_cert=escaner.comprobar_certificado if obtener is None else None)
            log(f"  -> {r['estado']}" + (f" · {r['frase_llamada']}" if r["frase_llamada"] else ""))
            resultados.append(r)
            escribir_resumen(resultados, saltadas, salida, fecha, completo=False)
    finally:
        escribir_resumen(resultados, saltadas, salida, fecha, completo=len(resultados) == len(procesar))
    return resultados, saltadas


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Informe previo de todas las clínicas de un CSV y resumen por "
                                             "prioridad de llamada (no contacta con nadie).")
    ap.add_argument("csv", help=r"CSV de clínicas, p. ej. ..\prospectos\clinicas.csv")
    ap.add_argument("--solo", default="", help="solo estos ids, separados por comas (p. ej. ARC-001,ARC-002)")
    ap.add_argument("--max-paginas", type=int, default=15, help="páginas como máximo por clínica (por defecto 15)")
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent / "informes"),
                    help="carpeta de informes (por defecto ./informes)")
    ap.add_argument("--contacto-nombre", default="", help="tu nombre para los informes")
    ap.add_argument("--contacto-telefono", default="", help="tu teléfono para los informes")
    ap.add_argument("--contacto-email", default="",
                    help="tu email para los informes (también va en el User-Agent: +contacto)")
    ap.add_argument("--reanalizar", action="store_true",
                    help="usar la copia guardada de cada web (informes/<clinica>/paginas.json) en vez de descargar")
    # Opción oculta (tests y casos puntuales): usar HTML guardado para un id en vez de descargar.
    ap.add_argument("--html-local-id", action="append", default=[], metavar="ID=CARPETA", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if not Path(args.csv).is_file():
        ap.error(f"no existe el archivo {args.csv}")
    contacto = {"nombre": args.contacto_nombre, "telefono": args.contacto_telefono, "email": args.contacto_email}
    try:
        resultados, saltadas = ejecutar_lote(args.csv, args.salida, args.solo, args.max_paginas, contacto,
                                             _html_local_por_id(args.html_local_id), reanalizar=args.reanalizar)
    except KeyboardInterrupt:
        print("\nInterrumpido: el resumen parcial está en", Path(args.salida) / "RESUMEN.html")
        return 130
    salida = Path(args.salida)
    con_frase = sum(r["estado"] == "ok" for r in resultados)
    errores = sum(r["estado"].startswith("error") for r in resultados)
    print(f"\n{len(resultados)} clínica(s) revisada(s): {con_frase} con frase para la llamada, {errores} con error, "
          f"{len(saltadas)} saltada(s).")
    print(f"Resumen: {salida / 'RESUMEN.html'}\n         {salida / 'RESUMEN.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
