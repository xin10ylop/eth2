
## 8. Independent audit

`scripts/12_audit.py` recomputes the 5-minute labels and the naive baseline directly from the raw 1-second files,
sharing no code with the feature pipeline. On the test period:
* **0 mismatches** in K or in the window close over 1,370,489 decision rows (44,352 windows);
* ties (`close == K`) occur in 0.30% of windows;
* the up-rate is 50.0%;
* the naive log loss recomputed independently is 0.4782, against 0.4781 in the pipeline.

## 9. Limitations and honest caveats

* **Reference source.** The model is trained on Binance ETHUSDT spot. If your reference and settlement price
  comes from another source (Chainlink ETH/USD, Coinbase, an index), rebuild the labels on that series.
* **Two live feeds, both low latency.** The directional edge lives at the 1–2 second scale and comes from ETH's
  perpetual and from BTC. In live use the engine needs ETH spot, ETH perp, BTC spot and BTC perp. A stale leader
  feed is forward-filled, which silently removes part of the short-horizon skill.
* **ETH vs BTC depends on horizon and period.** At 5 minutes ETH was more predictable in 2026, marginally ahead in the crash and
  trailed slightly in the 2025 bull run. From 30 s to 1 min BTC was more predictable in every period. ETH's advantage
  comes from its more forecastable volatility, and its directional skill beyond a few seconds is lower than BTC's
  (docs/RESEARCH_ETH.md).
* **Window-open direction is close to efficient.** At `e = 0` the 5-minute AUC is about 0.54. The value of the
  5-minute model is in continuous re-pricing through the window.
* **No transaction costs or market prices.** Log-loss gains are statistical skill. Turning them into profit
  depends on prices, fees and latency, none of which are modelled here.
* **Regime risk.** Walk-forward retrains tested on the 2025 bull run (+175%) and the 2025–26 crash (−53%)
  improve on the naive baseline in every month and in every regime slice: 5-minute +8.9 and +11.0 millinats, 30 s
  +14.1 and +17.9. The edge is smallest in the busiest hours. A structural change in market microstructure would require retraining
  (`scripts/11_train_production.sh`); the live `regime_alert` is designed to flag it.
* **Architecture.** A temporal CNN on the raw last 60 seconds of ETH and BTC sequences learns a forecast 0.93
  correlated with the gradient-boosted drift and adds no incremental IC.
