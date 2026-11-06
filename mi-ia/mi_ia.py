#!/usr/bin/env python3
"""Mi IA: tu asistente personal con memoria en Obsidian, que aprende de lo bueno y lo malo.

Cómo funciona (RAG + reglas + feedback):
  1. Lee la bóveda de Obsidian y la parte en fragmentos.
  2. Para cada pregunta busca lo relevante: por palabras (BM25) y, si hay modelo de
     embeddings, por significado.
  3. Siempre le pasa al modelo tus REGLAS (Memoria/Lecciones/Reglas - Hacer / No hacer).
  4. Responde con el motor elegido:
       ollama    modelo abierto local (por defecto; gratis y privado)
       anthropic API de Claude (ANTHROPIC_API_KEY)
       propia    tu red neuronal entrenada desde cero (red_neuronal/, experimental)
       ninguno   solo busca en la memoria
  5. Aprende:
       /recordar <texto>   guarda un recuerdo en la bóveda
       /bien               la última respuesta fue buena (se guarda como ejemplo)
       /mal <por qué>      fue mala: se guarda como error y se crea una regla "No hacer"
       /hacer <regla>      añade una regla de lo que SÍ debe hacer
       /evitar <regla>     añade una regla de lo que NO debe hacer
     Las conversaciones se guardan en Memoria/Conversaciones y las valoraciones en
     datos/preferencias.jsonl (formato listo para afinar un modelo con DPO o SFT más adelante).

Uso:
  python mi_ia.py chat             conversar en la terminal
  python mi_ia.py web              abrir la página web local en http://localhost:8765
  python mi_ia.py preguntar "..."  una pregunta suelta
  python mi_ia.py buscar "..."     ver qué notas encuentra
  python mi_ia.py estado           resumen de la memoria
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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
DATOS = RAIZ / "datos"
BOVEDA = Path(os.environ.get("MI_IA_BOVEDA", RAIZ.parent / "vault"))
MODELO_OLLAMA = os.environ.get("MI_IA_MODELO", "qwen3:8b")
MODELO_EMBED = os.environ.get("MI_IA_EMBED", "nomic-embed-text")
MODELO_CLAUDE = os.environ.get("MI_IA_MODELO_CLAUDE", "claude-sonnet-5-5")
URL_OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

SISTEMA = """Eres "Mi IA", el asistente personal de tu dueño. Tu memoria es su bóveda de Obsidian.

REGLAS QUE SIEMPRE CUMPLES (aprendidas de experiencias anteriores):
{reglas}

Cómo responder:
- Español, claro y directo.
- Usa la MEMORIA cuando sea relevante y di de qué nota sale ([[Nombre de la nota]]).
- Si la memoria no tiene la respuesta, dilo; luego puedes usar tu conocimiento general
  dejando claro que no viene de la memoria.
- Nunca inventes datos personales, fechas ni cifras."""

VACIAS = set(
    "a al algo con como de del el ella ellos en es esa ese eso esta este esto la las le lo los mas "
    "me mi muy no o para pero por que qué se si sin su sus te tu un una uno unos y ya the of and to in "
    "is it for on with as are be this that".split()
)


# =================================================================== memoria
def tokenizar(texto: str) -> list[str]:
    return [p for p in re.findall(r"[a-záéíóúñü0-9]+", texto.lower()) if p not in VACIAS and len(p) > 1]


def sin_frontmatter(texto: str) -> str:
    texto = re.sub(r"\A---\n.*?\n---\n", "", texto, flags=re.S)
    return re.sub(r"<!--.*?-->", "", texto, flags=re.S)


def cargar_fragmentos(boveda: Path, tam: int = 1200) -> list[dict]:
    fragmentos = []
    for ruta in sorted(boveda.rglob("*.md")):
        rel = ruta.relative_to(boveda)
        if any(p.startswith(".") for p in rel.parts) or "Conversaciones" in rel.parts:
            continue  # las conversaciones son historial, no memoria: si no, sus errores se volverían "verdad"
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        for sec in re.split(r"\n(?=#{1,3} )", texto):
            for i in range(0, len(sec), tam):
                trozo = sec[i : i + tam].strip()
                if len(trozo) > 40:
                    fragmentos.append({"nota": ruta.stem, "ruta": str(rel), "texto": trozo})
    return fragmentos


def leer_reglas(boveda: Path) -> str:
    partes = []
    for nombre, titulo in (("Reglas - Hacer", "SÍ hacer"), ("Reglas - No hacer", "NO hacer")):
        ruta = boveda / "Memoria" / "Lecciones" / f"{nombre}.md"
        if ruta.exists():
            lineas = [l.strip() for l in sin_frontmatter(ruta.read_text(encoding="utf-8")).splitlines()
                      if l.strip().startswith("- ")]
            if lineas:
                partes.append(f"{titulo}:\n" + "\n".join(lineas))
    return "\n\n".join(partes) or "(todavía no hay reglas)"


class Buscador:
    """Búsqueda híbrida: BM25 (palabras) + embeddings (significado) si están disponibles."""

    def __init__(self, fragmentos: list[dict], usar_embeddings: bool = True):
        self.frags = fragmentos
        self.docs = [tokenizar(f["nota"] + " " + f["texto"]) for f in fragmentos]
        self.media = sum(map(len, self.docs)) / max(len(self.docs), 1)
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(d) for d in self.docs]
        self.vectores = cargar_embeddings(fragmentos) if usar_embeddings else None

    def bm25(self, q: list[str], i: int, k1: float = 1.5, b: float = 0.75) -> float:
        tf, largo, s = self.tf[i], len(self.docs[i]), 0.0
        for t in q:
            if t in tf:
                f = tf[t]
                s += self.idf.get(t, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * largo / self.media))
        return s

    def buscar(self, consulta: str, k: int = 6) -> list[tuple[float, dict]]:
        q = tokenizar(consulta)
        lexico = [self.bm25(q, i) for i in range(len(self.frags))]
        tope = max(lexico) or 1.0
        puntos = [s / tope for s in lexico]
        if self.vectores:
            qv = embeber([consulta])
            if qv:
                qv = qv[0]
                for i, v in enumerate(self.vectores):
                    puntos[i] = 0.5 * puntos[i] + 0.5 * max(0.0, coseno(qv, v))
        orden = sorted(range(len(puntos)), key=lambda i: -puntos[i])
        return [(puntos[i], self.frags[i]) for i in orden[:k] if puntos[i] > 0]


def coseno(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return num / den if den else 0.0


# ================================================================ conexiones
def _post(url: str, datos: dict, cabeceras: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(url, data=json.dumps(datos).encode(), headers=cabeceras, method="POST")
    host = urllib.request.urlparse(url).hostname or ""
    abrir = (urllib.request.build_opener(urllib.request.ProxyHandler({})).open
             if host in {"localhost", "127.0.0.1", "::1"} else urllib.request.urlopen)
    with abrir(req, timeout=timeout) as r:
        return json.loads(r.read())


_EMBED_OK: bool | None = None


def embeber(textos: list[str]) -> list[list[float]] | None:
    """Vectores de significado con Ollama (/api/embed). None si no hay modelo de embeddings."""
    global _EMBED_OK
    if _EMBED_OK is False:
        return None
    try:
        r = _post(f"{URL_OLLAMA}/api/embed", {"model": MODELO_EMBED, "input": textos},
                  {"Content-Type": "application/json"}, timeout=300)
        _EMBED_OK = True
        return r["embeddings"]
    except Exception:
        if _EMBED_OK is None:
            print(f"(Búsqueda por significado desactivada: falta '{MODELO_EMBED}' en Ollama. "
                  f"Actívala con: ollama pull {MODELO_EMBED})", file=sys.stderr)
        _EMBED_OK = False
        return None


def cargar_embeddings(fragmentos: list[dict]) -> list[list[float]] | None:
    DATOS.mkdir(exist_ok=True)
    ruta = DATOS / f"embeddings-{re.sub(r'[^A-Za-z0-9_.-]', '_', MODELO_EMBED)}.json"  # una caché por modelo
    cache = json.loads(ruta.read_text()) if ruta.exists() else {}
    claves = [hashlib.sha1(f["texto"].encode()).hexdigest() for f in fragmentos]
    faltan = [i for i, c in enumerate(claves) if c not in cache]
    for ini in range(0, len(faltan), 32):
        lote = faltan[ini : ini + 32]
        vecs = embeber([fragmentos[i]["nota"] + "\n" + fragmentos[i]["texto"] for i in lote])
        if vecs is None:
            return None
        for i, v in zip(lote, vecs):
            cache[claves[i]] = v
    if faltan:
        ruta.write_text(json.dumps(cache))
    return [cache[c] for c in claves]


def generar(mensajes: list[dict], motor: str, sistema: str) -> str:
    if motor == "ollama":
        try:
            r = _post(f"{URL_OLLAMA}/api/chat",
                      {"model": MODELO_OLLAMA, "messages": [{"role": "system", "content": sistema}] + mensajes,
                       "stream": False}, {"Content-Type": "application/json"})
        except urllib.error.URLError as e:
            return (f"⚠️ No puedo hablar con Ollama en {URL_OLLAMA} ({e}). Ábrelo (ollama serve) y comprueba que "
                    f"tienes el modelo: ollama pull {MODELO_OLLAMA}")
        return re.sub(r"<think>.*?</think>", "", r["message"]["content"], flags=re.S).strip()
    if motor == "anthropic":
        clave = os.environ.get("ANTHROPIC_API_KEY")
        if not clave:
            return "⚠️ Falta la variable ANTHROPIC_API_KEY."
        r = _post("https://api.anthropic.com/v1/messages",
                  {"model": MODELO_CLAUDE, "max_tokens": 2000, "system": sistema, "messages": mensajes},
                  {"Content-Type": "application/json", "x-api-key": clave, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r["content"])
    if motor == "propia":
        sys.path.insert(0, str(RAIZ / "red_neuronal"))
        try:
            from generar import continuar  # noqa: E402
        except ImportError as e:
            return f"⚠️ La red propia necesita PyTorch y regex (pip install torch regex): {e}"
        pregunta = mensajes[-1]["content"].split("PREGUNTA:")[-1].strip()
        texto = continuar(f"## {pregunta}\n", tokens=150, temperatura=0.7)
        return "🧪 (red neuronal propia, experimental: escribe al estilo de tus notas, todavía no razona)\n" + texto
    raise ValueError(motor)


# ================================================================== IA
class MiIA:
    def __init__(self, boveda: Path, motor: str):
        self.boveda, self.motor = boveda, motor
        self.historial: list[dict] = []
        self.ultima: dict | None = None
        self.recargar()

    def recargar(self) -> None:
        self.buscador = Buscador(cargar_fragmentos(self.boveda), usar_embeddings=self.motor != "ninguno")

    def preguntar(self, pregunta: str) -> tuple[str, list[str]]:
        resultados = self.buscador.buscar(pregunta)
        fuentes = list(dict.fromkeys(f["nota"] for _, f in resultados))
        if self.motor == "ninguno":
            if not resultados:
                return "No encontré nada en la memoria.", []
            cuerpo = "\n\n".join(f"--- [[{f['nota']}]] ---\n{f['texto']}" for _, f in resultados[:2])
            return "Notas relevantes: " + ", ".join(f"[[{n}]]" for n in fuentes) + "\n\n" + cuerpo, fuentes
        memoria = "\n\n".join(f"--- [[{f['nota']}]] ---\n{f['texto']}" for _, f in resultados) or "(nada relevante)"
        mensajes = self.historial[-6:] + [{"role": "user", "content": f"MEMORIA:\n{memoria}\n\nPREGUNTA: {pregunta}"}]
        respuesta = generar(mensajes, self.motor, SISTEMA.format(reglas=leer_reglas(self.boveda)))
        self.historial += [{"role": "user", "content": pregunta}, {"role": "assistant", "content": respuesta}]
        self.ultima = {"pregunta": pregunta, "respuesta": respuesta, "fuentes": fuentes}
        self._registrar_conversacion(pregunta, respuesta, fuentes)
        return respuesta, fuentes

    # ------------------------------------------------------------ aprender
    def _registrar_conversacion(self, pregunta: str, respuesta: str, fuentes: list[str]) -> None:
        carpeta = self.boveda / "Memoria" / "Conversaciones"
        carpeta.mkdir(parents=True, exist_ok=True)
        hoy = dt.datetime.now()
        ruta = carpeta / f"{hoy:%Y-%m-%d} Conversaciones con Mi IA.md"
        if not ruta.exists():
            ruta.write_text(f"---\nfecha: {hoy:%Y-%m-%d}\ntipo: conversaciones\ntags: [memoria, conversaciones]\n---\n\n"
                            f"# Conversaciones con Mi IA ({hoy:%Y-%m-%d})\n", encoding="utf-8")
        refs = ", ".join(f"[[{f}]]" for f in fuentes[:4])
        with ruta.open("a", encoding="utf-8") as f:
            f.write(f"\n## {hoy:%H:%M}: {pregunta[:80]}\n**Tú:** {pregunta}\n\n**Mi IA:** {respuesta}\n\n*Fuentes: {refs}*\n")

    def _preferencia(self, valoracion: str, motivo: str = "") -> None:
        DATOS.mkdir(exist_ok=True)
        with (DATOS / "preferencias.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"fecha": dt.datetime.now().isoformat(timespec="seconds"), "motor": self.motor,
                                "valoracion": valoracion, "motivo": motivo, **(self.ultima or {})},
                               ensure_ascii=False) + "\n")

    def agregar_regla(self, tipo: str, texto: str) -> str:
        nombre = "Reglas - Hacer" if tipo == "hacer" else "Reglas - No hacer"
        ruta = self.boveda / "Memoria" / "Lecciones" / f"{nombre}.md"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if not ruta.exists():
            ruta.write_text(f"---\ntipo: reglas\ntags: [memoria, lecciones]\n---\n\n# {nombre}\n", encoding="utf-8")
        with ruta.open("a", encoding="utf-8") as f:
            f.write(f"- {texto.strip()} ({dt.date.today():%Y-%m-%d}, aprendido en uso)\n")
        return nombre

    def bien(self) -> str:
        if not self.ultima:
            return "No hay respuesta que valorar todavía."
        self._preferencia("buena")
        return "👍 Guardado como buen ejemplo."

    def mal(self, motivo: str) -> str:
        if not self.ultima:
            return "No hay respuesta que valorar todavía."
        self._preferencia("mala", motivo)
        if motivo:
            self.agregar_regla("evitar", f"{motivo} (error en: \"{self.ultima['pregunta'][:60]}\")")
            return "👎 Entendido. Lo añadí a [[Reglas - No hacer]] y no lo repetiré."
        return "👎 Guardado. Dime por qué con /mal <motivo> para crear una regla."

    def recordar(self, texto: str, titulo: str | None = None) -> Path:
        carpeta = self.boveda / "Memoria" / "Recuerdos"
        carpeta.mkdir(parents=True, exist_ok=True)
        ahora = dt.datetime.now()
        titulo = titulo or " ".join(texto.split()[:8])
        limpio = re.sub(r'[\\/:*?"<>|#\[\]]', "", titulo).strip()[:80] or "recuerdo"
        ruta = carpeta / f"{ahora:%Y-%m-%d} {limpio}.md"
        ruta.write_text(f"---\nfecha: {ahora:%Y-%m-%d %H:%M}\ntipo: recuerdo\ntags: [memoria]\n---\n\n# {titulo}\n\n"
                        f"{texto}\n\nVer también: [[Memoria - Sobre mí]]\n", encoding="utf-8")
        self.recargar()
        return ruta

    def comando(self, linea: str) -> str | None:
        """Procesa /comandos. Devuelve el texto de respuesta o None si no es un comando."""
        if not linea.startswith("/"):
            return None
        cmd, _, resto = linea.partition(" ")
        resto = resto.strip()
        if cmd == "/recordar" and resto:
            return f"🧠 Aprendido. Guardado en {self.recordar(resto).name}"
        if cmd == "/bien":
            return self.bien()
        if cmd == "/mal":
            return self.mal(resto)
        if cmd in ("/hacer", "/evitar") and resto:
            return f"📏 Regla añadida a [[{self.agregar_regla(cmd[1:], resto)}]]."
        if cmd == "/reglas":
            return leer_reglas(self.boveda)
        return AYUDA


AYUDA = """Comandos:
  /recordar <texto>   enséñame algo nuevo (se guarda en Obsidian)
  /bien               tu última respuesta fue buena
  /mal <por qué>      fue mala: no lo repitas
  /hacer <regla>      algo que siempre debo hacer
  /evitar <regla>     algo que nunca debo hacer
  /reglas             ver mis reglas
  salir"""


# ================================================================== web
PAGINA = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mi IA</title><style>
:root{--bg:#f6f5f2;--card:#fff;--txt:#1d1d1f;--sub:#6b6b70;--acc:#3b5bdb;--yo:#e9edff;--borde:#e3e1dc}
@media(prefers-color-scheme:dark){:root{--bg:#141416;--card:#1e1e22;--txt:#ececf0;--sub:#9a9aa2;--acc:#7c94ff;--yo:#262b45;--borde:#2c2c32}}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--txt);display:flex;flex-direction:column;height:100vh}
header{padding:14px 20px;border-bottom:1px solid var(--borde);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
h1{font-size:18px;margin:0}small{color:var(--sub)}#log{flex:1;overflow:auto;padding:20px;max-width:860px;width:100%;margin:0 auto}
.m{background:var(--card);border:1px solid var(--borde);border-radius:14px;padding:12px 16px;margin:0 0 12px;white-space:pre-wrap;word-wrap:break-word}
.yo{background:var(--yo);margin-left:15%}.f{color:var(--sub);font-size:13px;margin-top:6px}
.acc button{margin:8px 6px 0 0;border:1px solid var(--borde);background:transparent;color:var(--txt);border-radius:8px;padding:4px 10px;cursor:pointer}
form{display:flex;gap:8px;padding:14px 20px;border-top:1px solid var(--borde);max-width:860px;width:100%;margin:0 auto}
textarea{flex:1;resize:none;height:52px;padding:12px;border-radius:12px;border:1px solid var(--borde);background:var(--card);color:var(--txt);font:inherit}
form button{border:0;border-radius:12px;padding:0 18px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer}
</style></head><body>
<header><div><h1>🧠 Mi IA</h1><small id="estado"></small></div><small>/recordar · /bien · /mal &lt;por qué&gt; · /hacer · /evitar · /reglas</small></header>
<div id="log"></div>
<form id="f"><textarea id="q" placeholder="Pregúntame algo o enséñame con /recordar…" autofocus></textarea><button>Enviar</button></form>
<script>
const log=document.getElementById('log'),q=document.getElementById('q');
function add(t,c,fuentes){const d=document.createElement('div');d.className='m '+(c||'');d.textContent=t;
 if(fuentes&&fuentes.length){const f=document.createElement('div');f.className='f';f.textContent='Fuentes: '+fuentes.join(', ');d.appendChild(f)}
 if(c==='ia'){const a=document.createElement('div');a.className='acc';
  for(const [l,cmd] of [['👍 Bien','/bien'],['👎 Mal','/mal']]){const b=document.createElement('button');b.type='button';b.textContent=l;
   b.onclick=()=>{let x=cmd;if(cmd==='/mal'){const r=prompt('¿Qué hizo mal? (se convertirá en una regla)');if(r===null)return;x+=' '+r}enviar(x)};a.appendChild(b)}
  d.appendChild(a)}
 log.appendChild(d);log.scrollTop=log.scrollHeight}
async function enviar(t){add(t,'yo');const r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({texto:t})});
 const j=await r.json();add(j.respuesta,t.startsWith('/')?'':'ia',j.fuentes)}
document.getElementById('f').onsubmit=e=>{e.preventDefault();const t=q.value.trim();if(!t)return;q.value='';enviar(t)};
q.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();document.getElementById('f').requestSubmit()}});
fetch('/estado').then(r=>r.json()).then(j=>document.getElementById('estado').textContent=j.texto);
</script></body></html>"""


def servir(ia: MiIA, puerto: int) -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Manejador(BaseHTTPRequestHandler):
        def _json(self, datos: dict) -> None:
            cuerpo = json.dumps(datos, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_GET(self):
            if self.path == "/estado":
                notas = len({f["nota"] for f in ia.buscador.frags})
                return self._json({"texto": f"{notas} notas en memoria · motor: {ia.motor}"})
            cuerpo = PAGINA.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_POST(self):
            datos = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            texto = str(datos.get("texto", "")).strip()
            r = ia.comando(texto)
            if r is not None:
                return self._json({"respuesta": r, "fuentes": []})
            respuesta, fuentes = ia.preguntar(texto)
            self._json({"respuesta": respuesta, "fuentes": fuentes})

        def log_message(self, *a):
            pass

    print(f"Mi IA en http://localhost:{puerto}  (Ctrl+C para cerrar)")
    ThreadingHTTPServer(("127.0.0.1", puerto), Manejador).serve_forever()


# ================================================================== CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="Mi IA: asistente con memoria en Obsidian")
    ap.add_argument("--motor", choices=["ollama", "anthropic", "propia", "ninguno"],
                    default=os.environ.get("MI_IA_MOTOR", "ollama"))
    ap.add_argument("--boveda", type=Path, default=BOVEDA)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preguntar").add_argument("texto")
    sub.add_parser("buscar").add_argument("texto")
    r = sub.add_parser("recordar")
    r.add_argument("texto")
    r.add_argument("--titulo")
    sub.add_parser("chat")
    sub.add_parser("estado")
    w = sub.add_parser("web")
    w.add_argument("--puerto", type=int, default=8765)
    a = ap.parse_args()

    if not a.boveda.exists():
        sys.exit(f"No encuentro la bóveda en {a.boveda}. Usa --boveda o MI_IA_BOVEDA.")
    motor = "ninguno" if a.cmd in ("buscar", "recordar") else a.motor
    ia = MiIA(a.boveda, motor)

    if a.cmd == "recordar":
        print(f"Guardado en {ia.recordar(a.texto, a.titulo)}")
    elif a.cmd == "estado":
        notas = {f["nota"] for f in ia.buscador.frags}
        print(f"Bóveda: {a.boveda}\nNotas: {len(notas)}  Fragmentos: {len(ia.buscador.frags)}  Motor: {a.motor}\n")
        print(leer_reglas(a.boveda))
    elif a.cmd in ("buscar", "preguntar"):
        respuesta, _ = ia.preguntar(a.texto)
        print(respuesta)
    elif a.cmd == "web":
        servir(ia, a.puerto)
    elif a.cmd == "chat":
        print("🧠 Mi IA lista. Escribe tu pregunta, /ayuda para ver comandos, o 'salir'.")
        while True:
            try:
                q = input("\nTú: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q.lower() in {"salir", "exit", "quit"}:
                break
            if not q:
                continue
            r = ia.comando(q)
            if r is None:
                r, fuentes = ia.preguntar(q)
                if fuentes:
                    r += "\n   (fuentes: " + ", ".join(fuentes[:4]) + ")"
            print(f"\nMi IA: {r}")


if __name__ == "__main__":
    main()
