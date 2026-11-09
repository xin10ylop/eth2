"""Load aligned 1-second spot (+futures) series for arbitrary [start, end) epoch-second ranges."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from .build import month_bounds
from .config import DATA, XDATA, XSYMBOL

SPOT_KEYS = ("o", "h", "l", "c", "v", "qv", "tbv", "n")
FUT_KEYS = ("c", "v", "tbv", "n")


def _period_of(ts: int) -> str:
    import datetime as dt
    d = dt.datetime.fromtimestamp(ts, dt.UTC)
    return f"{d.year:04d}-{d.month:02d}"


def _next_period(p: str) -> str:
    y, m = map(int, p.split("-"))
    return f"{y + (m == 12):04d}-{(m % 12) + 1:02d}"


@lru_cache(maxsize=4)
def _load_month(kind: str, period: str, data_dir: str):
    path = Path(data_dir) / kind / f"{period}.npz"
    if not path.exists():
        return None
    z = np.load(path)
    keys = SPOT_KEYS if kind == "spot_1s" else FUT_KEYS
    return {k: z[k] for k in keys} | {"start": int(z["start"][0])}


def available_periods(kind: str = "spot_1s", data_dir: Path = DATA) -> list[str]:
    return sorted(p.stem for p in (Path(data_dir) / kind).glob("*.npz"))


def load_range(start: int, end: int, data_dir: Path = DATA, futures: bool = True) -> dict[str, np.ndarray]:
    """Return arrays covering seconds [start, end). Missing data -> NaN prices / zero volume.

    Keys: spot o,h,l,c,v,qv,tbv,n ; futures fc,fv,ftbv,fn ; 'start'.
    """
    N = end - start
    out = {k: np.full(N, np.nan) for k in ("o", "h", "l", "c")}
    for k in ("v", "qv", "tbv", "n"):
        out[k] = np.zeros(N)
    if futures:
        out["fc"] = np.full(N, np.nan)
        for k in ("fv", "ftbv", "fn"):
            out[k] = np.zeros(N)
    p = _period_of(start)
    while True:
        ms, me = month_bounds(p)
        if ms >= end:
            break
        lo, hi = max(ms, start), min(me, end)
        sp = _load_month("spot_1s", p, str(data_dir))
        if sp is not None:
            for k in SPOT_KEYS:
                out[k][lo - start:hi - start] = sp[k][lo - ms:hi - ms]
        if futures:
            fu = _load_month("fut_1s", p, str(data_dir))
            if fu is not None:
                for k in FUT_KEYS:
                    out["f" + k if k != "c" else "fc"][lo - start:hi - start] = fu[k][lo - ms:hi - ms]
        p = _next_period(p)
    out["start"] = start
    return out


def load_cross(start: int, end: int, xdata: Path = XDATA) -> dict[str, np.ndarray] | None:
    """Leader-asset (e.g. BTCUSDT) spot + perpetual bars on the same second grid, keys prefixed with x."""
    if not XSYMBOL or not (Path(xdata) / "spot_1s").exists():
        return None
    s = load_range(start, end, data_dir=Path(xdata), futures=True)
    return {"x" + k: v for k, v in s.items() if k != "start"}


def load_with_cross(start: int, end: int, data_dir: Path = DATA, futures: bool = True) -> dict[str, np.ndarray]:
    s = load_range(start, end, data_dir=data_dir, futures=futures)
    x = load_cross(start, end)
    if x is not None:
        s.update(x)
    return s
