"""ROI calculator (for the customer) and job ledger metrics (for us).

Customer ROI: what writing the memoria in-house costs them vs our price, and what the
memoria is worth given the contract at stake. Our metrics: contribution and revenue per
human hour, per job and cumulative. Run: python -m tender_agent.economics
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

JOBS = Path(__file__).resolve().parents[1] / "experiments" / "EXP-006-jobs.csv"
JOB_FIELDS = ["job_id", "date", "client", "tender", "price_eur", "paid_eur", "payment_fee_eur", "ai_usd",
              "human_min_intake", "human_min_review", "human_min_revisions", "human_min_admin",
              "qa_critical_found", "submitted", "result", "client_rating_1_5", "notes"]


def customer_roi(contract_value_eur: float, margin_pct: float, judgment_points: float, inhouse_hours: float,
                 staff_eur_h: float, price_eur: float, points_gain: float = 5.0, p_win_per_point: float = 0.02) -> dict:
    """All inputs are the customer's own numbers (ask them). points_gain and p_win_per_point are
    ASSUMPTIONS to show sensitivity, never promises."""
    inhouse_cost = inhouse_hours * staff_eur_h
    expected_margin = contract_value_eur * margin_pct / 100
    delta_ev = min(points_gain, judgment_points) * p_win_per_point * expected_margin
    return {"inhouse_cost_eur": round(inhouse_cost, 2), "our_price_eur": price_eur,
            "time_saved_value_eur": round(inhouse_cost - price_eur, 2),
            "contract_margin_at_stake_eur": round(expected_margin, 2),
            "expected_value_if_+{:.0f}_points_eur".format(points_gain): round(delta_ev, 2),
            "breakeven_extra_win_probability": round(price_eur / expected_margin, 5) if expected_margin else None}


def job_metrics(path: Path = JOBS, usd_eur: float = 0.92) -> dict:
    if not path.exists():
        return {"jobs": 0}
    rows = list(csv.DictReader(open(path)))
    num = lambda r, k: float(r.get(k) or 0)  # noqa: E731
    paid = sum(num(r, "paid_eur") for r in rows)
    fees = sum(num(r, "payment_fee_eur") for r in rows)
    ai = sum(num(r, "ai_usd") for r in rows) * usd_eur
    minutes = sum(num(r, k) for r in rows for k in JOB_FIELDS if k.startswith("human_min"))
    hours = minutes / 60
    contrib = paid - fees - ai
    return {"jobs": len(rows), "paid_jobs": sum(1 for r in rows if num(r, "paid_eur") > 0), "revenue_eur": round(paid, 2),
            "variable_cost_eur": round(fees + ai, 2), "contribution_eur": round(contrib, 2), "human_hours": round(hours, 2),
            "revenue_per_human_hour_eur": round(paid / hours, 2) if hours else None,
            "contribution_per_human_hour_eur": round(contrib / hours, 2) if hours else None,
            "avg_human_min_per_job": round(minutes / len(rows), 1) if rows else None}


def plan(price=390.0, ai_eur=7.0, fee_pct=0.0, human_min=180) -> dict:
    """Pre-revenue plan for one job (ESTIMATES until the first job is logged)."""
    fee = price * fee_pct
    contrib = price - ai_eur - fee
    return {"price_eur": price, "ai_eur": ai_eur, "payment_fee_eur": round(fee, 2), "contribution_eur": round(contrib, 2),
            "human_min": human_min, "revenue_per_human_hour_eur": round(price / (human_min / 60), 1),
            "contribution_per_human_hour_eur": round(contrib / (human_min / 60), 1)}


if __name__ == "__main__":
    print("plan (ESTIMATE):", plan())
    print("plan, 2nd job same client (ESTIMATE):", plan(human_min=100))
    print("actual jobs:", job_metrics())
    sys.exit(0)
