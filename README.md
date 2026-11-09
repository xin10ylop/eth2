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

### Results at a glance (held-out test, 1 Jun – 2 Nov 2026, 44,352 windows never used in development)

| horizon | naive RW log loss | **model** log loss | Δ vs naive, millinats [95% CI] | AUC | accuracy | direction-from-now AUC | top-10% direction accuracy | BTC model log loss (same period) |
|---|---|---|---|---|---|---|---|---|
| 10 s | 0.232 | **0.206** | +26.5 [+24.2, +29.2] | 0.974 | 91.2% | 0.624 | 71.6% | 0.190 |
| 15 s | 0.273 | **0.248** | +25.1 [+22.7, +27.8] | 0.962 | 89.2% | 0.606 | 68.9% | 0.231 |
| 30 s | 0.357 | **0.333** | +23.8 [+21.6, +26.3] | 0.931 | 84.7% | 0.579 | 65.2% | 0.316 |
| 1 min | 0.453 | **0.433** | +19.7 [+18.0, +21.6] | 0.878 | 78.8% | 0.556 | 60.7% | 0.420 |
| 5 min (to close) | 0.478 | **0.465** | +13.3 [+11.8, +15.0] | 0.852 | 75.5% | 0.546 | 60.6% | 0.487 |

These are `P(price ≥ fixed 5-minute reference)` probabilities, re-evaluated every ~10 s through every window. The improvement over the naive random walk is positive in **every test month** at every horizon. It also holds in **every regime slice**: volatility, trend, drawdown, vol expansion, intraday activity and weekday/weekend, with every CI above zero. **ETH vs BTC:** at 5 minutes, ETH was more predictable in 2026, by a wide margin in validation and test (lower log loss, higher AUC, better calibration), because its volatility is more forecastable. It was marginally ahead of BTC in the 2025–26 crash (0.4630 vs 0.4641) and trailed slightly in the 2025 bull run. From 10 s to 1 minute, BTC was more predictable in every period, because its short-horizon directional lead lasts longer. Full details are in [REPORT.md](REPORT.md).


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

Each second emits one JSON record. This is a real (trimmed) output from replaying ETHUSDT on 2026-10-15 14:32:00 UTC through the live engine with the BTC leader buffer (`scripts/09_replay_demo.py`, about 125 ms per second for all five horizons):

```json
{"ts": 1792074720, "window_start": 1792074600, "elapsed_s": 120, "remaining_s": 180, "reference_price": 2370.75, "price": 2364.72, "displacement_bps": -25.43,
 "horizons": {
  "close": {"horizon_s": 180.0, "p_above_reference": 0.082, "p_above_reference_raw": 0.083, "p_above_reference_structural": 0.088, "p_below_reference": 0.918, "p_up_from_now": 0.4884, "expected_move_bps": 0.2536, "sd_bps": 20.6599, "vol_bps_per_sqrt_s": 1.5399, "levels": {"K-10bp": {"price": 2368.38, "p_end_above": 0.1811, "p_touch_before_end": 0.3553}, "K+10bp": {"price": 2373.12, "p_end_above": 0.0337, "p_touch_before_end": 0.0529}}, "first_passage_from_now": {"10bp": {"up_first": 0.457, "down_first": 0.444, "neither": 0.099}}, "price_quantiles": {"q05": 2357.21, "q25": 2361.89, "q50": 2364.6, "q75": 2367.35, "q95": 2371.97}},
  "10s":   {"horizon_s": 10.0, "p_above_reference": 0.0006, "p_above_reference_raw": 0.0005, "p_above_reference_structural": 0.0016, "p_below_reference": 0.9994, "p_up_from_now": 0.4539, "expected_move_bps": -0.3616, "sd_bps": 5.4725, "vol_bps_per_sqrt_s": 1.7305, "levels": {"K-10bp": {"price": 2368.38, "p_end_above": 0.0048, "p_touch_before_end": 0.0052}, "K+10bp": {"price": 2373.12, "p_end_above": 0.0003, "p_touch_before_end": 0.0003}}, "first_passage_from_now": {"10bp": {"up_first": 0.02, "down_first": 0.044, "neither": 0.936}}, "price_quantiles": {"q05": 2362.73, "q25": 2363.98, "q50": 2364.61, "q75": 2365.25, "q95": 2366.46}},
  "15s": {"...": "..."}, "30s": {"...": "..."}, "60s": {"...": "..."}},
 "monitor": {"skill_24h_nats": {"10": null, "15": null, "30": null, "60": null, "T": null}, "cusum_5m": 0.0, "regime_alert": false, "reasons": []}}
```

