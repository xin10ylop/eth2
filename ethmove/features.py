"""Causal feature engine and targets.

Conventions (critical for avoiding look-ahead):
  * Bar j covers second [ts_j, ts_j + 1).  A decision at index i happens at the *start* of second i,
    so only bars j <= i-1 are known.  The current price is S_i = close[i-1].
  * The 5-minute window containing i starts at i0 = i - (ts_i mod 300).  Its reference price
    K = open[i0] (first trade of the window) is fixed for the whole window and known from the window
    open.  Elapsed e = i - i0 in [0, 300), remaining tau = 300 - e seconds.
  * The window outcome is close[i0 + 299] (last trade of the 5-minute candle).

Every feature below is a function of bars < i (plus K).  `tests/test_no_lookahead.py` verifies this
by perturbing all data at indices >= i and checking that features at i are bit-identical.
"""
from __future__ import annotations

import numpy as np
from numba import njit

from .config import ROUND_UNITS

WIN = 300
EPS = 1e-12


# ----------------------------------------------------------------------------------------------
# numba kernels
# ----------------------------------------------------------------------------------------------
@njit(cache=True)
def ewm_before(x, hl):
    """out[i] = EWMA of x[0..i-1] (strictly before i); half-life `hl` in samples. out[0] = x[0]."""
    n = len(x)
    a = 1.0 - 0.5 ** (1.0 / hl)
    out = np.empty(n)
    out[0] = x[0]
    s = x[0]
    for i in range(1, n):
        out[i] = s            # s summarises x[0..i-1]
        s = s + a * (x[i] - s)
    return out


@njit(cache=True)
def rolling_max_before(x, w):
    """out[i] = max(x[i-w .. i-1]) via monotone deque. out[0]=x[0]."""
    n = len(x)
    out = np.empty(n)
    dq = np.empty(n, dtype=np.int64)
    head = 0
    tail = 0
    out[0] = x[0]
    for i in range(1, n):
        j = i - 1
        while tail > head and x[dq[tail - 1]] <= x[j]:
            tail -= 1
        dq[tail] = j
        tail += 1
        while dq[head] < i - w:
            head += 1
        out[i] = x[dq[head]]
    return out


@njit(cache=True)
def window_state(c, h, l, lr2, sv, v, K, i0s, idx):
    """Path statistics of the current window up to (not including) bar i, for each sample index.

    Returns arrays: run_hi, run_lo (log rel. K), frac_above, n_cross, t_since_cross, rv_win, ofi_win,
    t_since_hi, t_since_lo.
    """
    m = len(idx)
    run_hi = np.zeros(m); run_lo = np.zeros(m); frac_above = np.full(m, 0.5)
    n_cross = np.zeros(m); t_since_cross = np.zeros(m); rv_win = np.zeros(m); ofi_win = np.zeros(m)
    t_since_hi = np.zeros(m); t_since_lo = np.zeros(m)
    for s in range(m):
        i = idx[s]
        i0 = i0s[s]
        k = K[s]
        lk = np.log(k)
        hi = 0.0
        lo = 0.0
        above = 0
        nc = 0
        last_side = 0
        last_cross = i0
        rv = 0.0
        svs = 0.0
        vs = 0.0
        ihi = i0
        ilo = i0
        for j in range(i0, i):
            a = np.log(h[j]) - lk
            b = np.log(l[j]) - lk
            if a > hi:
                hi = a
                ihi = j
            if b < lo:
                lo = b
                ilo = j
            side = 1 if c[j] >= k else -1
            if side == 1:
                above += 1
            if last_side != 0 and side != last_side:
                nc += 1
                last_cross = j
            last_side = side
            rv += lr2[j]
            svs += sv[j]
            vs += v[j]
        e = i - i0
        run_hi[s] = hi
        run_lo[s] = lo
        if e > 0:
            frac_above[s] = above / e
            ofi_win[s] = svs / (vs + 1e-9)
        n_cross[s] = nc
        t_since_cross[s] = i - last_cross
        rv_win[s] = rv
        t_since_hi[s] = i - ihi
        t_since_lo[s] = i - ilo
    return run_hi, run_lo, frac_above, n_cross, t_since_cross, rv_win, ofi_win, t_since_hi, t_since_lo


@njit(cache=True)
def future_targets(c, h, l, lr2, idx, i_end_win, horizons, deltas, maxh):
    """Forward-looking targets (ONLY used as labels, never as features).

    For each sample i (current price S=c[i-1]):
      ret[h]   log(c[i-1+h]/S) for h in horizons, and to window close (last column)
      rv[h]    sum lr2[i .. i-1+h]
      hi[h]/lo[h]  max log(high)/min log(low) over bars i..i-1+h, relative to log S
      tup[d]/tdn[d] first-passage times (seconds, 1-based) of +/- delta (log) from S, searching up to maxh
                    bars ahead; maxh+1 if never.
    """
    m = len(idx)
    H = len(horizons)
    D = len(deltas)
    ret = np.zeros((m, H + 1)); rv = np.zeros((m, H + 1)); hi = np.zeros((m, H + 1)); lo = np.zeros((m, H + 1))
    rv5 = np.zeros((m, H + 1))
    tup = np.full((m, D), maxh + 1, dtype=np.int16)
    tdn = np.full((m, D), maxh + 1, dtype=np.int16)
    for s in range(m):
        i = idx[s]
        ls = np.log(c[i - 1])
        # all horizons incl. window close
        for q in range(H + 1):
            hh = horizons[q] if q < H else i_end_win[s] - i + 1
            mx = -1e9
            mn = 1e9
            r2 = 0.0
            for j in range(i, i + hh):
                a = np.log(h[j])
                b = np.log(l[j])
                if a > mx:
                    mx = a
                if b < mn:
                    mn = b
                r2 += lr2[j]
            ret[s, q] = np.log(c[i - 1 + hh]) - ls
            rv[s, q] = r2
            # 5-second-sampled realised variance (absorbs the short-lag autocorrelation of 1s returns)
            acc = 0.0
            prev = ls
            j = 5
            while j < hh:
                cur = np.log(c[i - 1 + j])
                acc += (cur - prev) ** 2
                prev = cur
                j += 5
            cur = np.log(c[i - 1 + hh])
            acc += (cur - prev) ** 2
            rv5[s, q] = acc
            hi[s, q] = mx - ls
            lo[s, q] = mn - ls
        for d in range(D):
            up = ls + deltas[d]
            dn = ls - deltas[d]
            fu = maxh + 1
            fd = maxh + 1
            for j in range(i, i + maxh):
                if fu > maxh and np.log(h[j]) >= up:
                    fu = j - i + 1
                if fd > maxh and np.log(l[j]) <= dn:
                    fd = j - i + 1
                if fu <= maxh and fd <= maxh:
                    break
            tup[s, d] = fu
            tdn[s, d] = fd
    return ret, rv, rv5, hi, lo, tup, tdn


# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------
def _pref(x):
    cs = np.empty(len(x) + 1)
    cs[0] = 0.0
    np.cumsum(x, out=cs[1:])
    return cs


def _wsum(cs, idx, w):
    """sum of x[i-w .. i-1] for each i in idx (clipped at chunk start)."""
    lo = np.maximum(idx - w, 0)
    return cs[idx] - cs[lo]


def _nearest_round(p, unit):
    lo = np.floor(p / unit) * unit
    return lo, lo + unit


HORIZONS = (10, 15, 30, 60)
FP_DELTAS_BPS = (5, 10, 20, 30)


def sample_indices(ts0: int, n: int, lo: int, hi: int, step: int = 10, seed: int = 0) -> np.ndarray:
    """Decision indices (relative to chunk start ts0) for all windows starting in [lo, hi).

    Per window: e = 0 plus e = off + step*k (off random per window, reproducible) -> covers all
    elapsed seconds uniformly across windows while keeping 1/step sampling density.
    """
    w0 = ((lo + WIN - 1) // WIN) * WIN
    wins = np.arange(w0, hi, WIN)
    rng = np.random.default_rng(seed + int(w0))
    off = rng.integers(0, step, size=len(wins))
    es = []
    for k in range(WIN // step):
        es.append(off + step * k)
    E = np.stack(es, 1)
    E = np.concatenate([np.zeros((len(wins), 1), dtype=E.dtype), E], 1)
    idx = (wins[:, None] - ts0) + E
    # drop duplicate e=0 when off==0
    keep = np.ones_like(idx, dtype=bool)
    keep[:, 1] = off != 0
    return np.sort(idx[keep].ravel())


def compute(series: dict, idx: np.ndarray, seasonal: dict | None = None, with_targets: bool = True) -> dict:
    """Compute features (and optional targets) at chunk-relative sample indices `idx`.

    `series` is the output of series.load_range covering [ts0, ts0+N). Requires idx >= 1 and,
    for targets, idx + 361 <= N.
    """
    ts0 = int(series["start"])
    c = series["c"].astype(np.float64)
    h = series["h"].astype(np.float64)
    l = series["l"].astype(np.float64)
    o = series["o"].astype(np.float64)
    v = series["v"].astype(np.float64)
    qv = series["qv"].astype(np.float64)
    tbv = series["tbv"].astype(np.float64)
    ntr = series["n"].astype(np.float64)
    N = len(c)
    idx = np.asarray(idx, dtype=np.int64)
    ts = ts0 + idx
    e = (ts % WIN).astype(np.int64)
    i0 = idx - e
    tau = WIN - e

    lc = np.log(c)
    lr = np.zeros(N)
    lr[1:] = np.diff(lc)
    lr2 = lr * lr
    sv = 2.0 * tbv - v
    pk = (np.log(h) - np.log(l)) ** 2 / (4.0 * np.log(2.0))
    absr = np.abs(lr)
    bp = np.zeros(N)
    bp[1:] = absr[1:] * absr[:-1]

    cs_lr2 = _pref(lr2); cs_pk = _pref(pk); cs_bp = _pref(bp); cs_v = _pref(v); cs_n = _pref(ntr)
    cs_sv = _pref(sv); cs_qv = _pref(qv)

    F: dict[str, np.ndarray] = {}
    S = c[idx - 1]
    lS = np.log(S)
    K = o[i0]
    F["e"] = e.astype(np.float32)
    F["tau"] = tau.astype(np.float32)

    # ---------------- volatility ----------------
    vday = _wsum(cs_lr2, idx, 86400) / np.minimum(idx, 86400)
    for w in (10, 30, 60, 180, 300, 900, 3600, 14400, 86400):
        F[f"lrv_{w}"] = np.log(_wsum(cs_lr2, idx, w) / np.minimum(idx, w) + EPS)
    for w in (60, 300, 3600):
        F[f"lpk_{w}"] = np.log(_wsum(cs_pk, idx, w) / np.minimum(idx, w) + EPS)
    for w in (300, 3600):
        bv = (np.pi / 2) * _wsum(cs_bp, idx, w) / w
        F[f"jump_{w}"] = np.log((_wsum(cs_lr2, idx, w) / w + EPS) / (bv + EPS))
    for hl in (5, 30, 120, 600, 3600):
        F[f"lew_{hl}"] = np.log(ewm_before(lr2, float(hl))[idx] + EPS)
    sig_ref = np.sqrt(np.exp(F["lew_600"]) * 0.5 + np.exp(F["lrv_3600"]) * 0.5)  # per-second vol proxy
    for w in (60, 300):
        F[f"maxabs_{w}"] = rolling_max_before(absr, w)[idx] / (sig_ref + EPS)

    # ---------------- activity ----------------
    vday_v = _wsum(cs_v, idx, 86400) / np.minimum(idx, 86400) + 1e-9
    nday = _wsum(cs_n, idx, 86400) / np.minimum(idx, 86400) + 1e-9
    for w in (10, 60, 300, 3600):
        F[f"lvol_{w}"] = np.log(_wsum(cs_v, idx, w) / w / vday_v + 1e-6)
    for w in (10, 60, 300):
        F[f"lntr_{w}"] = np.log(_wsum(cs_n, idx, w) / w / nday + 1e-6)
    F["ltsize_300"] = np.log((_wsum(cs_v, idx, 300) + 1e-9) / (_wsum(cs_n, idx, 300) + 1) / (vday_v / nday))
    F["lvday"] = np.log(vday + EPS)  # daily variance level (regime)

    # ---------------- returns / momentum (standardized) ----------------
    for k in (1, 2, 3, 5, 10, 20, 30, 60, 120, 300, 900, 3600):
        r = lS - lc[np.maximum(idx - 1 - k, 0)]
        F[f"zret_{k}"] = r / (sig_ref * np.sqrt(k) + EPS)
    F["ret_300_bps"] = (lS - lc[np.maximum(idx - 301, 0)]) * 1e4

    # ---------------- order flow ----------------
    for w in (1, 2, 5, 10, 30, 60, 300, 900):
        F[f"ofi_{w}"] = _wsum(cs_sv, idx, w) / (_wsum(cs_v, idx, w) + 1e-9)
    for w in (10, 60, 300):
        F[f"sflow_{w}"] = _wsum(cs_sv, idx, w) / (vday_v * w)  # signed volume vs typical
    for hl in (5, 60):
        F[f"ewflow_{hl}"] = ewm_before(sv, float(hl))[idx] / vday_v
    # Kyle-lambda style price impact of flow over last hour and flow-unexplained return
    cs_rsv = _pref(lr * sv); cs_sv2 = _pref(sv * sv)
    lam = _wsum(cs_rsv, idx, 3600) / (_wsum(cs_sv2, idx, 3600) + 1e-9)
    F["llam"] = np.log(np.abs(lam) * vday_v / (np.sqrt(vday) + EPS) + 1e-6)
    for w in (10, 60, 300):
        r = lS - lc[np.maximum(idx - 1 - w, 0)]
        F[f"resid_{w}"] = (r - lam * _wsum(cs_sv, idx, w)) / (sig_ref * np.sqrt(w) + EPS)

    # ---------------- VWAP deviation ----------------
    for w in (60, 300, 3600):
        vw = (_wsum(cs_qv, idx, w) + 1e-9) / (_wsum(cs_v, idx, w) + 1e-12)
        F[f"vwap_{w}"] = (lS - np.log(vw)) / (sig_ref * np.sqrt(w) + EPS)

    # ---------------- futures (perpetual) lead-lag & basis ----------------
    if "fc" in series:
        fc = series["fc"].astype(np.float64)
        ok = np.isfinite(fc)
        if ok.mean() > 0.5:
            fc = np.where(ok, fc, c)  # neutral fill where futures missing
            lfc = np.log(fc)
            flr = np.zeros(N); flr[1:] = np.diff(lfc)
            fv = series["fv"].astype(np.float64); fsv = 2 * series["ftbv"].astype(np.float64) - fv
            cs_fv = _pref(fv); cs_fsv = _pref(fsv); cs_flr2 = _pref(flr * flr)
            basis = lfc - lc
            cs_b = _pref(basis)
            b_now = basis[idx - 1]
            F["basis_bps"] = b_now * 1e4
            for w in (60, 300, 3600):
                F[f"basis_dev_{w}"] = (b_now - _wsum(cs_b, idx, w) / np.minimum(idx, w)) / (sig_ref + EPS)
            for k in (1, 2, 3, 5, 10, 30, 60):
                fr = lfc[idx - 1] - lfc[np.maximum(idx - 1 - k, 0)]
                F[f"zfret_{k}"] = fr / (sig_ref * np.sqrt(k) + EPS)
            for w in (1, 2, 5, 10, 30, 300):
                F[f"fofi_{w}"] = _wsum(cs_fsv, idx, w) / (_wsum(cs_fv, idx, w) + 1e-9)
            fvday = _wsum(cs_fv, idx, 86400) / np.minimum(idx, 86400) + 1e-9
            for w in (10, 60, 300):
                F[f"fsflow_{w}"] = _wsum(cs_fsv, idx, w) / (fvday * w)
            F["lfvshare_300"] = np.log((_wsum(cs_fv, idx, 300) + 1e-9) / (_wsum(cs_v, idx, 300) + 1e-9))
            F["lfrv_60"] = np.log(_wsum(cs_flr2, idx, 60) / 60 + EPS)
            F["lfrv_300"] = np.log(_wsum(cs_flr2, idx, 300) / 300 + EPS)
            F["fut_ok"] = ok[idx - 1].astype(np.float32)

    # ---------------- cross-asset leader (BTC spot + perpetual) ----------------
    if "xc" in series:
        F.update(_cross_features(series, idx, lc, lr, cs_lr2, sig_ref, N))

    # ---------------- reference-anchored window state ----------------
    d = lS - np.log(K)
    F["d_bps"] = d * 1e4
    F["dz"] = d / (sig_ref * np.sqrt(tau) + EPS)
    F["dz_e"] = d / (sig_ref * np.sqrt(np.maximum(e, 1)) + EPS)  # displacement vs elapsed-time vol
    win_end_prev = np.maximum(i0 - 1, 1)
    Kp = o[np.maximum(i0 - WIN, 0)]
    F["prev_win_ret"] = (lc[win_end_prev] - np.log(Kp)) / (sig_ref * np.sqrt(WIN) + EPS)
    F["k_gap"] = (np.log(K) - lc[np.maximum(i0 - 1, 0)]) / (sig_ref + EPS)
    rh, rl, fa, ncr, tsc, rvw, ofw, tsh, tsl = window_state(c, h, l, lr2, sv, v, K, i0, idx)
    sw = sig_ref * np.sqrt(WIN) + EPS
    F["run_hi"] = rh / sw
    F["run_lo"] = rl / sw
    F["hi_gap"] = (rh - d) / sw   # how far below the window high we are
    F["lo_gap"] = (d - rl) / sw
    F["frac_above"] = fa
    F["n_cross"] = ncr
    F["t_since_cross"] = tsc
    F["t_since_hi"] = tsh
    F["t_since_lo"] = tsl
    F["lrv_win"] = np.log(rvw / np.maximum(e, 1) + EPS) - np.log(sig_ref ** 2 + EPS)
    F["ofi_win"] = ofw

    # ---------------- round-number levels ----------------
    for unit in ROUND_UNITS:
        lo_, hi_ = _nearest_round(S, unit)
        F[f"rnd_up_{int(unit)}"] = (np.log(hi_) - lS) / (sig_ref * np.sqrt(WIN) + EPS)
        F[f"rnd_dn_{int(unit)}"] = (lS - np.log(lo_)) / (sig_ref * np.sqrt(WIN) + EPS)

    # ---------------- calendar & seasonality ----------------
    sod = ts % 86400
    F["hour_sin"] = np.sin(2 * np.pi * sod / 86400)
    F["hour_cos"] = np.cos(2 * np.pi * sod / 86400)
    F["min_of_hour"] = ((ts % 3600) // 60).astype(np.float32)
    F["sec_of_min"] = (ts % 60).astype(np.float32)
    dow = ((ts // 86400) + 3) % 7  # 0 = Monday
    F["dow"] = dow.astype(np.float32)
    if seasonal is not None:
        F.update(seasonal_features(seasonal, ts, tau))

    F["sig_ref"] = sig_ref  # per-second vol proxy (kept for the structural layer)
    out = {k: np.asarray(val, dtype=np.float32) for k, val in F.items()}
    out["ts"] = ts
    out["K"] = K
    out["S"] = S

    if with_targets:
        i_end = i0 + WIN - 1
        deltas = np.array(FP_DELTAS_BPS, dtype=np.float64) * 1e-4
        ret, rv, rv5, hi, lo, tup, tdn = future_targets(c, h, l, lr2, idx, i_end, np.array(HORIZONS, dtype=np.int64), deltas, 360)
        names = [f"{x}" for x in HORIZONS] + ["T"]
        for q, nm in enumerate(names):
            out[f"y_ret_{nm}"] = ret[:, q]
            out[f"y_rv_{nm}"] = rv[:, q]
            out[f"y_rv5_{nm}"] = rv5[:, q]
            out[f"y_hi_{nm}"] = hi[:, q]
            out[f"y_lo_{nm}"] = lo[:, q]
        for q, dd in enumerate(FP_DELTAS_BPS):
            out[f"y_tup_{dd}"] = tup[:, q]
            out[f"y_tdn_{dd}"] = tdn[:, q]
        out["close_T"] = c[i_end]
    return out


def _cross_features(series, idx, lc, lr, cs_lr2, sig_ref, N):
    """Features of the leader asset (prefix x_), all from bars < i.  Missing leader data -> NaN."""
    X = {}
    xc = series["xc"].astype(np.float64)
    if np.isfinite(xc).mean() < 0.5:
        return X
    lxc = np.log(xc)
    xlr = np.zeros(N); xlr[1:] = np.diff(lxc)
    xlr = np.nan_to_num(xlr)
    xlr2 = xlr * xlr
    cs_x2 = _pref(xlr2)
    xsig = np.sqrt(ewm_before(xlr2, 600.0)[idx] * 0.5 + (_wsum(cs_x2, idx, 3600) / np.minimum(idx, 3600)) * 0.5)
    lX = lxc[idx - 1]
    for k in (1, 2, 3, 5, 10, 30, 60, 300):
        X[f"x_zret_{k}"] = (lX - lxc[np.maximum(idx - 1 - k, 0)]) / (xsig * np.sqrt(k) + EPS)
    xv = series["xv"].astype(np.float64); xsv = 2 * series["xtbv"].astype(np.float64) - xv
    cs_xv = _pref(xv); cs_xsv = _pref(xsv)
    for w in (1, 5, 10, 60):
        X[f"x_ofi_{w}"] = _wsum(cs_xsv, idx, w) / (_wsum(cs_xv, idx, w) + 1e-9)
    if "xfc" in series and np.isfinite(series["xfc"]).mean() > 0.5:
        xfc = np.where(np.isfinite(series["xfc"]), series["xfc"], xc).astype(np.float64)
        lxf = np.log(xfc)
        for k in (1, 2, 3, 5, 10, 30):
            X[f"x_zfret_{k}"] = (lxf[idx - 1] - lxf[np.maximum(idx - 1 - k, 0)]) / (xsig * np.sqrt(k) + EPS)
        xb = lxf - lxc
        cs_xb = _pref(np.nan_to_num(xb))
        X["x_basis_dev_300"] = (xb[idx - 1] - _wsum(cs_xb, idx, 300) / np.minimum(idx, 300)) / (xsig + EPS)
        xfv = series["xfv"].astype(np.float64); xfsv = 2 * series["xftbv"].astype(np.float64) - xfv
        cs_xfv = _pref(xfv); cs_xfsv = _pref(xfsv)
        for w in (1, 5, 30):
            X[f"x_fofi_{w}"] = _wsum(cs_xfsv, idx, w) / (_wsum(cs_xfv, idx, w) + 1e-9)
    # rolling 1-hour beta / correlation of 1s returns, and the implied catch-up of the primary asset
    cs_xy = _pref(lr * xlr)
    cov = _wsum(cs_xy, idx, 3600)
    vx = _wsum(cs_x2, idx, 3600)
    vy = _wsum(cs_lr2, idx, 3600)
    beta = cov / (vx + 1e-18)
    X["x_beta_3600"] = beta
    X["x_corr_3600"] = cov / (np.sqrt(vx * vy) + 1e-18)
    lS = lc[idx - 1]
    # short-lag catch-up only: longer gaps (30 s - 15 min) carried no out-of-sample information (docs/RESEARCH_ETH.md)
    for k in (2, 5, 10):
        rp = lS - lc[np.maximum(idx - 1 - k, 0)]
        rx = lX - lxc[np.maximum(idx - 1 - k, 0)]
        X[f"x_gap_{k}"] = (beta * rx - rp) / (sig_ref * np.sqrt(k) + EPS)
    # leader volatility helps forecast ETH volatility (+0.2-0.5 pp R2 of log RV in every month studied)
    X["x_lvolratio_300"] = np.log((_wsum(cs_x2, idx, 300) + 1e-14) / (_wsum(cs_lr2, idx, 300) + 1e-14))
    for w in (60, 300):
        X[f"x_lrv_{w}"] = np.log(_wsum(cs_x2, idx, w) / np.minimum(idx, w) + EPS)
    return X


# ----------------------------------------------------------------------------------------------
# causal seasonal profiles
# ----------------------------------------------------------------------------------------------
def build_seasonal(c: np.ndarray, ts0: int, lookback_days: int = 28, sec_days: int = 14) -> dict:
    """Causal intraday seasonality computed from 1s closes over the full history.

    tod[day, minute]  : mean RV of that minute-of-day over the previous `lookback_days` days,
                        divided by the overall mean minute RV over the same days (relative multiplier).
    sec[day, e]       : mean squared 1s return at second e of the 5-min window over the previous
                        `sec_days` days, relative to the mean.
    Only days strictly before `day` are used.
    """
    assert ts0 % 86400 == 0
    lc = np.log(c)
    lr = np.zeros(len(c)); lr[1:] = np.diff(lc)
    lr2 = np.nan_to_num(lr * lr)
    ndays = len(c) // 86400
    lr2 = lr2[: ndays * 86400]
    minute = lr2.reshape(ndays, 1440, 60).sum(-1)              # [day, minute]
    sec = lr2.reshape(ndays, 288, 300).mean(1)                  # [day, e]
    cm = np.cumsum(np.vstack([np.zeros((1, 1440)), minute]), 0)
    cs = np.cumsum(np.vstack([np.zeros((1, 300)), sec]), 0)
    tod = np.ones((ndays, 1440), dtype=np.float32)
    sp = np.ones((ndays, 300), dtype=np.float32)
    for dday in range(ndays):
        a = max(0, dday - lookback_days)
        if dday - a >= 3:
            m = (cm[dday] - cm[a]) / (dday - a)
            # smooth +-2 minutes circularly
            ms = sum(np.roll(m, k) for k in range(-2, 3)) / 5
            tod[dday] = ms / (ms.mean() + 1e-18)
        b = max(0, dday - sec_days)
        if dday - b >= 3:
            s = (cs[dday] - cs[b]) / (dday - b)
            sp[dday] = s / (s.mean() + 1e-18)
    return {"ts0": ts0, "tod": tod, "sec": sp, "sec_cum": np.concatenate([np.zeros((ndays, 1), np.float32), np.cumsum(sp, 1)], 1)}


def seasonal_features(seas: dict, ts: np.ndarray, tau: np.ndarray) -> dict:
    day = (ts - seas["ts0"]) // 86400
    day = np.clip(day, 0, seas["tod"].shape[0] - 1)
    mod = (ts % 86400) // 60
    tod = seas["tod"]
    out = {"seas_tod": np.log(tod[day, mod] + 1e-6),
           "seas_tod_next5": np.log(np.mean([tod[day, (mod + k) % 1440] for k in range(5)], 0) + 1e-6)}
    e = ts % WIN
    cum = seas["sec_cum"]
    for hname, hh in (("30", 30), ("60", 60)):
        # expected relative variance over next hh seconds (wrapping into next window)
        end = e + hh
        tot = np.where(end <= WIN, cum[day, np.minimum(end, WIN)] - cum[day, e],
                       (cum[day, WIN] - cum[day, e]) + cum[day, np.clip(end - WIN, 0, WIN)])
        out[f"seas_sec_{hname}"] = np.log(tot / hh + 1e-6)
    out["seas_sec_T"] = np.log((cum[day, WIN] - cum[day, e]) / tau + 1e-6)
    return out
