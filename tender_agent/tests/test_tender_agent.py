import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tender_agent import placsp, qa, agent, economics  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "sample_feed.atom"
SPEC = {
    "company_name": "Limpiezas Ejemplo, S.L.",
    "names_not_allowed": ["Otra Empresa SL"],
    "limits": {"max_pages": 3, "words_per_page": 450},
    "criteria": [
        {"id": "C1", "name": "Organización del servicio", "points": 20, "type": "juicio_valor", "must_include": ["cronograma", "sustituciones"]},
        {"id": "C2", "name": "Control de calidad", "points": 10, "type": "juicio_valor", "must_include": ["indicadores"]},
        {"id": "F1", "name": "Precio", "points": 60, "type": "formula", "keywords": ["precio"]},
        {"id": "F2", "name": "Bolsa de horas", "points": 10, "type": "formula", "keywords": ["bolsa de horas"]},
    ],
}
GOOD = """# Memoria técnica — Limpiezas Ejemplo, S.L.
## [C1] Organización del servicio
Cronograma semanal por centro y plan de sustituciones en 2 horas.
## [C2] Control de calidad
Indicadores mensuales de satisfacción e inspecciones.
"""


def test_parse_feed_fields():
    ts = placsp.parse_feed(FIX)
    t = {x.folder_id: x for x in ts}
    assert t["LIM-01/2026"].status == "PUB" and t["LIM-01/2026"].province == "Teruel"
    assert t["LIM-01/2026"].deadline == "2026-10-10" and t["LIM-01/2026"].budget_ex_vat == 240000
    assert t["LIM-01/2026"].technical_doc_uri.endswith("ppt1.pdf")
    assert t["LIM-07/2025"].awards[0].company == "Limpiezas Ejemplo, S.L." and t["LIM-07/2025"].awards[0].amount == 171000


def test_prospects_match_same_province_and_filter_big_groups(tmp_path):
    rows = placsp.main([str(FIX), "--today", "2026-09-24", "--out", str(tmp_path / "p.csv")])
    companies = {r["company"] for r in rows}
    assert companies == {"Limpiezas Ejemplo, S.L."}          # big group filtered, Huesca tender has no local winner
    r = rows[0]
    assert r["open_tender"] == "Servicio de limpieza de colegios públicos" and r["days_left"] == 16
    assert r["status"] == "NOT CONTACTED"


def test_open_tender_window():
    ts = placsp.latest_by_folder(placsp.parse_feed(FIX))
    assert placsp.open_tenders(ts, ["9091"], today=date(2026, 10, 5)) == []  # 5 days left < 7


def test_qa_passes_clean_memoria():
    r = qa.check(GOOD, SPEC)
    assert r.passed, qa.to_markdown(r)


@pytest.mark.parametrize("bad, check_name", [
    ("\nNuestro precio ofertado es competitivo.", "contamination_economic_term"),
    ("\nEl servicio costará 12.500 € anuales.", "contamination_currency"),
    ("\nOfrecemos una bolsa de horas de 200 horas.", "contamination_formula_value"),
    ("\nPlantilla: [[PENDIENTE: nº de limpiadoras]]", "placeholder"),
    ("\nComo hicimos para Otra Empresa SL.", "foreign_name"),
])
def test_qa_blocks_contamination_and_gaps(bad, check_name):
    r = qa.check(GOOD + bad, SPEC)
    assert not r.passed and any(f.check == check_name for f in r.findings)


def test_qa_missing_section_and_content():
    md = "# Memoria Limpiezas Ejemplo, S.L.\n## [C1] Organización\nCronograma.\n"
    r = qa.check(md, SPEC)
    checks = {(f.check, f.severity) for f in r.findings}
    assert ("coverage", "CRITICAL") in checks and ("required_content", "MAJOR") in checks


def test_qa_length_limit():
    r = qa.check(GOOD + ("palabra " * 1500), SPEC)
    assert any(f.check == "length" for f in r.findings)


def test_validate_spec_rejects_inconsistent_points():
    spec = agent.Spec(tender_title="t", buyer="b", deadline="", judgment_points_total=40, formula_points_total=60,
                      criteria=[agent.Criterion(id="C1", name="x", points=30, type="juicio_valor", source="p1"),
                                agent.Criterion(id="F1", name="precio", points=60, type="formula", source="p2")],
                      limits=agent.Limits(max_pages=20))
    with pytest.raises(ValueError):
        agent.validate_spec(spec)


def test_analyze_records_cost_with_fake_client(tmp_path):
    pdf = tmp_path / "pcap.pdf"; pdf.write_bytes(b"%PDF-1.4 fake")
    spec = agent.Spec(tender_title="t", buyer="b", deadline="", judgment_points_total=30, formula_points_total=70,
                      criteria=[agent.Criterion(id="C1", name="x", points=30, type="juicio_valor", source="p1"),
                                agent.Criterion(id="F1", name="precio", points=70, type="formula", source="p2")],
                      limits=agent.Limits(max_pages=20))
    fake = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=lambda **kw: SimpleNamespace(
        stop_reason="end_turn", parsed_output=spec, usage=SimpleNamespace(input_tokens=100_000, output_tokens=4_000)))))
    u = agent.Usage()
    out = agent.analyze([pdf], client=fake, usage=u)
    assert out.tender_title == "t" and u.usd == pytest.approx((100_000 * 5 + 4_000 * 25) / 1e6)


def test_economics():
    p = economics.plan(price=390, ai_eur=7, human_min=180)
    assert p["contribution_eur"] == 383 and p["revenue_per_human_hour_eur"] == 130.0
    roi = economics.customer_roi(contract_value_eur=500_000, margin_pct=8, judgment_points=40, inhouse_hours=16,
                                 staff_eur_h=20, price_eur=390)
    assert roi["inhouse_cost_eur"] == 320 and roi["breakeven_extra_win_probability"] == pytest.approx(390 / 40_000)
