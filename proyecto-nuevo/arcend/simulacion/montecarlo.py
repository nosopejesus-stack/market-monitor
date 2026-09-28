"""
Simulación Monte Carlo de estrategias de venta para Arcend (clínicas estéticas Madrid).

Cada ejecución sortea primero los PARÁMETROS (incertidumbre real: no sabemos las tasas)
y después simula semana a semana (azar operativo). Así el resultado refleja las dos
incertidumbres. Horizonte: 13 semanas (~90 días). Importes en euros, sin IVA.

Uso: python3 montecarlo.py [--runs 20000] [--seed 1]
Los supuestos están en ESTRATEGIAS y COMUN; todos son SIN VERIFICAR hasta medir las
primeras 20 puertas reales (ver informe).
"""
import argparse
import json
import numpy as np

SEMANAS = 13


def beta(rng, media, fuerza):
    """Beta con media dada; 'fuerza' alta = más seguros del valor."""
    return rng.beta(media * fuerza, (1 - media) * fuerza)


def tri(rng, lo, mode, hi):
    if lo == hi:  # valor fijo (p. ej. precio cerrado)
        return float(lo)
    return rng.triangular(lo, mode, hi)


COMUN = {
    "puertas_semana": (8, 15, 22),       # visitas/llamadas en frío que el usuario puede hacer por semana
    "mercado_clinicas": (180, 260, 350), # clínicas independientes alcanzables (Madrid capital)
    "semanas_hasta_decision": (1, 2, 4), # desde la conversación con decisor hasta el sí/no
    "semanas_implantacion": (1, 1.5, 3), # desde la firma hasta que el servicio funciona
    "churn_mensual": (0.02, 0.06, 0.15),
    "horas_por_puerta": 0.5, "horas_por_reunion": 1.0, "horas_por_cierre": 3.0,
}

# Tasas: (media, fuerza de la Beta). Precios: triangulares (lo, moda, hi).
ESTRATEGIAS = {
    "S1_notion_dos_paquetes": {
        "desc": "Oferta de Notion: 1.200 € + 890 €/mes o 1.900 € + 1.290 €/mes; informe risk-scanner como gancho",
        "p_decisor": (0.40, 20), "p_informe": (0.50, 20), "p_cierre": (0.25, 15),
        "mezcla_premium": (0.3, 0.4, 0.6),
        "setup": [(1200, 1200, 1200), (1900, 1900, 1900)],
        "cuota": [(890, 890, 890), (1290, 1290, 1290)],
        "pago_setup_firma": 1.0,
        "upsell": None,
    },
    "S2_blindaje_primero": {
        "desc": "Entrada barata y urgente: auditoría + corrección de publicidad sanitaria (web/RRSS) 690 € pago único; "
                "después se ofrece la cuota Atención+Blindaje",
        "p_decisor": (0.40, 20), "p_informe": (0.60, 20), "p_cierre": (0.35, 12),
        "mezcla_premium": (0, 0, 0),
        "setup": [(490, 690, 990)], "cuota": [(0, 0, 0)],
        "pago_setup_firma": 1.0,
        "upsell": {"p": (0.25, 10), "semanas": (2, 4, 8), "setup": (900, 1200, 1500), "cuota": (790, 990, 1290)},
    },
    "S3_solo_premium": {
        "desc": "Un único paquete: Atención + Blindaje 1.900 € + 1.290 €/mes",
        "p_decisor": (0.40, 20), "p_informe": (0.50, 20), "p_cierre": (0.18, 12),
        "mezcla_premium": (1, 1, 1),
        "setup": [(1900, 1900, 1900), (1900, 1900, 1900)],
        "cuota": [(1290, 1290, 1290), (1290, 1290, 1290)],
        "pago_setup_firma": 1.0,
        "upsell": None,
    },
    "S4_sin_entrada_a_resultados": {
        "desc": "Sin implantación: 490 €/mes + 60 € por paciente nuevo agendado (menos barrera, cobro más lento)",
        "p_decisor": (0.40, 20), "p_informe": (0.55, 20), "p_cierre": (0.35, 12),
        "mezcla_premium": (0, 0, 0),
        "setup": [(0, 0, 0)], "cuota": [(490, 490, 490)],
        "variable_mes": (120, 300, 600),
        "pago_setup_firma": 1.0,
        "upsell": None,
    },
}


def simular(est, rng, runs):
    c = COMUN
    ingresos_semana = np.zeros((runs, SEMANAS))
    horas = np.zeros(runs)
    clientes_fin = np.zeros(runs)
    mrr_fin = np.zeros(runs)
    params = {k: np.zeros(runs) for k in ("p_decisor", "p_informe", "p_cierre", "puertas", "churn")}
    for r in range(runs):
        pd_, pi, pc = (beta(rng, *est[k]) for k in ("p_decisor", "p_informe", "p_cierre"))
        puertas_sem = tri(rng, *c["puertas_semana"])
        mercado = int(tri(rng, *c["mercado_clinicas"]))
        churn = tri(rng, *c["churn_mensual"])
        mezcla = tri(rng, *est["mezcla_premium"]) if est["mezcla_premium"][2] > 0 else 0.0
        params["p_decisor"][r], params["p_informe"][r], params["p_cierre"][r] = pd_, pi, pc
        params["puertas"][r], params["churn"][r] = puertas_sem, churn
        up = est.get("upsell")
        p_up = beta(rng, *up["p"]) if up else 0.0

        restantes = mercado
        activos = []  # cuotas mensuales de clientes activos
        pendientes_alta = []  # (semana_inicio_cuota, cuota)
        h = 0.0
        for s in range(SEMANAS):
            n = min(rng.poisson(puertas_sem), restantes)
            restantes -= n
            h += n * c["horas_por_puerta"]
            dec = rng.binomial(n, pd_)
            inf = rng.binomial(dec, pi)
            h += dec * c["horas_por_reunion"]
            cierres = rng.binomial(inf, pc)
            for _ in range(cierres):
                lag = int(round(tri(rng, *c["semanas_hasta_decision"])))
                ws = s + lag
                if ws >= SEMANAS:
                    continue
                h += c["horas_por_cierre"]
                premium = rng.random() < mezcla
                i = 1 if (premium and len(est["setup"]) > 1) else 0
                setup = tri(rng, *est["setup"][i])
                cuota = tri(rng, *est["cuota"][i])
                ingresos_semana[r, ws] += setup * est["pago_setup_firma"]
                alta = ws + int(round(tri(rng, *c["semanas_implantacion"])))
                if cuota > 0:
                    pendientes_alta.append((alta, cuota))
                if up and rng.random() < p_up:
                    wu = ws + int(round(tri(rng, *up["semanas"])))
                    if wu < SEMANAS:
                        ingresos_semana[r, wu] += tri(rng, *up["setup"])
                        pendientes_alta.append((wu + 1, tri(rng, *up["cuota"])))
            # altas que empiezan esta semana
            nuevos = [q for (w, q) in pendientes_alta if w == s]
            activos.extend(nuevos)
            # cuota: se cobra cada 4 semanas desde el alta (aprox. mensual)
            if s % 4 == 0 and activos:
                sobreviven = [q for q in activos if rng.random() > churn]
                activos = sobreviven
                var = tri(rng, *est["variable_mes"]) if "variable_mes" in est else 0.0
                ingresos_semana[r, s] += sum(activos) + var * len(activos)
        horas[r] = h
        clientes_fin[r] = len(activos)
        mrr_fin[r] = sum(activos)
    return ingresos_semana, horas, clientes_fin, mrr_fin, params


def resumen(nombre, est, datos):
    ing, horas, cli, mrr, params = datos
    acum = ing.cumsum(axis=1)
    d30, d60, d90 = acum[:, 3], acum[:, 8], acum[:, 12]
    out = {
        "estrategia": nombre,
        "P(>=10k en 30d)": float((d30 >= 10000).mean()),
        "P(>=10k en 60d)": float((d60 >= 10000).mean()),
        "P(>=10k en 90d)": float((d90 >= 10000).mean()),
        "mediana_30d": float(np.median(d30)), "mediana_60d": float(np.median(d60)),
        "mediana_90d": float(np.median(d90)), "p10_90d": float(np.percentile(d90, 10)),
        "p90_90d": float(np.percentile(d90, 90)),
        "P(0 € en 30d)": float((d30 == 0).mean()),
        "semana_mediana_1er_cobro": float(np.median([np.argmax(row > 0) if row.any() else 99 for row in ing])),
        "mrr_mediano_90d": float(np.median(mrr)), "clientes_mediana_90d": float(np.median(cli)),
        "horas_humanas_mediana": float(np.median(horas)),
        "eur_por_hora_humana_90d": float(np.median(d90 / np.maximum(horas, 1))),
    }
    sens = {k: float(np.corrcoef(v, d90)[0, 1]) for k, v in params.items() if v.std() > 0}
    out["sensibilidad_corr_con_90d"] = dict(sorted(sens.items(), key=lambda kv: -abs(kv[1])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", default="resultados.json")
    a = ap.parse_args()
    res = []
    for i, (n, est) in enumerate(ESTRATEGIAS.items()):
        rng = np.random.default_rng(a.seed + i)
        res.append(resumen(n, est, simular(est, rng, a.runs)))
    json.dump(res, open(a.json, "w"), indent=2, ensure_ascii=False)
    cols = ["P(>=10k en 30d)", "P(>=10k en 60d)", "P(>=10k en 90d)", "mediana_30d", "mediana_90d",
            "p10_90d", "P(0 € en 30d)", "mrr_mediano_90d", "horas_humanas_mediana", "eur_por_hora_humana_90d"]
    print("estrategia".ljust(30) + "".join(c[:14].rjust(15) for c in cols))
    for r in res:
        print(r["estrategia"][:29].ljust(30) + "".join(
            (f"{r[c]:.0%}" if c.startswith("P(") else f"{r[c]:,.0f}").rjust(15) for c in cols))
    for r in res:
        print(r["estrategia"], "sensibilidad:", {k: round(v, 2) for k, v in r["sensibilidad_corr_con_90d"].items()})


if __name__ == "__main__":
    main()
