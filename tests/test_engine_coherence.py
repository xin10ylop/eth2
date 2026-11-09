"""Coherence of the probabilistic outputs of the trained engine (skipped if models/data are absent).

  * P(above K) + P(below K) = 1, all probabilities in [0, 1]
  * price quantiles are increasing
  * P(touch U before end) >= P(end above U) for every level U above the current price (and mirrored below)
  * P(end above K(1+d)) is decreasing in d
  * first-passage probabilities sum to one
"""
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "artifacts" / "models"


@pytest.fixture(scope="module")
def outputs():
    if not (MODELS / "horizon_T.pkl").exists() or not (ROOT / "data" / "features").exists():
        pytest.skip("trained models or features not available")
    from ethmove import data
    from ethmove.engine import Engine
    df = data.load("val", frac=0.002, seed=5)
    df = df.sample(min(300, len(df)), random_state=0)
    return Engine.load(MODELS).predict(df)


def test_coherence(outputs):
    for o in outputs:
        for name, h in o["horizons"].items():
            assert abs(h["p_above_reference"] + h["p_below_reference"] - 1) < 1e-9
            assert 0 <= h["p_above_reference"] <= 1 and 0 <= h["p_up_from_now"] <= 1
            q = list(h["price_quantiles"].values())
            assert all(np.diff(q) >= -1e-6), (name, q)
            levels = sorted(h["levels"].items(), key=lambda kv: kv[1]["price"])
            ends = [v["p_end_above"] for _, v in levels]
            assert all(np.diff(ends) <= 0.02), (name, ends)   # monotone up to boosting noise
            for _, v in levels:
                if v["price"] > o["price"]:
                    assert v["p_touch_before_end"] >= v["p_end_above"] - 0.03, (name, v)
                else:
                    assert v["p_touch_before_end"] >= (1 - v["p_end_above"]) - 0.03, (name, v)
            for fp in h["first_passage_from_now"].values():
                assert abs(fp["up_first"] + fp["down_first"] + fp["neither"] - 1) < 1e-6
