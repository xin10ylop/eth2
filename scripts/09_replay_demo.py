"""Replay a historical 5-minute window through the *live* predictor, second by second.

Prints a compact trace of the probabilities through the window and writes the full JSON stream.
usage: python scripts/09_replay_demo.py [--start "2026-10-15 14:30"] [--models artifacts/models]
"""
import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import series as se  # noqa: E402
from ethmove.live import BUF, LivePredictor, replay  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--start", default="2026-10-15 14:30")
ap.add_argument("--models", default="artifacts/models")
ap.add_argument("--out", default="artifacts/replay_demo.jsonl")
a = ap.parse_args()

t_win = int(dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.UTC).timestamp())
t_win -= t_win % 300
lo = t_win - BUF - 10
ser = se.load_with_cross(lo, t_win + 400)   # ETH + BTC leader on the same grid
pred = LivePredictor.from_artifacts(a.models)
t0 = time.time()
# replay from 1 second before the window so the first emitted decision is e=0
outs = replay(pred, ser, start_i=t_win - lo - 1, n_steps=300)
el = time.time() - t0
with open(a.out, "w") as f:
    for o in outs:
        f.write(json.dumps(o) + "\n")
K = outs[0]["reference_price"]
final = float(ser["c"][t_win - lo + 299])
print(f"window {dt.datetime.fromtimestamp(t_win, dt.UTC):%Y-%m-%d %H:%M} UTC   reference K = {K:.2f}   "
      f"final close = {final:.2f} ({'UP' if final >= K else 'DOWN'})   [{el/len(outs)*1e3:.0f} ms per second]")
hz = [h for h in ("10s", "15s", "30s", "60s", "close") if h in outs[0]["horizons"]]
print(" e    price     d(bps) " + " ".join(f"P({h}>=K)" for h in hz) + "  sd_close  touch K+10  touch K-10  alert")
for o in outs[::15]:
    c = o["horizons"]["close"]
    print(f"{o['elapsed_s']:3d} {o['price']:10.2f} {o['displacement_bps']:6.2f}  " + " ".join(f"{o['horizons'][h]['p_above_reference']:9.3f}" for h in hz)
          + f"   {c['sd_bps']:6.2f}    {c['levels']['K+10bp']['p_touch_before_end']:.3f}       {c['levels']['K-10bp']['p_touch_before_end']:.3f}    {o['monitor']['regime_alert']}")
