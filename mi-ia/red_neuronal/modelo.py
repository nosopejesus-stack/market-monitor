"""Mi red neuronal: un modelo de lenguaje pequeño construido desde cero, como en CS336.

Piezas (ver las notas de la bóveda):
  - Tokenizador BPE a nivel de bytes ............ [[Clase 01 - Panorama y tokenización]]
  - Transformer moderno: pre-norm RMSNorm, RoPE,
    SwiGLU, sin bias, atención causal ............. [[Clase 03 - Arquitecturas]]
  - Entrenamiento con AdamW + warmup y coseno .... [[Clase 02 - PyTorch, einops y contabilidad de recursos]]

Solo necesita PyTorch.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import regex as re_u  # admite clases Unicode (\p{L}); pip install regex
import torch
import torch.nn as nn
import torch.nn.functional as F

# Pre-tokenización estilo GPT-2: separa palabras, números, puntuación y espacios.
PATRON = re_u.compile(r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")


# ======================================================================= BPE
class TokenizadorBPE:
    """BPE a nivel de bytes: empieza con 256 bytes y fusiona los pares más frecuentes."""

    def __init__(self, fusiones: list[tuple[int, int]] | None = None):
        self.fusiones = [tuple(f) for f in (fusiones or [])]
        self.rango = {par: i for i, par in enumerate(self.fusiones)}
        self.vocab = {i: bytes([i]) for i in range(256)}
        for i, (a, b) in enumerate(self.fusiones):
            self.vocab[256 + i] = self.vocab[a] + self.vocab[b]
        self._cache: dict[str, list[int]] = {}

    @property
    def tam_vocab(self) -> int:
        return 256 + len(self.fusiones)

    @classmethod
    def entrenar(cls, texto: str, tam_vocab: int) -> "TokenizadorBPE":
        palabras = Counter(PATRON.findall(texto))
        secuencias = {p: list(p.encode("utf-8")) for p in palabras}
        fusiones: list[tuple[int, int]] = []
        for nuevo in range(256, tam_vocab):
            pares: Counter = Counter()
            for p, cuenta in palabras.items():
                s = secuencias[p]
                for a, b in zip(s, s[1:]):
                    pares[(a, b)] += cuenta
            if not pares:
                break
            mejor = max(pares, key=pares.get)
            if pares[mejor] < 2:
                break
            fusiones.append(mejor)
            for p in palabras:
                s = secuencias[p]
                i, out = 0, []
                while i < len(s):
                    if i + 1 < len(s) and (s[i], s[i + 1]) == mejor:
                        out.append(nuevo)
                        i += 2
                    else:
                        out.append(s[i])
                        i += 1
                secuencias[p] = out
        return cls(fusiones)

    def _codificar_palabra(self, palabra: str) -> list[int]:
        if palabra in self._cache:
            return self._cache[palabra]
        s = list(palabra.encode("utf-8"))
        while len(s) > 1:
            par = min(zip(s, s[1:]), key=lambda p: self.rango.get(p, 1 << 30))
            if par not in self.rango:
                break
            nuevo = 256 + self.rango[par]
            i, out = 0, []
            while i < len(s):
                if i + 1 < len(s) and (s[i], s[i + 1]) == par:
                    out.append(nuevo)
                    i += 2
                else:
                    out.append(s[i])
                    i += 1
            s = out
        self._cache[palabra] = s
        return s

    def codificar(self, texto: str) -> list[int]:
        return [t for p in PATRON.findall(texto) for t in self._codificar_palabra(p)]

    def decodificar(self, ids: list[int]) -> str:
        return b"".join(self.vocab[i] for i in ids).decode("utf-8", errors="replace")

    def guardar(self, ruta: Path) -> None:
        ruta.write_text(json.dumps({"fusiones": self.fusiones}), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta: Path) -> "TokenizadorBPE":
        return cls(json.loads(ruta.read_text(encoding="utf-8"))["fusiones"])


# =============================================================== Transformer
class RMSNorm(nn.Module):
    def __init__(self, d: int, eps: float = 1e-5):
        super().__init__()
        self.peso = nn.Parameter(torch.ones(d))
        self.eps = eps

    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.peso


def rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Rota pares de coordenadas según la posición (solo depende de la posición relativa)."""
    x1, x2 = x[..., 0::2], x[..., 1::2]
    return torch.stack((x1 * cos - x2 * sin, x1 * sin + x2 * cos), dim=-1).flatten(-2)


class Atencion(nn.Module):
    def __init__(self, d: int, cabezas: int):
        super().__init__()
        self.h, self.dh = cabezas, d // cabezas
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.salida = nn.Linear(d, d, bias=False)

    def forward(self, x, cos, sin):
        B, T, D = x.shape
        q, k, v = self.qkv(x).view(B, T, 3, self.h, self.dh).permute(2, 0, 3, 1, 4)
        q, k = rope(q, cos, sin), rope(k, cos, sin)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)  # FlashAttention cuando hay GPU
        return self.salida(y.transpose(1, 2).reshape(B, T, D))


class SwiGLU(nn.Module):
    def __init__(self, d: int):
        super().__init__()
        dff = int(8 * d / 3 / 64 + 0.999) * 64  # d_ff ≈ 8/3·d, redondeado a múltiplo de 64
        self.w1 = nn.Linear(d, dff, bias=False)
        self.w3 = nn.Linear(d, dff, bias=False)
        self.w2 = nn.Linear(dff, d, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class Bloque(nn.Module):
    def __init__(self, d: int, cabezas: int):
        super().__init__()
        self.n1, self.att = RMSNorm(d), Atencion(d, cabezas)
        self.n2, self.ff = RMSNorm(d), SwiGLU(d)

    def forward(self, x, cos, sin):
        x = x + self.att(self.n1(x), cos, sin)  # pre-norm: la norma no toca el camino residual
        return x + self.ff(self.n2(x))


class MiniGPT(nn.Module):
    def __init__(self, vocab: int, d: int = 256, capas: int = 6, cabezas: int = 8, contexto: int = 256):
        super().__init__()
        self.config = dict(vocab=vocab, d=d, capas=capas, cabezas=cabezas, contexto=contexto)
        self.emb = nn.Embedding(vocab, d)
        self.bloques = nn.ModuleList(Bloque(d, cabezas) for _ in range(capas))
        self.norma = RMSNorm(d)
        self.cabeza = nn.Linear(d, vocab, bias=False)
        self.cabeza.weight = self.emb.weight  # pesos compartidos entrada/salida
        dh = d // cabezas
        frec = 1.0 / (10000 ** (torch.arange(0, dh, 2).float() / dh))
        ang = torch.outer(torch.arange(contexto).float(), frec)
        self.register_buffer("cos", ang.cos(), persistent=False)
        self.register_buffer("sin", ang.sin(), persistent=False)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)

    def forward(self, ids, objetivos=None):
        T = ids.shape[1]
        x = self.emb(ids)
        cos, sin = self.cos[:T], self.sin[:T]
        for b in self.bloques:
            x = b(x, cos, sin)
        logits = self.cabeza(self.norma(x))
        perdida = None
        if objetivos is not None:
            perdida = F.cross_entropy(logits.view(-1, logits.size(-1)), objetivos.view(-1))
        return logits, perdida

    def num_parametros(self) -> int:
        return sum(p.numel() for p in self.parameters())

    @torch.no_grad()
    def generar(self, ids: torch.Tensor, max_nuevos: int = 200, temperatura: float = 0.8, top_k: int = 40) -> torch.Tensor:
        self.eval()
        for _ in range(max_nuevos):
            ventana = ids[:, -self.config["contexto"] :]
            logits, _ = self(ventana)
            logits = logits[:, -1, :] / max(temperatura, 1e-5)
            if top_k:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float("inf")
            siguiente = torch.multinomial(F.softmax(logits, dim=-1), 1)
            ids = torch.cat([ids, siguiente], dim=1)
        return ids


def lr_coseno(paso: int, total: int, maximo: float, calentamiento: int) -> float:
    if paso < calentamiento:
        return maximo * (paso + 1) / calentamiento
    progreso = (paso - calentamiento) / max(1, total - calentamiento)
    return maximo * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * progreso)))
