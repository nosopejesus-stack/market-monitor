"""Analysis + drafting agent (one agent, two calls). Everything checkable lives in qa.py.

1. analyze(pliego PDFs) -> criteria spec (structured output), validated before use.
2. draft(spec, client profile) -> memoria in Markdown, one "## [ID]" section per judgment criterion.
   Facts the client has not provided become [[PENDIENTE: ...]] placeholders, which QA blocks until
   filled. The model is told never to invent certifications, staff, machinery or numbers.
Costs are recorded per call so every job has a real AI cost.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-opus-5"
PRICE_USD_PER_MTOK = (5.0, 25.0)  # input, output (Claude API list price, skill reference 2026-06-24)


class Criterion(BaseModel):
    id: str = Field(description="C1, C2... for judgment criteria; F1, F2... for formula criteria (price included)")
    name: str
    points: float
    type: Literal["juicio_valor", "formula"]
    must_include: list[str] = Field(default_factory=list, description="Contents the pliego explicitly requires in this section")
    keywords: list[str] = Field(default_factory=list, description="For formula criteria: words that identify it (e.g. 'bolsa de horas')")
    source: str = Field(description="Clause/page of the pliego where the criterion is defined")


class Limits(BaseModel):
    max_pages: int | None = None
    words_per_page: int = 450
    format_rules: list[str] = Field(default_factory=list, description="Font, size, spacing, annex rules, envelope name")


class Spec(BaseModel):
    tender_title: str
    buyer: str
    deadline: str = Field(description="ISO date-time of submission deadline if stated, else empty")
    lots: list[str] = Field(default_factory=list)
    judgment_points_total: float
    formula_points_total: float
    criteria: list[Criterion]
    limits: Limits
    exclusion_risks: list[str] = Field(default_factory=list, description="Clauses that cause exclusion (envelope mixing, page limits, signatures)")
    solvency: list[str] = Field(default_factory=list, description="Economic/technical solvency requirements, as stated")
    subrogation: str = Field("", description="Staff subrogation obligations, if any")


@dataclass
class Usage:
    calls: list[dict] = field(default_factory=list)

    def add(self, step: str, u):
        cost = (u.input_tokens * PRICE_USD_PER_MTOK[0] + u.output_tokens * PRICE_USD_PER_MTOK[1]) / 1e6
        self.calls.append({"step": step, "input_tokens": u.input_tokens, "output_tokens": u.output_tokens, "usd": round(cost, 4)})

    @property
    def usd(self) -> float:
        return round(sum(c["usd"] for c in self.calls), 4)


def _pdf_block(p: Path) -> dict:
    return {"type": "document", "title": p.name,
            "source": {"type": "base64", "media_type": "application/pdf", "data": base64.standard_b64encode(p.read_bytes()).decode()}}


ANALYZE_PROMPT = """Eres analista de licitaciones públicas en España (Ley 9/2017). Lee los pliegos adjuntos (PCAP y PPT).
Extrae los criterios de adjudicación EXACTAMENTE como están: nombre, puntos, si se valoran por juicio de valor o por fórmula,
y los contenidos que el pliego exige para cada criterio de juicio de valor. Para los criterios de fórmula (incluido el precio),
lista palabras clave que los identifiquen (p. ej. 'bolsa de horas', 'mejoras', 'plazo de respuesta'), porque su valor NO puede
aparecer en la memoria técnica. Indica límites de páginas y formato, riesgos de exclusión, solvencia y subrogación.
Cita la cláusula o página de cada criterio. Si algo no aparece en los pliegos, déjalo vacío: no lo supongas."""

DRAFT_PROMPT = """Redacta la memoria técnica (sobre de criterios de juicio de valor) para la licitación descrita en SPEC,
en nombre de la empresa descrita en PERFIL. Reglas obligatorias:
1. Una sección por cada criterio de juicio de valor, con encabezado exacto '## [ID] Nombre', en el orden del pliego, y
   cubriendo todos sus contenidos exigidos (must_include).
2. NUNCA incluyas precios, importes, porcentajes de baja ni el valor de ningún criterio de fórmula (ni siquiera las
   palabras clave de esos criterios acompañadas de cifras): provocaría la exclusión por contaminación de sobres.
3. No inventes datos de la empresa: plantilla, maquinaria, certificaciones, clientes o cifras que no estén en PERFIL se
   escriben como [[PENDIENTE: qué dato falta]].
4. Concreta: frecuencias, turnos, protocolos, sustituciones, control de calidad, formación, medios, según el PPT.
5. Respeta el límite de páginas (≈{wpp} palabras por página, máximo {max_pages} páginas).
Devuelve solo la memoria en Markdown."""


def analyze(pdfs: list[Path], client: anthropic.Anthropic | None = None, usage: Usage | None = None) -> Spec:
    client = client or anthropic.Anthropic()
    usage = usage or Usage()
    content = [_pdf_block(p) for p in pdfs] + [{"type": "text", "text": ANALYZE_PROMPT}]
    resp = client.beta.messages.parse(
        model=MODEL, max_tokens=16000, messages=[{"role": "user", "content": content}], output_format=Spec,
        thinking={"type": "adaptive"}, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    usage.add("analyze", resp.usage)
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError(f"analysis failed (stop_reason={resp.stop_reason})")
    spec = resp.parsed_output
    validate_spec(spec)
    return spec


def validate_spec(spec: Spec) -> None:
    """Deterministic sanity checks; a failed check means a human reads the pliego clause."""
    j = sum(c.points for c in spec.criteria if c.type == "juicio_valor")
    fm = sum(c.points for c in spec.criteria if c.type == "formula")
    problems = []
    if abs(j - spec.judgment_points_total) > 0.01:
        problems.append(f"judgment points {j} != stated total {spec.judgment_points_total}")
    if abs(fm - spec.formula_points_total) > 0.01:
        problems.append(f"formula points {fm} != stated total {spec.formula_points_total}")
    ids = [c.id for c in spec.criteria]
    if len(ids) != len(set(ids)):
        problems.append("duplicate criterion ids")
    if not any(c.type == "juicio_valor" for c in spec.criteria):
        problems.append("no judgment criteria: a memoria may not be scored at all")
    if problems:
        raise ValueError("; ".join(problems))


def draft(spec: Spec, profile: dict, client: anthropic.Anthropic | None = None, usage: Usage | None = None) -> str:
    client = client or anthropic.Anthropic()
    usage = usage or Usage()
    prompt = DRAFT_PROMPT.format(wpp=spec.limits.words_per_page, max_pages=spec.limits.max_pages or "sin límite")
    msg = f"SPEC:\n{spec.model_dump_json(indent=1)}\n\nPERFIL:\n{json.dumps(profile, ensure_ascii=False, indent=1)}\n\n{prompt}"
    with client.messages.stream(model=MODEL, max_tokens=64000, thinking={"type": "adaptive"},
                                messages=[{"role": "user", "content": msg}]) as stream:
        final = stream.get_final_message()
    usage.add("draft", final.usage)
    if final.stop_reason == "refusal":
        raise RuntimeError("drafting refused")
    return "".join(b.text for b in final.content if b.type == "text")


def spec_for_qa(spec: Spec, company_name: str, names_not_allowed: list[str] | None = None) -> dict:
    d = json.loads(spec.model_dump_json())
    d["company_name"] = company_name
    d["names_not_allowed"] = names_not_allowed or []
    d["limits"] = {"max_pages": spec.limits.max_pages, "words_per_page": spec.limits.words_per_page}
    return d
