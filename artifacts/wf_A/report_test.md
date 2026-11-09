# Out-of-sample report — split `test` ('2025-05-01', '2025-09-01')  (1,085,644 decision rows, 35,136 five-minute windows)


## Horizon T: 5-minute (to the window close)

### P(S(t+h) ≥ K) — above the fixed 5-minute reference

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6930 | 0.2499 | 0.5000 | 0.0118 | 0.510 |
| naive_rw | 0.4656 | 0.1556 | 0.8543 | 0.0155 | 0.757 |
| vol_only | 0.4586 | 0.1545 | 0.8558 | 0.0120 | 0.757 |
| structural | 0.4570 | 0.1540 | 0.8565 | 0.0043 | 0.758 |
| full | 0.4567 | 0.1539 | 0.8567 | 0.0041 | 0.758 |
| full+recal | 0.4569 | 0.1539 | 0.8565 | 0.0040 | 0.758 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.121 millinats, 95% CI [-0.306, 0.068]

log-loss improvement of `full` over `naive_rw`: 8.904 millinats/decision, 95% day-block CI [7.613, 10.233]

log-loss improvement of `full` over `structural`: 0.260 millinats/decision, 95% day-block CI [0.066, 0.451]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 35,136 | 0.6931 | 0.6932 | 0.6931 | 0.6924 | 0.521 | 0.514 |
| 1-59 | 207,244 | 0.6931 | 0.6554 | 0.6518 | 0.6515 | 0.657 | 0.609 |
| 60-119 | 210,816 | 0.6931 | 0.5843 | 0.5745 | 0.5742 | 0.766 | 0.693 |
| 120-179 | 210,816 | 0.6931 | 0.4903 | 0.4784 | 0.4780 | 0.851 | 0.767 |
| 180-239 | 210,816 | 0.6931 | 0.3719 | 0.3604 | 0.3602 | 0.919 | 0.838 |
| 240-299 | 210,816 | 0.6931 | 0.1916 | 0.1839 | 0.1838 | 0.979 | 0.923 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2025-05 | 7.80 | 0.59 |
| 2025-06 | 9.34 | 0.14 |
| 2025-07 | 9.54 | -0.09 |
| 2025-08 | 8.95 | 0.40 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 154,677 | 0.031 | 0.028 |
| 0.1-0.2 | 73,068 | 0.150 | 0.150 |
| 0.2-0.3 | 77,445 | 0.251 | 0.258 |
| 0.3-0.4 | 92,149 | 0.352 | 0.363 |
| 0.4-0.5 | 134,744 | 0.456 | 0.463 |
| 0.5-0.6 | 140,740 | 0.544 | 0.549 |
| 0.6-0.7 | 93,786 | 0.648 | 0.651 |
| 0.7-0.8 | 77,404 | 0.749 | 0.751 |
| 0.8-0.9 | 74,831 | 0.851 | 0.852 |
| 0.9-1.0 | 166,800 | 0.970 | 0.970 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,071,692)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6902 | 0.5374 | 0.525 |
| full | 0.6903 | 0.5376 | 0.525 |

Information coefficient of the drift forecast: Pearson 0.0319, Spearman 0.0473
Top-decile-confidence directional accuracy: 0.592 (n=107,170)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 0.8066 | 0.6087 |
| corr(log forecast var, log realised var) | 0.7679 | 0.8165 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 3.0354 | 0.478 | 0.835 | 27.58 |
| structural | 2.9783 | 0.489 | 0.895 | 33.52 |
| full | 2.9770 | 0.488 | 0.891 | 33.10 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.888 | 0.2309 | 0.2117 | 0.2118 | 0.903 |
| -10 | 0.751 | 0.3805 | 0.3622 | 0.3623 | 0.871 |
| +10 | 0.258 | 0.3879 | 0.3686 | 0.3685 | 0.870 |
| +20 | 0.116 | 0.2392 | 0.2179 | 0.2178 | 0.899 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 772,694 | 0.371 | 0.4825 | 0.4728 | 0.4521 | 0.853 |
| K-5bp | 782,095 | 0.362 | 0.4792 | 0.4684 | 0.4484 | 0.854 |
| K+10bp | 904,449 | 0.276 | 0.4492 | 0.4249 | 0.4112 | 0.854 |
| K-10bp | 909,638 | 0.272 | 0.4426 | 0.4178 | 0.4053 | 0.857 |
| K+20bp | 1,020,605 | 0.136 | 0.3106 | 0.2803 | 0.2712 | 0.877 |
| K-20bp | 1,021,780 | 0.138 | 0.3100 | 0.2762 | 0.2692 | 0.882 |
| K+30bp | 1,058,921 | 0.065 | 0.1924 | 0.1692 | 0.1615 | 0.900 |
| K-30bp | 1,059,125 | 0.070 | 0.2032 | 0.1736 | 0.1678 | 0.903 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,085,421 | 0.387 | 0.8863 | 0.9015 | 0.8180 | 0.556 |
| 10 | 1,085,619 | 0.256 | 0.8818 | 0.8426 | 0.7899 | 0.544 |
| 20 | 1,085,639 | 0.103 | 0.5913 | 0.5224 | 0.4945 | 0.563 |
| 30 | 1,085,642 | 0.045 | 0.3590 | 0.3011 | 0.2788 | 0.610 |

## Horizon 30: 30-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6930 | 0.2499 | 0.5000 | 0.0059 | 0.509 |
| naive_rw | 0.3427 | 0.1074 | 0.9296 | 0.0136 | 0.842 |
| vol_only | 0.3338 | 0.1071 | 0.9305 | 0.0162 | 0.842 |
| structural | 0.3292 | 0.1056 | 0.9320 | 0.0043 | 0.845 |
| full | 0.3286 | 0.1054 | 0.9322 | 0.0020 | 0.845 |
| full+recal | 0.3286 | 0.1054 | 0.9322 | 0.0015 | 0.845 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.026 millinats, 95% CI [-0.101, 0.043]

log-loss improvement of `full` over `naive_rw`: 14.130 millinats/decision, 95% day-block CI [13.063, 15.530]

log-loss improvement of `full` over `structural`: 0.635 millinats/decision, 95% day-block CI [0.509, 0.780]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 35,136 | 0.6931 | 0.6935 | 0.6899 | 0.6881 | 0.554 | 0.538 |
| 1-59 | 207,244 | 0.6931 | 0.4995 | 0.4863 | 0.4856 | 0.844 | 0.758 |
| 60-119 | 210,816 | 0.6931 | 0.3575 | 0.3400 | 0.3394 | 0.929 | 0.849 |
| 120-179 | 210,816 | 0.6931 | 0.2849 | 0.2702 | 0.2696 | 0.956 | 0.884 |
| 180-239 | 210,816 | 0.6931 | 0.2398 | 0.2276 | 0.2270 | 0.969 | 0.904 |
| 240-299 | 108,980 | 0.6931 | 0.2137 | 0.2042 | 0.2038 | 0.975 | 0.914 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2025-05 | 11.30 | 0.62 |
| 2025-06 | 16.73 | 0.65 |
| 2025-07 | 13.82 | 0.82 |
| 2025-08 | 14.77 | 0.45 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 246,241 | 0.026 | 0.026 |
| 0.1-0.2 | 71,674 | 0.147 | 0.146 |
| 0.2-0.3 | 55,299 | 0.249 | 0.247 |
| 0.3-0.4 | 48,311 | 0.349 | 0.355 |
| 0.4-0.5 | 57,839 | 0.455 | 0.455 |
| 0.5-0.6 | 66,156 | 0.546 | 0.549 |
| 0.6-0.7 | 50,459 | 0.650 | 0.658 |
| 0.7-0.8 | 57,109 | 0.752 | 0.755 |
| 0.8-0.9 | 73,516 | 0.853 | 0.857 |
| 0.9-1.0 | 257,204 | 0.974 | 0.975 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,066,869)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6864 | 0.5640 | 0.545 |
| full | 0.6865 | 0.5634 | 0.544 |

Information coefficient of the drift forecast: Pearson 0.0887, Spearman 0.1071
Top-decile-confidence directional accuracy: 0.625 (n=106,687)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 0.9256 | 0.7147 |
| corr(log forecast var, log realised var) | 0.6032 | 0.6417 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 1.4324 | 0.476 | 0.832 | 13.30 |
| structural | 1.4005 | 0.508 | 0.900 | 16.05 |
| full | 1.4001 | 0.508 | 0.897 | 15.95 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.930 | 0.0946 | 0.0848 | 0.0848 | 0.978 |
| -10 | 0.815 | 0.2058 | 0.1893 | 0.1893 | 0.960 |
| +10 | 0.192 | 0.2066 | 0.1905 | 0.1904 | 0.960 |
| +20 | 0.071 | 0.0946 | 0.0846 | 0.0845 | 0.978 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 772,694 | 0.157 | 0.3203 | 0.3134 | 0.2836 | 0.889 |
| K-5bp | 782,095 | 0.156 | 0.3188 | 0.3096 | 0.2816 | 0.891 |
| K+10bp | 904,449 | 0.096 | 0.2208 | 0.2078 | 0.1915 | 0.918 |
| K-10bp | 909,638 | 0.097 | 0.2217 | 0.2070 | 0.1917 | 0.919 |
| K+20bp | 1,020,605 | 0.039 | 0.1033 | 0.0931 | 0.0871 | 0.955 |
| K-20bp | 1,021,780 | 0.040 | 0.1064 | 0.0951 | 0.0893 | 0.955 |
| K+30bp | 1,058,921 | 0.017 | 0.0536 | 0.0471 | 0.0438 | 0.967 |
| K-30bp | 1,059,125 | 0.019 | 0.0573 | 0.0496 | 0.0465 | 0.970 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,085,431 | 0.223 | 0.9390 | 0.9499 | 0.8372 | 0.592 |
| 10 | 1,085,623 | 0.073 | 0.4956 | 0.4451 | 0.4166 | 0.607 |
| 20 | 1,085,639 | 0.013 | 0.1447 | 0.1179 | 0.1049 | 0.692 |
| 30 | 1,085,642 | 0.004 | 0.0579 | 0.0467 | 0.0378 | 0.773 |

## Horizon 60: 1-minute

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6930 | 0.2499 | 0.5000 | 0.0063 | 0.508 |
| naive_rw | 0.4416 | 0.1428 | 0.8778 | 0.0183 | 0.786 |
| vol_only | 0.4315 | 0.1420 | 0.8793 | 0.0177 | 0.786 |
| structural | 0.4285 | 0.1409 | 0.8806 | 0.0050 | 0.788 |
| full | 0.4280 | 0.1408 | 0.8807 | 0.0036 | 0.788 |
| full+recal | 0.4281 | 0.1408 | 0.8807 | 0.0019 | 0.788 |

log-loss change from causal trailing recalibration (full -> full+recal): -0.013 millinats, 95% CI [-0.137, 0.099]

log-loss improvement of `full` over `naive_rw`: 13.589 millinats/decision, 95% day-block CI [12.228, 15.044]

log-loss improvement of `full` over `structural`: 0.483 millinats/decision, 95% day-block CI [0.343, 0.602]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 35,136 | 0.6931 | 0.6933 | 0.6922 | 0.6913 | 0.533 | 0.522 |
| 1-59 | 207,244 | 0.6931 | 0.5736 | 0.5630 | 0.5627 | 0.777 | 0.701 |
| 60-119 | 210,816 | 0.6931 | 0.4557 | 0.4393 | 0.4389 | 0.876 | 0.793 |
| 120-179 | 210,816 | 0.6931 | 0.3770 | 0.3613 | 0.3608 | 0.919 | 0.838 |
| 180-239 | 210,816 | 0.6931 | 0.3228 | 0.3110 | 0.3104 | 0.941 | 0.864 |
| 240-299 | 3,572 | 0.6931 | 0.3057 | 0.2976 | 0.2966 | 0.946 | 0.866 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2025-05 | 9.90 | 0.59 |
| 2025-06 | 15.98 | 0.24 |
| 2025-07 | 13.28 | 0.52 |
| 2025-08 | 15.33 | 0.58 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 146,395 | 0.037 | 0.037 |
| 0.1-0.2 | 74,041 | 0.149 | 0.149 |
| 0.2-0.3 | 67,833 | 0.249 | 0.251 |
| 0.3-0.4 | 63,017 | 0.350 | 0.351 |
| 0.4-0.5 | 80,286 | 0.455 | 0.460 |
| 0.5-0.6 | 86,012 | 0.545 | 0.552 |
| 0.6-0.7 | 65,477 | 0.650 | 0.660 |
| 0.7-0.8 | 67,358 | 0.750 | 0.759 |
| 0.8-0.9 | 76,087 | 0.852 | 0.856 |
| 0.9-1.0 | 151,894 | 0.965 | 0.966 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,077,888)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6903 | 0.5416 | 0.529 |
| full | 0.6900 | 0.5434 | 0.531 |

Information coefficient of the drift forecast: Pearson 0.0624, Spearman 0.0709
Top-decile-confidence directional accuracy: 0.584 (n=107,789)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 0.6489 | 0.4334 |
| corr(log forecast var, log realised var) | 0.6941 | 0.7368 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 2.0723 | 0.459 | 0.820 | 18.80 |
| structural | 2.0301 | 0.502 | 0.899 | 23.47 |
| full | 2.0279 | 0.502 | 0.892 | 22.89 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.919 | 0.1440 | 0.1296 | 0.1294 | 0.953 |
| -10 | 0.796 | 0.2879 | 0.2671 | 0.2669 | 0.923 |
| +10 | 0.212 | 0.2911 | 0.2704 | 0.2702 | 0.923 |
| +20 | 0.083 | 0.1453 | 0.1301 | 0.1299 | 0.953 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 772,694 | 0.241 | 0.4245 | 0.4154 | 0.3868 | 0.857 |
| K-5bp | 782,095 | 0.239 | 0.4201 | 0.4082 | 0.3822 | 0.859 |
| K+10bp | 904,449 | 0.158 | 0.3262 | 0.3059 | 0.2897 | 0.883 |
| K-10bp | 909,638 | 0.158 | 0.3259 | 0.3026 | 0.2880 | 0.885 |
| K+20bp | 1,020,605 | 0.068 | 0.1721 | 0.1537 | 0.1463 | 0.926 |
| K-20bp | 1,021,780 | 0.070 | 0.1753 | 0.1546 | 0.1481 | 0.928 |
| K+30bp | 1,058,921 | 0.031 | 0.0946 | 0.0819 | 0.0771 | 0.946 |
| K-30bp | 1,059,125 | 0.033 | 0.1004 | 0.0853 | 0.0811 | 0.950 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,085,415 | 0.333 | 1.0360 | 1.0856 | 0.9446 | 0.570 |
| 10 | 1,085,621 | 0.151 | 0.7822 | 0.7323 | 0.6829 | 0.575 |
| 20 | 1,085,639 | 0.035 | 0.3112 | 0.2598 | 0.2422 | 0.638 |
| 30 | 1,085,642 | 0.012 | 0.1421 | 0.1137 | 0.0994 | 0.720 |
