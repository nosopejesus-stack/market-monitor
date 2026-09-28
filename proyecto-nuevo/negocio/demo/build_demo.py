#!/usr/bin/env python3
"""Genera la demo personalizada de una agencia.

Uso:
    python build_demo.py agencias/ejemplo.json
    -> salida/<slug-de-la-agencia>/index.html

Solo usa la biblioteca estándar. La plantilla es index.html (en esta misma carpeta):
se sustituye el bloque de configuración entre /*CONFIG_INICIO*/ y /*CONFIG_FIN*/.
Los textos que dependen de los datos (horario, rama del presupuesto, banner) se calculan
aquí y se guardan en "calculado", para que la página no tenga que decidirlos.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / "index.html"
MARCA = re.compile(r"/\*CONFIG_INICIO\*/.*?/\*CONFIG_FIN\*/", re.S)
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
HORA = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
URL = re.compile(r"^https?://[^\s<>\"']{3,200}$")

HORARIO_POR_DEFECTO = {"apertura": "09:00", "cierre": "20:00"}
URL_PRIVACIDAD_POR_DEFECTO = "(enlace a la política de privacidad de la agencia)"
BANNER = "SIMULACIÓN · conversación y comprador inventados; tiempos orientativos"
RAMA_CALIENTE = "CALIENTE"
RAMA_REVISAR = "REVISAR PRESUPUESTO"


class ErrorConfig(ValueError):
    pass


def slugify(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "agencia"


def _texto(d: dict, clave: str, donde: str, obligatorio: bool = True, maximo: int = 80) -> None:
    v = d.get(clave)
    if v is None and not obligatorio:
        return
    if not isinstance(v, str) or not v.strip():
        raise ErrorConfig(f"{donde}.{clave}: debe ser un texto no vacío")
    if len(v) > maximo:
        raise ErrorConfig(f"{donde}.{clave}: máximo {maximo} caracteres")


def _numero(d: dict, clave: str, donde: str, minimo: int, maximo: int) -> None:
    v = d.get(clave)
    if isinstance(v, bool) or not isinstance(v, int) or not (minimo <= v <= maximo):
        raise ErrorConfig(f"{donde}.{clave}: debe ser un entero entre {minimo} y {maximo}")


def _minutos(hora: str, donde: str) -> int:
    m = HORA.match(str(hora))
    if not m:
        raise ErrorConfig(f"{donde}: usa formato HH:MM")
    return int(m.group(1)) * 60 + int(m.group(2))


def presupuesto_por_defecto(precio: int) -> int:
    """Presupuesto del lead si no se configura: un 6 % por encima del precio, redondeado a 10.000."""
    return math.ceil(precio * 1.06 / 10_000) * 10_000


def validar(cfg: dict) -> dict:
    if not isinstance(cfg, dict):
        raise ErrorConfig("el JSON debe ser un objeto")
    ag = cfg.get("agencia")
    if not isinstance(ag, dict):
        raise ErrorConfig("falta el objeto 'agencia'")
    _texto(ag, "nombre", "agencia")
    _texto(ag, "agente", "agencia")
    if not COLOR.match(str(ag.get("color", ""))):
        raise ErrorConfig("agencia.color: usa formato #RRGGBB, p. ej. #0f5f8c")
    url = ag.setdefault("url_privacidad", URL_PRIVACIDAD_POR_DEFECTO)
    if url != URL_PRIVACIDAD_POR_DEFECTO and not (isinstance(url, str) and URL.match(url)):
        raise ErrorConfig("agencia.url_privacidad: debe ser una URL http(s) sin espacios (máx. 200 caracteres)")

    horario = ag.setdefault("horario", dict(HORARIO_POR_DEFECTO))
    if not isinstance(horario, dict):
        raise ErrorConfig("agencia.horario debe ser un objeto con 'apertura' y 'cierre'")
    for k, v in HORARIO_POR_DEFECTO.items():
        horario.setdefault(k, v)
    apertura = _minutos(horario["apertura"], "agencia.horario.apertura")
    cierre = _minutos(horario["cierre"], "agencia.horario.cierre")
    if apertura >= cierre:
        raise ErrorConfig("agencia.horario: 'apertura' debe ser anterior a 'cierre'")

    lead = cfg.setdefault("lead", {})
    if not isinstance(lead, dict):
        raise ErrorConfig("'lead' debe ser un objeto")
    lead.setdefault("nombre", "Comprador de ejemplo (ficticio)")
    lead.setdefault("hora", "21:47")
    _texto(lead, "nombre", "lead")
    hora_lead = _minutos(lead["hora"], "lead.hora")
    lead.setdefault("primera_respuesta_seg", 40)
    _numero(lead, "primera_respuesta_seg", "lead", 1, 120)
    if "presupuesto" in lead:
        _numero(lead, "presupuesto", "lead", 10_000, 50_000_000)

    pisos = cfg.get("pisos")
    if not isinstance(pisos, list) or not 1 <= len(pisos) <= 3:
        raise ErrorConfig("'pisos' debe ser una lista de 1 a 3 pisos")
    calc_pisos = []
    for i, p in enumerate(pisos):
        donde = f"pisos[{i}]"
        if not isinstance(p, dict):
            raise ErrorConfig(f"{donde}: debe ser un objeto")
        p.setdefault("ref", f"REF-{i + 1}")
        for k in ("ref", "direccion", "barrio"):
            _texto(p, k, donde)
        _numero(p, "precio", donde, 10_000, 50_000_000)
        _numero(p, "m2", donde, 10, 5_000)
        _numero(p, "habitaciones", donde, 0, 20)
        if "presupuesto_lead" in p:
            _numero(p, "presupuesto_lead", donde, 10_000, 50_000_000)
            presupuesto = p["presupuesto_lead"]
        elif "presupuesto" in lead:
            presupuesto = lead["presupuesto"]
        else:
            presupuesto = presupuesto_por_defecto(p["precio"])
        rama = RAMA_CALIENTE if presupuesto >= p["precio"] else RAMA_REVISAR
        calc_pisos.append({"presupuesto": presupuesto, "rama": rama})

    cfg["ejemplo"] = bool(cfg.get("ejemplo", False))

    fuera = hora_lead < apertura or hora_lead >= cierre
    crono = "objetivo < 2 min (simulado)"
    if fuera:
        crono += f" · fuera de horario ({lead['hora']}), sin intervención humana"
    cfg["calculado"] = {
        "banner": BANNER + (" · agencia ficticia" if cfg["ejemplo"] else ""),
        "fuera_horario": fuera,
        "crono": crono,
        "pisos": calc_pisos,
    }
    return cfg


def avisos(cfg: dict) -> list[str]:
    """Avisos no bloqueantes (se imprimen por stderr)."""
    res = []
    nombre = cfg["agencia"]["nombre"]
    if cfg["ejemplo"] and "ficticia" not in nombre.lower():
        res.append(f"ejemplo=true pero el nombre '{nombre}' no contiene 'ficticia': "
                   "podría confundirse con una agencia real.")
    if not cfg["ejemplo"]:
        res.append("ejemplo=false: los datos de los pisos deben venir de la propia agencia y con su permiso.")
    if cfg["agencia"]["url_privacidad"] == URL_PRIVACIDAD_POR_DEFECTO:
        res.append("falta agencia.url_privacidad: se muestra un texto genérico en su lugar.")
    return res


def html_desde_config(cfg: dict, plantilla: str | None = None) -> str:
    if plantilla is None:
        plantilla = PLANTILLA.read_text(encoding="utf-8")
    if len(MARCA.findall(plantilla)) != 1:
        raise RuntimeError("la plantilla no tiene exactamente un bloque de configuración")
    datos = json.dumps(cfg, ensure_ascii=False, indent=2)
    # Evita cerrar la etiqueta <script> o abrir comentarios HTML desde los datos.
    datos = datos.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    bloque = "/*CONFIG_INICIO*/" + datos + "/*CONFIG_FIN*/"
    return MARCA.sub(lambda _m: bloque, plantilla)


def cargar(ruta_json: Path) -> dict:
    try:
        cfg = json.loads(ruta_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErrorConfig(f"JSON no válido: {e}") from e
    cfg = validar(cfg)
    cfg.pop("_aviso", None)
    return cfg


def generar(ruta_json: Path, dir_salida: Path) -> Path:
    cfg = cargar(ruta_json)
    html = html_desde_config(cfg)
    destino = dir_salida / slugify(cfg["agencia"]["nombre"]) / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Genera la demo de WhatsApp personalizada para una agencia.")
    ap.add_argument("json", type=Path, help="archivo JSON de la agencia (ver agencias/ejemplo.json)")
    ap.add_argument("--salida", type=Path, default=AQUI / "salida", help="carpeta de salida (por defecto ./salida)")
    args = ap.parse_args(argv)
    try:
        cfg = cargar(args.json)
        for a in avisos(cfg):
            print(f"Aviso: {a}", file=sys.stderr)
        destino = generar(args.json, args.salida)
    except (ErrorConfig, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Demo generada: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
