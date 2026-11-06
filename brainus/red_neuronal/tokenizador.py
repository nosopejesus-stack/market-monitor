"""Brainus: tokenizador BPE a nivel de bytes, escrito desde cero (CS336, tarea 1).

- Vocabulario: dict[int, bytes]. Fusiones: list[tuple[bytes, bytes]] en orden de creación.
- Tokens especiales (p. ej. "<|endoftext|>"): nunca se parten y nunca se fusionan con lo de alrededor.
- Pre-tokenización con la regex de GPT-2, para que no haya fusiones entre palabras.
- Entrenamiento eficiente: se cuentan las "palabras" una vez y, en cada fusión, solo se
  actualizan las palabras que contienen el par fusionado (índice par → palabras).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path

import regex as re

PATRON_GPT2 = re.compile(r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")
FIN = "<|endoftext|>"


def _partir_especiales(texto: str, especiales: list[str]) -> list[str]:
    """Separa el texto por los tokens especiales, conservándolos (los más largos primero)."""
    if not especiales:
        return [texto]
    patron = "(" + "|".join(re.escape(e) for e in sorted(especiales, key=len, reverse=True)) + ")"
    return [t for t in re.split(patron, texto) if t]


def entrenar_bpe(texto: str, tam_vocab: int, especiales: list[str] | None = None
                 ) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
    especiales = especiales or []
    vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
    for e in especiales:
        vocab[len(vocab)] = e.encode("utf-8")

    # 1. Contar palabras pre-tokenizadas (sin cruzar tokens especiales)
    conteo: Counter[tuple[bytes, ...]] = Counter()
    for trozo in _partir_especiales(texto, especiales):
        if trozo in especiales:
            continue
        for palabra in PATRON_GPT2.findall(trozo):
            conteo[tuple(bytes([b]) for b in palabra.encode("utf-8"))] += 1
    palabras = list(conteo.keys())
    frec = [conteo[p] for p in palabras]
    secuencias = [list(p) for p in palabras]

    # 2. Contar pares e índice par → palabras que lo contienen
    pares: Counter[tuple[bytes, bytes]] = Counter()
    donde: dict[tuple[bytes, bytes], set[int]] = defaultdict(set)
    for i, s in enumerate(secuencias):
        for a, b in zip(s, s[1:]):
            pares[(a, b)] += frec[i]
            donde[(a, b)].add(i)

    fusiones: list[tuple[bytes, bytes]] = []
    while len(vocab) < tam_vocab and pares:
        # el par más frecuente; empate → el lexicográficamente mayor (criterio de GPT-2 / CS336)
        mejor = max(pares.items(), key=lambda kv: (kv[1], kv[0]))[0]
        if pares[mejor] <= 0:
            break
        nuevo = mejor[0] + mejor[1]
        fusiones.append(mejor)
        vocab[len(vocab)] = nuevo
        for i in list(donde.get(mejor, ())):
            s = secuencias[i]
            # quitar los pares viejos de esta palabra
            for a, b in zip(s, s[1:]):
                pares[(a, b)] -= frec[i]
                if pares[(a, b)] <= 0:
                    del pares[(a, b)]
                donde[(a, b)].discard(i)
            # fusionar
            j, out = 0, []
            while j < len(s):
                if j + 1 < len(s) and s[j] == mejor[0] and s[j + 1] == mejor[1]:
                    out.append(nuevo)
                    j += 2
                else:
                    out.append(s[j])
                    j += 1
            secuencias[i] = out
            # añadir los pares nuevos
            for a, b in zip(out, out[1:]):
                pares[(a, b)] += frec[i]
                donde[(a, b)].add(i)
        donde.pop(mejor, None)
        pares.pop(mejor, None)
    return vocab, fusiones


class Tokenizador:
    def __init__(self, vocab: dict[int, bytes], fusiones: list[tuple[bytes, bytes]],
                 especiales: list[str] | None = None):
        self.vocab = dict(vocab)
        self.fusiones = list(fusiones)
        self.especiales = list(especiales or [])
        for e in self.especiales:  # añadir especiales que falten
            if e.encode("utf-8") not in self.vocab.values():
                self.vocab[len(self.vocab)] = e.encode("utf-8")
        self.id_de = {b: i for i, b in self.vocab.items()}
        self.rango = {par: r for r, par in enumerate(self.fusiones)}
        self._cache: dict[str, list[int]] = {}

    @property
    def tam_vocab(self) -> int:
        return len(self.vocab)

    def id_especial(self, token: str) -> int | None:
        return self.id_de.get(token.encode("utf-8"))

    def _codificar_palabra(self, palabra: str) -> list[int]:
        if palabra in self._cache:
            return self._cache[palabra]
        partes = [bytes([b]) for b in palabra.encode("utf-8")]
        while len(partes) > 1:
            par = min(zip(partes, partes[1:]), key=lambda p: self.rango.get(p, float("inf")))
            if par not in self.rango:
                break
            j, out = 0, []
            while j < len(partes):
                if j + 1 < len(partes) and (partes[j], partes[j + 1]) == par:
                    out.append(par[0] + par[1])
                    j += 2
                else:
                    out.append(partes[j])
                    j += 1
            partes = out
        ids = [self.id_de[p] for p in partes]
        self._cache[palabra] = ids
        return ids

    def encode(self, texto: str) -> list[int]:
        ids: list[int] = []
        for trozo in _partir_especiales(texto, self.especiales):
            if trozo in self.especiales:
                ids.append(self.id_de[trozo.encode("utf-8")])
            else:
                for palabra in PATRON_GPT2.findall(trozo):
                    ids.extend(self._codificar_palabra(palabra))
        return ids

    def encode_iterable(self, textos: Iterable[str]) -> Iterator[int]:
        """Codifica línea a línea sin cargar todo en memoria (archivos enormes)."""
        for t in textos:
            yield from self.encode(t)

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.vocab[i] for i in ids).decode("utf-8", errors="replace")

    # ---------------------------------------------------------- disco
    def guardar(self, ruta: Path) -> None:
        ruta.write_text(json.dumps({
            "vocab": {i: b.hex() for i, b in self.vocab.items()},
            "fusiones": [[a.hex(), b.hex()] for a, b in self.fusiones],
            "especiales": self.especiales,
        }), encoding="utf-8")

    @classmethod
    def cargar(cls, ruta: Path) -> "Tokenizador":
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        vocab = {int(i): bytes.fromhex(h) for i, h in d["vocab"].items()}
        fusiones = [(bytes.fromhex(a), bytes.fromhex(b)) for a, b in d["fusiones"]]
        return cls(vocab, fusiones, d["especiales"])
