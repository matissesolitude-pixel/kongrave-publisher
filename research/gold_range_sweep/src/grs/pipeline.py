"""Enchainement complet : M5 -> sessions -> mesures -> rapport."""
from __future__ import annotations

import pandas as pd

from .aggregate import load_m5
from .constants import ANCHORS, EXCLUDED_CSV, MIN_SESSIONS, PROJECTION_FACTOR, SESSIONS_CSV
from .report import build_report, make_plots, write_report
from .sessions import build_sessions


def run_sessions(m5: pd.DataFrame | None = None, k: float = PROJECTION_FACTOR):
    """Construit les sessions des deux ancrages et les ramene au MEME echantillon."""
    m5 = load_m5() if m5 is None else m5

    built, excl_frames = {}, []
    for a in ANCHORS:
        s, e = build_sessions(m5, a, k=k)
        built[a.name] = s
        excl_frames.append(e)
        print(f"  {a.name}: {len(s)} sessions retenues, {len(e)} ecartees", flush=True)

    # Echantillon commun : une date n'est gardee que si les DEUX ancrages la retiennent.
    sets = [set(s["session_date"]) for s in built.values() if not s.empty]
    common = set.intersection(*sets) if sets else set()

    for name, s in built.items():
        if s.empty:
            continue
        dropped = s[~s["session_date"].isin(common)]
        if not dropped.empty:
            excl_frames.append(pd.DataFrame({
                "session_date": dropped["session_date"],
                "ancrage": name,
                "motif": "ecartee_sur_l_autre_ancrage",
                "detail": "retenue ici mais ecartee sur l'autre ancrage ; "
                          "supprimee pour garder un echantillon identique",
            }))
        built[name] = s[s["session_date"].isin(common)].reset_index(drop=True)

    excluded = (pd.concat(excl_frames, ignore_index=True)
                if excl_frames else pd.DataFrame(columns=["session_date", "ancrage", "motif", "detail"]))
    excluded = excluded.sort_values(["session_date", "ancrage"], kind="stable")

    EXCLUDED_CSV.parent.mkdir(parents=True, exist_ok=True)
    excluded.to_csv(EXCLUDED_CSV, index=False)

    allsess = pd.concat(built.values(), ignore_index=True).sort_values(
        ["session_date", "ancrage"], kind="stable")
    SESSIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    allsess.to_csv(SESSIONS_CSV, index=False)

    print(f"\nEchantillon commun aux deux ancrages : {len(common)} sessions")
    print(f"Sessions ecartees (toutes causes, tous ancrages) : {len(excluded)}")
    if len(common) < MIN_SESSIONS:
        print(f"\n!! {len(common)} sessions retenues < {MIN_SESSIONS} : "
              "il faut elargir la fenetre historique avant d'aller plus loin.")
    return built, excluded, m5


def run_report(built: dict, excluded: pd.DataFrame, m5: pd.DataFrame, note: str = ""):
    n_common = len(next(iter(built.values()))) if built else 0
    text = build_report(built, excluded, n_common, note=note)
    path = write_report(text)
    plots = make_plots(built, m5)
    print(f"rapport  -> {path}")
    for p in plots:
        print(f"graphique-> {p}")
    return path, plots


def class_breakdown(built: dict) -> pd.DataFrame:
    rows = []
    for name, s in built.items():
        vc = s["classe"].value_counts()
        for cl in ("SWEEP_HAUT", "SWEEP_BAS", "BREAKOUT_HAUT", "BREAKOUT_BAS", "NONE"):
            n = int(vc.get(cl, 0))
            rows.append({"ancrage": name, "classe": cl, "n": n,
                         "part": n / len(s) if len(s) else float("nan")})
        rows.append({"ancrage": name, "classe": "-- dont double_side",
                     "n": int(s["double_side"].sum()),
                     "part": s["double_side"].mean() if len(s) else float("nan")})
    return pd.DataFrame(rows)
