"""Real-time inference: a rolling 1-second buffer that reuses *exactly* the batch feature code.

Serving uses the same `features.compute` used for training (no train/serve skew).  At each second
boundary the bars of every completed second are known; the decision row is the start of the new second.

    pred = LivePredictor.from_artifacts("artifacts/models")
    pred.warmup(spot_bars, fut_bars)           # >= 2 days of history recommended
    out = pred.on_second(spot_bar, fut_bar)    # call once per completed second -> dict of predictions

`replay()` drives the predictor from the historical archive and is used by tests to prove that
streaming predictions equal batch predictions.

`run_binance()` is a minimal connector for Binance public websockets (spot kline_1s + USDT-M perpetual
aggTrade).  It needs network access to Binance (api.binance.com may be geo-restricted in some regions).
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

from . import features as fe
from . import regime as rg
from .engine import Engine
from scipy import special as _sp

BUF = 2 * 86400 + 3600
SPOT_FIELDS = ("o", "h", "l", "c", "v", "qv", "tbv", "n")
FUT_FIELDS = ("fc", "fv", "ftbv", "fn")


class RollingBuffer:
    def __init__(self, size: int = BUF):
        self.size = size
        self.a = {k: np.full(size + 1, np.nan if k in ("o", "h", "l", "c", "fc") else 0.0) for k in SPOT_FIELDS + FUT_FIELDS}
        self.n = 0           # number of filled bars
        self.ts_last = None  # ts of the last filled bar

    def push(self, ts: int, spot: dict, fut: dict | None):
        if self.ts_last is not None and ts != self.ts_last + 1:
            # fill gaps with flat bars (causal forward fill)
            for g in range(self.ts_last + 1, ts):
                self._append(g, None, None)
        self._append(ts, spot, fut)

    def _append(self, ts, spot, fut):
        if self.n == self.size:
            for k in self.a:
                self.a[k][:-1] = np.roll(self.a[k][:-1], -1)  # O(size); fine at 1 Hz
            j = self.size - 1
        else:
            j = self.n
            self.n += 1
        prevc = self.a["c"][j - 1] if j > 0 else np.nan
        prevf = self.a["fc"][j - 1] if j > 0 else np.nan
        if spot is None:
            for k in ("o", "h", "l", "c"):
                self.a[k][j] = prevc
            for k in ("v", "qv", "tbv", "n"):
                self.a[k][j] = 0.0
        else:
            for k in SPOT_FIELDS:
                self.a[k][j] = spot[k]
        if fut is None or not np.isfinite(fut.get("fc", np.nan)):
            self.a["fc"][j] = prevf
            for k in ("fv", "ftbv", "fn"):
                self.a[k][j] = 0.0
        else:
            for k in FUT_FIELDS:
                self.a[k][j] = fut[k]
        self.ts_last = ts

    def series(self, k_open: float | None) -> tuple[dict, int]:
        """Series dict of length n+1 (last element = the not-yet-complete current second).
        If the current second opens a new 5-minute window, its open is set to K."""
        n = self.n
        s = {k: v[: n + 1].copy() for k, v in self.a.items()}
        for k in ("o", "h", "l", "c", "fc"):
            s[k][n] = s[k][n - 1]
        for k in ("v", "qv", "tbv", "n", "fv", "ftbv", "fn"):
            s[k][n] = 0.0
        if k_open is not None:
            s["o"][n] = k_open
        s["start"] = self.ts_last - n + 1
        return s, n


class LivePredictor:
    def __init__(self, engine: Engine, seasonal: dict | None, quantiles: bool = True, log_every: int = 5,
                 adapt: bool = True):
        self.engine = engine
        self.seasonal = seasonal
        self.buf = RollingBuffer()
        self.xbuf = RollingBuffer()     # leader asset (BTC) on the same second grid -> x_* features
        self.quantiles = quantiles
        # self-monitoring for the causal daily recalibration
        self.log_every = log_every
        self.adapt = adapt
        self.pending = deque()          # (resolve_ts, H, ts, e, p_raw, K, p_naive, p_struct)
        self.resolved = {H: [] for H in ("10", "15", "30", "60", "T")}
        self._day = None
        # regime state (daily aggregates -> causal regime features), refreshed every UTC day
        self.reg_daily = None
        self.reg_table = None
        # regime-break monitor
        self.monitor = RegimeMonitor()

    @classmethod
    def from_artifacts(cls, mdir="artifacts/models", seasonal_path="data/seasonal.npz",
                       regime_daily_path="data/regime_daily.npz", **kw):
        eng = Engine.load(mdir)
        seas = None
        if Path(seasonal_path).exists():
            z = np.load(seasonal_path)
            seas = {k: (int(z[k]) if k == "ts0" else z[k]) for k in z.files}
        obj = cls(eng, seas, **kw)
        if Path(regime_daily_path).exists():
            z = np.load(regime_daily_path)
            obj.reg_daily = {k: z[k] for k in z.files}
            obj.reg_table = rg.regime_table(obj.reg_daily)
        return obj

    def _roll_regime_day(self, day_done: int):
        """Append the just-completed UTC day (from the rolling buffer) to the daily aggregates."""
        if self.reg_daily is None or day_done in set(self.reg_daily["day"].tolist()):
            return
        n = self.buf.n
        end_ts = self.buf.ts_last + 1
        j1 = n - (end_ts - (day_done + 1) * 86400)
        j0 = j1 - 86400
        if j0 < 0:
            return
        a = self.buf.a
        agg = rg.daily_aggregates(a["c"][j0:j1], a["v"][j0:j1], a["fc"][j0:j1], a["fv"][j0:j1], day_done * 86400)
        self.reg_daily = {k: np.concatenate([self.reg_daily[k], agg[k]]) for k in self.reg_daily}
        self.reg_table = rg.regime_table(self.reg_daily)

    def _seasonal_for(self, ts):
        if self.seasonal is None:
            return None
        s = self.seasonal
        nd = s["tod"].shape[0]
        day = (ts - s["ts0"]) // 86400
        if day < nd:
            return s
        # beyond the stored history: reuse the latest profile (28-day average, changes slowly)
        extra = int(day - nd + 1)
        return {"ts0": s["ts0"], "tod": np.vstack([s["tod"], np.repeat(s["tod"][-1:], extra, 0)]),
                "sec": np.vstack([s["sec"], np.repeat(s["sec"][-1:], extra, 0)]),
                "sec_cum": np.vstack([s["sec_cum"], np.repeat(s["sec_cum"][-1:], extra, 0)])}

    def warmup(self, ts: np.ndarray, spot: dict, fut: dict | None = None, xspot: dict | None = None,
               xfut: dict | None = None):
        for i, t in enumerate(ts):
            self.buf.push(int(t), {k: spot[k][i] for k in SPOT_FIELDS},
                          None if fut is None else {k: fut[k][i] for k in FUT_FIELDS})
            if xspot is not None:
                self.xbuf.push(int(t), {k: xspot[k][i] for k in SPOT_FIELDS},
                               None if xfut is None else {k: xfut[k][i] for k in FUT_FIELDS})

    def features_now(self, k_open: float | None = None) -> pd.DataFrame:
        """Feature row for the decision at the start of second ts_last+1."""
        ts_now = self.buf.ts_last + 1
        e = ts_now % fe.WIN
        if e == 0 and k_open is None:
            k_open = float(self.buf.a["c"][self.buf.n - 1])  # best available until the first trade prints
        ser, idx = self.buf.series(k_open if e == 0 else None)
        if self.xbuf.n == self.buf.n and self.xbuf.n > 0 and self.xbuf.ts_last == self.buf.ts_last:
            xs, _ = self.xbuf.series(None)
            for k in SPOT_FIELDS + FUT_FIELDS:
                ser["x" + k] = xs[k]
        F = fe.compute(ser, np.array([idx]), seasonal=self._seasonal_for(ts_now), with_targets=False)
        if self.reg_table is not None:
            F.update(rg.lookup(self.reg_table, np.array([ts_now])))
        return pd.DataFrame({k: np.asarray(v) for k, v in F.items()})

    def push(self, ts: int, spot: dict, fut: dict | None, xspot: dict | None = None, xfut: dict | None = None):
        self.buf.push(ts, spot, fut)
        if xspot is not None or self.xbuf.n:
            self.xbuf.push(ts, xspot, xfut)          # None -> forward-filled (stale leader bar)
        self._resolve()
        day = ts // 86400
        if self._day is not None and day != self._day:
            self._roll_regime_day(self._day)
            if self.adapt:
                self.refit_recal(now_ts=day * 86400)
        self._day = day

    def _close_at(self, t):
        j = self.buf.n - 1 - (self.buf.ts_last - t)
        return float(self.buf.a["c"][j]) if 0 <= j < self.buf.n else np.nan

    def _resolve(self):
        while self.pending and self.pending[0][0] <= self.buf.ts_last:
            rt, H, ts, e, p, K, pn, pst = self.pending.popleft()
            c = self._close_at(rt)
            if np.isfinite(c):
                y = float(c >= K)
                self.resolved[H].append((ts, e, p, y, pst))
                self.monitor.update(H, ts, p, pn, y)
        horizon = 14 * 86400
        for H, L in self.resolved.items():
            if len(L) > 1.2 * horizon / self.log_every:
                del L[: len(L) - int(horizon / self.log_every)]

    def refit_recal(self, now_ts):
        from .recal import Recalibrator
        if self.engine.recal is None:
            self.engine.recal = Recalibrator()
        for H, L in self.resolved.items():
            if len(L) >= 5000:
                a = np.array(L)
                self.engine.recal.fit(H, a[:, 0], a[:, 1], a[:, 2], a[:, 3], now_ts, p_struct=a[:, 4])
        self.monitor.calib = {H: dict(v) for H, v in self.engine.recal.params.items()}

    def predict(self, k_open: float | None = None) -> dict:
        row = self.features_now(k_open)
        out = self.engine.predict(row, quantiles=self.quantiles)[0]
        ts = out["ts"]
        if ts % self.log_every == 0 or out["elapsed_s"] == 0:
            lsd = np.sqrt(np.exp(float(row["lrv_300"].iloc[0])))
            d = np.log(out["price"] / out["reference_price"])
            for H, name in (("10", "10s"), ("15", "15s"), ("30", "30s"), ("60", "60s"), ("T", "close")):
                if name in out["horizons"]:
                    hs = out["horizons"][name]["horizon_s"]
                    rt = out["window_start"] + 299 if H == "T" else ts + int(hs) - 1
                    pn = float(_sp.ndtr(d / (lsd * np.sqrt(hs) + 1e-12)))
                    hz = out["horizons"][name]
                    self.pending.append((rt, H, ts, out["elapsed_s"], hz["p_above_reference_raw"],
                                         out["reference_price"], pn, hz["p_above_reference_structural"]))
            self.pending = deque(sorted(self.pending))
        out["monitor"] = self.monitor.status()
        return out

    def on_second(self, ts: int, spot: dict, fut: dict | None, k_open: float | None = None,
                  xspot: dict | None = None, xfut: dict | None = None) -> dict:
        self.push(ts, spot, fut, xspot, xfut)
        return self.predict(k_open)


class RegimeMonitor:
    """Detects regime breaks from the model's own resolved predictions.

    * skill_24h[H]: mean log-loss advantage over the naive random walk during the last 24 hours (nats/decision)
    * CUSUM on the 5-minute skill, aggregated per window: S = max(0, S + (mu0 - x - k)); alarm if S > h
    * calibration slope of the latest daily recalibration outside [0.75, 1.33]
    An alert means the market behaves differently from the training regime: retrain
    (scripts/11_train_production.sh) and treat probabilities with extra caution until then.
    """

    def __init__(self, mu0=0.03, k=0.015, h=4.0):
        self.mu0, self.k, self.h = mu0, k, h
        self.hist = {H: deque() for H in ("10", "15", "30", "60", "T")}
        self.cusum = 0.0
        self.calib = {}
        self._win = None
        self._acc = []

    @staticmethod
    def _ll(p, y):
        p = min(max(p, 1e-6), 1 - 1e-6)
        return -(y * np.log(p) + (1 - y) * np.log(1 - p))

    def update(self, H, ts, p, pn, y):
        x = self._ll(pn, y) - self._ll(p, y)
        q = self.hist[H]
        q.append((ts, x))
        while q and q[0][0] < ts - 86400:
            q.popleft()
        if H == "T":
            w = ts // 300
            if self._win is not None and w != self._win and self._acc:
                xm = float(np.mean(self._acc))
                self.cusum = max(0.0, self.cusum + (self.mu0 - xm - self.k))
                self._acc = []
            self._win = w
            self._acc.append(x)

    def status(self):
        sk = {H: (float(np.mean([v for _, v in q])) if len(q) >= 200 else None) for H, q in self.hist.items()}
        # effective slope on the logit scale (sum of weights for the adaptive prior/head ensemble)
        slopes = [w[0] + (w[1] if len(w) == 3 else 0.0) for g in self.calib.values() for w in g.values()]
        reasons = []
        if self.cusum > self.h:
            reasons.append("cusum_5m_skill")
        if sk.get("T") is not None and sk["T"] < 0:
            reasons.append("negative_24h_skill_5m")
        if slopes and (min(slopes) < 0.75 or max(slopes) > 1.33):
            reasons.append("calibration_slope")
        return {"skill_24h_nats": sk, "cusum_5m": round(self.cusum, 3), "regime_alert": bool(reasons), "reasons": reasons}


# ------------------------------------------------------------------------------------------
def replay(pred: LivePredictor, series: dict, start_i: int, n_steps: int):
    """Drive `pred` second-by-second from a historical `series` (from series.load_range)."""
    ts0 = int(series["start"])
    spot = {k: series[k] for k in SPOT_FIELDS}
    fut = {"fc": series["fc"], "fv": series["fv"], "ftbv": series["ftbv"], "fn": series["fn"]}
    has_x = "xc" in series
    xspot = {k: series["x" + k] for k in SPOT_FIELDS} if has_x else None
    xfut = {k: series["x" + k] for k in FUT_FIELDS} if has_x else None
    w0 = max(0, start_i - BUF)
    sl = lambda d: None if d is None else {k: v[w0:start_i] for k, v in d.items()}  # noqa: E731
    pred.warmup(np.arange(ts0 + w0, ts0 + start_i), sl(spot), sl(fut), sl(xspot), sl(xfut))
    outs = []
    for i in range(start_i, start_i + n_steps):
        e_next = (ts0 + i + 1) % fe.WIN
        k_open = float(series["o"][i + 1]) if e_next == 0 else None
        at = lambda d: None if d is None else {k: d[k][i] for k in d}  # noqa: E731
        outs.append(pred.on_second(ts0 + i, at(spot), at(fut), k_open=k_open, xspot=at(xspot), xfut=at(xfut)))
    return outs


# ------------------------------------------------------------------------------------------
def _rest_warmup(requests, rest, symbol, start, end):
    """Spot 1s klines (exact) + perpetual 1m klines (approximate long windows) for one symbol."""
    rows, t = [], start
    while t < end:
        r = requests.get(f"{rest}/api/v3/klines", params=dict(symbol=symbol, interval="1s", startTime=t, limit=1000), timeout=10).json()
        if not r:
            break
        rows += r
        t = r[-1][0] + 1000
    k = np.array(rows, dtype=object)
    ts = (k[:, 0].astype(np.int64) // 1000)
    spot = {"o": k[:, 1].astype(float), "h": k[:, 2].astype(float), "l": k[:, 3].astype(float), "c": k[:, 4].astype(float),
            "v": k[:, 5].astype(float), "qv": k[:, 7].astype(float), "n": k[:, 8].astype(float), "tbv": k[:, 9].astype(float)}
    fm = {}
    t = start
    while t < end:
        fr = requests.get("https://fapi.binance.com/fapi/v1/klines", params=dict(symbol=symbol, interval="1m", startTime=t, limit=1500), timeout=10).json()
        if not fr:
            break
        fm.update({int(x[0]) // 1000: x for x in fr})
        t = int(fr[-1][0]) + 60000
    fut = {kk: np.zeros(len(ts)) for kk in FUT_FIELDS}
    for i, tt in enumerate(ts):
        m = fm.get(int(tt) - int(tt) % 60)
        if m is None:
            fut["fc"][i] = np.nan
            continue
        fut["fc"][i] = spot["c"][i] * float(m[4]) / float(spot["c"][i])
        fut["fv"][i] = float(m[5]) / 60; fut["ftbv"][i] = float(m[9]) / 60; fut["fn"][i] = float(m[8]) / 60
    return ts, spot, fut


def run_binance(pred: LivePredictor, symbol: str = "ETHUSDT", xsymbol: str | None = "BTCUSDT", out_path: str | None = None,
                spot_ws="wss://stream.binance.com:9443/ws", fut_ws="wss://fstream.binance.com/ws",
                rest="https://api.binance.com"):  # pragma: no cover - network
    """Minimal live loop for the primary asset plus the leader asset (requires websocket-client, requests)."""
    import threading

    import requests
    import websocket

    end = int(time.time()) * 1000
    start = end - BUF * 1000
    ts, spot, fut = _rest_warmup(requests, rest, symbol, start, end)
    xspot = xfut = None
    if xsymbol:
        xts, xs, xf = _rest_warmup(requests, rest, xsymbol, start, end)
        pos = {int(t): i for i, t in enumerate(xts)}
        j = np.array([pos.get(int(t), -1) for t in ts])
        ok = j >= 0
        xspot = {k: np.where(ok, v[np.maximum(j, 0)], np.nan) for k, v in xs.items()}
        xfut = {k: np.where(ok, v[np.maximum(j, 0)], np.nan) for k, v in xf.items()}
    pred.warmup(ts, spot, fut, xspot, xfut)

    state = {"fut": {}, "xfut": {}, "xspot": {}}
    lock = threading.Lock()

    def agg_trades(key):
        def on_msg(_, msg):
            d = json.loads(msg)
            sec = int(d["T"]) // 1000
            p, q = float(d["p"]), float(d["q"])
            with lock:
                b = state[key].setdefault(sec, {"fc": p, "fv": 0.0, "ftbv": 0.0, "fn": 0.0})
                b["fc"] = p; b["fv"] += q; b["fn"] += 1
                if not d["m"]:
                    b["ftbv"] += q
        return on_msg

    def kline_bar(d):
        return {"o": float(d["o"]), "h": float(d["h"]), "l": float(d["l"]), "c": float(d["c"]), "v": float(d["v"]),
                "qv": float(d["q"]), "n": float(d["n"]), "tbv": float(d["V"])}

    def on_xspot(_, msg):
        d = json.loads(msg)["k"]
        with lock:
            state["xspot"][int(d["t"]) // 1000] = kline_bar(d)   # latest update for that second

    def emit(out):
        line = json.dumps(out)
        print(line, flush=True)
        if out_path:
            with open(out_path, "a") as f:
                f.write(line + "\n")

    def on_spot(_, msg):
        d = json.loads(msg)["k"]
        sec = int(d["t"]) // 1000
        if state.get("pending_e0") == sec:
            # first print of a new 5-minute window: the reference price K is now known exactly
            state["pending_e0"] = None
            emit(pred.predict(k_open=float(d["o"])))
        if d["x"]:  # kline closed
            with lock:
                fb = state["fut"].pop(sec, None)
                xb = state["xspot"].pop(sec, None)
                xfb = state["xfut"].pop(sec, None)
                for key in ("fut", "xfut", "xspot"):
                    for old in [s_ for s_ in state[key] if s_ < sec]:
                        state[key].pop(old)
            pred.push(sec, kline_bar(d), fb, xb if xsymbol else None, xfb if xsymbol else None)
            if (sec + 1) % 300 == 0:
                state["pending_e0"] = sec + 1   # wait for the window's first trade to fix K
            else:
                emit(pred.predict())

    sym = symbol.lower()
    streams = [(f"{fut_ws}/{sym}@aggTrade", agg_trades("fut"))]
    if xsymbol:
        xs_ = xsymbol.lower()
        streams += [(f"{fut_ws}/{xs_}@aggTrade", agg_trades("xfut")), (f"{spot_ws}/{xs_}@kline_1s", on_xspot)]
    for url, cb in streams:
        threading.Thread(target=websocket.WebSocketApp(url, on_message=cb).run_forever, daemon=True).start()
    websocket.WebSocketApp(f"{spot_ws}/{sym}@kline_1s", on_message=on_spot).run_forever()
