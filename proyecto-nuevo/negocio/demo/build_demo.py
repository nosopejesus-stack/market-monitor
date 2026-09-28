#!/usr/bin/env python3
"""Genera la demo personalizada de una agencia.

Uso:
    python build_demo.py agencias/ejemplo.json
    -> salida/<slug-de-la-agencia>/index.html

Solo usa la biblioteca estándar. La plantilla es index.html (en esta misma carpeta):
se sustituye el bloque de configuración entre /*CONFIG_INICIO*/ y /*CONFIG_FIN*/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / "index.html"
MARCA = re.compile(r"/\*CONFIG_INICIO\*/.*?/\*CONFIG_FIN\*/", re.S)
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
HORA = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


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


def validar(cfg: dict) -> dict:
    if not isinstance(cfg, dict):
        raise ErrorConfig("el JSON debe ser un objeto")
    ag = cfg.get("agencia")
    if not isinstance(ag, dict):
        raise ErrorConfig("falta el objeto 'agencia'")
    _texto(ag, "nombre", "agencia")
    _texto(ag, "agente", "agencia")
    _texto(ag, "asistente", "agencia", obligatorio=False, maximo=30)
    if not COLOR.match(str(ag.get("color", ""))):
        raise ErrorConfig("agencia.color: usa formato #RRGGBB, p. ej. #0f5f8c")

    lead = cfg.setdefault("lead", {})
    if not isinstance(lead, dict):
        raise ErrorConfig("'lead' debe ser un objeto")
    lead.setdefault("nombre", "Lead de ejemplo (ficticio)")
    lead.setdefault("hora", "21:47")
    _texto(lead, "nombre", "lead")
    if not HORA.match(str(lead["hora"])):
        raise ErrorConfig("lead.hora: usa formato HH:MM")
    lead.setdefault("primera_respuesta_seg", 40)
    _numero(lead, "primera_respuesta_seg", "lead", 1, 120)

    pisos = cfg.get("pisos")
    if not isinstance(pisos, list) or not 1 <= len(pisos) <= 3:
        raise ErrorConfig("'pisos' debe ser una lista de 1 a 3 pisos")
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

    cfg["ejemplo"] = bool(cfg.get("ejemplo", False))
    return cfg


def generar(ruta_json: Path, dir_salida: Path) -> Path:
    try:
        cfg = json.loads(ruta_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErrorConfig(f"JSON no válido: {e}") from e
    cfg = validar(cfg)
    cfg.pop("_aviso", None)

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    if len(MARCA.findall(plantilla)) != 1:
        raise RuntimeError("la plantilla no tiene exactamente un bloque de configuración")

    datos = json.dumps(cfg, ensure_ascii=False, indent=2)
    # Evita cerrar la etiqueta <script> o abrir comentarios HTML desde los datos.
    datos = datos.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    bloque = "/*CONFIG_INICIO*/" + datos + "/*CONFIG_FIN*/"
    html = MARCA.sub(lambda _m: bloque, plantilla)

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
        destino = generar(args.json, args.salida)
    except (ErrorConfig, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"Demo generada: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
