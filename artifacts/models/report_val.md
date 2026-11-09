# Out-of-sample report — split `val` ('2026-03-01', '2026-06-01')  (809,850 decision rows, 26,208 five-minute windows)


## Horizon T: 5-minute (to the window close)

### P(S(t+h) ≥ K) — above the fixed 5-minute reference

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0074 | 0.501 |
| naive_rw | 0.4900 | 0.1616 | 0.8436 | 0.0203 | 0.749 |
| vol_only | 0.4769 | 0.1601 | 0.8458 | 0.0188 | 0.749 |
| structural | 0.4727 | 0.1591 | 0.8469 | 0.0042 | 0.751 |
| full | 0.4721 | 0.1589 | 0.8474 | 0.0033 | 0.751 |
| full+recal | 0.4720 | 0.1589 | 0.8474 | 0.0021 | 0.752 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.184 millinats, 95% CI [-0.014, 0.399]

log-loss improvement of `full` over `naive_rw`: 17.880 millinats/decision, 95% day-block CI [15.137, 20.871]

log-loss improvement of `full` over `structural`: 0.584 millinats/decision, 95% day-block CI [0.324, 0.896]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 26,208 | 0.6931 | 0.6932 | 0.6925 | 0.6912 | 0.537 | 0.527 |
| 1-59 | 154,650 | 0.6931 | 0.6546 | 0.6494 | 0.6483 | 0.663 | 0.614 |
| 60-119 | 157,248 | 0.6931 | 0.5870 | 0.5748 | 0.5739 | 0.767 | 0.693 |
| 120-179 | 157,248 | 0.6931 | 0.5091 | 0.4914 | 0.4909 | 0.841 | 0.757 |
| 180-239 | 157,248 | 0.6931 | 0.4116 | 0.3880 | 0.3877 | 0.906 | 0.822 |
| 240-299 | 157,248 | 0.6931 | 0.2567 | 0.2264 | 0.2264 | 0.969 | 0.907 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-03 | 13.13 | 0.64 |
| 2026-04 | 18.69 | 1.00 |
| 2026-05 | 21.98 | 0.11 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 111,668 | 0.032 | 0.035 |
| 0.1-0.2 | 53,920 | 0.150 | 0.150 |
| 0.2-0.3 | 59,277 | 0.251 | 0.245 |
| 0.3-0.4 | 74,005 | 0.352 | 0.353 |
| 0.4-0.5 | 107,679 | 0.454 | 0.457 |
| 0.5-0.6 | 108,000 | 0.545 | 0.551 |
| 0.6-0.7 | 72,975 | 0.648 | 0.655 |
| 0.7-0.8 | 57,986 | 0.749 | 0.749 |
| 0.8-0.9 | 53,872 | 0.850 | 0.855 |
| 0.9-1.0 | 110,468 | 0.968 | 0.969 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=793,654)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6883 | 0.5504 | 0.534 |
| full | 0.6880 | 0.5529 | 0.535 |

Information coefficient of the drift forecast: Pearson 0.0398, Spearman 0.0648
Top-decile-confidence directional accuracy: 0.620 (n=79,366)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.2121 | 0.8705 |
| corr(log forecast var, log realised var) | 0.7454 | 0.8044 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 2.3095 | 0.491 | 0.828 | 19.58 |
| structural | 2.2605 | 0.534 | 0.908 | 26.08 |
| full | 2.2583 | 0.533 | 0.905 | 25.88 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.933 | 0.1642 | 0.1407 | 0.1405 | 0.921 |
| -10 | 0.825 | 0.3163 | 0.2900 | 0.2899 | 0.887 |
| +10 | 0.173 | 0.3096 | 0.2845 | 0.2839 | 0.890 |
| +20 | 0.066 | 0.1614 | 0.1403 | 0.1400 | 0.920 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 632,031 | 0.308 | 0.4836 | 0.4718 | 0.4320 | 0.852 |
| K-5bp | 630,092 | 0.309 | 0.4885 | 0.4786 | 0.4378 | 0.848 |
| K+10bp | 722,945 | 0.194 | 0.3943 | 0.3642 | 0.3388 | 0.867 |
| K-10bp | 720,700 | 0.194 | 0.3958 | 0.3682 | 0.3421 | 0.865 |
| K+20bp | 782,724 | 0.082 | 0.2314 | 0.1983 | 0.1873 | 0.899 |
| K-20bp | 781,103 | 0.080 | 0.2361 | 0.2000 | 0.1867 | 0.896 |
| K+30bp | 798,819 | 0.039 | 0.1389 | 0.1139 | 0.1069 | 0.918 |
| K-30bp | 797,855 | 0.039 | 0.1468 | 0.1167 | 0.1089 | 0.917 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 809,735 | 0.321 | 0.9581 | 0.9999 | 0.8310 | 0.566 |
| 10 | 809,835 | 0.177 | 0.8020 | 0.7556 | 0.6628 | 0.558 |
| 20 | 809,850 | 0.062 | 0.4495 | 0.3727 | 0.3376 | 0.599 |
| 30 | 809,850 | 0.026 | 0.2579 | 0.2033 | 0.1790 | 0.673 |

## Horizon 30: 30-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0063 | 0.501 |
| naive_rw | 0.3518 | 0.1089 | 0.9275 | 0.0172 | 0.843 |
| vol_only | 0.3408 | 0.1090 | 0.9290 | 0.0268 | 0.843 |
| structural | 0.3320 | 0.1060 | 0.9314 | 0.0095 | 0.846 |
| full | 0.3301 | 0.1053 | 0.9321 | 0.0060 | 0.847 |
| full+recal | 0.3298 | 0.1053 | 0.9321 | 0.0020 | 0.847 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.249 millinats, 95% CI [0.120, 0.379]

log-loss improvement of `full` over `naive_rw`: 21.777 millinats/decision, 95% day-block CI [19.691, 23.988]

log-loss improvement of `full` over `structural`: 1.899 millinats/decision, 95% day-block CI [1.369, 2.507]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 26,208 | 0.6931 | 0.6938 | 0.6871 | 0.6852 | 0.574 | 0.552 |
| 1-59 | 154,650 | 0.6931 | 0.4991 | 0.4786 | 0.4756 | 0.852 | 0.767 |
| 60-119 | 157,248 | 0.6931 | 0.3557 | 0.3345 | 0.3326 | 0.932 | 0.854 |
| 120-179 | 157,248 | 0.6931 | 0.2993 | 0.2791 | 0.2774 | 0.953 | 0.882 |
| 180-239 | 157,248 | 0.6931 | 0.2555 | 0.2365 | 0.2350 | 0.966 | 0.902 |
| 240-299 | 81,222 | 0.6931 | 0.2419 | 0.2206 | 0.2195 | 0.971 | 0.909 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-03 | 16.46 | 0.82 |
| 2026-04 | 21.30 | 2.03 |
| 2026-05 | 27.75 | 2.88 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 181,449 | 0.028 | 0.024 |
| 0.1-0.2 | 57,743 | 0.147 | 0.135 |
| 0.2-0.3 | 43,119 | 0.248 | 0.233 |
| 0.3-0.4 | 35,853 | 0.349 | 0.341 |
| 0.4-0.5 | 40,484 | 0.453 | 0.444 |
| 0.5-0.6 | 47,764 | 0.549 | 0.545 |
| 0.6-0.7 | 40,037 | 0.650 | 0.656 |
| 0.7-0.8 | 45,426 | 0.752 | 0.761 |
| 0.8-0.9 | 59,612 | 0.853 | 0.858 |
| 0.9-1.0 | 182,337 | 0.971 | 0.974 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=778,232)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6799 | 0.5906 | 0.564 |
| full | 0.6796 | 0.5918 | 0.565 |

Information coefficient of the drift forecast: Pearson 0.1077, Spearman 0.1440
Top-decile-confidence directional accuracy: 0.671 (n=77,824)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.5236 | 1.1591 |
| corr(log forecast var, log realised var) | 0.6003 | 0.6515 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 1.0794 | 0.488 | 0.825 | 9.53 |
| structural | 1.0466 | 0.533 | 0.908 | 11.98 |
| full | 1.0456 | 0.530 | 0.905 | 11.90 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.958 | 0.0633 | 0.0529 | 0.0527 | 0.984 |
| -10 | 0.873 | 0.1580 | 0.1390 | 0.1387 | 0.968 |
| +10 | 0.125 | 0.1542 | 0.1363 | 0.1360 | 0.969 |
| +20 | 0.040 | 0.0622 | 0.0523 | 0.0522 | 0.983 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 632,031 | 0.116 | 0.2849 | 0.2757 | 0.2347 | 0.896 |
| K-5bp | 630,092 | 0.116 | 0.2894 | 0.2802 | 0.2380 | 0.894 |
| K+10bp | 722,945 | 0.062 | 0.1730 | 0.1570 | 0.1386 | 0.930 |
| K-10bp | 720,700 | 0.063 | 0.1756 | 0.1587 | 0.1403 | 0.928 |
| K+20bp | 782,724 | 0.023 | 0.0761 | 0.0653 | 0.0592 | 0.958 |
| K-20bp | 781,103 | 0.023 | 0.0753 | 0.0639 | 0.0577 | 0.960 |
| K+30bp | 798,819 | 0.010 | 0.0391 | 0.0328 | 0.0298 | 0.966 |
| K-30bp | 797,855 | 0.011 | 0.0390 | 0.0321 | 0.0290 | 0.970 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 809,754 | 0.142 | 0.7696 | 0.7537 | 0.6298 | 0.619 |
| 10 | 809,835 | 0.043 | 0.3494 | 0.2970 | 0.2639 | 0.646 |
| 20 | 809,850 | 0.008 | 0.1040 | 0.0816 | 0.0674 | 0.761 |
| 30 | 809,850 | 0.003 | 0.0415 | 0.0340 | 0.0251 | 0.836 |

## Horizon 60: 1-minute

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0065 | 0.500 |
| naive_rw | 0.4491 | 0.1443 | 0.8752 | 0.0192 | 0.785 |
| vol_only | 0.4366 | 0.1435 | 0.8776 | 0.0262 | 0.785 |
| structural | 0.4311 | 0.1415 | 0.8797 | 0.0107 | 0.788 |
| full | 0.4300 | 0.1412 | 0.8801 | 0.0084 | 0.789 |
| full+recal | 0.4296 | 0.1412 | 0.8801 | 0.0027 | 0.789 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.365 millinats, 95% CI [0.167, 0.535]

log-loss improvement of `full` over `naive_rw`: 19.084 millinats/decision, 95% day-block CI [17.200, 20.898]

log-loss improvement of `full` over `structural`: 1.107 millinats/decision, 95% day-block CI [0.915, 1.285]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 26,208 | 0.6931 | 0.6935 | 0.6909 | 0.6890 | 0.556 | 0.540 |
| 1-59 | 154,650 | 0.6931 | 0.5698 | 0.5555 | 0.5543 | 0.786 | 0.708 |
| 60-119 | 157,248 | 0.6931 | 0.4535 | 0.4334 | 0.4325 | 0.881 | 0.796 |
| 120-179 | 157,248 | 0.6931 | 0.3893 | 0.3705 | 0.3693 | 0.915 | 0.832 |
| 180-239 | 157,248 | 0.6931 | 0.3462 | 0.3254 | 0.3243 | 0.935 | 0.857 |
| 240-299 | 2,598 | 0.6931 | 0.3724 | 0.3348 | 0.3344 | 0.931 | 0.859 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-03 | 14.62 | 0.95 |
| 2026-04 | 18.83 | 1.43 |
| 2026-05 | 23.95 | 0.95 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 102,649 | 0.039 | 0.030 |
| 0.1-0.2 | 58,739 | 0.149 | 0.128 |
| 0.2-0.3 | 52,088 | 0.249 | 0.237 |
| 0.3-0.4 | 48,530 | 0.350 | 0.339 |
| 0.4-0.5 | 58,230 | 0.454 | 0.447 |
| 0.5-0.6 | 66,507 | 0.547 | 0.549 |
| 0.6-0.7 | 52,685 | 0.650 | 0.656 |
| 0.7-0.8 | 54,384 | 0.750 | 0.756 |
| 0.8-0.9 | 57,628 | 0.851 | 0.863 |
| 0.9-1.0 | 103,760 | 0.962 | 0.965 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=797,153)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6878 | 0.5577 | 0.541 |
| full | 0.6873 | 0.5604 | 0.543 |

Information coefficient of the drift forecast: Pearson 0.0765, Spearman 0.0967
Top-decile-confidence directional accuracy: 0.614 (n=79,716)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.0848 | 0.6951 |
| corr(log forecast var, log realised var) | 0.6751 | 0.7281 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 1.5532 | 0.470 | 0.817 | 13.47 |
| structural | 1.5128 | 0.531 | 0.910 | 17.40 |
| full | 1.5104 | 0.532 | 0.907 | 17.27 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.950 | 0.1010 | 0.0837 | 0.0835 | 0.964 |
| -10 | 0.857 | 0.2289 | 0.2033 | 0.2029 | 0.936 |
| +10 | 0.140 | 0.2229 | 0.1988 | 0.1983 | 0.938 |
| +20 | 0.047 | 0.0977 | 0.0823 | 0.0820 | 0.963 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 632,031 | 0.187 | 0.3916 | 0.3756 | 0.3364 | 0.865 |
| K-5bp | 630,092 | 0.188 | 0.3986 | 0.3808 | 0.3411 | 0.861 |
| K+10bp | 722,945 | 0.105 | 0.2634 | 0.2368 | 0.2180 | 0.900 |
| K-10bp | 720,700 | 0.106 | 0.2676 | 0.2396 | 0.2204 | 0.898 |
| K+20bp | 782,724 | 0.040 | 0.1280 | 0.1078 | 0.1004 | 0.936 |
| K-20bp | 781,103 | 0.040 | 0.1310 | 0.1086 | 0.1003 | 0.936 |
| K+30bp | 798,819 | 0.018 | 0.0705 | 0.0577 | 0.0533 | 0.951 |
| K-30bp | 797,855 | 0.019 | 0.0713 | 0.0574 | 0.0527 | 0.954 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 809,737 | 0.237 | 0.9842 | 0.9902 | 0.8314 | 0.591 |
| 10 | 809,835 | 0.091 | 0.5925 | 0.5214 | 0.4684 | 0.606 |
| 20 | 809,850 | 0.021 | 0.2226 | 0.1769 | 0.1539 | 0.705 |
| 30 | 809,850 | 0.008 | 0.1030 | 0.0811 | 0.0642 | 0.790 |
