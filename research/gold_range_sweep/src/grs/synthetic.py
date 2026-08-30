"""Generateur de ticks synthetiques -- UNIQUEMENT pour l'auto-test du pipeline.

Ces donnees sont un bruit calibre, pas un marche. Tout resultat produit a partir
d'elles est un test de plomberie et n'a AUCUNE signification de marche.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from .constants import DECIMAL_FACTOR, POINT
from .sessions import market_closed

TICK_SECONDS = 5
SESSION_START_H = 18   # UTC
SESSION_HOURS = 10     # 18:00 -> 04:00


def make_ticks(n_days: int = 200, end: dt.date | None = None, seed: int = 7,
               start_price: float = 3300.0, vol_scale: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = end or dt.date(2025, 7, 31)
    days = [end - dt.timedelta(days=i) for i in range(n_days)][::-1]

    price = start_price
    frames = []
    for d in days:
        t0 = pd.Timestamp(dt.datetime.combine(d, dt.time(SESSION_START_H)), tz="UTC")
        n = SESSION_HOURS * 3600 // TICK_SECONDS
        ts = t0 + pd.to_timedelta(np.arange(n) * TICK_SECONDS, unit="s")
        keep = np.array([not market_closed(t) for t in ts])
        if keep.sum() < 100:
            continue
        ts = ts[keep]

        # marche aleatoire, volatilite plus forte a l'ouverture asiatique
        hour = ts.hour.to_numpy()
        vol = np.where((hour >= 23) | (hour < 2), 0.055, 0.035) * vol_scale
        steps = rng.normal(0.0, 1.0, len(ts)) * vol
        bid = price + np.cumsum(steps)
        price = float(bid[-1])

        # spread : large en fin de session US et sur la bascule de jour, serre ensuite
        base = np.where((hour >= 20) & (hour < 23), 45.0, 28.0)
        base = np.where((hour >= 0) & (hour < 1), 55.0, base)
        spread_pts = np.clip(base + rng.normal(0, 6.0, len(ts)), 8.0, 400.0)
        ask = bid + spread_pts * POINT

        # on repasse par la quantification entiere de Dukascopy
        bid = np.round(bid * DECIMAL_FACTOR) / DECIMAL_FACTOR
        ask = np.round(ask * DECIMAL_FACTOR) / DECIMAL_FACTOR

        frames.append(pd.DataFrame({
            "ts": ts, "bid": bid, "ask": ask,
            "bid_vol": rng.random(len(ts)), "ask_vol": rng.random(len(ts)),
        }))

    return pd.concat(frames, ignore_index=True).sort_values("ts").reset_index(drop=True)


def write_raw(ticks: pd.DataFrame, raw_dir) -> list:
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for (y, m), part in ticks.groupby([ticks["ts"].dt.year, ticks["ts"].dt.month]):
        p = raw_dir / f"{y:04d}-{m:02d}.parquet"
        part.reset_index(drop=True).to_parquet(p, index=False, compression="zstd")
        out.append(p)
    return out
