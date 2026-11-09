# ETH research notes (before any model was trained)

These notes record what the data says about ETHUSDT at the 1-second scale, and the design decisions that follow.
Every number here comes from `docs/research/study*.py` run on Binance 1-second data. They are linear,
month-by-month, out-of-sample measurements: fitted on the first half of a month, scored on the second half.

## Literature

* Perpetual swaps dominate ETH price discovery over spot (Alexander, Choi, Massie & Sohn, 2020, minute data).
* Centralised venues and futures generally lead ETH price discovery. Results are mixed in high-volatility
  periods (Pascual, Rubio, Cebada et al., arXiv 2506.08718, 2025).
* BTC carries the largest information share among major coins, though this was measured on daily data
  (Chang & Shi, 2020).
* Lead-lag effects vary intraday and weaken around the US equity open (Huth & Abergel; Long, Southampton thesis).
* No published seconds-level BTC→ETH measurement was found, so it was measured here.

## Findings

**1. Staleness.** ETHUSDT spot has many more seconds without a trade: 6–30% across months, against 1–12% for
BTCUSDT. Its last-trade price is staler.

**2. Lead-lag at the 1-second scale.** Correlation of the ETH spot return at *t* with the leader's return at *t−k*:

| month | ETH perp k=1 | BTC perp k=1 | BTC spot k=1 | k=2 (ETH perp / BTC perp) |
|---|---|---|---|---|
| 2024-03 | 0.182 | 0.172 | 0.145 | 0.046 / 0.045 |
| 2024-08 | 0.130 | 0.109 | 0.085 | 0.029 / 0.026 |

BTC's perpetual leads ETH spot almost as strongly as ETH's own perpetual does. Most of the effect is gone after
2–3 seconds. Between the two perpetuals, BTC leads ETH slightly (0.099 vs 0.065 in Aug 2024).

**3. Is ETH more predictable than BTC?** The test used an identical out-of-sample linear protocol. The table shows
the correlation (IC) of the forecast with the realised standardised return. "own" means the asset's own spot and
perpetual returns, flows and basis.

| month | 1 s: BTC / ETH / ETH+BTC | 10 s: BTC / ETH / ETH+BTC | 30 s: BTC / ETH / ETH+BTC | 60 s: BTC / ETH / ETH+BTC |
|---|---|---|---|---|
| 2024-03 | 0.271 / 0.277 / **0.289** | 0.194 / 0.167 / 0.172 | 0.144 / 0.110 / 0.112 | 0.121 / 0.083 / 0.084 |
| 2024-08 | 0.253 / 0.253 / **0.261** | 0.230 / 0.177 / 0.183 | 0.171 / 0.116 / 0.120 | 0.123 / 0.088 / 0.090 |
| 2025-03 | 0.257 / 0.279 / **0.283** | 0.221 / 0.194 / 0.195 | 0.169 / 0.122 / 0.123 | 0.128 / 0.089 / 0.090 |
| 2025-09 | 0.247 / 0.248 / **0.250** | 0.235 / 0.210 / 0.212 | 0.172 / 0.148 / 0.148 | 0.127 / 0.105 / 0.106 |
| 2026-01 | 0.217 / 0.210 / 0.212 | 0.205 / 0.183 / 0.184 | 0.163 / 0.127 / 0.128 | 0.128 / 0.092 / 0.092 |
| 2026-05 | 0.231 / 0.228 / **0.232** | 0.253 / 0.218 / 0.222 | 0.208 / 0.155 / 0.157 | 0.167 / 0.118 / 0.119 |
| 2026-09 | 0.219 / 0.221 / **0.224** | 0.239 / 0.179 / 0.181 | 0.183 / 0.123 / 0.125 | 0.142 / 0.093 / 0.095 |

At 1 second, ETH plus its BTC leader is as predictable as BTC, and usually slightly more. From 5 seconds on,
**ETH is consistently *less* directionally predictable than BTC**: its spot catches up with the perpetual
within 1–2 seconds, so less predictable drift is left for longer horizons. BTC as a leader adds a small but
consistent +0.002 to +0.012 of IC at every horizon in every month.

**4. Hypotheses that were rejected:**
* *Staleness catch-up.* The perpetual and BTC moves since the last ETH spot trade, alone or interacted with the
  stale time, add essentially nothing beyond the basis deviation (IC changes ≤ 0.001).
* *Slow ETH/BTC relative-value reversion.* The beta-adjusted BTC−ETH return gap over 30 s, 60 s, 5 min and 15 min
  has zero or negative out-of-sample R² for 30 s – 5 min ETH returns in every month tested.

**5. Volatility.** ETH's own realised-variance history explains 40–62% of the variance of the log future realised
variance at 60 s and 300 s. Adding BTC's realised variance raises that by 0.2–0.5 percentage points in every month
tested.

**6. Variance ratios.** E[R²]/E[RV] for 1-second-sampled RV is 1.23–1.38 because of positive short-lag
autocorrelation. With 5-second sampling it is 1.11–1.20, and with 10-second sampling 1.05–1.15.


## Design decisions that follow

* **Keep the BTC-validated architecture.** Every ingredient of it is about ETH's own microstructure: the perp→spot
  lead, flows, the volatility engine and the structural layer, and they all apply.
* **Add a BTC leader block** (`x_*`). It covers BTC spot and perpetual returns over 1–300 s, BTC flows, BTC basis
  deviation, a rolling 1-hour ETH/BTC beta and correlation, short-lag beta-adjusted catch-up (2/5/10 s), and BTC
  realised volatility. It is justified by findings 2, 3 and 5, and its inclusion is re-tested on the validation
  period (ablation `no_cross_asset_btc`).
* **Drop** the staleness catch-up features and the long relative-value gaps (finding 4).
* **Volatility target.** 5-second-sampled RV for horizons of 30 s and more; 10-second sampling would be less
  biased but has half the samples. 1-second RV for 10 s and 15 s, with the scale recalibrated by stage C
  (finding 6).
* **ETH round-number levels** are $10, $50 and $100, the equivalent scale of BTC's $100/$500/$1000. They are kept
  only if the ablation supports them.
* **Expectation.** For ETH, the directional skill beyond a few seconds should be lower than for BTC (finding 3).
  Any ETH advantage will come from the very short horizons and from volatility, not from 30 s – 5 min direction.
  Every recipe choice (regime handling, recency weighting, adaptive ensemble per horizon) is re-decided on ETH's
  validation period rather than copied from BTC.

