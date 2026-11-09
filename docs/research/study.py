"""ETH microstructure study: staleness, autocorrelation, perp->spot and BTC->ETH lead-lag, incremental
predictability of BTC beyond ETH's own perp, variance ratios.  Usage: python study.py 2024-06 [2024-09 ...]"""
import sys
import numpy as np

E = "data"; B = "data/xasset/BTCUSDT"


def load(root, kind, m):
    z = np.load(f"{root}/{kind}/{m}.npz")
    return {k: z[k] for k in z.files}


def lr(c):
    x = np.zeros(len(c)); x[1:] = np.diff(np.log(c)); return np.nan_to_num(x)


def agg(x, a, b):
    """sum of x over lags a..b (x shifted so value at t uses x[t-a] .. x[t-b])"""
    cs = np.r_[0, np.cumsum(x)]
    t = np.arange(len(x))
    lo = np.clip(t - b, 0, None); hi = np.clip(t - a + 1, 0, None)
    return cs[hi] - cs[lo]


for m in sys.argv[1:]:
    es, ef, bs, bf = load(E, "spot_1s", m), load(E, "fut_1s", m), load(B, "spot_1s", m), load(B, "fut_1s", m)
    N = min(len(es["c"]), len(bs["c"]))
    e, ep, b, bp = lr(es["c"][:N]), lr(np.where(np.isfinite(ef["c"][:N]), ef["c"][:N], es["c"][:N])), lr(bs["c"][:N]), lr(np.where(np.isfinite(bf["c"][:N]), bf["c"][:N], bs["c"][:N]))
    print(f"\n===== {m} =====  ETH stale seconds (no trade): {np.mean(es['n'][:N]==0):.3f}   BTC: {np.mean(bs['n'][:N]==0):.3f}")
    print("ACF ETH spot :", " ".join(f"{k}:{np.corrcoef(e[:-k], e[k:])[0,1]:.3f}" for k in (1, 2, 3, 5, 10, 30)))
    print("ACF BTC spot :", " ".join(f"{k}:{np.corrcoef(b[:-k], b[k:])[0,1]:.3f}" for k in (1, 2, 3, 5, 10, 30)))
    for name, x in (("ETH perp", ep), ("BTC spot", b), ("BTC perp", bp)):
        print(f"corr(ETH spot_t, {name}_t-k):", " ".join(f"{k}:{np.corrcoef(e[k:], x[:N-k])[0,1]:.3f}" for k in range(0, 8)))
    print("corr(BTC perp_t, ETH perp_t-k):", " ".join(f"{k}:{np.corrcoef(bp[k:], ep[:N-k])[0,1]:.3f}" for k in range(1, 5)),
          "| corr(ETH perp_t, BTC perp_t-k):", " ".join(f"{k}:{np.corrcoef(ep[k:], bp[:N-k])[0,1]:.3f}" for k in range(1, 5)))
    # predictive regressions, forward returns h, fit first half / test second half
    basis = np.log(np.where(np.isfinite(ef["c"][:N]), ef["c"][:N], es["c"][:N])) - np.log(es["c"][:N])
    bdev = basis - np.convolve(basis, np.ones(300) / 300, "full")[:N]
    bb = np.log(np.where(np.isfinite(bf["c"][:N]), bf["c"][:N], bs["c"][:N])) - np.log(bs["c"][:N])
    bbdev = bb - np.convolve(bb, np.ones(300) / 300, "full")[:N]
    own = [agg(e, 1, 1), agg(e, 2, 3), agg(e, 4, 10), agg(ep, 1, 1), agg(ep, 2, 3), agg(ep, 4, 10), np.r_[0, bdev[:-1]]]
    btc = [agg(bp, 1, 1), agg(bp, 2, 3), agg(bp, 4, 10), agg(b, 1, 1), agg(b, 2, 3), agg(b, 4, 10), np.r_[0, bbdev[:-1]]]
    sig = np.sqrt(np.convolve(e * e, np.ones(3600) / 3600, "full")[:N]) + 1e-9
    half = N // 2
    for h in (1, 5, 10, 30, 60):
        cs = np.r_[0, np.cumsum(e)]
        y = (cs[np.minimum(np.arange(N) + h, N)] - cs[np.arange(N)]) / (sig * np.sqrt(h))   # forward return t+1..t+h
        y = np.clip(y, -8, 8)
        res = {}
        for nm, cols in (("own", own), ("btc_only", btc), ("own+btc", own + btc)):
            X = np.column_stack([c_ / sig for c_ in cols] + [np.ones(N)])
            sl = slice(3600, half); te = slice(half + 3600, N - h)
            w = np.linalg.lstsq(X[sl], y[sl], rcond=None)[0]
            p = X[te] @ w
            res[nm] = (1 - np.mean((y[te] - p) ** 2) / np.mean((y[te] - y[te].mean()) ** 2), np.corrcoef(p, y[te])[0, 1])
        print(f"h={h:>2}s  OOS R2/IC  own {res['own'][0]:.4f}/{res['own'][1]:.3f}   btc-only {res['btc_only'][0]:.4f}/{res['btc_only'][1]:.3f}   own+btc {res['own+btc'][0]:.4f}/{res['own+btc'][1]:.3f}")
    # variance ratios (which RV sampling matches the variance of h-second returns)
    for h in (30, 60, 300):
        idx = np.arange(3600, N - h, 7)
        cs = np.r_[0, np.cumsum(e)]
        R = cs[idx + h] - cs[idx]
        out = [f"h={h}: E[R^2]/E[RV_k]"]
        lc = np.log(es["c"][:N])
        for k in (1, 2, 5, 10):
            rv = np.zeros(len(idx))
            for j in range(0, h, k):
                rv += (lc[np.minimum(idx + j + k, idx + h)] - lc[idx + j]) ** 2
            out.append(f"k={k}:{np.mean(R**2)/np.mean(rv):.2f}")
        print("  ".join(out))
    # beta / correlation of 1s returns
    print(f"1s corr ETH-BTC spot {np.corrcoef(e, b)[0,1]:.3f}  perp {np.corrcoef(ep, bp)[0,1]:.3f}   beta(ETH spot on BTC perp) {np.cov(e, bp)[0,1]/np.var(bp):.2f}   vol ratio ETH/BTC {np.std(e)/np.std(b):.2f}")
