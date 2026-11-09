"""Regime-sliced out-of-sample evaluation: does the edge survive in every market regime?

Slices are defined by *causal* regime variables with thresholds fixed on the TRAINING period, so the same
definitions apply to any test period.  For each slice and horizon: naive / structural / full log loss, the
improvement with a day-block bootstrap CI, AUC and calibration; plus pure-direction AUC for 30s.

usage: python scripts/14_regime_eval.py [--models artifacts/models] [--split test] [--dates ...]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import special

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, metrics as M  # noqa: E402
from ethmove.engine import Engine  # noqa: E402
from ethmove.model import hlen  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--models", default="artifacts/models")
ap.add_argument("--split", default="test")
ap.add_argument("--dates", default="")
ap.add_argument("--boot", type=int, default=300)
a = ap.parse_args()
splits = data.SPLITS
if a.dates:
    d0, d1, d2, d3 = a.dates.split(",")
    splits = {"train": (d0, d1), "val": (d1, d2), "test": (d2, d3)}

# thresholds from the training period (causal regime variables)
cols = ["ts", "rg_lvol7", "rg_trend7", "rg_dd30", "rg_volratio", "lrv_3600"]
trq = data.load("train", frac=0.05, seed=9, splits=splits)
Q = {c: np.nanquantile(trq[c].to_numpy(), [1 / 3, 2 / 3]) for c in ("rg_lvol7", "rg_trend7", "lrv_3600")}
df = data.load(a.split, splits=splits)
eng = Engine.load(a.models)
df, S_ = eng.augment(df)
day = df["ts"].to_numpy() // 86400
dow = ((day + 3) % 7)


def terc(c, names):
    v = df[c].to_numpy()
    return {names[0]: v <= Q[c][0], names[1]: (v > Q[c][0]) & (v <= Q[c][1]), names[2]: v > Q[c][1]}


slices = {"all": {"all": np.ones(len(df), bool)}}
slices["volatility regime (7-day)"] = terc("rg_lvol7", ["calm", "normal", "turbulent"])
slices["trend regime (7-day)"] = terc("rg_trend7", ["bear", "sideways", "bull"])
slices["drawdown from 30-day high"] = {"deep (< -3 daily sd)": df["rg_dd30"].to_numpy() < -3,
                                       "shallow": df["rg_dd30"].to_numpy() >= -3}
slices["vol expansion (7d vs 30d)"] = {"expanding (> +0.3)": df["rg_volratio"].to_numpy() > 0.3,
                                       "stable/contracting": df["rg_volratio"].to_numpy() <= 0.3}
slices["intraday activity (1-hour vol)"] = terc("lrv_3600", ["quiet hour", "normal hour", "hot hour"])
slices["calendar"] = {"weekday": dow < 5, "weekend": dow >= 5}

P = {}
for H, hm in eng.models.items():
    s = S_[H]
    y = hm._d1_target(df)
    pf, ps = hm.predict_above(df, s)
    qK = np.log(df["K"].to_numpy() / df["S"].to_numpy())
    pn = special.ndtr(-qK / (np.sqrt(np.exp(df["lrv_300"].to_numpy(np.float64)) * hlen(df, H)) + 1e-12))
    within = (df["e"].to_numpy() + hlen(df, H) <= 300) if H != "T" else np.ones(len(df), bool)
    P[H] = (y, pf, ps, pn, within)
R30 = df["y_ret_30"].to_numpy()
pdir, _ = eng.models["30"].predict_cdf(df, np.full(len(df), 1e-12), s=S_["30"])

out = {}
md = [f"# Regime-sliced results — `{a.split}` {splits[a.split]} — models `{a.models}`\n",
      "Thresholds for the regime variables are fixed on the training period. Δ = log-loss improvement of the full "
      "model over the naive random walk, in millinats per decision, with a 95% day-block bootstrap CI.\n"]
for fam, sl in slices.items():
    md.append(f"\n## {fam}\n")
    extra = [h for h in ("15", "10") if h in P]
    md.append("| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | " + "".join(f"{h}s Δ | " for h in extra) + "30s dir. AUC |")
    md.append("|---|---|---|---|---|---|---|---|" + "---|" * len(extra) + "---|")
    for name, m0 in sl.items():
        r = {"windows": int(len(np.unique(df["ts"].to_numpy()[m0] // 300)))}
        if r["windows"] < 200:
            continue
        cells = []
        for H in [h for h in ("T", "60", "30", "15", "10") if h in P]:
            y, pf, ps, pn, within = P[H]
            m = m0 & within
            mean, lo, hi, _ = M.block_bootstrap_diff(M.ll_vec(y[m], pn[m]), M.ll_vec(y[m], pf[m]), day[m], a.boot)
            r[H] = {"naive": M.logloss(y[m], pn[m]), "structural": M.logloss(y[m], ps[m]), "full": M.logloss(y[m], pf[m]),
                    "dll": mean, "ci": [lo, hi], "auc": M.auc(y[m], pf[m]), "ece": M.ece(y[m], pf[m])}
            cells.append(r[H])
        nz = m0 & (R30 != 0)
        r["dir_auc_30"] = M.auc((R30[nz] > 0).astype(float), pdir[nz])
        out.setdefault(fam, {})[name] = r
        t, s1, s3 = r["T"], r["60"], r["30"]
        md.append(f"| {name} | {r['windows']:,} | {t['naive']:.4f} → {t['full']:.4f} | {t['dll']*1e3:+.1f} [{t['ci'][0]*1e3:+.1f}, {t['ci'][1]*1e3:+.1f}] | "
                  f"{t['auc']:.3f} | {t['ece']:.4f} | {s1['dll']*1e3:+.1f} | {s3['dll']*1e3:+.1f} | "
                  + "".join(f"{r[h]['dll']*1e3:+.1f} | " for h in extra) + f"{r['dir_auc_30']:.3f} |")
tag = Path(a.models).name + "_" + a.split
Path("artifacts/regime").mkdir(parents=True, exist_ok=True)
json.dump(out, open(f"artifacts/regime/regime_eval_{tag}.json", "w"), indent=1, default=float)
Path(f"artifacts/regime/regime_eval_{tag}.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
