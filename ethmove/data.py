"""Dataset loading and chronological splits (with embargo)."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

FEAT_DIR = Path(__file__).resolve().parents[1] / "data" / "features"

NON_FEATURES = {"ts", "K", "S", "close_T"}


def ts_of(date: str) -> int:
    return int(dt.datetime.fromisoformat(date).replace(tzinfo=dt.UTC).timestamp())


# Chronological protocol. Test is never used for any modelling decision.
SPLITS = {
    "train": ("2024-02-01", "2026-03-01"),
    "val": ("2026-03-01", "2026-06-01"),
    "test": ("2026-06-01", "2026-11-03"),
}
EMBARGO_S = 86400  # drop the last day of each segment (labels look ahead up to 6 minutes)


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_FEATURES and not c.startswith("y_")]


def load(split: str, frac: float = 1.0, seed: int = 0, columns: list[str] | None = None,
         feat_dir: Path = FEAT_DIR, splits: dict | None = None, regime: bool = True) -> pd.DataFrame:
    lo, hi = (ts_of(x) for x in (splits or SPLITS)[split])
    hi_eff = hi - EMBARGO_S
    parts = []
    rng = np.random.default_rng(seed)
    for f in sorted(feat_dir.glob("*.parquet")):
        y, m = map(int, f.stem.split("-"))
        ms = ts_of(f"{y:04d}-{m:02d}-01")
        me = ts_of(f"{y + (m == 12):04d}-{(m % 12) + 1:02d}-01")
        if me <= lo or ms >= hi_eff:
            continue
        t = pq.read_table(f, columns=columns).to_pandas()
        xf = feat_dir.parent / "targets_extra" / f.name
        if xf.exists() and columns is None:
            x = pq.read_table(xf).to_pandas()
            assert np.array_equal(x["ts"].to_numpy(), t["ts"].to_numpy()), f"misaligned extra targets {xf}"
            for k in x.columns:
                if k not in t.columns:
                    t[k] = x[k].to_numpy()
        t = t[(t.ts >= lo) & (t.ts < hi_eff)]
        if frac < 1.0:
            # subsample whole windows (keeps within-window structure; avoids near-duplicate rows)
            w = (t.ts.values // 300)
            uw = np.unique(w)
            keep = rng.random(len(uw)) < frac
            t = t[np.isin(w, uw[keep])]
        parts.append(t)
    df = pd.concat(parts, ignore_index=True)
    if regime:
        rp = feat_dir.parent / "regime.npz"
        if rp.exists():
            from . import regime as rg
            for k, v in rg.lookup(rg.load(rp), df["ts"].to_numpy()).items():
                df[k] = v
    return df
