"""(1) slow BTC->ETH relative-value catch-up (gap over 30s..15min) for 30s..300s targets;
(2) does BTC volatility (and BTC-ETH vol ratio) help forecast ETH realised volatility?"""
import sys
import numpy as np

E = "data"; B = "data/xasset/BTCUSDT"


def load(root, kind, m):
    z = np.load(f"{root}/{kind}/{m}.npz"); return {k: z[k] for k in z.files}


def lr(c):
    x = np.zeros(len(c)); x[1:] = np.diff(np.log(c)); return np.nan_to_num(x)


def wsum(x, w):
    cs = np.r_[0, np.cumsum(x)]; t = np.arange(1, len(x) + 1)   # sum of x[t-w+1..t] (known at end of bar t)
    return cs[t] - cs[np.maximum(t - w, 0)]


def oos(y, X):
    X = np.column_stack([X, np.ones(len(y))])
    half = len(y) // 2
    w = np.linalg.lstsq(X[:half], y[:half], rcond=None)[0]
    p = X[half:] @ w
    return 1 - np.mean((y[half:] - p) ** 2) / np.var(y[half:]), np.corrcoef(p, y[half:])[0, 1]


for m in sys.argv[1:]:
    es, ef, bs, bf = load(E, "spot_1s", m), load(E, "fut_1s", m), load(B, "spot_1s", m), load(B, "fut_1s", m)
    N = min(len(es["c"]), len(bs["c"]))
    e = lr(es["c"][:N]); ep = lr(np.where(np.isfinite(ef["c"][:N]), ef["c"][:N], es["c"][:N]))
    bp = lr(np.where(np.isfinite(bf["c"][:N]), bf["c"][:N], bs["c"][:N]))
    beta = wsum(e * bp, 3600) / (wsum(bp * bp, 3600) + 1e-18)
    sig = np.sqrt(wsum(e * e, 3600) / 3600) + 1e-9
    idx = np.arange(7200, N - 300, 5)
    t = idx - 1                      # last known bar
    print(f"\n===== {m} =====")
    cs = np.r_[0, np.cumsum(e)]
    own = np.column_stack([wsum(e, k)[t] / (sig[t] * np.sqrt(k)) for k in (1, 3, 10, 30)] + [wsum(ep, k)[t] / (sig[t] * np.sqrt(k)) for k in (1, 3, 10)])
    gaps = np.column_stack([(beta[t] * wsum(bp, k)[t] - wsum(e, k)[t]) / (sig[t] * np.sqrt(k)) for k in (30, 60, 300, 900)])
    for h in (30, 60, 300):
        y = np.clip((cs[t + 1 + h] - cs[t + 1]) / (sig[t] * np.sqrt(h)), -8, 8)
        r0 = oos(y, own); r1 = oos(y, np.column_stack([own, gaps])); rg = oos(y, gaps)
        print(f"h={h:>3}s  own {r0[0]:.4f}/{r0[1]:.3f}   gaps-only {rg[0]:.4f}/{rg[1]:.3f}   own+gaps {r1[0]:.4f}/{r1[1]:.3f}")
    # volatility: log future RV(5s-sampled proxy: 1s RV) over 60/300s on own past RV vs + BTC RV
    for h in (60, 300):
        fut = np.log(np.array([np.sum(e[i:i + h] ** 2) for i in idx]) + 1e-14)
        Xo = np.column_stack([np.log(wsum(e * e, k)[t] / k + 1e-14) for k in (10, 60, 300, 3600)])
        Xb = np.column_stack([np.log(wsum(bp * bp, k)[t] / k + 1e-14) for k in (10, 60, 300, 3600)])
        r0 = oos(fut, Xo); r1 = oos(fut, np.column_stack([Xo, Xb]))
        print(f"vol h={h}s: R2 log-RV own {r0[0]:.4f}  own+BTC {r1[0]:.4f}")
