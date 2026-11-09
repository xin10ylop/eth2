"""Where (if anywhere) is ETH more predictable than BTC?  Identical protocol for both assets.
(b) volatility: OOS R2 of log future RV (30/60/300 s) from a HAR-style regression on own RV (+ the other asset)
(c) event study: after large leader moves (|BTC perp 1s| > 4 sd), how much of the beta-implied move ETH spot
    has NOT yet made at t, and how much of it arrives over the next 1..30 s (vs ETH perp shocks for comparison)
(d) mean reversion: autocorrelation of 1-min and 5-min returns; reversal after flow-driven 1-min moves"""
import sys
import numpy as np

E = "data"; B = "data/xasset/BTCUSDT"


def load(root, kind, m):
    z = np.load(f"{root}/{kind}/{m}.npz"); return {k: z[k] for k in z.files}


def lr(c):
    x = np.zeros(len(c)); x[1:] = np.diff(np.log(c)); return np.nan_to_num(x)


def wsum(x, w):
    cs = np.r_[0, np.cumsum(x)]; t = np.arange(1, len(x) + 1)
    return cs[t] - cs[np.maximum(t - w, 0)]


def oos(y, X):
    X = np.column_stack([X, np.ones(len(y))]); half = len(y) // 2
    w = np.linalg.lstsq(X[:half], y[:half], rcond=None)[0]; p = X[half:] @ w
    return 1 - np.mean((y[half:] - p) ** 2) / np.var(y[half:]), p, y[half:]


for m in sys.argv[1:]:
    es, ef, bs, bf = load(E, "spot_1s", m), load(E, "fut_1s", m), load(B, "spot_1s", m), load(B, "fut_1s", m)
    N = min(len(es["c"]), len(bs["c"]))
    e = lr(es["c"][:N]); b = lr(bs["c"][:N])
    ep = lr(np.where(np.isfinite(ef["c"][:N]), ef["c"][:N], es["c"][:N]))
    bp = lr(np.where(np.isfinite(bf["c"][:N]), bf["c"][:N], bs["c"][:N]))
    idx = np.arange(7200, N - 300, 7); t = idx - 1
    print(f"\n===== {m} =====")
    # (b) volatility predictability (5s-sampled future RV, HAR inputs)
    for h in (30, 60, 300):
        row = []
        for nm, x, z in (("ETH", e, bp), ("BTC", b, ep)):
            cs = np.r_[0, np.cumsum(x)]
            fut = np.zeros(len(idx))
            for j in range(0, h, 5):
                fut += (cs[idx + min(j + 5, h)] - cs[idx + j]) ** 2
            y = np.log(fut + 1e-14)
            Xo = np.column_stack([np.log(wsum(x * x, k)[t] / k + 1e-14) for k in (10, 60, 300, 3600, 14400)])
            r2, p, yy = oos(y, Xo)
            r2x, _, _ = oos(y, np.column_stack([Xo, np.log(wsum(z * z, 300)[t] / 300 + 1e-14), np.log(wsum(z * z, 60)[t] / 60 + 1e-14)]))
            row.append(f"{nm} R2 {r2:.3f} (+other asset {r2x:.3f})")
        print(f"vol h={h:>3}s  " + "   ".join(row))
    # (c) event study after large BTC perp seconds
    sd = np.sqrt(wsum(bp * bp, 3600) / 3600) + 1e-12
    beta = wsum(e * bp, 3600) / (wsum(bp * bp, 3600) + 1e-18)
    ev = np.where((np.abs(bp) > 4 * np.r_[sd[0], sd[:-1]]) & (np.arange(N) > 7200) & (np.arange(N) < N - 60))[0]
    if len(ev) > 50:
        s = np.sign(bp[ev])
        implied = beta[ev - 1] * bp[ev]                          # beta-implied ETH move for the shock second
        done0 = e[ev]                                            # ETH spot move in the same second
        cs = np.r_[0, np.cumsum(e)]
        line = f"BTC-perp shocks n={len(ev)}: ETH spot same-second {np.mean(done0 * s) / np.mean(implied * s):.0%} of beta-implied move;"
        for k in (1, 3, 10, 30):
            later = cs[ev + 1 + k] - cs[ev + 1]
            line += f" next {k}s +{np.mean(later * s) / np.mean(implied * s):.0%}"
        print(line)
    sd_e = np.sqrt(wsum(ep * ep, 3600) / 3600) + 1e-12
    ev2 = np.where((np.abs(ep) > 4 * np.r_[sd_e[0], sd_e[:-1]]) & (np.arange(N) > 7200) & (np.arange(N) < N - 60))[0]
    if len(ev2) > 50:
        s = np.sign(ep[ev2]); cs = np.r_[0, np.cumsum(e)]
        line = f"ETH-perp shocks n={len(ev2)}: ETH spot same-second {np.mean(e[ev2]*s)/np.mean(ep[ev2]*s):.0%} of perp move;"
        for k in (1, 3, 10, 30):
            line += f" next {k}s +{np.mean((cs[ev2+1+k]-cs[ev2+1])*s)/np.mean(ep[ev2]*s):.0%}"
        print(line)
    # same for BTC spot vs BTC perp shocks (BTC's own lag)
    sd_b = np.sqrt(wsum(bp * bp, 3600) / 3600) + 1e-12
    ev3 = np.where((np.abs(bp) > 4 * np.r_[sd_b[0], sd_b[:-1]]) & (np.arange(N) > 7200) & (np.arange(N) < N - 60))[0]
    if len(ev3) > 50:
        s = np.sign(bp[ev3]); cs = np.r_[0, np.cumsum(b)]
        line = f"BTC: spot vs own-perp shocks n={len(ev3)}: same-second {np.mean(b[ev3]*s)/np.mean(bp[ev3]*s):.0%};"
        for k in (1, 3, 10, 30):
            line += f" next {k}s +{np.mean((cs[ev3+1+k]-cs[ev3+1])*s)/np.mean(bp[ev3]*s):.0%}"
        print(line)
    # (d) mean reversion at minute scales
    for nm, x in (("ETH", e), ("BTC", b)):
        r1 = x[: N // 60 * 60].reshape(-1, 60).sum(1); r5 = x[: N // 300 * 300].reshape(-1, 300).sum(1)
        print(f"{nm}: ACF 1-min {np.corrcoef(r1[:-1], r1[1:])[0,1]:+.3f}  5-min {np.corrcoef(r5[:-1], r5[1:])[0,1]:+.3f}  "
              f"sign-reversal 5-min {np.mean(np.sign(r5[:-1]) != np.sign(r5[1:])):.3f}")
