"""Telechargement des ticks Dukascopy (bid ET ask) vers Parquet mensuel.

Format Dukascopy .bi5 :
  URL   datafeed.dukascopy.com/datafeed/{SYMBOL}/{YYYY}/{MM-1}/{DD}/{HH}h_ticks.bi5
        (mois indexe a partir de 0, heure en UTC)
  corps LZMA "alone", puis des enregistrements de 20 octets big-endian :
        >I ms depuis le debut de l'heure
        >I ask (entier)
        >I bid (entier)
        >f volume ask
        >f volume bid

Une reponse vide ou un 404 = pas de tick sur cette heure. C'est normal (nuit,
week-end, fin de session US sur l'or). On le journalise, on n'interpole jamais.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import io
import json
import lzma
import struct
import sys
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
import requests

from .constants import (
    DECIMAL_FACTOR,
    DUKASCOPY_URL,
    MANIFEST_DIR,
    PRICE_SANITY_RANGE,
    RAW_DIR,
    SYMBOL,
)

TICK_STRUCT = struct.Struct(">IIIff")
TICK_SIZE = TICK_STRUCT.size  # 20


class AskMissingError(RuntimeError):
    """Le flux ne porte pas d'ask exploitable -> on s'arrete, on ne substitue rien."""


class PriceScaleError(RuntimeError):
    """Le prix decode est hors plage plausible -> DECIMAL_FACTOR suspect."""


@dataclass
class HourResult:
    hour_utc: dt.datetime
    status: str          # ok | empty | http_404 | http_error | error
    n_ticks: int
    detail: str = ""


def decode_bi5(payload: bytes, hour_utc: dt.datetime) -> pd.DataFrame:
    """Decode un .bi5 en DataFrame(ts, bid, ask, bid_vol, ask_vol)."""
    if not payload:
        return _empty_ticks()

    try:
        raw = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(payload)
    except lzma.LZMAError:
        try:
            raw = lzma.decompress(payload, format=lzma.FORMAT_AUTO)
        except lzma.LZMAError:
            # Certaines heures vides sont servies non compressees.
            raw = payload

    if len(raw) == 0:
        return _empty_ticks()
    if len(raw) % TICK_SIZE != 0:
        raise ValueError(
            f"taille decompressee {len(raw)} non multiple de {TICK_SIZE} "
            f"pour {hour_utc:%Y-%m-%d %H}h"
        )

    n = len(raw) // TICK_SIZE
    arr = np.frombuffer(raw, dtype=np.dtype([
        ("ms", ">u4"), ("ask", ">u4"), ("bid", ">u4"),
        ("ask_vol", ">f4"), ("bid_vol", ">f4"),
    ]), count=n)

    base = pd.Timestamp(hour_utc).tz_localize("UTC") if hour_utc.tzinfo is None \
        else pd.Timestamp(hour_utc).tz_convert("UTC")

    df = pd.DataFrame({
        "ts": base + pd.to_timedelta(arr["ms"].astype("int64"), unit="ms"),
        "bid": arr["bid"].astype("float64") / DECIMAL_FACTOR,
        "ask": arr["ask"].astype("float64") / DECIMAL_FACTOR,
        "bid_vol": arr["bid_vol"].astype("float64"),
        "ask_vol": arr["ask_vol"].astype("float64"),
    })
    return df


def _empty_ticks() -> pd.DataFrame:
    return pd.DataFrame({
        "ts": pd.Series([], dtype="datetime64[ms, UTC]"),
        "bid": pd.Series([], dtype="float64"),
        "ask": pd.Series([], dtype="float64"),
        "bid_vol": pd.Series([], dtype="float64"),
        "ask_vol": pd.Series([], dtype="float64"),
    })


def validate_ticks(df: pd.DataFrame) -> None:
    """Garde-fous durs : ask reellement present, echelle de prix plausible."""
    if df.empty:
        return
    med = float(df["bid"].median())
    lo, hi = PRICE_SANITY_RANGE
    if not (lo <= med <= hi):
        raise PriceScaleError(
            f"prix bid median decode = {med:.4f}, hors de [{lo}, {hi}]. "
            f"DECIMAL_FACTOR={DECIMAL_FACTOR} est probablement faux. "
            "Aucune correction automatique n'est appliquee."
        )
    if not np.isfinite(df["ask"]).any() or (df["ask"] <= 0).all():
        raise AskMissingError("colonne ask absente ou nulle sur tout l'echantillon")
    spread = df["ask"] - df["bid"]
    if (spread <= 0).mean() > 0.5:
        raise AskMissingError(
            f"spread ask-bid <= 0 sur {(spread <= 0).mean():.1%} des ticks : "
            "le flux ne porte pas d'ask exploitable"
        )


def fetch_hour(session: requests.Session, hour_utc: dt.datetime,
               retries: int = 4, timeout: int = 30) -> tuple[HourResult, pd.DataFrame]:
    url = DUKASCOPY_URL.format(
        symbol=SYMBOL, year=hour_utc.year, month0=hour_utc.month - 1,
        day=hour_utc.day, hour=hour_utc.hour,
    )
    delay = 2.0
    last = ""
    for attempt in range(retries + 1):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 404:
                return HourResult(hour_utc, "http_404", 0), _empty_ticks()
            if r.status_code != 200:
                last = f"http {r.status_code}"
                raise requests.HTTPError(last)
            df = decode_bi5(r.content, hour_utc)
            if df.empty:
                return HourResult(hour_utc, "empty", 0), df
            return HourResult(hour_utc, "ok", len(df)), df
        except Exception as exc:  # reseau, decodage
            last = f"{type(exc).__name__}: {exc}"
            if attempt >= retries:
                break
            time.sleep(delay)
            delay *= 2
    return HourResult(hour_utc, "error", 0, last), _empty_ticks()


def month_hours(year: int, month: int, start: dt.datetime, end: dt.datetime) -> list[dt.datetime]:
    first = dt.datetime(year, month, 1)
    nxt = dt.datetime(year + (month == 12), (month % 12) + 1, 1)
    hours, cur = [], first
    while cur < nxt:
        if start <= cur < end:
            hours.append(cur)
        cur += dt.timedelta(hours=1)
    return hours


def download_month(year: int, month: int, start: dt.datetime, end: dt.datetime,
                   workers: int = 12, force: bool = False) -> dict:
    """Telecharge un mois, ecrit data/raw/{YYYY-MM}.parquet + son manifeste."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"{year:04d}-{month:02d}"
    pq = RAW_DIR / f"{tag}.parquet"
    mf = MANIFEST_DIR / f"{tag}.json"

    hours = month_hours(year, month, start, end)
    if not hours:
        return {"month": tag, "hours": 0, "ticks": 0, "skipped": True}

    if pq.exists() and mf.exists() and not force:
        man = json.loads(mf.read_text())
        if man.get("complete") and man.get("n_hours") == len(hours):
            print(f"  {tag} deja complet ({man['n_ticks']:,} ticks) - saute", flush=True)
            return man

    frames, results = [], []
    with requests.Session() as sess:
        sess.headers["User-Agent"] = "grs-research/1.0"
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(fetch_hour, sess, h): h for h in hours}
            done = 0
            for fut in cf.as_completed(futs):
                res, df = fut.result()
                results.append(res)
                if not df.empty:
                    frames.append(df)
                done += 1
                if done % 100 == 0 or done == len(hours):
                    print(f"  {tag} {done}/{len(hours)} heures", flush=True)

    if frames:
        ticks = pd.concat(frames, ignore_index=True).sort_values("ts", kind="stable")
        ticks = ticks.reset_index(drop=True)
        validate_ticks(ticks)
        ticks.to_parquet(pq, index=False, compression="zstd")
    else:
        ticks = _empty_ticks()
        ticks.to_parquet(pq, index=False, compression="zstd")

    errs = [r for r in results if r.status == "error"]
    man = {
        "month": tag,
        "n_hours": len(hours),
        "n_ticks": int(len(ticks)),
        "complete": len(errs) == 0,
        "hours": {r.hour_utc.strftime("%Y-%m-%dT%H"): {"status": r.status, "n": r.n_ticks}
                  for r in sorted(results, key=lambda r: r.hour_utc)},
        "errors": [{"hour": r.hour_utc.strftime("%Y-%m-%dT%H"), "detail": r.detail} for r in errs],
    }
    mf.write_text(json.dumps(man, indent=1))
    print(f"  {tag} -> {len(ticks):,} ticks, {len(errs)} heures en erreur", flush=True)
    return man


def download_range(months: int, end: dt.datetime | None = None,
                   workers: int = 12, force: bool = False) -> list[dict]:
    end = end or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    start = (end - pd.DateOffset(months=months)).to_pydatetime()
    print(f"Fenetre : {start:%Y-%m-%d %H}h -> {end:%Y-%m-%d %H}h UTC ({months} mois)", flush=True)
    out, cur = [], dt.datetime(start.year, start.month, 1)
    while cur < end:
        out.append(download_month(cur.year, cur.month, start, end, workers=workers, force=force))
        cur = dt.datetime(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
    total = sum(m.get("n_ticks", 0) for m in out)
    print(f"TOTAL : {total:,} ticks sur {len(out)} partitions mensuelles", flush=True)
    return out
