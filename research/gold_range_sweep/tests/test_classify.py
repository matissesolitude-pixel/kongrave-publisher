"""Tests de la classification et du trade mecanique, sur des cas fabriques a la main."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from grs.sessions import classify, build_trade, max_gap_minutes, market_closed

HIGH, LOW = 100.0, 90.0
R = 10.0


def bars(spec, t0="2025-01-16 00:15"):
    """spec = liste de (open, high, low, close). t_high/t_low places pour que
    l'extreme touche en premier soit celui atteint le plus tot dans la bougie."""
    ts = pd.date_range(t0, periods=len(spec), freq="5min", tz="UTC")
    rows = []
    for i, (o, h, l, c) in enumerate(spec):
        # l'extreme le plus proche de la cloture est atteint en dernier
        hi_last = abs(h - c) < abs(l - c)
        rows.append(dict(
            ts=ts[i], open=o, high=h, low=l, close=c, n_ticks=50,
            t_high=ts[i] + pd.Timedelta(minutes=3 if hi_last else 1),
            t_low=ts[i] + pd.Timedelta(minutes=1 if hi_last else 3),
            spread_mean_pts=30.0, spread_max_pts=60.0, spread_p95_pts=45.0,
            spread_close_pts=30.0, spread_mean_usd=0.30, close_ask=c + 0.30,
        ))
    return pd.DataFrame(rows)


def t(name, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got!r}" + ("" if ok else f" (attendu {want!r})"))
    return ok


def main():
    ok = True
    print("classification")
    # sweep haut : depassement puis cloture revenue sous le High dans la bougie meme
    ok &= t("sweep haut (retour bougie 1)",
            classify(bars([(99, 102, 98, 99)]), HIGH, LOW).klass, "SWEEP_HAUT")
    # retour a la 3e bougie -> encore un sweep
    ok &= t("sweep haut (retour bougie 3)",
            classify(bars([(99, 102, 99, 101), (101, 103, 100.5, 101.5), (101, 102, 98, 99)]),
                     HIGH, LOW).klass, "SWEEP_HAUT")
    # retour a la 4e bougie -> trop tard : 3 clotures au-dessus = breakout
    ok &= t("breakout haut (3 clotures au-dessus)",
            classify(bars([(99, 102, 99, 101), (101, 103, 100.5, 101.5),
                           (101, 104, 100.5, 102), (102, 102, 98, 99)]), HIGH, LOW).klass,
            "BREAKOUT_HAUT")
    ok &= t("sweep bas", classify(bars([(91, 92, 88, 91)]), HIGH, LOW).klass, "SWEEP_BAS")
    ok &= t("breakout bas",
            classify(bars([(91, 91, 88, 89), (89, 89.5, 87, 88), (88, 88.5, 86, 87)]),
                     HIGH, LOW).klass, "BREAKOUT_BAS")
    ok &= t("aucun franchissement",
            classify(bars([(95, 99, 91, 96), (96, 99.5, 90.5, 97)]), HIGH, LOW).klass, "NONE")

    # franchissement trop tardif pour etre confirme
    c = classify(bars([(95, 99, 91, 96), (96, 102, 95, 101)]), HIGH, LOW)
    ok &= t("franchissement tardif -> NONE", c.klass, "NONE")
    ok &= t("flag late_breach_unconfirmed", "late_breach_unconfirmed" in c.flags, True)

    # double cote : bas franchi en premier (bougie 1), haut ensuite (bougie 2)
    c = classify(bars([(95, 99, 88, 95), (95, 102, 94, 99)]), HIGH, LOW)
    ok &= t("double cote -> classe sur le 1er franchissement", c.klass, "SWEEP_BAS")
    ok &= t("flag double_side", "double_side" in c.flags, True)

    # les deux bornes franchies dans la MEME bougie : ordre tranche par t_high/t_low
    b = bars([(95, 102, 88, 95)])
    b.loc[0, "t_low"] = b.loc[0, "ts"] + pd.Timedelta(seconds=30)   # bas d'abord
    b.loc[0, "t_high"] = b.loc[0, "ts"] + pd.Timedelta(minutes=4)
    c = classify(b, HIGH, LOW)
    ok &= t("meme bougie -> bas en premier", c.breach_side, "BAS")
    ok &= t("flag same_bar_breach", "same_bar_breach" in c.flags, True)
    b.loc[0, "t_high"] = b.loc[0, "ts"] + pd.Timedelta(seconds=10)  # haut d'abord
    ok &= t("meme bougie -> haut en premier", classify(b, HIGH, LOW).breach_side, "HAUT")

    print("trade mecanique")
    # SWEEP_HAUT -> short, entree a la cloture du retour, stop a l'extreme du sweep
    w = bars([(99, 102, 98, 99)])
    post = pd.concat([w, bars([(99, 99, 79, 80)], t0="2025-01-16 00:20")], ignore_index=True)
    c = classify(w, HIGH, LOW)
    tr = build_trade(c, w, post, HIGH, LOW, R, 1.0)
    ok &= t("sweep haut -> short", tr["direction"], -1)
    ok &= t("entree = cloture du retour", tr["entry_price"], 99.0)
    ok &= t("stop = extreme du sweep", tr["stop"], 102.0)
    ok &= t("cible = Low - 1R", tr["target"], 80.0)
    ok &= t("cible atteinte", tr["exit_reason"], "cible")
    ok &= t("pnl brut R", round(tr["pnl_gross_R"], 4), 1.9)
    # cout = 1 spread de 30 pts = 0.30 USD sur R=10 -> 0.03 R
    ok &= t("pnl net R", round(tr["pnl_net_R"], 4), 1.87)
    ok &= t("mfe R", round(tr["mfe_R"], 4), 2.0)

    # BREAKOUT_HAUT -> long au retest de la borne, stop 0.1R sous la borne
    w = bars([(99, 102, 99, 101), (101, 103, 100.5, 101.5), (101, 104, 100.5, 102)])
    post = pd.concat([w, bars([(102, 102.5, 99.5, 101)], t0="2025-01-16 00:30"),
                      bars([(101, 111, 100.5, 110)], t0="2025-01-16 00:35")], ignore_index=True)
    c = classify(w, HIGH, LOW)
    tr = build_trade(c, w, post, HIGH, LOW, R, 1.0)
    ok &= t("breakout haut -> long", tr["direction"], 1)
    ok &= t("entree sur la borne", tr["entry_price"], 100.0)
    ok &= t("stop 0.1R sous la borne", round(tr["stop"], 6), 99.0)
    ok &= t("cible = High + 1R", tr["target"], 110.0)
    ok &= t("cible atteinte", tr["exit_reason"], "cible")

    # breakout sans retest
    post2 = pd.concat([w, bars([(102, 108, 101.5, 107)], t0="2025-01-16 00:30")], ignore_index=True)
    ok &= t("breakout sans retest", build_trade(c, w, post2, HIGH, LOW, R, 1.0)["trade_flags"],
            "no_retest")

    print("regles d'exclusion")
    grid = pd.DatetimeIndex(pd.date_range("2025-01-15 19:45", periods=54, freq="5min", tz="UTC"))
    t0 = pd.Timestamp("2025-01-15 19:45", tz="UTC"); t1 = pd.Timestamp("2025-01-16 00:15", tz="UTC")
    ok &= t("grille complete -> 0 trou", max_gap_minutes(grid, t0, t1), 0.0)
    ok &= t("3 barres manquantes -> 15 min", max_gap_minutes(grid.delete([10, 11, 12]), t0, t1), 15.0)
    ok &= t("4 barres manquantes -> 20 min", max_gap_minutes(grid.delete([10, 11, 12, 13]), t0, t1), 20.0)
    ok &= t("samedi ferme", market_closed(pd.Timestamp("2025-01-18 12:00", tz="UTC")), True)
    ok &= t("vendredi 22h ferme", market_closed(pd.Timestamp("2025-01-17 22:00", tz="UTC")), True)
    ok &= t("vendredi 20h ouvert", market_closed(pd.Timestamp("2025-01-17 20:00", tz="UTC")), False)
    ok &= t("dimanche 23h ouvert", market_closed(pd.Timestamp("2025-01-19 23:00", tz="UTC")), False)

    print("\n" + ("TOUS LES TESTS PASSENT" if ok else "ECHEC"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
