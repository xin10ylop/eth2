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

**7. Where ETH *is* more predictable: volatility.** The test is an out-of-sample R² of the log future realised
variance (5-second sampled) from a HAR-style regression on the asset's own realised variance, with the identical
protocol for both assets:

| month | 30 s: ETH / BTC | 60 s: ETH / BTC | 300 s: ETH / BTC |
|---|---|---|---|
| 2024-08 | **0.297** / 0.259 | **0.444** / 0.329 | 0.611 / **0.642** |
| 2025-09 | **0.350** / 0.319 | **0.436** / 0.350 | **0.633** / 0.418 |
| 2026-05 | **0.283** / 0.226 | **0.365** / 0.230 | **0.521** / 0.473 |
| 2026-09 | **0.389** / 0.304 | **0.480** / 0.322 | **0.621** / 0.529 |

ETH's short-horizon volatility is markedly more forecastable than BTC's: +0.04 to +0.15 of R² at 30–60 s, in every
month. This is the main reason ETH should be *more* predictable for this task. P(price ≥ K) is driven mostly by
the displacement measured in units of the forecast remaining volatility, so a sharper volatility forecast
directly sharpens every reference-anchored probability.

**8. ETH follows large BTC moves, and keeps going.** After a BTC-perpetual second beyond 4σ (about 1% of seconds,
roughly 4 per 5-minute window), ETH spot makes 94–108% of its beta-implied move in the same second. It then
continues a further **+24% to +49% in the same direction over the next 10–30 s**. After ETH's own perpetual
shocks, ETH spot continues only +11% to +21%.

Explicit shock features add essentially nothing beyond the generic leader block, at most +0.003 IC and only at 1–5 s
(`study5.py`). The continuation is already captured by the BTC and ETH return features, and the trees handle the
tail non-linearity.

**9. Minute-scale mean reversion.** There is no consistent ETH-vs-BTC difference: the 1- and 5-minute return
autocorrelations are within ±0.05 for both.

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
* **Why ETH is more predictable, and how the model uses it.** The advantage is in **volatility** (finding 7) and in
  the very short horizons (finding 3, 1 s), not in 30 s – 5 min direction. The volatility engine therefore carries
  the ETH edge. It gets the BTC volatility inputs (finding 5), and the structural layer turns sharper volatility
  into sharper reference-anchored probabilities.
* **No explicit BTC-shock features** (finding 8: no incremental value beyond the leader block).
  Every recipe choice (regime handling, recency weighting, adaptive ensemble per horizon) is re-decided on ETH's
  validation period rather than copied from BTC.


## Validation-period decisions (Mar–May 2026; the test period was not used)

These come from `scripts/05_ablation.py`, `13_regime_check.py` and `16_cross_check.py`, run on the volatility and
drift engines plus the structural above-reference probability:

| decision | evidence (validation above-reference log loss, lower is better) | choice |
|---|---|---|
| BTC leader block at 30 s | with 0.32616, without 0.32654; IC 0.1465 vs 0.1441 | **keep** |
| BTC leader at 1 min | everywhere 0.41054, volatility only 0.41062, nowhere 0.41104 | **direction + volatility** |
| BTC leader at 5 min | everywhere 0.47397, **volatility only 0.47379**, nowhere 0.47389 | **volatility only** (lead is gone by 5 min) |
| ETH round-number levels ($10/$50/$100) | 30 s: with 0.32616, without 0.32640 | **keep** (unlike BTC, where they did nothing) |
| regime state in the volatility engine | 30 s 0.32616 → 0.32614; 5 min 0.47397 → 0.47395 | keep (neutral; adaptivity) |
| 180-day recency weighting | improves 10 s, 15 s and 5 min in every month; worsens 30 s and 60 s in every month | **10 s, 15 s and 5 min only** |
| perpetual (ETH) features | removing them costs 30 s IC 0.147 → 0.107 | core |

Rule used for recency weighting: adopt it for a horizon only if no validation month got worse.

## Verdict from the full models (held-out test, Jun–Nov 2026, identical protocol for both assets)

| horizon | ETH model log loss | BTC model log loss | more predictable |
|---|---|---|---|
| 10 s | 0.206 | 0.190 | BTC |
| 15 s | 0.248 | 0.231 | BTC |
| 30 s | 0.333 | 0.316 | BTC |
| 1 min | 0.433 | 0.420 | BTC |
| **5 min (to close)** | **0.465** | 0.487 | **ETH**: also higher AUC (0.852 vs 0.838), accuracy (75.5% vs 74.4%) and calibration (ECE 0.0017 vs 0.0025) |

**Why ETH is more predictable at the 5-minute horizon:** its volatility is markedly more forecastable (finding 7).
The probability of finishing above the fixed reference depends mostly on the displacement measured in units of
the remaining volatility, so smoother, more forecastable volatility makes that probability sharper. Even the
naive random-walk baseline is far better on ETH at 5 minutes (0.478 vs 0.534).

**Why BTC is more predictable from 10 s to 1 min:** BTC's spot lags its perpetual for longer, so its short-horizon
directional signal persists longer (finding 3). ETH's spot catches up within 1–2 s, and BTC's lead over ETH, though
real, adds only a little. The two assets start from the same naive level at these horizons.

**How the ETH model uses this:** the volatility engine, with BTC volatility inputs at every horizon, carries the
ETH edge. The BTC leader drives direction only up to 60 s. The design choices were re-decided on ETH validation
data rather than copied: recency weighting only at 10 s, 15 s and 5 min; no adaptive ensemble; round levels kept.
