
## 8. Independent audit

`scripts/12_audit.py` recomputes the 5-minute labels and the naive baseline directly from the raw 1-second files,
sharing no code with the feature pipeline. On the test period:
* **0 mismatches** in K or in the window close over 1,370,489 decision rows (44,352 windows);
* ties (`close == K`) occur in 0.44% of windows;
* the up-rate is 49.9%;
* the naive log loss recomputed independently is 0.5346, against 0.5337 in the pipeline (rounding of the
  volatility proxy).

## 9. Limitations and honest caveats

* **Reference source.** The model is trained on Binance BTCUSDT spot. If your reference and settlement price
  comes from another source (Chainlink BTC/USD streams, Coinbase, an index), the lead-lag structure and the tie
  behaviour change. Rebuild the labels on that series; the pipeline is source-agnostic.
* **Latency.** The lead-lag edge lives at the 1–3 second scale. The live engine needs both feeds with low
  latency, and stale perp data silently removes most of the directional skill. Ablations show that removing
  the perp features costs about a third of the 30s drift IC.
* **Window-open direction is close to efficient.** At `e = 0` the 5-minute AUC is about 0.53. The boosted head is
  slightly worse than the analytic prior there; validation and test agree. The adaptive ensemble therefore
  falls back to the prior at the open (test log loss 0.6917, against 0.6937 for the head alone). The value of the
  5-minute model is in continuous re-pricing through the window, not in calling the direction at the open. For
  that, the 10s–60s models are much stronger.
* **Calibration drift.** In 2026 the raw 5-minute head is slightly over-confident at the extremes. The causal
  14-day trailing recalibration removes this (ECE 0.014 → 0.003 on test). The live engine refits it daily from
  its own resolved predictions.
* **Explicit regime features add little.** Multi-day regime state in the volatility engine plus 180-day recency
  weighting (the v2 recipe) is statistically indistinguishable from v1 on both validation and test (≤ 0.8 millinats,
  inside the CIs). The robustness comes from volatility-standardised inputs, causal recalibration and the adaptive
  ensemble, not from regime labels. v2 is kept as the production recipe because it was the validation choice and
  adapts faster to structural change; v1 results are reported alongside.
* **No transaction costs or market prices.** Log-loss gains are statistical skill. Turning them into profit
  against a real order book or prediction market depends on its prices, fees and latency, none of which are
  modelled here.
* **Regime risk.** Three fully separate retrains were tested on a bull run (May–Aug 2025), a 43% crash (Nov 2025 – Feb
  2026) and a bear low and rebound (Jun–Nov 2026). They improve on the naive baseline in every month and every
  regime slice. The edge is smallest in the crash fold: the 5-minute gain is +15.6 millinats there against +44 in
  2026, and the 30s direction AUC is 0.58 against 0.62. It is also smallest in the busiest hours, where spot catches
  up with the perpetual fastest. A structural change in market microstructure (for example a venue migration of
  price discovery) would require retraining with `scripts/11_train_production.sh`; the live `regime_alert` is
  designed to tell you when.
* **Architecture.** A temporal CNN reading the raw last 60 seconds learns a forecast that is 0.94 correlated with
  the gradient-boosted drift and adds no incremental IC (§7). The edge is captured by the engineered features. More
  model capacity is unlikely to help; more *information* (order-book data, other venues) is where further gains
  would come from.
