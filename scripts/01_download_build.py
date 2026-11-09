"""Download Binance 1s spot klines (+ optional futures aggTrades) and build aligned monthly npz files.

usage: python scripts/01_download_build.py --start 2024-01 --end 2026-11 [--futures]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import download, build  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--start", default="2024-01")
ap.add_argument("--end", default="2026-11")
ap.add_argument("--symbol", default="ETHUSDT")
ap.add_argument("--futures", action="store_true")
ap.add_argument("--spot", action="store_true")
ap.add_argument("--data", default="data")
ap.add_argument("--keep-zips", action="store_true")
a = ap.parse_args()

root = Path(a.data)
for period in download.month_range(a.start, a.end):
    t0 = time.time()
    if a.spot:
        out = root / "spot_1s" / f"{period}.npz"
        if not out.exists():
            zips = download.fetch("klines", a.symbol, period, root / "raw" / "spot", market="spot", interval="1s")
            if zips:
                d = build.build_spot_month(zips, period)
                d = build.ffill_prices(d, None)
                out.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(out, **d)
                if not a.keep_zips:
                    for z in zips:
                        z.unlink()
                print(f"spot {period}: {len(zips)} files, present={d['present'].mean():.5f} ({time.time()-t0:.0f}s)", flush=True)
            else:
                print(f"spot {period}: no data", flush=True)
    if a.futures:
        t0 = time.time()
        out = root / "fut_1s" / f"{period}.npz"
        if not out.exists():
            zips = download.fetch("aggTrades", a.symbol, period, root / "raw" / "fut", market="futures/um")
            if zips:
                d = build.build_futures_month(zips, period)
                d = build.ffill_prices(d, None)
                out.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(out, **d)
                if not a.keep_zips:
                    for z in zips:
                        z.unlink()
                print(f"fut {period}: {len(zips)} files, present={d['present'].mean():.5f} ({time.time()-t0:.0f}s)", flush=True)
            else:
                print(f"fut {period}: no data", flush=True)
