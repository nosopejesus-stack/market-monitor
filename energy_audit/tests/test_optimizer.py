import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from energy_audit.optimizer import Supply, audit  # noqa: E402

P6 = ["P1", "P2", "P3", "P4", "P5", "P6"]


def supply(contracted, peaks_by_month, price=0.05, tariff="3.0TD"):
    periods = P6 if tariff == "3.0TD" else ["P1", "P2"]
    return Supply("t", tariff, dict(zip(periods, contracted)), {p: price for p in periods},
                  [dict(zip(periods, m)) for m in peaks_by_month])


def test_overcontracted_saving_uses_invoice_price():
    s = supply([50] * 6, [[20] * 6] * 12, price=0.05)
    r = audit(s, margin=0.10)
    assert all(row["recommended_kw"] == 22.0 for row in r.rows)
    # 28 kW x 6 periods x 0.05 EUR/kW/day x 365
    assert r.annual_saving_eur == pytest.approx(28 * 6 * 0.05 * 365)
    assert not r.warnings


def test_monotonic_p1_to_p6():
    s = supply([40] * 6, [[30, 10, 10, 10, 10, 25]] * 12)
    rec = [row["recommended_kw"] for row in audit(s, margin=0.0).rows]
    assert rec == sorted(rec)
    assert rec[0] == 30.0 and rec[-1] == 30.0


def test_never_recommends_below_observed_peak():
    s = supply([40] * 6, [[18.04] * 6] * 12)
    for row in audit(s, margin=0.0).rows:
        assert row["recommended_kw"] >= row["observed_peak_kw"]


def test_peak_above_contract_warns_and_claims_no_saving_there():
    s = supply([20] * 6, [[25] * 6] * 12)
    r = audit(s, margin=0.0)
    assert r.annual_saving_eur == 0
    assert any("exceeds contract" in w for w in r.warnings)


def test_short_history_warns():
    s = supply([50] * 6, [[20] * 6] * 3)
    assert any("months of demand data" in w for w in audit(s).warnings)


def test_2td_two_periods_independent():
    s = supply([9.9, 9.9], [[4.0, 6.0]] * 12, tariff="2.0TD")
    rec = [row["recommended_kw"] for row in audit(s, margin=0.0).rows]
    assert rec == [4.0, 6.0]


def test_missing_period_rejected():
    s = Supply("t", "3.0TD", {"P1": 10}, {p: 0.05 for p in P6}, [{p: 5 for p in P6}])
    with pytest.raises(ValueError):
        audit(s)
