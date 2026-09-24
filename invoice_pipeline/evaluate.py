"""Evaluate pipeline output against ground truth (the gestoría's own posted entries).

Usage:
  python -m invoice_pipeline.evaluate runs/<batch>.jsonl ground_truth.csv [--eur-per-hour 18] [--usd-eur 0.92]

ground_truth.csv columns (one row per document; amounts in EUR, dot decimal):
  file, issuer_name, issuer_nif, invoice_number, issue_date (YYYY-MM-DD), base_total, vat_total, total,
  vat_rates (e.g. "21;10"), duplicate_of (file name or empty), review_seconds (measured, optional),
  category (layout/scan/handwritten/... free text for stratified reporting, optional)

The most important number is the FALSE-ACCEPT rate: invoices the pipeline accepted automatically that
have at least one wrong key field. Arithmetic validation cannot catch a consistent misread (e.g. every
amount read with the wrong decimal separator), so this can only be measured against ground truth.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from difflib import SequenceMatcher
from pathlib import Path

from .duplicates import find_duplicates, norm_nif, norm_number

KEY_FIELDS = ["issuer_nif", "invoice_number", "issue_date", "base_total", "vat_total", "vat_rates", "total"]
ALL_FIELDS = ["issuer_name"] + KEY_FIELDS


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def required_n(true_rate: float, target_lower: float, z: float = 1.96) -> int:
    """Smallest n for which the Wilson lower bound at the observed rate exceeds target_lower."""
    for n in range(10, 200_000):
        if wilson(round(true_rate * n), n, z)[0] >= target_lower:
            return n
    return -1


def _pred_fields(inv: dict) -> dict:
    lines = inv.get("vat_lines", [])
    return {"issuer_name": inv.get("issuer_name", ""), "issuer_nif": inv.get("issuer_nif", ""),
            "invoice_number": inv.get("invoice_number", ""), "issue_date": inv.get("issue_date", ""),
            "base_total": round(sum(l["base"] for l in lines), 2), "vat_total": round(sum(l["vat_amount"] for l in lines), 2),
            "vat_rates": sorted({float(l["vat_rate"]) for l in lines}), "total": round(float(inv.get("total", 0)), 2)}


def _truth_fields(row: dict) -> dict:
    return {"issuer_name": row["issuer_name"], "issuer_nif": row["issuer_nif"], "invoice_number": row["invoice_number"],
            "issue_date": row["issue_date"], "base_total": round(float(row["base_total"]), 2),
            "vat_total": round(float(row["vat_total"]), 2),
            "vat_rates": sorted({float(x) for x in row["vat_rates"].split(";") if x.strip()}),
            "total": round(float(row["total"]), 2)}


def field_ok(field: str, pred, truth) -> bool:
    if field == "issuer_name":
        return SequenceMatcher(None, str(pred).lower(), str(truth).lower()).ratio() >= 0.85
    if field == "issuer_nif":
        return norm_nif(pred) == norm_nif(truth)
    if field == "invoice_number":
        return norm_number(pred) == norm_number(truth)
    if field in ("base_total", "vat_total", "total"):
        return abs(float(pred) - float(truth)) <= 0.01
    return pred == truth


def evaluate(results: list[dict], truth: dict[str, dict], eur_per_hour: float = 18.0, usd_eur: float = 0.92) -> dict:
    n = len(results)
    field_hits = {f: [0, 0] for f in ALL_FIELDS}
    accepted = review = false_accept = true_accept = unnecessary_review = 0
    model_cost_usd = sum(r.get("cost_usd", 0.0) for r in results)
    latencies = sorted(r.get("latency_s", 0.0) for r in results)
    review_seconds = 0.0
    per_category: dict[str, list[int]] = {}
    missing_truth = []
    for r in results:
        name = Path(r["file"]).name
        t = truth.get(name)
        if t is None:
            missing_truth.append(name); continue
        tf = _truth_fields(t)
        review_seconds += float(t.get("review_seconds") or 0)
        inv = r.get("invoice")
        all_ok = False
        if inv:
            pf = _pred_fields(inv)
            oks = {f: field_ok(f, pf[f], tf[f]) for f in ALL_FIELDS}
            for f, ok in oks.items():
                field_hits[f][0] += ok; field_hits[f][1] += 1
            all_ok = all(oks[f] for f in KEY_FIELDS)
        cat = t.get("category") or "unlabelled"
        per_category.setdefault(cat, [0, 0])
        if r["status"] == "accepted":
            accepted += 1
            true_accept += all_ok; false_accept += (not all_ok)
            per_category[cat][0] += all_ok
        else:
            review += 1
            unnecessary_review += all_ok
        per_category[cat][1] += 1
    # duplicates: compare detected groups with ground truth duplicate_of
    dup_input = [{"id": Path(r["file"]).name, **_pred_fields(r["invoice"])} for r in results if r.get("invoice")]
    detected = {i for g in find_duplicates(dup_input) for i in g["ids"][1:]}
    actual = {name for name, t in truth.items() if (t.get("duplicate_of") or "").strip()}
    dup_tp = len(detected & actual)
    eur_model = model_cost_usd * usd_eur
    eur_review = review_seconds / 3600 * eur_per_hour
    fa_ci = wilson(false_accept, accepted)
    inv_acc_ci = wilson(true_accept, accepted)
    return {
        "documents": n, "missing_ground_truth": missing_truth,
        "accepted_automatically": accepted, "sent_to_review": review,
        "exception_rate": review / n if n else float("nan"),
        "field_accuracy": {f: {"correct": c, "of": m, "rate": c / m if m else float("nan"), "ci95": wilson(c, m)}
                           for f, (c, m) in field_hits.items()},
        "invoice_level_accuracy_of_accepted": {"rate": true_accept / accepted if accepted else float("nan"), "ci95": inv_acc_ci},
        "false_accepts": false_accept, "false_accept_rate": {"rate": false_accept / accepted if accepted else float("nan"), "ci95": fa_ci},
        "unnecessary_reviews": unnecessary_review,
        "duplicates": {"actual": len(actual), "detected": len(detected), "true_positive": dup_tp,
                       "false_positive": len(detected - actual), "missed": len(actual - detected)},
        "latency_s": {"p50": latencies[len(latencies) // 2] if latencies else None,
                      "p95": latencies[int(len(latencies) * 0.95) - 1] if latencies else None},
        "cost": {"model_eur": round(eur_model, 4), "human_review_eur": round(eur_review, 2),
                 "model_eur_per_document": round(eur_model / n, 5) if n else None,
                 "total_eur_per_accepted_invoice": round((eur_model + eur_review) / accepted, 4) if accepted else None,
                 "note": "add infrastructure, support and reprocessing from the pilot log for the full unit cost"},
        "by_category_accepted_correct": {k: {"accepted_correct": v[0], "of": v[1]} for k, v in per_category.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_jsonl"); ap.add_argument("ground_truth_csv")
    ap.add_argument("--eur-per-hour", type=float, default=18.0)
    ap.add_argument("--usd-eur", type=float, default=0.92)
    a = ap.parse_args()
    results = [json.loads(l) for l in open(a.results_jsonl) if l.strip()]
    truth = {row["file"]: row for row in csv.DictReader(open(a.ground_truth_csv))}
    print(json.dumps(evaluate(results, truth, a.eur_per_hour, a.usd_eur), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
