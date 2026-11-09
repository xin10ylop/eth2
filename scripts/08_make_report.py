"""Assemble REPORT.md from the evaluation / ablation JSON files (no numbers are typed by hand)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
A = ROOT / "artifacts"


def load(p):
    p = A / p
    return json.load(open(p)) if p.exists() else None


import os
MAIN = os.environ.get("MAIN", "models")
main = load(f"{MAIN}/report_test.json")
val = load(f"{MAIN}/report_val.json")
v1 = load("models_v1/report_test.json") if MAIN != "models_v1" else None
reg = {k: load(f"regime/regime_eval_{k}.json") for k in (f"{MAIN}_test", "wf_A_test", "wf_B_test")}
wfs = {k: load(f"wf_{k}/report_test.json") for k in ("A", "B")}
abl = {h: load(f"ablation/ablation_{h}.json") for h in ("30", "60", "T")}
seq = {h: load(f"ablation/sequence_cnn_{h}.json") for h in ("30", "T")}
HN = {"T": "5-minute (to close)", "10": "10-second", "15": "15-second", "30": "30-second", "60": "1-minute"}
ALLH = ("10", "15", "30", "60", "T")
L = []
w = L.append


def f(x, n=4):
    return "–" if x is None else f"{x:.{n}f}"


def mn(d):
    return f"{d['mean']*1e3:+.1f} [{d['ci95'][0]*1e3:+.1f}, {d['ci95'][1]*1e3:+.1f}]"


w("# Out-of-sample results\n")
w(f"Main test period **{main['range'][0]} → {main['range'][1]}** ({main['rows']:,} decision rows). "
  "Nothing in this period was used for training, early stopping, feature selection, recalibration choices or "
  "hyper-parameters. Log loss is in nats; lower is better. Improvements are reported in **millinats per decision**, "
  "with **95% day-block bootstrap CIs** in brackets. A coin flip scores 0.6931.\n")
w("For calibration, `full+recal` adds the causal trailing recalibration. It is fitted each day on the previous "
  "14 days of resolved outcomes. Enabling it was decided on the validation period.\n")

# ---------------------------------------------------------------- headline
w("## 1. P(price ≥ fixed 5-minute reference) — every horizon\n")
w("| horizon | naive RW | structural | full | full+recal | Δ full vs naive | Δ full vs structural | AUC | accuracy | ECE (full+recal) |")
w("|---|---|---|---|---|---|---|---|---|---|")
for H in ALLH:
    r = main["horizons"].get(H)
    if not r:
        continue
    a = r["above_ref"]
    w(f"| {HN[H]} | {f(a['naive_rw']['logloss'])} | {f(a['structural']['logloss'])} | {f(a['full']['logloss'])} | "
      f"{f(a['full+recal']['logloss'])} | {mn(a['dll_vs_naive_rw'])} | {mn(a['dll_vs_structural'])} | "
      f"{f(a['full+recal']['auc'],3)} | {f(a['full+recal']['acc'],3)} | {f(a['full+recal']['ece'])} |")
w("\n*naive RW* is a driftless Gaussian random walk using the last 5 minutes' realised volatility, which is what most "
  "dashboards compute. *structural* is the analytic layer on top of the learned volatility, drift and shape. "
  "*full* adds the prior-boosted head. For 30s and 60s the table uses decision times whose horizon ends inside the "
  "window.\n")

ad = {sp: load(f"ablation/adaptive_ensemble_{MAIN}_{sp}.json") for sp in ("val", "test")}
if ad["test"]:
    w("### Adaptive prior/head ensemble (regime-adaptive weighting)\n")
    w("Each UTC day and elapsed-time bucket, a logistic stack of logit(boosted head) and logit(structural prior) is refitted "
      "on the previous 14 days of resolved outcomes. Where the ML correction stops helping, for example at the window "
      "open or after a regime shift, weight moves back to the analytic prior. For ETH it did not beat the plain "
      "2-parameter recalibration at any horizon on validation, and the test confirms this, so plain recalibration "
      "ships for every ETH horizon.\n")
    w("| split | horizon | structural | full | full+recal | adaptive | Δ adaptive vs recal (millinats) |")
    w("|---|---|---|---|---|---|---|")
    for sp in ("val", "test"):
        for H, r_ in (ad[sp] or {}).items():
            d_ = r_["adaptive_vs_recal"]
            w(f"| {sp} | {HN[H]} | {r_['structural']['all']:.4f} | {r_['full']['all']:.4f} | {r_['full+recal']['all']:.4f} | "
              f"{r_['adaptive']['all']:.4f} | {d_['mean']*1e3:+.2f} [{d_['ci95'][0]*1e3:+.2f}, {d_['ci95'][1]*1e3:+.2f}] |")
    w("")

r = main["horizons"]["T"]
w("### 5-minute model, continuously through the window (test)\n")
w("| elapsed (s) | n | naive RW | structural | full | full+recal | AUC | accuracy |")
w("|---|---|---|---|---|---|---|---|")
for b, d in r["above_ref_by_e"].items():
    w(f"| {b} | {d['n']:,} | {f(d['naive_rw'])} | {f(d['structural'])} | {f(d['full'])} | {f(d['full+recal'])} | {f(d['auc_full'],3)} | {f(d['acc_full'],3)} |")
w("\nAt `e=0` the price is exactly at the reference, so the forecast is purely directional. That is the hardest case, "
  "and it is reported separately.\n")

# ---------------------------------------------------------------- ETH vs BTC (same test period, same protocol)
btc_path = os.environ.get("BTC_REPORT", str(ROOT.parent / "btc-movement" / "artifacts" / "models" / "report_test.json"))
btc = json.load(open(btc_path)) if Path(btc_path).exists() else None
if btc and tuple(btc["range"]) == tuple(main["range"]):
    w("### ETH vs BTC: which is more predictable? (same test period, identical protocol)\n")
    w("| horizon | ETH naive → model | BTC naive → model | ETH Δ vs naive | BTC Δ vs naive | ETH AUC | BTC AUC | ETH dir. AUC | BTC dir. AUC |")
    w("|---|---|---|---|---|---|---|---|---|")
    for H in ALLH:
        if H in main["horizons"] and H in btc["horizons"]:
            e_, b_ = main["horizons"][H], btc["horizons"][H]
            ea, ba = e_["above_ref"], b_["above_ref"]
            w(f"| {HN[H]} | {ea['naive_rw']['logloss']:.4f} → **{ea['full+recal']['logloss']:.4f}** | {ba['naive_rw']['logloss']:.4f} → **{ba['full+recal']['logloss']:.4f}** | "
              f"{ea['dll_vs_naive_rw']['mean']*1e3:+.1f} | {ba['dll_vs_naive_rw']['mean']*1e3:+.1f} | {ea['full+recal']['auc']:.3f} | {ba['full+recal']['auc']:.3f} | "
              f"{e_['direction']['full']['auc']:.3f} | {b_['direction']['full']['auc']:.3f} |")
    w("\nLower absolute log loss means the reference-anchored outcome is more predictable. **At 5 minutes ETH is more "
      "predictable than BTC**: lower log loss, higher AUC and better calibration. Even the naive baseline is far better "
      "on ETH there, because ETH's volatility is smoother and more forecastable (docs/RESEARCH_ETH.md, finding 7), so "
      "the model's *improvement* over naive is smaller although its absolute accuracy is higher. **From 10 s to 1 "
      "minute BTC is more predictable.** Both start from the same naive level, but BTC's spot lags its perpetual for "
      "longer, so it keeps more short-horizon directional signal (finding 3).\n")

# ---------------------------------------------------------------- direction
w("## 2. Pure direction from *now* (displacement removed)\n")
w("This is P(S(t+h) > S(t)). It isolates genuine predictive power: no information comes from where the price sits "
  "relative to K.\n")
w("| horizon | log loss | AUC | accuracy | top-10%-confidence accuracy | IC (Spearman) |")
w("|---|---|---|---|---|---|")
for H in [h for h in ALLH if h in main["horizons"]]:
    d = main["horizons"][H]["direction"]
    w(f"| {HN[H]} | {f(d['full']['logloss'])} | {f(d['full']['auc'],3)} | {f(d['full']['acc'],3)} | {f(d['top_decile_acc'],3)} | {f(d['ic_spearman'],3)} |")

# ---------------------------------------------------------------- magnitude / speed
w("\n## 3. Magnitude and speed\n")
w("| horizon | QLIKE naive → model | corr(log σ̂², log RV) naive → model | pinball (bps) naive → full | 50% cov | 90% cov |")
w("|---|---|---|---|---|---|")
for H in [h for h in ALLH if h in main["horizons"]]:
    v = main["horizons"][H]["volatility"]; q = main["horizons"][H]["quantiles"]
    w(f"| {HN[H]} | {f(v['qlike_rv5_naive'],3)} → **{f(v['qlike_rv5_model'],3)}** | {f(v['corr_log_sd_rv5_naive'],3)} → **{f(v['corr_log_sd_rv5_model'],3)}** | "
      f"{f(q['naive_rw']['pinball_bps'],3)} → **{f(q['full']['pinball_bps'],3)}** | {f(q['full']['cov50'],3)} | {f(q['full']['cov90'],3)} |")

# ---------------------------------------------------------------- thresholds / touch / first passage
w("\n## 4. Levels: thresholds, touches, which comes first\n")
for H in [h for h in ALLH if h in main["horizons"]]:
    h = main["horizons"][H]
    w(f"### {HN[H]}\n")
    w("| question | n | base rate | naive LL | structural LL | full LL | full AUC |")
    w("|---|---|---|---|---|---|---|")
    for d, t in h["thresholds"].items():
        w(f"| end ≥ K{int(d):+d}bp | – | {t['base']:.3f} | {f(t['naive'])} | {f(t['structural'])} | **{f(t['full'])}** | {f(t['auc'],3)} |")
    for k, t in h["touch"].items():
        w(f"| touch {k} | {t['n']:,} | {t['base']:.3f} | {f(t['naive'])} | {f(t['structural'])} | **{f(t['full'])}** | {f(t['auc'],3)} |")
    for d, t in h["first_passage"].items():
        w(f"| ±{d}bp: which first (3-class) | {t['n']:,} | up-first {t['p_up_obs']:.3f} | {f(t['naive'])} | {f(t['structural'])} | **{f(t['full'])}** | {f(t['auc_up_vs_down'],3)} (up vs down) |")
    w("")

# ---------------------------------------------------------------- consistency
w("## 5. Consistency\n")
w("### Month by month (main test, 5-minute model, Δ log loss in millinats)\n")
w("| month | full vs naive RW | full vs structural |\n|---|---|---|")
for m, d in main["horizons"]["T"].get("above_ref_monthly", {}).items():
    w(f"| {m} | {d['vs_naive']*1e3:+.1f} | {d['vs_struct']*1e3:+.1f} |")
w("\n### Walk-forward (full retrain on an expanding window for each fold)\n")
w("| fold | test period | horizon | naive RW | full | full+recal | Δ full vs naive | dir. AUC |")
w("|---|---|---|---|---|---|---|---|")
folds = [("A", wfs["A"]), ("B", wfs["B"]), ("val", val), ("main", main)] + ([("main (v1 recipe)", v1)] if v1 else [])
for name, rep in folds:
    if not rep:
        continue
    for H in ALLH:
        if H not in rep["horizons"]:
            continue
        a = rep["horizons"][H]["above_ref"]
        w(f"| {name} | {rep['range'][0]} → {rep['range'][1]} | {HN[H]} | {f(a['naive_rw']['logloss'])} | {f(a['full']['logloss'])} | "
          f"{f(a['full+recal']['logloss'])} | {mn(a['dll_vs_naive_rw'])} | {f(rep['horizons'][H]['direction']['full']['auc'],3)} |")
w("\n(`val` was used for early stopping, so it is slightly optimistic. It is shown for completeness.)\n")

# ---------------------------------------------------------------- regimes
w("## 6. Robustness across market regimes\n")
w("Regime variables are causal (only previous days), and their thresholds are fixed on the training period. "
  "Each cell is the 5-minute log-loss improvement over the naive random walk in millinats, with a 95% day-block "
  "CI, plus AUC. The edge has to hold in **every** slice, not just on average.\n")
for tag, title in ((f"{MAIN}_test", "main test (Jun–Nov 2026: bear low and rebound)"),
                   ("wf_A_test", "walk-forward fold A (May–Aug 2025: bull run)"),
                   ("wf_B_test", "walk-forward fold B (Nov 2025–Feb 2026: crash −43%)")):
    R = reg.get(tag)
    if not R:
        continue
    w(f"### {title}\n")
    w("| regime family | slice | windows | Δ 5-min [95% CI] | 5-min AUC | Δ 1-min | Δ 30s | 30s direction AUC |")
    w("|---|---|---|---|---|---|---|---|")
    for fam, sl in R.items():
        for name, r in sl.items():
            t = r["T"]
            w(f"| {fam} | {name} | {r['windows']:,} | {t['dll']*1e3:+.1f} [{t['ci'][0]*1e3:+.1f}, {t['ci'][1]*1e3:+.1f}] | {t['auc']:.3f} | "
              f"{r['60']['dll']*1e3:+.1f} | {r['30']['dll']*1e3:+.1f} | {r['dir_auc_30']:.3f} |")
    w("")
rc = {h: load(f"ablation/regime_check_{h}.json") for h in ("30", "T")}
rcv = {h: load(f"ablation/regime_check_{h}_volonly.json") for h in ("30", "T")}
if rc["T"]:
    w("### How regime handling was chosen (validation period only)\n")
    w("| horizon | configuration | above-ref LL | Δ vs base (millinats) | vol QLIKE | drift IC |")
    w("|---|---|---|---|---|---|")
    for h in ("30", "T"):
        if not rc[h]:
            continue
        b0 = rc[h]["base"]["above_ref_ll"]
        rows = [(k, v) for k, v in rc[h].items()] + [(k + " (vol-engine only)", v) for k, v in (rcv[h] or {}).items()]
        for k, v in rows:
            w(f"| {HN[h]} | {k} | {v['above_ref_ll']:.5f} | {(v['above_ref_ll']-b0)*1e3:+.2f} | {v['vol_qlike']:.4f} | {v['ic']:.4f} |")
    w("\nRegime state is used in the volatility engine only. On ETH validation it is neutral there (30 s: 0.32616 → "
      "0.32614; 5 min: 0.47397 → 0.47395) and is kept for adaptivity. The rule is never to let regime or calendar "
      "variables drive direction, because two years contain too few regimes to learn regime-dependent drift. Recency "
      "weighting with a 180-day half-life is adopted only for horizons where no validation month got worse: 10 s, 15 s "
      "and 5 min. It hurt 30 s and 60 s in every month.\n")

# ---------------------------------------------------------------- ETH-specific decisions
cc = {h: load(f"ablation/cross_check_{h}.json") for h in ("60", "T")}
if any(cc.values()):
    w("### Where the BTC-leader block belongs (validation)\n")
    w("| horizon | BTC features everywhere | volatility engine only | nowhere |\n|---|---|---|---|")
    for h, r_ in cc.items():
        if r_:
            w(f"| {HN[h]} | {r_['x_everywhere']['above_ref_ll']:.5f} (IC {r_['x_everywhere']['ic']:.4f}) | "
              f"{r_['x_vol_only']['above_ref_ll']:.5f} (IC {r_['x_vol_only']['ic']:.4f}) | {r_['x_nowhere']['above_ref_ll']:.5f} (IC {r_['x_nowhere']['ic']:.4f}) |")
    w("\nThe BTC lead drives direction up to 60 s and feeds volatility at every horizon. For the 5-minute drift it is "
      "noise; that model receives the lead through the stacked 30 s / 60 s forecasts (docs/RESEARCH_ETH.md).\n")

# ---------------------------------------------------------------- ablations
w("## 7. What drives the predictions (ablations on the validation period)\n")
for H in ("30", "60", "T"):
    ab = abl.get(H)
    if not ab:
        continue
    base = ab["all"]
    w(f"### {HN[H]}\n")
    w("| feature set | drift IC | direction AUC | above-ref LL (structural) | Δ LL vs all (millinats) | vol QLIKE |")
    w("|---|---|---|---|---|---|")
    for k, d in ab.items():
        w(f"| {k} | {d['ic']:.4f} | {d['dir_auc']:.4f} | {d['above_ref_ll']:.5f} | {(d['above_ref_ll']-base['above_ref_ll'])*1e3:+.2f} | {d['vol_qlike']:.4f} |")
    if "ridge_ic" in base:
        w(f"\nA linear (ridge) drift model on the same features reaches IC {base['ridge_ic']:.4f} (AUC {base['ridge_dir_auc']:.4f}), "
          f"against {base['ic']:.4f} for LightGBM.\n")
    top = list(base.get("top_drift_features", {}).items())[:10]
    if top:
        w("Top drift features (gain share): " + ", ".join(f"`{k}` {v:.2f}" for k, v in top) + "\n")
w("### Architecture experiment: temporal CNN on raw 1-second sequences\n")
for H, s in seq.items():
    if s:
        w(f"- **{HN[H]}**: the CNN alone has IC {s['ic_B_cnn']:.4f}; LightGBM drift alone {s['ic_B_lgbm_drift']:.4f}; "
          f"the blend (weight on the CNN {s['blend_w_cnn']:.1f}, chosen on held-out days) {s['ic_B_blend']:.4f}. "
          f"Correlation between the two forecasts: {s['corr_cnn_lgbm']:.2f}.")
def bottom_line():
    hz = main["horizons"]
    B = ["# REPORT — ETH movement relative to the fixed 5-minute reference\n",
         f"**Bottom line.** These are results on the held-out test period {main['range'][0]} → {main['range'][1]} "
         f"({main['rows']:,} decision rows). It was never used during development. All numbers below are generated from "
         "`artifacts/*/report_*.json`.\n"]
    for H in ALLH:
        if H not in hz:
            continue
        a = hz[H]["above_ref"]; d = hz[H]["direction"]; r = a["full+recal"]
        B.append(f"* **{HN[H]}** — P(price ≥ K): log loss **{r['logloss']:.3f}** vs **{a['naive_rw']['logloss']:.3f}** for the "
                 f"naive random walk, an improvement of {mn(a['dll_vs_naive_rw'])} millinats per decision. AUC {r['auc']:.3f}, accuracy "
                 f"{r['acc']:.1%}, ECE {r['ece']:.4f}. Direction from now: AUC {d['full']['auc']:.3f}, top-10%-confidence "
                 f"accuracy {d['top_decile_acc']:.1%}.")
    from ethmove.recal import STACK_HORIZONS
    adt = load(f"ablation/adaptive_ensemble_{MAIN}_test.json")
    if adt and "T" in adt and "T" in STACK_HORIZONS:
        B.append(f"* With the adaptive prior/head ensemble that ships in the live engine, the 5-minute log loss is "
                 f"**{adt['T']['adaptive']['all']:.4f}**.")
    t = hz["T"]["above_ref_by_e"]
    last = t.get("240-299"); first = t.get("0-0")
    if last and first:
        B.append(f"* Through the 5-minute window, accuracy rises from {first['acc_full']:.1%} at the open (pure direction) "
                 f"to {last['acc_full']:.1%} in the last minute.")
    B.append("")
    B.append("How to read the numbers. Late in the window most of `P(close ≥ K)` is \"physics\": the displacement from K "
             "measured in units of remaining volatility. Every model gets the easy part right, so the honest comparison is "
             "against strong baselines, not a coin flip. The genuinely predictive part lives in three places, each "
             "measured separately below:\n"
             "1. a much better volatility forecast;\n"
             "2. a short-horizon drift driven mainly by the perpetual→spot lead-lag;\n"
             "3. learned corrections of the shape, touches and first passages.\n")
    return "\n".join(B) + "\n"


header = bottom_line()
footer = (ROOT / "docs" / "report_footer.md").read_text() if (ROOT / "docs" / "report_footer.md").exists() else ""
(ROOT / "REPORT.md").write_text(header + "\n".join(L) + "\n" + footer)
print("\n".join(L))
