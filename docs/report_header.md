# REPORT — BTC movement relative to the fixed 5-minute reference

**Bottom line (held-out test, Jun 1 → Nov 2 2026, 44,352 five-minute windows never seen in development):**

* **5-minute:** `P(close ≥ K)` evaluated continuously through the window (every ~10 s) has log loss **0.487**,
  against **0.534** for the usual "random walk + recent volatility" estimate. That is +47 millinats per decision,
  with the improvement positive in **every month** and in both walk-forward folds. AUC is 0.838, overall accuracy
  74.5%, and accuracy is 90% in the last minute of the window. Calibration error is 0.003.
* **1-minute:** `P(S(t+60) ≥ K)` has log loss **0.420** against 0.456, AUC 0.887.
* **30-second:** `P(S(t+30) ≥ K)` has log loss **0.316** against 0.358, AUC 0.938. The learned heads add a further
  +9.5 millinats [6.8, 12.9] over the strong analytic model.
* **Pure direction from now**, with no displacement information, has 30s AUC 0.617, overall accuracy 58.3%, and
  **71.4% accuracy on the 10% most confident calls**. The 1-minute equivalents are AUC 0.585 and 66.4%.
* **Magnitude and speed** are well calibrated. 50% and 90% predictive intervals cover 51–54% and 89–90% of
  outcomes at every horizon. The volatility forecast more than halves QLIKE relative to recent realised
  volatility at 5 minutes.
* **Levels:** touch and which-comes-first probabilities improve strongly on the analytic formulas. For example,
  the 3-class log loss for ±5 bp at 5 minutes goes from 0.891 to 0.751.

How to read the numbers. Late in the window most of `P(close ≥ K)` is "physics": the displacement from K
measured in units of remaining volatility. Every model gets the easy part right, so the honest comparison is
against strong baselines, not against a coin flip. The genuinely predictive part lives in three places:
1. a much better volatility forecast;
2. a short-horizon drift driven mainly by the perpetual→spot lead-lag;
3. learned corrections of the shape, touches and first passages.

All three are measured separately below. The window open (`e = 0`), when the price sits exactly at K, is the
pure-direction case. There the 5-minute edge is small (AUC 0.53), while the 30-second edge is real (AUC 0.62).

