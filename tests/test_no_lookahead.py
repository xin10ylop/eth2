"""Look-ahead bias test: features at decision index i must not change when ANY data at index >= i
is modified.  Run: python -m pytest tests -q  (needs data/spot_1s for one month; falls back to synthetic)."""
import numpy as np
import pytest

from ethmove import features as fe


def _synthetic(n=4 * 86400, seed=0):
    rng = np.random.default_rng(seed)
    ts0 = 1_700_000_000 - (1_700_000_000 % 86400)
    lr = rng.standard_t(4, n) * 2e-5
    c = 60000 * np.exp(np.cumsum(lr))
    o = np.r_[c[0], c[:-1]] * np.exp(rng.normal(0, 1e-6, n))
    h = np.maximum(c, o) * np.exp(np.abs(rng.normal(0, 1e-5, n)))
    l = np.minimum(c, o) * np.exp(-np.abs(rng.normal(0, 1e-5, n)))
    v = rng.exponential(0.3, n); tbv = v * rng.uniform(0, 1, n)
    fc = c * np.exp(rng.normal(0, 1e-5, n) + 1e-4)
    fv = rng.exponential(2.0, n)
    d = {"start": ts0, "o": o, "h": h, "l": l, "c": c, "v": v, "qv": v * c, "tbv": tbv,
         "n": rng.poisson(20, n).astype(float), "fc": fc, "fv": fv, "ftbv": fv * rng.uniform(0, 1, n),
         "fn": rng.poisson(50, n).astype(float)}
    # leader asset (BTC-like), correlated with a 1-second lead
    xlr = 0.6 * np.r_[lr[1:], 0] + rng.standard_t(4, n) * 1.5e-5
    xc = 100000 * np.exp(np.cumsum(xlr))
    xv = rng.exponential(0.2, n)
    d.update({"xo": np.r_[xc[0], xc[:-1]], "xh": xc * 1.00001, "xl": xc * 0.99999, "xc": xc, "xv": xv, "xqv": xv * xc,
              "xtbv": xv * rng.uniform(0, 1, n), "xn": rng.poisson(30, n).astype(float),
              "xfc": xc * np.exp(rng.normal(0, 1e-5, n)), "xfv": rng.exponential(1.0, n),
              "xftbv": rng.exponential(0.5, n), "xfn": rng.poisson(40, n).astype(float)})
    return d


def _corrupt(series, cut, seed=1):
    rng = np.random.default_rng(seed)
    s = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in series.items()}
    for k, v in s.items():
        if isinstance(v, np.ndarray):
            n = len(v) - cut
            s[k][cut:] = v[cut:] * np.exp(rng.normal(0, 0.01, n)) + (0 if k in "ohlc" or k == "fc" else rng.exponential(1, n))
    return s


@pytest.mark.parametrize("cut_e", [0, 1, 37, 150, 299])
def test_features_do_not_use_future(cut_e):
    series = _synthetic()
    ts0 = series["start"]
    # pick a cut inside day 3 at given elapsed second
    cut = 3 * 86400 + 600 + cut_e
    idx = np.arange(cut - 2000, cut + 1)
    seas_a = fe.build_seasonal(series["c"], ts0)
    a = fe.compute(series, idx, seasonal=seas_a, with_targets=False)
    s2 = _corrupt(series, cut)
    # The reference price K = open of the window's first bar is *known at the window open*.
    # If the cut is exactly at a window start, keep that one open price (it is information at time i).
    if (ts0 + cut) % 300 == 0:
        s2["o"][cut] = series["o"][cut]
    seas_b = fe.build_seasonal(s2["c"], ts0)
    b = fe.compute(s2, idx, seasonal=seas_b, with_targets=False)
    assert any(k.startswith("x_") for k in a), "cross-asset features must be covered by this test"
    for k in a:
        if k in ("ts",):
            continue
        assert np.array_equal(a[k], b[k], equal_nan=True), f"feature {k} uses data at/after decision index"


def test_targets_do_use_future():
    """Sanity: targets must change when the future changes (they are labels)."""
    series = _synthetic()
    idx = np.array([3 * 86400 + 600 + 10])
    a = fe.compute(series, idx, with_targets=True)
    b = fe.compute(_corrupt(series, int(idx[0])), idx, with_targets=True)
    assert a["y_ret_T"][0] != b["y_ret_T"][0]


def test_reference_fixed_within_window():
    series = _synthetic()
    ts0 = series["start"]
    w = 3 * 86400 + 900  # window start (multiple of 300 since ts0 is a day boundary)
    idx = np.arange(w, w + 300)
    f = fe.compute(series, idx, with_targets=True)
    assert np.all(f["K"] == series["o"][w])
    assert np.all(f["close_T"] == series["c"][w + 299])
    assert np.all(f["e"] == np.arange(300))
    # y_ret_T measured to the window's final close
    np.testing.assert_allclose(f["y_ret_T"], np.log(series["c"][w + 299] / series["c"][idx - 1]))
