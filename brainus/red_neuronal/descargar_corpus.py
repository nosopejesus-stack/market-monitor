#!/usr/bin/env python3
"""Descarga más texto general en español (Wikipedia, de Hugging Face) para entrenar una Brainus más grande.

  pip install pyarrow
  python brainus/red_neuronal/descargar_corpus.py --mb 200

Guarda corpus/es_wiki_<N>mb.txt.gz. Licencia del texto: CC BY-SA 4.0 (colaboradores de Wikipedia).
Regla de Chinchilla (Clase 09): unos 20 tokens por parámetro. Para el perfil "potente" (125M)
lo ideal serían unos 2.500M tokens (~7 GB de texto), pero con 200-1000 MB ya mejora mucho.
"""
from __future__ import annotations

import argparse
import gzip
import random
import re
import urllib.request
from pathlib import Path

URL = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/main/20231101.es/train-{:05d}-of-00013.parquet"
CORPUS = Path(__file__).resolve().parent / "corpus"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=int, default=200, help="megas de texto a guardar")
    a = ap.parse_args()
    import pyarrow.parquet as pq

    CORPUS.mkdir(exist_ok=True)
    objetivo, total, trozos = a.mb * 1_000_000, 0, []
    for n in range(13):
        tmp = CORPUS / "tmp.parquet"
        print(f"Descargando parte {n + 1}/13 ...")
        urllib.request.urlretrieve(URL.format(n), tmp)
        textos = pq.read_table(tmp, columns=["text"]).column("text").to_pylist()
        tmp.unlink()
        random.Random(n).shuffle(textos)
        for t in textos:
            t = re.sub(r"\n{3,}", "\n\n", t).strip()
            if len(t) < 800:
                continue
            trozos.append(t)
            total += len(t)
            if total >= objetivo:
                break
        if total >= objetivo:
            break
    destino = CORPUS / f"es_wiki_{a.mb}mb.txt.gz"
    destino.write_bytes(gzip.compress("<|endoftext|>".join(trozos).encode("utf-8"), compresslevel=6))
    print(f"Guardado {destino} ({total / 1e6:.0f} MB de texto, {len(trozos)} artículos)")


if __name__ == "__main__":
    main()
