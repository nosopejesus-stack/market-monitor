import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from invoice_pipeline.schema import Invoice, VatLine  # noqa: E402
from invoice_pipeline.validate import check, valid_nif  # noqa: E402
from invoice_pipeline import extract  # noqa: E402


def test_nif_variants():
    assert valid_nif("12345678Z")          # DNI: 12345678 % 23 = 14 -> Z
    assert not valid_nif("12345678A")
    assert valid_nif("X1234567L")          # NIE X -> 0: 01234567 % 23 = 19 -> L
    assert valid_nif("B12345674")          # CIF, digit control
    assert not valid_nif("B12345675")
    assert valid_nif("ESB12345674")
    assert valid_nif("Q1234567D")          # letter control group
    assert not valid_nif("Q12345674")


def good_invoice(**kw):
    base = dict(issuer_name="Proveedor SL", issuer_nif="B12345674", recipient_nif="12345678Z",
                invoice_number="F-2026-001", issue_date="2026-09-01", concept="servicios",
                vat_lines=[VatLine(base=100.0, vat_rate=21.0, vat_amount=21.0)],
                withholding_rate=15.0, withholding_amount=15.0, total=106.0,
                suggested_expense_account="623")
    base.update(kw)
    return Invoice(**base)


def test_valid_invoice_passes():
    errors, _ = check(good_invoice())
    assert errors == []


def test_arithmetic_errors_caught():
    assert any("VAT" in e for e in check(good_invoice(vat_lines=[VatLine(base=100, vat_rate=21, vat_amount=12)]))[0])
    assert any("total" in e for e in check(good_invoice(total=121.0))[0])
    assert any("not a Spanish rate" in e for e in check(good_invoice(
        vat_lines=[VatLine(base=100, vat_rate=16, vat_amount=16)], total=101.0))[0])
    assert any("check digit" in e for e in check(good_invoice(issuer_nif="B12345675"))[0])


class FakeMessages:
    """Returns a bad extraction from the cheap tier and a good one from the strong tier."""

    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []

    def parse(self, model, **kw):
        self.calls.append(model)
        inv = self.outputs[model]
        return SimpleNamespace(model=model, stop_reason="end_turn", parsed_output=inv,
                               usage=SimpleNamespace(input_tokens=2000, output_tokens=300))


def fake_client(outputs):
    m = FakeMessages(outputs)
    return SimpleNamespace(messages=m, beta=SimpleNamespace(messages=m)), m


def test_escalates_then_accepts(tmp_path):
    f = tmp_path / "inv.png"; f.write_bytes(b"\x89PNG fake")
    client, m = fake_client({"claude-haiku-4-5": good_invoice(total=999.0), "claude-opus-5": good_invoice()})
    r = extract.process(f, client)
    assert r.status == "accepted" and m.calls == ["claude-haiku-4-5", "claude-opus-5"]
    # cost counts BOTH attempts: haiku (2000*1 + 300*5)/1e6 + opus (2000*5 + 300*25)/1e6
    assert abs(r.cost_usd - (0.0035 + 0.0175)) < 1e-9


def test_cheap_tier_accepted_without_escalation(tmp_path):
    f = tmp_path / "inv.png"; f.write_bytes(b"x")
    client, m = fake_client({"claude-haiku-4-5": good_invoice(), "claude-opus-5": good_invoice()})
    assert extract.process(f, client).status == "accepted" and m.calls == ["claude-haiku-4-5"]


def test_human_review_when_all_tiers_fail(tmp_path):
    f = tmp_path / "inv.png"; f.write_bytes(b"x")
    bad = good_invoice(issuer_nif="B00000001")
    client, _ = fake_client({"claude-haiku-4-5": bad, "claude-opus-5": bad})
    r = extract.process(f, client)
    assert r.status == "human_review" and r.invoice is None
    s = extract.summarize([r])
    assert s["accepted"] == 0 and s["cost_per_accepted_invoice_usd"] is None


# ---- cycle 02 red-team fixes -------------------------------------------------

def test_suplidos_counted_in_total():
    inv = good_invoice(non_taxable_amount=30.0, total=136.0)
    assert check(inv)[0] == []
    assert any("total" in e for e in check(good_invoice(total=136.0))[0])


def test_reverse_charge_requires_zero_vat():
    inv = good_invoice(tax_regime="INVERSION_SUJETO_PASIVO", vat_lines=[VatLine(base=100, vat_rate=0, vat_amount=0)],
                       total=85.0)
    assert check(inv)[0] == []
    bad = good_invoice(tax_regime="INVERSION_SUJETO_PASIVO")
    assert any("non-zero VAT" in e for e in check(bad)[0])


def test_unsupported_regime_goes_to_human_without_escalation(tmp_path):
    f = tmp_path / "inv.png"; f.write_bytes(b"x")
    igic = good_invoice(tax_regime="IGIC", vat_lines=[VatLine(base=100, vat_rate=7, vat_amount=7)], total=92.0)
    client, m = fake_client({"claude-haiku-4-5": igic, "claude-opus-5": igic})
    r = extract.process(f, client)
    assert r.status == "human_review" and "IGIC" in r.review_reason and m.calls == ["claude-haiku-4-5"]


def test_unsupported_file_type_is_reviewed_not_crashed(tmp_path):
    f = tmp_path / "scan.tiff"; f.write_bytes(b"x")
    client, m = fake_client({})
    r = extract.process(f, client)
    assert r.status == "human_review" and m.calls == []


def test_duplicates_strong_and_weak():
    from invoice_pipeline.duplicates import find_duplicates
    inv = [{"id": "a", "issuer_nif": "ESB12345674", "invoice_number": "F-2026/001", "issue_date": "2026-09-01", "total": 106},
           {"id": "b", "issuer_nif": "B12345674", "invoice_number": "f2026 0001", "issue_date": "2026-09-01", "total": 106},
           {"id": "c", "issuer_nif": "B12345674", "invoice_number": "X-9", "issue_date": "2026-09-02", "total": 50},
           {"id": "d", "issuer_nif": "B12345674", "invoice_number": "X-10", "issue_date": "2026-09-02", "total": 50}]
    groups = {g["kind"]: set(g["ids"]) for g in find_duplicates(inv)}
    assert groups["strong"] == {"a", "b"} and groups["weak"] == {"c", "d"}


def test_evaluate_catches_consistent_misread_as_false_accept():
    from invoice_pipeline.evaluate import evaluate
    # decimal-separator misread: every amount /1000 -> arithmetic still consistent, so the validator accepts it
    misread = good_invoice(vat_lines=[VatLine(base=0.1, vat_rate=21.0, vat_amount=0.021)],
                           withholding_amount=0.015, total=0.106).model_dump()
    ok = good_invoice().model_dump()
    results = [{"file": "x/1.pdf", "status": "accepted", "invoice": ok, "cost_usd": 0.005, "latency_s": 3},
               {"file": "x/2.pdf", "status": "accepted", "invoice": misread, "cost_usd": 0.005, "latency_s": 4}]
    truth_row = dict(issuer_name="Proveedor SL", issuer_nif="B12345674", invoice_number="F-2026-001",
                     issue_date="2026-09-01", base_total="100", vat_total="21", total="106", vat_rates="21",
                     duplicate_of="", review_seconds="0")
    rep = evaluate(results, {"1.pdf": truth_row, "2.pdf": truth_row})
    assert rep["false_accepts"] == 1 and rep["accepted_automatically"] == 2
    assert rep["duplicates"]["detected"] == 1  # same NIF + number twice


def test_required_sample_size_is_large():
    from invoice_pipeline.evaluate import required_n
    # proving >=97% with 95% confidence when the true rate is 98.5% needs hundreds of observations
    assert 200 < required_n(0.985, 0.97) < 2000
