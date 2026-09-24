"""Money dashboard: renders experiments/ledger.json into a static dashboard/index.html.

Every tile shows whether its number is ACTUAL, ESTIMATE or ASSUMPTION. Missing data renders
as "—" (not measured yet), never as zero.
Run: python dashboard/build_dashboard.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "experiments" / "ledger.json"
OUT = ROOT / "dashboard" / "index.html"

MONEY_TILES = [
    ("revenue_eur", "Revenue", "€"), ("mrr_eur", "MRR", "€"), ("customers", "Customers", ""),
    ("paid_pilots", "Paid pilots", ""), ("prospects_contacted", "Prospects contacted", ""),
    ("variable_costs_eur", "Variable costs", "€"), ("ai_costs_eur", "AI costs", "€"),
    ("gross_margin_pct", "Gross margin", "%"), ("cac_eur", "CAC", "€"), ("payback_months", "Payback", "mo"),
    ("churn_pct", "Churn", "%"), ("ai_cost_per_accepted_invoice_eur", "AI cost / accepted invoice", "€"),
]
STATUS_ICON = {"KILLED": "✕", "QUEUED": "…", "RUNNING": "▶", "PASSED": "✓"}


def fmt(v, unit):
    if v is None:
        return "—"
    if unit == "€":
        return f"€{v:,.4f}".rstrip("0").rstrip(".") if isinstance(v, float) and v < 1 else f"€{v:,.0f}"
    if unit == "%":
        return f"{v:.0f}%"
    if unit == "mo":
        return f"{v:.1f} mo"
    return f"{v:,}"


def tile(label, value, kind, note=""):
    t = f' title="{html.escape(note)}"' if note else ""
    return (f'<div class="tile"{t}><div class="label">{html.escape(label)}</div>'
            f'<div class="value">{value}</div><div class="kind kind-{kind.lower()}">{kind}</div></div>')


def build():
    L = json.loads(LEDGER.read_text())
    m, p, q = L["money"], L["pipeline"], L["quant"]
    tiles = "".join(tile(lbl, fmt(m[k]["value"], u), m[k]["kind"], m[k].get("note", "")) for k, lbl, u in MONEY_TILES if k in m)
    ptiles = "".join(tile(lbl, fmt(v, ""), "ACTUAL") for lbl, v in [
        ("Opportunities generated", p["opportunities_generated"]), ("Surviving", p["opportunities_surviving"]),
        ("Validated (paid signal)", p["validated_opportunities"]), ("Active MVPs", p["active_mvps"])])
    qtiles = "".join(tile(lbl, v, "ACTUAL") for lbl, v in [
        ("Strategies tested", fmt(q["strategies_tested"], "")),
        ("With validated edge", fmt(q["strategies_with_validated_edge"], "")),
        ("Live capital", fmt(q["live_capital_eur"], "€")),
        ("Paper drawdown", "—" if q["paper_trading_drawdown_R"] is None else f'{q["paper_trading_drawdown_R"]}R')])
    rows = []
    for e in L["experiments"]:
        st = e["status"]
        icon = next((v for k, v in STATUS_ICON.items() if st.startswith(k)), "•")
        rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in [
            html.escape(e["id"]), f'<span class="status">{icon} {html.escape(st)}</span>',
            html.escape(e["hypothesis"]), html.escape(str(e.get("result") or "—")),
            html.escape(str(e.get("failure_reason") or e.get("kill") or "—")),
            html.escape(e["next_action"])]) + "</tr>")
    page = TEMPLATE.format(updated=html.escape(L["updated"]), hero=fmt(m["revenue_eur"]["value"], "€"),
                           tiles=tiles, ptiles=ptiles, qtiles=qtiles, rows="\n".join(rows))
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(ROOT)}")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Money Dashboard</title>
<style>
:root {{ color-scheme: light; --bg:#fcfcfb; --card:#ffffff; --line:#e4e3de; --text:#0b0b0b; --text2:#52514e; --muted:#7a7974;
  --actual:#2a78d6; --estimate:#8a5a00; --assumption:#6b5fb8; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ color-scheme: dark; --bg:#1a1a19; --card:#232322;
  --line:#3a3a38; --text:#ffffff; --text2:#c3c2b7; --muted:#9a998f; --actual:#6ea8ef; --estimate:#e0b04a; --assumption:#b0a8f0; }} }}
:root[data-theme="dark"] {{ color-scheme: dark; --bg:#1a1a19; --card:#232322; --line:#3a3a38; --text:#ffffff; --text2:#c3c2b7;
  --muted:#9a998f; --actual:#6ea8ef; --estimate:#e0b04a; --assumption:#b0a8f0; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:24px 16px 48px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} h2 {{ font-size:16px; margin:32px 0 12px; color:var(--text2); font-weight:600; }}
.sub {{ color:var(--muted); font-size:13px; }}
.hero {{ margin:20px 0 8px; }} .hero .value {{ font-size:52px; font-weight:600; line-height:1; }}
.hero .label {{ color:var(--text2); }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:12px; }}
.tile {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }}
.tile .label {{ color:var(--text2); font-size:13px; }} .tile .value {{ font-size:24px; font-weight:600; margin:4px 0; }}
.kind {{ font-size:11px; letter-spacing:.04em; font-weight:600; }}
.kind-actual {{ color:var(--actual); }} .kind-estimate {{ color:var(--estimate); }} .kind-assumption {{ color:var(--assumption); }}
.kind-estimate::before {{ content:"~ "; }} .kind-assumption::before {{ content:"? "; }}
.tablewrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:10px; background:var(--card); }}
table {{ border-collapse:collapse; width:100%; font-size:13px; min-width:760px; }}
th,td {{ text-align:left; padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--text2); font-weight:600; }} tr:last-child td {{ border-bottom:0; }}
.status {{ white-space:nowrap; font-weight:600; }}
.legend {{ font-size:12px; color:var(--text2); margin-top:8px; }}
</style></head><body><main>
<h1>Money dashboard</h1>
<div class="sub">Updated {updated} · generated from experiments/ledger.json · “—” = not measured yet</div>
<div class="hero"><div class="label">Real revenue to date</div><div class="value">{hero}</div></div>
<div class="legend"><b>ACTUAL</b> = measured · <b>~ ESTIMATE</b> = arithmetic on facts · <b>? ASSUMPTION</b> = to be replaced by data</div>
<h2>Money</h2><div class="grid">{tiles}</div>
<h2>Pipeline</h2><div class="grid">{ptiles}</div>
<h2>Quant</h2><div class="grid">{qtiles}</div>
<h2>Experiments</h2>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Status</th><th>Hypothesis</th><th>Result</th><th>Failure / kill rule</th><th>Next action</th></tr></thead>
<tbody>
{rows}
</tbody></table></div>
</main></body></html>
"""

if __name__ == "__main__":
    build()
