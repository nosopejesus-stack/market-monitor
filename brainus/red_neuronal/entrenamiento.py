"""Brainus: utilidades de entrenamiento escritas desde cero (CS336, tarea 1).

  cross_entropy ............ pérdida estable con log-sum-exp
  AdamW .................... optimizador (Loshchilov y Hutter, 2019), con corrección de sesgo
  lr_coseno ................ calentamiento lineal + caída coseno hasta un mínimo
  recortar_gradientes ...... recorte por norma L2 global
  obtener_lote ............. muestras aleatorias (x, y) de un array de tokens (sirve con np.memmap)
  guardar/cargar_checkpoint  modelo + optimizador + iteración
"""
from __future__ import annotations

import math
import os
from collections.abc import Iterable
from typing import IO, BinaryIO

import numpy as np
import numpy.typing as npt
import torch
from torch import Tensor


def cross_entropy(logits: Tensor, objetivos: Tensor) -> Tensor:
    """Media de -log softmax(logits)[objetivo], calculada sin desbordamientos."""
    logits = logits.reshape(-1, logits.shape[-1]).to(torch.float32)
    objetivos = objetivos.reshape(-1)
    maximo = logits.amax(dim=-1, keepdim=True)
    log_suma_exp = maximo.squeeze(-1) + torch.log(torch.exp(logits - maximo).sum(dim=-1))
    correcto = logits.gather(-1, objetivos[:, None]).squeeze(-1)
    return (log_suma_exp - correcto).mean()


class AdamW(torch.optim.Optimizer):
    """AdamW con weight decay desacoplado.

    Para cada parámetro θ con gradiente g, en el paso t:
        θ ← θ − α·λ·θ                         (weight decay desacoplado)
        m ← β1·m + (1−β1)·g ;  v ← β2·v + (1−β2)·g²
        α_t = α·√(1−β2^t) / (1−β1^t)           (corrección de sesgo)
        θ ← θ − α_t · m / (√v + ε)
    """

    def __init__(self, params, lr: float = 1e-3, betas: tuple[float, float] = (0.9, 0.999), eps: float = 1e-8,
                 weight_decay: float = 0.01):
        if lr < 0:
            raise ValueError(f"lr no válido: {lr}")
        super().__init__(params, dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay))

    @torch.no_grad()
    def step(self, closure=None):
        perdida = closure() if closure is not None else None
        for grupo in self.param_groups:
            lr, (b1, b2), eps, wd = grupo["lr"], grupo["betas"], grupo["eps"], grupo["weight_decay"]
            for p in grupo["params"]:
                if p.grad is None:
                    continue
                g = p.grad
                estado = self.state[p]
                if not estado:
                    estado["t"] = 0
                    estado["m"] = torch.zeros_like(p)
                    estado["v"] = torch.zeros_like(p)
                estado["t"] += 1
                t, m, v = estado["t"], estado["m"], estado["v"]
                p.mul_(1 - lr * wd)
                m.mul_(b1).add_(g, alpha=1 - b1)
                v.mul_(b2).addcmul_(g, g, value=1 - b2)
                lr_t = lr * math.sqrt(1 - b2**t) / (1 - b1**t)
                p.addcdiv_(m, v.sqrt().add_(eps), value=-lr_t)
        return perdida


def lr_coseno(it: int, lr_max: float, lr_min: float, calentamiento: int, ciclo: int) -> float:
    """Calentamiento lineal hasta lr_max, caída coseno hasta lr_min en `ciclo` pasos, y luego lr_min."""
    if it < calentamiento:
        return it / calentamiento * lr_max
    if it <= ciclo:
        progreso = (it - calentamiento) / (ciclo - calentamiento)
        return lr_min + 0.5 * (1 + math.cos(math.pi * progreso)) * (lr_max - lr_min)
    return lr_min


def recortar_gradientes(parametros: Iterable[torch.nn.Parameter], norma_max: float, eps: float = 1e-6) -> float:
    """Si la norma L2 de TODOS los gradientes juntos supera norma_max, los escala para que valga norma_max."""
    grads = [p.grad for p in parametros if p.grad is not None]
    if not grads:
        return 0.0
    total = torch.sqrt(sum((g.detach().to(torch.float32) ** 2).sum() for g in grads))
    if total > norma_max:
        factor = norma_max / (total + eps)
        for g in grads:
            g.mul_(factor)
    return float(total)


def obtener_lote(datos: npt.NDArray, tam_lote: int, contexto: int, dispositivo: str) -> tuple[Tensor, Tensor]:
    """x = trozos aleatorios de longitud `contexto`; y = los mismos trozos desplazados un token."""
    inicios = np.random.randint(0, len(datos) - contexto, size=tam_lote)
    x = np.stack([datos[i : i + contexto] for i in inicios]).astype(np.int64)
    y = np.stack([datos[i + 1 : i + 1 + contexto] for i in inicios]).astype(np.int64)
    return torch.from_numpy(x).to(dispositivo), torch.from_numpy(y).to(dispositivo)


def guardar_checkpoint(modelo: torch.nn.Module, optimizador: torch.optim.Optimizer | None, iteracion: int,
                       destino: str | os.PathLike | BinaryIO | IO[bytes], extra: dict | None = None) -> None:
    torch.save({"modelo": modelo.state_dict(),
                "optimizador": optimizador.state_dict() if optimizador is not None else None,
                "iteracion": iteracion, **(extra or {})}, destino)


def cargar_checkpoint(origen: str | os.PathLike | BinaryIO | IO[bytes], modelo: torch.nn.Module,
                      optimizador: torch.optim.Optimizer | None = None) -> int:
    ck = torch.load(origen, map_location="cpu", weights_only=False)
    modelo.load_state_dict(ck["modelo"])
    if optimizador is not None and ck.get("optimizador"):
        optimizador.load_state_dict(ck["optimizador"])
    return ck["iteracion"]
