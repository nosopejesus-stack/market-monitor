# Minimal Ollama-compatible /api/chat server backed by a small HF model, to test mi_ia.py end-to-end.
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
M = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(M); model = AutoModelForCausalLM.from_pretrained(M, torch_dtype=torch.float32)
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        ids = tok.apply_chat_template(d["messages"], add_generation_prompt=True, return_tensors="pt")
        if not isinstance(ids, torch.Tensor): ids = ids["input_ids"]
        out = model.generate(ids, max_new_tokens=220, do_sample=False)
        txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
        body = json.dumps({"message": {"role": "assistant", "content": txt}}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
print("ready", flush=True)
HTTPServer(("127.0.0.1", 11434), H).serve_forever()
