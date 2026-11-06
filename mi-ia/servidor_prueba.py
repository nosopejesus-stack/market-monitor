"""Servidor de PRUEBA que imita la API de Ollama (/api/chat y /api/embed) con un modelo pequeño
de Hugging Face. Sirve para probar Mi IA sin instalar Ollama (por ejemplo en un servidor en la nube).

En tu PC usa Ollama de verdad; esto no hace falta.
  pip install torch transformers jinja2
  python mi-ia/servidor_prueba.py              # Qwen/Qwen2.5-0.5B-Instruct en el puerto 11434
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

M = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(M)
model = AutoModelForCausalLM.from_pretrained(M, dtype=torch.float32)


@torch.no_grad()
def embed(textos):
    vecs = []
    for t in textos:
        ids = tok(t, return_tensors="pt", truncation=True, max_length=256)
        h = model(**ids, output_hidden_states=True).hidden_states[-1][0]
        vecs.append(h.mean(0).tolist())
    return vecs


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/embed":
            entrada = d["input"] if isinstance(d["input"], list) else [d["input"]]
            body = {"embeddings": embed(entrada)}
        else:
            ids = tok.apply_chat_template(d["messages"], add_generation_prompt=True, return_tensors="pt")
            if not isinstance(ids, torch.Tensor):
                ids = ids["input_ids"]
            out = model.generate(ids, max_new_tokens=220, do_sample=False)
            body = {"message": {"role": "assistant", "content": tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)}}
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


print("ready", flush=True)
HTTPServer(("127.0.0.1", 11434), H).serve_forever()
