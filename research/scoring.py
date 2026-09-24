"""Decision-support score (NOT objective truth). All inputs are 1-5 JUDGMENTS made in cycle 01,
informed by the evidence in reports/cycle-01.md. Change the numbers when evidence arrives.

score = geometric_mean(8 positives) - 0.15 * sum(6 penalties)
"""
import math

POS = ["demand", "pain", "wtp", "frequency", "automation", "distribution", "margin", "defensibility"]
NEG = ["competition", "cac", "regulatory", "technical", "platform", "ai_cost"]
S = {
    "S1 Gestoría invoice-to-ledger":        ([4, 4, 4, 5, 4, 3, 4, 3], [4, 3, 2, 2, 1, 1]),
    "S2 Contracted-power audit":            ([3, 3, 3, 1, 5, 3, 5, 2], [4, 3, 1, 1, 2, 1]),
    "S3 Verifactu 2027 migration":          ([4, 3, 3, 1, 3, 3, 3, 1], [4, 3, 2, 1, 1, 1]),
    "S4 AI memoria técnica studio":         ([4, 4, 4, 3, 4, 3, 4, 2], [3, 3, 1, 2, 1, 2]),
    "S5 Grant application service":         ([4, 3, 4, 2, 3, 3, 4, 2], [4, 3, 2, 2, 1, 1]),
    "S6 Strategy falsification reports":    ([2, 3, 2, 2, 4, 4, 5, 2], [3, 2, 2, 1, 1, 1]),
    "S7 CBAM declarant service":            ([3, 4, 4, 4, 3, 2, 4, 3], [3, 4, 3, 3, 1, 1]),
    "S8 EUDR due diligence":                ([2, 4, 3, 3, 3, 2, 4, 3], [3, 4, 3, 3, 1, 1]),
    "S9 Tender price-to-win analytics":     ([2, 3, 3, 3, 4, 3, 5, 4], [2, 3, 1, 3, 1, 1]),
    "S10 Redsys chargeback handling":       ([2, 3, 3, 4, 3, 2, 4, 3], [2, 4, 2, 3, 3, 1]),
    "S11 Property-manager back office":     ([2, 3, 3, 5, 4, 2, 4, 3], [3, 4, 1, 2, 1, 1]),
    "S12 Insurance-broker claims intake":   ([2, 3, 3, 4, 4, 2, 4, 3], [3, 4, 2, 2, 1, 1]),
    "S13 Gestoría payroll incidents":       ([3, 4, 3, 5, 3, 3, 3, 3], [3, 3, 2, 3, 1, 1]),
    "S14 Procurement recovery audit":       ([2, 4, 4, 2, 4, 2, 4, 3], [2, 4, 1, 2, 1, 1]),
}

rows = []
for name, (p, n) in S.items():
    g = math.exp(sum(math.log(x) for x in p) / len(p))
    rows.append((g - 0.15 * sum(n), name, p, n))
print("| rank | opportunity | score | " + " | ".join(POS) + " | " + " | ".join(f"−{x}" for x in NEG) + " |")
print("|" + "---|" * (3 + len(POS) + len(NEG)))
for i, (sc, name, p, n) in enumerate(sorted(rows, reverse=True), 1):
    print(f"| {i} | {name} | {sc:.2f} | " + " | ".join(map(str, p)) + " | " + " | ".join(map(str, n)) + " |")
