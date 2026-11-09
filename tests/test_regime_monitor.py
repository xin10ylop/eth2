"""The live regime-break monitor must stay quiet while the model beats the naive baseline and alarm once the
model's edge disappears (simulated regime break)."""
import numpy as np

from ethmove.live import RegimeMonitor


def test_monitor_alarms_after_break():
    rng = np.random.default_rng(0)
    mon = RegimeMonitor()
    ts = 1_790_000_000
    # regime 1: model informative (p close to truth), naive coin-flip-ish
    for i in range(288 * 30):
        t = ts + i * 10
        y = float(rng.random() < 0.5)
        p = 0.8 if y else 0.2
        p = 0.65 * p + 0.35 * 0.5
        mon.update("T", t, p, 0.5, y)
    assert not mon.status()["regime_alert"]
    # regime 2: model confidently wrong half of the time (its edge is gone)
    for i in range(288 * 30, 288 * 90):
        t = ts + i * 10
        y = float(rng.random() < 0.5)
        p = 0.75 if rng.random() < 0.5 else 0.25
        mon.update("T", t, p, 0.5, y)
    st = mon.status()
    assert st["regime_alert"] and "cusum_5m_skill" in st["reasons"]
