"""Duplicate supplier-invoice detection (deterministic).

Two invoices are duplicates when they share the issuer NIF and the normalised invoice number
(strong match), or when they share issuer NIF, issue date and total but the numbers differ only
by formatting noise (weak match: flagged for review, never auto-rejected).
"""
from __future__ import annotations

import re
from collections import defaultdict


def norm_nif(s: str) -> str:
    s = re.sub(r"[\s\-.]", "", (s or "").upper())
    return s[2:] if s.startswith("ES") and len(s) == 11 else s


def norm_number(s: str) -> str:
    # "F-2026/001", "F2026 001" and "f2026-0001" collapse to the same key; leading zeros inside digit runs are dropped
    tokens = re.findall(r"[A-Z]+|\d+", (s or "").upper())
    return "".join(str(int(t)) if t.isdigit() else t for t in tokens)


def find_duplicates(invoices: list[dict]) -> list[dict]:
    """invoices: dicts with id, issuer_nif, invoice_number, issue_date, total. Returns duplicate groups."""
    strong, weak = defaultdict(list), defaultdict(list)
    for inv in invoices:
        nif = norm_nif(inv.get("issuer_nif", ""))
        if not nif:
            continue
        strong[(nif, norm_number(inv.get("invoice_number", "")))].append(inv["id"])
        weak[(nif, inv.get("issue_date", ""), round(float(inv.get("total", 0) or 0), 2))].append(inv["id"])
    out, seen = [], set()
    for key, ids in strong.items():
        if len(ids) > 1:
            out.append({"kind": "strong", "key": key, "ids": ids}); seen.add(frozenset(ids))
    for key, ids in weak.items():
        if len(ids) > 1 and frozenset(ids) not in seen:
            out.append({"kind": "weak", "key": key, "ids": ids})
    return out
