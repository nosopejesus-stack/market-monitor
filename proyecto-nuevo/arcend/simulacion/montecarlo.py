"""
Simulación Monte Carlo v2 de estrategias de venta para Arcend (clínicas estéticas Madrid).

Cada ejecución sortea los PARÁMETROS (no conocemos las tasas reales) y después simula
semana a semana (azar operativo). Horizonte: 13 semanas. Importes en euros, sin IVA.
Resultado en CAJA NETA: descuenta cuota de autónomo (desde el primer sí), retención de
IRPF (caja que no entra ahora) e impagos.

v2 (tras revisión): cuotas cobradas desde el alta de cada cliente y churn solo tras el
primer cobro; variable a mes vencido y por cliente; retraso de decisión, horas de entrega
y precios por estrategia; tope de horas humanas por semana (la entrega quita tiempo a
la prospección); números aleatorios comunes entre estrategias; oportunidades abiertas al
final; sensibilidad por rangos (Spearman).

Uso: python3 montecarlo.py [--runs 20000] [--seed 1]
Todos los supuestos son SIN VERIFICAR hasta medir las primeras 20 puertas reales.
"""
import argparse
import json
import math
import numpy as np

SEMANAS = 13
CORTES = {"4sem": 3, "8sem": 7, "13sem": 12}   # índice de la última semana incluida


def beta(rng, media, fuerza):
    return rng.beta(media * fuerza, (1 - media) * fuerza)


def tri(rng, lo, mode, hi):
    if lo == hi:
        return float(lo)
    return rng.triangular(lo, mode, hi)


def semanas(rng, t):
    return int(math.floor(tri(rng, *t) + 0.5))


# Supuestos comunes: se sortean UNA vez por ejecución y se comparten entre estrategias.
COMUN = {
    "puertas_semana": (8, 15, 22),        # capacidad de prospección si no hay entrega
    "mercado_clinicas": (180, 260, 350),  # clínicas independientes alcanzables
    "churn_mensual": (0.02, 0.06, 0.15),
    "retencion_irpf": (0.0, 0.07, 0.15),  # 0 si actividad empresarial; 7/15 % profesional
    "p_impago": (0.0, 0.03, 0.08),
    "cuota_autonomo_mes": 80.0,           # SIN VERIFICAR (tarifa plana 2026)
    "horas_max_semana": 40.0,
    "horas_por_puerta": 0.5, "horas_por_reunion": 1.0, "horas_por_cierre": 2.0,
}

PAQ1 = {"setup": 1200, "cuota": 890}      # Atención
PAQ2 = {"setup": 1900, "cuota": 1290}     # Atención + Blindaje
AUDITORIA = 690                           # Blindaje suelto: auditoría + corrección

BASE = {
    "p_decisor": (0.40, 20), "p_informe": (0.50, 20),
    "decision": (1, 2, 4), "horas_extra_puerta": 0.0,
    "p_trimestral": None, "dto_trimestral": 0.10,
    "referidos": None, "upsell": None, "variable_mes": None,
    "horas_setup": (2, 4, 8), "horas_cliente_mes": (0.5, 1, 2),
    "canal": "visita",   # "visita": puertas en persona; "telefono": llamadas con cita previa
}
CANALES = {
    "visita":   {"mult_puertas": 1.0, "horas_por_puerta": 0.5},
    # Llamar con el anzuelo del informe ya hecho y pedir 10 min con el titular: más contactos por
    # hora, pero el decisor se alcanza menos por llamada (se aplica factor en p_decisor).
    "telefono": {"mult_puertas": 2.5, "horas_por_puerta": 0.2, "factor_decisor": 0.7},
}

ESTRATEGIAS = {
    "S1_notion": dict(BASE,
        desc="Notion: paquete 1 (1.200 + 890/mes) o 2 (1.900 + 1.290/mes); informe tras 1ª reunión",
        p_cierre=(0.25, 15), mezcla_premium=(0.3, 0.4, 0.6), paquetes=[PAQ1, PAQ2]),
    "S3_solo_premium": dict(BASE,
        desc="Solo paquete 2 (1.900 + 1.290/mes)",
        p_cierre=(0.18, 15), mezcla_premium=(1, 1, 1), paquetes=[PAQ2]),
    "S2_blindaje_primero": dict(BASE,
        desc="Auditoría + corrección de publicidad sanitaria 690 € único; al entregarla se ofrece el paquete 2 "
             "descontando lo pagado (1.210 + 1.290/mes)",
        p_informe=(0.60, 20), p_cierre=(0.35, 15), decision=(0, 0.5, 2),
        mezcla_premium=(0, 0, 0), paquetes=[{"setup": AUDITORIA, "cuota": 0}],
        horas_setup=(1, 2, 4), horas_cliente_mes=(0, 0, 0),
        upsell={"p": (0.25, 12), "semanas": (0, 1, 3),
                "setup": PAQ2["setup"] - AUDITORIA, "cuota": PAQ2["cuota"]}),
    "S4_resultados": dict(BASE,
        desc="Sin implantación: 490 €/mes + 60 € por paciente nuevo agendado (a mes vencido)",
        p_informe=(0.55, 20), p_cierre=(0.35, 15), decision=(0, 1, 2),
        mezcla_premium=(0, 0, 0), paquetes=[{"setup": 0, "cuota": 490}],
        variable_mes=(120, 300, 600)),
    "S5_notion_turbo": dict(BASE,
        desc="S1 + informe risk-scanner ya hecho en la 1ª visita y decisión en la reunión + opción de pago "
             "trimestral anticipado (-10 %) + referidos",
        p_informe=(0.85, 20), p_cierre=(0.22, 15), decision=(0, 1, 2), horas_extra_puerta=0.1,
        mezcla_premium=(0.3, 0.4, 0.6), paquetes=[PAQ1, PAQ2],
        p_trimestral=(0.35, 12), referidos=(0.3, 0.5, 0.8)),
    "S6_blindaje_turbo": dict(BASE,
        desc="S2 + informe ya hecho en la 1ª visita + upsell en la entrega + referidos",
        p_informe=(0.85, 20), p_cierre=(0.33, 15), decision=(0, 0.5, 1), horas_extra_puerta=0.1,
        mezcla_premium=(0, 0, 0), paquetes=[{"setup": AUDITORIA, "cuota": 0}],
        horas_setup=(1, 2, 4), horas_cliente_mes=(0, 0, 0),
        upsell={"p": (0.25, 12), "semanas": (0, 0.5, 2),
                "setup": PAQ2["setup"] - AUDITORIA, "cuota": PAQ2["cuota"]},
        p_trimestral=(0.35, 12), referidos=(0.3, 0.5, 0.8)),
    "S7_blindaje_continuo": dict(BASE,
        desc="Blindaje continuo: 390 € auditoría + corrección y 190 €/mes de vigilancia de web/RRSS "
             "(automatizada con risk-scanner); informe ya hecho en la 1ª visita; upsell a Atención más tarde",
        p_informe=(0.85, 20), p_cierre=(0.40, 15), decision=(0, 0.5, 1), horas_extra_puerta=0.1,
        mezcla_premium=(0, 0, 0), paquetes=[{"setup": 390, "cuota": 190}],
        horas_setup=(0.5, 1, 2), horas_cliente_mes=(0, 0.25, 0.5),
        upsell={"p": (0.15, 12), "semanas": (2, 4, 8), "setup": PAQ1["setup"], "cuota": PAQ1["cuota"]},
        p_trimestral=(0.35, 12), referidos=(0.3, 0.5, 0.8)),
    "S8_continuo_telefono": dict(BASE,
        desc="S7 captando por teléfono con cita previa (anzuelo: informe ya hecho de su web)",
        p_informe=(0.85, 20), p_cierre=(0.40, 15), decision=(0, 0.5, 1), horas_extra_puerta=0.1,
        mezcla_premium=(0, 0, 0), paquetes=[{"setup": 390, "cuota": 190}],
        horas_setup=(0.5, 1, 2), horas_cliente_mes=(0, 0.25, 0.5),
        upsell={"p": (0.15, 12), "semanas": (2, 4, 8), "setup": PAQ1["setup"], "cuota": PAQ1["cuota"]},
        p_trimestral=(0.35, 12), referidos=(0.3, 0.5, 0.8), canal="telefono"),
    "S10_menu_telefono": dict(BASE,
        desc="Menú de 3 escalones por teléfono con informe ya hecho: Blindaje continuo 390 + 190/mes · "
             "Atención 1.200 + 890/mes · Atención + Blindaje 1.900 + 1.290/mes; decisión en la reunión, "
             "trimestral opcional, referidos, y subida de escalón más tarde",
        p_informe=(0.85, 20), p_cierre=(0.30, 15), decision=(0, 0.5, 1.5), horas_extra_puerta=0.1,
        mezcla_premium=(0, 0, 0), paquetes=[{"setup": 390, "cuota": 190}, PAQ1, PAQ2],
        pesos=(11, 6, 3),   # Dirichlet: ~55 % barato, 30 % Atención, 15 % completo
        horas_setup=(1, 3, 6), horas_cliente_mes=(0.2, 0.6, 1.5),
        upsell={"p": (0.12, 12), "semanas": (3, 6, 10), "setup": PAQ1["setup"], "cuota": PAQ1["cuota"]},
        p_trimestral=(0.35, 12), referidos=(0.3, 0.5, 0.8), canal="telefono"),
    "S9_turbo_telefono": dict(BASE,
        desc="S5 (paquetes Notion con informe ya hecho, decisión en reunión, trimestral, referidos) por teléfono",
        p_informe=(0.85, 20), p_cierre=(0.22, 15), decision=(0, 1, 2), horas_extra_puerta=0.1,
        mezcla_premium=(0.3, 0.4, 0.6), paquetes=[PAQ1, PAQ2],
        p_trimestral=(0.35, 12), referidos=(0.3, 0.5, 0.8), canal="telefono"),
}


def sortear_comunes(rng):
    c = COMUN
    return {
        "puertas": tri(rng, *c["puertas_semana"]),
        "mercado": int(round(tri(rng, *c["mercado_clinicas"]))),
        "churn": tri(rng, *c["churn_mensual"]),
        "retencion": tri(rng, *c["retencion_irpf"]),
        "p_impago": tri(rng, *c["p_impago"]),
    }


def simular_una(est, cm, rng):
    c = COMUN
    canal = CANALES[est["canal"]]
    pd_ = beta(rng, *est["p_decisor"]) * canal.get("factor_decisor", 1.0)
    pi = beta(rng, *est["p_informe"])
    pc = beta(rng, *est["p_cierre"])
    mezcla = tri(rng, *est["mezcla_premium"])
    pesos = rng.dirichlet(est["pesos"]) if est.get("pesos") else None
    p_tri = beta(rng, *est["p_trimestral"]) if est["p_trimestral"] else 0.0
    ref_media = tri(rng, *est["referidos"]) if est["referidos"] else 0.0
    up = est["upsell"]
    p_up = beta(rng, *up["p"]) if up else 0.0

    ingresos = np.zeros(SEMANAS)
    horas_sem = np.zeros(SEMANAS)
    restantes = cm["mercado"]
    clientes = []            # dicts: alta, cuota, prepagado_hasta, var
    eventos = []             # (semana, tipo, datos)
    referidos_pend = np.zeros(SEMANAS + 8)
    primer_si = None
    abiertas = 0
    mrr_comprometido = 0.0

    def cobrar(semana, importe):
        if rng.random() < cm["p_impago"]:
            return
        ingresos[semana] += importe * (1 - cm["retencion"])

    for s in range(SEMANAS):
        # horas de entrega de esta semana (clientes activos + implantaciones)
        activos = [cl for cl in clientes if cl["alta"] <= s and cl["vivo"]]
        h_entrega = sum(cl["h_mes"] / 4 for cl in activos) + horas_sem[s]
        h_libres = max(0.0, c["horas_max_semana"] - h_entrega)
        h_puerta = canal["horas_por_puerta"] + est["horas_extra_puerta"]
        cap = int(h_libres // (h_puerta + pd_ * c["horas_por_reunion"]))
        n = min(rng.poisson(cm["puertas"] * canal["mult_puertas"]), restantes, cap)
        restantes -= n
        dec = rng.binomial(n, pd_) + int(referidos_pend[s])
        horas_sem[s] += n * h_puerta + dec * c["horas_por_reunion"]
        inf = rng.binomial(dec, pi)
        for _ in range(rng.binomial(inf, pc)):
            ws = s + semanas(rng, est["decision"])
            if ws >= SEMANAS:
                abiertas += 1
                continue
            if est.get("pesos"):
                paq = est["paquetes"][rng.choice(len(est["paquetes"]), p=pesos)]
            else:
                premium = rng.random() < mezcla
                paq = est["paquetes"][1 if premium and len(est["paquetes"]) > 1 else 0]
            eventos.append((ws, "firma", paq))
    # procesar firmas en orden (las firmas generan cobros, altas, upsells y referidos)
        for (w, tipo, paq) in [e for e in eventos if e[0] == s]:
            if tipo == "firma":
                if primer_si is None:
                    primer_si = s
                horas_sem[s] += c["horas_por_cierre"]
                h_setup = tri(rng, *est["horas_setup"])
                alta = s + max(1, semanas(rng, (1, 1.5, 3)))
                for k in range(2):  # reparto de horas de implantación
                    if s + k < SEMANAS:
                        horas_sem[s + k] += h_setup / 2
                cobrar(s, paq["setup"])
                if paq["cuota"] > 0:
                    nuevo_cliente(clientes, rng, est, cm, s, alta, paq["cuota"], p_tri, cobrar)
                if up and rng.random() < p_up:
                    wu = s + semanas(rng, up["semanas"])
                    if wu < SEMANAS:
                        eventos.append((wu, "upsell", {"setup": up["setup"], "cuota": up["cuota"]}))
                    else:
                        abiertas += 1
                if ref_media:
                    for _ in range(rng.poisson(ref_media)):
                        wr = s + int(rng.integers(2, 7))
                        if wr < SEMANAS:
                            referidos_pend[wr] += 1
            elif tipo == "upsell":
                horas_sem[s] += c["horas_por_reunion"] + c["horas_por_cierre"]
                cobrar(s, paq["setup"])
                nuevo_cliente(clientes, rng, est, cm, s, s + 1, paq["cuota"], p_tri, cobrar)
        # cuotas: cada 4 semanas desde el alta de cada cliente; churn tras el 1er cobro
        for cl in clientes:
            if not cl["vivo"] or s < cl["alta"] or (s - cl["alta"]) % 4:
                continue
            if s > cl["alta"] and rng.random() < cm["churn"]:
                cl["vivo"] = False
                continue
            if s >= cl["prepagado_hasta"]:
                cobrar(s, cl["cuota"])
            if cl["var"] and s > cl["alta"]:
                cobrar(s, tri(rng, *cl["var"]))
        # cuota de autónomo desde el primer sí
        if primer_si is not None and s >= primer_si and (s - primer_si) % 4 == 0:
            ingresos[s] -= c["cuota_autonomo_mes"]

    vivos = [cl for cl in clientes if cl["vivo"]]
    mrr = sum(cl["cuota"] + (cl["var"][1] if cl["var"] else 0) for cl in vivos)
    return ingresos, horas_sem.sum(), len(vivos), mrr, abiertas, {
        "p_decisor": pd_, "p_informe": pi, "p_cierre": pc, "mezcla": mezcla,
        "p_trimestral": p_tri, "referidos": ref_media, "p_upsell": p_up,
        "puertas": cm["puertas"], "churn": cm["churn"], "mercado": cm["mercado"],
        "retencion": cm["retencion"],
    }


def nuevo_cliente(clientes, rng, est, cm, s, alta, cuota, p_tri, cobrar):
    prepagado = alta
    if p_tri and rng.random() < p_tri:  # 3 meses por adelantado en la firma con descuento
        cobrar(s, 3 * cuota * (1 - est["dto_trimestral"]))
        prepagado = alta + 12
    clientes.append({"alta": alta, "cuota": cuota, "prepagado_hasta": prepagado, "vivo": True,
                     "h_mes": tri(rng, *est["horas_cliente_mes"]), "var": est["variable_mes"]})


def rangos(x):
    return np.argsort(np.argsort(x)).astype(float)


def correr(runs, seed):
    res = {}
    nombres = list(ESTRATEGIAS)
    datos = {n: {"ing": np.zeros((runs, SEMANAS)), "horas": np.zeros(runs), "cli": np.zeros(runs),
                 "mrr": np.zeros(runs), "abiertas": np.zeros(runs), "params": []} for n in nombres}
    for r in range(runs):
        cm = sortear_comunes(np.random.default_rng([seed, r]))
        for i, n in enumerate(nombres):
            ing, h, cli, mrr, ab, p = simular_una(ESTRATEGIAS[n], cm, np.random.default_rng([seed, r, i + 1]))
            d = datos[n]
            d["ing"][r], d["horas"][r], d["cli"][r], d["mrr"][r], d["abiertas"][r] = ing, h, cli, mrr, ab
            d["params"].append(p)
    for n in nombres:
        d = datos[n]
        acum = d["ing"].cumsum(axis=1)
        f = {k: acum[:, i] for k, i in CORTES.items()}
        cobra = d["ing"] > 0
        primera = np.array([np.argmax(row) if row.any() else np.nan for row in cobra])
        out = {"estrategia": n, "desc": ESTRATEGIAS[n]["desc"]}
        for k, v in f.items():
            out[f"P(>=10k {k})"] = float((v >= 10000).mean())
            out[f"mediana_{k}"] = float(np.median(v))
        out["p10_13sem"] = float(np.percentile(f["13sem"], 10))
        out["p90_13sem"] = float(np.percentile(f["13sem"], 90))
        out["P(caja<=0 a 4sem)"] = float((f["4sem"] <= 0).mean())
        out["P(sin cobro 13sem)"] = float(np.isnan(primera).mean())
        out["semana_1er_cobro_mediana"] = float(np.nanmedian(primera)) + 1 if (~np.isnan(primera)).any() else None
        out["mrr_mediano_13sem"] = float(np.median(d["mrr"]))
        out["clientes_mediana_13sem"] = float(np.median(d["cli"]))
        out["oportunidades_abiertas_mediana"] = float(np.median(d["abiertas"]))
        out["horas_humanas_mediana"] = float(np.median(d["horas"]))
        out["eur_hora_13sem"] = float(np.median(f["13sem"] / np.maximum(d["horas"], 1)))
        rv = rangos(f["13sem"])
        sens = {}
        for k in d["params"][0]:
            x = np.array([p[k] for p in d["params"]])
            if x.std() > 0:
                sens[k] = float(np.corrcoef(rangos(x), rv)[0, 1])
        out["sensibilidad_spearman_13sem"] = dict(sorted(sens.items(), key=lambda kv: -abs(kv[1]))[:5])
        res[n] = out
    return res


# Escenario "mercado": calibrado con investigacion/mercado.md (tasas prudentes).
# Por puerta: decisor ~20 %; cierre ~8 % de las conversaciones con decisor.
MERCADO = {
    "COMUN": {"mercado_clinicas": (250, 450, 700), "churn_mensual": (0.02, 0.04, 0.08)},
    "p_decisor": (0.20, 15),
    "p_cierre": {"S1_notion": (0.13, 15), "S3_solo_premium": (0.09, 15), "S2_blindaje_primero": (0.20, 15),
                 "S4_resultados": (0.20, 15), "S5_notion_turbo": (0.11, 15), "S6_blindaje_turbo": (0.19, 15),
                 "S7_blindaje_continuo": (0.24, 15), "S8_continuo_telefono": (0.24, 15), "S9_turbo_telefono": (0.11, 15), "S10_menu_telefono": (0.16, 15)},
}


def aplicar_escenario(nombre):
    if nombre != "mercado":
        return
    COMUN.update(MERCADO["COMUN"])
    for n, est in ESTRATEGIAS.items():
        est["p_decisor"] = MERCADO["p_decisor"]
        est["p_cierre"] = MERCADO["p_cierre"][n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", choices=["notion", "mercado"], default="mercado")
    ap.add_argument("--runs", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", default="resultados.json")
    a = ap.parse_args()
    aplicar_escenario(a.escenario)
    print(f"Escenario: {a.escenario} · {a.runs} ejecuciones")
    res = correr(a.runs, a.seed)
    json.dump(list(res.values()), open(a.json, "w"), indent=2, ensure_ascii=False)
    cols = ["P(>=10k 4sem)", "P(>=10k 8sem)", "P(>=10k 13sem)", "mediana_4sem", "mediana_8sem",
            "mediana_13sem", "p10_13sem", "P(caja<=0 a 4sem)", "mrr_mediano_13sem", "horas_humanas_mediana"]
    print("caja NETA (€)".ljust(22) + "".join(c[:13].rjust(14) for c in cols))
    for r in res.values():
        print(r["estrategia"][:21].ljust(22) + "".join(
            (f"{r[c]:.0%}" if c.startswith("P(") else f"{r[c]:,.0f}").rjust(14) for c in cols))
    for r in res.values():
        print(f'{r["estrategia"]}: 1er cobro sem {r["semana_1er_cobro_mediana"]}, abiertas {r["oportunidades_abiertas_mediana"]:.0f}, '
              f'sens {({k: round(v, 2) for k, v in r["sensibilidad_spearman_13sem"].items()})}')


if __name__ == "__main__":
    main()
