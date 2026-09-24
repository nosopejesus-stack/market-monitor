"""Supplier-invoice extraction with complexity routing and per-invoice cost tracking.

AGENT WHERE REASONING MATTERS (reading a messy PDF), CODE WHERE DETERMINISM MATTERS
(validate.py). Routing:
  LOW      claude-haiku-4-5  -> extract; accept only if every deterministic check passes
  HIGH     claude-opus-5     -> re-extract when LOW fails validation
  CRITICAL human review      -> when HIGH also fails; nothing is posted automatically

The unit metric is COST PER ACCEPTED INVOICE (model spend of every attempt, including
failed ones, divided by invoices that passed validation), not cost per API call.
"""
from __future__ import annotations

import base64
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import anthropic

from .schema import Invoice
from .validate import check, unsupported_reason

# USD per million tokens (input, output) — from the Claude API reference cached 2026-06-24.
PRICES = {"claude-haiku-4-5": (1.00, 5.00), "claude-opus-5": (5.00, 25.00)}
TIERS = ["claude-haiku-4-5", "claude-opus-5"]

PROMPT = (
    "Extract the data of this Spanish supplier invoice (factura recibida). Copy NIF/CIF and the invoice "
    "number exactly as printed. Give one VAT line per VAT rate with its taxable base and VAT amount; include "
    "recargo de equivalencia and IRPF retention only if printed. Use ISO dates. If a field is illegible, "
    "leave it empty rather than guessing; the result is checked arithmetically and by NIF check digits."
)


@dataclass
class Attempt:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    errors: list[str] = field(default_factory=list)
    stop_reason: str = ""


@dataclass
class Result:
    file: str
    status: str  # "accepted" | "human_review"
    invoice: dict | None
    warnings: list[str]
    attempts: list[Attempt]
    review_reason: str = ""
    latency_s: float = 0.0

    @property
    def cost_usd(self) -> float:
        return sum(a.cost_usd for a in self.attempts)


def _document_block(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode()
    if path.suffix.lower() == ".pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}}
    media = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[path.suffix.lower()]
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}}


def _call(client: anthropic.Anthropic, model: str, block: dict):
    messages = [{"role": "user", "content": [block, {"type": "text", "text": PROMPT}]}]
    if model == "claude-opus-5":
        # Server-side refusal fallbacks (opt-in); routes by refusal category.
        return client.beta.messages.parse(
            model=model, max_tokens=16000, messages=messages, output_format=Invoice,
            thinking={"type": "adaptive"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        )
    return client.messages.parse(model=model, max_tokens=4096, messages=messages, output_format=Invoice)


def process(path: Path, client: anthropic.Anthropic | None = None, tiers: list[str] = TIERS) -> Result:
    client = client or anthropic.Anthropic()
    try:
        block = _document_block(path)
    except (KeyError, OSError) as exc:  # unsupported format (tiff, heic, docx...) or unreadable file
        return Result(str(path), "human_review", None, [], [], review_reason=f"unreadable or unsupported file: {exc}")
    attempts: list[Attempt] = []
    last_errors: list[str] = []
    t_start = time.monotonic()
    for model in tiers:
        att = Attempt(model=model)
        t0 = time.monotonic()
        try:
            resp = _call(client, model, block)
        except anthropic.RateLimitError:
            raise  # let the caller back off; do not burn a tier on a 429
        except anthropic.APIStatusError as e:
            att.errors.append(f"api error {e.status_code}")
            attempts.append(att)
            continue
        att.latency_s = round(time.monotonic() - t0, 2)
        att.stop_reason = resp.stop_reason or ""
        u = resp.usage
        att.input_tokens, att.output_tokens = u.input_tokens, u.output_tokens
        pin, pout = PRICES.get(resp.model, PRICES[model])
        att.cost_usd = round((u.input_tokens * pin + u.output_tokens * pout) / 1e6, 6)
        if resp.stop_reason == "refusal" or resp.parsed_output is None:
            att.errors.append(f"no structured output (stop_reason={resp.stop_reason})")
            attempts.append(att)
            continue
        inv: Invoice = resp.parsed_output
        reason = unsupported_reason(inv)
        if reason:
            att.errors = [reason]
            attempts.append(att)
            return Result(str(path), "human_review", inv.model_dump(), [], attempts, review_reason=reason,
                          latency_s=round(time.monotonic() - t_start, 2))
        errors, warnings = check(inv)
        att.errors = errors
        last_errors = errors
        attempts.append(att)
        if not errors:
            return Result(str(path), "accepted", inv.model_dump(), warnings, attempts,
                          latency_s=round(time.monotonic() - t_start, 2))
    return Result(str(path), "human_review", None, [], attempts, review_reason="; ".join(last_errors) or "no valid extraction",
                  latency_s=round(time.monotonic() - t_start, 2))


def run_folder(folder: Path, out_jsonl: Path) -> dict:
    """Process every invoice in a folder; append results to a JSONL ledger; return unit economics."""
    client = anthropic.Anthropic()
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".webp"})
    results = []
    with out_jsonl.open("a") as f:
        for p in files:
            r = process(p, client)
            results.append(r)
            f.write(json.dumps({**asdict(r), "cost_usd": r.cost_usd}, ensure_ascii=False) + "\n")
    return summarize(results)


def summarize(results: list[Result]) -> dict:
    accepted = [r for r in results if r.status == "accepted"]
    total_cost = sum(r.cost_usd for r in results)
    by_tier = {}
    for r in accepted:
        by_tier[r.attempts[-1].model] = by_tier.get(r.attempts[-1].model, 0) + 1
    return {
        "invoices": len(results),
        "accepted": len(accepted),
        "human_review": len(results) - len(accepted),
        "accepted_by_tier": by_tier,
        "model_cost_usd": round(total_cost, 4),
        "cost_per_accepted_invoice_usd": round(total_cost / len(accepted), 5) if accepted else None,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: python -m invoice_pipeline.extract <invoice_folder> <results.jsonl>")
        sys.exit(2)
    print(json.dumps(run_folder(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
