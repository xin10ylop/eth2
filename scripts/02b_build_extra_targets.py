"""Supplemental labels for extra horizons (default 10s and 15s) at the SAME decision rows as the feature files.

Labels only (forward-looking); features are horizon-agnostic and already built.  One parquet per month in
data/targets_extra/, row-aligned with data/features/ (checked by ts).

usage: python scripts/02b_build_extra_targets.py [--horizons 10,15]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import features as fe, series as se  # noqa: E402
from ethmove.build import month_bounds  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--horizons", default="10,15")
a = ap.parse_args()
Hs = np.array([int(h) for h in a.horizons.split(",")], dtype=np.int64)
out_dir = Path("data/targets_extra"); out_dir.mkdir(parents=True, exist_ok=True)
for f in sorted(Path("data/features").glob("*.parquet")):
    out = out_dir / f.name
    if out.exists():
        continue
    t0 = time.time()
    ts = pq.read_table(f, columns=["ts"]).column("ts").to_numpy()
    ms, me = month_bounds(f.stem)
    cs, ce = ms - 3600, me + 400
    se._load_month.cache_clear()
    s = se.load_range(cs, ce, futures=False)
    c, h, l = s["c"], s["h"], s["l"]
    lr = np.zeros(len(c)); lr[1:] = np.diff(np.log(c))
    idx = (ts - cs).astype(np.int64)
    e = ts % fe.WIN
    i_end = idx - e + fe.WIN - 1
    ret, rv, rv5, hi, lo, _, _ = fe.future_targets(c, h, l, lr * lr, idx, i_end, Hs, np.array([5e-4]), 1)
    cols = {"ts": ts}
    for q, H in enumerate(Hs):
        cols[f"y_ret_{H}"] = ret[:, q]; cols[f"y_rv_{H}"] = rv[:, q]; cols[f"y_rv5_{H}"] = rv5[:, q]
        cols[f"y_hi_{H}"] = hi[:, q]; cols[f"y_lo_{H}"] = lo[:, q]
    pq.write_table(pa.table(cols), out, compression="zstd")
    print(f"{f.stem}: {len(ts)} rows ({time.time()-t0:.0f}s)", flush=True)
