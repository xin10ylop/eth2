"""Engine: the three horizon models working together + human-readable outputs.

Horizon stacking: the 30s and 60s drift/vol forecasts (high signal-to-noise estimates of the immediate
predictable move) are fed as inputs to the 5-minute (to-close) model.  On the training set these inputs
are out-of-fold, so the 5-minute model never sees in-sample short-horizon predictions.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from .model import FP_DELTAS, HorizonModel, hlen
from .recal import Recalibrator

STACK_FROM = ("30", "60")
LEVELS_BPS = (-30, -20, -10, -5, 5, 10, 20, 30)
QPROBS = (0.05, 0.25, 0.5, 0.75, 0.95)
NAMES = {"10": "10s", "15": "15s", "30": "30s", "60": "60s", "T": "close"}


def stack_columns(df: pd.DataFrame, s: dict, H: str) -> dict:
    return {f"h{H}_mz": s["mz"].astype(np.float32), f"h{H}_lsd": np.log(s["sd"]).astype(np.float32)}


class Engine:
    def __init__(self, models: dict[str, HorizonModel], recal: Recalibrator | None = None):
        self.models = models
        self.recal = recal

    @classmethod
    def load(cls, mdir: str | Path) -> "Engine":
        mdir = Path(mdir)
        ms = {}
        for H in ("10", "15", "30", "60", "T"):
            p = mdir / f"horizon_{H}.pkl"
            if p.exists():
                with open(p, "rb") as f:
                    ms[H] = pickle.load(f)
                    ms[H].log = None
        rc = None
        if (mdir / "recal.json").exists():
            import json
            rc = Recalibrator.from_json(json.load(open(mdir / "recal.json")))
        return cls(ms, rc)

    def augment(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        """Add stacking inputs; returns (df, structural outputs per horizon)."""
        out = {}
        df = df.copy()
        for H in STACK_FROM:
            if H in self.models:
                s = self.models[H].predict_struct(df)
                out[H] = s
                for k, v in stack_columns(df, s, H).items():
                    df[k] = v
        for H, hm in self.models.items():   # every other horizon (incl. 10s/15s and the 5-minute stack)
            if H not in out:
                out[H] = hm.predict_struct(df)
        return df, out

    # --------------------------------------------------------------------------------------
    def predict(self, df: pd.DataFrame, levels_bps=LEVELS_BPS, fp_bps=FP_DELTAS, quantiles=True) -> list[dict]:
        """Full prediction set for each row (decision time). Returns list of dicts (JSON-serialisable)."""
        df, S_ = self.augment(df)
        n = len(df)
        S = df["S"].to_numpy(np.float64)
        K = df["K"].to_numpy(np.float64)
        qK = np.log(K / S)
        res = [dict(ts=int(df["ts"].iloc[i]), window_start=int(df["ts"].iloc[i] - df["e"].iloc[i]),
                    elapsed_s=int(df["e"].iloc[i]), remaining_s=int(df["tau"].iloc[i]),
                    reference_price=float(K[i]), price=float(S[i]),
                    displacement_bps=float((S[i] / K[i] - 1) * 1e4), horizons={}) for i in range(n)]
        for H, hm in self.models.items():
            s = S_[H]
            p_raw, p_st = hm.predict_above(df, s)
            p_above = self.recal.apply(H, df["e"].to_numpy(), p_raw, p_struct=p_st) if self.recal is not None else p_raw
            p_up, _ = hm.predict_cdf(df, np.full(n, 1e-12), s=s)
            # all levels / first-passage sizes in one batched call each
            Lv = np.asarray(levels_bps, float)
            ri = np.repeat(np.arange(n), len(Lv))
            dfr = df.iloc[ri]
            sr = {k: v[ri] for k, v in s.items()}
            q = (qK[:, None] + Lv[None, :] * 1e-4).ravel()
            p_end = hm.predict_cdf(dfr, q, s=sr)[0]
            side = (q > 0).astype(int)
            dist = np.abs(q)
            p_t = hm.predict_touch(dfr, np.maximum(dist, 1e-9), side, s=sr)[0]
            p_t = np.where(dist <= 1e-9, 1.0, p_t)
            # logical coherence: finishing beyond a level implies having touched it
            p_t = np.maximum(p_t, np.where(side == 1, p_end, 1 - p_end))
            p_end = p_end.reshape(n, len(Lv)); p_t = p_t.reshape(n, len(Lv))
            lv = {d: (p_end[:, j], p_t[:, j]) for j, d in enumerate(levels_bps)}
            Fd = np.asarray(fp_bps, float)
            rf = np.repeat(np.arange(n), len(Fd))
            Pf = hm.predict_first(df.iloc[rf], np.tile(Fd, n), s={k: v[rf] for k, v in s.items()})[0].reshape(n, len(Fd), 3)
            fp = {d: Pf[:, j] for j, d in enumerate(fp_bps)}
            Q = hm.quantiles(df, QPROBS, s=s) if quantiles else None
            h = hlen(df, H)
            for i in range(n):
                o = {
                    "horizon_s": float(h[i]),
                    "p_above_reference": float(p_above[i]),
                    "p_above_reference_raw": float(p_raw[i]),
                    "p_above_reference_structural": float(p_st[i]),
                    "p_below_reference": float(1 - p_above[i]),
                    "p_up_from_now": float(p_up[i]),
                    "expected_move_bps": float(s["mu"][i] * 1e4),
                    "sd_bps": float(s["sd"][i] * 1e4),
                    "vol_bps_per_sqrt_s": float(s["sd"][i] / np.sqrt(h[i]) * 1e4),
                    "levels": {f"K{d:+d}bp": {"price": float(K[i] * np.exp(d * 1e-4)),
                                               "p_end_above": float(lv[d][0][i]),
                                               "p_touch_before_end": float(lv[d][1][i])}
                               for d in levels_bps},
                    "first_passage_from_now": {f"{d}bp": {"up_first": float(fp[d][i, 1]),
                                                           "down_first": float(fp[d][i, 2]),
                                                           "neither": float(fp[d][i, 0])} for d in fp_bps},
                }
                if Q is not None:
                    o["price_quantiles"] = {f"q{int(p*100):02d}": float(S[i] * np.exp(Q[i, k])) for k, p in enumerate(QPROBS)}
                res[i]["horizons"][NAMES[H]] = o
        return res
