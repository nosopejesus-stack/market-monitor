"""Tests de Brainus: cada pieza escrita a mano se compara con la referencia oficial de PyTorch.

  pip install pytest
  python -m pytest brainus/red_neuronal/test_red.py -v
"""
from __future__ import annotations

import io
import math

import numpy as np
import pytest
import torch
import torch.nn.functional as F

from entrenamiento import (AdamW, cargar_checkpoint, cross_entropy, guardar_checkpoint, lr_coseno, obtener_lote,
                           recortar_gradientes)
from modelo import (AtencionMultiCabeza, BloqueTransformer, Embedding, Linear, RMSNorm, RoPE, SwiGLU, TransformerLM,
                    atencion_escalada, silu, softmax)
from tokenizador import FIN, Tokenizador, entrenar_bpe

torch.manual_seed(0)
ATOL = 1e-5


def test_linear_igual_que_pytorch():
    capa = Linear(16, 8)
    x = torch.randn(2, 5, 16)
    assert torch.allclose(capa(x), F.linear(x, capa.weight), atol=ATOL)
    assert capa.weight.shape == (8, 16)


def test_linear_inicializacion_normal_truncada():
    capa = Linear(512, 512)
    std = math.sqrt(2 / 1024)
    assert capa.weight.abs().max() <= 3 * std + 1e-6
    assert abs(capa.weight.std().item() - std) / std < 0.15


def test_embedding_igual_que_pytorch():
    emb = Embedding(50, 8)
    ids = torch.randint(0, 50, (3, 7))
    assert torch.allclose(emb(ids), F.embedding(ids, emb.weight))


def test_rmsnorm_formula_y_tipo():
    norma = RMSNorm(8, eps=1e-5)
    with torch.no_grad():
        norma.weight.copy_(torch.rand(8))
    x = torch.randn(4, 8)
    esperado = x / torch.sqrt((x**2).mean(-1, keepdim=True) + 1e-5) * norma.weight
    assert torch.allclose(norma(x), esperado, atol=ATOL)
    assert norma(x.to(torch.bfloat16)).dtype == torch.bfloat16  # vuelve al tipo de entrada


def test_silu_y_swiglu():
    x = torch.randn(10, 16)
    assert torch.allclose(silu(x), F.silu(x), atol=ATOL)
    ffn = SwiGLU(16, 48)
    esperado = F.linear(F.silu(F.linear(x, ffn.w1.weight)) * F.linear(x, ffn.w3.weight), ffn.w2.weight)
    assert torch.allclose(ffn(x), esperado, atol=ATOL)


def test_softmax_estable_igual_que_pytorch():
    x = torch.randn(3, 4, 10) * 50 + 1000  # valores enormes: un softmax ingenuo desbordaría
    for dim in (0, 1, 2, -1):
        assert torch.allclose(softmax(x, dim), torch.softmax(x, dim), atol=ATOL)
    assert not torch.isnan(softmax(x, -1)).any()


def test_atencion_escalada_con_mascara():
    Q, K, V = torch.randn(2, 3, 6, 8), torch.randn(2, 3, 6, 8), torch.randn(2, 3, 6, 8)
    causal = torch.ones(6, 6, dtype=torch.bool).tril()
    esperado = F.scaled_dot_product_attention(Q, K, V, attn_mask=causal)
    assert torch.allclose(atencion_escalada(Q, K, V, causal), esperado, atol=ATOL)
    assert torch.allclose(atencion_escalada(Q, K, V), F.scaled_dot_product_attention(Q, K, V), atol=ATOL)


def _rope_referencia(x: torch.Tensor, pos: torch.Tensor, theta: float) -> torch.Tensor:
    """RoPE con números complejos: cada par (x_2k, x_2k+1) es un complejo que se multiplica por e^{i·pos·θ_k}."""
    d = x.shape[-1]
    frec = theta ** (-torch.arange(0, d, 2, dtype=torch.float64) / d)
    ang = pos.to(torch.float64)[..., None] * frec
    xc = torch.view_as_complex(x.to(torch.float64).reshape(*x.shape[:-1], d // 2, 2).contiguous())
    return torch.view_as_real(xc * torch.polar(torch.ones_like(ang), ang)).reshape(x.shape).to(x.dtype)


def test_rope_igual_que_formula_compleja():
    rope = RoPE(10000.0, 16, 64)
    x = torch.randn(2, 10, 16)
    pos = torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]])
    assert torch.allclose(rope(x, pos), _rope_referencia(x, pos, 10000.0), atol=1e-5)


def test_rope_solo_depende_de_posicion_relativa():
    rope = RoPE(10000.0, 16, 128)
    q, k = torch.randn(16), torch.randn(16)
    def punto(i, j):
        return (rope(q[None], torch.tensor([i])) * rope(k[None], torch.tensor([j]))).sum()
    assert torch.allclose(punto(3, 1), punto(53, 51), atol=1e-4)


def test_atencion_multicabeza_igual_que_pytorch():
    d, h = 32, 4
    att = AtencionMultiCabeza(d, h)
    mha = torch.nn.MultiheadAttention(d, h, bias=False, batch_first=True)
    with torch.no_grad():
        mha.in_proj_weight.copy_(torch.cat([att.q_proj.weight, att.k_proj.weight, att.v_proj.weight]))
        mha.out_proj.weight.copy_(att.output_proj.weight)
    x = torch.randn(2, 7, d)
    mascara = torch.ones(7, 7, dtype=torch.bool).triu(1)  # en PyTorch True = prohibido
    esperado, _ = mha(x, x, x, attn_mask=mascara, need_weights=False)
    assert torch.allclose(att(x), esperado, atol=ATOL)


def test_atencion_es_causal():
    att = AtencionMultiCabeza(32, 4, RoPE(10000.0, 8, 32))
    x = torch.randn(1, 10, 32)
    y1 = att(x)
    x2 = x.clone()
    x2[0, 6:] = torch.randn(4, 32)  # cambiar el futuro no debe afectar al pasado
    assert torch.allclose(att(x2)[0, :6], y1[0, :6], atol=ATOL)


def test_bloque_y_modelo_completo():
    modelo = TransformerLM(vocab_size=100, context_length=32, d_model=64, num_layers=2, num_heads=4)
    ids = torch.randint(0, 100, (3, 20))
    logits = modelo(ids)
    assert logits.shape == (3, 20, 100)
    # truncar la entrada no cambia las predicciones de las posiciones que quedan
    assert torch.allclose(modelo(ids[:, :10]), logits[:, :10], atol=1e-4)
    nombres = set(modelo.state_dict())
    for clave in ("token_embeddings.weight", "layers.0.attn.q_proj.weight", "layers.0.attn.output_proj.weight",
                  "layers.1.ln1.weight", "layers.1.ffn.w2.weight", "ln_final.weight", "lm_head.weight"):
        assert clave in nombres
    bloque = BloqueTransformer(64, 4, 128, RoPE(10000.0, 16, 32))
    assert bloque(torch.randn(2, 5, 64)).shape == (2, 5, 64)


def test_cross_entropy_igual_que_pytorch():
    logits = torch.randn(8, 50) * 30 + 500  # enormes: comprueba estabilidad
    objetivos = torch.randint(0, 50, (8,))
    assert torch.allclose(cross_entropy(logits, objetivos), F.cross_entropy(logits, objetivos), atol=1e-4)
    logits3 = torch.randn(2, 5, 50)
    obj3 = torch.randint(0, 50, (2, 5))
    assert torch.allclose(cross_entropy(logits3, obj3), F.cross_entropy(logits3.view(-1, 50), obj3.view(-1)), atol=ATOL)


def test_adamw_igual_que_pytorch():
    torch.manual_seed(1)
    a = torch.nn.Linear(10, 5)
    b = torch.nn.Linear(10, 5)
    b.load_state_dict(a.state_dict())
    mio = AdamW(a.parameters(), lr=1e-2, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.1)
    ref = torch.optim.AdamW(b.parameters(), lr=1e-2, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.1)
    for _ in range(25):
        x = torch.randn(4, 10)
        for modelo, opt in ((a, mio), (b, ref)):
            opt.zero_grad()
            modelo(x).pow(2).sum().backward()
            opt.step()
    for p, q in zip(a.parameters(), b.parameters()):
        assert torch.allclose(p, q, atol=1e-5)


def test_lr_coseno():
    lr = [lr_coseno(it, 1.0, 0.1, 7, 21) for it in range(25)]
    assert lr[0] == 0 and abs(lr[7] - 1.0) < 1e-9 and abs(lr[21] - 0.1) < 1e-9 and lr[24] == 0.1
    assert abs(lr[14] - 0.55) < 1e-9  # mitad del coseno = punto medio entre máximo y mínimo
    assert all(lr[i] >= lr[i + 1] for i in range(7, 24))


def test_recortar_gradientes_igual_que_pytorch():
    a, b = torch.nn.Linear(10, 10), torch.nn.Linear(10, 10)
    b.load_state_dict(a.state_dict())
    x = torch.randn(4, 10) * 100
    a(x).sum().backward()
    b(x).sum().backward()
    recortar_gradientes(a.parameters(), 1.0)
    torch.nn.utils.clip_grad_norm_(b.parameters(), 1.0)
    for p, q in zip(a.parameters(), b.parameters()):
        assert torch.allclose(p.grad, q.grad, atol=1e-5)


def test_obtener_lote():
    datos = np.arange(100)
    x, y = obtener_lote(datos, 16, 8, "cpu")
    assert x.shape == y.shape == (16, 8) and x.dtype == torch.long
    assert torch.equal(y, x + 1)
    assert int(x.max()) < 100 - 1


def test_checkpoint_ida_y_vuelta():
    modelo = TransformerLM(50, 16, 32, 1, 2)
    opt = AdamW(modelo.parameters(), lr=1e-3)
    modelo(torch.randint(0, 50, (2, 8))).sum().backward()
    opt.step()
    buffer = io.BytesIO()
    guardar_checkpoint(modelo, opt, 123, buffer)
    buffer.seek(0)
    otro = TransformerLM(50, 16, 32, 1, 2)
    otro_opt = AdamW(otro.parameters(), lr=1e-3)
    assert cargar_checkpoint(buffer, otro, otro_opt) == 123
    for p, q in zip(modelo.parameters(), otro.parameters()):
        assert torch.equal(p, q)
    assert otro_opt.state_dict()["state"].keys() == opt.state_dict()["state"].keys()


TEXTO = ("hola mundo, hola amigo. el mundo es grande y el amigo es bueno. " * 20 + FIN + " otra historia. ") * 3


def test_bpe_ida_y_vuelta_y_especiales():
    vocab, fusiones = entrenar_bpe(TEXTO, 300, [FIN])
    assert len(vocab) <= 300 and len(fusiones) == len(vocab) - 257
    assert FIN.encode() in vocab.values()
    assert all(FIN.encode() not in v or v == FIN.encode() for v in vocab.values())  # nunca se fusiona con nada
    tok = Tokenizador(vocab, fusiones, [FIN])
    for t in (TEXTO, "¡Hola, señor! ñandú 🌍 1234", "", f"a{FIN}b{FIN}{FIN}", "  espacios   raros \n\n"):
        assert tok.decode(tok.encode(t)) == t
    ids = tok.encode(f"hola{FIN}mundo")
    assert ids.count(tok.id_especial(FIN)) == 1
    assert len(tok.encode(TEXTO)) < len(TEXTO.encode()) / 2  # comprime


def test_bpe_primera_fusion_es_el_par_mas_frecuente():
    vocab, fusiones = entrenar_bpe("aaaa bbb aaaa", 258, [])
    assert fusiones[0] == (b"a", b"a")


def test_bpe_guardar_cargar(tmp_path):
    vocab, fusiones = entrenar_bpe(TEXTO, 280, [FIN])
    tok = Tokenizador(vocab, fusiones, [FIN])
    tok.guardar(tmp_path / "t.json")
    otro = Tokenizador.cargar(tmp_path / "t.json")
    assert otro.encode(TEXTO) == tok.encode(TEXTO)
    assert list(tok.encode_iterable(["hola ", "mundo"])) == tok.encode("hola ") + tok.encode("mundo")


def test_generar_top_p_y_temperatura_cero():
    torch.manual_seed(0)
    modelo = TransformerLM(30, 16, 32, 1, 2)
    salida = modelo.generar([1, 2, 3], max_nuevos=20, temperatura=0.8, top_p=0.5)
    assert len(salida) == 23 and all(0 <= t < 30 for t in salida)
    g1 = modelo.generar([1, 2, 3], max_nuevos=5, temperatura=0)
    g2 = modelo.generar([1, 2, 3], max_nuevos=5, temperatura=0)
    assert g1 == g2  # temperatura 0 = determinista
    corta = modelo.generar([1, 2, 3], max_nuevos=50, temperatura=0, fin=g1[4])
    assert corta[-1] == g1[4] and len(corta) <= 5  # se detiene al generar el token de fin


@pytest.mark.parametrize("pasos", [60])
def test_aprende_un_patron(pasos):
    """Prueba de humo: el modelo debe memorizar una secuencia repetida (la pérdida baja mucho)."""
    torch.manual_seed(0)
    datos = np.array([1, 2, 3, 4, 5, 6, 7, 8] * 50)
    modelo = TransformerLM(10, 16, 32, 2, 2)
    opt = AdamW(modelo.parameters(), lr=1e-2)
    inicial = None
    for _ in range(pasos):
        x, y = obtener_lote(datos, 8, 16, "cpu")
        perdida = cross_entropy(modelo(x), y)
        inicial = inicial or perdida.item()
        opt.zero_grad()
        perdida.backward()
        recortar_gradientes(modelo.parameters(), 1.0)
        opt.step()
    assert perdida.item() < inicial * 0.2
