"""Contracted-power audit for Spanish electricity supplies (2.0TD / 3.0TD).

Deterministic by design: no AI, no market data. Every price comes from the
customer's own invoice (EUR per kW per day, per period), so the saving estimate
is only as uncertain as the demand data.

Policy implemented: NO-EXCESS. Recommended power per period = highest observed
monthly maximum demand in that period x (1 + margin), rounded up, then forced
non-decreasing P1 <= P2 <= ... <= P6 (3.0TD). Because the recommendation never
sits below an observed peak, the audit does not rely on the excess-power penalty
formula (changed by CNMC Circular 1/2025 and NOT verified in this repo).

Known limitations (surface them to the customer, never hide them):
- Monthly maxima come from invoices or Datadis `get-max-power`; a future peak above
  history would incur excess charges. The margin is the buffer for that.
- Rules on how often power can be lowered, fees for later increases, and whether
  values must be "normalised" are UNVERIFIED here and must be checked with the
  distributor before advising a change.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field

PERIODS = {"2.0TD": ["P1", "P2"], "3.0TD": ["P1", "P2", "P3", "P4", "P5", "P6"]}
MIN_MONTHS_FULL_CONFIDENCE = 12


@dataclass
class Supply:
    name: str
    tariff: str
    contracted_kw: dict[str, float]
    price_eur_kw_day: dict[str, float]
    monthly_max_kw: list[dict[str, float]]  # one dict per month: {"month": "2026-01", "P1": .., ...}
    reactive_eur_last12: float = 0.0
    excess_eur_last12: float = 0.0


@dataclass
class AuditResult:
    name: str
    tariff: str
    months_of_data: int
    rows: list[dict] = field(default_factory=list)
    annual_saving_eur: float = 0.0
    reactive_eur_last12: float = 0.0
    excess_eur_last12: float = 0.0
    warnings: list[str] = field(default_factory=list)


def _ceil(x: float, step: float) -> float:
    return math.ceil(round(x / step, 9)) * step


def audit(s: Supply, margin: float = 0.10, step_kw: float = 0.1) -> AuditResult:
    if s.tariff not in PERIODS:
        raise ValueError(f"unsupported tariff {s.tariff!r}; expected one of {list(PERIODS)}")
    periods = PERIODS[s.tariff]
    for key, d in [("contracted_kw", s.contracted_kw), ("price_eur_kw_day", s.price_eur_kw_day)]:
        missing = [p for p in periods if p not in d]
        if missing:
            raise ValueError(f"{s.name}: {key} missing periods {missing}")
    if not s.monthly_max_kw:
        raise ValueError(f"{s.name}: no demand data")

    res = AuditResult(s.name, s.tariff, len(s.monthly_max_kw),
                      reactive_eur_last12=s.reactive_eur_last12, excess_eur_last12=s.excess_eur_last12)
    peak = {p: max(float(m.get(p, 0.0) or 0.0) for m in s.monthly_max_kw) for p in periods}
    target = {p: _ceil(peak[p] * (1 + margin), step_kw) for p in periods}
    # Access-tariff rule for 6-period tariffs: contracted power must not decrease from P1 to P6.
    rec, floor = {}, 0.0
    for p in periods:
        floor = max(floor, target[p]) if s.tariff == "3.0TD" else target[p]
        rec[p] = round(floor, 3)

    for p in periods:
        cur, new = float(s.contracted_kw[p]), rec[p]
        price_year = float(s.price_eur_kw_day[p]) * 365
        saving = max(cur - new, 0.0) * price_year
        res.rows.append({"period": p, "contracted_kw": cur, "observed_peak_kw": peak[p],
                         "recommended_kw": new, "eur_per_kw_year": round(price_year, 4),
                         "annual_saving_eur": round(saving, 2),
                         "note": "raise: peak exceeds contract" if new > cur else ""})
        res.annual_saving_eur += saving
        if new > cur:
            res.warnings.append(f"{p}: observed peak {peak[p]:.1f} kW with margin exceeds contract {cur:.1f} kW; "
                                "supply may be paying excess charges — review before lowering other periods.")
    res.annual_saving_eur = round(res.annual_saving_eur, 2)

    if res.months_of_data < MIN_MONTHS_FULL_CONFIDENCE:
        res.warnings.append(f"only {res.months_of_data} months of demand data; seasonal peaks may be missing "
                            f"(need {MIN_MONTHS_FULL_CONFIDENCE}). Treat the saving as optimistic.")
    if s.tariff == "3.0TD" and max(rec.values()) <= 15.0:
        res.warnings.append("all recommended powers <= 15 kW: supply might qualify for 2.0TD; evaluate separately.")
    if s.tariff == "2.0TD" and max(rec.values()) > 15.0:
        res.warnings.append("recommended power > 15 kW is outside 2.0TD scope.")
    if s.reactive_eur_last12 > 0:
        res.warnings.append(f"reactive-energy charges of EUR {s.reactive_eur_last12:.2f} in the last 12 months: "
                            "a capacitor bank quote may remove them (capex not included in the saving).")
    return res


def load_supply(obj: dict) -> Supply:
    return Supply(name=obj["name"], tariff=obj["tariff"], contracted_kw=obj["contracted_kw"],
                  price_eur_kw_day=obj["price_eur_kw_day"], monthly_max_kw=obj["monthly_max_kw"],
                  reactive_eur_last12=obj.get("reactive_eur_last12", 0.0),
                  excess_eur_last12=obj.get("excess_eur_last12", 0.0))


def render_markdown(r: AuditResult, margin: float) -> str:
    lines = [f"# Auditoría de potencia contratada — {r.name}", "",
             f"Tarifa: **{r.tariff}** · Meses de datos: **{r.months_of_data}** · Margen de seguridad: **{margin:.0%}**", "",
             "| Periodo | Contratada kW | Pico observado kW | Recomendada kW | €/kW·año (su factura) | Ahorro anual € |",
             "|---|---|---|---|---|---|"]
    for row in r.rows:
        lines.append(f"| {row['period']} | {row['contracted_kw']:.1f} | {row['observed_peak_kw']:.1f} | "
                     f"{row['recommended_kw']:.1f} | {row['eur_per_kw_year']:.2f} | {row['annual_saving_eur']:.2f} |")
    lines += ["", f"**Ahorro anual estimado en término de potencia: {r.annual_saving_eur:.2f} €** "
              "(ESTIMACIÓN basada en sus precios de factura y sus picos históricos; no incluye IVA ni impuesto eléctrico).", ""]
    if r.reactive_eur_last12:
        lines.append(f"Cargos por energía reactiva últimos 12 meses: {r.reactive_eur_last12:.2f} €.")
    if r.warnings:
        lines += ["", "## Avisos", ""] + [f"- {w}" for w in r.warnings]
    lines += ["", "_Antes de solicitar el cambio a la distribuidora, verificar condiciones y costes de modificación "
              "de potencia y de una posible subida futura._"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m energy_audit.optimizer supply.json [margin]")
        return 2
    margin = float(argv[2]) if len(argv) > 2 else 0.10
    with open(argv[1]) as f:
        data = json.load(f)
    for obj in data if isinstance(data, list) else [data]:
        print(render_markdown(audit(load_supply(obj), margin=margin), margin))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
