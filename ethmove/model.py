"""The prediction stack, one `HorizonModel` per horizon ('30', '60', 'T' = to the 5-minute close).

Stage A  volatility engine   LightGBM (gamma deviance, log link) on realised variance over the horizon,
                             normalised by a causal vol proxy -> sd_h (forecast std of the log return).
Stage B  drift engine        LightGBM (L2) on the standardised return R/sd_h -> mu_h.
Stage C  shape               Student-t (nu, scale) of the OOF standardised residuals, per tau bucket.
Stage D  probability heads   LightGBM boosted *from the structural prior*: init_score = logit(p_struct),
                             trees only learn the correction.  Heads:
                               D1 above-reference  P(S_h >= K)                (K = fixed 5-min open)
                               D2 conditional CDF  P(R_h >= q) for any q      (monotone in q)
                               D3 touch            P(max/min over (t, t+h] crosses level)
                               D4 first passage    P(+delta first), P(-delta first), P(neither)

Stages A/B are cross-fitted on contiguous time blocks so that everything fed to C/D on the training
set is out-of-fold.  Early stopping uses the validation period only.  The test period is never seen.
"""
from __future__ import annotations

import time

import lightgbm as lgb
import numpy as np
import pandas as pd

from . import structural as st

H_LEN = {"10": 10, "15": 15, "30": 30, "60": 60}
FP_DELTAS = (5, 10, 20, 30)
TAU_BUCKETS = np.array([0, 10, 30, 60, 120, 200, 300])

BASE = dict(learning_rate=0.05, num_leaves=63, min_data_in_leaf=2000, feature_fraction=0.6,
            bagging_fraction=0.5, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=4,
            max_bin=63, seed=1)

# Pure calendar features are allowed in the volatility engine (intraday vol seasonality is robust) but
# excluded from every directional model: calendar "drift" effects are a classic source of overfitting.
CALENDAR = ("hour_sin", "hour_cos", "dow", "min_of_hour", "sec_of_min")
# Multi-day regime state (prefix rg_) is likewise allowed only in the volatility engine.
# BTC-leader features (prefix x_) drive direction only up to 60 s: the BTC->ETH directional lead is gone within
# a minute (docs/RESEARCH_ETH.md, finding 3), so they are noise for the 5-minute drift, which still receives the
# lead through the stacked 30 s / 60 s forecasts.  They feed the volatility engine at every horizon.
CROSS_DIR_HORIZONS = ("10", "15", "30", "60")
# Multi-day regime state (ethmove/regime.py, prefix rg_) is likewise allowed only in the volatility engine.


def hlen(df: pd.DataFrame, H: str) -> np.ndarray:
    if H == "T":
        return df["tau"].to_numpy(np.float64)
    return np.full(len(df), float(H_LEN[H]))


def _X(df, cols):
    return np.ascontiguousarray(df[cols].to_numpy(np.float32))


def _fit(X, y, params, rounds, Xv=None, yv=None, init=None, initv=None, early=60, log=None,
         monotone=None, weight=None):
    p = dict(BASE); p.update(params)
    if monotone is not None:
        p["monotone_constraints"] = monotone
        p["monotone_constraints_method"] = "advanced"
    ds = lgb.Dataset(X, y, init_score=init, weight=weight, free_raw_data=True)
    valid = []
    cb = []
    if Xv is not None:
        dv = lgb.Dataset(Xv, yv, init_score=initv, reference=ds, free_raw_data=True)
        valid = [dv]
        cb = [lgb.early_stopping(early, verbose=False)]
    t0 = time.time()
    b = lgb.train(p, ds, num_boost_round=rounds, valid_sets=valid, callbacks=cb)
    if log is not None:
        log(f"    fit {p.get('objective')} n={len(y)} iters={b.best_iteration or b.current_iteration()} ({time.time()-t0:.0f}s)")
    return b


def _blocks(ts: np.ndarray, k: int, gap: int = 3600):
    """Contiguous time blocks; returns list of (train_mask, test_mask) with a gap around test block."""
    q = np.quantile(ts, np.linspace(0, 1, k + 1))
    out = []
    for i in range(k):
        te = (ts >= q[i]) & ((ts < q[i + 1]) if i < k - 1 else (ts <= q[i + 1]))
        tr = (ts < q[i] - gap) | (ts > q[i + 1] + gap)
        out.append((tr, te))
    return out


def _pred(b, X, **kw):
    """LightGBM predict; single-threaded for tiny batches (live inference) to avoid thread overhead."""
    if len(X) < 2000:
        kw["num_threads"] = 1
    return b.predict(X, num_iteration=b.best_iteration or None, **kw)


def tau_bucket(tau):
    return np.clip(np.searchsorted(TAU_BUCKETS, tau, side="left") - 1, 0, len(TAU_BUCKETS) - 2)


class HorizonModel:
    def __init__(self, H: str, feats: list[str], log=print, n_folds: int = 3):
        self.H = H
        self.feats = list(feats)
        # regime state may scale volatility / tails but never drive direction (same rule as calendar features)
        self.dir_feats = [f for f in self.feats if f not in CALENDAR and not f.startswith("rg_")
                          and (H in CROSS_DIR_HORIZONS or not f.startswith("x_"))]
        self.log = log
        self.n_folds = n_folds
        self.models = {}
        self.shape = {}
        self.w_tr = None          # optional per-row training weights (e.g. recency decay)

    # ------------------------------------------------------------------ stage A / B
    def _vol_target(self, df):
        h = hlen(df, self.H)
        sig2 = df["sig_ref"].to_numpy(np.float64) ** 2
        # >= 30s: 5-second-sampled RV (absorbs the short-lag autocorrelation of 1s returns); for 10s/15s it
        # would have only 2-3 terms, so the lower-noise 1s RV is used and stage C re-scales the variance.
        key = f"y_rv5_{self.H}" if self.H == "T" or H_LEN[self.H] >= 30 else f"y_rv_{self.H}"
        return np.clip(df[key].to_numpy(np.float64) / (h * sig2), 1e-3, 1e3)

    def _var_from(self, df, pred):
        return pred * hlen(df, self.H) * df["sig_ref"].to_numpy(np.float64) ** 2

    def _drift_target(self, df, sd):
        return np.clip(df[f"y_ret_{self.H}"].to_numpy(np.float64) / sd, -6, 6)

    def fit_ab(self, tr: pd.DataFrame, va: pd.DataFrame):
        """Fit vol and drift engines. Returns OOF (sd, mu) for tr and full-model (sd, mu) for va."""
        L = self.log
        Xtr, Xva = _X(tr, self.feats), _X(va, self.feats)
        ytr, yva = self._vol_target(tr), self._vol_target(va)
        L(f"[{self.H}] stage A vol")
        pv = dict(objective="gamma", learning_rate=0.08)
        W = self.w_tr
        full = _fit(Xtr, ytr, pv, 2000, Xva, yva, log=L, weight=W)
        n_it = full.best_iteration or full.current_iteration()
        self.models["vol"] = full
        oof = np.empty(len(tr))
        ts = tr["ts"].to_numpy()
        for trm, tem in _blocks(ts, self.n_folds):
            b = _fit(Xtr[trm], ytr[trm], pv, n_it, log=L, weight=None if W is None else W[trm])
            oof[tem] = b.predict(Xtr[tem])
        sd_tr = np.sqrt(self._var_from(tr, oof))
        sd_va = np.sqrt(self._var_from(va, full.predict(Xva, num_iteration=n_it)))

        L(f"[{self.H}] stage B drift")
        Xtr, Xva = _X(tr, self.dir_feats), _X(va, self.dir_feats)
        utr, uva = self._drift_target(tr, sd_tr), self._drift_target(va, sd_va)
        pd_ = dict(objective="regression", learning_rate=0.05, num_leaves=31, min_data_in_leaf=5000,
                   lambda_l2=50.0)
        fullb = _fit(Xtr, utr, pd_, 3000, Xva, uva, log=L, weight=W)
        n_itb = fullb.best_iteration or fullb.current_iteration()
        self.models["drift"] = fullb
        moof = np.empty(len(tr))
        for trm, tem in _blocks(ts, self.n_folds):
            b = _fit(Xtr[trm], utr[trm], pd_, n_itb, log=L, weight=None if W is None else W[trm])
            moof[tem] = b.predict(Xtr[tem])
        m_va = fullb.predict(Xva, num_iteration=n_itb)
        return (sd_tr, moof), (sd_va, m_va)

    # ------------------------------------------------------------------ stage C
    def fit_shape(self, tr, sd, m):
        R = tr[f"y_ret_{self.H}"].to_numpy(np.float64)
        eps = (R / sd - m)
        tb = tau_bucket(tr["tau"].to_numpy()) if self.H == "T" else np.zeros(len(tr), int)
        self.shape = {}
        for b in np.unique(tb):
            e = eps[tb == b]
            e = e[np.isfinite(e)]
            if len(e) > 200000:
                e = np.random.default_rng(0).choice(e, 200000, replace=False)
            self.shape[int(b)] = st.fit_t_nu(e)
        self.log(f"[{self.H}] stage C shape: " + ", ".join(f"b{b}: nu={v['nu']:.3g} s={v['scale']:.3f}" for b, v in self.shape.items()))

    def _shape_arrays(self, df):
        tb = tau_bucket(df["tau"].to_numpy()) if self.H == "T" else np.zeros(len(df), int)
        nu = np.array([self.shape[int(b)]["nu"] for b in range(max(self.shape) + 1)])[tb]
        sc = np.array([self.shape[int(b)]["scale"] for b in range(max(self.shape) + 1)])[tb]
        nu = np.where(nu > 1e8, np.inf, nu)
        return nu, sc

    # ------------------------------------------------------------------ structural layer
    def structural(self, df, sd, m):
        """Returns dict with sd_eff, mu (log-return units), nu."""
        nu, sc = self._shape_arrays(df)
        sd_eff = sd * sc
        mu = m * sd           # expected log return over horizon
        return {"sd": sd_eff, "mu": mu, "nu": nu, "mz": mu / sd_eff}

    @staticmethod
    def p_above_struct(q, s):
        """P(R >= q) under the structural t distribution. q in log-return units."""
        z = (q - s["mu"]) / s["sd"]
        nu = s["nu"]
        out = np.empty(len(z))
        g = ~np.isfinite(nu)
        out[g] = st.prob_above(z[g], 0.0)
        if (~g).any():
            out[~g] = st.prob_above(z[~g], 0.0, nu[~g])
        return out

    def _sfeats(self, df, s, extra):
        cols = {"s_lsd": np.log(s["sd"]), "s_mz": s["mz"]}
        cols.update(extra)
        return np.column_stack([_X(df, self.dir_feats)] + [np.asarray(v, np.float32)[:, None] for v in cols.values()]), list(self.dir_feats) + list(cols)

    # ------------------------------------------------------------------ D1: above reference
    def _d1_inputs(self, df, s):
        q = np.log(df["K"].to_numpy(np.float64) / df["S"].to_numpy(np.float64))
        p = self.p_above_struct(q, s)
        X, names = self._sfeats(df, s, {"s_zq": (q - s["mu"]) / s["sd"], "s_lp": st.logit(p)})
        return X, p, names

    def _d1_target(self, df):
        if self.H == "T":
            return (df["close_T"].to_numpy() >= df["K"].to_numpy()).astype(float)
        R = df[f"y_ret_{self.H}"].to_numpy(np.float64)
        q = np.log(df["K"].to_numpy(np.float64) / df["S"].to_numpy(np.float64))
        # exact tie handling: S_h >= K  <=>  R >= q  (computed in float64 on prices)
        return (df["S"].to_numpy(np.float64) * np.exp(R) >= df["K"].to_numpy(np.float64) * (1 - 1e-12)).astype(float)

    # ------------------------------------------------------------------ D2: generic CDF
    @staticmethod
    def _d2_draw(n, rng):
        return rng.uniform(-2.75, 2.75, n)

    def _d2_inputs(self, df, s, g):
        q = s["mu"] + g * s["sd"]
        p = self.p_above_struct(q, s)
        X, names = self._sfeats(df, s, {"g": g, "s_lp": st.logit(p)})
        return X, p, names, q

    # ------------------------------------------------------------------ D3: touch
    @staticmethod
    def _d3_draw(n, rng):
        return rng.uniform(0.05, 3.0, n), rng.integers(0, 2, n)  # barrier (sd units), side 1=up 0=down

    def _d3_inputs(self, df, s, g, side):
        mz = s["mz"]
        p = np.where(side == 1, st.prob_touch_up(g, mz), st.prob_touch_down(g, mz))
        X, names = self._sfeats(df, s, {"g": g, "side": side, "s_lp": st.logit(p)})
        return X, p, names

    def _d3_target(self, df, s, g, side):
        hi = df[f"y_hi_{self.H}"].to_numpy(np.float64)
        lo = df[f"y_lo_{self.H}"].to_numpy(np.float64)
        lvl = g * s["sd"]
        return np.where(side == 1, hi >= lvl, lo <= -lvl).astype(float)

    # ------------------------------------------------------------------ D4: first passage
    def _d4_inputs(self, df, s, dbps):
        a = dbps * 1e-4 / s["sd"]
        pu, pdn = st.prob_first_passage(a, a, s["mz"])
        pn = np.clip(1 - pu - pdn, 1e-6, 1)
        P = np.column_stack([pn, np.clip(pu, 1e-6, 1), np.clip(pdn, 1e-6, 1)])
        P /= P.sum(1, keepdims=True)
        X, names = self._sfeats(df, s, {"fp_a": a, "fp_lpu": np.log(P[:, 1]), "fp_lpd": np.log(P[:, 2])})
        return X, P, names

    def _d4_target(self, df, dbps):
        h = hlen(df, self.H)
        tu = np.zeros(len(df)); td = np.zeros(len(df))
        for d in FP_DELTAS:
            m = dbps == d
            tu[m] = df[f"y_tup_{d}"].to_numpy()[m]
            td[m] = df[f"y_tdn_{d}"].to_numpy()[m]
        up = (tu <= h) & (tu < td)
        dn = (td <= h) & (td < tu)
        tie = (tu <= h) & (tu == td)
        y = np.where(up, 1, np.where(dn, 2, 0))
        return y, tie

    # ------------------------------------------------------------------ fit heads
    def fit_heads(self, tr, s_tr, va, s_va, heads=("d1", "d2", "d3", "d4")):
        L = self.log
        rng = np.random.default_rng(42)
        hp = dict(objective="binary", learning_rate=0.03, num_leaves=31, min_data_in_leaf=4000,
                  lambda_l2=20.0, feature_fraction=0.6)
        if "d1" in heads:
            L(f"[{self.H}] D1 above-reference head")
            Xt, pt, names = self._d1_inputs(tr, s_tr)
            Xv, pv, _ = self._d1_inputs(va, s_va)
            self.models["d1"] = _fit(Xt, self._d1_target(tr), hp, 3000, Xv, self._d1_target(va),
                                     init=st.logit(pt), initv=st.logit(pv), log=L, weight=self.w_tr)
            self.d1_names = names
        if "d2" in heads:
            L(f"[{self.H}] D2 conditional-CDF head")
            gt, gv = self._d2_draw(len(tr), rng), self._d2_draw(len(va), rng)
            Xt, pt, names, qt = self._d2_inputs(tr, s_tr, gt)
            Xv, pv, _, qv = self._d2_inputs(va, s_va, gv)
            yt = (tr[f"y_ret_{self.H}"].to_numpy() >= qt).astype(float)
            yv = (va[f"y_ret_{self.H}"].to_numpy() >= qv).astype(float)
            mono = [0] * Xt.shape[1]
            mono[names.index("g")] = -1
            mono[names.index("s_lp")] = 1
            self.models["d2"] = _fit(Xt, yt, hp, 3000, Xv, yv, init=st.logit(pt), initv=st.logit(pv), log=L,
                                     monotone=mono, weight=self.w_tr)
        if "d3" in heads:
            L(f"[{self.H}] D3 touch head")
            gt, sdt = self._d3_draw(len(tr), rng)
            gv, sdv = self._d3_draw(len(va), rng)
            Xt, pt, names = self._d3_inputs(tr, s_tr, gt, sdt)
            Xv, pv, _ = self._d3_inputs(va, s_va, gv, sdv)
            mono = [0] * Xt.shape[1]
            mono[names.index("g")] = -1
            self.models["d3"] = _fit(Xt, self._d3_target(tr, s_tr, gt, sdt), dict(hp, learning_rate=0.06), 3000, Xv,
                                     self._d3_target(va, s_va, gv, sdv), init=st.logit(pt), initv=st.logit(pv),
                                     log=L, monotone=mono, weight=self.w_tr)
        if "d4" in heads:
            L(f"[{self.H}] D4 first-passage head")
            dt_ = rng.choice(FP_DELTAS, len(tr)); dv_ = rng.choice(FP_DELTAS, len(va))
            Xt, Pt, names = self._d4_inputs(tr, s_tr, dt_)
            Xv, Pv, _ = self._d4_inputs(va, s_va, dv_)
            yt, tiet = self._d4_target(tr, dt_)
            yv, tiev = self._d4_target(va, dv_)
            mp = dict(hp); mp.update(objective="multiclass", num_class=3, learning_rate=0.06)
            self.models["d4"] = _fit(Xt[~tiet], yt[~tiet], mp, 3000, Xv[~tiev], yv[~tiev],
                                     init=np.log(Pt[~tiet]), initv=np.log(Pv[~tiev]), log=L,
                                     weight=None if self.w_tr is None else self.w_tr[~tiet])

    # ------------------------------------------------------------------ inference
    def predict_struct(self, df):
        X = _X(df, self.feats)
        sd = np.sqrt(self._var_from(df, _pred(self.models["vol"], X)))
        Xd = _X(df, self.dir_feats)
        m = _pred(self.models["drift"], Xd)
        return self.structural(df, sd, m)

    def _raw(self, key, X):
        return _pred(self.models[key], X, raw_score=True)

    def predict_above(self, df, s=None):
        s = s if s is not None else self.predict_struct(df)
        X, p, _ = self._d1_inputs(df, s)
        return st.sigmoid(st.logit(p) + self._raw("d1", X)), p

    def predict_cdf(self, df, q, s=None):
        """P(R_h >= q) for per-row log-return threshold q (array)."""
        s = s if s is not None else self.predict_struct(df)
        g = (q - s["mu"]) / s["sd"]
        X, p, _, _ = self._d2_inputs(df, s, g)
        return st.sigmoid(st.logit(p) + self._raw("d2", X)), p

    def predict_touch(self, df, level, side, s=None):
        """P(price reaches `level` (log distance from S, >0) on `side` (1 up / 0 down) within horizon)."""
        s = s if s is not None else self.predict_struct(df)
        g = level / s["sd"]
        X, p, _ = self._d3_inputs(df, s, g, side)
        return st.sigmoid(st.logit(p) + self._raw("d3", X)), p

    def predict_first(self, df, dbps, s=None):
        s = s if s is not None else self.predict_struct(df)
        X, P, _ = self._d4_inputs(df, s, np.broadcast_to(np.asarray(dbps, float), (len(df),)))
        raw = self._raw("d4", X)
        z = np.log(P) + raw
        z -= z.max(1, keepdims=True)
        E = np.exp(z)
        return E / E.sum(1, keepdims=True), P

    def quantiles(self, df, probs=(0.05, 0.25, 0.5, 0.75, 0.95), s=None, grid=np.linspace(-4, 4, 81), chunk=4000):
        """Quantiles of R_h by inverting the monotone D2 CDF on a grid (one batched model call per chunk)."""
        s = s if s is not None else self.predict_struct(df)
        n, G = len(df), len(grid)
        sf = np.empty((n, G))
        for a in range(0, n, chunk):
            b = min(n, a + chunk)
            sub = df.iloc[a:b]
            m = b - a
            rep = sub.iloc[np.repeat(np.arange(m), G)]
            srep = {k: np.repeat(v[a:b], G) for k, v in s.items()}
            g = np.tile(grid, m)
            X, p, _, _ = self._d2_inputs(rep, srep, g)
            sf[a:b] = st.sigmoid(st.logit(p) + self._raw("d2", X)).reshape(m, G)
        cdf = 1 - sf
        cdf = np.maximum.accumulate(cdf, axis=1)
        out = np.empty((n, len(probs)))
        for k, pr in enumerate(probs):
            j = np.clip((cdf < pr).sum(1), 1, G - 1)
            c0 = cdf[np.arange(n), j - 1]; c1 = cdf[np.arange(n), j]
            w = np.clip((pr - c0) / np.maximum(c1 - c0, 1e-9), 0, 1)
            gq = grid[j - 1] + w * (grid[j] - grid[j - 1])
            out[:, k] = s["mu"] + gq * s["sd"]
        return out
