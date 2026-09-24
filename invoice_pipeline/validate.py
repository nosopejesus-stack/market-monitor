"""Deterministic checks for Spanish supplier invoices.

CODE WHERE DETERMINISM MATTERS: everything that can be checked with arithmetic or a
check digit is checked here, never by the model. A failed check escalates the invoice
to a stronger model and then to a human; it is never silently "fixed".
"""
from __future__ import annotations

import re
from datetime import date

from .schema import Invoice

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
CIF_CONTROL_LETTERS = "JABCDEFGHI"
VAT_RATES = {0.0, 4.0, 5.0, 10.0, 21.0}          # 5% existed only temporarily (2022-2024); flagged below
SURCHARGE_RATES = {0.0, 0.5, 1.4, 1.75, 5.2}     # recargo de equivalencia
TOL = 0.02                                        # EUR rounding tolerance per line


def valid_nif(raw: str) -> bool:
    """DNI, NIE or CIF with correct control character. Accepts an optional 'ES' VAT prefix."""
    s = re.sub(r"[\s\-.]", "", raw or "").upper()
    if s.startswith("ES") and len(s) == 11:
        s = s[2:]
    if re.fullmatch(r"\d{8}[A-Z]", s):
        return DNI_LETTERS[int(s[:8]) % 23] == s[8]
    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", s):
        return DNI_LETTERS[int(str("XYZ".index(s[0])) + s[1:8]) % 23] == s[8]
    if re.fullmatch(r"[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]", s):
        digits = s[1:8]
        even = sum(int(d) for d in digits[1::2])
        odd = sum(sum(divmod(int(d) * 2, 10)) for d in digits[0::2])
        ctrl = (10 - (even + odd) % 10) % 10
        c = s[8]
        if s[0] in "PQRSNW" or s[0] in "KLM":
            return c == CIF_CONTROL_LETTERS[ctrl]
        if s[0] in "ABEH":
            return c == str(ctrl)
        return c in (str(ctrl), CIF_CONTROL_LETTERS[ctrl])
    return False


# Regimes the pilot validator cannot check deterministically yet. They go straight to a human with
# a specific reason instead of being escalated to a stronger model (which would fail the same checks).
UNSUPPORTED_REGIMES = {"IGIC", "IPSI", "EXTRANJERO", "OTRO"}


def unsupported_reason(inv: Invoice) -> str | None:
    if inv.tax_regime in UNSUPPORTED_REGIMES:
        return f"tax regime {inv.tax_regime} not supported by the pilot validator"
    return None


def check(inv: Invoice, today: date | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Any error means the extraction is not trusted."""
    errors, warnings = [], []
    today = today or date.today()
    if not valid_nif(inv.issuer_nif):
        errors.append(f"issuer NIF '{inv.issuer_nif}' fails check digit")
    if inv.recipient_nif and not valid_nif(inv.recipient_nif):
        errors.append(f"recipient NIF '{inv.recipient_nif}' fails check digit")
    if not inv.invoice_number.strip():
        errors.append("missing invoice number")
    try:
        d = date.fromisoformat(inv.issue_date)
        if d > today:
            errors.append(f"issue date {d} is in the future")
        if d.year < today.year - 6:
            warnings.append(f"issue date {d} is more than 6 years old")
    except ValueError:
        errors.append(f"issue date '{inv.issue_date}' is not ISO YYYY-MM-DD")
    if not inv.vat_lines:
        errors.append("no VAT breakdown lines")
    zero_vat_regime = inv.tax_regime in {"EXENTO", "INVERSION_SUJETO_PASIVO"}
    base_sum = vat_sum = surcharge_sum = 0.0
    for i, ln in enumerate(inv.vat_lines):
        if zero_vat_regime and (ln.vat_rate != 0 or ln.vat_amount != 0):
            errors.append(f"line {i}: {inv.tax_regime} invoice with non-zero VAT")
        if ln.vat_rate not in VAT_RATES:
            errors.append(f"line {i}: VAT rate {ln.vat_rate}% is not a Spanish rate")
        elif ln.vat_rate == 5.0:
            warnings.append(f"line {i}: 5% VAT only applied temporarily; confirm")
        if abs(ln.base * ln.vat_rate / 100 - ln.vat_amount) > TOL:
            errors.append(f"line {i}: base {ln.base} x {ln.vat_rate}% != VAT {ln.vat_amount}")
        if ln.surcharge_rate not in SURCHARGE_RATES:
            errors.append(f"line {i}: surcharge rate {ln.surcharge_rate}% unknown")
        if abs(ln.base * ln.surcharge_rate / 100 - ln.surcharge_amount) > TOL:
            errors.append(f"line {i}: surcharge arithmetic mismatch")
        base_sum += ln.base; vat_sum += ln.vat_amount; surcharge_sum += ln.surcharge_amount
    if abs(base_sum * inv.withholding_rate / 100 - inv.withholding_amount) > TOL * max(1, len(inv.vat_lines)):
        errors.append(f"withholding {inv.withholding_rate}% of {base_sum:.2f} != {inv.withholding_amount}")
    if inv.non_taxable_amount < 0:
        warnings.append("negative suplidos amount")
    expected_total = base_sum + vat_sum + surcharge_sum - inv.withholding_amount + inv.non_taxable_amount
    if abs(expected_total - inv.total) > TOL * max(1, len(inv.vat_lines)):
        errors.append(f"total {inv.total} != bases+VAT+surcharge-withholding+suplidos {expected_total:.2f}")
    if inv.total < 0:
        warnings.append("negative total: credit note (factura rectificativa)?")
    return errors, warnings
