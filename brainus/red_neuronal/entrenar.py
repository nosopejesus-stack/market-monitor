#!/usr/bin/env python3
"""Entrena la red neuronal de Brainus con tu bóveda de Obsidian (y texto general en español).

Receta de CS336 en dos fases:
  1. PREENTRENAMIENTO: mucho texto general (Wikipedia) → aprende el idioma.
  2. MID-TRAINING (--continuar): tu bóveda mezclada con algo de texto general → aprende
     lo tuyo sin olvidar el español. Siempre se guarda la MEJOR versión (validación).

Tamaños (--perfil):
  pequeno   ~ 14M parámetros  CPU, ~40 min            (el que viene entrenado)
  medio     ~ 45M parámetros  CPU potente o GPU
  potente   ~ 125M parámetros (tamaño GPT-2 small); necesita GPU NVIDIA o Mac M-series y horas
Ejemplos:
  python brainus/red_neuronal/entrenar.py --continuar                       # aprende tus notas nuevas
  python brainus/red_neuronal/descargar_corpus.py --mb 200                  # más texto general
  python brainus/red_neuronal/entrenar.py --perfil potente --minutos 240    # tu Brainus grande (GPU)
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from entrenamiento import AdamW, cross_entropy, guardar_checkpoint, lr_coseno, obtener_lote, recortar_gradientes
from modelo import TransformerLM
from tokenizador import FIN, Tokenizador, entrenar_bpe

AQUI = Path(__file__).resolve().parent
PESOS = AQUI / "pesos"
CORPUS = AQUI / "corpus"
PERFILES = {
    "pequeno": dict(d_model=384, num_layers=6, num_heads=6, context_length=256, vocab=4096, lote=16),
    "medio": dict(d_model=512, num_layers=8, num_heads=8, context_length=512, vocab=8192, lote=16),
    "potente": dict(d_model=768, num_layers=12, num_heads=12, context_length=1024, vocab=16384, lote=16),
}


def leer_boveda(boveda: Path) -> str:
    textos = []
    for ruta in sorted(boveda.rglob("*.md")):
        rel = ruta.relative_to(boveda)
        if any(p.startswith(".") for p in rel.parts) or "Conversaciones" in rel.parts:
            continue
        textos.append(ruta.read_text(encoding="utf-8", errors="ignore"))
    return FIN.join(textos) + FIN


def leer_corpus(carpeta: Path) -> str:
    partes = []
    descargados = list(carpeta.glob("es_wiki_*mb.txt.gz"))
    for ruta in sorted(carpeta.glob("*")):
        if descargados and ruta.name == "es_wiki_muestra.txt.gz":
            continue  # la muestra ya está dentro del corpus descargado: no duplicar (Clase 14)
        if ruta.suffix == ".gz":
            partes.append(gzip.decompress(ruta.read_bytes()).decode("utf-8", errors="ignore"))
        elif ruta.suffix in (".txt",) and ruta.name != "LEEME.txt":
            partes.append(ruta.read_text(encoding="utf-8", errors="ignore"))
    return FIN.join(partes)


def dispositivo() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def tokens_a_array(tok: Tokenizador, texto: str) -> np.ndarray:
    tipo = np.uint16 if tok.tam_vocab < 65536 else np.int32
    return np.array(tok.encode(texto), dtype=tipo)


def main() -> None:
    ap = argparse.ArgumentParser(description="Entrena la red neuronal de Brainus")
    ap.add_argument("--boveda", type=Path, default=AQUI.parent.parent / "vault")
    ap.add_argument("--perfil", choices=PERFILES, default="pequeno")
    ap.add_argument("--minutos", type=float, default=None, help="tiempo de entrenamiento")
    ap.add_argument("--continuar", action="store_true", help="mid-training desde los pesos guardados")
    ap.add_argument("--reanudar", action="store_true", help="seguir PREentrenando (texto general + bóveda) desde los pesos")
    ap.add_argument("--mezcla", type=float, default=3.0, help="--continuar: texto general = mezcla × bóveda")
    ap.add_argument("--repetir", type=int, default=2, help="--continuar: veces que se repite la bóveda")
    ap.add_argument("--lr", type=float, default=None)
    a = ap.parse_args()

    torch.manual_seed(0)
    np.random.seed(0)
    PESOS.mkdir(exist_ok=True)
    dev = dispositivo()
    ruta_tok, ruta_modelo = PESOS / "tokenizador.json", PESOS / "brainus.pt"
    boveda = leer_boveda(a.boveda)
    general = leer_corpus(CORPUS) if CORPUS.exists() else ""
    print(f"Bóveda: {len(boveda):,} caracteres · texto general: {len(general):,} · dispositivo: {dev}")

    texto_valid = ""
    if a.continuar or a.reanudar:
        if not ruta_modelo.exists():
            raise SystemExit("No hay pesos guardados. Entrena primero sin --continuar.")
        tok = Tokenizador.cargar(ruta_tok)
        ck = torch.load(ruta_modelo, map_location="cpu", weights_only=False)
        modelo = TransformerLM(**ck["config"])
        modelo.load_state_dict(ck["modelo"])
        perfil = ck.get("perfil", "?")
        if a.reanudar:
            texto = general + FIN + boveda
            lr_max = a.lr or 5e-4
            minutos = a.minutos or 20
            print("Reanudando el preentrenamiento desde los pesos guardados.")
        else:
            # Validación = notas tuyas APARTADAS + algo de texto general: la mejor versión es la que
            # aprende lo tuyo sin olvidar el español (si solo se midiera Wikipedia, no aprendería tus notas).
            notas = boveda.split(FIN)
            apartadas = notas[::10]  # 1 de cada 10 notas no se usa para entrenar
            entreno_notas = [n for i, n in enumerate(notas) if i % 10]
            bov_val = FIN.join(apartadas)
            n_mezcla = int(len(boveda) * a.mezcla)
            texto = FIN.join(entreno_notas) * a.repetir + FIN + general[:n_mezcla]
            texto_valid = bov_val + FIN + general[n_mezcla : n_mezcla + len(bov_val)]
            lr_max = a.lr or 3e-4
            minutos = a.minutos or 3
            print("Mid-training: aprendiendo la bóveda desde los pesos guardados.")
    else:
        p = PERFILES[a.perfil]
        t0 = time.time()
        muestra = boveda + FIN + general[:3_000_000]  # el BPE se entrena con una muestra
        vocab, fusiones = entrenar_bpe(muestra, p["vocab"], [FIN])
        tok = Tokenizador(vocab, fusiones, [FIN])
        tok.guardar(ruta_tok)
        print(f"Tokenizador BPE: {tok.tam_vocab} tokens ({time.time() - t0:.0f}s)")
        modelo = TransformerLM(tok.tam_vocab, p["context_length"], p["d_model"], p["num_layers"], p["num_heads"])
        texto = general + FIN + boveda
        lr_max = a.lr or (1e-3 if a.perfil == "pequeno" else 6e-4)
        minutos = a.minutos or 15
        perfil = a.perfil

    t0 = time.time()
    datos = tokens_a_array(tok, texto)
    if texto_valid:
        entreno, valid = datos, tokens_a_array(tok, texto_valid)
    else:
        corte = int(len(datos) * 0.95)
        entreno, valid = datos[:corte], datos[corte:]
    ctx = modelo.config["context_length"]
    lote = PERFILES.get(perfil, PERFILES["pequeno"])["lote"]
    print(f"Tokens: {len(datos):,} ({len(texto.encode()) / max(1, len(datos)):.2f} bytes/token, "
          f"{time.time() - t0:.0f}s) · parámetros: {modelo.num_parametros():,}")

    modelo.to(dev)
    con_decay = [p for p in modelo.parameters() if p.dim() >= 2]
    sin_decay = [p for p in modelo.parameters() if p.dim() < 2]
    opt = AdamW([{"params": con_decay, "weight_decay": 0.1}, {"params": sin_decay, "weight_decay": 0.0}],
                lr=lr_max, betas=(0.9, 0.95), eps=1e-8)

    @torch.no_grad()
    def evaluar(n: int = 8) -> float:
        modelo.eval()
        v = sum(cross_entropy(modelo(x), y).item() for x, y in (obtener_lote(valid, lote, ctx, dev) for _ in range(n))) / n
        modelo.train()
        return v

    # medir cuántos pasos caben en el tiempo pedido
    modelo.train()
    t0 = time.time()
    for _ in range(3):
        x, y = obtener_lote(entreno, lote, ctx, dev)
        cross_entropy(modelo(x), y).backward()
        opt.zero_grad(set_to_none=True)
    total = max(30, int(minutos * 60 / ((time.time() - t0) / 3) * 0.9))
    calentamiento = max(10, total // 20)
    print(f"Entrenando {total} pasos (~{minutos:.0f} min). Pérdida al azar ≈ {math.log(tok.tam_vocab):.2f}")

    mejor, mejor_estado, inicio = float("inf"), None, time.time()
    cada = max(1, total // 12)
    for paso in range(total):
        lr = lr_coseno(paso, lr_max, lr_max / 10, calentamiento, total)
        for g in opt.param_groups:
            g["lr"] = lr
        x, y = obtener_lote(entreno, lote, ctx, dev)
        perdida = cross_entropy(modelo(x), y)
        opt.zero_grad(set_to_none=True)
        perdida.backward()
        recortar_gradientes(modelo.parameters(), 1.0)
        opt.step()
        if paso % cada == 0 or paso == total - 1:
            v = evaluar()
            if v < mejor:
                mejor, mejor_estado = v, copy.deepcopy(modelo.state_dict())
            print(f"  paso {paso:6d}/{total}  pérdida {perdida.item():.3f}  validación {v:.3f}  lr {lr:.1e}  "
                  f"({time.time() - inicio:.0f}s)", flush=True)

    modelo.load_state_dict(mejor_estado)
    modelo.to("cpu")
    # Se guarda en bfloat16: la mitad de espacio y casi la misma calidad (Clase 02). Al cargar se pasa a float32.
    estado_bf16 = {k: v.to(torch.bfloat16) for k, v in modelo.state_dict().items()}
    torch.save({"modelo": estado_bf16, "optimizador": None, "iteracion": total, "config": modelo.config,
                "perfil": perfil}, ruta_modelo)
    bytes_por_token = len(texto.encode()) / max(1, len(datos))
    bpb = mejor / math.log(2) / bytes_por_token  # bits por byte: comparable entre tokenizadores distintos
    fase = "mid-training" if a.continuar else ("preentrenamiento (reanudado)" if a.reanudar else "preentrenamiento")
    info = {"fecha": time.strftime("%Y-%m-%d %H:%M"), "perfil": perfil, "fase": fase, "bits_por_byte": round(bpb, 3), "parametros": modelo.num_parametros(), "tokens": int(len(datos)), "pasos": total,
            "mejor_validacion": round(mejor, 3), "perplejidad": round(math.exp(mejor), 1)}
    historial = PESOS / "historial.json"
    registros = json.loads(historial.read_text()) if historial.exists() else []
    historial.write_text(json.dumps(registros + [info], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado en {ruta_modelo} · mejor validación {mejor:.3f} (perplejidad {math.exp(mejor):.1f}, "
          f"{bpb:.3f} bits/byte)")


if __name__ == "__main__":
    main()
