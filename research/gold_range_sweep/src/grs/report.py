"""Redaction de out/report.md et des graphiques.

Le rapport ne contient que des chiffres et des bornes. Aucune recommandation,
aucune conclusion de trading.
"""
from __future__ import annotations

import datetime as dt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .constants import (
    ABANDON_COND_EDGE_MIN,
    ABANDON_NET_EXPECTANCY_MIN,
    ABANDON_TOP_DECILE_MAX,
    ABANDON_UNCOND_TOUCH_MIN,
    BREAKOUT_CONFIRM_BARS,
    BREAKOUT_STOP_BUFFER_R,
    COND_RACE_START,
    MAX_RANGE_GAP_MIN,
    PLOTS_DIR,
    POINT,
    PROJECTION_FACTOR,
    REPORT_MD,
    SWEEP_MAX_BARS,
)
from .measures import measure1, measure2, measure3, measure4, verdicts


def _md(df: pd.DataFrame, floats: int = 4) -> str:
    if df is None or df.empty:
        return "_(aucune ligne)_\n"
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else f"{x:.{floats}f}")
    head = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "| " + " | ".join("---" for _ in d.columns) + " |"
    body = "\n".join("| " + " | ".join(map(str, r)) + " |" for r in d.to_numpy())
    return f"{head}\n{sep}\n{body}\n"


def build_report(per_anchor: dict[str, pd.DataFrame], excluded: pd.DataFrame,
                 common_dates: int, note: str = "") -> str:
    L: list[str] = []
    A = L.append
    A("# XAUUSD - range fin de session US, deblayage a l'ouverture asiatique")
    A("")
    A(f"Genere le {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. "
      "Backtest et statistiques uniquement.")
    if note:
        A("")
        A(note)
    A("")

    results = {}
    for name, s in per_anchor.items():
        m1 = measure1(s)
        m2 = measure2(s)
        m3 = measure3(s)
        m4 = measure4(s)
        results[name] = (m1, m2, m3, m4, verdicts(m1, m2, m3, m4))

    # ---------------- criteres d'abandon, en tete ----------------
    A("## Criteres d'abandon")
    A("")
    A("Ecrits avant tout resultat. Un critere FAIL est un critere non franchi, rien de plus.")
    A("")
    for name, (_, _, _, _, v) in results.items():
        A(f"### {name}")
        A("")
        A(_md(v))
        A("")

    # ---------------- echantillon ----------------
    A("## Echantillon")
    A("")
    A(f"- Sessions retenues, identiques pour les deux ancrages : **{common_dates}**")
    for name, s in per_anchor.items():
        A(f"- {name} : {len(s)} sessions, "
          f"R median {s['R'].median():.2f} USD ({s['R_pts'].median():.0f} points)")
    A("")
    if not excluded.empty:
        A("Sessions ecartees, par motif :")
        A("")
        piv = (excluded.groupby(["motif", "ancrage"]).size()
               .unstack(fill_value=0).reset_index())
        A(_md(piv, floats=0))
        A("")
        A("Le detail session par session est dans `data/excluded.csv`.")
    A("")

    # ---------------- mesures ----------------
    titles = {
        1: "MESURE 1 - inconditionnel",
        2: "MESURE 2 - conditionnel",
        3: "MESURE 3 - MFE / MAE et esperance",
        4: "MESURE 4 - stabilite",
    }
    for name, (m1, m2, m3, m4, _) in results.items():
        A(f"## {name}")
        A("")
        A(f"### {titles[1]}")
        A("")
        A("Sur toutes les sessions retenues, sans aucune condition d'entree. "
          "Touche mesuree entre la fin du range et le cutoff.")
        A("")
        A(_md(m1))
        A("")
        A(f"### {titles[2]}")
        A("")
        A("Probabilite que la cible **opposee** a la classe soit touchee avant la cible "
          f"du meme cote. Course mesuree a partir de `{COND_RACE_START}` jusqu'a l'heure "
          "de sortie. Les sessions ou aucune des deux cibles n'est touchee sont comptees "
          "a part (`n_non_resolues`) et ne comptent jamais comme un succes.")
        A("")
        A(_md(m2))
        A("")
        A(f"### {titles[3]}")
        A("")
        A("MFE et MAE en multiples de R. `esperance_brute_R` et `esperance_nette_R` sont "
          "cote a cote ; `ecart_brut_net_R` est le cout d'execution, calcule avec le "
          "spread horodate de la bougie d'entree de chaque trade.")
        A("")
        A(_md(m3))
        A("")
        A(f"### {titles[4]}")
        A("")
        A("**Par trimestre**")
        A("")
        A(_md(m4["par_trimestre"]))
        A("")
        A("**Par jour de semaine**")
        A("")
        A(_md(m4["par_jour"]))
        A("")
        d = m4["decile_superieur"]
        if np.isfinite(d.get("part", float("nan"))):
            share = ">100%" if d["part"] > 1.0 else f"{d['part']:.1%}"
            A(f"**Decile superieur** : les {d['n_decile']} meilleures sessions sur {d['n']} "
              f"portent {share} du total net ({d['top_R']:+.2f}R sur {d['total_R']:+.2f}R)."
              + (f" {d['note'].capitalize()}." if d.get("note") else ""))
        else:
            A(f"**Decile superieur** : {d.get('note', 'non calculable')}"
              + (f" (total net {d['total_R']:+.2f}R)." if np.isfinite(d.get("total_R", np.nan)) else "."))
        A("")

    # ---------------- comparatif ----------------
    A("## Comparatif ANCRAGE_UTC vs ANCRAGE_NY")
    A("")
    A(_md(_comparison(per_anchor, results)))
    A("")

    # ---------------- parametres ----------------
    A("## Parametres et hypotheses de modelisation")
    A("")
    A(f"- Facteur de projection : **{PROJECTION_FACTOR}** "
      "(`PROJECTION_FACTOR` dans `src/grs/constants.py`, une seule valeur a changer)")
    A(f"- SWEEP : retour en {SWEEP_MAX_BARS} bougies M5 ou moins, bougie de franchissement incluse")
    A(f"- BREAKOUT : {BREAKOUT_CONFIRM_BARS} clotures M5 consecutives au-dela de la borne, sans retour")
    A(f"- Exclusion sur trou de donnees dans le range : > {MAX_RANGE_GAP_MIN} min")
    A(f"- 1 point = {POINT} USD")
    A("- OHLC construit sur le **bid** ; bougies posees sur la grille **UTC**")
    A("- Cout d'execution : un spread plein par aller-retour, pris sur la bougie d'entree "
      "(`spread_close_pts` pour une entree a la cloture, `spread_mean_pts` pour une entree "
      "en limite sur la borne). Aucun spread moyen global n'est utilise nulle part.")
    A("")
    A("**Hypothese ajoutee la ou le cahier des charges est muet** : pour un BREAKOUT, "
      f"le stop est place a **{BREAKOUT_STOP_BUFFER_R} R** de l'autre cote de la borne "
      "franchie (`BREAKOUT_STOP_BUFFER_R`). Le cahier des charges dit \"stop de l'autre "
      "cote de la borne\" sans donner de distance, et une distance nulle serait degeneree "
      "puisque l'entree se fait sur la borne elle-meme. Ce choix influence directement "
      "l'esperance des deux classes BREAKOUT.")
    A("")
    A("## Graphiques")
    A("")
    A("- `plots/distribution_temps_de_touche.png`")
    A("- `plots/distribution_R.png`")
    A("- `plots/spread_par_tranche_5min.png`")
    A("")
    return "\n".join(L)


def _comparison(per_anchor: dict[str, pd.DataFrame], results: dict) -> pd.DataFrame:
    rows = []
    names = list(per_anchor)

    def add(label, fn):
        r = {"indicateur": label}
        for n in names:
            r[n] = fn(n)
        rows.append(r)

    add("sessions", lambda n: f"{len(per_anchor[n])}")
    add("R median (USD)", lambda n: f"{per_anchor[n]['R'].median():.2f}")
    for ev in ("cible haute touchee", "cible basse touchee", "au moins une des deux", "les deux"):
        add(f"M1 {ev}", lambda n, ev=ev: _p(results[n][0], "evenement", ev))
    for cl in ("SWEEP_HAUT", "SWEEP_BAS", "BREAKOUT_HAUT", "BREAKOUT_BAS"):
        add(f"repartition {cl}",
            lambda n, cl=cl: f"{(per_anchor[n]['classe'] == cl).sum()} "
                             f"({(per_anchor[n]['classe'] == cl).mean():.1%})")
        add(f"M2 {cl} (cible opposee en 1er)", lambda n, cl=cl: _p2(results[n][1], cl))
    add("repartition NONE",
        lambda n: f"{(per_anchor[n]['classe'] == 'NONE').sum()} "
                  f"({(per_anchor[n]['classe'] == 'NONE').mean():.1%})")
    add("sessions double_side", lambda n: f"{int(per_anchor[n]['double_side'].sum())}")
    add("M3 esperance brute (R, toutes)", lambda n: _m3(results[n][2], "esperance_brute_R"))
    add("M3 esperance nette (R, toutes)", lambda n: _m3(results[n][2], "esperance_nette_R"))
    add("M3 cout d'execution (R)", lambda n: _m3(results[n][2], "ecart_brut_net_R"))
    add("M4 part du decile superieur",
        lambda n: _decile(results[n][3]["decile_superieur"]))
    return pd.DataFrame(rows)


def _decile(d: dict) -> str:
    part = d.get("part", float("nan"))
    if not np.isfinite(part):
        return "non applicable"
    return ">100%" if part > 1.0 else f"{part:.1%}"


def _p(m1: pd.DataFrame, col: str, val: str) -> str:
    r = m1[m1[col] == val]
    if r.empty:
        return "-"
    r = r.iloc[0]
    return f"{r['proportion']:.1%} [{r['ic95_bas']:.1%}, {r['ic95_haut']:.1%}] n={int(r['n'])}"


def _p2(m2: pd.DataFrame, cl: str) -> str:
    r = m2[m2["classe"] == cl]
    if r.empty or not np.isfinite(r.iloc[0]["proportion"]):
        return "-"
    r = r.iloc[0]
    return (f"{r['proportion']:.1%} [{r['ic95_bas']:.1%}, {r['ic95_haut']:.1%}] "
            f"n={int(r['n_resolues'])}")


def _m3(m3: pd.DataFrame, col: str) -> str:
    r = m3[m3["classe"] == "TOUTES"]
    if r.empty or col not in r.columns or not np.isfinite(r.iloc[0][col]):
        return "-"
    return f"{r.iloc[0][col]:+.4f}"


# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------
def make_plots(per_anchor: dict[str, pd.DataFrame], m5: pd.DataFrame) -> list[str]:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    made = []

    # 1. distribution des temps de touche
    fig, axes = plt.subplots(1, len(per_anchor), figsize=(6 * len(per_anchor), 4), squeeze=False)
    for ax, (name, s) in zip(axes[0], per_anchor.items()):
        for col, lab in (("t_touch_haute_min", "cible haute"), ("t_touch_basse_min", "cible basse")):
            v = s[col].dropna()
            if len(v):
                ax.hist(v, bins=30, alpha=0.55, label=f"{lab} (n={len(v)})")
        cut = (s["cutoff_utc"] - s["range_end_utc"]).dt.total_seconds().div(60).median()
        ax.axvline(cut, color="crimson", ls="--", lw=1.2,
                   label=f"cutoff MESURE 1 ({cut:.0f} min)")
        ax.set_title(f"{name} - temps de touche")
        ax.set_xlabel("minutes depuis la fin du range")
        ax.set_ylabel("sessions")
        ax.legend(fontsize=8)
    fig.tight_layout()
    p = PLOTS_DIR / "distribution_temps_de_touche.png"
    fig.savefig(p, dpi=130); plt.close(fig); made.append(str(p))

    # 2. distribution des R
    fig, ax = plt.subplots(figsize=(7, 4))
    for name, s in per_anchor.items():
        ax.hist(s["R_pts"].dropna(), bins=40, alpha=0.55, label=f"{name} (n={len(s)})")
    ax.set_title("Distribution de R")
    ax.set_xlabel("R (points)"); ax.set_ylabel("sessions"); ax.legend(fontsize=8)
    fig.tight_layout()
    p = PLOTS_DIR / "distribution_R.png"
    fig.savefig(p, dpi=130); plt.close(fig); made.append(str(p))

    # 3. spread moyen par tranche de 5 min sur la fenetre
    fig, ax = plt.subplots(figsize=(8, 4))
    for name, s in per_anchor.items():
        curve = _spread_curve(s, m5)
        if curve is not None and len(curve):
            ax.plot(curve.index, curve.to_numpy(), marker="o", ms=3, label=name)
    ax.set_title("Spread moyen par tranche de 5 min sur la fenetre")
    ax.set_xlabel("minutes depuis la fin du range"); ax.set_ylabel("spread moyen (points)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout()
    p = PLOTS_DIR / "spread_par_tranche_5min.png"
    fig.savefig(p, dpi=130); plt.close(fig); made.append(str(p))
    return made


def _spread_curve(s: pd.DataFrame, m5: pd.DataFrame) -> pd.Series | None:
    if s.empty:
        return None
    m5 = m5.set_index("ts").sort_index()
    acc: dict[int, list[float]] = {}
    for _, row in s.iterrows():
        t0, t1 = row["range_end_utc"], row["window_end_utc"]
        seg = m5.loc[(m5.index >= t0) & (m5.index < t1)]
        for ts, bar in seg.iterrows():
            off = int((ts - t0).total_seconds() // 60)
            acc.setdefault(off, []).append(float(bar["spread_mean_pts"]))
    if not acc:
        return None
    return pd.Series({k: float(np.mean(v)) for k, v in sorted(acc.items())})


def write_report(text: str) -> str:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(text, encoding="utf-8")
    return str(REPORT_MD)
