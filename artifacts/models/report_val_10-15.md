# Out-of-sample report — split `val` ('2026-03-01', '2026-06-01')  (809,850 decision rows, 26,208 five-minute windows)


## Horizon 10: 10-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0065 | 0.504 |
| naive_rw | 0.2246 | 0.0662 | 0.9724 | 0.0200 | 0.911 |
| vol_only | 0.2195 | 0.0672 | 0.9729 | 0.0288 | 0.911 |
| structural | 0.2055 | 0.0630 | 0.9745 | 0.0110 | 0.911 |
| full | 0.2003 | 0.0611 | 0.9756 | 0.0039 | 0.915 |
| full+recal | 0.2002 | 0.0610 | 0.9756 | 0.0010 | 0.915 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.145 millinats, 95% CI [0.067, 0.234]

log-loss improvement of `full` over `naive_rw`: 24.307 millinats/decision, 95% day-block CI [21.799, 26.697]

log-loss improvement of `full` over `structural`: 5.202 millinats/decision, 95% day-block CI [3.889, 6.445]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 26,208 | 0.6931 | 0.6945 | 0.6743 | 0.6685 | 0.615 | 0.587 |
| 1-59 | 154,650 | 0.6931 | 0.3557 | 0.3300 | 0.3201 | 0.937 | 0.860 |
| 60-119 | 157,248 | 0.6931 | 0.2168 | 0.1975 | 0.1922 | 0.977 | 0.924 |
| 120-179 | 157,248 | 0.6931 | 0.1736 | 0.1568 | 0.1528 | 0.986 | 0.941 |
| 180-239 | 157,248 | 0.6931 | 0.1482 | 0.1326 | 0.1293 | 0.990 | 0.951 |
| 240-299 | 133,638 | 0.6931 | 0.1398 | 0.1221 | 0.1189 | 0.991 | 0.956 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-03 | 17.94 | 2.72 |
| 2026-04 | 24.55 | 5.19 |
| 2026-05 | 30.65 | 7.77 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 281,820 | 0.018 | 0.016 |
| 0.1-0.2 | 39,638 | 0.146 | 0.131 |
| 0.2-0.3 | 24,636 | 0.246 | 0.231 |
| 0.3-0.4 | 18,248 | 0.349 | 0.344 |
| 0.4-0.5 | 20,416 | 0.452 | 0.450 |
| 0.5-0.6 | 24,514 | 0.550 | 0.549 |
| 0.6-0.7 | 23,549 | 0.650 | 0.654 |
| 0.7-0.8 | 27,133 | 0.753 | 0.759 |
| 0.8-0.9 | 42,953 | 0.855 | 0.868 |
| 0.9-1.0 | 283,333 | 0.981 | 0.983 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=707,929)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6579 | 0.6498 | 0.608 |
| full | 0.6579 | 0.6493 | 0.608 |

Information coefficient of the drift forecast: Pearson 0.1712, Spearman 0.2418
Top-decile-confidence directional accuracy: 0.757 (n=70,793)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 4.1760 | 3.8111 |
| corr(log forecast var, log realised var) | 0.4787 | 0.5265 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 0.5862 | 0.577 | 0.852 | 5.50 |
| structural | 0.5622 | 0.576 | 0.903 | 6.27 |
| full | 0.5611 | 0.552 | 0.897 | 6.19 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.962 | 0.0319 | 0.0268 | 0.0267 | 0.996 |
| -10 | 0.884 | 0.0841 | 0.0727 | 0.0725 | 0.991 |
| +10 | 0.113 | 0.0840 | 0.0725 | 0.0723 | 0.991 |
| +20 | 0.036 | 0.0319 | 0.0266 | 0.0265 | 0.995 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 632,031 | 0.049 | 0.1639 | 0.1610 | 0.1195 | 0.933 |
| K-5bp | 630,092 | 0.049 | 0.1667 | 0.1639 | 0.1217 | 0.930 |
| K+10bp | 722,945 | 0.025 | 0.0878 | 0.0824 | 0.0649 | 0.958 |
| K-10bp | 720,700 | 0.026 | 0.0878 | 0.0824 | 0.0648 | 0.959 |
| K+20bp | 782,724 | 0.009 | 0.0342 | 0.0304 | 0.0254 | 0.974 |
| K-20bp | 781,103 | 0.009 | 0.0337 | 0.0300 | 0.0250 | 0.976 |
| K+30bp | 798,819 | 0.004 | 0.0164 | 0.0141 | 0.0121 | 0.975 |
| K-30bp | 797,855 | 0.004 | 0.0162 | 0.0140 | 0.0119 | 0.978 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 809,775 | 0.048 | 0.3839 | 0.3579 | 0.2920 | 0.665 |
| 10 | 809,840 | 0.010 | 0.1202 | 0.0991 | 0.0813 | 0.707 |
| 20 | 809,850 | 0.002 | 0.0268 | 0.0214 | 0.0157 | 0.820 |
| 30 | 809,850 | 0.000 | 0.0087 | 0.0072 | 0.0051 | 0.876 |

## Horizon 15: 15-second

### P(S(t+h) ≥ K) — above the fixed 5-minute reference (decision times whose horizon stays inside the window)

| model | log loss | Brier | AUC | ECE | accuracy |
|---|---|---|---|---|---|
| climatology | 0.6931 | 0.2500 | 0.5000 | 0.0063 | 0.503 |
| naive_rw | 0.2666 | 0.0798 | 0.9601 | 0.0185 | 0.889 |
| vol_only | 0.2595 | 0.0807 | 0.9608 | 0.0285 | 0.889 |
| structural | 0.2472 | 0.0768 | 0.9629 | 0.0107 | 0.891 |
| full | 0.2435 | 0.0754 | 0.9638 | 0.0041 | 0.894 |
| full+recal | 0.2433 | 0.0754 | 0.9638 | 0.0012 | 0.894 |

log-loss change from causal trailing recalibration (full -> full+recal): 0.156 millinats, 95% CI [0.064, 0.252]

log-loss improvement of `full` over `naive_rw`: 23.050 millinats/decision, 95% day-block CI [20.539, 25.563]

log-loss improvement of `full` over `structural`: 3.684 millinats/decision, 95% day-block CI [2.622, 4.826]

By elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):

| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |
|---|---|---|---|---|---|---|---|
| 0-0 | 26,208 | 0.6931 | 0.6941 | 0.6793 | 0.6758 | 0.600 | 0.575 |
| 1-59 | 154,650 | 0.6931 | 0.4078 | 0.3840 | 0.3773 | 0.911 | 0.829 |
| 60-119 | 157,248 | 0.6931 | 0.2649 | 0.2445 | 0.2407 | 0.965 | 0.901 |
| 120-179 | 157,248 | 0.6931 | 0.2148 | 0.1961 | 0.1930 | 0.977 | 0.923 |
| 180-239 | 157,248 | 0.6931 | 0.1825 | 0.1664 | 0.1640 | 0.984 | 0.936 |
| 240-299 | 120,543 | 0.6931 | 0.1718 | 0.1531 | 0.1511 | 0.986 | 0.942 |

Monthly consistency (log-loss improvement of full vs naive_rw, millinats):

| month | vs naive_rw | vs structural |
|---|---|---|
| 2026-03 | 16.76 | 1.66 |
| 2026-04 | 23.18 | 3.85 |
| 2026-05 | 29.42 | 5.62 |

Reliability of `full` (all elapsed times):

| p bin | n | mean p | observed |
|---|---|---|---|
| 0.0-0.1 | 251,106 | 0.021 | 0.019 |
| 0.1-0.2 | 45,553 | 0.146 | 0.135 |
| 0.2-0.3 | 31,061 | 0.248 | 0.230 |
| 0.3-0.4 | 24,735 | 0.349 | 0.339 |
| 0.4-0.5 | 27,162 | 0.452 | 0.450 |
| 0.5-0.6 | 30,511 | 0.550 | 0.548 |
| 0.6-0.7 | 28,938 | 0.650 | 0.656 |
| 0.7-0.8 | 33,260 | 0.753 | 0.759 |
| 0.8-0.9 | 50,994 | 0.855 | 0.866 |
| 0.9-1.0 | 249,825 | 0.978 | 0.980 |

### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n=740,619)

| model | log loss (coin=0.6931) | AUC | accuracy |
|---|---|---|---|
| structural | 0.6672 | 0.6282 | 0.591 |
| full | 0.6672 | 0.6280 | 0.592 |

Information coefficient of the drift forecast: Pearson 0.1471, Spearman 0.2034
Top-decile-confidence directional accuracy: 0.729 (n=74,062)

### Volatility / speed of movement

| metric | naive (5-min RV) | model |
|---|---|---|
| QLIKE vs 5s-sampled realised var | 2.7499 | 2.3901 |
| corr(log forecast var, log realised var) | 0.5182 | 0.5642 |

### Magnitude: predictive quantiles of the log return (n=30,000)

| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |
|---|---|---|---|---|
| naive_rw | 0.7366 | 0.541 | 0.842 | 6.74 |
| structural | 0.7096 | 0.559 | 0.907 | 8.03 |
| full | 0.7083 | 0.540 | 0.900 | 7.94 |

### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))

| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|
| -20 | 0.961 | 0.0410 | 0.0344 | 0.0342 | 0.993 |
| -10 | 0.881 | 0.1066 | 0.0932 | 0.0930 | 0.985 |
| +10 | 0.116 | 0.1053 | 0.0920 | 0.0918 | 0.985 |
| +20 | 0.037 | 0.0407 | 0.0341 | 0.0340 | 0.992 |

### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)

| level | n | base rate | naive LL | structural LL | full LL | full AUC |
|---|---|---|---|---|---|---|
| K+5bp | 632,031 | 0.068 | 0.2016 | 0.1970 | 0.1550 | 0.921 |
| K-5bp | 630,092 | 0.069 | 0.2049 | 0.2005 | 0.1574 | 0.918 |
| K+10bp | 722,945 | 0.036 | 0.1126 | 0.1047 | 0.0866 | 0.949 |
| K-10bp | 720,700 | 0.036 | 0.1127 | 0.1045 | 0.0863 | 0.950 |
| K+20bp | 782,724 | 0.013 | 0.0458 | 0.0405 | 0.0349 | 0.969 |
| K-20bp | 781,103 | 0.013 | 0.0447 | 0.0391 | 0.0336 | 0.973 |
| K+30bp | 798,819 | 0.006 | 0.0225 | 0.0193 | 0.0169 | 0.970 |
| K-30bp | 797,855 | 0.006 | 0.0222 | 0.0189 | 0.0165 | 0.977 |

### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon

| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |
|---|---|---|---|---|---|---|
| 5 | 809,771 | 0.075 | 0.5150 | 0.4931 | 0.4050 | 0.645 |
| 10 | 809,839 | 0.018 | 0.1832 | 0.1534 | 0.1294 | 0.688 |
| 20 | 809,850 | 0.003 | 0.0448 | 0.0359 | 0.0272 | 0.802 |
| 30 | 809,850 | 0.001 | 0.0157 | 0.0130 | 0.0093 | 0.878 |
