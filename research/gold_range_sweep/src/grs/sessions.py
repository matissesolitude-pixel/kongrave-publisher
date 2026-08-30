"""Construction des sessions, exclusions, classification, trades mecaniques."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import holidays
import numpy as np
import pandas as pd

from .constants import (
    ANCHORS,
    BAR_MINUTES,
    BREAKOUT_CONFIRM_BARS,
    BREAKOUT_STOP_BUFFER_R,
    COND_RACE_START,
    HOLIDAY_COUNTRIES,
    MAX_RANGE_GAP_MIN,
    POINT,
    PROJECTION_FACTOR,
    ROUND_TURN_SPREADS,
    SWEEP_MAX_BARS,
    WEEKLY_CLOSE,
    WEEKLY_OPEN,
    Anchor,
)

FAR_FUTURE = pd.Timestamp("2262-01-01", tz="UTC")


# ---------------------------------------------------------------------------
# Bornes temporelles
# ---------------------------------------------------------------------------
def anchor_bounds(anchor: Anchor, session_date: dt.date) -> dict[str, pd.Timestamp]:
    """Bornes UTC d'une session, calculees dans le fuseau de l'ancrage."""
    out = {}
    for key in ("range_start", "range_end", "window_end", "cutoff", "exit"):
        doff, hh, mm = getattr(anchor, key)
        local = pd.Timestamp(
            dt.datetime.combine(session_date + dt.timedelta(days=doff), dt.time(hh, mm)),
            tz=anchor.tz,
        )
        out[key] = local.tz_convert("UTC")
    return out


def market_closed(ts: pd.Timestamp) -> bool:
    """Fermeture hebdomadaire du spot or."""
    wd, t = ts.weekday(), (ts.hour, ts.minute)
    cw, ch, cm = WEEKLY_CLOSE
    ow, oh, om = WEEKLY_OPEN
    if wd == cw and t >= (ch, cm):
        return True
    if wd == 5:
        return True
    if wd == ow and t < (oh, om):
        return True
    return False


def touches_weekend(t0: pd.Timestamp, t1: pd.Timestamp) -> bool:
    """Vrai si [t0, t1) chevauche la fermeture hebdomadaire (pas de 5 min)."""
    cur = t0
    step = pd.Timedelta(minutes=BAR_MINUTES)
    while cur < t1:
        if market_closed(cur):
            return True
        cur += step
    return market_closed(t1 - step)


def max_gap_minutes(bars_ts: pd.DatetimeIndex, t0: pd.Timestamp, t1: pd.Timestamp) -> float:
    """Plus long trou (en minutes) sur la grille M5 de [t0, t1)."""
    grid = pd.date_range(t0, t1 - pd.Timedelta(minutes=BAR_MINUTES),
                         freq=f"{BAR_MINUTES}min", tz="UTC")
    if len(grid) == 0:
        return 0.0
    present = grid.isin(bars_ts)
    best = run = 0
    for ok in present:
        run = 0 if ok else run + 1
        best = max(best, run)
    return best * BAR_MINUTES


# ---------------------------------------------------------------------------
# Calendrier des exclusions
# ---------------------------------------------------------------------------
def build_holiday_calendars(years: list[int]) -> dict[str, object]:
    return {c: holidays.country_holidays(c, years=years) for c in HOLIDAY_COUNTRIES}


def holiday_reason(cals: dict, dates: list[dt.date]) -> str | None:
    for country, cal in cals.items():
        for d in dates:
            if d in cal:
                return f"ferie_{country}:{cal.get(d)}|{d}"
    return None


# ---------------------------------------------------------------------------
# Recherche de touche
# ---------------------------------------------------------------------------
def _first_touch_up(bars: pd.DataFrame, level: float) -> pd.Timestamp | None:
    hit = bars.index[bars["high"].to_numpy() >= level]
    if len(hit) == 0:
        return None
    return bars.loc[hit[0], "t_high"]


def _first_touch_dn(bars: pd.DataFrame, level: float) -> pd.Timestamp | None:
    hit = bars.index[bars["low"].to_numpy() <= level]
    if len(hit) == 0:
        return None
    return bars.loc[hit[0], "t_low"]


def _mins(ts: pd.Timestamp | None, ref: pd.Timestamp) -> float:
    return float("nan") if ts is None else (ts - ref).total_seconds() / 60.0


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
@dataclass
class Classification:
    klass: str = "NONE"
    breach_side: str = ""
    breach_idx: int = -1
    breach_time: pd.Timestamp | None = None
    return_idx: int = -1
    confirm_idx: int = -1
    sweep_extreme: float = float("nan")
    flags: list[str] = field(default_factory=list)


def classify(window: pd.DataFrame, high: float, low: float) -> Classification:
    """Classification evaluee a la fin de la fenetre."""
    c = Classification()
    if window.empty:
        return c

    w = window.reset_index(drop=True)
    up = np.flatnonzero(w["high"].to_numpy() > high)
    dn = np.flatnonzero(w["low"].to_numpy() < low)

    if len(up) == 0 and len(dn) == 0:
        return c
    if len(up) and len(dn):
        c.flags.append("double_side")

    # Premier franchissement, ordonne a la milliseconde grace a t_high / t_low.
    t_up = w.loc[up[0], "t_high"] if len(up) else FAR_FUTURE
    t_dn = w.loc[dn[0], "t_low"] if len(dn) else FAR_FUTURE
    if len(up) and len(dn) and up[0] == dn[0]:
        c.flags.append("same_bar_breach")

    if t_up <= t_dn:
        c.breach_side, c.breach_idx, c.breach_time = "HAUT", int(up[0]), t_up
    else:
        c.breach_side, c.breach_idx, c.breach_time = "BAS", int(dn[0]), t_dn

    b = c.breach_idx
    span = w.iloc[b:b + SWEEP_MAX_BARS]
    if c.breach_side == "HAUT":
        back = np.flatnonzero(span["close"].to_numpy() < high)
        c.sweep_extreme = float(span["high"].max())
    else:
        back = np.flatnonzero(span["close"].to_numpy() > low)
        c.sweep_extreme = float(span["low"].min())

    if len(back):
        c.klass = f"SWEEP_{c.breach_side}"
        c.return_idx = b + int(back[0])
        c.sweep_extreme = (
            float(w.iloc[b:c.return_idx + 1]["high"].max()) if c.breach_side == "HAUT"
            else float(w.iloc[b:c.return_idx + 1]["low"].min())
        )
        return c

    conf = w.iloc[b:b + BREAKOUT_CONFIRM_BARS]
    if len(conf) == BREAKOUT_CONFIRM_BARS:
        beyond = (conf["close"].to_numpy() > high) if c.breach_side == "HAUT" \
            else (conf["close"].to_numpy() < low)
        if beyond.all():
            c.klass = f"BREAKOUT_{c.breach_side}"
            c.confirm_idx = b + BREAKOUT_CONFIRM_BARS - 1
            return c

    if b + max(SWEEP_MAX_BARS, BREAKOUT_CONFIRM_BARS) > len(w):
        c.flags.append("late_breach_unconfirmed")
    return c


# ---------------------------------------------------------------------------
# Trade mecanique (MESURE 3)
# ---------------------------------------------------------------------------
def build_trade(cls: Classification, window: pd.DataFrame, post: pd.DataFrame,
                high: float, low: float, R: float, k: float) -> dict:
    """Entree/stop/cible mecaniques, puis parcours barre a barre jusqu'a la sortie.

    `post` = bougies de la fenetre + apres, jusqu'a l'heure de sortie.
    """
    out = {
        "entry_time": pd.NaT, "entry_price": np.nan, "direction": 0,
        "stop": np.nan, "target": np.nan, "exit_reason": "",
        "exit_time": pd.NaT, "exit_price": np.nan,
        "spread_entry_pts": np.nan, "spread_entry_usd": np.nan,
        "mfe_R": np.nan, "mae_R": np.nan, "pnl_gross_R": np.nan, "pnl_net_R": np.nan,
        "trade_flags": "",
    }
    if cls.klass == "NONE" or post.empty or not np.isfinite(R) or R <= 0:
        return out

    p = post.reset_index(drop=True)
    w_len = len(window)
    flags: list[str] = []

    if cls.klass.startswith("SWEEP"):
        i = cls.return_idx
        if i < 0 or i >= len(p):
            return out
        entry_i = i
        close_entry = True
        out["entry_time"] = p.loc[i, "ts"]
        out["entry_price"] = float(p.loc[i, "close"])
        # Entree a la cloture -> cout = spread du dernier tick de la bougie.
        out["spread_entry_pts"] = float(p.loc[i, "spread_close_pts"])
        if cls.breach_side == "HAUT":
            out["direction"] = -1
            out["stop"] = cls.sweep_extreme
            out["target"] = low - k * R
        else:
            out["direction"] = 1
            out["stop"] = cls.sweep_extreme
            out["target"] = high + k * R
    else:  # BREAKOUT : entree au premier retest de la borne franchie
        c_i = cls.confirm_idx
        if c_i < 0:
            return out
        bound = high if cls.breach_side == "HAUT" else low
        found = -1
        for j in range(c_i + 1, len(p)):
            if cls.breach_side == "HAUT" and p.loc[j, "low"] <= bound:
                found = j
                break
            if cls.breach_side == "BAS" and p.loc[j, "high"] >= bound:
                found = j
                break
        if found < 0:
            out["trade_flags"] = "no_retest"
            return out
        entry_i = found
        close_entry = False
        out["entry_time"] = p.loc[found, "ts"]
        out["entry_price"] = float(bound)
        # Entree intra-bougie (limite sur la borne) -> spread moyen de la bougie.
        out["spread_entry_pts"] = float(p.loc[found, "spread_mean_pts"])
        if found >= w_len:
            flags.append("retest_hors_fenetre")
        if cls.breach_side == "HAUT":
            out["direction"] = 1
            out["stop"] = bound - BREAKOUT_STOP_BUFFER_R * R
            out["target"] = bound + k * R
        else:
            out["direction"] = -1
            out["stop"] = bound + BREAKOUT_STOP_BUFFER_R * R
            out["target"] = bound - k * R

    d = out["direction"]
    entry, stop, target = out["entry_price"], out["stop"], out["target"]
    out["spread_entry_usd"] = out["spread_entry_pts"] * POINT

    if (d == 1 and (stop >= entry or target <= entry)) or \
       (d == -1 and (stop <= entry or target >= entry)):
        flags.append("niveaux_degeneres")
        out["trade_flags"] = ",".join(flags)
        return out

    # Une entree A LA CLOTURE ne peut pas subir les excursions de sa propre
    # bougie : le parcours demarre a la bougie suivante. Une entree en limite
    # sur la borne (breakout) reste exposee au reste de sa bougie.
    walk_start = entry_i + 1 if close_entry else entry_i
    if walk_start >= len(p):
        flags.append("aucune_bougie_apres_entree")
        out["trade_flags"] = ",".join(flags)
        return out

    mfe = mae = 0.0
    for j in range(walk_start, len(p)):
        bar = p.loc[j]
        fav = (bar["high"] - entry) if d == 1 else (entry - bar["low"])
        adv = (entry - bar["low"]) if d == 1 else (bar["high"] - entry)
        mfe, mae = max(mfe, float(fav)), max(mae, float(adv))

        hit_t = (bar["high"] >= target) if d == 1 else (bar["low"] <= target)
        hit_s = (bar["low"] <= stop) if d == 1 else (bar["high"] >= stop)
        if hit_t and hit_s:
            # Ordre exact grace aux horodatages des extremes.
            t_t = bar["t_high"] if d == 1 else bar["t_low"]
            t_s = bar["t_low"] if d == 1 else bar["t_high"]
            first_target = t_t < t_s
            flags.append("stop_et_cible_meme_bougie")
        elif hit_t:
            first_target = True
        elif hit_s:
            first_target = False
        else:
            continue

        out["exit_time"] = bar["t_high"] if (first_target == (d == 1)) else bar["t_low"]
        out["exit_price"] = target if first_target else stop
        out["exit_reason"] = "cible" if first_target else "stop"
        break
    else:
        last = p.iloc[-1]
        out["exit_time"] = last["ts"]
        out["exit_price"] = float(last["close"])
        out["exit_reason"] = "sortie_horaire"

    gross = d * (out["exit_price"] - entry) / R
    cost = ROUND_TURN_SPREADS * out["spread_entry_usd"] / R
    out["mfe_R"], out["mae_R"] = mfe / R, mae / R
    out["pnl_gross_R"], out["pnl_net_R"] = gross, gross - cost
    out["trade_flags"] = ",".join(flags)
    return out


# ---------------------------------------------------------------------------
# Construction des sessions
# ---------------------------------------------------------------------------
def build_sessions(m5: pd.DataFrame, anchor: Anchor,
                   k: float = PROJECTION_FACTOR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renvoie (sessions retenues, sessions exclues) pour un ancrage."""
    m5 = m5.sort_values("ts", kind="stable").reset_index(drop=True)
    ts = pd.DatetimeIndex(m5["ts"])
    local_dates = ts.tz_convert(anchor.tz).date
    first, last = min(local_dates), max(local_dates)
    cals = build_holiday_calendars(list(range(first.year, last.year + 2)))

    rows, excl = [], []
    day = first
    while day <= last:
        b = anchor_bounds(anchor, day)
        rej = _session_rejection(m5, ts, b, cals, day, anchor)
        if rej:
            excl.append({"session_date": day, "ancrage": anchor.name,
                         "motif": rej[0], "detail": rej[1]})
            day += dt.timedelta(days=1)
            continue
        rows.append(_session_row(m5, ts, b, day, anchor, k))
        day += dt.timedelta(days=1)

    sessions = pd.DataFrame(rows)
    excluded = pd.DataFrame(excl, columns=["session_date", "ancrage", "motif", "detail"])
    return sessions, excluded


def _slice(m5: pd.DataFrame, ts: pd.DatetimeIndex,
           t0: pd.Timestamp, t1: pd.Timestamp) -> pd.DataFrame:
    lo, hi = ts.searchsorted(t0, "left"), ts.searchsorted(t1, "left")
    return m5.iloc[lo:hi]


def _session_rejection(m5, ts, b, cals, day, anchor) -> tuple[str, str] | None:
    if touches_weekend(b["range_start"], b["exit"]):
        return ("week_end", f"{b['range_start']:%a %H:%M} -> {b['exit']:%a %H:%M} UTC")

    dates = sorted({b["range_start"].tz_convert(anchor.tz).date(),
                    b["window_end"].tz_convert(anchor.tz).date(),
                    b["exit"].tz_convert(anchor.tz).date()})
    hol = holiday_reason(cals, dates)
    if hol:
        return ("jour_ferie", hol)

    rng = _slice(m5, ts, b["range_start"], b["range_end"])
    if rng.empty:
        return ("range_sans_donnee", f"0 bougie entre {b['range_start']} et {b['range_end']}")

    gap = max_gap_minutes(pd.DatetimeIndex(rng["ts"]), b["range_start"], b["range_end"])
    if gap > MAX_RANGE_GAP_MIN:
        return ("trou_range", f"{gap:.0f} min > {MAX_RANGE_GAP_MIN} min")

    if _slice(m5, ts, b["range_end"], b["window_end"]).empty:
        return ("fenetre_sans_donnee", f"0 bougie entre {b['range_end']} et {b['window_end']}")

    hi, lo = float(rng["high"].max()), float(rng["low"].min())
    if not np.isfinite(hi - lo) or (hi - lo) <= 0:
        return ("range_nul", f"High={hi} Low={lo}")
    return None


def _session_row(m5, ts, b, day, anchor, k) -> dict:
    rng = _slice(m5, ts, b["range_start"], b["range_end"])
    win = _slice(m5, ts, b["range_end"], b["window_end"])
    to_cut = _slice(m5, ts, b["range_end"], b["cutoff"])
    post = _slice(m5, ts, b["range_end"], b["exit"])

    high, low = float(rng["high"].max()), float(rng["low"].min())
    R = high - low
    tgt_hi, tgt_lo = high + k * R, low - k * R

    cls = classify(win, high, low)

    # MESURE 1 : touche avant le cutoff.
    t_hi_cut = _first_touch_up(to_cut, tgt_hi)
    t_lo_cut = _first_touch_dn(to_cut, tgt_lo)
    # Horizon complet, jusqu'a la sortie.
    t_hi_all = _first_touch_up(post, tgt_hi)
    t_lo_all = _first_touch_dn(post, tgt_lo)

    # MESURE 2 : course entre les deux cibles a partir du point de decision.
    race0 = b["window_end"] if COND_RACE_START == "window_end" else b["range_end"]
    race = _slice(m5, ts, race0, b["exit"])
    r_hi = _first_touch_up(race, tgt_hi)
    r_lo = _first_touch_dn(race, tgt_lo)

    trade = build_trade(cls, win, post, high, low, R, k)

    row = {
        "session_date": day,
        "ancrage": anchor.name,
        "range_start_utc": b["range_start"], "range_end_utc": b["range_end"],
        "window_end_utc": b["window_end"], "cutoff_utc": b["cutoff"], "exit_utc": b["exit"],
        "weekday": b["range_start"].tz_convert(anchor.tz).strftime("%a"),
        "quarter": f"{day.year}Q{(day.month - 1) // 3 + 1}",
        "High": high, "Low": low, "R": R, "R_pts": R / POINT,
        "cible_haute": tgt_hi, "cible_basse": tgt_lo,
        "classe": cls.klass,
        "flags": ",".join(cls.flags),
        "double_side": "double_side" in cls.flags,
        "n_bars_range": len(rng), "n_bars_window": len(win),
        "window_max_gap_min": max_gap_minutes(pd.DatetimeIndex(win["ts"]),
                                             b["range_end"], b["window_end"]),
        "spread_range_mean_pts": float(rng["spread_mean_pts"].mean()),
        "spread_window_mean_pts": float(win["spread_mean_pts"].mean()) if len(win) else np.nan,
        # MESURE 1
        "touch_haute_avant_cutoff": t_hi_cut is not None,
        "touch_basse_avant_cutoff": t_lo_cut is not None,
        "t_touch_haute_cutoff_min": _mins(t_hi_cut, b["range_end"]),
        "t_touch_basse_cutoff_min": _mins(t_lo_cut, b["range_end"]),
        # horizon complet
        "t_touch_haute_min": _mins(t_hi_all, b["range_end"]),
        "t_touch_basse_min": _mins(t_lo_all, b["range_end"]),
        # MESURE 2
        "race_t_haute_min": _mins(r_hi, race0),
        "race_t_basse_min": _mins(r_lo, race0),
    }
    row.update(trade)
    return row


def opposite_first(row: pd.Series) -> float:
    """MESURE 2 : la cible opposee a la classe est-elle touchee en premier ?

    NaN si aucune des deux cibles n'est touchee sur l'horizon (session non
    resolue : elle est comptee a part, jamais comptee comme un succes).
    """
    k = row["classe"]
    if k == "NONE":
        return np.nan
    hi, lo = row["race_t_haute_min"], row["race_t_basse_min"]
    same, opp = (hi, lo) if k.endswith("HAUT") else (lo, hi)
    if not np.isfinite(same) and not np.isfinite(opp):
        return np.nan
    if not np.isfinite(opp):
        return 0.0
    if not np.isfinite(same):
        return 1.0
    return float(opp < same)
