"""Structural (analytic) probability layer.

All quantities are expressed in *standardized* coordinates over the horizon: distances are divided by
sigma_h = sigma * sqrt(h) (the forecast standard deviation of the log return over the horizon), and
the drift mu is the expected log return over the horizon divided by sigma_h.

Provides
  * terminal CDF with Student-t shape (variance-matched)
  * one-sided barrier touch probability for Brownian motion with drift (reflection principle)
  * two-sided first-passage probabilities (method of images + Girsanov), exact for BM with drift
"""
from __future__ import annotations

import numpy as np
from scipy import special, stats

LOGIT_CLIP = 1e-6


def logit(p):
    p = np.clip(p, LOGIT_CLIP, 1 - LOGIT_CLIP)
    return np.log(p) - np.log1p(-p)


def sigmoid(x):
    return special.expit(x)


# ------------------------------------------------------------------ terminal distribution
def t_scale(nu):
    nu = np.asarray(nu, dtype=float)
    return np.where(np.isfinite(nu), np.sqrt(np.maximum(nu - 2, 1e-6) / nu), 1.0)


def prob_above(q, mu, nu=np.inf):
    """P(X >= q) for X = mu + eps, eps unit-variance Student-t(nu) (Gaussian if nu=inf). Standardized units."""
    z = (np.asarray(q) - mu)
    if np.all(~np.isfinite(nu)):
        return special.ndtr(-z)
    s = t_scale(nu)
    return stats.t.sf(z / s, nu)


def quantile(p, mu, nu=np.inf):
    if np.all(~np.isfinite(nu)):
        return mu + special.ndtri(p)
    return mu + t_scale(nu) * stats.t.ppf(p, nu)


# ------------------------------------------------------------------ barrier touch (one-sided)
def _I(c, m):
    """I(c, m) = int_0^1 c/sqrt(2 pi s^3) exp(-c^2/(2s) - m^2 s/2) ds  for c > 0 (numerically stable)."""
    am = np.abs(m)
    return (np.exp(am * c + special.log_ndtr(-(am + c)))
            + np.exp(-am * c + special.log_ndtr(am - c)))


def prob_touch_up(a, mu):
    """P(max_{s<=1} (mu s + W_s) >= a), a > 0 (standardized). Reflection principle with drift."""
    a = np.maximum(np.asarray(a, dtype=float), 0.0)
    mu = np.asarray(mu, dtype=float)
    return np.clip(special.ndtr(mu - a) + np.exp(2 * mu * a + special.log_ndtr(-mu - a)), 0.0, 1.0)


def prob_touch_down(b, mu):
    """P(min_{s<=1} (mu s + W_s) <= -b), b > 0."""
    return prob_touch_up(b, -np.asarray(mu, dtype=float))


# ------------------------------------------------------------------ two-sided first passage
def prob_first_passage(a, b, mu, kmax=None):
    """For X_s = mu s + W_s on s in [0,1], upper barrier a>0, lower barrier -b<0:
    returns (P(hit a first, before time 1), P(hit -b first, before time 1)). Exact series."""
    a = np.maximum(np.asarray(a, dtype=float), 1e-9)
    b = np.maximum(np.asarray(b, dtype=float), 1e-9)
    mu = np.asarray(mu, dtype=float) + 0 * a
    L = a + b
    if kmax is None:
        kmax = int(np.clip(np.ceil(7.0 / np.maximum(L.min(), 1e-3)), 4, 400))
    pu = np.zeros_like(a)
    pd = np.zeros_like(a)
    for k in range(-kmax, kmax + 1):
        cu = a + 2 * k * L
        cd = b + 2 * k * L
        pu += np.sign(cu) * _I(np.abs(cu), mu)
        pd += np.sign(cd) * _I(np.abs(cd), mu)
    pu = np.exp(mu * a) * pu
    pd = np.exp(-mu * b) * pd
    pu = np.clip(pu, 0, 1)
    pd = np.clip(pd, 0, 1)
    tot = pu + pd
    scale = np.where(tot > 1, 1 / np.maximum(tot, 1e-12), 1.0)
    return pu * scale, pd * scale


# ------------------------------------------------------------------ Student-t fit
def fit_t_nu(eps, grid=(2.5, 3, 3.5, 4, 5, 6, 8, 10, 15, 25, 50, 1e9)):
    """MLE of nu for unit-variance Student-t on standardized residuals (with free scale)."""
    eps = np.asarray(eps, dtype=float)
    eps = eps[np.isfinite(eps)]
    best = None
    for nu in grid:
        s_grid = np.linspace(0.6, 1.6, 41)
        for s in s_grid:
            if nu > 1e8:
                ll = stats.norm.logpdf(eps / s).sum() - len(eps) * np.log(s)
            else:
                sc = s * np.sqrt((nu - 2) / nu)
                ll = stats.t.logpdf(eps / sc, nu).sum() - len(eps) * np.log(sc)
            if best is None or ll > best[0]:
                best = (ll, nu, s)
    return {"nu": best[1], "scale": best[2], "ll": best[0]}
