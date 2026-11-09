# Regime-sliced results — `test` ('2025-11-01', '2026-03-01') — models `artifacts/wf_B`

Thresholds for the regime variables are fixed on the training period. Δ = log-loss improvement of the full model over the naive random walk, in millinats per decision, with a 95% day-block bootstrap CI.


## all

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| all | 34,272 | 0.4741 → 0.4631 | +11.0 [+9.3, +12.8] | 0.853 | 0.0068 | +15.7 | +17.9 | 0.571 |

## volatility regime (7-day)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| calm | 8,928 | 0.4802 → 0.4635 | +16.7 [+13.0, +20.8] | 0.853 | 0.0091 | +21.9 | +24.9 | 0.593 |
| normal | 13,536 | 0.4763 → 0.4651 | +11.2 [+8.6, +13.9] | 0.851 | 0.0106 | +16.5 | +18.9 | 0.574 |
| turbulent | 11,808 | 0.4670 → 0.4606 | +6.4 [+4.4, +8.7] | 0.855 | 0.0065 | +9.9 | +11.5 | 0.550 |

## trend regime (7-day)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| bear | 14,976 | 0.4684 → 0.4607 | +7.7 [+5.2, +9.9] | 0.854 | 0.0077 | +11.9 | +13.6 | 0.557 |
| sideways | 13,536 | 0.4769 → 0.4639 | +13.0 [+10.5, +15.9] | 0.852 | 0.0072 | +17.8 | +20.7 | 0.582 |
| bull | 5,760 | 0.4823 → 0.4674 | +14.9 [+9.4, +20.4] | 0.849 | 0.0061 | +20.3 | +22.6 | 0.583 |

## drawdown from 30-day high

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| deep (< -3 daily sd) | 25,920 | 0.4727 → 0.4628 | +9.9 [+7.8, +11.7] | 0.853 | 0.0071 | +14.1 | +16.0 | 0.566 |
| shallow | 8,352 | 0.4783 → 0.4640 | +14.3 [+10.6, +18.4] | 0.853 | 0.0080 | +20.4 | +23.9 | 0.588 |

## vol expansion (7d vs 30d)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| expanding (> +0.3) | 7,488 | 0.4676 → 0.4599 | +7.7 [+4.4, +11.2] | 0.855 | 0.0099 | +10.9 | +12.9 | 0.551 |
| stable/contracting | 26,784 | 0.4759 → 0.4640 | +11.9 [+9.7, +13.9] | 0.852 | 0.0061 | +17.0 | +19.3 | 0.576 |

## intraday activity (1-hour vol)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| quiet hour | 11,309 | 0.4927 → 0.4712 | +21.5 [+18.4, +24.6] | 0.847 | 0.0064 | +28.6 | +32.6 | 0.611 |
| normal hour | 11,301 | 0.4716 → 0.4631 | +8.5 [+6.7, +10.8] | 0.853 | 0.0067 | +13.3 | +15.0 | 0.566 |
| hot hour | 13,425 | 0.4606 → 0.4565 | +4.1 [+2.7, +5.7] | 0.857 | 0.0089 | +6.7 | +8.0 | 0.537 |

## calendar

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| weekday | 24,480 | 0.4697 → 0.4616 | +8.2 [+6.7, +9.9] | 0.854 | 0.0078 | +12.2 | +13.7 | 0.560 |
| weekend | 9,792 | 0.4850 → 0.4670 | +18.0 [+14.1, +21.7] | 0.850 | 0.0082 | +24.4 | +28.5 | 0.599 |
