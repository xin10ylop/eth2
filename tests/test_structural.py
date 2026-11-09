"""Verify analytic barrier formulas against Monte Carlo Brownian motion with drift."""
import numpy as np

from ethmove import structural as st


def _mc(a, b, mu, n=40000, steps=4000, seed=0):
    rng = np.random.default_rng(seed)
    dt = 1.0 / steps
    x = np.zeros(n)
    hit_u = np.zeros(n, bool); hit_d = np.zeros(n, bool); first_u = np.zeros(n, bool); first_d = np.zeros(n, bool)
    for _ in range(steps):
        x += mu * dt + np.sqrt(dt) * rng.standard_normal(n)
        nu = (~hit_u) & (x >= a)
        nd = (~hit_d) & (x <= -b)
        first_u |= nu & ~hit_d & ~hit_u & ~(first_d)
        first_d |= nd & ~hit_u & ~hit_d & ~(first_u)
        hit_u |= nu; hit_d |= nd
    return hit_u.mean(), first_u.mean(), first_d.mean()


def test_touch_and_first_passage_vs_mc():
    for a, b, mu in [(0.5, 0.5, 0.0), (1.0, 0.4, 0.3), (0.3, 1.2, -0.5), (1.5, 1.5, 1.0)]:
        tu, fu, fd = _mc(a, b, mu)
        pu = st.prob_touch_up(np.array([a]), np.array([mu]))[0]
        au, ad = st.prob_first_passage(np.array([a]), np.array([b]), np.array([mu]))
        # discrete monitoring in MC under-counts touches slightly (~0.58*sqrt(dt) barrier shift)
        assert abs(pu - tu) < 0.03, (a, mu, pu, tu)
        assert abs(au[0] - fu) < 0.03, (a, b, mu, au, fu)
        assert abs(ad[0] - fd) < 0.03, (a, b, mu, ad, fd)


def test_prob_above_consistency():
    q = np.linspace(-3, 3, 13)
    p = st.prob_above(q, 0.0)
    assert np.all(np.diff(p) < 0)
    np.testing.assert_allclose(st.prob_above(np.array([0.0]), 0.0), 0.5)
    p_t = st.prob_above(q, 0.2, nu=np.full_like(q, 4.0))
    assert np.all(np.diff(p_t) < 0)
