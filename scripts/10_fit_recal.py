"""Fit the starting parameters of the live daily recalibrator on the most recent 14 days of data.

(Live, the predictor then refits itself every UTC day from its own resolved predictions.)
usage: python scripts/10_fit_recal.py [--models artifacts/models] [--end 2026-11-03]
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data  # noqa: E402
from ethmove.engine import Engine  # noqa: E402
from ethmove.recal import Recalibrator  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--models", default="artifacts/models")
ap.add_argument("--end", default="2026-11-03")
a = ap.parse_args()
end = data.ts_of(a.end)
start = (dt.datetime.fromtimestamp(end - 15 * 86400, dt.UTC)).strftime("%Y-%m-%d")
df = data.load("r", splits={"r": (start, a.end)})
eng = Engine.load(a.models)
eng.recal = None
df, S_ = eng.augment(df)
rc = Recalibrator()
now = int(df["ts"].max()) + 3601
for H, hm in eng.models.items():
    p, ps = hm.predict_above(df, S_[H])
    y = hm._d1_target(df)
    rc.fit(H, df["ts"].to_numpy(), df["e"].to_numpy(), p, y, now_ts=now, p_struct=ps)
json.dump(rc.to_json(), open(Path(a.models) / "recal.json", "w"), indent=1)
print(json.dumps(rc.to_json(), indent=1))
