"""Agregation tick -> M5 alignee sur l'horloge UTC.

L'OHLC est construit sur le BID. Le spread est une colonne de premier plan :
spread_mean / spread_max / spread_p95 en points, plus le spread horodate de la
derniere transaction de la bougie (spread_close), qui sert de cout d'execution
pour toute entree "a la cloture".

Les bougies sont posees sur la grille UTC (floor 5 min sur l'horodatage UTC du
tick), jamais sur l'horloge serveur du fournisseur.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import BAR_MINUTES, M5_DIR, POINT, RAW_DIR

M5_COLUMNS = [
    "ts", "open", "high", "low", "close", "n_ticks",
    "t_high", "t_low",
    "spread_mean_pts", "spread_max_pts", "spread_p95_pts", "spread_close_pts",
    "spread_mean_usd", "close_ask",
]


def aggregate_ticks(ticks: pd.DataFrame) -> pd.DataFrame:
    """ticks(ts, bid, ask, ...) -> bougies M5."""
    if ticks.empty:
        return pd.DataFrame(columns=M5_COLUMNS)

    df = ticks.sort_values("ts", kind="stable").reset_index(drop=True)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    # Grille UTC stricte.
    df["bar"] = df["ts"].dt.floor(f"{BAR_MINUTES}min")
    df["spread_pts"] = (df["ask"] - df["bid"]) / POINT

    g = df.groupby("bar", sort=True)
    out = g.agg(
        open=("bid", "first"),
        high=("bid", "max"),
        low=("bid", "min"),
        close=("bid", "last"),
        n_ticks=("bid", "size"),
        spread_mean_pts=("spread_pts", "mean"),
        spread_max_pts=("spread_pts", "max"),
        spread_close_pts=("spread_pts", "last"),
        close_ask=("ask", "last"),
    )
    out["spread_p95_pts"] = g["spread_pts"].quantile(0.95)
    out["spread_mean_usd"] = out["spread_mean_pts"] * POINT

    # Horodatage exact des extremes : permet d'ordonner deux franchissements
    # survenus dans la meme bougie sans aucune heuristique.
    idx_hi = g["bid"].idxmax()
    idx_lo = g["bid"].idxmin()
    out["t_high"] = df["ts"].to_numpy()[idx_hi.to_numpy()]
    out["t_low"] = df["ts"].to_numpy()[idx_lo.to_numpy()]

    out = out.reset_index().rename(columns={"bar": "ts"})
    return out[M5_COLUMNS]


def aggregate_all(force: bool = False) -> pd.DataFrame:
    """Agrege chaque partition mensuelle brute vers data/m5/."""
    M5_DIR.mkdir(parents=True, exist_ok=True)
    raws = sorted(p for p in RAW_DIR.glob("*.parquet"))
    if not raws:
        raise FileNotFoundError(f"aucune partition brute dans {RAW_DIR}")
    frames = []
    for p in raws:
        dst = M5_DIR / p.name
        if dst.exists() and not force:
            m5 = pd.read_parquet(dst)
        else:
            m5 = aggregate_ticks(pd.read_parquet(p))
            m5.to_parquet(dst, index=False, compression="zstd")
        print(f"  {p.stem}: {len(m5):,} bougies M5", flush=True)
        frames.append(m5)
    allm5 = pd.concat(frames, ignore_index=True).sort_values("ts", kind="stable")
    allm5 = allm5.drop_duplicates("ts", keep="last").reset_index(drop=True)
    print(f"TOTAL M5 : {len(allm5):,} bougies "
          f"({allm5['ts'].min()} -> {allm5['ts'].max()})", flush=True)
    return allm5


def load_m5() -> pd.DataFrame:
    files = sorted(M5_DIR.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"aucune bougie M5 dans {M5_DIR} - lancer l'agregation")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts", kind="stable").drop_duplicates("ts", keep="last")
    return df.reset_index(drop=True)
