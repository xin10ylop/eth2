# Out-of-sample report — split `test` ('2025-11-01', '2026-03-01')  (1,058,986 decision rows, 34,272 five-minute windows)


## Horizon T: 5-minute (to the window close)

### P(S(t+h) ≥ K) — above the fixed 5-minute reference

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0100 | 0.503 |
| naive_rw | 0.4741 | 0.1581 | 0.8494 | 0.0122 | 0.753 |
| vol_only | 0.4667 | 0.1571 | 0.8515 | 0.0198 | 0.753 |
| structural | 0.4634 | 0.1561 | 0.8525 | 0.0054 | 0.755 |
| full | 0.4631 | 0.1560 | 0.8527 | 0.0068 | 0.755 |
| full+recal | 0.4630 | 0.1561 | 0.8526 | 0.0029 | 0.755 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.124 millinats, 95% CI [-0.170, 0.421]

log-loss improvement of `full` over `naive_rw`: 10.981 millinats/decision, 95% day-block CI [9.306, 12.798]

log-loss improvement of `full` over `structural`: 0.281 millinats/decision, 95% day-block CI [0.111, 0.467]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 34,272 | 0.6931 | 0.6932 | 0.6922 | 0.6914 | 0.532 | 0.522 |
| 1-59 | 202,186 | 0.6931 | 0.6557 | 0.6517 | 0.6512 | 0.658 | 0.609 |
| 60-119 | 205,632 | 0.6931 | 0.5869 | 0.5772 | 0.5768 | 0.764 | 0.693 |
| 120-179 | 205,632 | 0.6931 | 0.4999 | 0.4876 | 0.4872 | 0.844 | 0.759 |
| 180-239 | 205,632 | 0.6931 | 0.3853 | 0.3712 | 0.3710 | 0.914 | 0.831 |
| 240-299 | 205,632 | 0.6931 | 0.2093 | 0.1944 | 0.1945 | 0.977 | 0.921 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2025-11 | 5.98 | 0.45 |
| 2025-12 | 11.55 | 0.32 |
| 2026-01 | 15.72 | 0.23 |
| 2026-02 | 10.45 | 0.10 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 141,314 | 0.031 | 0.024 |
| 0.1-0.2 | 67,770 | 0.150 | 0.129 |
| 0.2-0.3 | 73,789 | 0.251 | 0.235 |
| 0.3-0.4 | 93,005 | 0.352 | 0.339 |
| 0.4-0.5 | 138,177 | 0.455 | 0.451 |
| 0.5-0.6 | 146,733 | 0.544 | 0.546 |
| 0.6-0.7 | 97,536 | 0.648 | 0.648 |
| 0.7-0.8 | 80,187 | 0.749 | 0.749 |
| 0.8-0.9 | 71,987 | 0.850 | 0.856 |
| 0.9-1.0 | 148,488 | 0.968 | 0.971 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,039,048)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6894 | 0.5435 | 0.528 |
| full | 0.6891 | 0.5465 | 0.531 |

Information coefficient of the drift forecast: Pearson 0.0230, Spearman 0.0522
Top-decile-confidence directional accuracy: 0.609 (n=103,905)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.0897 | 0.7798 |
| corr(log forecast var, log realised var) | 0.7810 | 0.8309 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 3.0374 | 0.504 | 0.843 | 26.21 |
| structural | 2.9883 | 0.531 | 0.907 | 32.36 |
| full | 2.9878 | 0.530 | 0.905 | 32.16 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.888 | 0.2195 | 0.1992 | 0.1992 | 0.917 |
| -10 | 0.771 | 0.3525 | 0.3311 | 0.3311 | 0.886 |
| +10 | 0.221 | 0.3413 | 0.3257 | 0.3255 | 0.887 |
| +20 | 0.105 | 0.2053 | 0.1900 | 0.1900 | 0.919 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 785,370 | 0.339 | 0.4832 | 0.4744 | 0.4396 | 0.857 |
| K-5bp | 786,761 | 0.340 | 0.4894 | 0.4740 | 0.4441 | 0.853 |
| K+10bp | 903,048 | 0.240 | 0.4131 | 0.3943 | 0.3728 | 0.869 |
| K-10bp | 899,772 | 0.238 | 0.4203 | 0.3945 | 0.3752 | 0.865 |
| K+20bp | 996,723 | 0.121 | 0.2752 | 0.2510 | 0.2392 | 0.896 |
| K-20bp | 992,771 | 0.125 | 0.2841 | 0.2541 | 0.2438 | 0.895 |
| K+30bp | 1,028,707 | 0.067 | 0.1819 | 0.1606 | 0.1530 | 0.918 |
| K-30bp | 1,026,649 | 0.073 | 0.1980 | 0.1699 | 0.1628 | 0.917 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,058,639 | 0.357 | 0.9159 | 0.9434 | 0.8124 | 0.559 |
| 10 | 1,058,921 | 0.231 | 0.8324 | 0.8038 | 0.7250 | 0.548 |
| 20 | 1,058,981 | 0.101 | 0.5483 | 0.4943 | 0.4570 | 0.559 |
| 30 | 1,058,985 | 0.051 | 0.3526 | 0.3066 | 0.2813 | 0.594 |

## Horizon 30: 30-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6930 | 0.2499 | 0.5000 | 0.0076 | 0.508 |
| naive_rw | 0.3534 | 0.1102 | 0.9259 | 0.0170 | 0.841 |
| vol_only | 0.3434 | 0.1101 | 0.9271 | 0.0233 | 0.841 |
| structural | 0.3373 | 0.1080 | 0.9288 | 0.0090 | 0.842 |
| full | 0.3355 | 0.1073 | 0.9296 | 0.0066 | 0.844 |
| full+recal | 0.3353 | 0.1073 | 0.9296 | 0.0036 | 0.844 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.164 millinats, 95% CI [0.072, 0.274]

log-loss improvement of `full` over `naive_rw`: 17.918 millinats/decision, 95% day-block CI [16.161, 20.180]

log-loss improvement of `full` over `structural`: 1.796 millinats/decision, 95% day-block CI [1.225, 2.544]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 34,272 | 0.6931 | 0.6935 | 0.6878 | 0.6843 | 0.570 | 0.551 |
| 1-59 | 202,186 | 0.6931 | 0.5003 | 0.4854 | 0.4822 | 0.847 | 0.764 |
| 60-119 | 205,632 | 0.6931 | 0.3707 | 0.3510 | 0.3492 | 0.924 | 0.845 |
| 120-179 | 205,632 | 0.6931 | 0.3050 | 0.2863 | 0.2851 | 0.950 | 0.877 |
| 180-239 | 205,632 | 0.6931 | 0.2514 | 0.2369 | 0.2358 | 0.966 | 0.901 |
| 240-299 | 106,262 | 0.6931 | 0.2217 | 0.2086 | 0.2076 | 0.974 | 0.915 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2025-11 | 13.87 | 0.55 |
| 2025-12 | 19.33 | 2.59 |
| 2026-01 | 25.49 | 3.15 |
| 2026-02 | 12.10 | 0.71 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 229,550 | 0.027 | 0.025 |
| 0.1-0.2 | 72,494 | 0.147 | 0.132 |
| 0.2-0.3 | 55,850 | 0.248 | 0.232 |
| 0.3-0.4 | 47,692 | 0.349 | 0.336 |
| 0.4-0.5 | 56,792 | 0.454 | 0.449 |
| 0.5-0.6 | 67,978 | 0.547 | 0.556 |
| 0.6-0.7 | 53,857 | 0.650 | 0.664 |
| 0.7-0.8 | 60,000 | 0.752 | 0.763 |
| 0.8-0.9 | 76,291 | 0.853 | 0.860 |
| 0.9-1.0 | 239,112 | 0.972 | 0.973 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,022,082)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6846 | 0.5708 | 0.548 |
| full | 0.6846 | 0.5712 | 0.549 |

Information coefficient of the drift forecast: Pearson 0.0768, Spearman 0.1064
Top-decile-confidence directional accuracy: 0.647 (n=102,209)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 1.3701 | 1.0327 |
| corr(log forecast var, log realised var) | 0.6733 | 0.7059 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 1.4260 | 0.508 | 0.841 | 12.79 |
| structural | 1.4003 | 0.537 | 0.905 | 15.25 |
| full | 1.4002 | 0.538 | 0.904 | 15.24 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.927 | 0.0926 | 0.0832 | 0.0831 | 0.980 |
| -10 | 0.828 | 0.1890 | 0.1727 | 0.1727 | 0.964 |
| +10 | 0.168 | 0.1874 | 0.1731 | 0.1730 | 0.963 |
| +20 | 0.069 | 0.0902 | 0.0812 | 0.0811 | 0.980 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 785,370 | 0.142 | 0.3110 | 0.3025 | 0.2665 | 0.893 |
| K-5bp | 786,761 | 0.140 | 0.3119 | 0.3018 | 0.2663 | 0.891 |
| K+10bp | 903,048 | 0.086 | 0.2072 | 0.1942 | 0.1772 | 0.922 |
| K-10bp | 899,772 | 0.085 | 0.2075 | 0.1930 | 0.1760 | 0.922 |
| K+20bp | 996,723 | 0.038 | 0.1027 | 0.0924 | 0.0859 | 0.955 |
| K-20bp | 992,771 | 0.039 | 0.1043 | 0.0936 | 0.0870 | 0.956 |
| K+30bp | 1,028,707 | 0.020 | 0.0593 | 0.0522 | 0.0488 | 0.968 |
| K-30bp | 1,026,649 | 0.021 | 0.0606 | 0.0531 | 0.0496 | 0.970 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,058,652 | 0.205 | 0.8598 | 0.8592 | 0.7417 | 0.592 |
| 10 | 1,058,934 | 0.082 | 0.4886 | 0.4464 | 0.4105 | 0.599 |
| 20 | 1,058,981 | 0.020 | 0.1739 | 0.1510 | 0.1348 | 0.658 |
| 30 | 1,058,985 | 0.007 | 0.0770 | 0.0660 | 0.0558 | 0.727 |

## Horizon 60: 1-minute

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0079 | 0.506 |
| naive_rw | 0.4508 | 0.1456 | 0.8729 | 0.0175 | 0.783 |
| vol_only | 0.4404 | 0.1450 | 0.8748 | 0.0253 | 0.783 |
| structural | 0.4361 | 0.1434 | 0.8764 | 0.0101 | 0.785 |
| full | 0.4351 | 0.1431 | 0.8769 | 0.0094 | 0.786 |
| full+recal | 0.4348 | 0.1430 | 0.8769 | 0.0034 | 0.786 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.283 millinats, 95% CI [0.122, 0.466]

log-loss improvement of `full` over `naive_rw`: 15.659 millinats/decision, 95% day-block CI [13.809, 17.715]

log-loss improvement of `full` over `structural`: 0.968 millinats/decision, 95% day-block CI [0.793, 1.174]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 34,272 | 0.6931 | 0.6934 | 0.6909 | 0.6885 | 0.549 | 0.535 |
| 1-59 | 202,186 | 0.6931 | 0.5735 | 0.5627 | 0.5614 | 0.779 | 0.703 |
| 60-119 | 205,632 | 0.6931 | 0.4643 | 0.4465 | 0.4456 | 0.872 | 0.789 |
| 120-179 | 205,632 | 0.6931 | 0.3944 | 0.3764 | 0.3757 | 0.912 | 0.830 |
| 180-239 | 205,632 | 0.6931 | 0.3345 | 0.3204 | 0.3197 | 0.937 | 0.860 |
| 240-299 | 3,446 | 0.6931 | 0.3357 | 0.3139 | 0.3122 | 0.940 | 0.861 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2025-11 | 11.96 | 0.69 |
| 2025-12 | 16.91 | 0.87 |
| 2026-01 | 22.13 | 1.19 |
| 2026-02 | 10.90 | 1.13 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 129,755 | 0.038 | 0.033 |
| 0.1-0.2 | 72,050 | 0.149 | 0.131 |
| 0.2-0.3 | 66,111 | 0.250 | 0.232 |
| 0.3-0.4 | 63,376 | 0.350 | 0.335 |
| 0.4-0.5 | 79,463 | 0.455 | 0.445 |
| 0.5-0.6 | 93,108 | 0.546 | 0.552 |
| 0.6-0.7 | 69,200 | 0.650 | 0.660 |
| 0.7-0.8 | 71,086 | 0.750 | 0.760 |
| 0.8-0.9 | 76,442 | 0.851 | 0.861 |
| 0.9-1.0 | 136,209 | 0.962 | 0.964 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=1,042,607)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6892 | 0.5476 | 0.532 |
| full | 0.6890 | 0.5494 | 0.533 |

Information coefficient of the drift forecast: Pearson 0.0536, Spearman 0.0724
Top-decile-confidence directional accuracy: 0.604 (n=104,261)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 0.9704 | 0.6238 |
| corr(log forecast var, log realised var) | 0.7388 | 0.7718 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 2.0371 | 0.488 | 0.834 | 18.08 |
| structural | 2.0071 | 0.536 | 0.911 | 22.57 |
| full | 2.0051 | 0.535 | 0.907 | 22.28 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.916 | 0.1398 | 0.1253 | 0.1251 | 0.959 |
| -10 | 0.812 | 0.2633 | 0.2427 | 0.2424 | 0.932 |
| +10 | 0.184 | 0.2580 | 0.2411 | 0.2408 | 0.931 |
| +20 | 0.079 | 0.1348 | 0.1219 | 0.1217 | 0.958 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 785,370 | 0.219 | 0.4120 | 0.4033 | 0.3652 | 0.863 |
| K-5bp | 786,761 | 0.217 | 0.4150 | 0.4018 | 0.3654 | 0.861 |
| K+10bp | 903,048 | 0.140 | 0.2993 | 0.2820 | 0.2626 | 0.893 |
| K-10bp | 899,772 | 0.139 | 0.3034 | 0.2814 | 0.2625 | 0.891 |
| K+20bp | 996,723 | 0.064 | 0.1643 | 0.1476 | 0.1393 | 0.931 |
| K-20bp | 992,771 | 0.066 | 0.1684 | 0.1495 | 0.1413 | 0.932 |
| K+30bp | 1,028,707 | 0.034 | 0.0997 | 0.0865 | 0.0819 | 0.951 |
| K-30bp | 1,026,649 | 0.037 | 0.1039 | 0.0897 | 0.0847 | 0.952 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 1,058,635 | 0.297 | 0.9833 | 1.0276 | 0.8643 | 0.572 |
| 10 | 1,058,926 | 0.148 | 0.7144 | 0.6773 | 0.6138 | 0.572 |
| 20 | 1,058,981 | 0.045 | 0.3306 | 0.2911 | 0.2653 | 0.618 |
| 30 | 1,058,985 | 0.018 | 0.1683 | 0.1455 | 0.1279 | 0.678 |
