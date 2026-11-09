"""Market-regime state (slow, multi-day), strictly causal.

Daily aggregates are computed from the 1-second archive; the regime features for a decision made on UTC
day D use only days < D (the current day's partial information is already in the intraday features).

Features (prefix `rg_`):
  rg_lvol1/7/30     log mean daily realised variance (1-minute returns) over the last 1/7/30 days
  rg_volratio       rg_lvol7 - rg_lvol30            (vol expanding / contracting)
  rg_vov30          std of log daily RV over 30 days (vol-of-vol: regime instability)
  rg_trend1/7/30    cumulative return over 1/7/30 days, in units of the daily vol
  rg_dd30           drawdown from the 30-day high, in daily-vol units
  rg_up30           distance above the 30-day low, in daily-vol units
  rg_lvolu7         log(7-day / 30-day spot volume)         (activity regime)
  rg_illiq7         log(7-day / 30-day Amihud illiquidity)  (liquidity regime)
  rg_basis7         7-day mean perp-spot basis (bps)         (carry / leverage regime)
  rg_basis_chg      1-day minus 7-day basis (bps)
  rg_fshare7        log(perp / spot volume), 7 days          (where price discovery happens)
  rg_age            days since the 7-day vol last crossed its 30-day vol (age of the current vol regime)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .build import month_bounds
from .download import month_range

DAY = 86400
REGIME_COLS = ["rg_lvol1", "rg_lvol7", "rg_lvol30", "rg_volratio", "rg_vov30", "rg_trend1", "rg_trend7",
               "rg_trend30", "rg_dd30", "rg_up30", "rg_lvolu7", "rg_illiq7", "rg_basis7", "rg_basis_chg",
               "rg_fshare7", "rg_age"]


def daily_aggregates(c, v, fc, fv, ts0):
    """Per-day aggregates from aligned 1s arrays starting at a day boundary ts0."""
    nd = len(c) // DAY
    c = c[: nd * DAY].reshape(nd, DAY)
    v = v[: nd * DAY].reshape(nd, DAY)
    fc = fc[: nd * DAY].reshape(nd, DAY)
    fv = fv[: nd * DAY].reshape(nd, DAY)
    lm = np.log(c[:, 59::60])                       # 1-minute closes
    prev = np.concatenate([[lm[0, 0]], lm[:-1, -1]])
    r1m = np.diff(np.concatenate([prev[:, None], lm], 1), axis=1)
    out = {
        "day": (ts0 // DAY) + np.arange(nd),
        "rv": np.nansum(r1m ** 2, 1),
        "absr": np.nansum(np.abs(r1m), 1),
        "close": c[:, -1],
        "open": c[:, 0],
        "vol": v.sum(1),
        "fvol": fv.sum(1),
        "basis": np.nanmean(np.log(np.where(np.isfinite(fc), fc, c)) - np.log(c), 1),
    }
    return out


def build_daily(periods=None, data_dir="data"):
    from . import series as se
    periods = periods or se.available_periods("spot_1s", Path(data_dir))
    parts = []
    for p in periods:
        ms, me = month_bounds(p)
        s = se.load_range(ms, me, data_dir=Path(data_dir), futures=True)
        pres = np.isfinite(s["c"])
        if pres.sum() < DAY:
            continue
        nd = int(pres.sum()) // DAY
        n = nd * DAY
        parts.append(daily_aggregates(s["c"][:n], s["v"][:n], s["fc"][:n], s["fv"][:n], ms))
    d = {k: np.concatenate([p_[k] for p_ in parts]) for k in parts[0]}
    # keep only days with real trading (spot volume > 0)
    ok = d["vol"] > 0
    return {k: v[ok] for k, v in d.items()}


def _trail(x, n, fn):
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        a = x[max(0, i - n): i]          # strictly previous days
        if len(a):
            out[i] = fn(a)
    return out


def regime_table(daily: dict) -> dict:
    """Regime features per day D (row i) using only rows < i.  Returns {'day': days, col: values}."""
    lrv = np.log(daily["rv"] + 1e-12)
    rv = daily["rv"]
    lc = np.log(daily["close"])
    sig_d = np.sqrt(_trail(rv, 30, np.mean))      # typical daily vol over the last 30 days
    T = {"day": daily["day"]}
    T["rg_lvol1"] = _trail(lrv, 1, np.mean)
    T["rg_lvol7"] = np.log(_trail(rv, 7, np.mean) + 1e-12)
    T["rg_lvol30"] = np.log(_trail(rv, 30, np.mean) + 1e-12)
    T["rg_volratio"] = T["rg_lvol7"] - T["rg_lvol30"]
    T["rg_vov30"] = _trail(lrv, 30, np.std)
    lc_prev = np.concatenate([[np.nan], lc[:-1]])
    for n in (1, 7, 30):
        base = np.concatenate([np.full(n + 1, np.nan), lc[:-(n + 1)]]) if len(lc) > n + 1 else np.full(len(lc), np.nan)
        T[f"rg_trend{n}"] = (lc_prev - base) / (sig_d * np.sqrt(n))
    hi30 = _trail(lc, 30, np.max)
    lo30 = _trail(lc, 30, np.min)
    T["rg_dd30"] = (lc_prev - hi30) / sig_d
    T["rg_up30"] = (lc_prev - lo30) / sig_d
    T["rg_lvolu7"] = np.log(_trail(daily["vol"], 7, np.mean) / _trail(daily["vol"], 30, np.mean))
    illiq = daily["absr"] / (daily["vol"] * daily["close"] + 1e-9)
    T["rg_illiq7"] = np.log(_trail(illiq, 7, np.mean) / _trail(illiq, 30, np.mean))
    T["rg_basis7"] = _trail(daily["basis"], 7, np.mean) * 1e4
    T["rg_basis_chg"] = _trail(daily["basis"], 1, np.mean) * 1e4 - T["rg_basis7"]
    T["rg_fshare7"] = np.log(_trail(daily["fvol"], 7, np.sum) / _trail(daily["vol"], 7, np.sum))
    # age of the current vol regime: days since sign(volratio) last changed
    sgn = np.sign(np.nan_to_num(T["rg_volratio"]))
    age = np.zeros(len(sgn))
    for i in range(1, len(sgn)):
        age[i] = age[i - 1] + 1 if sgn[i] == sgn[i - 1] else 0
    T["rg_age"] = np.log1p(age)
    return T


def lookup(table: dict, ts: np.ndarray) -> dict:
    """Regime features for decision timestamps (day = ts // 86400). Days beyond the table reuse the last row
    (a live process should refresh the table daily)."""
    day = np.asarray(ts) // DAY
    idx = np.searchsorted(table["day"], day)
    idx = np.clip(idx, 0, len(table["day"]) - 1)
    exact = table["day"][idx] == day
    out = {}
    for k in REGIME_COLS:
        v = table[k][idx].astype(np.float32)
        out[k] = np.where(exact, v, table[k][-1]).astype(np.float32)
    return out


def save(table: dict, path="data/regime.npz"):
    np.savez(path, **table)


def load(path="data/regime.npz"):
    z = np.load(path)
    return {k: z[k] for k in z.files}
