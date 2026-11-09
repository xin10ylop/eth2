"""Parse raw Binance archives into gap-free, aligned 1-second arrays (one .npz per month).

Spot 1s klines -> o,h,l,c,v,qv,n,tbv on a complete UTC second grid.
Futures aggTrades -> per-second close/high/low/volume/taker-buy-volume/n/qv on the same grid.

Every second of the month is present in the output; seconds without trades are flagged
(`present=False`) and carry the previous close as o=h=l=c with zero volume.
"""
from __future__ import annotations

import calendar
import datetime as dt
import io
import zipfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.csv as pcsv


def month_bounds(period: str) -> tuple[int, int]:
    y, m = map(int, period.split("-"))
    start = int(calendar.timegm(dt.datetime(y, m, 1).timetuple()))
    y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
    end = int(calendar.timegm(dt.datetime(y2, m2, 1).timetuple()))
    return start, end


def _read_zip_csv(path: Path, names: list[str], types: dict) -> pa.Table:
    with zipfile.ZipFile(path) as z:
        inner = z.namelist()[0]
        raw = z.read(inner)
    # detect header
    first = raw[:200].split(b"\n")[0]
    has_header = not first[:1].isdigit()
    ro = pcsv.ReadOptions(column_names=names, skip_rows=1 if has_header else 0, block_size=1 << 26)
    co = pcsv.ConvertOptions(column_types=types)
    return pcsv.read_csv(io.BytesIO(raw), read_options=ro, convert_options=co)


def _to_seconds(t: np.ndarray) -> np.ndarray:
    """Binance timestamps are ms (pre-2025 spot / futures) or us (spot from 2025). Return epoch seconds."""
    t = t.astype(np.int64)
    mx = t.max()
    if mx > 10**15:  # microseconds
        return t // 1_000_000
    return t // 1000


KLINE_COLS = ["ot", "o", "h", "l", "c", "v", "ct", "qv", "n", "tbv", "tbq", "ig"]


def build_spot_month(zips: list[Path], period: str) -> dict[str, np.ndarray]:
    start, end = month_bounds(period)
    N = end - start
    types = {k: pa.float64() for k in ["o", "h", "l", "c", "v", "qv", "tbv", "tbq"]}
    types.update({"ot": pa.int64(), "ct": pa.int64(), "n": pa.int64(), "ig": pa.string()})
    tabs = [_read_zip_csv(p, KLINE_COLS, types) for p in sorted(zips)]
    tab = pa.concat_tables(tabs)
    sec = _to_seconds(tab["ot"].to_numpy())
    idx = sec - start
    ok = (idx >= 0) & (idx < N)
    idx = idx[ok]
    out = {}
    present = np.zeros(N, dtype=bool)
    present[idx] = True
    for k in ["o", "h", "l", "c"]:
        a = np.full(N, np.nan)
        a[idx] = tab[k].to_numpy()[ok]
        out[k] = a
    for k in ["v", "qv", "tbv"]:
        a = np.zeros(N)
        a[idx] = tab[k].to_numpy()[ok]
        out[k] = a
    n = np.zeros(N, dtype=np.int32)
    n[idx] = tab["n"].to_numpy()[ok]
    out["n"] = n
    out["present"] = present
    out["start"] = np.array([start], dtype=np.int64)
    return out


AGG_COLS = ["id", "p", "q", "f", "l", "t", "m"]


def build_futures_month(zips: list[Path], period: str) -> dict[str, np.ndarray]:
    """Aggregate futures aggTrades to 1s bars, streaming the CSV in batches (bounded memory)."""
    start, end = month_bounds(period)
    N = end - start
    types = {"id": pa.int64(), "p": pa.float64(), "q": pa.float64(), "f": pa.int64(), "l": pa.int64(), "t": pa.int64(), "m": pa.bool_()}
    c = np.full(N, np.nan); h = np.full(N, -np.inf); lo = np.full(N, np.inf)
    v = np.zeros(N); bv = np.zeros(N); qv = np.zeros(N); n = np.zeros(N, dtype=np.int64)
    last_t = np.full(N, -1, dtype=np.int64)
    for p in sorted(zips):
        with zipfile.ZipFile(p) as z:
            inner = z.namelist()[0]
            with z.open(inner) as fh:
                first = fh.read(64)
            has_header = not first[:1].isdigit()
            with z.open(inner) as fh:
                ro = pcsv.ReadOptions(column_names=AGG_COLS, skip_rows=1 if has_header else 0, block_size=1 << 26)
                reader = pcsv.open_csv(fh, read_options=ro, convert_options=pcsv.ConvertOptions(column_types=types))
                for batch in reader:
                    t = batch.column("t").to_numpy()
                    sec = _to_seconds(t) if t.max() > 10**15 else t // 1000
                    price = batch.column("p").to_numpy(); qty = batch.column("q").to_numpy()
                    is_buy = ~batch.column("m").to_numpy(zero_copy_only=False).astype(bool)
                    idx = sec - start
                    ok = (idx >= 0) & (idx < N)
                    idx, price, qty, is_buy, t = idx[ok], price[ok], qty[ok], is_buy[ok], t[ok]
                    if len(idx) == 0:
                        continue
                    order = np.lexsort((t, idx))
                    idx, price, qty, is_buy, t = idx[order], price[order], qty[order], is_buy[order], t[order]
                    lastm = np.r_[idx[1:] != idx[:-1], True]
                    li, lp, lt = idx[lastm], price[lastm], t[lastm]
                    newer = lt >= last_t[li]
                    c[li[newer]] = lp[newer]; last_t[li[newer]] = lt[newer]
                    np.maximum.at(h, idx, price)
                    np.minimum.at(lo, idx, price)
                    v += np.bincount(idx, weights=qty, minlength=N)
                    bv += np.bincount(idx, weights=qty * is_buy, minlength=N)
                    qv += np.bincount(idx, weights=qty * price, minlength=N)
                    n += np.bincount(idx, minlength=N)
    present = n > 0
    h[~present] = np.nan; lo[~present] = np.nan
    return {"c": c, "h": h, "l": lo, "v": v, "tbv": bv, "qv": qv, "n": n.astype(np.int32), "present": present,
            "start": np.array([start], dtype=np.int64)}


def ffill_prices(d: dict[str, np.ndarray], prev_close: float | None) -> dict[str, np.ndarray]:
    """Forward-fill missing seconds with previous close (causal)."""
    c = d["c"]
    pres = ~np.isnan(c)
    idx = np.where(pres, np.arange(len(c)), -1)
    np.maximum.accumulate(idx, out=idx)
    filled = np.where(idx >= 0, c[np.maximum(idx, 0)], np.nan)
    if prev_close is not None:
        filled = np.where(np.isnan(filled), prev_close, filled)
    miss = ~pres
    d["c"] = filled
    for k in ["o", "h", "l"]:
        if k in d:
            d[k] = np.where(miss, filled, d[k])
    return d
