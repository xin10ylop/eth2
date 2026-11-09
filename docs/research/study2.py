"""(1) ETH vs BTC predictability with the identical linear protocol; (2) value of staleness-aware catch-up features."""
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


@njit(cache=True)
def stale(n):
    """seconds since the last bar with trades, as known at the end of bar t"""
    out = np.zeros(len(n)); s = 0.0
    for t in range(len(n)):
        s = 0.0 if n[t] > 0 else s + 1.0
        out[t] = s
    return out


def oos(y, cols, sig, N, h):
    X = np.column_stack([c_ for c_ in cols] + [np.ones(N)])
    half = N // 2
    sl = slice(3600, half); te = slice(half + 3600, N - h)
    w = np.linalg.lstsq(X[sl], y[sl], rcond=None)[0]
    p = X[te] @ w
    return 1 - np.mean((y[te] - p) ** 2) / np.mean((y[te] - y[te].mean()) ** 2), np.corrcoef(p, y[te])[0, 1]


def own_block(s, f):
    N = len(s["c"])
    e = lr(s["c"]); fc = np.where(np.isfinite(f["c"][:N]), f["c"][:N], s["c"]); ep = lr(fc)
    basis = np.log(fc) - np.log(s["c"]); bdev = basis - np.convolve(basis, np.ones(300) / 300, "full")[:N]
    return e, ep, [agg(e, 1, 1), agg(e, 2, 3), agg(e, 4, 10), agg(ep, 1, 1), agg(ep, 2, 3), agg(ep, 4, 10), np.r_[0, bdev[:-1]]], fc


for m in sys.argv[1:]:
    es, ef, bs, bf = load(E, "spot_1s", m), load(E, "fut_1s", m), load(B, "spot_1s", m), load(B, "fut_1s", m)
    N = min(len(es["c"]), len(bs["c"]))
    es = {k: v[:N] for k, v in es.items()}; bs = {k: v[:N] for k, v in bs.items()}
    e, ep, own_e, efc = own_block(es, ef)
    b, bp, own_b, bfc = own_block(bs, bf)
    sig_e = np.sqrt(np.convolve(e * e, np.ones(3600) / 3600, "full")[:N]) + 1e-9
    sig_b = np.sqrt(np.convolve(b * b, np.ones(3600) / 3600, "full")[:N]) + 1e-9
    # staleness-aware catch-up: perp (and BTC) move since the last ETH spot trade, lagged so it is known at t
    st = stale(es["n"].astype(np.float64))
    lastc = np.zeros(N, dtype=np.int64)          # index of last traded bar
    j = 0
    for t in range(N):
        if es["n"][t] > 0:
            j = t
        lastc[t] = j
    lef = np.log(efc); lbf = np.log(bfc)
    perp_since = np.r_[0, (lef - lef[lastc])[:-1]]
    btc_since = np.r_[0, (lbf - lbf[lastc])[:-1]]
    st_l = np.r_[0, st[:-1]]
    stale_feats = [perp_since, btc_since, perp_since * np.minimum(st_l, 10), btc_since * np.minimum(st_l, 10)]
    print(f"\n===== {m} =====")
    for h in (1, 5, 10, 30, 60):
        cs = np.r_[0, np.cumsum(e)]; ye = np.clip((cs[np.minimum(np.arange(N) + h, N)] - cs[np.arange(N)]) / (sig_e * np.sqrt(h)), -8, 8)
        cs = np.r_[0, np.cumsum(b)]; yb = np.clip((cs[np.minimum(np.arange(N) + h, N)] - cs[np.arange(N)]) / (sig_b * np.sqrt(h)), -8, 8)
        bt_for_e = [agg(bp, 1, 1), agg(bp, 2, 3), agg(bp, 4, 10), agg(b, 1, 1), agg(b, 2, 3), agg(b, 4, 10)]
        r_b = oos(yb, [c_ / sig_b for c_ in own_b], sig_b, N, h)
        r_e = oos(ye, [c_ / sig_e for c_ in own_e], sig_e, N, h)
        r_eb = oos(ye, [c_ / sig_e for c_ in own_e + bt_for_e], sig_e, N, h)
        r_ebs = oos(ye, [c_ / sig_e for c_ in own_e + bt_for_e + stale_feats], sig_e, N, h)
        print(f"h={h:>2}s  BTC own {r_b[0]:.4f}/{r_b[1]:.3f} | ETH own {r_e[0]:.4f}/{r_e[1]:.3f}  +BTC {r_eb[0]:.4f}/{r_eb[1]:.3f}  +BTC+stale {r_ebs[0]:.4f}/{r_ebs[1]:.3f}")
