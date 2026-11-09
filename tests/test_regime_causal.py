"""Regime features for day D must not depend on day D or later."""
import numpy as np

from ethmove import regime


def _daily(n=120, seed=0):
    rng = np.random.default_rng(seed)
    return {"day": np.arange(19000, 19000 + n), "rv": rng.lognormal(-14, 0.5, n), "absr": rng.lognormal(-5, 0.3, n),
            "close": 60000 * np.exp(np.cumsum(rng.normal(0, 0.02, n))), "open": np.zeros(n),
            "vol": rng.lognormal(10, 0.3, n), "fvol": rng.lognormal(12, 0.3, n), "basis": rng.normal(2e-4, 1e-4, n)}


def test_regime_table_is_causal():
    d = _daily()
    a = regime.regime_table(d)
    for cut in (40, 77, 119):
        d2 = {k: v.copy() for k, v in d.items()}
        rng = np.random.default_rng(cut)
        for k in ("rv", "absr", "close", "vol", "fvol", "basis"):
            d2[k][cut:] = d2[k][cut:] * rng.lognormal(0, 0.5, len(d2[k]) - cut)
        b = regime.regime_table(d2)
        for k in regime.REGIME_COLS:
            assert np.array_equal(a[k][: cut + 1], b[k][: cut + 1], equal_nan=True), k
