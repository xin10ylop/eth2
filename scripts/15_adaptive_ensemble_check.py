"""Adaptive (causal) ensemble of the structural prior and the boosted head, vs plain recalibration.

For each split (val first: the decision; test: reported) and each horizon, per elapsed-time bucket:
  full            boosted head
  full+recal      daily trailing 2-parameter recalibration of the head (current default)
  adaptive        daily trailing logistic stack of logit(head) and logit(structural), per e-bucket
usage: python scripts/15_adaptive_ensemble_check.py --models artifacts/models_v2 --split val
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, metrics as M, structural as st  # noqa: E402
from ethmove.engine import Engine  # noqa: E402
from ethmove.model import hlen  # noqa: E402
from ethmove.recal import trailing_recalibrate, trailing_stack  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--models", default="artifacts/models_v2")
ap.add_argument("--split", default="val")
ap.add_argument("--horizons", default="T,60,30")
a = ap.parse_args()
lo_ts = data.ts_of(data.SPLITS[a.split][0])
wlo = dt.datetime.fromtimestamp(lo_ts - 15 * 86400, dt.UTC).strftime("%Y-%m-%d")
w = data.load("warm", splits={"warm": (wlo, data.SPLITS[a.split][0])})
w = w[w.ts < lo_ts - 3600]
df = pd.concat([w, data.load(a.split)], ignore_index=True)
main = df["ts"].to_numpy() >= lo_ts
eng = Engine.load(a.models)
df, S_ = eng.augment(df)
e = df["e"].to_numpy()
eb = np.digitize(e, [1, 60, 120, 180, 240])
day = df["ts"].to_numpy() // 86400
res = {}
for H in a.horizons.split(","):
    hm = eng.models[H]
    y = hm._d1_target(df)
    pf, ps = hm.predict_above(df, S_[H])
    pr = trailing_recalibrate(df["ts"].to_numpy(), pf, y, groups=eb, min_rows=3000)
    pa = trailing_stack(df["ts"].to_numpy(), np.column_stack([st.logit(pf), st.logit(ps)]), y, groups=eb, min_rows=3000)
    within = main & ((e + hlen(df, H) <= 300) if H != "T" else True)
    r = {}
    for name, p in (("structural", ps), ("full", pf), ("full+recal", pr), ("adaptive", pa)):
        r[name] = {"all": M.logloss(y[within], p[within]),
                   "by_e": {str(b): M.logloss(y[within & (eb == b)], p[within & (eb == b)]) for b in range(6)}}
    mean, lo, hi, _ = M.block_bootstrap_diff(M.ll_vec(y[within], pr[within]), M.ll_vec(y[within], pa[within]), day[within], 500)
    r["adaptive_vs_recal"] = {"mean": mean, "ci95": [lo, hi]}
    res[H] = r
    print(f"[{a.split} {H}] " + " ".join(f"{k}={v['all']:.5f}" for k, v in r.items() if isinstance(v, dict) and "all" in v)
          + f"  adaptive-recal: {mean*1e3:+.2f} [{lo*1e3:+.2f}, {hi*1e3:+.2f}] millinats", flush=True)
    for name in ("structural", "full", "full+recal", "adaptive"):
        print("    ", f"{name:11s}", " ".join(f"e{b}:{r[name]['by_e'][str(b)]:.4f}" for b in range(6)), flush=True)
Path("artifacts/ablation").mkdir(exist_ok=True, parents=True)
json.dump(res, open(f"artifacts/ablation/adaptive_ensemble_{Path(a.models).name}_{a.split}.json", "w"), indent=1)
