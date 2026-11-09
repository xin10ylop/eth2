"""Train the full stack for each horizon and save to artifacts/.

usage: python scripts/03_train.py [--frac 0.35] [--horizons T,30,60] [--smoke]
"""
import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, model  # noqa: E402
from ethmove.engine import STACK_FROM, stack_columns  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--frac", type=float, default=0.35)
ap.add_argument("--horizons", default="30,60,T")
ap.add_argument("--no-stack", action="store_true", help="do not feed 30s/60s forecasts into the 5-minute model")
ap.add_argument("--heads", default="d1,d2,d3,d4")
ap.add_argument("--smoke", action="store_true")
ap.add_argument("--dates", default="", help="walk-forward: train_start,val_start,test_start,test_end (YYYY-MM-DD)")
ap.add_argument("--out", default="artifacts/models")
ap.add_argument("--drop", default="", help="comma-separated feature prefixes to drop (ablation)")
ap.add_argument("--half-life", type=float, default=180.0,
                help="recency weighting of training rows, half-life in days (0 = unweighted)")
ap.add_argument("--no-regime", action="store_true", help="exclude the multi-day regime features (v1 recipe)")
a = ap.parse_args()

splits = data.SPLITS
if a.smoke:
    splits = {"train": ("2024-02-01", "2024-08-01"), "val": ("2024-08-01", "2024-09-01"), "test": ("2024-09-01", "2024-11-01")}
if a.dates:
    d0, d1, d2, d3 = a.dates.split(",")
    splits = {"train": (d0, d1), "val": (d1, d2), "test": (d2, d3)}

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
logf = open(out / "train.log", "a")


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    logf.write(line + "\n"); logf.flush()


t0 = time.time()
tr = data.load("train", frac=a.frac, seed=1, splits=splits)
va = data.load("val", frac=1.0, splits=splits)
feats = data.feature_columns(tr)
drops = [d for d in a.drop.split(",") if d] + (["rg_"] if a.no_regime else [])
feats = [f for f in feats if not any(f.startswith(d) for d in drops)]
log(f"train {len(tr):,} rows  val {len(va):,} rows  {len(feats)} features  splits={splits}  ({time.time()-t0:.0f}s)")

W = None
if a.half_life > 0:
    age = (data.ts_of(splits["train"][1]) - tr["ts"].to_numpy()) / 86400.0
    W = 0.5 ** (age / a.half_life)
    log(f"recency weighting: half-life {a.half_life:.0f} days, effective sample share {W.sum()**2 / (W**2).sum() / len(W):.2f}")
stacked = []
for H in a.horizons.split(","):
    hfeats = feats + (stacked if H == "T" else [])
    hm = model.HorizonModel(H, hfeats, log=log)
    hm.w_tr = W
    (sd_tr, m_tr), (sd_va, m_va) = hm.fit_ab(tr, va)
    hm.fit_shape(tr, sd_tr, m_tr)
    s_tr = hm.structural(tr, sd_tr, m_tr)
    s_va = hm.structural(va, sd_va, m_va)
    if H in STACK_FROM and not a.no_stack:
        # out-of-fold short-horizon forecasts become inputs of the 5-minute model
        for k, v in stack_columns(tr, s_tr, H).items():
            tr[k] = v
            stacked.append(k)
        for k, v in stack_columns(va, s_va, H).items():
            va[k] = v
    hm.fit_heads(tr, s_tr, va, s_va, heads=tuple(a.heads.split(",")))
    hm.log = None
    hm.w_tr = None
    hm.recipe = {"half_life_days": a.half_life, "regime_features": not a.no_regime, "frac": a.frac, "splits": splits}
    with open(out / f"horizon_{H}.pkl", "wb") as f:
        pickle.dump(hm, f)
    log(f"[{H}] saved ({time.time()-t0:.0f}s)")
