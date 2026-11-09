# Regime-sliced results — `test` ('2025-05-01', '2025-09-01') — models `artifacts/wf_A`

Thresholds for the regime variables are fixed on the training period. Δ = log-loss improvement of the full model over the naive random walk, in millinats per decision, with a 95% day-block bootstrap CI.


## all

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| all | 35,136 | 0.4656 → 0.4567 | +8.9 [+7.6, +10.2] | 0.857 | 0.0041 | +13.6 | +14.1 | 0.563 |

## volatility regime (7-day)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| calm | 4,608 | 0.4610 → 0.4532 | +7.8 [+3.9, +12.7] | 0.860 | 0.0127 | +15.2 | +16.9 | 0.576 |
| normal | 15,264 | 0.4654 → 0.4568 | +8.6 [+6.9, +10.2] | 0.856 | 0.0053 | +14.0 | +14.0 | 0.564 |
| turbulent | 15,264 | 0.4673 → 0.4578 | +9.5 [+7.8, +11.2] | 0.856 | 0.0038 | +12.7 | +13.5 | 0.559 |

## trend regime (7-day)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| bear | 6,048 | 0.4678 → 0.4578 | +10.0 [+7.7, +12.7] | 0.857 | 0.0068 | +15.3 | +15.8 | 0.568 |
| sideways | 13,824 | 0.4685 → 0.4589 | +9.6 [+7.5, +11.8] | 0.855 | 0.0047 | +15.5 | +16.1 | 0.570 |
| bull | 15,264 | 0.4622 → 0.4544 | +7.8 [+6.2, +9.4] | 0.858 | 0.0068 | +11.2 | +11.7 | 0.555 |

## drawdown from 30-day high

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| deep (< -3 daily sd) | 6,336 | 0.4682 → 0.4586 | +9.7 [+7.1, +12.0] | 0.856 | 0.0047 | +17.9 | +19.9 | 0.586 |
| shallow | 28,800 | 0.4651 → 0.4563 | +8.7 [+7.2, +10.2] | 0.857 | 0.0056 | +12.6 | +12.9 | 0.558 |

## vol expansion (7d vs 30d)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| expanding (> +0.3) | 5,472 | 0.4663 → 0.4573 | +9.0 [+6.4, +11.0] | 0.857 | 0.0045 | +11.9 | +14.0 | 0.560 |
| stable/contracting | 29,664 | 0.4655 → 0.4566 | +8.9 [+7.5, +10.3] | 0.857 | 0.0042 | +13.9 | +14.2 | 0.564 |

## intraday activity (1-hour vol)

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| quiet hour | 7,713 | 0.4754 → 0.4598 | +15.6 [+12.3, +18.8] | 0.855 | 0.0041 | +24.8 | +25.2 | 0.602 |
| normal hour | 14,411 | 0.4657 → 0.4574 | +8.3 [+6.7, +9.9] | 0.856 | 0.0082 | +13.5 | +14.6 | 0.563 |
| hot hour | 15,093 | 0.4608 → 0.4547 | +6.1 [+4.7, +7.6] | 0.858 | 0.0047 | +8.1 | +8.2 | 0.540 |

## calendar

| slice | windows | 5-min naive → full | Δ 5-min | 5-min AUC | 5-min ECE | 1-min Δ | 30s Δ | 30s dir. AUC |
|---|---|---|---|---|---|---|---|---|
| weekday | 25,056 | 0.4607 → 0.4541 | +6.6 [+5.6, +7.6] | 0.859 | 0.0037 | +11.1 | +12.0 | 0.555 |
| weekend | 10,080 | 0.4779 → 0.4633 | +14.6 [+12.6, +16.8] | 0.852 | 0.0068 | +19.7 | +19.4 | 0.583 |
