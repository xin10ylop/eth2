"""Architecture experiment: temporal CNN over raw 1-second sequences + engineered features.

Question: does a learned encoder of the last L seconds of raw spot/perp returns, basis and order flow find
directional information the gradient-boosted drift engine misses?

Protocol (validation period only; the test period is untouched):
  * target  u = R_h / sd_h  (sd_h from the trained main vol engine), clipped to +-6
  * train on a window-subsample of the training period, early-stop on half of validation (val-A),
    report IC on the other half (val-B), alone and blended with the main LightGBM drift forecast.

usage: python scripts/06_sequence_model.py --horizon 30 [--L 60] [--frac 0.1]
"""
import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, series as se  # noqa: E402
from ethmove.build import month_bounds  # noqa: E402
from ethmove.engine import Engine  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--horizon", default="30")
ap.add_argument("--L", type=int, default=60)
ap.add_argument("--frac", type=float, default=0.1)
ap.add_argument("--epochs", type=int, default=6)
ap.add_argument("--models", default="artifacts/models")
a = ap.parse_args()
H, L = a.horizon, a.L
torch.manual_seed(0); np.random.seed(0)
torch.set_num_threads(4)

eng = Engine.load(a.models)
hm = eng.models[H]


def sequences(df):
    """Raw channel windows [n, C, L] for the rows of df (decision at ts uses bars ts-L .. ts-1)."""
    out = np.zeros((len(df), 8, L), np.float32)
    ts = df["ts"].to_numpy()
    months = np.array([time.strftime("%Y-%m", time.gmtime(t)) for t in ts[:: 1]])
    for mo in np.unique(months):
        rows = np.where(months == mo)[0]
        ms, me = month_bounds(mo)
        lo = ms - 7200
        s = se.load_range(lo, me + 1)
        c = s["c"]; lc = np.log(c); lr = np.r_[0, np.diff(lc)]
        fc = np.where(np.isfinite(s["fc"]), s["fc"], c); lfc = np.log(fc); flr = np.r_[0, np.diff(lfc)]
        basis = lfc - lc
        bm = np.convolve(basis, np.ones(300) / 300, mode="full")[: len(basis)]  # causal 300s mean
        v = s["v"]; fv = s["fv"]
        vtyp = np.convolve(v, np.ones(3600) / 3600, mode="full")[: len(v)] + 1e-9
        fvtyp = np.convolve(fv, np.ones(3600) / 3600, mode="full")[: len(fv)] + 1e-9
        sv = (2 * s["tbv"] - v) / vtyp
        fsv = (2 * s["ftbv"] - fv) / fvtyp
        rng_ = (np.log(s["h"]) - np.log(s["l"]))
        lvol = np.log1p(v / vtyp)
        i = ts[rows] - lo
        sig = df["sig_ref"].to_numpy()[rows][:, None]
        J = i[:, None] - L + np.arange(L)[None, :]   # bars i-L .. i-1
        out[rows, 0] = lr[J] / sig
        out[rows, 1] = flr[J] / sig
        out[rows, 2] = (basis[J] - bm[i - 1][:, None]) / sig
        out[rows, 3] = np.clip(sv[J], -20, 20)
        out[rows, 4] = np.clip(fsv[J], -20, 20)
        out[rows, 5] = rng_[J] / sig
        out[rows, 6] = lvol[J]
        out[rows, 7] = (lc[J] - lc[i - 1][:, None]) / (sig * np.sqrt(L))
    return np.clip(np.nan_to_num(out), -30, 30)


def prep(split, frac, seed):
    df = data.load(split, frac=frac, seed=seed)
    df, S_ = eng.augment(df)
    s = S_[H]
    u = np.clip(df[f"y_ret_{H}"].to_numpy() / s["sd"], -6, 6).astype(np.float32)
    F = np.nan_to_num(df[hm.dir_feats].to_numpy(np.float32))
    return df, sequences(df), F, u, s["mz"]


class Net(nn.Module):
    def __init__(self, nf):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(8, 32, 5, padding=2), nn.GELU(),
            nn.Conv1d(32, 32, 5, padding=4, dilation=2), nn.GELU(),
            nn.Conv1d(32, 32, 5, padding=8, dilation=4), nn.GELU())
        self.dense = nn.Sequential(nn.Linear(nf, 128), nn.GELU(), nn.Dropout(0.1))
        self.head = nn.Sequential(nn.Linear(32 * 2 + 32 + 128, 128), nn.GELU(), nn.Dropout(0.1), nn.Linear(128, 1))
        self.last = nn.Linear(8 * 8, 32)

    def forward(self, x, f):
        h = self.conv(x)
        pooled = torch.cat([h.mean(-1), h[:, :, -8:].mean(-1)], 1)
        last = self.last(x[:, :, -8:].reshape(len(x), -1))
        return self.head(torch.cat([pooled, last, self.dense(f)], 1)).squeeze(-1)


t0 = time.time()
tr_df, Xs_tr, F_tr, u_tr, m_tr = prep("train", a.frac, 11)
va_df, Xs_va, F_va, u_va, m_va = prep("val", 0.6, 12)
print(f"train {len(u_tr):,} val {len(u_va):,} ({time.time()-t0:.0f}s)", flush=True)
mu_f, sd_f = F_tr.mean(0), F_tr.std(0) + 1e-6
F_tr = np.clip((F_tr - mu_f) / sd_f, -8, 8); F_va = np.clip((F_va - mu_f) / sd_f, -8, 8)
# split validation by day into A (early stopping) / B (reporting)
day = va_df["ts"].to_numpy() // 86400
A = (day % 2) == 0
B = ~A

net = Net(F_tr.shape[1])
opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
Xt, Ft, ut = map(torch.from_numpy, (Xs_tr, F_tr, u_tr))
Xv, Fv = torch.from_numpy(Xs_va), torch.from_numpy(F_va)


def predict(X, F):
    net.eval(); out = []
    with torch.no_grad():
        for k in range(0, len(X), 8192):
            out.append(net(X[k:k + 8192], F[k:k + 8192]).numpy())
    net.train()
    return np.concatenate(out)


best = (-1, None, None)
for ep in range(a.epochs):
    perm = torch.randperm(len(ut))
    tl = 0
    for k in range(0, len(perm), 2048):
        b = perm[k:k + 2048]
        loss = ((net(Xt[b], Ft[b]) - ut[b]) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step(); tl += loss.item() * len(b)
    pv = predict(Xv, Fv)
    icA = stats.spearmanr(pv[A], u_va[A]).statistic
    print(f"epoch {ep} train_mse={tl/len(ut):.4f} val-A IC={icA:.4f} ({time.time()-t0:.0f}s)", flush=True)
    if icA > best[0]:
        best = (icA, pv.copy(), ep)

pv = best[1]
R = va_df[f"y_ret_{H}"].to_numpy()
res = {"horizon": H, "L": L, "n_train": int(len(u_tr)), "best_epoch": best[2]}
for name, p in (("lgbm_drift", m_va), ("cnn", pv)):
    res[f"ic_B_{name}"] = float(stats.spearmanr(p[B], R[B]).statistic)
# blend weight chosen on A, evaluated on B
zs = lambda x, m: (x - x[m].mean()) / x[m].std()  # noqa: E731
best_w, best_ic = 0, -1
for w in np.linspace(0, 1, 11):
    ic = stats.spearmanr((1 - w) * zs(m_va, A)[A] + w * zs(pv, A)[A], R[A]).statistic
    if ic > best_ic:
        best_w, best_ic = w, ic
blend = (1 - best_w) * zs(m_va, A) + best_w * zs(pv, A)
res["blend_w_cnn"] = float(best_w)
res["ic_B_blend"] = float(stats.spearmanr(blend[B], R[B]).statistic)
res["corr_cnn_lgbm"] = float(np.corrcoef(pv, m_va)[0, 1])
print(json.dumps(res, indent=1))
Path("artifacts/ablation").mkdir(parents=True, exist_ok=True)
json.dump(res, open(f"artifacts/ablation/sequence_cnn_{H}.json", "w"), indent=1)
