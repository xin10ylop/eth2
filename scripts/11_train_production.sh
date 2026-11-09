#!/usr/bin/env bash
# Production refit: same (v2) recipe as the evaluated model, trained on all data up to the last two months, which are
# used for early stopping; then the live recalibrator is initialised on the final 14 days.
# The *expected* performance of this model is the one measured out-of-sample for artifacts/models (REPORT.md).
# Run monthly, or whenever the live engine raises a regime_alert.
set -e
cd "$(dirname "$0")/.."
END=${END:-2026-11-03}
VAL=${VAL:-2026-09-01}
OUT=${OUT:-artifacts/production}
python scripts/03_train.py --frac ${FRAC:-0.35} --horizons 30,60,T --dates 2024-02-01,$VAL,$END,$END --out $OUT
python scripts/03_train.py --frac ${FRAC:-0.3} --horizons 10,15 --dates 2024-02-01,$VAL,$END,$END --out $OUT
python scripts/10_fit_recal.py --models $OUT --end $END
