#!/usr/bin/env python3
"""Mi IA: un asistente que responde usando tu bóveda de Obsidian como memoria.

Cómo funciona (RAG, "retrieval-augmented generation"):
  1. Lee todas las notas .md de la bóveda y las parte en fragmentos.
  2. Para cada pregunta busca los fragmentos más relevantes (BM25).
  3. Se los pasa a un modelo de lenguaje junto con la pregunta.
  4. Lo que le pidas que recuerde lo guarda como nota nueva en la bóveda,
     así "aprende" de forma permanente y tú lo ves en Obsidian.

Solo usa la biblioteca estándar de Python 3.9+. Modelos soportados:
  - ollama    (por defecto): modelo local y gratis, en http://localhost:11434
  - anthropic: la API de Claude; necesita la variable ANTHROPIC_API_KEY
  - ninguno:  solo búsqueda; muestra las notas encontradas sin generar texto

Uso:
  python mi_ia.py preguntar "¿qué es GRPO?"
  python mi_ia.py chat
  python mi_ia.py recordar "Mi bar favorito para probar cócteles es X"
  python mi_ia.py buscar "leyes de escala"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BOVEDA = Path(os.environ.get("MI_IA_BOVEDA", RAIZ.parent / "vault"))
MODELO_OLLAMA = os.environ.get("MI_IA_MODELO", "qwen3:8b")
MODELO_CLAUDE = os.environ.get("MI_IA_MODELO_CLAUDE", "claude-sonnet-5-5")
URL_OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

SISTEMA = """Eres "Mi IA", el asistente personal de tu dueño.
Tu memoria es su bóveda de Obsidian: abajo tienes los fragmentos más relevantes.
Reglas:
- Responde en español, claro y directo.
- Básate en la memoria cuando sea relevante y di de qué nota sale ([[Nombre de la nota]]).
- Si la memoria no contiene la respuesta, dilo y responde con tu conocimiento general,
  dejando claro qué parte no viene de la memoria.
- No inventes datos personales del dueño que no estén en la memoria."""

PALABRAS_VACIAS = set(
    "a al algo con como de del el ella ellos en es esa ese eso esta este esto la las le lo los mas "
    "me mi muy no o para pero por que qué se si sin su sus te tu un una uno unos y ya the of and to in "
    "is it for on with as are be this that".split()
)


# ---------------------------------------------------------------- memoria
def tokenizar(texto: str) -> list[str]:
    palabras = re.findall(r"[a-záéíóúñü0-9]+", texto.lower())
    return [p for p in palabras if p not in PALABRAS_VACIAS and len(p) > 1]


def cargar_fragmentos(boveda: Path, tam: int = 1200) -> list[dict]:
    """Parte cada nota por encabezados y en trozos de ~tam caracteres."""
    fragmentos = []
    for ruta in sorted(boveda.rglob("*.md")):
        if any(parte.startswith(".") for parte in ruta.relative_to(boveda).parts):
            continue
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        nombre = ruta.stem
        secciones = re.split(r"\n(?=#{1,3} )", texto)
        for sec in secciones:
            for i in range(0, len(sec), tam):
                trozo = sec[i : i + tam].strip()
                if len(trozo) > 40:
                    fragmentos.append({"nota": nombre, "ruta": str(ruta.relative_to(boveda)), "texto": trozo})
    return fragmentos


class Buscador:
    """BM25 clásico: puntúa los fragmentos por coincidencia de palabras ponderada."""

    def __init__(self, fragmentos: list[dict], k1: float = 1.5, b: float = 0.75):
        self.frags = fragmentos
        self.docs = [tokenizar(f["nota"] + " " + f["texto"]) for f in fragmentos]
        self.k1, self.b = k1, b
        self.media = sum(map(len, self.docs)) / max(len(self.docs), 1)
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def buscar(self, consulta: str, k: int = 6) -> list[tuple[float, dict]]:
        q = tokenizar(consulta)
        puntos = []
        for i, tf in enumerate(self.tf):
            largo = len(self.docs[i])
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf.get(t, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * largo / self.media))
            if s > 0:
                puntos.append((s, self.frags[i]))
        puntos.sort(key=lambda x: -x[0])
        return puntos[:k]


def contexto(resultados: list[tuple[float, dict]]) -> str:
    return "\n\n".join(f"--- [[{f['nota']}]] ---\n{f['texto']}" for _, f in resultados)


# ---------------------------------------------------------------- modelos
def _post(url: str, datos: dict, cabeceras: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(datos).encode(), headers=cabeceras, method="POST")
    host = urllib.request.urlparse(url).hostname or ""
    if host in {"localhost", "127.0.0.1", "::1"}:
        # Un modelo local nunca debe pasar por un proxy HTTP del sistema.
        abrir = urllib.request.build_opener(urllib.request.ProxyHandler({})).open
    else:
        abrir = urllib.request.urlopen
    with abrir(req, timeout=600) as r:
        return json.loads(r.read())


def generar(mensajes: list[dict], motor: str) -> str:
    if motor == "ollama":
        try:
            r = _post(
                f"{URL_OLLAMA}/api/chat",
                {"model": MODELO_OLLAMA, "messages": [{"role": "system", "content": SISTEMA}] + mensajes, "stream": False},
                {"Content-Type": "application/json"},
            )
        except urllib.error.URLError as e:
            sys.exit(f"No pude hablar con Ollama en {URL_OLLAMA} ({e}). ¿Está abierto? Prueba: ollama serve")
        return r["message"]["content"]
    if motor == "anthropic":
        clave = os.environ.get("ANTHROPIC_API_KEY")
        if not clave:
            sys.exit("Falta la variable ANTHROPIC_API_KEY.")
        r = _post(
            "https://api.anthropic.com/v1/messages",
            {"model": MODELO_CLAUDE, "max_tokens": 2000, "system": SISTEMA, "messages": mensajes},
            {"Content-Type": "application/json", "x-api-key": clave, "anthropic-version": "2023-06-01"},
        )
        return "".join(b.get("text", "") for b in r["content"])
    raise ValueError(motor)


def responder(pregunta: str, buscador: Buscador, motor: str, historial: list[dict] | None = None) -> str:
    resultados = buscador.buscar(pregunta)
    if motor == "ninguno":
        if not resultados:
            return "No encontré nada en la memoria."
        return "Notas relevantes:\n" + "\n".join(f"  {p:5.1f}  [[{f['nota']}]]" for p, f in resultados) + "\n\n" + contexto(resultados[:2])
    mensaje = f"MEMORIA (fragmentos de la bóveda):\n{contexto(resultados) or '(nada relevante)'}\n\nPREGUNTA: {pregunta}"
    mensajes = (historial or []) + [{"role": "user", "content": mensaje}]
    return generar(mensajes, motor)


# ---------------------------------------------------------------- aprender
def recordar(texto: str, boveda: Path, titulo: str | None = None) -> Path:
    """Guarda un recuerdo nuevo en Memoria/ con fecha; Obsidian lo muestra al momento."""
    carpeta = boveda / "Memoria" / "Recuerdos"
    carpeta.mkdir(parents=True, exist_ok=True)
    ahora = dt.datetime.now()
    titulo = titulo or " ".join(texto.split()[:8])
    limpio = re.sub(r'[\\/:*?"<>|#\[\]]', "", titulo).strip()[:80] or "recuerdo"
    ruta = carpeta / f"{ahora:%Y-%m-%d} {limpio}.md"
    ruta.write_text(
        f"---\nfecha: {ahora:%Y-%m-%d %H:%M}\ntipo: recuerdo\ntags: [memoria]\n---\n\n# {titulo}\n\n{texto}\n\n"
        f"Ver también: [[Memoria - Sobre mí]]\n",
        encoding="utf-8",
    )
    return ruta


# ---------------------------------------------------------------- CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="Mi IA: asistente con memoria en Obsidian")
    ap.add_argument("--motor", choices=["ollama", "anthropic", "ninguno"], default=os.environ.get("MI_IA_MOTOR", "ollama"))
    ap.add_argument("--boveda", type=Path, default=BOVEDA)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preguntar").add_argument("texto")
    sub.add_parser("buscar").add_argument("texto")
    r = sub.add_parser("recordar")
    r.add_argument("texto")
    r.add_argument("--titulo")
    sub.add_parser("chat")
    sub.add_parser("estado")
    a = ap.parse_args()

    if not a.boveda.exists():
        sys.exit(f"No encuentro la bóveda en {a.boveda}. Usa --boveda o MI_IA_BOVEDA.")

    if a.cmd == "recordar":
        print(f"Guardado en {recordar(a.texto, a.boveda, a.titulo)}")
        return

    buscador = Buscador(cargar_fragmentos(a.boveda))
    if a.cmd == "estado":
        notas = {f["nota"] for f in buscador.frags}
        print(f"Bóveda: {a.boveda}\nNotas: {len(notas)}  Fragmentos: {len(buscador.frags)}  Motor: {a.motor}")
    elif a.cmd == "buscar":
        print(responder(a.texto, buscador, "ninguno"))
    elif a.cmd == "preguntar":
        print(responder(a.texto, buscador, a.motor))
    elif a.cmd == "chat":
        print("Mi IA lista. Escribe tu pregunta, '/recordar <texto>' para enseñarle algo, o 'salir'.")
        historial: list[dict] = []
        while True:
            try:
                q = input("\nTú: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in {"salir", "exit", "quit"}:
                break
            if q.startswith("/recordar "):
                ruta = recordar(q[len("/recordar ") :], a.boveda)
                buscador = Buscador(cargar_fragmentos(a.boveda))  # reindexar: ya lo sabe
                print(f"Mi IA: Aprendido. Lo guardé en {ruta.name}")
                continue
            resp = responder(q, buscador, a.motor, historial[-6:])
            print(f"\nMi IA: {resp}")
            historial += [{"role": "user", "content": q}, {"role": "assistant", "content": resp}]


if __name__ == "__main__":
    main()
