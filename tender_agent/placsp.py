"""Discovery agent (deterministic): open tenders + past winners from the PLACSP Atom feed.

Source: "Licitaciones publicadas en los perfiles del contratante ubicados en la Plataforma de
Contratación del Sector Público" (open data, Ministerio de Hacienda). Monthly zips:
  https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_YYYYMM.zip
XML paths follow the CODICE place-ext schema as used by the working open-source reader
b-thinking/CSPAtomReader. Fields not used by that reader (deadline, location, status, winner NIF)
follow the same schema and must be checked on the first real file (see README).

Output: prospects = companies that WON a contract with the same CPV family in the same province,
matched to OPEN tenders with enough days left to write a memoria. That match is the
hyper-specific reason to contact them.
"""
from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "cbc": "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2",
    "cbc-place-ext": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2",
    "cac-place-ext": "urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2",
}
# ContractFolderStatusCode values: PRE anuncio previo, PUB en plazo, EV pendiente de adjudicación,
# ADJ adjudicada, RES resuelta, ANUL anulada.
OPEN_STATUSES = {"PUB"}
# TenderResult ResultCode: 8 = adjudicado (used by CSPAtomReader for awarded winners); 9 = formalizado (ASM)
AWARD_CODES = {"8", "9"}


@dataclass
class Award:
    company: str
    nif: str
    amount: float | None
    date: str


@dataclass
class Tender:
    entry_id: str
    link: str
    folder_id: str
    title: str
    status: str
    buyer: str
    cpvs: list[str]
    budget_ex_vat: float | None
    province: str
    deadline: str
    legal_doc_uri: str = ""
    technical_doc_uri: str = ""
    awards: list[Award] = field(default_factory=list)


def _t(node, path):
    el = node.find(path, NS) if node is not None else None
    return (el.text or "").strip() if el is not None and el.text else ""


def _f(node, path):
    try:
        return float(_t(node, path))
    except ValueError:
        return None


def parse_feed(path: str | Path) -> list[Tender]:
    root = ET.parse(path).getroot()
    out = []
    for e in root.findall("atom:entry", NS):
        cfs = e.find("cac-place-ext:ContractFolderStatus", NS)
        if cfs is None:
            continue
        proj = cfs.find("cac:ProcurementProject", NS)
        link = e.find("atom:link", NS)
        t = Tender(
            entry_id=_t(e, "atom:id"),
            link=link.get("href", "") if link is not None else "",
            folder_id=_t(cfs, "cbc:ContractFolderID"),
            title=_t(proj, "cbc:Name") or _t(e, "atom:title"),
            status=_t(cfs, "cbc-place-ext:ContractFolderStatusCode"),
            buyer=_t(cfs, "cac-place-ext:LocatedContractingParty/cac:Party/cac:PartyName/cbc:Name"),
            cpvs=[(c.text or "").strip() for c in cfs.findall(
                "cac:ProcurementProject/cac:RequiredCommodityClassification/cbc:ItemClassificationCode", NS)],
            budget_ex_vat=_f(proj, "cac:BudgetAmount/cbc:TaxExclusiveAmount"),
            province=_t(proj, "cac:RealizedLocation/cbc:CountrySubentity"),
            deadline=_t(cfs, "cac:TenderingProcess/cac:TenderSubmissionDeadlinePeriod/cbc:EndDate"),
            legal_doc_uri=_t(cfs, "cac:LegalDocumentReference/cac:Attachment/cac:ExternalReference/cbc:URI"),
            technical_doc_uri=_t(cfs, "cac:TechnicalDocumentReference/cac:Attachment/cac:ExternalReference/cbc:URI"),
        )
        for r in cfs.findall("cac:TenderResult", NS):
            if _t(r, "cbc:ResultCode") in AWARD_CODES:
                t.awards.append(Award(
                    company=_t(r, "cac:WinningParty/cac:PartyName/cbc:Name"),
                    nif=_t(r, "cac:WinningParty/cac:PartyIdentification/cbc:ID"),
                    amount=_f(r, "cac:AwardedTenderedProject/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount"),
                    date=_t(r, "cbc:AwardDate")))
        out.append(t)
    return out


def latest_by_folder(tenders: list[Tender]) -> list[Tender]:
    """The feed repeats a tender on every status change; keep the last entry per folder+buyer."""
    seen = {}
    for t in tenders:
        seen[(t.folder_id, t.buyer)] = t
    return list(seen.values())


def _cpv_match(cpvs, prefixes):
    return any(c.startswith(p) for c in cpvs for p in prefixes)


def _norm(s: str) -> str:
    return " ".join((s or "").upper().replace(",", " ").replace(".", " ").split())


def open_tenders(tenders, cpv_prefixes, provinces=None, today: date | None = None, min_days=7, max_days=45,
                 min_budget=30_000):
    today = today or date.today()
    out = []
    for t in tenders:
        if t.status not in OPEN_STATUSES or not _cpv_match(t.cpvs, cpv_prefixes):
            continue
        if provinces and _norm(t.province) not in {_norm(p) for p in provinces}:
            continue
        if (t.budget_ex_vat or 0) < min_budget or not t.deadline:
            continue
        days = (datetime.fromisoformat(t.deadline[:10]).date() - today).days
        if min_days <= days <= max_days:
            out.append((t, days))
    return sorted(out, key=lambda x: x[1])


def winners(tenders, cpv_prefixes, provinces=None):
    """company -> list of (tender, award) in the CPV family (and provinces, if given)."""
    by = {}
    for t in tenders:
        if not t.awards or not _cpv_match(t.cpvs, cpv_prefixes):
            continue
        if provinces and _norm(t.province) not in {_norm(p) for p in provinces}:
            continue
        for a in t.awards:
            if a.company:
                by.setdefault((_norm(a.company), a.nif), []).append((t, a))
    return by


def prospects(tenders, cpv_prefixes, today=None, **kw):
    """Rows: one per (company, open tender in a province where the company already won)."""
    tenders = latest_by_folder(tenders)
    opens = open_tenders(tenders, cpv_prefixes, today=today, **kw)
    wins = winners(tenders, cpv_prefixes)
    rows = []
    for (company, nif), items in wins.items():
        won_provinces = {_norm(t.province) for t, _ in items}
        total = sum(a.amount or 0 for _, a in items)
        largest = max((a.amount or 0 for _, a in items), default=0)
        for t, days in opens:
            if _norm(t.province) not in won_provinces:
                continue
            ref = max(items, key=lambda x: x[1].amount or 0)
            rows.append({
                "company": items[0][1].company, "nif": nif, "province": t.province,
                "past_wins": len(items), "past_awarded_eur": round(total, 2), "largest_award_eur": round(largest, 2),
                "reference_win": f"{ref[0].title} — {ref[0].buyer} ({ref[1].date[:10]}, {ref[1].amount or 0:,.0f} €)",
                "open_tender": t.title, "open_buyer": t.buyer, "open_budget_ex_vat": t.budget_ex_vat,
                "deadline": t.deadline[:10], "days_left": days, "tender_link": t.link,
                "pliego_admin": t.legal_doc_uri, "pliego_tecnico": t.technical_doc_uri,
                "status": "NOT CONTACTED",
            })
    return sorted(rows, key=lambda r: (r["days_left"], -r["past_wins"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find tender-writing prospects from PLACSP Atom files")
    ap.add_argument("atom_files", nargs="+")
    ap.add_argument("--cpv", nargs="+", default=["9091", "90919", "77311", "50700"],
                    help="CPV prefixes (default: building cleaning, gardening, building maintenance)")
    ap.add_argument("--today", default=None)
    ap.add_argument("--min-days", type=int, default=7)
    ap.add_argument("--max-days", type=int, default=45)
    ap.add_argument("--max-largest-award", type=float, default=3_000_000,
                    help="exclude companies whose largest award exceeds this (big groups are not SME buyers)")
    ap.add_argument("--out", default="prospects.csv")
    a = ap.parse_args(argv)
    tenders = [t for f in a.atom_files for t in parse_feed(f)]
    today = date.fromisoformat(a.today) if a.today else None
    rows = [r for r in prospects(tenders, a.cpv, today=today, min_days=a.min_days, max_days=a.max_days)
            if r["largest_award_eur"] <= a.max_largest_award]
    with open(a.out, "w", newline="") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    print(f"{len(tenders)} entries parsed; {len(rows)} prospect rows -> {a.out}", file=sys.stderr)
    return rows


if __name__ == "__main__":
    main()
