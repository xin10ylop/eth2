# REPORT — ETH movement relative to the fixed 5-minute reference

**Bottom line.** These are results on the held-out test period 2026-06-01 → 2026-11-03 (1,370,495 decision rows). It was never used during development. All numbers below are generated from `artifacts/*/report_*.json`.

* **10-second** — P(price ≥ K): log loss **0.206** vs **0.232** for the naive random walk, an improvement of +26.5 [+24.2, +29.2] millinats per decision. AUC 0.974, accuracy 91.2%, ECE 0.0013. Direction from now: AUC 0.624, top-10%-confidence accuracy 71.6%.
* **15-second** — P(price ≥ K): log loss **0.248** vs **0.273** for the naive random walk, an improvement of +25.1 [+22.7, +27.8] millinats per decision. AUC 0.962, accuracy 89.2%, ECE 0.0012. Direction from now: AUC 0.606, top-10%-confidence accuracy 68.9%.
* **30-second** — P(price ≥ K): log loss **0.333** vs **0.357** for the naive random walk, an improvement of +23.8 [+21.6, +26.3] millinats per decision. AUC 0.931, accuracy 84.7%, ECE 0.0025. Direction from now: AUC 0.579, top-10%-confidence accuracy 65.2%.
* **1-minute** — P(price ≥ K): log loss **0.433** vs **0.453** for the naive random walk, an improvement of +19.7 [+18.0, +21.6] millinats per decision. AUC 0.878, accuracy 78.8%, ECE 0.0032. Direction from now: AUC 0.556, top-10%-confidence accuracy 60.7%.
* **5-minute (to close)** — P(price ≥ K): log loss **0.465** vs **0.478** for the naive random walk, an improvement of +13.3 [+11.8, +15.0] millinats per decision. AUC 0.852, accuracy 75.5%, ECE 0.0017. Direction from now: AUC 0.546, top-10%-confidence accuracy 60.6%.
* Through the 5-minute window, accuracy rises from 53.1% at the open (pure direction) to 91.7% in the last minute.

How to read the numbers. Late in the window most of `P(close ≥ K)` is "physics": the displacement from K measured in units of remaining volatility. Every model gets the easy part right, so the honest comparison is against strong baselines, not a coin flip. The genuinely predictive part lives in three places, each measured separately below:
1. a much better volatility forecast;
2. a short-horizon drift driven mainly by the perpetual→spot lead-lag;
3. learned corrections of the shape, touches and first passages.

# Out-of-sample results

Main test period **2026-06-01 → 2026-11-03** (1,370,495 decision rows). Nothing in this period was used for training, early stopping, feature selection, recalibration choices or hyper-parameters. Log loss is in nats; lower is better. Improvements are reported in **millinats per decision**, with **95% day-block bootstrap CIs** in brackets. A coin flip scores 0.6931.

For calibration, `full+recal` adds the causal trailing recalibration. It is fitted each day on the previous 14 days of resolved outcomes. Enabling it was decided on the validation period.

## 1. P(price ≥ fixed 5-minute reference) — every horizon

| horizon | naive RW | structural | full | full+recal | Δ full vs naive | Δ full vs structural | AUC | accuracy | ECE (full+recal) |
|---|---|---|---|---|---|---|---|---|---|
| 10-second | 0.2323 | 0.2129 | 0.2059 | 0.2059 | +26.5 [+24.2, +29.2] | +7.1 [+5.4, +9.1] | 0.974 | 0.912 | 0.0013 |
| 15-second | 0.2730 | 0.2534 | 0.2479 | 0.2479 | +25.1 [+22.7, +27.8] | +5.5 [+4.1, +7.4] | 0.962 | 0.892 | 0.0012 |
| 30-second | 0.3570 | 0.3366 | 0.3332 | 0.3332 | +23.8 [+21.6, +26.3] | +3.4 [+2.3, +4.7] | 0.931 | 0.847 | 0.0025 |
| 1-minute | 0.4528 | 0.4346 | 0.4330 | 0.4330 | +19.7 [+18.0, +21.6] | +1.6 [+1.1, +2.1] | 0.878 | 0.788 | 0.0032 |
| 5-minute (to close) | 0.4781 | 0.4652 | 0.4648 | 0.4648 | +13.3 [+11.8, +15.0] | +0.4 [+0.2, +0.6] | 0.852 | 0.755 | 0.0017 |

*naive RW* is a driftless Gaussian random walk using the last 5 minutes' realised volatility, which is what most dashboards compute. *structural* is the analytic layer on top of the learned volatility, drift and shape. *full* adds the prior-boosted head. For 30s and 60s the table uses decision times whose horizon ends inside the window.

### Adaptive prior/head ensemble (regime-adaptive weighting)

Each UTC day and elapsed-time bucket, a logistic stack of logit(boosted head) and logit(structural prior) is refitted on the previous 14 days of resolved outcomes. Where the ML correction stops helping, for example at the window open or after a regime shift, weight moves back to the analytic prior. For ETH it did not beat the plain 2-parameter recalibration at any horizon on validation, and the test confirms this, so plain recalibration ships for every ETH horizon.

| split | horizon | structural | full | full+recal | adaptive | Δ adaptive vs recal (millinats) |
|---|---|---|---|---|---|---|
| val | 5-minute (to close) | 0.4727 | 0.4721 | 0.4720 | 0.4720 | -0.04 [-0.19, +0.11] |
| val | 1-minute | 0.4311 | 0.4300 | 0.4296 | 0.4297 | -0.06 [-0.12, -0.01] |
| val | 30-second | 0.3320 | 0.3301 | 0.3298 | 0.3298 | -0.01 [-0.05, +0.03] |
| val | 15-second | 0.2472 | 0.2435 | 0.2434 | 0.2434 | -0.01 [-0.06, +0.02] |
| val | 10-second | 0.2055 | 0.2003 | 0.2002 | 0.2002 | -0.01 [-0.04, +0.02] |
| test | 5-minute (to close) | 0.4652 | 0.4648 | 0.4648 | 0.4649 | -0.04 [-0.11, +0.03] |
| test | 1-minute | 0.4346 | 0.4330 | 0.4330 | 0.4329 | +0.07 [-0.09, +0.26] |
| test | 30-second | 0.3366 | 0.3332 | 0.3332 | 0.3331 | +0.09 [-0.05, +0.27] |
| test | 15-second | 0.2534 | 0.2479 | 0.2479 | 0.2479 | +0.01 [-0.05, +0.09] |
| test | 10-second | 0.2129 | 0.2059 | 0.2059 | 0.2059 | +0.02 [-0.02, +0.07] |

### 5-minute model, continuously through the window (test)

| elapsed (s) | n | naive RW | structural | full | full+recal | AUC | accuracy |
|---|---|---|---|---|---|---|---|
| 0-0 | 44,352 | 0.6932 | 0.6923 | 0.6911 | 0.6911 | 0.537 | 0.531 |
| 1-59 | 261,695 | 0.6553 | 0.6507 | 0.6501 | 0.6500 | 0.660 | 0.611 |
| 60-119 | 266,112 | 0.5861 | 0.5759 | 0.5754 | 0.5754 | 0.765 | 0.693 |
| 120-179 | 266,112 | 0.5007 | 0.4857 | 0.4852 | 0.4853 | 0.845 | 0.761 |
| 180-239 | 266,112 | 0.3924 | 0.3747 | 0.3744 | 0.3745 | 0.912 | 0.830 |
| 240-299 | 266,112 | 0.2230 | 0.2043 | 0.2044 | 0.2043 | 0.975 | 0.917 |

At `e=0` the price is exactly at the reference, so the forecast is purely directional. That is the hardest case, and it is reported separately.

### ETH vs BTC: which is more predictable? (same test period, identical protocol)

| horizon | ETH naive → model | BTC naive → model | ETH Δ vs naive | BTC Δ vs naive | ETH AUC | BTC AUC | ETH dir. AUC | BTC dir. AUC |
|---|---|---|---|---|---|---|---|---|
| 10-second | 0.2323 → **0.2059** | 0.2332 → **0.1898** | +26.5 | +43.4 | 0.974 | 0.978 | 0.624 | 0.658 |
| 15-second | 0.2730 → **0.2479** | 0.2741 → **0.2307** | +25.1 | +43.4 | 0.962 | 0.967 | 0.606 | 0.644 |
| 30-second | 0.3570 → **0.3332** | 0.3579 → **0.3163** | +23.8 | +41.5 | 0.931 | 0.938 | 0.579 | 0.616 |
| 1-minute | 0.4528 → **0.4330** | 0.4562 → **0.4202** | +19.7 | +36.1 | 0.878 | 0.887 | 0.556 | 0.585 |
| 5-minute (to close) | 0.4781 → **0.4648** | 0.5337 → **0.4875** | +13.3 | +43.7 | 0.852 | 0.838 | 0.546 | 0.562 |

Lower absolute log loss means the reference-anchored outcome is more predictable. **At 5 minutes ETH is more predictable than BTC**: lower log loss, higher AUC and better calibration. Even the naive baseline is far better on ETH there, because ETH's volatility is smoother and more forecastable (docs/RESEARCH_ETH.md, finding 7), so the model's *improvement* over naive is smaller although its absolute accuracy is higher. **From 10 s to 1 minute BTC is more predictable.** Both start from the same naive level, but BTC's spot lags its perpetual for longer, so it keeps more short-horizon directional signal (finding 3).

## 2. Pure direction from *now* (displacement removed)

This is P(S(t+h) > S(t)). It isolates genuine predictive power: no information comes from where the price sits relative to K.

| horizon | log loss | AUC | accuracy | top-10%-confidence accuracy | IC (Spearman) |
|---|---|---|---|---|---|
| 10-second | 0.6697 | 0.624 | 0.590 | 0.716 | 0.217 |
| 15-second | 0.6762 | 0.606 | 0.576 | 0.689 | 0.179 |
| 30-second | 0.6829 | 0.579 | 0.556 | 0.652 | 0.129 |
| 1-minute | 0.6881 | 0.556 | 0.539 | 0.607 | 0.088 |
| 5-minute (to close) | 0.6893 | 0.546 | 0.530 | 0.606 | 0.061 |

## 3. Magnitude and speed

| horizon | QLIKE naive → model | corr(log σ̂², log RV) naive → model | pinball (bps) naive → full | 50% cov | 90% cov |
|---|---|---|---|---|---|
| 10-second | 4.347 → **3.977** | 0.500 → **0.542** | 0.553 → **0.535** | 0.548 | 0.890 |
| 15-second | 2.873 → **2.501** | 0.544 → **0.584** | 0.695 → **0.674** | 0.532 | 0.894 |
| 30-second | 1.574 → **1.196** | 0.630 → **0.671** | 1.017 → **0.992** | 0.534 | 0.900 |
| 1-minute | 1.089 → **0.696** | 0.702 → **0.742** | 1.465 → **1.430** | 0.523 | 0.904 |
| 5-minute (to close) | 1.209 → **0.876** | 0.759 → **0.814** | 2.164 → **2.125** | 0.530 | 0.909 |

## 4. Levels: thresholds, touches, which comes first

### 10-second

| question | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| end ≥ K-20bp | – | 0.966 | 0.0274 | 0.0243 | **0.0242** | 0.997 |
| end ≥ K-10bp | – | 0.888 | 0.0787 | 0.0698 | **0.0697** | 0.992 |
| end ≥ K+10bp | – | 0.108 | 0.0767 | 0.0681 | **0.0680** | 0.992 |
| end ≥ K+20bp | – | 0.033 | 0.0269 | 0.0233 | **0.0232** | 0.997 |
| touch K+5bp | 1,082,146 | 0.047 | 0.1511 | 0.1496 | **0.1136** | 0.935 |
| touch K-5bp | 1,071,832 | 0.048 | 0.1594 | 0.1564 | **0.1185** | 0.932 |
| touch K+10bp | 1,230,349 | 0.024 | 0.0756 | 0.0731 | **0.0582** | 0.965 |
| touch K-10bp | 1,224,933 | 0.024 | 0.0788 | 0.0761 | **0.0601** | 0.963 |
| touch K+20bp | 1,328,121 | 0.008 | 0.0270 | 0.0247 | **0.0207** | 0.982 |
| touch K-20bp | 1,326,293 | 0.009 | 0.0276 | 0.0255 | **0.0214** | 0.983 |
| touch K+30bp | 1,353,425 | 0.004 | 0.0134 | 0.0115 | **0.0100** | 0.980 |
| touch K-30bp | 1,353,175 | 0.004 | 0.0132 | 0.0117 | **0.0100** | 0.985 |
| ±5bp: which first (3-class) | 1,370,379 | up-first 0.045 | 0.3452 | 0.3231 | **0.2717** | 0.645 (up vs down) |
| ±10bp: which first (3-class) | 1,370,477 | up-first 0.009 | 0.0960 | 0.0813 | **0.0677** | 0.665 (up vs down) |
| ±20bp: which first (3-class) | 1,370,492 | up-first 0.001 | 0.0202 | 0.0159 | **0.0123** | 0.787 (up vs down) |
| ±30bp: which first (3-class) | 1,370,494 | up-first 0.000 | 0.0076 | 0.0061 | **0.0045** | 0.823 (up vs down) |

### 15-second

| question | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| end ≥ K-20bp | – | 0.965 | 0.0353 | 0.0311 | **0.0310** | 0.994 |
| end ≥ K-10bp | – | 0.885 | 0.0993 | 0.0888 | **0.0886** | 0.987 |
| end ≥ K+10bp | – | 0.111 | 0.0970 | 0.0867 | **0.0866** | 0.987 |
| end ≥ K+20bp | – | 0.034 | 0.0348 | 0.0300 | **0.0299** | 0.994 |
| touch K+5bp | 1,082,146 | 0.065 | 0.1873 | 0.1836 | **0.1477** | 0.925 |
| touch K-5bp | 1,071,832 | 0.067 | 0.1965 | 0.1913 | **0.1530** | 0.922 |
| touch K+10bp | 1,230,349 | 0.033 | 0.0977 | 0.0931 | **0.0782** | 0.957 |
| touch K-10bp | 1,224,933 | 0.034 | 0.1005 | 0.0959 | **0.0798** | 0.957 |
| touch K+20bp | 1,328,121 | 0.011 | 0.0363 | 0.0326 | **0.0283** | 0.978 |
| touch K-20bp | 1,326,293 | 0.012 | 0.0363 | 0.0331 | **0.0287** | 0.980 |
| touch K+30bp | 1,353,425 | 0.005 | 0.0186 | 0.0159 | **0.0140** | 0.975 |
| touch K-30bp | 1,353,175 | 0.005 | 0.0177 | 0.0155 | **0.0136** | 0.984 |
| ±5bp: which first (3-class) | 1,370,373 | up-first 0.070 | 0.4690 | 0.4491 | **0.3820** | 0.625 (up vs down) |
| ±10bp: which first (3-class) | 1,370,476 | up-first 0.016 | 0.1514 | 0.1293 | **0.1111** | 0.645 (up vs down) |
| ±20bp: which first (3-class) | 1,370,492 | up-first 0.002 | 0.0334 | 0.0264 | **0.0210** | 0.773 (up vs down) |
| ±30bp: which first (3-class) | 1,370,494 | up-first 0.001 | 0.0129 | 0.0103 | **0.0077** | 0.832 (up vs down) |

### 30-second

| question | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| end ≥ K-20bp | – | 0.961 | 0.0536 | 0.0472 | **0.0470** | 0.988 |
| end ≥ K-10bp | – | 0.877 | 0.1465 | 0.1315 | **0.1313** | 0.971 |
| end ≥ K+10bp | – | 0.119 | 0.1437 | 0.1289 | **0.1286** | 0.971 |
| end ≥ K+20bp | – | 0.037 | 0.0536 | 0.0462 | **0.0460** | 0.987 |
| touch K+5bp | 1,082,146 | 0.110 | 0.2678 | 0.2589 | **0.2236** | 0.901 |
| touch K-5bp | 1,071,832 | 0.113 | 0.2771 | 0.2664 | **0.2294** | 0.899 |
| touch K+10bp | 1,230,349 | 0.058 | 0.1517 | 0.1409 | **0.1260** | 0.939 |
| touch K-10bp | 1,224,933 | 0.059 | 0.1560 | 0.1447 | **0.1288** | 0.938 |
| touch K+20bp | 1,328,121 | 0.020 | 0.0605 | 0.0531 | **0.0483** | 0.968 |
| touch K-20bp | 1,326,293 | 0.021 | 0.0597 | 0.0528 | **0.0482** | 0.971 |
| touch K+30bp | 1,353,425 | 0.009 | 0.0318 | 0.0264 | **0.0241** | 0.974 |
| touch K-30bp | 1,353,175 | 0.009 | 0.0304 | 0.0255 | **0.0233** | 0.980 |
| ±5bp: which first (3-class) | 1,370,365 | up-first 0.134 | 0.7114 | 0.6997 | **0.6022** | 0.600 (up vs down) |
| ±10bp: which first (3-class) | 1,370,470 | up-first 0.038 | 0.2979 | 0.2575 | **0.2321** | 0.616 (up vs down) |
| ±20bp: which first (3-class) | 1,370,492 | up-first 0.007 | 0.0758 | 0.0602 | **0.0515** | 0.732 (up vs down) |
| ±30bp: which first (3-class) | 1,370,494 | up-first 0.002 | 0.0315 | 0.0247 | **0.0194** | 0.807 (up vs down) |

### 1-minute

| question | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| end ≥ K-20bp | – | 0.955 | 0.0857 | 0.0747 | **0.0745** | 0.971 |
| end ≥ K-10bp | – | 0.862 | 0.2113 | 0.1917 | **0.1914** | 0.943 |
| end ≥ K+10bp | – | 0.133 | 0.2100 | 0.1892 | **0.1889** | 0.942 |
| end ≥ K+20bp | – | 0.043 | 0.0852 | 0.0731 | **0.0729** | 0.970 |
| touch K+5bp | 1,082,146 | 0.178 | 0.3706 | 0.3552 | **0.3214** | 0.871 |
| touch K-5bp | 1,071,832 | 0.181 | 0.3785 | 0.3619 | **0.3271** | 0.868 |
| touch K+10bp | 1,230,349 | 0.099 | 0.2361 | 0.2151 | **0.2000** | 0.911 |
| touch K-10bp | 1,224,933 | 0.100 | 0.2384 | 0.2188 | **0.2025** | 0.910 |
| touch K+20bp | 1,328,121 | 0.035 | 0.1050 | 0.0903 | **0.0843** | 0.949 |
| touch K-20bp | 1,326,293 | 0.037 | 0.1033 | 0.0896 | **0.0838** | 0.953 |
| touch K+30bp | 1,353,425 | 0.016 | 0.0577 | 0.0474 | **0.0439** | 0.961 |
| touch K-30bp | 1,353,175 | 0.017 | 0.0548 | 0.0450 | **0.0420** | 0.968 |
| ±5bp: which first (3-class) | 1,370,351 | up-first 0.226 | 0.9254 | 0.9345 | **0.8051** | 0.577 (up vs down) |
| ±10bp: which first (3-class) | 1,370,469 | up-first 0.083 | 0.5224 | 0.4672 | **0.4260** | 0.586 (up vs down) |
| ±20bp: which first (3-class) | 1,370,491 | up-first 0.018 | 0.1699 | 0.1381 | **0.1230** | 0.678 (up vs down) |
| ±30bp: which first (3-class) | 1,370,494 | up-first 0.006 | 0.0766 | 0.0601 | **0.0498** | 0.763 (up vs down) |

### 5-minute (to close)

| question | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| end ≥ K-20bp | – | 0.938 | 0.1433 | 0.1281 | **0.1280** | 0.933 |
| end ≥ K-10bp | – | 0.830 | 0.2928 | 0.2748 | **0.2749** | 0.898 |
| end ≥ K+10bp | – | 0.170 | 0.2997 | 0.2773 | **0.2771** | 0.895 |
| end ≥ K+20bp | – | 0.062 | 0.1465 | 0.1289 | **0.1286** | 0.929 |
| touch K+5bp | 1,082,146 | 0.295 | 0.4683 | 0.4579 | **0.4212** | 0.855 |
| touch K-5bp | 1,071,832 | 0.295 | 0.4677 | 0.4596 | **0.4204** | 0.856 |
| touch K+10bp | 1,230,349 | 0.184 | 0.3679 | 0.3424 | **0.3218** | 0.875 |
| touch K-10bp | 1,224,933 | 0.183 | 0.3546 | 0.3398 | **0.3171** | 0.880 |
| touch K+20bp | 1,328,121 | 0.072 | 0.2010 | 0.1758 | **0.1664** | 0.909 |
| touch K-20bp | 1,326,293 | 0.073 | 0.1937 | 0.1732 | **0.1640** | 0.916 |
| touch K+30bp | 1,353,425 | 0.034 | 0.1215 | 0.0993 | **0.0934** | 0.927 |
| touch K-30bp | 1,353,175 | 0.034 | 0.1123 | 0.0944 | **0.0893** | 0.937 |
| ±5bp: which first (3-class) | 1,370,346 | up-first 0.310 | 0.9186 | 0.9617 | **0.8108** | 0.555 (up vs down) |
| ±10bp: which first (3-class) | 1,370,474 | up-first 0.167 | 0.7280 | 0.6984 | **0.6244** | 0.551 (up vs down) |
| ±20bp: which first (3-class) | 1,370,492 | up-first 0.055 | 0.3694 | 0.3180 | **0.2926** | 0.596 (up vs down) |
| ±30bp: which first (3-class) | 1,370,494 | up-first 0.023 | 0.2028 | 0.1645 | **0.1480** | 0.664 (up vs down) |

## 5. Consistency

### Month by month (main test, 5-minute model, Δ log loss in millinats)

| month | full vs naive RW | full vs structural |
|---|---|---|
| 2026-06 | +10.5 | +0.4 |
| 2026-07 | +13.0 | +0.4 |
| 2026-08 | +16.1 | +0.3 |
| 2026-09 | +14.4 | +0.4 |
| 2026-10 | +12.1 | +0.3 |
| 2026-11 | +18.0 | +3.3 |

### Walk-forward (full retrain on an expanding window for each fold)

| fold | test period | horizon | naive RW | full | full+recal | Δ full vs naive | dir. AUC |
|---|---|---|---|---|---|---|---|
| A | 2025-05-01 → 2025-09-01 | 30-second | 0.3427 | 0.3286 | 0.3286 | +14.1 [+13.1, +15.5] | 0.563 |
| A | 2025-05-01 → 2025-09-01 | 1-minute | 0.4416 | 0.4280 | 0.4281 | +13.6 [+12.2, +15.0] | 0.543 |
| A | 2025-05-01 → 2025-09-01 | 5-minute (to close) | 0.4656 | 0.4567 | 0.4569 | +8.9 [+7.6, +10.2] | 0.538 |
| B | 2025-11-01 → 2026-03-01 | 30-second | 0.3534 | 0.3355 | 0.3353 | +17.9 [+16.2, +20.2] | 0.571 |
| B | 2025-11-01 → 2026-03-01 | 1-minute | 0.4508 | 0.4351 | 0.4348 | +15.7 [+13.8, +17.7] | 0.549 |
| B | 2025-11-01 → 2026-03-01 | 5-minute (to close) | 0.4741 | 0.4631 | 0.4630 | +11.0 [+9.3, +12.8] | 0.546 |
| val | 2026-03-01 → 2026-06-01 | 10-second | 0.2246 | 0.2003 | 0.2002 | +24.3 [+21.8, +26.7] | 0.649 |
| val | 2026-03-01 → 2026-06-01 | 15-second | 0.2666 | 0.2435 | 0.2433 | +23.0 [+20.5, +25.6] | 0.628 |
| val | 2026-03-01 → 2026-06-01 | 30-second | 0.3518 | 0.3301 | 0.3298 | +21.8 [+19.7, +24.0] | 0.592 |
| val | 2026-03-01 → 2026-06-01 | 1-minute | 0.4491 | 0.4300 | 0.4296 | +19.1 [+17.2, +20.9] | 0.560 |
| val | 2026-03-01 → 2026-06-01 | 5-minute (to close) | 0.4900 | 0.4721 | 0.4720 | +17.9 [+15.1, +20.9] | 0.553 |
| main | 2026-06-01 → 2026-11-03 | 10-second | 0.2323 | 0.2059 | 0.2059 | +26.5 [+24.2, +29.2] | 0.624 |
| main | 2026-06-01 → 2026-11-03 | 15-second | 0.2730 | 0.2479 | 0.2479 | +25.1 [+22.7, +27.8] | 0.606 |
| main | 2026-06-01 → 2026-11-03 | 30-second | 0.3570 | 0.3332 | 0.3332 | +23.8 [+21.6, +26.3] | 0.579 |
| main | 2026-06-01 → 2026-11-03 | 1-minute | 0.4528 | 0.4330 | 0.4330 | +19.7 [+18.0, +21.6] | 0.556 |
| main | 2026-06-01 → 2026-11-03 | 5-minute (to close) | 0.4781 | 0.4648 | 0.4648 | +13.3 [+11.8, +15.0] | 0.546 |

(`val` was used for early stopping, so it is slightly optimistic. It is shown for completeness.)

## 6. Robustness across market regimes

Regime variables are causal (only previous days), and their thresholds are fixed on the training period. Each cell is the 5-minute log-loss improvement over the naive random walk in millinats, with a 95% day-block CI, plus AUC. The edge has to hold in **every** slice, not just on average.

### main test (Jun–Nov 2026: bear low and rebound)

| regime family | slice | windows | Δ 5-min [95% CI] | 5-min AUC | Δ 1-min | Δ 30s | 30s direction AUC |
|---|---|---|---|---|---|---|---|
| all | all | 44,352 | +13.3 [+11.7, +15.2] | 0.852 | +19.7 | +23.8 | 0.579 |
| volatility regime (7-day) | calm | 34,560 | +14.6 [+12.9, +16.6] | 0.851 | +21.0 | +25.7 | 0.583 |
| volatility regime (7-day) | normal | 6,048 | +6.8 [+3.6, +10.5] | 0.859 | +14.2 | +17.4 | 0.567 |
| volatility regime (7-day) | turbulent | 3,744 | +10.8 [+7.2, +14.9] | 0.855 | +17.2 | +17.1 | 0.563 |
| trend regime (7-day) | bear | 13,248 | +11.3 [+8.9, +14.4] | 0.851 | +16.7 | +18.8 | 0.573 |
| trend regime (7-day) | sideways | 18,720 | +15.0 [+12.6, +17.3] | 0.851 | +23.0 | +28.4 | 0.587 |
| trend regime (7-day) | bull | 12,384 | +12.7 [+10.0, +15.5] | 0.854 | +17.9 | +22.2 | 0.574 |
| drawdown from 30-day high | deep (< -3 daily sd) | 16,416 | +10.8 [+8.4, +13.2] | 0.852 | +16.5 | +18.3 | 0.572 |
| drawdown from 30-day high | shallow | 27,936 | +14.7 [+12.8, +16.9] | 0.852 | +21.6 | +27.1 | 0.583 |
| vol expansion (7d vs 30d) | expanding (> +0.3) | 6,912 | +9.8 [+6.7, +13.1] | 0.855 | +15.8 | +16.8 | 0.562 |
| vol expansion (7d vs 30d) | stable/contracting | 37,440 | +13.9 [+12.0, +16.0] | 0.852 | +20.5 | +25.1 | 0.582 |
| intraday activity (1-hour vol) | quiet hour | 24,373 | +19.7 [+17.6, +22.1] | 0.847 | +27.0 | +33.9 | 0.599 |
| intraday activity (1-hour vol) | normal hour | 13,855 | +6.3 [+4.9, +8.1] | 0.860 | +13.1 | +14.6 | 0.562 |
| intraday activity (1-hour vol) | hot hour | 8,422 | +5.3 [+3.4, +7.2] | 0.856 | +8.6 | +8.8 | 0.543 |
| calendar | weekday | 31,680 | +9.8 [+8.5, +11.0] | 0.854 | +16.2 | +18.6 | 0.572 |
| calendar | weekend | 12,672 | +22.0 [+19.0, +25.9] | 0.848 | +28.5 | +36.9 | 0.599 |

### walk-forward fold A (May–Aug 2025: bull run, +175%)

| regime family | slice | windows | Δ 5-min [95% CI] | 5-min AUC | Δ 1-min | Δ 30s | 30s direction AUC |
|---|---|---|---|---|---|---|---|
| all | all | 35,136 | +8.9 [+7.6, +10.2] | 0.857 | +13.6 | +14.1 | 0.563 |
| volatility regime (7-day) | calm | 4,608 | +7.8 [+3.9, +12.7] | 0.860 | +15.2 | +16.9 | 0.576 |
| volatility regime (7-day) | normal | 15,264 | +8.6 [+6.9, +10.2] | 0.856 | +14.0 | +14.0 | 0.564 |
| volatility regime (7-day) | turbulent | 15,264 | +9.5 [+7.8, +11.2] | 0.856 | +12.7 | +13.5 | 0.559 |
| trend regime (7-day) | bear | 6,048 | +10.0 [+7.7, +12.7] | 0.857 | +15.3 | +15.8 | 0.568 |
| trend regime (7-day) | sideways | 13,824 | +9.6 [+7.5, +11.8] | 0.855 | +15.5 | +16.1 | 0.570 |
| trend regime (7-day) | bull | 15,264 | +7.8 [+6.2, +9.4] | 0.858 | +11.2 | +11.7 | 0.555 |
| drawdown from 30-day high | deep (< -3 daily sd) | 6,336 | +9.7 [+7.1, +12.0] | 0.856 | +17.9 | +19.9 | 0.586 |
| drawdown from 30-day high | shallow | 28,800 | +8.7 [+7.2, +10.2] | 0.857 | +12.6 | +12.9 | 0.558 |
| vol expansion (7d vs 30d) | expanding (> +0.3) | 5,472 | +9.0 [+6.4, +11.0] | 0.857 | +11.9 | +14.0 | 0.560 |
| vol expansion (7d vs 30d) | stable/contracting | 29,664 | +8.9 [+7.5, +10.3] | 0.857 | +13.9 | +14.2 | 0.564 |
| intraday activity (1-hour vol) | quiet hour | 7,713 | +15.6 [+12.3, +18.8] | 0.855 | +24.8 | +25.2 | 0.602 |
| intraday activity (1-hour vol) | normal hour | 14,411 | +8.3 [+6.7, +9.9] | 0.856 | +13.5 | +14.6 | 0.563 |
| intraday activity (1-hour vol) | hot hour | 15,093 | +6.1 [+4.7, +7.6] | 0.858 | +8.1 | +8.2 | 0.540 |
| calendar | weekday | 25,056 | +6.6 [+5.6, +7.6] | 0.859 | +11.1 | +12.0 | 0.555 |
| calendar | weekend | 10,080 | +14.6 [+12.6, +16.8] | 0.852 | +19.7 | +19.4 | 0.583 |

### walk-forward fold B (Nov 2025–Feb 2026: crash −53%)

| regime family | slice | windows | Δ 5-min [95% CI] | 5-min AUC | Δ 1-min | Δ 30s | 30s direction AUC |
|---|---|---|---|---|---|---|---|
| all | all | 34,272 | +11.0 [+9.3, +12.8] | 0.853 | +15.7 | +17.9 | 0.571 |
| volatility regime (7-day) | calm | 8,928 | +16.7 [+13.0, +20.8] | 0.853 | +21.9 | +24.9 | 0.593 |
| volatility regime (7-day) | normal | 13,536 | +11.2 [+8.6, +13.9] | 0.851 | +16.5 | +18.9 | 0.574 |
| volatility regime (7-day) | turbulent | 11,808 | +6.4 [+4.4, +8.7] | 0.855 | +9.9 | +11.5 | 0.550 |
| trend regime (7-day) | bear | 14,976 | +7.7 [+5.2, +9.9] | 0.854 | +11.9 | +13.6 | 0.557 |
| trend regime (7-day) | sideways | 13,536 | +13.0 [+10.5, +15.9] | 0.852 | +17.8 | +20.7 | 0.582 |
| trend regime (7-day) | bull | 5,760 | +14.9 [+9.4, +20.4] | 0.849 | +20.3 | +22.6 | 0.583 |
| drawdown from 30-day high | deep (< -3 daily sd) | 25,920 | +9.9 [+7.8, +11.7] | 0.853 | +14.1 | +16.0 | 0.566 |
| drawdown from 30-day high | shallow | 8,352 | +14.3 [+10.6, +18.4] | 0.853 | +20.4 | +23.9 | 0.588 |
| vol expansion (7d vs 30d) | expanding (> +0.3) | 7,488 | +7.7 [+4.4, +11.2] | 0.855 | +10.9 | +12.9 | 0.551 |
| vol expansion (7d vs 30d) | stable/contracting | 26,784 | +11.9 [+9.7, +13.9] | 0.852 | +17.0 | +19.3 | 0.576 |
| intraday activity (1-hour vol) | quiet hour | 11,309 | +21.5 [+18.4, +24.6] | 0.847 | +28.6 | +32.6 | 0.611 |
| intraday activity (1-hour vol) | normal hour | 11,301 | +8.5 [+6.7, +10.8] | 0.853 | +13.3 | +15.0 | 0.566 |
| intraday activity (1-hour vol) | hot hour | 13,425 | +4.1 [+2.7, +5.7] | 0.857 | +6.7 | +8.0 | 0.537 |
| calendar | weekday | 24,480 | +8.2 [+6.7, +9.9] | 0.854 | +12.2 | +13.7 | 0.560 |
| calendar | weekend | 9,792 | +18.0 [+14.1, +21.7] | 0.850 | +24.4 | +28.5 | 0.599 |

### How regime handling was chosen (validation period only)

| horizon | configuration | above-ref LL | Δ vs base (millinats) | vol QLIKE | drift IC |
|---|---|---|---|---|---|
| 30-second | base | 0.32616 | +0.00 | 1.1644 | 0.1465 |
| 30-second | base+decay180 | 0.32648 | +0.32 | 1.1661 | 0.1464 |
| 30-second | base+decay365 | 0.32656 | +0.39 | 1.1651 | 0.1465 |
| 30-second | +regime | 0.32614 | -0.02 | 1.1628 | 0.1461 |
| 30-second | +regime+decay180 | 0.32662 | +0.45 | 1.1647 | 0.1461 |
| 30-second | +regime+decay365 | 0.32654 | +0.37 | 1.1674 | 0.1466 |
| 5-minute (to close) | base | 0.47397 | +0.00 | 0.8686 | 0.0697 |
| 5-minute (to close) | base+decay180 | 0.47373 | -0.24 | 0.8665 | 0.0733 |
| 5-minute (to close) | base+decay365 | 0.47377 | -0.20 | 0.8719 | 0.0707 |
| 5-minute (to close) | +regime | 0.47395 | -0.01 | 0.8684 | 0.0708 |
| 5-minute (to close) | +regime+decay180 | 0.47414 | +0.17 | 0.8725 | 0.0722 |
| 5-minute (to close) | +regime+decay365 | 0.47406 | +0.10 | 0.8721 | 0.0734 |

Regime state is used in the volatility engine only. On ETH validation it is neutral there (30 s: 0.32616 → 0.32614; 5 min: 0.47397 → 0.47395) and is kept for adaptivity. The rule is never to let regime or calendar variables drive direction, because two years contain too few regimes to learn regime-dependent drift. Recency weighting with a 180-day half-life is adopted only for horizons where no validation month got worse: 10 s, 15 s and 5 min. It hurt 30 s and 60 s in every month.

### Where the BTC-leader block belongs (validation)

| horizon | BTC features everywhere | volatility engine only | nowhere |
|---|---|---|---|
| 1-minute | 0.41054 (IC 0.0984) | 0.41062 (IC 0.0982) | 0.41104 (IC 0.0978) |
| 5-minute (to close) | 0.47397 (IC 0.0697) | 0.47379 (IC 0.0737) | 0.47389 (IC 0.0734) |

The BTC lead drives direction up to 60 s and feeds volatility at every horizon. For the 5-minute drift it is noise; that model receives the lead through the stacked 30 s / 60 s forecasts (docs/RESEARCH_ETH.md).

## 7. What drives the predictions (ablations on the validation period)

### 30-second

| feature set | drift IC | direction AUC | above-ref LL (structural) | Δ LL vs all (millinats) | vol QLIKE |
|---|---|---|---|---|---|
| all | 0.1465 | 0.5889 | 0.32616 | +0.00 | 1.1644 |
| no_cross_asset_btc | 0.1441 | 0.5871 | 0.32654 | +0.38 | 1.1660 |
| no_futures | 0.1074 | 0.5613 | 0.32836 | +2.19 | 1.1677 |
| no_flow | 0.1453 | 0.5882 | 0.32618 | +0.02 | 1.1654 |
| no_window_state | 0.1463 | 0.5888 | 0.32628 | +0.11 | 1.1653 |
| no_round_levels | 0.1463 | 0.5886 | 0.32640 | +0.23 | 1.1637 |
| no_momentum | 0.1440 | 0.5871 | 0.32673 | +0.57 | 1.1715 |
| spot_price_only | 0.0890 | 0.5482 | 0.32924 | +3.07 | 1.1712 |
| no_futures_no_cross | 0.0906 | 0.5489 | 0.32917 | +3.01 | 1.1702 |

A linear (ridge) drift model on the same features reaches IC 0.1395 (AUC 0.5825), against 0.1465 for LightGBM.

Top drift features (gain share): `basis_dev_60` 0.20, `basis_dev_300` 0.15, `basis_dev_3600` 0.04, `zfret_1` 0.03, `zfret_2` 0.02, `zfret_3` 0.01, `x_zfret_1` 0.01, `lrv_180` 0.01, `zfret_10` 0.01, `zfret_5` 0.01

### 5-minute (to close)

| feature set | drift IC | direction AUC | above-ref LL (structural) | Δ LL vs all (millinats) | vol QLIKE |
|---|---|---|---|---|---|
| all | 0.0697 | 0.5498 | 0.47397 | +0.00 | 0.8686 |
| no_cross_asset_btc | 0.0734 | 0.5519 | 0.47389 | -0.07 | 0.8698 |
| no_futures | 0.0494 | 0.5324 | 0.47479 | +0.83 | 0.8722 |
| no_flow | 0.0704 | 0.5502 | 0.47374 | -0.22 | 0.8712 |
| no_window_state | 0.0697 | 0.5497 | 0.47372 | -0.24 | 0.8653 |
| no_round_levels | 0.0702 | 0.5503 | 0.47387 | -0.10 | 0.8665 |
| no_momentum | 0.0701 | 0.5496 | 0.47431 | +0.35 | 0.8758 |
| spot_price_only | 0.0484 | 0.5307 | 0.47473 | +0.76 | 0.8734 |
| no_futures_no_cross | 0.0478 | 0.5308 | 0.47474 | +0.78 | 0.8717 |

A linear (ridge) drift model on the same features reaches IC 0.0645 (AUC 0.5420), against 0.0697 for LightGBM.

Top drift features (gain share): `basis_dev_300` 0.12, `basis_dev_60` 0.12, `basis_dev_3600` 0.05, `e` 0.05, `tau` 0.03, `x_corr_3600` 0.03, `zfret_2` 0.03, `lrv_14400` 0.02, `prev_win_ret` 0.02, `lvol_3600` 0.02

### Architecture experiment: temporal CNN on raw 1-second sequences

- **30-second**: the CNN alone has IC 0.1389; LightGBM drift alone 0.1472; the blend (weight on the CNN 0.1, chosen on held-out days) 0.1472. Correlation between the two forecasts: 0.93.

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
