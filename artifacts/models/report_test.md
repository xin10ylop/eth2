# Out-of-sample report — split `test` ('2026-06-01', '2026-11-03')  (1,370,495 decision rows, 44,352 five-minute windows)


## Horizon T: 5-minute (to the window close)

### P(S(t+h) ≥ K) — above the fixed 5-minute reference

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0073 | 0.500 |
| naive_rw | 0.4781 | 0.1585 | 0.8492 | 0.0166 | 0.753 |
| vol_only | 0.4691 | 0.1577 | 0.8508 | 0.0212 | 0.753 |
| structural | 0.4652 | 0.1565 | 0.8519 | 0.0053 | 0.754 |
| full | 0.4648 | 0.1564 | 0.8523 | 0.0053 | 0.755 |
| full+recal | 0.4648 | 0.1564 | 0.8522 | 0.0017 | 0.755 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.020 millinats, 95% CI [-0.224, 0.197]

log-loss improvement of `full` over `naive_rw`: 13.255 millinats/decision, 95% day-block CI [11.778, 15.043]

log-loss improvement of `full` over `structural`: 0.375 millinats/decision, 95% day-block CI [0.156, 0.609]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 44,352 | 0.6931 | 0.6932 | 0.6923 | 0.6911 | 0.537 | 0.531 |
| 1-59 | 261,695 | 0.6931 | 0.6553 | 0.6507 | 0.6501 | 0.660 | 0.611 |
| 60-119 | 266,112 | 0.6931 | 0.5861 | 0.5759 | 0.5754 | 0.765 | 0.693 |
| 120-179 | 266,112 | 0.6931 | 0.5007 | 0.4857 | 0.4852 | 0.845 | 0.761 |
| 180-239 | 266,112 | 0.6931 | 0.3924 | 0.3747 | 0.3744 | 0.912 | 0.830 |
| 240-299 | 266,112 | 0.6931 | 0.2230 | 0.2043 | 0.2044 | 0.975 | 0.917 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-06 | 10.50 | 0.36 |
| 2026-07 | 12.99 | 0.39 |
| 2026-08 | 16.09 | 0.33 |
| 2026-09 | 14.39 | 0.39 |
| 2026-10 | 12.10 | 0.31 |
| 2026-11 | 18.05 | 3.34 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 191,269 | 0.032 | 0.031 |
| 0.1-0.2 | 92,633 | 0.150 | 0.142 |
| 0.2-0.3 | 100,036 | 0.251 | 0.243 |
| 0.3-0.4 | 122,410 | 0.352 | 0.346 |
| 0.4-0.5 | 181,746 | 0.455 | 0.458 |
| 0.5-0.6 | 184,866 | 0.545 | 0.551 |
| 0.6-0.7 | 120,474 | 0.648 | 0.658 |
| 0.7-0.8 | 97,021 | 0.749 | 0.757 |
| 0.8-0.9 | 90,233 | 0.850 | 0.857 |
| 0.9-1.0 | 189,807 | 0.968 | 0.971 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,336,688)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6892 | 0.5458 | 0.530 |
| full | 0.6893 | 0.5461 | 0.530 |

Information coefficient of the drift forecast: Pearson 0.0352, Spearman 0.0610
Top-decile-confidence directional accuracy: 0.606 (n=133,669)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.2094 | 0.8762 |
| corr(log forecast var, log realised var) | 0.7587 | 0.8144 |

### Magnitude: predictive quantiles of the log return (n=60,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 2.1645 | 0.486 | 0.833 | 18.79 |
| structural | 2.1265 | 0.532 | 0.912 | 24.39 |
| full | 2.1252 | 0.530 | 0.909 | 24.18 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.938 | 0.1433 | 0.1281 | 0.1280 | 0.933 |
| -10 | 0.830 | 0.2928 | 0.2748 | 0.2749 | 0.898 |
| +10 | 0.170 | 0.2997 | 0.2773 | 0.2771 | 0.895 |
| +20 | 0.062 | 0.1465 | 0.1289 | 0.1286 | 0.929 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 1,082,146 | 0.295 | 0.4683 | 0.4579 | 0.4212 | 0.855 |
| K-5bp | 1,071,832 | 0.295 | 0.4677 | 0.4596 | 0.4204 | 0.856 |
| K+10bp | 1,230,349 | 0.184 | 0.3679 | 0.3424 | 0.3218 | 0.875 |
| K-10bp | 1,224,933 | 0.183 | 0.3546 | 0.3398 | 0.3171 | 0.880 |
| K+20bp | 1,328,121 | 0.072 | 0.2010 | 0.1758 | 0.1664 | 0.909 |
| K-20bp | 1,326,293 | 0.073 | 0.1937 | 0.1732 | 0.1640 | 0.916 |
| K+30bp | 1,353,425 | 0.034 | 0.1215 | 0.0993 | 0.0934 | 0.927 |
| K-30bp | 1,353,175 | 0.034 | 0.1123 | 0.0944 | 0.0893 | 0.937 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,370,346 | 0.310 | 0.9186 | 0.9617 | 0.8108 | 0.555 |
| 10 | 1,370,474 | 0.167 | 0.7280 | 0.6984 | 0.6244 | 0.551 |
| 20 | 1,370,492 | 0.055 | 0.3694 | 0.3180 | 0.2926 | 0.596 |
| 30 | 1,370,494 | 0.023 | 0.2028 | 0.1645 | 0.1480 | 0.664 |

## Horizon 30: 30-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0092 | 0.501 |
| naive_rw | 0.3570 | 0.1097 | 0.9265 | 0.0201 | 0.843 |
| vol_only | 0.3443 | 0.1100 | 0.9275 | 0.0268 | 0.843 |
| structural | 0.3366 | 0.1074 | 0.9294 | 0.0080 | 0.844 |
| full | 0.3332 | 0.1061 | 0.9308 | 0.0039 | 0.847 |
| full+recal | 0.3332 | 0.1061 | 0.9308 | 0.0025 | 0.847 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.011 millinats, 95% CI [-0.100, 0.086]

log-loss improvement of `full` over `naive_rw`: 23.818 millinats/decision, 95% day-block CI [21.634, 26.288]

log-loss improvement of `full` over `structural`: 3.396 millinats/decision, 95% day-block CI [2.340, 4.712]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 44,352 | 0.6931 | 0.6935 | 0.6855 | 0.6829 | 0.582 | 0.555 |
| 1-59 | 261,695 | 0.6931 | 0.5081 | 0.4886 | 0.4830 | 0.847 | 0.763 |
| 60-119 | 266,112 | 0.6931 | 0.3719 | 0.3471 | 0.3432 | 0.927 | 0.850 |
| 120-179 | 266,112 | 0.6931 | 0.3033 | 0.2807 | 0.2781 | 0.953 | 0.882 |
| 180-239 | 266,112 | 0.6931 | 0.2552 | 0.2372 | 0.2347 | 0.966 | 0.903 |
| 240-299 | 137,473 | 0.6931 | 0.2330 | 0.2147 | 0.2127 | 0.972 | 0.914 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-06 | 16.08 | 1.13 |
| 2026-07 | 18.57 | 1.51 |
| 2026-08 | 31.09 | 8.18 |
| 2026-09 | 29.71 | 2.76 |
| 2026-10 | 23.06 | 3.21 |
| 2026-11 | 39.74 | 6.56 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 312,962 | 0.028 | 0.027 |
| 0.1-0.2 | 95,587 | 0.147 | 0.140 |
| 0.2-0.3 | 71,101 | 0.248 | 0.238 |
| 0.3-0.4 | 58,960 | 0.349 | 0.338 |
| 0.4-0.5 | 65,847 | 0.453 | 0.445 |
| 0.5-0.6 | 80,280 | 0.549 | 0.543 |
| 0.6-0.7 | 68,207 | 0.650 | 0.653 |
| 0.7-0.8 | 77,208 | 0.752 | 0.760 |
| 0.8-0.9 | 99,715 | 0.852 | 0.855 |
| 0.9-1.0 | 311,989 | 0.971 | 0.971 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,302,955)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6829 | 0.5792 | 0.556 |
| full | 0.6829 | 0.5793 | 0.556 |

Information coefficient of the drift forecast: Pearson 0.0968, Spearman 0.1287
Top-decile-confidence directional accuracy: 0.652 (n=130,296)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.5737 | 1.1963 |
| corr(log forecast var, log realised var) | 0.6299 | 0.6710 |

### Magnitude: predictive quantiles of the log return (n=60,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 1.0175 | 0.499 | 0.828 | 9.09 |
| structural | 0.9925 | 0.535 | 0.903 | 11.25 |
| full | 0.9917 | 0.534 | 0.900 | 11.17 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.961 | 0.0536 | 0.0472 | 0.0470 | 0.988 |
| -10 | 0.877 | 0.1465 | 0.1315 | 0.1313 | 0.971 |
| +10 | 0.119 | 0.1437 | 0.1289 | 0.1286 | 0.971 |
| +20 | 0.037 | 0.0536 | 0.0462 | 0.0460 | 0.987 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 1,082,146 | 0.110 | 0.2678 | 0.2589 | 0.2236 | 0.901 |
| K-5bp | 1,071,832 | 0.113 | 0.2771 | 0.2664 | 0.2294 | 0.899 |
| K+10bp | 1,230,349 | 0.058 | 0.1517 | 0.1409 | 0.1260 | 0.939 |
| K-10bp | 1,224,933 | 0.059 | 0.1560 | 0.1447 | 0.1288 | 0.938 |
| K+20bp | 1,328,121 | 0.020 | 0.0605 | 0.0531 | 0.0483 | 0.968 |
| K-20bp | 1,326,293 | 0.021 | 0.0597 | 0.0528 | 0.0482 | 0.971 |
| K+30bp | 1,353,425 | 0.009 | 0.0318 | 0.0264 | 0.0241 | 0.974 |
| K-30bp | 1,353,175 | 0.009 | 0.0304 | 0.0255 | 0.0233 | 0.980 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,370,365 | 0.134 | 0.7114 | 0.6997 | 0.6022 | 0.600 |
| 10 | 1,370,470 | 0.038 | 0.2979 | 0.2575 | 0.2321 | 0.616 |
| 20 | 1,370,492 | 0.007 | 0.0758 | 0.0602 | 0.0515 | 0.732 |
| 30 | 1,370,494 | 0.002 | 0.0315 | 0.0247 | 0.0194 | 0.807 |

## Horizon 60: 1-minute

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0083 | 0.500 |
| naive_rw | 0.4528 | 0.1451 | 0.8741 | 0.0217 | 0.784 |
| vol_only | 0.4395 | 0.1445 | 0.8757 | 0.0255 | 0.784 |
| structural | 0.4346 | 0.1427 | 0.8776 | 0.0093 | 0.786 |
| full | 0.4330 | 0.1422 | 0.8784 | 0.0066 | 0.788 |
| full+recal | 0.4330 | 0.1421 | 0.8784 | 0.0032 | 0.788 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.078 millinats, 95% CI [-0.066, 0.216]

log-loss improvement of `full` over `naive_rw`: 19.727 millinats/decision, 95% day-block CI [18.004, 21.561]

log-loss improvement of `full` over `structural`: 1.554 millinats/decision, 95% day-block CI [1.143, 2.051]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 44,352 | 0.6931 | 0.6934 | 0.6888 | 0.6871 | 0.563 | 0.542 |
| 1-59 | 261,695 | 0.6931 | 0.5771 | 0.5632 | 0.5610 | 0.780 | 0.704 |
| 60-119 | 266,112 | 0.6931 | 0.4663 | 0.4440 | 0.4425 | 0.875 | 0.792 |
| 120-179 | 266,112 | 0.6931 | 0.3921 | 0.3717 | 0.3704 | 0.915 | 0.833 |
| 180-239 | 266,112 | 0.6931 | 0.3396 | 0.3214 | 0.3202 | 0.937 | 0.860 |
| 240-299 | 4,417 | 0.6931 | 0.3241 | 0.3060 | 0.3041 | 0.943 | 0.870 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-06 | 14.85 | 0.87 |
| 2026-07 | 15.01 | 0.85 |
| 2026-08 | 24.36 | 3.23 |
| 2026-09 | 24.44 | 1.35 |
| 2026-10 | 19.57 | 1.42 |
| 2026-11 | 31.99 | 2.02 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 178,112 | 0.039 | 0.034 |
| 0.1-0.2 | 98,918 | 0.148 | 0.137 |
| 0.2-0.3 | 86,240 | 0.250 | 0.238 |
| 0.3-0.4 | 79,710 | 0.350 | 0.339 |
| 0.4-0.5 | 97,527 | 0.454 | 0.449 |
| 0.5-0.6 | 114,580 | 0.547 | 0.550 |
| 0.6-0.7 | 89,387 | 0.649 | 0.660 |
| 0.7-0.8 | 89,774 | 0.750 | 0.760 |
| 0.8-0.9 | 96,342 | 0.851 | 0.855 |
| 0.9-1.0 | 178,210 | 0.962 | 0.961 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,339,913)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6883 | 0.5543 | 0.538 |
| full | 0.6881 | 0.5558 | 0.539 |

Information coefficient of the drift forecast: Pearson 0.0675, Spearman 0.0879
Top-decile-confidence directional accuracy: 0.607 (n=133,992)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.0894 | 0.6964 |
| corr(log forecast var, log realised var) | 0.7024 | 0.7425 |

### Magnitude: predictive quantiles of the log return (n=60,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 1.4651 | 0.466 | 0.816 | 12.85 |
| structural | 1.4323 | 0.523 | 0.908 | 16.34 |
| full | 1.4303 | 0.523 | 0.904 | 16.23 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.955 | 0.0857 | 0.0747 | 0.0745 | 0.971 |
| -10 | 0.862 | 0.2113 | 0.1917 | 0.1914 | 0.943 |
| +10 | 0.133 | 0.2100 | 0.1892 | 0.1889 | 0.942 |
| +20 | 0.043 | 0.0852 | 0.0731 | 0.0729 | 0.970 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 1,082,146 | 0.178 | 0.3706 | 0.3552 | 0.3214 | 0.871 |
| K-5bp | 1,071,832 | 0.181 | 0.3785 | 0.3619 | 0.3271 | 0.868 |
| K+10bp | 1,230,349 | 0.099 | 0.2361 | 0.2151 | 0.2000 | 0.911 |
| K-10bp | 1,224,933 | 0.100 | 0.2384 | 0.2188 | 0.2025 | 0.910 |
| K+20bp | 1,328,121 | 0.035 | 0.1050 | 0.0903 | 0.0843 | 0.949 |
| K-20bp | 1,326,293 | 0.037 | 0.1033 | 0.0896 | 0.0838 | 0.953 |
| K+30bp | 1,353,425 | 0.016 | 0.0577 | 0.0474 | 0.0439 | 0.961 |
| K-30bp | 1,353,175 | 0.017 | 0.0548 | 0.0450 | 0.0420 | 0.968 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,370,351 | 0.226 | 0.9254 | 0.9345 | 0.8051 | 0.577 |
| 10 | 1,370,469 | 0.083 | 0.5224 | 0.4672 | 0.4260 | 0.586 |
| 20 | 1,370,491 | 0.018 | 0.1699 | 0.1381 | 0.1230 | 0.678 |
| 30 | 1,370,494 | 0.006 | 0.0766 | 0.0601 | 0.0498 | 0.763 |
