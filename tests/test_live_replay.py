"""Train/serve skew test: streaming features (rolling buffer, one second at a time) must equal the batch
features used for training/evaluation on the same data."""
import numpy as np
import pandas as pd

from ethmove import features as fe
from ethmove.live import BUF, LivePredictor

from test_no_lookahead import _synthetic


class _NoEngine:
    pass


def test_streaming_features_equal_batch():
    series = _synthetic(n=BUF + 2000)
    ts0 = int(series["start"])
    seas = fe.build_seasonal(series["c"], ts0)
    lp = LivePredictor(_NoEngine(), seas)
    start_i = BUF + 1000 - 5
    # warm up with exactly BUF seconds so the rolling buffer starts where batch features have full history
    w0 = start_i - BUF
    spot = {k: series[k] for k in ("o", "h", "l", "c", "v", "qv", "tbv", "n")}
    fut = {k: series[k] for k in ("fc", "fv", "ftbv", "fn")}
    xspot = {k: series["x" + k] for k in spot}
    xfut = {k: series["x" + k] for k in fut}
    sl = lambda d: {k: v[w0:start_i] for k, v in d.items()}  # noqa: E731
    lp.warmup(np.arange(ts0 + w0, ts0 + start_i), sl(spot), sl(fut), sl(xspot), sl(xfut))
    rows = []
    idxs = []
    for i in range(start_i, start_i + 320):   # crosses a 5-minute boundary
        lp.push(ts0 + i, {k: spot[k][i] for k in spot}, {k: fut[k][i] for k in fut},
                {k: xspot[k][i] for k in xspot}, {k: xfut[k][i] for k in xfut})
        e_next = (ts0 + i + 1) % 300
        k_open = float(series["o"][i + 1]) if e_next == 0 else None
        rows.append(lp.features_now(k_open))
        idxs.append(i + 1)
    live = pd.concat(rows, ignore_index=True)
    assert any(c.startswith("x_") for c in live.columns)
    # batch: same history window (features with lookback <= BUF are identical given identical inputs)
    sub = {k: (v[w0:] if isinstance(v, np.ndarray) else v) for k, v in series.items()}
    sub["start"] = ts0 + w0
    batch = fe.compute(sub, np.array(idxs) - w0, seasonal=seas, with_targets=False)
    for k in live.columns:
        a = live[k].to_numpy(); b = np.asarray(batch[k])
        if k in ("ts",):
            assert np.array_equal(a, b)
            continue
        np.testing.assert_allclose(a, b, rtol=2e-5, atol=1e-6, err_msg=k)
