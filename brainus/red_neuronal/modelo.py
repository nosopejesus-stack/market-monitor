"""Brainus: el modelo de lenguaje, escrito desde cero siguiendo CS336 (tarea 1, "Basics").

Todo está programado a mano con operaciones básicas de PyTorch (multiplicaciones, exp, sumas):
no se usan nn.Linear, nn.Embedding, F.softmax, F.scaled_dot_product_attention ni similares.

Piezas, en el orden del curso ([[Clase 03 - Arquitecturas]]):
  Linear, Embedding ............... capas básicas sin bias, inicialización normal truncada
  RMSNorm ......................... normalización (en float32 para estabilidad)
  SwiGLU (con SiLU) ............... red feed-forward con compuerta
  softmax, atención escalada ...... con máscara causal
  RoPE ............................ posiciones por rotación
  Atención multi-cabeza ........... Q, K y V en una sola multiplicación
  Bloque Transformer (pre-norm) ... x + Atención(Norma(x)); x + FFN(Norma(x))
  TransformerLM ................... embeddings → N bloques → norma final → lm_head
"""
from __future__ import annotations

import math

import torch
from torch import Tensor, nn


def _normal_truncada(t: Tensor, std: float) -> Tensor:
    return nn.init.trunc_normal_(t, mean=0.0, std=std, a=-3 * std, b=3 * std)


class Linear(nn.Module):
    """y = x Wᵀ, sin bias. W ~ N(0, 2/(d_in+d_out)) truncada a ±3σ."""

    def __init__(self, d_in: int, d_out: int, device=None, dtype=None):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(d_out, d_in, device=device, dtype=dtype))
        _normal_truncada(self.weight, math.sqrt(2.0 / (d_in + d_out)))

    def forward(self, x: Tensor) -> Tensor:
        return x @ self.weight.T


class Embedding(nn.Module):
    """Tabla de vectores: devuelve la fila de cada id. W ~ N(0, 1) truncada a ±3."""

    def __init__(self, num_embeddings: int, embedding_dim: int, device=None, dtype=None):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(num_embeddings, embedding_dim, device=device, dtype=dtype))
        _normal_truncada(self.weight, 1.0)

    def forward(self, ids: Tensor) -> Tensor:
        return self.weight[ids]


class RMSNorm(nn.Module):
    """x / sqrt(media(x²) + eps) · g. Se calcula en float32 y se vuelve al tipo original."""

    def __init__(self, d_model: int, eps: float = 1e-5, device=None, dtype=None):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model, device=device, dtype=dtype))

    def forward(self, x: Tensor) -> Tensor:
        tipo = x.dtype
        x = x.to(torch.float32)
        rms = torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return (x / rms * self.weight).to(tipo)


def silu(x: Tensor) -> Tensor:
    return x * torch.sigmoid(x)


class SwiGLU(nn.Module):
    """FFN(x) = W2 (SiLU(W1 x) ⊙ W3 x)."""

    def __init__(self, d_model: int, d_ff: int, device=None, dtype=None):
        super().__init__()
        self.w1 = Linear(d_model, d_ff, device, dtype)
        self.w2 = Linear(d_ff, d_model, device, dtype)
        self.w3 = Linear(d_model, d_ff, device, dtype)

    def forward(self, x: Tensor) -> Tensor:
        return self.w2(silu(self.w1(x)) * self.w3(x))


def d_ff_por_defecto(d_model: int) -> int:
    """≈ 8/3 · d_model, redondeado a múltiplo de 64 (eficiente en hardware)."""
    return 64 * math.ceil(8 * d_model / 3 / 64)


def softmax(x: Tensor, dim: int) -> Tensor:
    """Softmax estable: se resta el máximo antes de exponenciar para no desbordar."""
    x = x - x.amax(dim=dim, keepdim=True)
    e = torch.exp(x)
    return e / e.sum(dim=dim, keepdim=True)


def atencion_escalada(Q: Tensor, K: Tensor, V: Tensor, mascara: Tensor | None = None) -> Tensor:
    """softmax(Q Kᵀ / √d_k) V. `mascara` True = se puede mirar; False = prohibido."""
    puntos = Q @ K.transpose(-2, -1) / math.sqrt(Q.shape[-1])
    if mascara is not None:
        puntos = puntos.masked_fill(~mascara, float("-inf"))
    return softmax(puntos, dim=-1) @ V


class RoPE(nn.Module):
    """Rotary Position Embedding: rota cada par (x_2k, x_2k+1) un ángulo pos · θ^(-2k/d)."""

    def __init__(self, theta: float, d_k: int, max_seq_len: int, device=None):
        super().__init__()
        assert d_k % 2 == 0, "d_k debe ser par para RoPE"
        frec = theta ** (-torch.arange(0, d_k, 2, device=device, dtype=torch.float32) / d_k)
        angulos = torch.arange(max_seq_len, device=device, dtype=torch.float32)[:, None] * frec[None, :]
        self.register_buffer("cos", angulos.cos(), persistent=False)
        self.register_buffer("sin", angulos.sin(), persistent=False)

    def forward(self, x: Tensor, posiciones: Tensor) -> Tensor:
        cos, sin = self.cos[posiciones], self.sin[posiciones]  # (..., seq, d_k/2)
        par, impar = x[..., 0::2], x[..., 1::2]
        rot_par = par * cos - impar * sin
        rot_impar = par * sin + impar * cos
        return torch.stack((rot_par, rot_impar), dim=-1).flatten(-2).to(x.dtype)


class AtencionMultiCabeza(nn.Module):
    """Atención causal multi-cabeza; Q, K y V salen de una sola multiplicación de matrices."""

    def __init__(self, d_model: int, num_heads: int, rope: RoPE | None = None, device=None, dtype=None):
        super().__init__()
        assert d_model % num_heads == 0
        self.h, self.d_k = num_heads, d_model // num_heads
        self.q_proj = Linear(d_model, d_model, device, dtype)
        self.k_proj = Linear(d_model, d_model, device, dtype)
        self.v_proj = Linear(d_model, d_model, device, dtype)
        self.output_proj = Linear(d_model, d_model, device, dtype)
        self.rope = rope

    def forward(self, x: Tensor, posiciones: Tensor | None = None) -> Tensor:
        *lote, seq, d = x.shape
        w_qkv = torch.cat([self.q_proj.weight, self.k_proj.weight, self.v_proj.weight], dim=0)
        qkv = x @ w_qkv.T  # una sola multiplicación para las tres proyecciones
        q, k, v = (t.reshape(*lote, seq, self.h, self.d_k).transpose(-3, -2) for t in qkv.split(d, dim=-1))
        if self.rope is not None:
            if posiciones is None:
                posiciones = torch.arange(seq, device=x.device)
            pos = posiciones.unsqueeze(-2) if posiciones.dim() > 1 else posiciones  # misma posición en cada cabeza
            q, k = self.rope(q, pos), self.rope(k, pos)
        causal = torch.ones(seq, seq, dtype=torch.bool, device=x.device).tril()
        y = atencion_escalada(q, k, v, causal)
        y = y.transpose(-3, -2).reshape(*lote, seq, d)
        return self.output_proj(y)


class BloqueTransformer(nn.Module):
    def __init__(self, d_model: int, num_heads: int, d_ff: int, rope: RoPE, device=None, dtype=None):
        super().__init__()
        self.ln1 = RMSNorm(d_model, device=device, dtype=dtype)
        self.attn = AtencionMultiCabeza(d_model, num_heads, rope, device, dtype)
        self.ln2 = RMSNorm(d_model, device=device, dtype=dtype)
        self.ffn = SwiGLU(d_model, d_ff, device, dtype)

    def forward(self, x: Tensor, posiciones: Tensor | None = None) -> Tensor:
        x = x + self.attn(self.ln1(x), posiciones)
        return x + self.ffn(self.ln2(x))


class TransformerLM(nn.Module):
    def __init__(self, vocab_size: int, context_length: int, d_model: int, num_layers: int, num_heads: int,
                 d_ff: int | None = None, rope_theta: float = 10000.0, device=None, dtype=None):
        super().__init__()
        d_ff = d_ff or d_ff_por_defecto(d_model)
        self.config = dict(vocab_size=vocab_size, context_length=context_length, d_model=d_model,
                           num_layers=num_layers, num_heads=num_heads, d_ff=d_ff, rope_theta=rope_theta)
        rope = RoPE(rope_theta, d_model // num_heads, context_length, device)
        self.token_embeddings = Embedding(vocab_size, d_model, device, dtype)
        self.layers = nn.ModuleList(BloqueTransformer(d_model, num_heads, d_ff, rope, device, dtype)
                                    for _ in range(num_layers))
        self.ln_final = RMSNorm(d_model, device=device, dtype=dtype)
        self.lm_head = Linear(d_model, vocab_size, device, dtype)

    def forward(self, ids: Tensor) -> Tensor:
        x = self.token_embeddings(ids)
        posiciones = torch.arange(ids.shape[-1], device=ids.device)
        for capa in self.layers:
            x = capa(x, posiciones)
        return self.lm_head(self.ln_final(x))

    def num_parametros(self) -> int:
        return sum(p.numel() for p in self.parameters())

    @torch.no_grad()
    def generar(self, ids: list[int], max_nuevos: int = 200, temperatura: float = 0.8, top_p: float = 0.9,
                fin: int | None = None) -> list[int]:
        """Decodificación con temperatura y muestreo *top-p* (nucleus sampling)."""
        self.eval()
        dispositivo = self.lm_head.weight.device
        salida = list(ids)
        for _ in range(max_nuevos):
            ventana = torch.tensor([salida[-self.config["context_length"]:]], device=dispositivo)
            logits = self(ventana)[0, -1]
            if temperatura <= 0:
                siguiente = int(logits.argmax())
            else:
                prob = softmax(logits / temperatura, dim=-1)
                orden, indices = prob.sort(descending=True)
                acumulada = orden.cumsum(0)
                quitar = acumulada - orden > top_p  # se queda con el menor conjunto que suma ≥ top_p
                orden[quitar] = 0
                orden = orden / orden.sum()
                siguiente = int(indices[torch.multinomial(orden, 1)])
            salida.append(siguiente)
            if fin is not None and siguiente == fin:
                break
        return salida
