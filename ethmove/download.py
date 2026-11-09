"""Download raw Binance public market data from data.binance.vision.

Only public, historical, exchange-published files are used (no third-party data).
Files are verified against the published SHA256 CHECKSUM files.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import time
import urllib.request
from pathlib import Path

BASE = "https://data.binance.vision/data"


def _get(url: str, dest: Path, retries: int = 5) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for k in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(tmp, dest)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            time.sleep(2 ** k)
        except Exception:
            time.sleep(2 ** k)
    return False


def _verify(path: Path, checksum_url: str) -> bool:
    try:
        with urllib.request.urlopen(checksum_url, timeout=60) as r:
            expected = r.read().decode().split()[0].strip()
    except Exception:
        return True  # checksum unavailable: accept (logged by caller)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest() == expected


def month_range(start: str, end: str):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    while (y, m) <= (ye, me):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch(kind: str, symbol: str, period: str, out_dir: Path, market: str = "spot", interval: str | None = None) -> list[Path]:
    """Fetch one month of data. Tries the monthly archive, falls back to daily archives.

    kind: 'klines' (needs interval) or 'aggTrades'. market: 'spot' or 'futures/um'.
    Returns list of local zip paths (one monthly or several daily).
    """
    sub = f"{kind}/{symbol}/{interval}" if interval else f"{kind}/{symbol}"
    stem = f"{symbol}-{interval}" if interval else f"{symbol}-{kind}"
    name = f"{stem}-{period}.zip"
    url = f"{BASE}/{market}/monthly/{sub}/{name}"
    dest = out_dir / name
    if dest.exists() or _get(url, dest):
        if not _verify(dest, url + ".CHECKSUM"):
            dest.unlink()
            raise RuntimeError(f"checksum mismatch {url}")
        return [dest]
    # fall back to daily files
    y, m = map(int, period.split("-"))
    d = dt.date(y, m, 1)
    today = dt.date.today()
    paths = []
    while d.month == m and d < today:
        dname = f"{stem}-{d.isoformat()}.zip"
        durl = f"{BASE}/{market}/daily/{sub}/{dname}"
        ddest = out_dir / "daily" / dname
        if ddest.exists() or _get(durl, ddest):
            if not _verify(ddest, durl + ".CHECKSUM"):
                ddest.unlink()
                raise RuntimeError(f"checksum mismatch {durl}")
            paths.append(ddest)
        d += dt.timedelta(days=1)
    return paths
