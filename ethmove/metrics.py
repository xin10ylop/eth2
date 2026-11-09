"""Evaluation metrics: proper scoring rules, calibration, and day-block bootstrap confidence intervals."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

EPS = 1e-7


def logloss(y, p):
    p = np.clip(p, EPS, 1 - EPS)
    return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))


def ll_vec(y, p):
    p = np.clip(p, EPS, 1 - EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def brier(y, p):
    return np.mean((p - y) ** 2)


def auc(y, p):
    if len(np.unique(y)) < 2:
        return np.nan
    return roc_auc_score(y, p)


def ece(y, p, bins=20):
    """Expected calibration error with equal-mass bins."""
    o = np.argsort(p)
    chunks = np.array_split(o, bins)
    e = 0.0
    for c in chunks:
        if len(c):
            e += len(c) * abs(p[c].mean() - y[c].mean())
    return e / len(p)


def reliability(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    b = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    rows = []
    for k in range(bins):
        m = b == k
        if m.sum():
            rows.append((edges[k], edges[k + 1], int(m.sum()), float(p[m].mean()), float(y[m].mean())))
    return rows


def multi_logloss(y, P):
    P = np.clip(P, EPS, 1)
    return -np.mean(np.log(P[np.arange(len(y)), y]))


def pinball(y, q, tau):
    d = y - q
    return np.mean(np.maximum(tau * d, (tau - 1) * d))


def qlike(rv, var):
    """QLIKE loss for variance forecasts (robust to noisy proxies; Patton 2011)."""
    r = np.maximum(rv, 1e-20) / np.maximum(var, 1e-20)
    return np.mean(r - np.log(r) - 1)


def block_bootstrap_diff(loss_a, loss_b, day, n_boot=1000, seed=0):
    """Mean(loss_a - loss_b) with 95% CI from a day-block bootstrap (rows in the same UTC day move together).

    Positive = model b is better.  Returns (mean, lo, hi, frac_boot>0).
    """
    d = loss_a - loss_b
    days, inv = np.unique(day, return_inverse=True)
    s = np.bincount(inv, weights=d)
    n = np.bincount(inv)
    rng = np.random.default_rng(seed)
    nd = len(days)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        k = rng.integers(0, nd, nd)
        boots[i] = s[k].sum() / n[k].sum()
    return float(d.mean()), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)), float((boots > 0).mean())


def binary_report(y, p):
    return {"n": int(len(y)), "logloss": logloss(y, p), "brier": brier(y, p), "auc": auc(y, p),
            "ece": ece(y, p), "acc": float(np.mean((p >= 0.5) == (y >= 0.5))), "base": float(np.mean(y))}
