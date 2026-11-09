"""Validation-only check of where the BTC-leader block (x_*) belongs for a horizon:
everywhere / volatility engine only / nowhere.  usage: python scripts/16_cross_check.py --horizon T"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import special, stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, metrics as M, model as mdl  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--horizon", default="T")
ap.add_argument("--frac", type=float, default=0.15)
a = ap.parse_args()
H = a.horizon
tr = data.load("train", frac=a.frac, seed=3)
va = data.load("val", frac=0.5, seed=4)
allf = [f for f in data.feature_columns(tr) if not f.startswith("rg_")]
nox = [f for f in allf if not f.startswith("x_")]
R = va[f"y_ret_{H}"].to_numpy(); qK = np.log(va["K"].to_numpy() / va["S"].to_numpy())
nz = R != 0
res = {}
for name, vfeats, dfeats in (("x_everywhere", allf, [f for f in allf if f not in mdl.CALENDAR]),
                             ("x_vol_only", allf, [f for f in nox if f not in mdl.CALENDAR]),
                             ("x_nowhere", nox, [f for f in nox if f not in mdl.CALENDAR])):
    t0 = time.time()
    hm = mdl.HorizonModel(H, vfeats, log=None)
    yK = hm._d1_target(va)
    Xtr, Xva = mdl._X(tr, vfeats), mdl._X(va, vfeats)
    vb = mdl._fit(Xtr, hm._vol_target(tr), dict(objective="gamma", learning_rate=0.08), 2000, Xva, hm._vol_target(va))
    sd_tr = np.sqrt(hm._var_from(tr, vb.predict(Xtr))); sd_va = np.sqrt(hm._var_from(va, vb.predict(Xva)))
    Xtr, Xva = mdl._X(tr, dfeats), mdl._X(va, dfeats)
    utr, uva = hm._drift_target(tr, sd_tr), hm._drift_target(va, sd_va)
    db = mdl._fit(Xtr, utr, dict(objective="regression", num_leaves=31, min_data_in_leaf=5000, lambda_l2=50.0), 3000, Xva, uva)
    m = db.predict(Xva)
    sc = np.sqrt(np.mean((tr[f"y_ret_{H}"].to_numpy() / sd_tr - db.predict(Xtr)) ** 2))
    pK = special.ndtr(-(qK - m * sd_va) / (sd_va * sc))
    res[name] = {"ic": float(stats.spearmanr(m[nz], R[nz]).statistic), "above_ref_ll": M.logloss(yK, pK),
                 "vol_qlike": M.qlike(va[f"y_rv5_{H}"].to_numpy(), (sd_va * sc) ** 2)}
    print(f"[{H}] {name:13s} " + " ".join(f"{k}={v:.5f}" for k, v in res[name].items()) + f" ({time.time()-t0:.0f}s)", flush=True)
Path("artifacts/ablation").mkdir(parents=True, exist_ok=True)
json.dump(res, open(f"artifacts/ablation/cross_check_{H}.json", "w"), indent=1)
