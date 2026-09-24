# Money Engine — Cycle 01 report (2026-09-24)

## 0. Executive summary

| question | answer |
|---|---|
| Real revenue created this cycle | **€0**. No customer has been contacted: every outward action needs your approval. |
| Strong signals obtained (§38 A-E) | **None yet.** D ("robust quant edge") was tested and **failed**. A-C need outreach you must approve. |
| XAUUSD hypothesis | **Rejected.** 68.8% win rate against 69.5% random-walk breakeven; −0.020R per trade after spread (t = −0.72), 2020-2026, 599 trades. It fails in the independent 2006-2019 era too. |
| Opportunities generated / survived | 102 generated → **14 survive** (78 killed, 8 merged, 2 parked). Full list: [`research/opportunity_longlist.csv`](../research/opportunity_longlist.csv) |
| Recommended first experiment | **EXP-002: paid pilot of invoice-to-ledger automation for Spanish gestorías** (S1). Test price: **€0.20 per posted invoice** plus a setup fee. |
| Built this cycle | XAUUSD backtester and study (9 tests), gestoría invoice pipeline with model routing and cost-per-accepted-invoice tracking, contracted-power audit tool, scenario economics, money dashboard, experiment ledger, Spanish landing page and outreach drafts. 22 automated tests pass. |
| Needs your approval | (1) sending any outreach, (2) publishing the landing page, (3) an Anthropic API key and a small budget (~€20) for the pilot run on real invoices, (4) confirming what "708 points" means on your broker (see §7). |

How to read this document:
- **FACT** = seen in a cited source (§11). Most facts came from web-search summaries of vendor and regulator pages; primary pages on boe.es and several vendor sites were **blocked** from this environment and could not be opened.
- **EST** = arithmetic on facts.
- **ASM** = assumption to be replaced by experiment data.
- **UNVERIFIED** = plausible, no evidence found.

No customer, revenue, backtest or statistic in this report is invented. Where a number is a judgment, it says so.

---

## 1. What was done

1. **Research.** Current web evidence (September 2026) on pricing, competitors, regulation and demand across finance, B2B services, compliance, energy, ecommerce, trading tools and developer tools.
2. **Discovery.** Generated 102 opportunities and filtered on money already spent, evidence of willingness to pay, competition, distribution access from Spain, and regulatory risk.
3. **Quant.** Pulled 31 years of XAU/USD daily and 6.7 years of hourly data (Twelve Data), rebuilt MT5-style daily bars, and ran a falsification battery against the XAUUSD hypothesis.
4. **Economics.** Scenario models in [`research/economics.md`](../research/economics.md) and judgment scores in [`research/scoring.md`](../research/scoring.md).
5. **Build.** Only what the first experiments need (§8).

What was **not** done: no customer conversations, no outreach, no payments, and no live or paper trading.

---

## 2. Surviving opportunities (14)

Ranked by the decision-support score (geometric mean of 8 positives − 0.15 × sum of 6 penalties). All
inputs are 1-5 **judgments**, visible in [`research/scoring.md`](../research/scoring.md).
**Evidence strength** is listed separately: a high score with weak evidence means "test cheaply", not "build".

| # | opportunity | score | evidence strength | fast cash? | compounds? |
|---|---|---|---|---|---|
| S1 | Gestoría invoice-to-ledger automation | 1.88 | medium: market size + implementation prices FACT, WTP of *this* offer UNVERIFIED | yes | yes |
| S9 | Tender price-to-win analytics | 1.62 | **weak**: demand UNVERIFIED | no | yes |
| S4 | AI-assisted memoria técnica studio | 1.61 | medium: service prices FACT | **yes** | partly |
| S13 | Gestoría payroll-incident automation | 1.36 | weak | yes | yes |
| S14 | Procurement recovery audit (duplicate/overpayments) | 1.33 | weak for Spain | yes | no |
| S6 | Trading-strategy falsification reports | 1.31 | medium: low prices FACT | yes (small) | no |
| S11 | Property-manager back office | 1.31 | weak | yes | yes |
| S5 | Grant (subvención) application service | 1.07 | medium: fee % FACT | slow | no |
| S12 | Insurance-broker claims intake | 1.07 | weak | yes | yes |
| S7 | CBAM declarant-as-a-service | 1.04 | strong regulatory FACT, weak demand evidence for newcomers | no | yes |
| S2 | Contracted-power audit (success fee) | 1.02 | medium: model FACT; **ticket small (EST ~€150)** | yes (small) | yes (load-curve data) |
| S8 | EUDR due-diligence service | 0.66 | strong regulatory FACT; deadline has slipped twice | no | partly |
| S10 | Chargeback handling for Redsys merchants | 0.66 | weak | no | no |
| S3 | Verifactu 2027 migration service | 0.56 | strong deadline FACT; commodity | yes (time-boxed) | no |

### Opportunity cards

Every card answers the 19 questions. Where a field is identical to S1 it says so.

#### S1 — Gestoría supplier-invoice → accounting-entry automation
1. **Problem.** Spanish gestorías key supplier invoices into a3/Sage/Contasol by hand: data entry, VAT breakdown, account assignment, then chasing errors.
2. **Customer.** The gestoría (payer). The 77% with fewer than 10 employees are the target: owner-led and fast to decide.
3. **Existing solution.** Manual entry; OCR modules inside accounting suites; freelance or agency automation projects.
4. **Evidence of demand.** FACT: ~60,000 asesorías in Spain, 77% with <10 employees [S1]. FACT (secondary citation): 23% use any AI in accounting processes [S2]. FACT: automation implementations are sold at €800-2,000, and €3,000-5,000 with reconciliation [S3, vendor blogs, weak]. **UNVERIFIED:** willingness to pay *us*.
5. **Competition.** Accounting-suite OCR (Sage, a3), niche AI vendors and agencies (copilotgestoria, vertebragestion, xpertix…), plus generic OCR such as Dext. Crowded but fragmented.
6. **Existing pricing.** Implementations €800-5,000 [S3]. Per-invoice SaaS pricing in Spain UNVERIFIED.
7. **Proposed solution.** Invoice PDF → structured extraction → **deterministic validation** (NIF/CIF check digits, VAT arithmetic, totals) → CSV import file for the gestoría's software. Model routing: Haiku first, Opus on validation failure, human review last. Nothing is posted without passing every check.
8. **MVP.** Built: `invoice_pipeline/`. Still missing: the import-file mapping for the pilot's specific software. **UNVERIFIED formats; get them from the pilot customer.**
9. **Estimated build cost.** Done so far: ~1 day. Remaining: 1-2 days per software mapping (ASM).
10. **Estimated AI operating cost.** EST **$0.0135 (≈€0.012) per accepted invoice**. Human review, not AI, is the main variable cost (ASM ~€0.04/invoice) [economics.md].
11. **Acquisition strategy.** Direct calls and visits to small gestorías in one province, local professional associations, and LinkedIn to owners. Cold commercial email carries LSSI consent risk; see §10.
12. **Potential margin.** At €150/month flat: 18% contribution. **At €0.20/invoice (€300/month for 1,500 invoices): 59%** (all ASM) [economics.md].
13. **Defensibility.** Workflow moat (embedded in month-end close); an evaluation moat (labelled invoice set + validation rules); switching cost. A prompt is not a moat; the validated-invoice dataset is.
14. **Regulatory risk.** Low-medium: GDPR processor agreement (DPA) with each gestoría, and EU data residency may be asked for.
15. **Time to first sale.** ASM: weeks, not days. Driven by trust, not by the build.
16. **Confidence.** Medium on market; low on this offer's WTP.
17. **Biggest unknown.** Will a gestoría pay per invoice when its software vendor sells a "good enough" OCR add-on?
18. **Kill condition.** <2 paid pilots from 25 qualified conversations, **or** field-level accuracy <97% on real invoices after two fixes, **or** human-review rate >10%.
19. **First validation experiment.** EXP-002 (§8).

#### S4 — AI-assisted memoria técnica studio (public tenders)
1. **Problem.** SMEs bidding on public tenders must write a technical proposal (memoria técnica) against a long specification, under deadline. It is often the scoring criterion that decides the award.
2. **Customer.** Construction, cleaning, maintenance, IT and services SMEs that bid regularly.
3. **Existing solution.** In-house staff, freelance writers, tender consultancies; AI drafting tools are emerging.
4. **Evidence.** FACT: services priced from €350 per memoria to >€5,000 for heavy documentation, often with a success component [S10]. AI-first competitors exist (Noetia, LicitaIA) [S10], so the category is live.
5. **Competition.** Consultancies (Concurra, Licitek…) and AI tools.
6. **Existing pricing.** €350-5,000+ per memoria [S10].
7. **Solution.** Specification (pliego) → requirement and scoring-criteria extraction → compliance matrix → drafted sections → human editor → customer. The AI does the long-document reasoning; a human owns the claims.
8. **MVP.** Not built. The pipeline is about 1-2 days (ASM); the first jobs can be done "concierge" style with Claude directly.
9. **Build cost.** ~1-2 days (ASM).
10. **AI operating cost.** EST ~€8 per memoria (≈200k input and 40k output tokens on claude-opus-5).
11. **Acquisition.** Firms that won similar lots (public award data), business associations, and inbound ("memoria técnica 48h").
12. **Margin.** EST €302 contribution per €700 job after 6 h editing and €150 CAC (ASM) [economics.md].
13. **Defensibility.** Low at first. Grows with a library of won and lost proposals and evaluator scores (data moat) and with S9 analytics.
14. **Regulatory.** Low. The customer signs the bid; commitments must be the customer's own.
15. **Time to first sale.** ASM: plausibly the fastest of all, because a live deadline creates urgency.
16. **Confidence.** Medium.
17. **Biggest unknown.** Will bidders trust a newcomer with a scored document? Win-rate attribution is noisy.
18. **Kill condition.** 0 paid jobs from 30 targeted conversations with active bidders, or editing time >12 h per job.
19. **First validation.** EXP-003: offer 3 discounted memorias (€350) to firms bidding on currently open tenders. Success = ≥1 paid job and a customer rating ≥4/5.

#### S2 — Contracted-power audit for 3.0TD supplies (success fee)
1. **Problem.** Businesses pay a fixed power term on contracted kW whether or not they use it. Over-contracted power and reactive-energy penalties are recurring waste.
2. **Customer.** SMEs on 3.0TD (>15 kW): restaurants, hotels, workshops, gyms, small industry.
3. **Existing solution.** Energy consultants and brokers, often "free" because retailers pay them commissions [S7].
4. **Evidence.** FACT: consultancies sell power optimisation, some on success fees [S7]. FACT: Datadis gives authorised third parties hourly consumption and max-power data [S6, S8].
5. **Competition.** Brokers and consultancies, many conflicted.
6. **Existing pricing.** "Free" (broker) or % of savings (UNVERIFIED typical %).
7. **Solution.** Built: deterministic **no-excess** optimiser. It uses the customer's own invoice prices, never recommends below an observed peak, and enforces the P1≤…≤P6 ordering.
8. **MVP.** Built: `energy_audit/` with tests.
9. **Build cost.** Done.
10. **AI cost.** €0: this problem is deterministic.
11. **Acquisition.** Gestorías as referral partners (same buyer network as S1).
12. **Margin.** EST €40 contribution per job at a 25% fee on an ASM €600 median saving. **Small.**
13. **Defensibility.** A dataset of load curves by business type for benchmarking; otherwise low.
14. **Regulatory.** Low. Customer consent is required for data access.
15. **Time to first sale.** Fee arrives after the power change and the next invoices.
16. **Confidence.** Medium on mechanism, **low on ticket size**.
17. **Biggest unknown.** The real distribution of over-contracting (vendor claims like "90% of contracts can be optimised" are marketing, not evidence).
18. **Kill condition.** Median saving <€600 per year across the first 10 real invoices.
19. **First validation.** EXP-004: collect 10 real invoice sets (via gestoría partners or your network), run the tool, and look at the saving distribution. Costs ~2 hours.

#### S9 — Tender price-to-win analytics
1. **Problem.** Bidders price blind; awarded prices and discount levels by buyer and CPV code are public but scattered.
2. **Customer.** Frequent bidders and their consultancies.
3. **Existing solution.** Alert platforms (show tenders), gut feel.
4. **Evidence.** Alert market is crowded [S11]. Demand for *pricing* analytics: **UNVERIFIED**.
5. **Competition.** Alert platforms may add it.
6. **Existing pricing.** Unknown.
7. **Solution.** Parse awarded contracts (PLACSP open data) → winning discount distributions per buyer, CPV and region → bid-price recommendation.
8. **MVP.** Data pipeline plus one report for one sector (e.g. cleaning in one region).
9. **Build cost.** ~3-5 days (ASM).
10. **AI cost.** Low: mostly deterministic parsing, with an LLM for messy award documents.
11. **Acquisition.** Bundle with S4 customers.
12. **Margin.** High once built (data product).
13. **Defensibility.** **Data moat** (cleaned history plus outcomes).
14. **Regulatory.** Low (public data).
15. **Time to first sale.** Slow.
16. **Confidence.** Low.
17. **Biggest unknown.** Whether bidders pay for pricing insight separately from bid writing.
18. **Kill condition.** 0 of 10 S4 customers willing to pay ≥€50/month for it.
19. **First validation.** Ask S4 customers for a paid one-off price benchmark (€99).

#### S13 — Gestoría payroll-incident automation
1-3: Monthly payroll inputs (absences, overtime, new hires) arrive by email and WhatsApp and are keyed into payroll software by hand. Customer: the labour department of the gestoría. Existing solution: manual work, A3nom/Sage payroll modules.
4-6: Same market facts as S1 [S1, S2]. Specific pricing UNVERIFIED.
7-10: Extraction plus validation into a payroll-incident import. Error cost is high (salaries), so human-in-the-loop is mandatory. MVP after S1 (it reuses the pipeline). AI cost similar to S1.
11-14: Same channel as S1. Upsell. Workflow moat. Employee personal data: DPA and GDPR.
15-19: After S1. Confidence low. Unknown: import formats. Kill: no S1 customer wants it. Validation: ask during S1 pilots.

#### S14 — Procurement recovery audit (duplicate payments, missed discounts, overbilling)
1-3: Mid-size companies overpay suppliers (duplicates, price-list drift). Customer: CFO. Existing solution: internal audit; international recovery-audit firms work on contingency (UNVERIFIED Spanish presence).
4-6: Spanish demand UNVERIFIED. Contingency pricing typical of the industry, % UNVERIFIED.
7-10: Extract the AP ledger and invoices → deterministic duplicate and variance detection → LLM for contract-term matching. MVP: scripts over an ERP export. Low AI cost.
11-14: Requires trust with ERP data, so CAC is high. Low regulatory risk. Knowledge moat.
15-19: Slow to first sale. Confidence low. Unknown: recoverable % in Spanish SMEs. Kill: <€5k found in the first 2 audits. Validation: one free audit for a friendly company.

#### S6 — Trading-strategy falsification reports
1-3: Retail and prop traders fool themselves with high-win-rate rules (like the XAUUSD one). Customer: the trader. Existing solution: MQL5/Upwork freelancers, self-testing.
4-6: FACT: MQL5 backtest jobs budget $30-125; Upwork up to ~$1,200 [S14]. Low WTP.
7-10: Built. The EXP-001 engine is a template for stop/limit rules. AI cost ~0.
11-14: Your own trader communities: **your distribution edge**. No moat. Regulatory: must not become advice or signals.
15-19: Fast but small. Confidence medium on demand, low on ticket. Unknown: will traders pay for *bad news*? Kill: <3 paid reports at ≥€49 from 50 community contacts. Validation: post the XAUUSD case study (with your permission) and offer 5 reports.

#### S11 — Property-manager back office · S12 — Insurance-broker claims intake
Both reuse the S1 extraction and validation core in other document-heavy verticals. Answers:
- **Fields 1-3.** The problem is manual document processing in each vertical. The customer is the property-management firm or the insurance broker. Today it is done by hand or in legacy software.
- **Fields 4-6 (evidence, competition, pricing).** Demand is UNVERIFIED and pricing unknown. Vertical software vendors exist.
- **Fields 7-10 (solution, MVP, cost).** Same as S1, plus per-vertical schemas.
- **Fields 11-14.** Sold through direct sales, with higher CAC than S1 because there is no partner channel. Workflow moat. Personal-data GDPR.
- **Fields 15-19.** Build only after S1 proves the core. Confidence is low. Kill if S1 is killed on accuracy. Validate with 5 discovery calls each once S1 has a case study.

#### S5 — Grant (subvención) application service
1-3: SMEs miss grants or fail the paperwork. Customer: the SME. Existing solution: consultancies (Fandit…).
4-6: FACT: success fees of 10-25% on small and medium grants, 3-15% on large ones, often plus a fixed part [S12].
7-10: Grant matching over BDNS plus AI-drafted application. Human submission.
11-14: Via gestorías (S1 channel). Low moat. Regulatory: accuracy of declarations.
15-19: **Cash arrives months after concession.** Confidence medium. Unknown: approval rates. Kill: no signed success-fee mandate in 20 conversations. Validation: via S1 gestoría partners.

#### S7 — CBAM declarant-as-a-service
1-3: Importers of CBAM goods (steel, aluminium, cement, fertilisers…) above 50 t per year must be authorised declarants and file annual declarations with embedded-emission data [S20]. Customer: importers. Existing solution: customs brokers, Big-4, CBAM SaaS.
4-6: FACT: definitive regime since 1 January 2026, and declarations can be delegated to an EU-established third party with an EORI number [S20]. First certificate surrender is 30 September 2027 [S20]. Pricing UNVERIFIED.
7-10: Supplier emissions-data collection and validation, plus declaration preparation. Moderate AI (supplier documents in many languages).
11-14: Via customs brokers. Knowledge moat. **Regulatory liability is real**, so partner with a customs broker.
15-19: Slow (year-end declaration cycle). Confidence low for a newcomer. Unknown: how many Spanish importers remain above 50 t after the Omnibus. Kill: no customs-broker partner in 10 conversations. Validation: 10 calls to Spanish customs brokers.

#### S8 — EUDR due-diligence service
1-3: Operators placing coffee, cocoa, soy, palm oil, cattle, wood or rubber on the EU market need due-diligence statements. Customer: importers, e.g. coffee roasters and furniture importers.
4-6: FACT: applies 30 December 2026 (large/medium) and 30 June 2027 (micro/small), with simplified downstream duties [S21]. It has already slipped twice. Pricing UNVERIFIED.
7-10: Geolocation and supplier-document collection and validation.
11-14: Via trade associations. Regulatory risk of **further delay**.
15-19: Confidence low. Kill: any further postponement announced. Validation: 10 calls to Spanish coffee and wood importers before December 2026.

#### S10 — Chargeback handling for Redsys merchants
1-19 compressed: a plausible gap (Spanish bank POS disputes handled manually through bank portals), but demand, access and pricing are all **UNVERIFIED**. The platform dependency on the banks is high. Kill: no bank gives an API or file export. Validation: 5 merchant interviews.

#### S3 — Verifactu 2027 migration service
1-3: Every Spanish company must invoice with Verifactu-compliant software from 1 January 2027 (autónomos 1 July 2027) [S5]. Anyone on Excel, Word or old tools must migrate. Customer: SMEs, via gestorías.
4-6: Deadline FACT [S5]. Compliant software is everywhere; the service gap is migration and hand-holding, with pricing UNVERIFIED.
7-10: Inventory of the gestoría's clients' invoicing tools → migration playbook → bulk onboarding. Low AI.
11-14: Via gestorías (S1 channel). **No moat, time-boxed.**
15-19: A good *door-opener* for S1 conversations, not a business. Kill: after July 2027 by design.

---

## 3. Economic models (scenarios, not forecasts)

Numeric models for S1, S1b, S2 and S4 are in [`research/economics.md`](../research/economics.md), generated by `research/economics.py`.

| | S1 (€150/mo flat) | S1b (€0.20/invoice) | S2 (25% of saving) | S4 (€700/job) |
|---|---|---|---|---|
| Variable cost per unit | €124/mo | €124/mo | €60/job | €248/job |
| of which AI | €18.6/mo (EST) | €18.6/mo | €0 | €8/job (EST) |
| Contribution | €26/mo (18%) | €176/mo (59%) | €40/job | €302/job |
| CAC (ASM) | €600 | €600 | €20 via partner | €150 |
| Payback | setup fee covers CAC | setup fee covers CAC | n/a | n/a |
| 10 customers or jobs per year | €2.6k contribution | €20.6k | −€0.2k | €1.8k |
| 100 | €37k | €217k | €3.4k | €29k |
| 1,000 | €382k | (not credible for a solo operator) | €39k | €301k |

Readings:
- **S1:** human review, not the model, is the margin driver. The cheapest lever is reducing review rate through better validation rules, not a cheaper model.
- **S2:** too small to be a business alone. At best it's an add-on through the S1 channel.
- **S4:** has the best unit economics per job, but no recurring revenue.

**Cost per completed customer job** (the metric that matters):

| opportunity | unit of value | AI cost | all-in variable cost (ASM) |
|---|---|---|---|
| S1 | accepted, posted invoice | ~€0.012 | ~€0.08 incl. review, support, infra |
| S4 | delivered memoria | ~€8 | ~€248 incl. 6 h editing |
| S2 | audited supply | €0 | ~€60 incl. 1.5 h |
| S6 | falsification report | ~€0 | ~2-4 h analyst time |

---

## 4. Fast-cash report

A first payment could plausibly be pursued soon for these. No timeline is promised.

| | S4 memoria studio | S1 gestoría pilot | S6 falsification report | S2 power audit |
|---|---|---|---|---|
| Exact customer | SME that bids on public tenders ≥3×/year (cleaning, maintenance, IT services), 5-50 staff | Gestoría with 2-10 staff, 30-150 business clients, on a3/Sage/Contasol | Retail or prop trader with a rule-based strategy and trade history | SME on 3.0TD with ≥12 invoices |
| Exact problem | Needs a scored memoria técnica before a live deadline | Staff hours keying supplier invoices | Doesn't know if the strategy has an edge | Paying for unused kW |
| Exact offer | "Memoria técnica lista en 72 h, redactada con IA y revisada por una persona" | "Contabilizamos sus facturas de proveedor: usted solo revisa excepciones" | "Intentamos destruir su estrategia con datos. Si sobrevive, sabrá por qué" | "Auditoría gratuita de potencia; solo cobramos si ahorra" |
| Price hypothesis | €350 first 3 jobs (intro), then €700 | Pilot €300 (1 client batch, 1 month) → €0.20/invoice + €1,200 setup | €49-149 per report | 25% of first-year saving |
| Channel | Award data → phone/LinkedIn; associations | Phone/visits in one province; colegios and associations; LinkedIn | Your trading communities | Via gestoría partners |
| First outreach | 30 firms that won similar lots in the last 12 months (public data) | 25 gestorías; show the S1 pipeline on 20 of *their* sample invoices | Case study post (XAUUSD) + 5 report offers | Ask 5 gestorías for 10 clients' invoices |
| MVP required | Concierge (Claude + editor) | Built (`invoice_pipeline/`) + import mapping | Built (`quant/`) | Built (`energy_audit/`) |
| Delivery workflow | pliego → requirement matrix → draft → human edit → customer review → deliver | batch upload → extraction → validation → exceptions to human → import file → gestoría imports | intake rule + data → engine → report → 30-min call | invoices → tool → human check → report → customer requests change → fee on next invoices |
| Validation criteria | ≥1 paid job from 30 conversations; ≤12 h editing; rating ≥4/5 | ≥2 paid pilots from 25 conversations; ≥97% field accuracy; review ≤10% | ≥3 paid from 50 contacts | median saving ≥€600 per year on first 10 |

---

## 5. Compounding report

| asset | why it could compound |
|---|---|
| **Validated Spanish invoice dataset + validation rules (S1)** | Every processed invoice improves extraction evals and lowers the human-review rate, which is the main cost. The labelled set becomes an **evaluation moat**. It extends to S11, S12 and S13 with the same core: one engine, several verticals. |
| **Gestoría channel (S1 → S2, S3, S5, S13)** | 60k firms each serve dozens of SMEs. One trusted gestoría relationship is a distribution channel for every SME product. This is the real **distribution moat** candidate. |
| **Tender outcome library + price-to-win data (S4 → S9)** | Every memoria and award outcome feeds a proprietary win/loss dataset. Price analytics on public awards is data others don't clean. |
| **Load-curve library (S2)** | Benchmarks by business type ("restaurants your size contract 30% less"). Small value alone; a lead generator for S1. |
| **Quant validation engine (EXP-001)** | Reusable falsification harness: stop/limit geometry, intrabar bounds, controls, FDR, out-of-era tests. It protects your capital from bad strategies and underpins S6. |

---

## 6. Quant report

Full report: [`quant/REPORT_XAUUSD.md`](../quant/REPORT_XAUUSD.md). Generated tables: [`quant/results/xau_study.md`](../quant/results/xau_study.md).

| item | result |
|---|---|
| Promising hypotheses | None that justify capital. One *relative* effect replicated: SELL STOP after large-bodied bullish candles (≥0.53 ATR) does much worse than after small ones. Absolute edge not shown. |
| Datasets | Twelve Data XAU/USD H1 2020-2026 (39,614 bars) and D1 2006-2019. D1 before 2006 discarded (fixing prices). |
| Data quality | H1 timestamps are Australia/Sydney time (established from the maintenance-gap pattern). Weekend stubs in 2024+ D1. Composite spot feed, not your broker. |
| Methodology | Event simulator with gap fills, half-spread triggers, three intrabar resolutions (WORST/PATH/BEST). Controls: every day, bearish days, mirror BUY STOP, permutation vs random days. 44 conditional slices with IS-only cut points and BH-FDR. IS→OOS selection test. ATR-scaled geometry grid. Independent 2006-2019 era. Bootstrap Monte Carlo. |
| Backtest (literal, $0.30 spread, PATH) | 599 trades, WR 68.8%, **−0.020R/trade**, 95% CI [−0.076, +0.034], PF 0.94, max DD 22R |
| Out-of-sample | IS 2020-22 −0.006R; OOS 2023-26 −0.029R; 2006-19 bounds −0.182R to −0.013R |
| Robustness | No ATR geometry gives a significant positive expectancy. The ×10 points reading has only 53 fills (inconclusive). |
| Failure modes | Fixed-$ geometry vs 4× volatility expansion; strong bull trend against shorts; spread sensitivity (−0.06R at $1 spread) |
| Transaction costs | Modelled; decisive at the margin |
| Statistical confidence | Literal rule: consistent with zero edge, most likely slightly negative. Multiple testing is ~70 hypotheses; one FDR survivor. |
| Further research? | **No capital.** An optional pre-registered paper test of the "skip large bodies" filter costs nothing, but its best-case value is ~1.4% a year at 0.5% risk. |

---

## 7. Open question for you (quant)

"708 points" on XAUUSD depends on the broker's digits:
- On 2-digit MT5 (e.g. FTMO), 708 points = **$7.08**. That's what I tested as primary.
- If your platform uses 3-digit gold, or you meant "pips" of $0.10, the geometry is very different.

The ×10 reading is in T6 (inconclusive). Tell me your broker's XAUUSD digits and I'll re-run in 5 seconds (`python -m xau.study` after changing `POINT`).

---

## 8. First experiment

### Selection by expected learning ÷ cost

| candidate | what we'd learn | remaining cost | time to signal | decision |
|---|---|---|---|---|
| **EXP-002 S1 gestoría paid pilot** | WTP for per-invoice automation in a 60k-firm market; real accuracy and review rate | low: pipeline built; ~10-15 h outreach, ~€20 API | weeks | **SELECTED** |
| EXP-003 S4 memoria concierge | fastest one-off cash; trust in AI drafting | medium: 6-12 h per job before any sale | 1-3 weeks | next |
| EXP-004 S2 savings sizing | real distribution of over-contracting | ~2 h once 10 invoice sets arrive | days | run in parallel via S1 conversations |
| S6 falsification offer | trader WTP | ~2 h | days | only with your permission to publish the case study |

S1 is the largest and most repeatable prize with the stronger price evidence. Most of its build cost is
already paid. The same conversations can collect S2 invoice data and test S3 as a door-opener.

### EXP-002 specification (ledger: [`experiments/EXP-002-gestoria-pilot.md`](../experiments/EXP-002-gestoria-pilot.md))

- **Hypothesis.** A small Spanish gestoría will pay a €300 pilot fee, then €0.20 per accepted invoice, for supplier-invoice extraction into its accounting software, if field accuracy is ≥97% and it only reviews exceptions.
- **Built.**
  - `invoice_pipeline/`: Haiku → Opus → human routing; deterministic NIF/VAT/total validation; cost per accepted invoice; JSONL ledger.
  - `landing/gestorias.html`: a Spanish landing page, **not published**.
  - `outreach/gestorias.md`: call script and follow-up drafts, **not sent**.
- **Steps (each outward step needs your OK).**
  1. You approve the list and script.
  2. 25 conversations.
  3. For interested firms, run their 20-50 anonymised sample invoices through the pipeline and report accuracy, review rate and cost.
  4. Ask for the €300 pilot.
- **Measure.** Conversations → demos → sample runs → paid pilots; field-level accuracy; review rate; cost per accepted invoice; hours saved (customer-reported).
- **Pass.** ≥2 paid pilots and ≥97% accuracy and ≤10% review.
- **Kill.** <2 paid pilots after 25 qualified conversations, or accuracy <97% after two iteration rounds.
- **Budget.** ≤€20 API spend, ≤15 h of your time.

---

## 9. Kill log highlights (evidence-based kills)

| killed | why |
|---|---|
| NRUA holiday-rental registration service | Supreme Court annulled NRUA on 19 May 2026 [S19] |
| AI receptionist for Spanish clinics | €29-55/month commodity with many vendors [S22] |
| Prop-firm drawdown guard EA | free open-source versions published this month [S13] |
| BORME new-company leads | free and near-free sources [S23] |
| Marketplace payout reconciliation (Spain) | Accountali, Netto, Datali, Holded [S17] |
| Bank-statement converter | DocuClipper from ~$20-29/month and clones [S4] |
| Tender alert SaaS | 5+ Spanish incumbents [S11] |
| Chargeback SaaS (generic) | Chargeflow 25% of recovered with ROI guarantee [S16] |
| Trading journal | TradeZella $35-99/month, feature-saturated [S15] |
| XAUUSD literal rule | EXP-001 |

---

## 10. Risks and red team of this plan

- **Outreach law.** Spain's LSSI restricts unsolicited commercial email, including to businesses (UNVERIFIED for your exact case; get it checked). The plan therefore favours phone, visits, associations, LinkedIn and partner referrals. Nothing is sent without your approval.
- **Evidence quality.** Most market facts come from vendor blogs and search summaries. Primary sources (BOE, some vendor pages) were blocked here. Treat "FACT" as "seen in a source", not "audited".
- **Crowding.** S1 and S4 have active competitors. The bet is on vertical focus, validation quality and channel, not on a technology gap.
- **Human cost.** At small scale the economics depend on your hours. The scenario tables price your hour at €40 (ASM).
- **Security.**
  - Invoices contain personal data (NIFs of autónomos). Use a DPA, least privilege and no retention beyond need.
  - Keep the API key in an environment variable, never in code.
  - Treat invoice content as untrusted input: the pipeline uses structured output and deterministic checks, and never executes content.
- **Sunk-cost trap.** Energy and invoice code already exist. That is not a reason to continue them if the kill conditions trigger.

---

## 11. Sources

Accessed 2026-09-24. "(snippet)" means seen through search results only; the page itself could not be opened from this environment.

- **S1** Channel Partner, radiografía de las asesorías — https://www.channelpartner.es/ticpymes/radiografia-de-las-asesorias-en-espana-un-sector-clave-que-cambia-por-la-digitalizacion-la-ia-y-los-giros-normativos/ (snippet)
- **S2** TuAsesoríaIA, IA para contabilidad (cites Consejo General de Economistas 2025) — https://tuasesoriaia.com/ia-contabilidad/ (snippet; secondary)
- **S3** Vendor blogs on invoice OCR + IA for gestorías: https://copilotgestoria.com/blog/automatizar-procesamiento-facturas-ocr-ia-gestoria · https://xpertix.com/ia-gestorias-asesorias-automatizacion/ · https://ciberfobia.com/blog/contabilizacion-automatica-facturas/ (snippet; the €800-2,000 figure was not isolated to one page, so **weak**)
- **S4** DocuClipper pricing — https://www.docuclipper.com/pricing/ (snippet)
- **S5** Verifactu 2027 dates (RD-ley 15/2025) — https://advisory.ecija.com/verifactu-2027/ · https://grupoalbatros.org/2026/02/23/verifactu-aplazamiento-2027-rdl-15-2025/ (snippet)
- **S6** Datadis third-party access — https://dev.datadis.es/faqs · https://aelec.es/datadis/ (snippet)
- **S7** Power-optimisation consultancies — https://www.creara.es/gestion-energetica/optimizacion-potencia-contratada/ · https://tuasesoriaenergetica.com/inicio/asesoramiento-energetico-empresas/ (snippet)
- **S8** Datadis `get-max-power` endpoint — https://github.com/MrMarble/datadis (snippet)
- **S9** CNMC peajes 2026, BOE-A-2025-26348 — https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-26348 (snippet: 3.0TD power peaje P1 14.935084 €/kW·year … P6 0.535313; **not used in code**)
- **S10** Memoria técnica services and AI tools — https://www.concurra.es/ · https://licitek.com/consultoria-licitaciones-publicas/ · https://noetia.io/ · https://hans-soluciones.es/memorias-tecnicas-licitaciones/ (snippet)
- **S11** Spanish tender platforms — https://boletinclaro.es/blog/plataformas-licitaciones-espana-comparativa · https://licitafacil.pro/ · https://licitaalerta.com/ (snippet)
- **S12** Grant consultancy fees — https://blog.fandit.es/funcionan-consultoras-gestores-subvenciones/ · https://euremconsultores.es/tarifas/ (snippet)
- **S13** Free prop-firm equity guards on MQL5 — https://www.mql5.com/en/code/77350 · https://www.mql5.com/en/code/76437 (snippet)
- **S14** Backtest job budgets — https://www.mql5.com/en/job/245601 · https://www.mql5.com/en/job/224154 · https://www.upwork.com/freelance-jobs/mql-5/ (snippet)
- **S15** TradeZella pricing — https://www.tradezella.com/pricing (snippet)
- **S16** Chargeflow pricing — https://www.chargeflow.io/pricing (snippet)
- **S17** Spanish marketplace accounting tools — https://accountali.com/platform/contabilidad-marketplaces/ · https://mentorday.es/wikitips/caso-cerrar-liquidaciones-de-amazon-con-netto-sin-excel/ (snippet)
- **S18** A2X pricing — https://www.a2xaccounting.com/shopify/pricing (snippet)
- **S19** NRUA annulled (STS 620/2026, 19 May 2026) — https://net2rent.com/el-tribunal-supremo-anula-el-nrua/ · https://www.apivirtual.com/registro-unico-alquiler-vacacional-anulado-supremo-2026/ (snippet)
- **S20** CBAM definitive period — https://taxation-customs.ec.europa.eu/news/cbam-successfully-entered-force-1-january-2026-2026-01-14_en · https://www.epa.ie/our-services/licensing/climate-change/eu-carbon-border-adjustment-mechanism/ (snippet)
- **S21** EUDR postponement — https://www.consilium.europa.eu/en/press/press-releases/2025/12/18/deforestation-council-signs-off-targeted-revision-to-simplify-and-postpone-the-regulation/ (snippet)
- **S22** AI receptionist prices in Spain — https://myhabla.com/blog/precio-recepcionista-virtual-ia-espana-comparativa-2026 · https://ringuno.com/es/dental-clinics · https://clinicbot.es/ (snippet)
- **S23** BORME data sources — https://empresascreadashoy.com/ · https://apify.com/startquicklabs/borme-scraper-pro (snippet)
- **Market data** Twelve Data XAU/USD (connector), pulled 2026-09-24
- **Model prices** Claude API model table (skill reference cached 2026-06-24): Haiku 4.5 $1/$5, Opus 5 $5/$25 per MTok
