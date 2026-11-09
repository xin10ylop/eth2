"""Build the sampled feature/target dataset, one parquet file per month.

usage: python scripts/02_build_features.py [--start 2024-02] [--end 2026-11] [--step 10] [--wait]
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
from ethmove.download import month_range  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--start", default="2024-02")
ap.add_argument("--end", default="2026-11")
ap.add_argument("--step", type=int, default=10)
ap.add_argument("--wait", action="store_true", help="wait for futures month files to appear")
ap.add_argument("--out", default="data/features")
a = ap.parse_args()

DATA = Path("data")
out_dir = Path(a.out); out_dir.mkdir(parents=True, exist_ok=True)

# ---- data extent ----
periods = se.available_periods("spot_1s")
first_ts = month_bounds(periods[0])[0]
last = np.load(DATA / "spot_1s" / f"{periods[-1]}.npz")
data_end = month_bounds(periods[-1])[0] + int(np.where(last["present"])[0].max()) + 1
data_end -= data_end % 300
print("data from", first_ts, "to", data_end, flush=True)

# ---- causal seasonal profiles over full history ----
seas_path = DATA / "seasonal.npz"
if not seas_path.exists() or seas_path.stat().st_mtime < (DATA / "spot_1s" / f"{periods[-1]}.npz").stat().st_mtime:
    full = se.load_range(first_ts, data_end, futures=False)
    seas = fe.build_seasonal(full["c"], first_ts)
    np.savez(seas_path, **{k: v for k, v in seas.items()})
    del full
z = np.load(seas_path)
seas = {k: (int(z[k]) if k == "ts0" else z[k]) for k in z.files}

for period in month_range(a.start, a.end):
    out = out_dir / f"{period}.parquet"
    if out.exists():
        continue
    ms, me = month_bounds(period)
    if ms >= data_end:
        break
    fut_path = DATA / "fut_1s" / f"{period}.npz"
    while not fut_path.exists():
        if not a.wait:
            print(f"{period}: futures missing, skipping", flush=True)
            break
        time.sleep(30)
    if not fut_path.exists():
        continue
    t0 = time.time()
    hi = min(me, data_end - 400)
    cs, ce = ms - 2 * 86400, min(me + 400, data_end)
    se._load_month.cache_clear()
    ser = se.load_with_cross(cs, ce, futures=True)   # primary asset + leader asset (x*) on the same grid
    idx = fe.sample_indices(cs, ce - cs, ms, hi, step=a.step, seed=7)
    F = fe.compute(ser, idx, seasonal=seas, with_targets=True)
    tab = pa.table({k: v for k, v in F.items()})
    pq.write_table(tab, out, compression="zstd")
    print(f"{period}: {len(idx)} rows, {len(F)} cols, {time.time()-t0:.0f}s", flush=True)

# ---- causal multi-day regime state (daily aggregates + rg_* table) ----
from ethmove import regime as rg  # noqa: E402
daily = rg.build_daily()
np.savez(DATA / "regime_daily.npz", **daily)
rg.save(rg.regime_table(daily), DATA / "regime.npz")
print(f"regime table: {len(daily['day'])} days", flush=True)
