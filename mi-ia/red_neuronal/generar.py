#!/usr/bin/env python3
"""Hace hablar a tu red neuronal: continúa el texto que le des.

  python mi-ia/red_neuronal/generar.py "La tokenización"
  python mi-ia/red_neuronal/generar.py "# Clase 18" --tokens 300 --temperatura 0.7
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch

from modelo import MiniGPT, TokenizadorBPE

PESOS = Path(__file__).resolve().parent / "pesos"


def cargar():
    tok = TokenizadorBPE.cargar(PESOS / "tokenizador.json")
    ck = torch.load(PESOS / "mi_red.pt", map_location="cpu")
    modelo = MiniGPT(**ck["config"])
    modelo.load_state_dict(ck["estado"])
    return tok, modelo


def continuar(texto: str, tokens: int = 200, temperatura: float = 0.8) -> str:
    tok, modelo = cargar()
    ids = torch.tensor([tok.codificar(texto) or [32]], dtype=torch.long)
    salida = modelo.generar(ids, max_nuevos=tokens, temperatura=temperatura)
    return tok.decodificar(salida[0].tolist())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("texto")
    ap.add_argument("--tokens", type=int, default=200)
    ap.add_argument("--temperatura", type=float, default=0.8)
    a = ap.parse_args()
    torch.manual_seed(0)
    print(continuar(a.texto, a.tokens, a.temperatura))
