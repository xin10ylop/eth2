"""Independent audit of the 5-minute labels and of the headline baseline, straight from the raw 1s files.

It shares no code with features.py, so a labelling bug in the main pipeline would show up as a mismatch:
  1. Recompute K (window open) and the window close directly from the monthly spot npz files and compare
     with the K / close_T stored in the feature dataset for the test period.
  2. Recompute the naive random-walk baseline log loss for the test rows from raw prices.
  3. Report the share of ties (close == K) and the base rate of "up".
"""
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from scipy import special

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data  # noqa: E402
from ethmove.build import month_bounds  # noqa: E402

lo, hi = (data.ts_of(x) for x in data.SPLITS["test"])
rows = []
mism_K = mism_C = n = 0
ties = ups = wins = 0
ll = []
for f in sorted((Path("data") / "features").glob("*.parquet")):
    ms, me = month_bounds(f.stem)
    if me <= lo or ms >= hi:
        continue
    t = pq.read_table(f, columns=["ts", "K", "close_T", "S", "e", "lrv_300"]).to_pandas()
    t = t[(t.ts >= lo) & (t.ts < hi - 86400) & (t.ts > ms)]  # skip the month's first second (needs previous file)
    z = np.load(Path("data") / "spot_1s" / f"{f.stem}.npz")
    o, c = z["o"], z["c"]
    ws = (t.ts.values - t.e.values.astype(np.int64))
    i0 = ws - ms
    K_raw = o[i0]
    C_raw = c[i0 + 299]
    mism_K += int(np.sum(np.abs(K_raw - t.K.values) > 1e-9))
    mism_C += int(np.sum(np.abs(C_raw - t.close_T.values) > 1e-9))
    n += len(t)
    # current price = close of the previous second, recomputed raw
    S_raw = c[t.ts.values - ms - 1]
    assert np.allclose(S_raw, t.S.values)
    y = (C_raw >= K_raw).astype(float)
    tau = 300 - t.e.values
    # naive RW from raw: realised variance of the last 300 1s log returns
    lc = np.log(c)
    lr2 = np.r_[0, np.diff(lc)] ** 2
    cs = np.r_[0, np.cumsum(lr2)]
    j = t.ts.values - ms
    rv = (cs[j] - cs[np.maximum(j - 300, 0)]) / 300
    sd = np.sqrt(rv * tau) + 1e-12
    p = special.ndtr(np.log(S_raw / K_raw) / sd)
    p = np.clip(p, 1e-7, 1 - 1e-7)
    ll.append(-(y * np.log(p) + (1 - y) * np.log(1 - p)))
    uw, idx = np.unique(ws, return_index=True)
    wins += len(uw)
    ties += int(np.sum(C_raw[idx] == K_raw[idx]))
    ups += int(np.sum(C_raw[idx] >= K_raw[idx]))
ll = np.concatenate(ll)
print(f"rows audited: {n:,}   windows: {wins:,}")
print(f"K mismatches: {mism_K}   close mismatches: {mism_C}")
print(f"ties (close == K): {ties} ({ties / wins:.4%})   up-rate (close >= K): {ups / wins:.4f}")
print(f"naive RW log loss recomputed from raw files: {ll.mean():.4f}")
