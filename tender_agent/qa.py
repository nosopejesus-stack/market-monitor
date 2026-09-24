"""QA agent (deterministic) for a memoria técnica draft.

Draft convention (enforced by the drafting prompt): each scored section starts with a heading
that carries the criterion id, e.g. "## [C2] Organización y plan de trabajo".

Checks, by severity:
  CRITICAL  contamination: economic data or values of formula-scored criteria inside the
            technical (judgment) envelope. Tribunals uphold exclusion for this (see README).
  CRITICAL  a judgment criterion with no section.
  MAJOR     required content missing from a section; page limit exceeded; placeholders left.
  MINOR     claims the client must confirm (certifications, guarantees, superlatives).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field

CURRENCY = re.compile(r"(\d[\d.,]*\s?(€|eur\b|euros?\b))|(€\s?\d)", re.I)
ECONOMIC_TERMS = ["oferta economica", "precio ofertado", "precio unitario", "importe ofertado", "baja ofertada",
                  "porcentaje de baja", "descuento sobre", "presupuesto ofertado", "coste por hora", "precio/hora",
                  "tarifa horaria"]
CLAIMS = ["garantizamos", "100 %", "100%", "el mejor", "la mejor", "lider", "certificad", "iso 9001", "iso 14001",
          "iso 45001", "sin coste", "gratuit"]
PLACEHOLDER = re.compile(r"\[\[.*?\]\]|\bPENDIENTE\b|\bXXX+\b|<<.*?>>")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


@dataclass
class Finding:
    severity: str
    check: str
    detail: str
    where: str = ""


@dataclass
class Report:
    passed: bool
    words: int
    est_pages: float
    findings: list[Finding] = field(default_factory=list)


def split_sections(md: str) -> dict[str, str]:
    """criterion id -> section text (heading line through the next heading of same or higher level)."""
    out, cur, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r"^#{1,3}\s*\[([A-Za-z]\d+)\]", line)
        if m:
            if cur:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1).upper(), [line]
        elif re.match(r"^#{1,2}\s", line) and cur:
            out[cur] = "\n".join(buf); cur, buf = None, []
        elif cur:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf)
    return out


def check(md: str, spec: dict) -> Report:
    f: list[Finding] = []
    text = norm(md)
    words = len(re.findall(r"\w+", md))
    wpp = spec.get("limits", {}).get("words_per_page", 450)
    est_pages = round(words / wpp, 1)
    sections = split_sections(md)
    judged = [c for c in spec["criteria"] if c["type"] == "juicio_valor"]
    formula = [c for c in spec["criteria"] if c["type"] == "formula"]

    # coverage
    for c in judged:
        sec = sections.get(c["id"].upper())
        if sec is None:
            f.append(Finding("CRITICAL", "coverage", f"no section for judgment criterion {c['id']} '{c['name']}' ({c.get('points', '?')} pts)"))
            continue
        for term in c.get("must_include", []):
            if norm(term) not in norm(sec):
                f.append(Finding("MAJOR", "required_content", f"'{term}' not found", c["id"]))
    for sid in sections:
        if sid not in {c["id"].upper() for c in spec["criteria"]}:
            f.append(Finding("MINOR", "unknown_section", f"section [{sid}] does not map to any criterion"))

    # contamination (only meaningful when something is scored by formula)
    if formula:
        for m in CURRENCY.finditer(md):
            ctx = md[max(0, m.start() - 60): m.end() + 30].replace("\n", " ")
            f.append(Finding("CRITICAL", "contamination_currency", f"monetary amount in technical memoria: '…{ctx}…'"))
        for term in ECONOMIC_TERMS:
            if term in text:
                f.append(Finding("CRITICAL", "contamination_economic_term", f"economic term '{term}' in technical memoria"))
        for c in formula:
            for kw in c.get("keywords", []):
                for m in re.finditer(re.escape(norm(kw)), text):
                    window = text[m.start(): m.end() + 80]
                    if re.search(r"\d", window):
                        f.append(Finding("CRITICAL", "contamination_formula_value",
                                         f"formula criterion {c['id']} '{c['name']}' seems quantified in the memoria: '…{window[:90]}…'"))
                        break

    # length and format
    max_pages = spec.get("limits", {}).get("max_pages")
    if max_pages and est_pages > max_pages:
        f.append(Finding("MAJOR", "length", f"estimated {est_pages} pages > limit {max_pages} ({wpp} words/page)"))
    for m in PLACEHOLDER.finditer(md):
        f.append(Finding("MAJOR", "placeholder", f"unfilled placeholder '{m.group(0)[:60]}'"))
    for name in spec.get("names_not_allowed", []):
        if norm(name) in text:
            f.append(Finding("CRITICAL", "foreign_name", f"name of another company/buyer found: '{name}'"))
    company = spec.get("company_name")
    if company and norm(company) not in text:
        f.append(Finding("MAJOR", "company_name", f"bidder name '{company}' does not appear"))

    # claims the client must confirm
    for term in CLAIMS:
        if norm(term) in text:
            f.append(Finding("MINOR", "claim_to_verify", f"claim '{term}' must be confirmed by the client (evidence or remove)"))

    passed = not any(x.severity in ("CRITICAL", "MAJOR") for x in f)
    return Report(passed, words, est_pages, f)


def to_markdown(r: Report) -> str:
    lines = [f"# QA — {'APTO' if r.passed else 'NO APTO'}", "",
             f"Palabras: {r.words} · páginas estimadas: {r.est_pages}", ""]
    if not r.findings:
        lines.append("Sin incidencias.")
    for sev in ["CRITICAL", "MAJOR", "MINOR"]:
        items = [x for x in r.findings if x.severity == sev]
        if items:
            lines += [f"## {sev} ({len(items)})", ""] + [f"- **{x.check}** {('['+x.where+'] ') if x.where else ''}{x.detail}" for x in items] + [""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("memoria_md"); ap.add_argument("criteria_json")
    a = ap.parse_args(argv)
    r = check(open(a.memoria_md).read(), json.load(open(a.criteria_json)))
    print(to_markdown(r))
    return 0 if r.passed else 1


if __name__ == "__main__":
    sys.exit(main())
