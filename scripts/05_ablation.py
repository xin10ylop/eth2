"""Feature-family ablations on the VALIDATION period (the test period is not touched).

For each feature set, fits the vol + drift engines (stage A/B, early-stopped on val) for a horizon and
reports on val: drift IC, directional AUC, and the structural above-reference log loss.  Also fits a
ridge-regression drift model as an architecture-robustness check.

usage: python scripts/05_ablation.py --horizon 30 [--frac 0.2]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import special, stats
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, metrics as M, model as mdl  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--horizon", default="30")
ap.add_argument("--frac", type=float, default=0.2)
ap.add_argument("--out", default="artifacts/ablation")
a = ap.parse_args()
H = a.horizon
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

tr = data.load("train", frac=a.frac, seed=3)
va = data.load("val", frac=0.5, seed=4)
allf = [f for f in data.feature_columns(tr) if not f.startswith("rg_")]  # same feature universe as the 30s/60s runs
FUT = [f for f in allf if f.startswith(("basis", "zfret", "fofi", "fsflow", "lfvshare", "lfrv", "fut_ok"))]
FLOW = [f for f in allf if f.startswith(("ofi", "sflow", "ewflow", "llam", "resid", "fofi", "fsflow"))]
WIN = ["run_hi", "run_lo", "hi_gap", "lo_gap", "frac_above", "n_cross", "t_since_cross", "t_since_hi", "t_since_lo",
       "lrv_win", "ofi_win", "prev_win_ret", "k_gap", "dz_e"]
RND = [f for f in allf if f.startswith("rnd_")]
CROSS = [f for f in allf if f.startswith("x_")]
MOM = [f for f in allf if f.startswith(("zret", "zfret", "resid", "vwap", "ret_300"))]
configs = {
    "all": allf,
    "no_cross_asset_btc": [f for f in allf if f not in CROSS],
    "no_futures": [f for f in allf if f not in FUT],
    "no_flow": [f for f in allf if f not in FLOW],
    "no_window_state": [f for f in allf if f not in WIN],
    "no_round_levels": [f for f in allf if f not in RND],
    "no_momentum": [f for f in allf if f not in MOM],
    "spot_price_only": [f for f in allf if f not in FUT and f not in FLOW and f not in CROSS],
    "no_futures_no_cross": [f for f in allf if f not in FUT and f not in CROSS],
}
R = va[f"y_ret_{H}"].to_numpy(np.float64)
qK = np.log(va["K"].to_numpy() / va["S"].to_numpy())
hm0 = mdl.HorizonModel(H, allf, log=None)
yK = hm0._d1_target(va)
nz = R != 0
res = {}
for name, feats in configs.items():
    t0 = time.time()
    hm = mdl.HorizonModel(H, feats, log=None)
    Xtr, Xva = mdl._X(tr, hm.feats), mdl._X(va, hm.feats)
    vb = mdl._fit(Xtr, hm._vol_target(tr), dict(objective="gamma", learning_rate=0.08), 2000, Xva, hm._vol_target(va))
    sd_tr = np.sqrt(hm._var_from(tr, vb.predict(Xtr))); sd_va = np.sqrt(hm._var_from(va, vb.predict(Xva)))
    Xtr, Xva = mdl._X(tr, hm.dir_feats), mdl._X(va, hm.dir_feats)
    utr, uva = hm._drift_target(tr, sd_tr), hm._drift_target(va, sd_va)
    db = mdl._fit(Xtr, utr, dict(objective="regression", num_leaves=31, min_data_in_leaf=5000, lambda_l2=50.0), 3000, Xva, uva)
    m = db.predict(Xva)
    # simple scale calibration (from train residuals) for the structural above-K probability
    sc = np.sqrt(np.mean((tr[f"y_ret_{H}"].to_numpy() / sd_tr - db.predict(Xtr)) ** 2))
    z = (qK - m * sd_va) / (sd_va * sc)
    pK = special.ndtr(-z)
    pdir = special.ndtr(m / sc)
    r = {"ic": float(stats.spearmanr(m[nz], R[nz]).statistic),
         "dir_auc": M.auc((R[nz] > 0).astype(float), pdir[nz]),
         "above_ref_ll": M.logloss(yK, pK),
         "vol_qlike": M.qlike(va[f"y_rv5_{H}"].to_numpy(), (sd_va * sc) ** 2),
         "n_feats": len(feats), "iters_vol": vb.best_iteration, "iters_drift": db.best_iteration}
    if name == "all":
        # architecture check: ridge drift on standardized (winsorized) features
        sc_ = StandardScaler().fit(np.clip(Xtr, -1e6, 1e6))
        f = lambda X: np.clip(np.nan_to_num(sc_.transform(np.clip(X, -1e6, 1e6))), -6, 6)  # noqa: E731
        rr = Ridge(alpha=100.0).fit(f(Xtr), utr)
        mr = rr.predict(f(Xva))
        r["ridge_ic"] = float(stats.spearmanr(mr[nz], R[nz]).statistic)
        r["ridge_dir_auc"] = M.auc((R[nz] > 0).astype(float), mr[nz])
        imp = db.feature_importance("gain"); imp = imp / imp.sum()
        r["top_drift_features"] = {hm.dir_feats[i]: float(imp[i]) for i in np.argsort(-imp)[:20]}
    res[name] = r
    print(f"[{H}] {name:18s} ic={r['ic']:.4f} dirAUC={r['dir_auc']:.4f} aboveK_LL={r['above_ref_ll']:.5f} "
          f"qlike={r['vol_qlike']:.4f} ({time.time()-t0:.0f}s)", flush=True)
json.dump(res, open(out / f"ablation_{H}.json", "w"), indent=1)
