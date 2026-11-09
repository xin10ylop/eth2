"""Causal trailing recalibration (adapts to regime drift without look-ahead).

For each UTC day d, a 2-parameter logistic map p' = sigmoid(a * logit(p) + b) is fitted on the rows of
days [d - lookback, d) whose outcomes are already known (all labels resolve within 6 minutes; rows of the
final hour before d are excluded for safety) and applied to day d.  Optionally fitted per elapsed-time
bucket.  The same object is used in the live engine (refit once per day from logged predictions).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .structural import logit, sigmoid


def _fit_ab(z, y, w=None, l2=1.0):
    w = np.ones_like(z) if w is None else w

    def f(p):
        a, b = p
        s = a * z + b
        ll = np.sum(w * (np.logaddexp(0, s) - y * s)) / w.sum()
        return ll + l2 * ((a - 1) ** 2 + b ** 2) / len(z)

    def g(p):
        a, b = p
        s = a * z + b
        r = w * (sigmoid(s) - y) / w.sum()
        return np.array([np.sum(r * z) + 2 * l2 * (a - 1) / len(z), np.sum(r) + 2 * l2 * b / len(z)])

    o = minimize(f, x0=np.array([1.0, 0.0]), jac=g, method="L-BFGS-B", bounds=[(0.5, 2.0), (-1, 1)])
    return o.x


def _fit_stack(Z, y, l2=1.0):
    """Logistic stack p = sigmoid(Z @ w + b) with ridge shrinkage towards w = (1, 0, ...), b = 0."""
    k = Z.shape[1]
    w0 = np.zeros(k + 1); w0[0] = 1.0

    def f(w):
        s = Z @ w[:k] + w[k]
        return np.mean(np.logaddexp(0, s) - y * s) + l2 * np.sum((w - w0) ** 2) / len(y)

    def g(w):
        s = Z @ w[:k] + w[k]
        r = (sigmoid(s) - y) / len(y)
        return np.r_[Z.T @ r, r.sum()] + 2 * l2 * (w - w0) / len(y)

    o = minimize(f, x0=w0.copy(), jac=g, method="L-BFGS-B", bounds=[(-1.0, 2.0)] * k + [(-1, 1)])
    return o.x


def trailing_stack(ts, Z, y, lookback_days=14, gap_s=3600, min_rows=5000, groups=None):
    """Causal adaptive ensemble: each UTC day, per group, fit p = sigmoid(sum_j w_j * Z_j + b) on the previous
    `lookback_days` of resolved rows (Z_0 = logit of the main forecast, others = alternative forecasts)."""
    ts = np.asarray(ts); y = np.asarray(y, float); Z = np.asarray(Z, float)
    day = ts // 86400
    out = sigmoid(Z[:, 0])
    groups = np.zeros(len(y), int) if groups is None else np.asarray(groups)
    for d in np.unique(day):
        cur = day == d
        hist = (ts >= d * 86400 - lookback_days * 86400) & (ts < d * 86400 - gap_s)
        for g_ in np.unique(groups[cur]):
            hm = hist & (groups == g_)
            cm = cur & (groups == g_)
            if hm.sum() < min_rows:
                continue
            w = _fit_stack(Z[hm], y[hm])
            out[cm] = sigmoid(Z[cm] @ w[:-1] + w[-1])
    return out


def trailing_recalibrate(ts, p, y, lookback_days=14, gap_s=3600, min_rows=20000, groups=None):
    """Return recalibrated probabilities for every row (rows without enough history are left unchanged)."""
    ts = np.asarray(ts); p = np.asarray(p, float); y = np.asarray(y, float)
    z = logit(p)
    day = ts // 86400
    out = p.copy()
    groups = np.zeros(len(p), int) if groups is None else np.asarray(groups)
    for d in np.unique(day):
        cur = day == d
        hist = (ts >= d * 86400 - lookback_days * 86400) & (ts < d * 86400 - gap_s)
        for g in np.unique(groups[cur]):
            hm = hist & (groups == g)
            cm = cur & (groups == g)
            if hm.sum() < min_rows:
                continue
            a, b = _fit_ab(z[hm], y[hm])
            out[cm] = sigmoid(a * z[cm] + b)
    return out


E_EDGES = (1, 60, 120, 180, 240)


STACK_HORIZONS = ("T",)   # adaptive prior/head ensemble (chosen on validation); others: 2-parameter recalibration


class Recalibrator:
    """Per-(horizon, elapsed-bucket) causal recalibration of P(above reference), refitted daily.

    For horizons in STACK_HORIZONS the map is an adaptive ensemble
        p = sigmoid(w1 * logit(p_head) + w2 * logit(p_structural) + b)
    so the weight on the analytic prior vs the learned correction follows recent performance (regime-adaptive);
    for the other horizons it is the 2-parameter map p = sigmoid(a * logit(p_head) + b).
    Params are fitted on the last `lookback_days` of resolved rows only; identity until enough history exists.
    """

    def __init__(self, params: dict | None = None, lookback_days: int = 14, min_rows: int = 3000):
        self.params = params or {}
        self.lookback_days = lookback_days
        self.min_rows = min_rows

    @staticmethod
    def group(e):
        return np.digitize(np.asarray(e), E_EDGES)

    def fit(self, H, ts, e, p, y, now_ts, gap_s=3600, p_struct=None):
        ts = np.asarray(ts); m = (ts >= now_ts - self.lookback_days * 86400) & (ts < now_ts - gap_s)
        g = self.group(e)
        z = logit(np.asarray(p, float))
        y = np.asarray(y, float)
        stack = H in STACK_HORIZONS and p_struct is not None
        Z = np.column_stack([z, logit(np.asarray(p_struct, float))]) if stack else z[:, None]
        out = dict(self.params.get(H, {}))
        for k in np.unique(g[m]):
            mk = m & (g == k)
            if mk.sum() >= self.min_rows:
                w = _fit_stack(Z[mk], y[mk]) if stack else np.r_[_fit_ab(z[mk], y[mk])]
                out[int(k)] = tuple(float(v) for v in w)
        self.params[H] = out

    def apply(self, H, e, p, p_struct=None):
        if H not in self.params or not self.params[H]:
            return np.asarray(p, float)
        g = self.group(e)
        z = logit(np.asarray(p, float))
        zs = logit(np.asarray(p_struct, float)) if p_struct is not None else None
        out = np.asarray(p, float).copy()
        for k, w in self.params[H].items():
            m = g == int(k)
            if len(w) == 3 and zs is not None:
                out[m] = sigmoid(w[0] * z[m] + w[1] * zs[m] + w[2])
            elif len(w) == 2:
                out[m] = sigmoid(w[0] * z[m] + w[1])
        return out

    def to_json(self):
        return {"lookback_days": self.lookback_days, "params": {H: {str(k): v for k, v in d.items()} for H, d in self.params.items()}}

    @classmethod
    def from_json(cls, d):
        return cls({H: {int(k): tuple(v) for k, v in g.items()} for H, g in d["params"].items()}, d.get("lookback_days", 14))
