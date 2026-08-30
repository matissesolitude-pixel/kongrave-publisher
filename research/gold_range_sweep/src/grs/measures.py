"""Les 4 mesures + intervalles de Wilson + verdicts d'abandon.

Aucune interpretation ici : des comptes, des proportions, des bornes.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .constants import (
    ABANDON_COND_EDGE_MIN,
    ABANDON_NET_EXPECTANCY_MIN,
    ABANDON_TOP_DECILE_MAX,
    ABANDON_UNCOND_TOUCH_MIN,
    WILSON_Z,
)
from .sessions import opposite_first

CLASSES = ("SWEEP_HAUT", "SWEEP_BAS", "BREAKOUT_HAUT", "BREAKOUT_BAS", "NONE")


def wilson(k: int, n: int, z: float = WILSON_Z) -> tuple[float, float, float]:
    """(proportion, borne basse, borne haute) a 95 %."""
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z / d * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, max(0.0, c - h), min(1.0, c + h)


# ---------------------------------------------------------------------------
# MESURE 1 -- inconditionnel
# ---------------------------------------------------------------------------
def measure1(s: pd.DataFrame) -> pd.DataFrame:
    n = len(s)
    hi = s["touch_haute_avant_cutoff"].astype(bool)
    lo = s["touch_basse_avant_cutoff"].astype(bool)
    rows = []
    for label, mask in (
        ("cible haute touchee", hi),
        ("cible basse touchee", lo),
        ("au moins une des deux", hi | lo),
        ("les deux", hi & lo),
    ):
        k = int(mask.sum())
        p, l, u = wilson(k, n)
        rows.append({"evenement": label, "k": k, "n": n,
                     "proportion": p, "ic95_bas": l, "ic95_haut": u})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# MESURE 2 -- conditionnel
# ---------------------------------------------------------------------------
def measure2(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    s["opp_first"] = s.apply(opposite_first, axis=1)
    rows = []
    for klass in CLASSES:
        sub = s[s["classe"] == klass]
        if klass == "NONE":
            continue
        res = sub[np.isfinite(sub["opp_first"])]
        k, n = int(res["opp_first"].sum()), len(res)
        p, l, u = wilson(k, n)
        rows.append({
            "classe": klass,
            "n_sessions": len(sub),
            "n_resolues": n,
            "n_non_resolues": len(sub) - n,
            "k_cible_opposee_en_premier": k,
            "proportion": p, "ic95_bas": l, "ic95_haut": u,
            "vs_50pct": _vs_half(l, u),
        })
    return pd.DataFrame(rows)


def _vs_half(lo: float, hi: float) -> str:
    if not np.isfinite(lo):
        return "n/a"
    if lo > 0.5:
        return "au-dessus de 50% (IC95 exclut 50%)"
    if hi < 0.5:
        return "en-dessous de 50% (IC95 exclut 50%)"
    return "indistinguable de 50% (IC95 contient 50%)"


# ---------------------------------------------------------------------------
# MESURE 3 -- MFE / MAE / esperance
# ---------------------------------------------------------------------------
def measure3(s: pd.DataFrame) -> pd.DataFrame:
    tr = s[np.isfinite(s["pnl_net_R"])]
    rows = []
    for klass in [c for c in CLASSES if c != "NONE"] + ["TOUTES"]:
        sub = tr if klass == "TOUTES" else tr[tr["classe"] == klass]
        n = len(sub)
        if n == 0:
            rows.append({"classe": klass, "n_trades": 0})
            continue
        g, net = sub["pnl_gross_R"], sub["pnl_net_R"]
        rows.append({
            "classe": klass, "n_trades": n,
            "mfe_moy_R": sub["mfe_R"].mean(), "mfe_med_R": sub["mfe_R"].median(),
            "mae_moy_R": sub["mae_R"].mean(), "mae_med_R": sub["mae_R"].median(),
            "esperance_brute_R": g.mean(), "esperance_nette_R": net.mean(),
            "ecart_brut_net_R": g.mean() - net.mean(),
            "cout_moy_R": (sub["spread_entry_usd"] / sub["R"]).mean(),
            "spread_entree_moy_pts": sub["spread_entry_pts"].mean(),
            "taux_cible": (sub["exit_reason"] == "cible").mean(),
            "taux_stop": (sub["exit_reason"] == "stop").mean(),
            "taux_sortie_horaire": (sub["exit_reason"] == "sortie_horaire").mean(),
            "ecart_type_net_R": net.std(ddof=1) if n > 1 else float("nan"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# MESURE 4 -- stabilite
# ---------------------------------------------------------------------------
def measure4(s: pd.DataFrame) -> dict[str, pd.DataFrame | float]:
    tr = s[np.isfinite(s["pnl_net_R"])]

    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def _agg(by: str) -> pd.DataFrame:
        if tr.empty:
            return pd.DataFrame(columns=[by, "n_trades", "esperance_brute_R", "esperance_nette_R"])
        src = tr
        if by == "weekday":
            src = tr.assign(weekday=pd.Categorical(tr["weekday"], categories=order, ordered=True))
        g = src.groupby(by, sort=True, observed=True)
        out = pd.DataFrame({
            "n_trades": g.size(),
            "esperance_brute_R": g["pnl_gross_R"].mean(),
            "esperance_nette_R": g["pnl_net_R"].mean(),
            "total_net_R": g["pnl_net_R"].sum(),
        }).reset_index()
        return out

    return {
        "par_trimestre": _agg("quarter"),
        "par_jour": _agg("weekday"),
        "decile_superieur": top_decile_share(tr["pnl_net_R"]),
        "n_trades": len(tr),
    }


def top_decile_share(pnl: pd.Series) -> dict:
    """Part de l'esperance totale portee par le decile de sessions le plus performant."""
    v = np.sort(pnl.dropna().to_numpy())[::-1]
    n = len(v)
    if n == 0:
        return {"n": 0, "n_decile": 0, "part": float("nan"), "total_R": float("nan"),
                "note": "aucun trade"}
    k = max(1, math.ceil(n / 10))
    total, top = float(v.sum()), float(v[:k].sum())
    if total <= 0:
        return {"n": n, "n_decile": k, "part": float("nan"), "total_R": total,
                "top_R": top,
                "note": "total net <= 0 : la part du decile n'a pas de sens, "
                        "critere non applicable"}
    part = top / total
    note = ""
    if part > 1.0:
        note = ("le reste de l'echantillon contribue negativement : la totalite de "
                "l'esperance, et au-dela, vient du decile superieur")
    return {"n": n, "n_decile": k, "part": part, "total_R": total, "top_R": top,
            "note": note}


# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------
def verdicts(m1: pd.DataFrame, m2: pd.DataFrame, m3: pd.DataFrame, m4: dict) -> pd.DataFrame:
    rows = []

    au_moins_une = float(m1.loc[m1["evenement"] == "au moins une des deux", "proportion"].iloc[0])
    rows.append({
        "critere": f"Taux de touche inconditionnel (au moins une cible) >= {ABANDON_UNCOND_TOUCH_MIN:.0%} avant le cutoff",
        "valeur": f"{au_moins_une:.1%}",
        "verdict": "PASS" if au_moins_une >= ABANDON_UNCOND_TOUCH_MIN else "FAIL",
    })

    best = m2["proportion"].max() if len(m2) and m2["proportion"].notna().any() else float("nan")
    best_cls = m2.loc[m2["proportion"].idxmax(), "classe"] if np.isfinite(best) else "-"
    cond_ok = np.isfinite(best) and best >= ABANDON_COND_EDGE_MIN

    net = float(m3.loc[m3["classe"] == "TOUTES", "esperance_nette_R"].iloc[0]) \
        if "esperance_nette_R" in m3.columns and (m3["classe"] == "TOUTES").any() else float("nan")
    exp_ok = np.isfinite(net) and net >= ABANDON_NET_EXPECTANCY_MIN

    rows.append({
        "critere": f"Edge conditionnelle >= {ABANDON_COND_EDGE_MIN:.0%} ET esperance nette >= {ABANDON_NET_EXPECTANCY_MIN:.2f}R",
        "valeur": f"meilleure edge {best:.1%} ({best_cls}) ; esperance nette {net:+.3f}R"
                  if np.isfinite(best) else f"edge n/a ; esperance nette {net:+.3f}R",
        "verdict": "PASS" if (cond_ok and exp_ok) else "FAIL",
    })

    dec = m4["decile_superieur"]
    part = dec.get("part", float("nan"))
    if not np.isfinite(part):
        v, val = "FAIL", f"non applicable ({dec.get('note', '')})"
    else:
        v = "PASS" if part <= ABANDON_TOP_DECILE_MAX else "FAIL"
        share = ">100%" if part > 1.0 else f"{part:.1%}"
        val = f"{share} de l'esperance totale sur {dec['n_decile']}/{dec['n']} sessions"
        if dec.get("note"):
            val += f" ({dec['note']})"
    rows.append({
        "critere": f"Part du decile superieur <= {ABANDON_TOP_DECILE_MAX:.0%}",
        "valeur": val, "verdict": v,
    })
    return pd.DataFrame(rows)
