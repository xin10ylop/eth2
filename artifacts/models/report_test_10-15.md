# Out-of-sample report — split `test` ('2026-06-01', '2026-11-03')  (1,370,495 decision rows, 44,352 five-minute windows)


## Horizon 10: 10-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0097 | 0.504 |
| naive_rw | 0.2323 | 0.0679 | 0.9710 | 0.0213 | 0.909 |
| vol_only | 0.2255 | 0.0689 | 0.9714 | 0.0287 | 0.909 |
| structural | 0.2129 | 0.0655 | 0.9725 | 0.0093 | 0.907 |
| full | 0.2059 | 0.0628 | 0.9742 | 0.0013 | 0.912 |
| full+recal | 0.2059 | 0.0628 | 0.9742 | 0.0013 | 0.912 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.018 millinats, 95% CI [-0.059, 0.019]

log-loss improvement of `full` over `naive_rw`: 26.457 millinats/decision, 95% day-block CI [24.180, 29.177]

log-loss improvement of `full` over `structural`: 7.050 millinats/decision, 95% day-block CI [5.409, 9.116]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 44,352 | 0.6931 | 0.6942 | 0.6762 | 0.6687 | 0.617 | 0.590 |
| 1-59 | 261,695 | 0.6931 | 0.3733 | 0.3490 | 0.3348 | 0.931 | 0.852 |
| 60-119 | 266,112 | 0.6931 | 0.2307 | 0.2090 | 0.2013 | 0.975 | 0.921 |
| 120-179 | 266,112 | 0.6931 | 0.1830 | 0.1629 | 0.1578 | 0.985 | 0.940 |
| 180-239 | 266,112 | 0.6931 | 0.1496 | 0.1348 | 0.1305 | 0.989 | 0.951 |
| 240-299 | 226,177 | 0.6931 | 0.1360 | 0.1201 | 0.1166 | 0.991 | 0.957 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-06 | 17.90 | 2.78 |
| 2026-07 | 23.11 | 4.65 |
| 2026-08 | 34.40 | 13.74 |
| 2026-09 | 31.84 | 6.40 |
| 2026-10 | 24.43 | 7.18 |
| 2026-11 | 42.16 | 17.57 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 479,745 | 0.017 | 0.018 |
| 0.1-0.2 | 65,600 | 0.146 | 0.140 |
| 0.2-0.3 | 41,357 | 0.246 | 0.245 |
| 0.3-0.4 | 29,545 | 0.349 | 0.353 |
| 0.4-0.5 | 32,957 | 0.453 | 0.443 |
| 0.5-0.6 | 40,961 | 0.551 | 0.545 |
| 0.6-0.7 | 40,379 | 0.649 | 0.642 |
| 0.7-0.8 | 44,662 | 0.752 | 0.754 |
| 0.8-0.9 | 72,882 | 0.855 | 0.854 |
| 0.9-1.0 | 482,472 | 0.981 | 0.981 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,180,866)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6682 | 0.6255 | 0.590 |
| full | 0.6697 | 0.6242 | 0.590 |

Information coefficient of the drift forecast: Pearson 0.1586, Spearman 0.2165
Top-decile-confidence directional accuracy: 0.716 (n=118,087)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 4.3467 | 3.9765 |
| corr(log forecast var, log realised var) | 0.4999 | 0.5424 |

### Magnitude: predictive quantiles of the log return (n=60,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 0.5535 | 0.583 | 0.851 | 5.25 |
| structural | 0.5359 | 0.575 | 0.897 | 5.87 |
| full | 0.5346 | 0.548 | 0.890 | 5.78 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.966 | 0.0274 | 0.0243 | 0.0242 | 0.997 |
| -10 | 0.888 | 0.0787 | 0.0698 | 0.0697 | 0.992 |
| +10 | 0.108 | 0.0767 | 0.0681 | 0.0680 | 0.992 |
| +20 | 0.033 | 0.0269 | 0.0233 | 0.0232 | 0.997 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 1,082,146 | 0.047 | 0.1511 | 0.1496 | 0.1136 | 0.935 |
| K-5bp | 1,071,832 | 0.048 | 0.1594 | 0.1564 | 0.1185 | 0.932 |
| K+10bp | 1,230,349 | 0.024 | 0.0756 | 0.0731 | 0.0582 | 0.965 |
| K-10bp | 1,224,933 | 0.024 | 0.0788 | 0.0761 | 0.0601 | 0.963 |
| K+20bp | 1,328,121 | 0.008 | 0.0270 | 0.0247 | 0.0207 | 0.982 |
| K-20bp | 1,326,293 | 0.009 | 0.0276 | 0.0255 | 0.0214 | 0.983 |
| K+30bp | 1,353,425 | 0.004 | 0.0134 | 0.0115 | 0.0100 | 0.980 |
| K-30bp | 1,353,175 | 0.004 | 0.0132 | 0.0117 | 0.0100 | 0.985 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,370,379 | 0.045 | 0.3452 | 0.3231 | 0.2717 | 0.645 |
| 10 | 1,370,477 | 0.009 | 0.0960 | 0.0813 | 0.0677 | 0.665 |
| 20 | 1,370,492 | 0.001 | 0.0202 | 0.0159 | 0.0123 | 0.787 |
| 30 | 1,370,494 | 0.000 | 0.0076 | 0.0061 | 0.0045 | 0.823 |

## Horizon 15: 15-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0094 | 0.503 |
| naive_rw | 0.2730 | 0.0812 | 0.9589 | 0.0204 | 0.888 |
| vol_only | 0.2642 | 0.0820 | 0.9594 | 0.0280 | 0.888 |
| structural | 0.2534 | 0.0790 | 0.9608 | 0.0085 | 0.887 |
| full | 0.2479 | 0.0768 | 0.9624 | 0.0016 | 0.892 |
| full+recal | 0.2479 | 0.0768 | 0.9624 | 0.0012 | 0.892 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.017 millinats, 95% CI [-0.063, 0.032]

log-loss improvement of `full` over `naive_rw`: 25.090 millinats/decision, 95% day-block CI [22.746, 27.806]

log-loss improvement of `full` over `structural`: 5.518 millinats/decision, 95% day-block CI [4.055, 7.385]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 44,352 | 0.6931 | 0.6939 | 0.6793 | 0.6747 | 0.604 | 0.577 |
| 1-59 | 261,695 | 0.6931 | 0.4228 | 0.4005 | 0.3899 | 0.904 | 0.822 |
| 60-119 | 266,112 | 0.6931 | 0.2779 | 0.2553 | 0.2492 | 0.962 | 0.898 |
| 120-179 | 266,112 | 0.6931 | 0.2231 | 0.2015 | 0.1974 | 0.976 | 0.922 |
| 180-239 | 266,112 | 0.6931 | 0.1827 | 0.1673 | 0.1638 | 0.984 | 0.936 |
| 240-299 | 204,212 | 0.6931 | 0.1659 | 0.1498 | 0.1470 | 0.987 | 0.944 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-06 | 16.25 | 1.96 |
| 2026-07 | 20.25 | 3.13 |
| 2026-08 | 33.77 | 11.91 |
| 2026-09 | 31.17 | 4.83 |
| 2026-10 | 23.50 | 5.45 |
| 2026-11 | 37.96 | 11.16 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 428,879 | 0.021 | 0.021 |
| 0.1-0.2 | 75,788 | 0.146 | 0.142 |
| 0.2-0.3 | 51,376 | 0.248 | 0.240 |
| 0.3-0.4 | 40,176 | 0.349 | 0.346 |
| 0.4-0.5 | 44,100 | 0.452 | 0.446 |
| 0.5-0.6 | 51,183 | 0.550 | 0.548 |
| 0.6-0.7 | 48,848 | 0.650 | 0.646 |
| 0.7-0.8 | 55,493 | 0.753 | 0.752 |
| 0.8-0.9 | 86,150 | 0.855 | 0.856 |
| 0.9-1.0 | 426,602 | 0.978 | 0.978 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,236,268)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6748 | 0.6073 | 0.576 |
| full | 0.6762 | 0.6062 | 0.576 |

Information coefficient of the drift forecast: Pearson 0.1314, Spearman 0.1790
Top-decile-confidence directional accuracy: 0.689 (n=123,627)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 2.8732 | 2.5013 |
| corr(log forecast var, log realised var) | 0.5440 | 0.5840 |

### Magnitude: predictive quantiles of the log return (n=60,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 0.6951 | 0.546 | 0.842 | 6.43 |
| structural | 0.6753 | 0.555 | 0.901 | 7.50 |
| full | 0.6741 | 0.532 | 0.894 | 7.40 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.965 | 0.0353 | 0.0311 | 0.0310 | 0.994 |
| -10 | 0.885 | 0.0993 | 0.0888 | 0.0886 | 0.987 |
| +10 | 0.111 | 0.0970 | 0.0867 | 0.0866 | 0.987 |
| +20 | 0.034 | 0.0348 | 0.0300 | 0.0299 | 0.994 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 1,082,146 | 0.065 | 0.1873 | 0.1836 | 0.1477 | 0.925 |
| K-5bp | 1,071,832 | 0.067 | 0.1965 | 0.1913 | 0.1530 | 0.922 |
| K+10bp | 1,230,349 | 0.033 | 0.0977 | 0.0931 | 0.0782 | 0.957 |
| K-10bp | 1,224,933 | 0.034 | 0.1005 | 0.0959 | 0.0798 | 0.957 |
| K+20bp | 1,328,121 | 0.011 | 0.0363 | 0.0326 | 0.0283 | 0.978 |
| K-20bp | 1,326,293 | 0.012 | 0.0363 | 0.0331 | 0.0287 | 0.980 |
| K+30bp | 1,353,425 | 0.005 | 0.0186 | 0.0159 | 0.0140 | 0.975 |
| K-30bp | 1,353,175 | 0.005 | 0.0177 | 0.0155 | 0.0136 | 0.984 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,370,373 | 0.070 | 0.4690 | 0.4491 | 0.3820 | 0.625 |
| 10 | 1,370,476 | 0.016 | 0.1514 | 0.1293 | 0.1111 | 0.645 |
| 20 | 1,370,492 | 0.002 | 0.0334 | 0.0264 | 0.0210 | 0.773 |
| 30 | 1,370,494 | 0.001 | 0.0129 | 0.0103 | 0.0077 | 0.832 |
