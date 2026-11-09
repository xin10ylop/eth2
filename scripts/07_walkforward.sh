#!/usr/bin/env bash
# Walk-forward with the final (v2) recipe: retrain the full stack on expanding windows and evaluate on later,
# disjoint test periods covering different market regimes.
#   Fold A: train Feb 2024 - Feb 2025, val Mar-Apr 2025, test May - Aug 2025   (bull run: 94k -> 124k -> 109k)
#   Fold B: train Feb 2024 - Aug 2025, val Sep-Oct 2025, test Nov 2025 - Feb 2026 (crash: 110k -> 63k, -43%)
#   Main  : train Feb 2024 - Feb 2026, val Mar-May 2026, test Jun - Nov 2026      (bear low 58k, rebound to 87k)
set -e
cd "$(dirname "$0")/.."
FRAC=${FRAC:-0.3}
run() {  # name dates
  python scripts/03_train.py --frac "$FRAC" --dates "$2" --out "artifacts/wf_$1" > "artifacts/wf_$1.out" 2>&1
  python scripts/04_evaluate.py --split test --dates "$2" --models "artifacts/wf_$1" --qsub 30000 --boot 300 > "artifacts/wf_$1_eval.out" 2>&1
  python scripts/14_regime_eval.py --split test --dates "$2" --models "artifacts/wf_$1" > "artifacts/wf_$1_regime.out" 2>&1
}
run A 2024-02-01,2025-03-01,2025-05-01,2025-09-01
run B 2024-02-01,2025-09-01,2025-11-01,2026-03-01
