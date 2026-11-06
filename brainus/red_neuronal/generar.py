#!/usr/bin/env python3
"""Haz hablar a la red neuronal de Brainus: continúa el texto que le des.

  python brainus/red_neuronal/generar.py "La tokenización"
  python brainus/red_neuronal/generar.py "## Leyes de escala" --tokens 300 --temperatura 0.7 --top-p 0.9
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path

import torch

from modelo import TransformerLM
from tokenizador import FIN, Tokenizador

PESOS = Path(__file__).resolve().parent / "pesos"


@lru_cache(maxsize=1)
def cargar() -> tuple[Tokenizador, TransformerLM]:
    tok = Tokenizador.cargar(PESOS / "tokenizador.json")
    ck = torch.load(PESOS / "brainus.pt", map_location="cpu", weights_only=False)
    modelo = TransformerLM(**ck["config"])
    modelo.load_state_dict(ck["modelo"])
    return tok, modelo


def continuar(texto: str, tokens: int = 200, temperatura: float = 0.8, top_p: float = 0.9) -> str:
    tok, modelo = cargar()
    ids = modelo.generar(tok.encode(texto), max_nuevos=tokens, temperatura=temperatura, top_p=top_p,
                         fin=tok.id_especial(FIN))
    return tok.decode(ids).replace(FIN, "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("texto")
    ap.add_argument("--tokens", type=int, default=200)
    ap.add_argument("--temperatura", type=float, default=0.8)
    ap.add_argument("--top-p", type=float, default=0.9)
    a = ap.parse_args()
    torch.manual_seed(0)
    print(continuar(a.texto, a.tokens, a.temperatura, a.top_p))
