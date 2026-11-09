"""Regime-robustness design choices, decided on the VALIDATION period only.

Compares, for the vol + drift engines (stage A/B) and the structural above-reference probability:
  base            current feature set
  +regime         + causal multi-day regime state (ethmove/regime.py)
  decayHL         recency-weighted training (weight = 0.5 ** (age / HL days))
Reported per validation month as well, to see whether a choice helps consistently or only on average.

usage: python scripts/13_regime_check.py --horizon 30 [--frac 0.15]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import special, stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, metrics as M, model as mdl  # noqa: E402
from ethmove.regime import REGIME_COLS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--horizon", default="30")
ap.add_argument("--frac", type=float, default=0.15)
a = ap.parse_args()
H = a.horizon
tr = data.load("train", frac=a.frac, seed=3)
va = data.load("val", frac=0.5, seed=4)
allf = data.feature_columns(tr)
base = [f for f in allf if f not in REGIME_COLS]
t_end = data.ts_of(data.SPLITS["train"][1])
age_days = (t_end - tr["ts"].to_numpy()) / 86400
import os
ONLY = os.environ.get("ONLY")
configs = {
    "base": (base, None),
    "base+decay180": (base, 0.5 ** (age_days / 180)),
    "base+decay365": (base, 0.5 ** (age_days / 365)),
    "+regime": (allf, None),
    "+regime+decay180": (allf, 0.5 ** (age_days / 180)),
    "+regime+decay365": (allf, 0.5 ** (age_days / 365)),
}
R = va[f"y_ret_{H}"].to_numpy(np.float64)
qK = np.log(va["K"].to_numpy() / va["S"].to_numpy())
yK = mdl.HorizonModel(H, base, log=None)._d1_target(va)
nz = R != 0
month = np.array([time.strftime("%Y-%m", time.gmtime(t)) for t in va["ts"].to_numpy()])
if ONLY:
    configs = {k: v for k, v in configs.items() if k in ONLY.split(",")}
res = {}
for name, (feats, w) in configs.items():
    t0 = time.time()
    hm = mdl.HorizonModel(H, feats, log=None)
    Xtr, Xva = mdl._X(tr, hm.feats), mdl._X(va, hm.feats)
    vb = mdl._fit(Xtr, hm._vol_target(tr), dict(objective="gamma", learning_rate=0.08), 2000, Xva, hm._vol_target(va), weight=w)
    sd_tr = np.sqrt(hm._var_from(tr, vb.predict(Xtr))); sd_va = np.sqrt(hm._var_from(va, vb.predict(Xva)))
    Xtr, Xva = mdl._X(tr, hm.dir_feats), mdl._X(va, hm.dir_feats)
    utr, uva = hm._drift_target(tr, sd_tr), hm._drift_target(va, sd_va)
    db = mdl._fit(Xtr, utr, dict(objective="regression", num_leaves=31, min_data_in_leaf=5000, lambda_l2=50.0), 3000, Xva, uva, weight=w)
    m = db.predict(Xva)
    ww = np.ones(len(utr)) if w is None else w
    sc = np.sqrt(np.sum(ww * (tr[f"y_ret_{H}"].to_numpy() / sd_tr - db.predict(Xtr)) ** 2) / ww.sum())
    pK = special.ndtr(-(qK - m * sd_va) / (sd_va * sc))
    r = {"ic": float(stats.spearmanr(m[nz], R[nz]).statistic),
         "dir_auc": M.auc((R[nz] > 0).astype(float), special.ndtr(m / sc)[nz]),
         "above_ref_ll": M.logloss(yK, pK), "vol_qlike": M.qlike(va[f"y_rv5_{H}"].to_numpy(), (sd_va * sc) ** 2),
         "monthly_ll": {mo: M.logloss(yK[month == mo], pK[month == mo]) for mo in np.unique(month)},
         "monthly_qlike": {mo: M.qlike(va[f"y_rv5_{H}"].to_numpy()[month == mo], ((sd_va * sc) ** 2)[month == mo]) for mo in np.unique(month)}}
    if name.startswith("+regime") and "decay" not in name:
        imp = vb.feature_importance("gain"); imp = imp / imp.sum()
        r["vol_regime_gain_share"] = float(sum(imp[i] for i, f in enumerate(hm.feats) if f.startswith("rg_")))
        imp = db.feature_importance("gain"); imp = imp / imp.sum()
        r["drift_regime_gain_share"] = float(sum(imp[i] for i, f in enumerate(hm.dir_feats) if f.startswith("rg_")))
    res[name] = r
    print(f"[{H}] {name:18s} ic={r['ic']:.4f} dirAUC={r['dir_auc']:.4f} aboveK_LL={r['above_ref_ll']:.5f} qlike={r['vol_qlike']:.4f} "
          f"monthlyLL={' '.join(f'{v:.4f}' for v in r['monthly_ll'].values())} ({time.time()-t0:.0f}s)", flush=True)
Path("artifacts/ablation").mkdir(parents=True, exist_ok=True)
json.dump(res, open(f"artifacts/ablation/regime_check_{H}{'_' + os.environ.get('TAG') if os.environ.get('TAG') else ''}.json", "w"), indent=1)
