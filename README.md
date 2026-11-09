# eth2 — probabilistic ETH model anchored on the fixed 5-minute reference price

This repository predicts ETHUSDT **relative to the fixed opening price of the current 5-minute candle**,
continuously through every window. It covers five horizons: **10 s, 15 s, 30 s, 1 min and the 5-minute close**.
For each horizon it gives:

* `P(price ≥ K)` and `P(price < K)` against the fixed reference `K`
* the expected move, its standard deviation and price quantiles (5/25/50/75/95 %)
* `P(end ≥ K·(1+δ))` for any level, from a monotone conditional CDF
* `P(touch K·(1±δ) before the horizon ends)`
* which comes first from the current price: `P(+δ)`, `P(−δ)`, `P(neither)`
* the forecast volatility (speed of movement)

RESULTS_AT_A_GLANCE

See **[REPORT.md](REPORT.md)** for the full out-of-sample evaluation and
**[docs/RESEARCH_ETH.md](docs/RESEARCH_ETH.md)** for the research that shaped the ETH design.

## 1. Why ETH is different (research summary)

The ETH model was not copied from the BTC one. Every ETH-specific choice comes from measurements on ETH's own
1-second data (`docs/research/`) or from its validation period:

1. **Where ETH is more predictable: volatility.** ETH's short-horizon volatility is markedly more forecastable than
   BTC's: out-of-sample R² of the log future realised variance is +0.04 to +0.15 higher at 30–60 s, in every month
   tested. P(price ≥ K) is driven mostly by the displacement measured in remaining-volatility units, so this is
   the main lever.
2. **BTC leads ETH.** BTC's perpetual leads ETH spot by 1–2 seconds, almost as strongly as ETH's own perpetual does.
   After large BTC seconds (beyond 4σ), ETH spot continues a further 24–49% of the beta-implied move over the next
   10–30 s.
3. **ETH is not more predictable in direction beyond a few seconds.** At 1 s, ETH plus its BTC leader matches or beats
   BTC. From 5 s to 60 s, ETH's directional skill is consistently lower than BTC's, because its spot catches up
   with the perpetual within 1–2 s.
4. **Rejected hypotheses.** Staleness catch-up features, slow ETH/BTC relative-value reversion (30 s – 15 min) and
   explicit BTC-shock features all add nothing out of sample.

## 2. Architecture

The structural-plus-ML stack is the same as in btc-movement. It is applied to ETH's own microstructure, plus a
**BTC leader block**:

```
 1-second ETH spot bars ─┐
 1-second ETH perp bars  ├─► causal feature engine (≈168 features, all from bars < t)
 1-second BTC spot+perp ─┤      BTC leader block x_*: BTC spot/perp returns 1–300 s, flows, basis deviation,
 causal seasonality      ┘      rolling ETH/BTC beta and correlation, 2/5/10 s catch-up, BTC volatility
                                 │
           per horizon h ∈ {10 s, 15 s, 30 s, 60 s, close}
           A. volatility engine (5 s-sampled RV target; 1 s RV for 10 s/15 s)   ← BTC features at every horizon
           B. drift engine                                                     ← BTC features up to 60 s only
           C. Student-t shape per remaining-time bucket
           structural layer: terminal CDF · touch (reflection) · exact two-sided first passage
           D. prior-boosted heads: above-reference · monotone CDF · touch · first passage
           30 s and 60 s forecasts stacked out-of-fold into the 5-minute model
           causal daily recalibration / adaptive prior-head ensemble
```

ETH-specific validation decisions (Mar–May 2026; the test period was never used):

| choice | ETH | why |
|---|---|---|
| BTC leader block | direction up to 60 s, volatility everywhere | at 5 min, BTC features as directional inputs hurt; as volatility inputs they help |
| recency weighting (180-day half-life) | 10 s, 15 s and 5 min only | adopted only where no validation month got worse |
| round-number levels | $10 / $50 / $100, kept | they help ETH slightly (they did nothing for BTC) |
| regime state | volatility engine only | neutral on validation; no regime-dependent drift |

## 3. Rigour

The rigour protocol is the same as in btc-movement:
* chronological splits with a one-day embargo: train Feb 2024 → Feb 2026, validation Mar–May 2026, test Jun 1 → Nov 2 2026
* look-ahead tests that corrupt all data at or after the decision index, including the BTC leader series
  (mutation-tested)
* streaming features equal batch features (`tests/test_live_replay.py`, with both buffers)
* out-of-fold stacking
* causal seasonality, regime state and recalibration
* day-block bootstrap CIs
* regime-sliced and walk-forward evaluation
* an independent label audit from the raw files

## 4. Usage

```bash
pip install -r requirements.txt
python scripts/01_download_build.py --spot --futures --symbol ETHUSDT --data data --start 2024-01 --end 2026-11
python scripts/01_download_build.py --spot --futures --symbol BTCUSDT --data data/xasset/BTCUSDT --start 2024-01 --end 2026-11
python scripts/02_build_features.py --start 2024-02 --end 2026-11      # features (+BTC leader), labels, regime table
python scripts/03_train.py --frac 0.35 --horizons 10,15,30,60,T          # all five horizons, ≈75 min on 4 cores
python scripts/04_evaluate.py --split test --horizons T,30,60
python scripts/04_evaluate.py --split test --horizons 10,15
python scripts/15_adaptive_ensemble_check.py --split val                  # decides the adaptive ensemble per horizon
python scripts/14_regime_eval.py --split test
python scripts/10_fit_recal.py
MAIN=models python scripts/08_make_report.py
python -m pytest tests -q
```

Live, this needs Binance public websockets for ETHUSDT and BTCUSDT, spot and perpetual:

```python
from ethmove.live import LivePredictor, run_binance
run_binance(LivePredictor.from_artifacts("artifacts/models"), symbol="ETHUSDT", xsymbol="BTCUSDT",
            out_path="predictions.jsonl")
```

LIVE_EXAMPLE
