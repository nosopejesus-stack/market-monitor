#!/usr/bin/env python3
"""Entrena (o re-entrena) tu red neuronal con todo lo que hay en la bóveda de Obsidian.

  python mi-ia/red_neuronal/entrenar.py                 # entrena desde cero
  python mi-ia/red_neuronal/entrenar.py --continuar     # sigue aprendiendo con las notas nuevas
  python mi-ia/red_neuronal/entrenar.py --minutos 30    # entrena más tiempo (mejor resultado)

Cuanto más escribas en la bóveda, más aprende. Con GPU (CUDA o Apple MPS) va mucho más rápido.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import math
import time
from pathlib import Path

import torch

from modelo import MiniGPT, TokenizadorBPE, lr_coseno

AQUI = Path(__file__).resolve().parent
PESOS = AQUI / "pesos"


def leer_boveda(boveda: Path) -> str:
    textos = []
    for ruta in sorted(boveda.rglob("*.md")):
        if any(p.startswith(".") for p in ruta.relative_to(boveda).parts):
            continue
        textos.append(ruta.read_text(encoding="utf-8", errors="ignore"))
    return "\n\n<|fin|>\n\n".join(textos)


def dispositivo() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boveda", type=Path, default=AQUI.parent.parent / "vault")
    ap.add_argument("--extra", type=Path, nargs="*", default=[], help="carpetas extra con .md, .txt o .txt.gz (por defecto: red_neuronal/corpus)")
    ap.add_argument("--minutos", type=float, default=8.0)
    ap.add_argument("--vocab", type=int, default=1024)
    ap.add_argument("--d", type=int, default=256)
    ap.add_argument("--capas", type=int, default=6)
    ap.add_argument("--contexto", type=int, default=256)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=None, help="por defecto 1e-3 (desde cero) o 3e-4 (--continuar)")
    ap.add_argument("--continuar", action="store_true")
    ap.add_argument("--mezcla", type=float, default=1.0, help="con --continuar: texto extra = mezcla × tamaño de la bóveda")
    ap.add_argument("--repetir", type=int, default=3, help="con --continuar y --extra: veces que se repite la bóveda")
    a = ap.parse_args()

    torch.manual_seed(0)
    if a.lr is None:
        a.lr = 3e-4 if a.continuar else 1e-3
    boveda = leer_boveda(a.boveda)
    extra = ""
    carpetas = a.extra or ([AQUI / "corpus"] if (AQUI / "corpus").exists() else [])
    for carpeta in carpetas:
        for ruta in sorted(list(carpeta.rglob("*.md")) + list(carpeta.rglob("*.txt"))):
            extra += "\n\n" + ruta.read_text(encoding="utf-8", errors="ignore")
        for ruta in sorted(carpeta.rglob("*.txt.gz")):
            extra += "\n\n" + gzip.decompress(ruta.read_bytes()).decode("utf-8", errors="ignore")
    if a.continuar and extra:
        # Mid-training: sobre todo la bóveda, con un poco de texto general para no olvidar (Clase 14)
        extra = extra[: int(len(boveda) * a.mezcla)]
        boveda = boveda * a.repetir
    texto = boveda + extra
    print(f"Texto de entrenamiento: {len(texto):,} caracteres (bóveda {len(boveda):,})")

    PESOS.mkdir(exist_ok=True)
    ruta_tok, ruta_modelo = PESOS / "tokenizador.json", PESOS / "mi_red.pt"
    dev = dispositivo()

    if a.continuar and ruta_modelo.exists():
        tok = TokenizadorBPE.cargar(ruta_tok)
        ck = torch.load(ruta_modelo, map_location="cpu")
        modelo = MiniGPT(**ck["config"])
        modelo.load_state_dict(ck["estado"])
        print("Continuando desde los pesos guardados.")
    else:
        t0 = time.time()
        tok = TokenizadorBPE.entrenar(boveda + extra[:2_000_000], a.vocab)  # una muestra basta para el BPE
        tok.guardar(ruta_tok)
        print(f"Tokenizador BPE: {tok.tam_vocab} tokens ({time.time() - t0:.0f}s)")
        modelo = MiniGPT(tok.tam_vocab, d=a.d, capas=a.capas, cabezas=max(1, a.d // 32), contexto=a.contexto)

    datos = torch.tensor(tok.codificar(texto), dtype=torch.long)
    corte = int(len(datos) * 0.95)
    entreno, valid = datos[:corte], datos[corte:]
    ctx = modelo.config["contexto"]
    print(f"Tokens: {len(datos):,} (compresión {len(texto.encode()) / len(datos):.2f} bytes/token)")
    print(f"Parámetros: {modelo.num_parametros():,}  Dispositivo: {dev}")

    modelo.to(dev)
    decay = [p for p in modelo.parameters() if p.dim() >= 2]
    sin_decay = [p for p in modelo.parameters() if p.dim() < 2]
    opt = torch.optim.AdamW([{"params": decay, "weight_decay": 0.1}, {"params": sin_decay, "weight_decay": 0.0}],
                            lr=a.lr, betas=(0.9, 0.95))

    def lote(fuente):
        i = torch.randint(0, len(fuente) - ctx - 1, (a.batch,))
        x = torch.stack([fuente[j : j + ctx] for j in i]).to(dev)
        y = torch.stack([fuente[j + 1 : j + ctx + 1] for j in i]).to(dev)
        return x, y

    @torch.no_grad()
    def evaluar() -> float:
        modelo.eval()
        perdidas = [modelo(*lote(valid))[1].item() for _ in range(10)]
        modelo.train()
        return sum(perdidas) / len(perdidas)

    # estimar pasos que caben en el tiempo pedido
    modelo.train()
    t0 = time.time()
    for _ in range(3):
        _, p = modelo(*lote(entreno))
        p.backward()
        opt.zero_grad(set_to_none=True)
    por_paso = (time.time() - t0) / 3
    total = max(50, int(a.minutos * 60 / por_paso))
    print(f"Entrenando {total} pasos (~{a.minutos:.0f} min). Pérdida inicial (azar) ≈ {math.log(tok.tam_vocab):.2f}")

    inicio = time.time()
    mejor, mejor_estado = float("inf"), None
    for paso in range(total):
        for g in opt.param_groups:
            g["lr"] = lr_coseno(paso, total, a.lr, calentamiento=min(100, total // 10))
        _, perdida = modelo(*lote(entreno))
        perdida.backward()
        torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
        opt.step()
        opt.zero_grad(set_to_none=True)
        if paso % max(1, total // 10) == 0 or paso == total - 1:
            v = evaluar()
            if v < mejor:  # guardar la mejor versión: si empieza a sobreajustar, nos quedamos con esta
                mejor, mejor_estado = v, copy.deepcopy(modelo.state_dict())
            print(f"  paso {paso:5d}/{total}  pérdida {perdida.item():.3f}  validación {v:.3f}  "
                  f"({time.time() - inicio:.0f}s)", flush=True)
    if mejor_estado is not None:
        modelo.load_state_dict(mejor_estado)
        print(f"Me quedo con la mejor versión (validación {mejor:.3f}).")

    modelo.to("cpu")
    torch.save({"config": modelo.config, "estado": modelo.state_dict()}, ruta_modelo)
    (PESOS / "info.json").write_text(json.dumps({
        "fecha": time.strftime("%Y-%m-%d %H:%M"), "caracteres": len(texto), "tokens": len(datos),
        "parametros": modelo.num_parametros(), "pasos": total, "validacion": round(evaluar_cpu(modelo, valid, ctx), 3),
    }, indent=2), encoding="utf-8")
    print(f"Guardado en {ruta_modelo}")


@torch.no_grad()
def evaluar_cpu(modelo: MiniGPT, valid: torch.Tensor, ctx: int) -> float:
    modelo.eval()
    n = (len(valid) - 1) // ctx
    if n == 0:
        return float("nan")
    x = valid[: n * ctx].view(n, ctx)
    y = valid[1 : n * ctx + 1].view(n, ctx)
    return modelo(x, y)[1].item()


if __name__ == "__main__":
    main()
