"""Asset configuration.

The primary asset is ETHUSDT (Binance spot, with its USDT-margined perpetual).  BTCUSDT is used as a
cross-asset *leader*: its spot and perpetual 1-second bars enter as `x_*` features (strictly causal, same
second grid).  Override with the environment variables ETHMOVE_SYMBOL / ETHMOVE_XSYMBOL.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYMBOL = os.environ.get("ETHMOVE_SYMBOL", "ETHUSDT").upper()
XSYMBOL = os.environ.get("ETHMOVE_XSYMBOL", "BTCUSDT").upper()   # "" disables cross-asset features

DATA = ROOT / "data"
XDATA = DATA / "xasset" / XSYMBOL          # spot_1s/ and fut_1s/ of the leader asset

# Round-number price levels (support/resistance clustering of limit orders), in quote currency.
ROUND_UNITS = {"BTCUSDT": (100.0, 500.0, 1000.0), "ETHUSDT": (10.0, 50.0, 100.0)}.get(SYMBOL, (10.0, 50.0, 100.0))
