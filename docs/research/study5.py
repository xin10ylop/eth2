"""Do explicit BTC-shock features add to own + generic BTC features (identical OOS protocol as study2)?
shock_t = BTC-perp 1s return / its 1h sd, kept only when |z| > 3; exponentially decayed signed sums (hl 2/10/30 s)
of shocks, and perp-based beta gaps over 1/3/10/30 s."""
import sys
import numpy as np
from numba import njit

E = "data"; B = "data/xasset/BTCUSDT"


def load(root, kind, m):
    z = np.load(f"{root}/{kind}/{m}.npz"); return {k: z[k] for k in z.files}


def lr(c):
    x = np.zeros(len(c)); x[1:] = np.diff(np.log(c)); return np.nan_to_num(x)


def agg(x, a, b):
    cs = np.r_[0, np.cumsum(x)]; t = np.arange(len(x))
    return cs[np.clip(t - a + 1, 0, None)] - cs[np.clip(t - b, 0, None)]


def wsum(x, w):
    cs = np.r_[0, np.cumsum(x)]; t = np.arange(1, len(x) + 1)
    return cs[t] - cs[np.maximum(t - w, 0)]


@njit(cache=True)
def ewm(x, hl):
    a = 1 - 0.5 ** (1 / hl); out = np.empty(len(x)); s = 0.0
    for i in range(len(x)):
        s = s + a * (x[i] - s); out[i] = s
    return out


def oos(y, cols, N, h):
    X = np.column_stack(cols + [np.ones(N)]); half = N // 2
    sl = slice(3600, half); te = slice(half + 3600, N - h)
    w = np.linalg.lstsq(X[sl], y[sl], rcond=None)[0]; p = X[te] @ w
    return np.corrcoef(p, y[te])[0, 1]


for m in sys.argv[1:]:
    es, ef, bs, bf = load(E, "spot_1s", m), load(E, "fut_1s", m), load(B, "spot_1s", m), load(B, "fut_1s", m)
    N = min(len(es["c"]), len(bs["c"]))
    e = lr(es["c"][:N]); b = lr(bs["c"][:N])
    efc = np.where(np.isfinite(ef["c"][:N]), ef["c"][:N], es["c"][:N]); ep = lr(efc)
    bp = lr(np.where(np.isfinite(bf["c"][:N]), bf["c"][:N], bs["c"][:N]))
    basis = np.log(efc) - np.log(es["c"][:N]); bdev = basis - np.convolve(basis, np.ones(300) / 300, "full")[:N]
    sig = np.sqrt(np.convolve(e * e, np.ones(3600) / 3600, "full")[:N]) + 1e-9
    own = [agg(e, 1, 1), agg(e, 2, 3), agg(e, 4, 10), agg(ep, 1, 1), agg(ep, 2, 3), agg(ep, 4, 10), np.r_[0, bdev[:-1]]]
    btc = [agg(bp, 1, 1), agg(bp, 2, 3), agg(bp, 4, 10), agg(b, 1, 1), agg(b, 2, 3), agg(b, 4, 10)]
    sdb = np.sqrt(wsum(bp * bp, 3600) / 3600) + 1e-12
    z = bp / np.r_[sdb[0], sdb[:-1]]
    shock = np.where(np.abs(z) > 3, np.clip(z, -20, 20), 0.0)
    beta = wsum(e * bp, 3600) / (wsum(bp * bp, 3600) + 1e-18)
    shocks = [np.r_[0, ewm(shock, hl)[:-1]] for hl in (2.0, 10.0, 30.0)]
    gaps = [np.r_[0, (beta * wsum(bp, k) - wsum(e, k))[:-1]] / (sig * np.sqrt(k)) for k in (1, 3, 10, 30)]
    print(f"\n===== {m} =====  shock seconds: {np.mean(shock != 0):.3%}")
    for h in (1, 5, 10, 30, 60):
        cs = np.r_[0, np.cumsum(e)]
        y = np.clip((cs[np.minimum(np.arange(N) + h, N)] - cs[np.arange(N)]) / (sig * np.sqrt(h)), -8, 8)
        base = [c_ / sig for c_ in own + btc]
        i0 = oos(y, base, N, h)
        i1 = oos(y, base + shocks, N, h)
        i2 = oos(y, base + shocks + gaps, N, h)
        # conditional on a recent shock (last 10 s): IC inside shock regimes only
        print(f"h={h:>2}s  own+BTC {i0:.3f}   +shock {i1:.3f}   +shock+perp-gaps {i2:.3f}")
