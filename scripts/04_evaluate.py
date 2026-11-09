"""Out-of-sample evaluation of every capability, per horizon, against explicit baselines.

usage: python scripts/04_evaluate.py [--split test] [--models artifacts/models] [--smoke]
Writes artifacts/<models>/report_<split>.json and .md
"""
import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
from scipy import special

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ethmove import data, metrics as M, structural as st  # noqa: E402
from ethmove.model import FP_DELTAS, hlen  # noqa: E402
from ethmove.engine import Engine  # noqa: E402
from ethmove.recal import trailing_recalibrate  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--split", default="test")
ap.add_argument("--models", default="artifacts/models")
ap.add_argument("--horizons", default="T,30,60")
ap.add_argument("--smoke", action="store_true")
ap.add_argument("--dates", default="", help="walk-forward: train_start,val_start,test_start,test_end (YYYY-MM-DD)")
ap.add_argument("--qsub", type=int, default=60000, help="rows used for quantile/CRPS evaluation")
ap.add_argument("--boot", type=int, default=500)
ap.add_argument("--no-recal", action="store_true")
a = ap.parse_args()

splits = data.SPLITS
if a.smoke:
    splits = {"train": ("2024-02-01", "2024-08-01"), "val": ("2024-08-01", "2024-09-01"), "test": ("2024-09-01", "2024-11-01")}
if a.dates:
    d0, d1, d2, d3 = a.dates.split(",")
    splits = {"train": (d0, d1), "val": (d1, d2), "test": (d2, d3)}
mdir = Path(a.models)
t0 = time.time()
df = data.load(a.split, splits=splits)
day = (df["ts"].to_numpy() // 86400)
month = np.array([f"{y}" for y in (df["ts"].to_numpy() // (86400 * 30.4375)).astype(int)])
ym = np.array([time.strftime("%Y-%m", time.gmtime(t)) for t in df["ts"].to_numpy()[:: 1]]) if len(df) < 3_000_000 else month
e = df["e"].to_numpy()
EB = [(0, 0), (1, 59), (60, 119), (120, 179), (180, 239), (240, 299)]
report = {"split": a.split, "range": splits[a.split], "rows": int(len(df)), "horizons": {}}
md = [f"# Out-of-sample report — split `{a.split}` {splits[a.split]}  ({len(df):,} decision rows, "
      f"{len(np.unique(df['ts'].to_numpy() // 300)):,} five-minute windows)\n"]
print(f"loaded {len(df):,} rows ({time.time()-t0:.0f}s)", flush=True)


def fmt(x, n=4):
    return "nan" if x is None or not np.isfinite(x) else f"{x:.{n}f}"


def naive_sd(df, H):
    """Naive vol: realised variance over the last 5 minutes (per second) scaled by sqrt(h)."""
    return np.sqrt(np.exp(df["lrv_300"].to_numpy(np.float64)) * hlen(df, H)) + 1e-12


eng = Engine.load(mdir)
n_main = len(df)
if not a.no_recal:
    # 15 days preceding the split, used ONLY as history for the causal trailing recalibration
    lo_ts = data.ts_of(splits[a.split][0])
    import datetime as _dt
    wlo = (_dt.datetime.fromtimestamp(lo_ts - 15 * 86400, _dt.UTC)).strftime("%Y-%m-%d")
    wdf = data.load("warm", splits={"warm": (wlo, splits[a.split][0])})
    wdf = wdf[wdf.ts < lo_ts - 3600]
    import pandas as _pd
    df = _pd.concat([wdf, df], ignore_index=True)
    n_warm = len(wdf)
else:
    n_warm = 0
df, S_all = eng.augment(df)
WARM = np.zeros(len(df), bool); WARM[:n_warm] = True
RECAL = {}
for H in a.horizons.split(","):
    if H in eng.models and n_warm:
        hm = eng.models[H]
        y_ = hm._d1_target(df)
        p_, _ = hm.predict_above(df, S_all[H])
        eb_ = np.digitize(df["e"].to_numpy(), [1, 60, 120, 180, 240])
        RECAL[H] = trailing_recalibrate(df["ts"].to_numpy(), p_, y_, groups=eb_, min_rows=5000)[~WARM]
df = df[~WARM].reset_index(drop=True)
S_all = {H: {k: v[~WARM] for k, v in s_.items()} for H, s_ in S_all.items()}
for H in a.horizons.split(","):
    if H not in eng.models:
        continue
    hm = eng.models[H]
    R = df[f"y_ret_{H}"].to_numpy(np.float64)
    S = df["S"].to_numpy(np.float64); K = df["K"].to_numpy(np.float64)
    qK = np.log(K / S)
    h = hlen(df, H)
    rep = {}
    s = S_all[H]
    sd_n = naive_sd(df, H)
    title = {"T": "5-minute (to the window close)", "10": "10-second", "15": "15-second", "30": "30-second", "60": "1-minute"}[H]
    md.append(f"\n## Horizon {H}: {title}\n")

    # ---------------- 1. above the fixed reference price ----------------
    y = hm._d1_target(df)
    p_full, p_struct = hm.predict_above(df, s)
    p_recal = RECAL.get(H, p_full)
    p_naive = special.ndtr(-(qK) / sd_n)
    p_volonly = special.ndtr(-(qK) / s["sd"])
    p_clim = np.full(len(y), y.mean())  # NB: uses test base rate (generous to the baseline)
    models_ = {"climatology": p_clim, "naive_rw": p_naive, "vol_only": p_volonly, "structural": p_struct, "full": p_full,
               "full+recal": p_recal}
    if H != "T":
        within = (e + h) <= 300
    else:
        within = np.ones(len(y), bool)
    rows = []
    for name, p in models_.items():
        r = M.binary_report(y[within], p[within])
        rows.append((name, r))
    rep["above_ref"] = {n: r for n, r in rows}
    md.append(f"### P(S(t+h) ≥ K) — above the fixed 5-minute reference" + (" (decision times whose horizon stays inside the window)" if H != "T" else "") + "\n")
    md.append("| model | log loss | Brier | AUC | ECE | accuracy |\n|---|---|---|---|---|---|")
    for n, r in rows:
        md.append(f"| {n} | {fmt(r['logloss'])} | {fmt(r['brier'])} | {fmt(r['auc'])} | {fmt(r['ece'])} | {fmt(r['acc'],3)} |")
    mean, lo, hi, pb = M.block_bootstrap_diff(M.ll_vec(y[within], p_full[within]), M.ll_vec(y[within], p_recal[within]), day[within], a.boot)
    rep["above_ref"]["dll_recal_vs_full"] = {"mean": mean, "ci95": [lo, hi], "p_boot_gt0": pb}
    md.append(f"\nlog-loss change from causal trailing recalibration (full -> full+recal): {mean*1e3:.3f} millinats, 95% CI [{lo*1e3:.3f}, {hi*1e3:.3f}]")
    for base in ("naive_rw", "structural"):
        mean, lo, hi, pb = M.block_bootstrap_diff(M.ll_vec(y[within], models_[base][within]), M.ll_vec(y[within], p_full[within]), day[within], a.boot)
        rep["above_ref"][f"dll_vs_{base}"] = {"mean": mean, "ci95": [lo, hi], "p_boot_gt0": pb}
        md.append(f"\nlog-loss improvement of `full` over `{base}`: {mean*1e3:.3f} millinats/decision, 95% day-block CI [{lo*1e3:.3f}, {hi*1e3:.3f}]")
    # by elapsed bucket
    md.append("\nBy elapsed time in the window (log loss; skill = 1 - LL/LL_climatology-at-0.5):\n")
    md.append("| elapsed s | n | base | naive_rw | structural | full | full AUC | full acc |\n|---|---|---|---|---|---|---|---|")
    rep["above_ref_by_e"] = {}
    for lo_, hi_ in EB:
        m = within & (e >= lo_) & (e <= hi_)
        if m.sum() < 100:
            continue
        r = {n: M.logloss(y[m], p[m]) for n, p in models_.items()}
        ra = M.auc(y[m], p_full[m]); acc = float(np.mean((p_full[m] >= .5) == y[m]))
        rep["above_ref_by_e"][f"{lo_}-{hi_}"] = r | {"auc_full": ra, "acc_full": acc, "n": int(m.sum())}
        md.append(f"| {lo_}-{hi_} | {m.sum():,} | {fmt(np.log(2))} | {fmt(r['naive_rw'])} | {fmt(r['structural'])} | {fmt(r['full'])} | {fmt(ra,3)} | {fmt(acc,3)} |")
    # monthly consistency
    md.append("\nMonthly consistency (log-loss improvement of full vs naive_rw, millinats):\n")
    months = np.array([time.strftime("%Y-%m", time.gmtime(t)) for t in df["ts"].to_numpy()[::50]])
    mon_full = np.repeat(months, 50)[: len(df)] if len(months) * 50 >= len(df) else None
    mlist = []
    if mon_full is not None:
        for mo in np.unique(mon_full):
            m = within & (mon_full == mo)
            d_ = M.logloss(y[m], p_naive[m]) - M.logloss(y[m], p_full[m])
            d2 = M.logloss(y[m], p_struct[m]) - M.logloss(y[m], p_full[m])
            mlist.append((mo, d_, d2))
        md.append("| month | vs naive_rw | vs structural |\n|---|---|---|")
        for mo, d_, d2 in mlist:
            md.append(f"| {mo} | {d_*1e3:.2f} | {d2*1e3:.2f} |")
        rep["above_ref_monthly"] = {mo: {"vs_naive": d_, "vs_struct": d2} for mo, d_, d2 in mlist}
    # calibration table
    md.append("\nReliability of `full` (all elapsed times):\n")
    md.append("| p bin | n | mean p | observed |\n|---|---|---|---|")
    for lo_, hi_, n_, mp, ob in M.reliability(y[within], p_full[within], 10):
        md.append(f"| {lo_:.1f}-{hi_:.1f} | {n_:,} | {mp:.3f} | {ob:.3f} |")

    # ---------------- 2. pure direction relative to the current price ----------------
    nz = R != 0
    yd = (R[nz] > 0).astype(float)
    pd_full, pd_struct = hm.predict_cdf(df[nz], np.full(nz.sum(), 1e-12), s={k: v[nz] for k, v in s.items()})
    ic = np.corrcoef(s["mu"][nz], R[nz])[0, 1]
    from scipy.stats import spearmanr
    ric = spearmanr(s["mu"][nz], R[nz]).statistic
    rd = {"structural": M.binary_report(yd, pd_struct), "full": M.binary_report(yd, pd_full), "ic_pearson": float(ic), "ic_spearman": float(ric)}
    rep["direction"] = rd
    md.append(f"\n### Direction from *now*: P(S(t+h) > S(t)) (excl. unchanged, n={nz.sum():,})\n")
    md.append("| model | log loss (coin=0.6931) | AUC | accuracy |\n|---|---|---|---|")
    for n in ("structural", "full"):
        md.append(f"| {n} | {fmt(rd[n]['logloss'])} | {fmt(rd[n]['auc'])} | {fmt(rd[n]['acc'],3)} |")
    md.append(f"\nInformation coefficient of the drift forecast: Pearson {ic:.4f}, Spearman {ric:.4f}")
    # accuracy on most confident decile
    conf = np.abs(pd_full - 0.5)
    top = conf >= np.quantile(conf, 0.9)
    md.append(f"Top-decile-confidence directional accuracy: {np.mean((pd_full[top] > .5) == yd[top]):.3f} (n={top.sum():,})")
    rep["direction"]["top_decile_acc"] = float(np.mean((pd_full[top] > .5) == yd[top]))

    # ---------------- 3. volatility (how fast it moves) ----------------
    r2 = R ** 2
    rv5 = df[f"y_rv5_{H}"].to_numpy(np.float64)
    vrep = {"qlike_R2_naive": M.qlike(r2 + 1e-14, sd_n ** 2), "qlike_R2_model": M.qlike(r2 + 1e-14, s["sd"] ** 2),
            "qlike_rv5_naive": M.qlike(rv5, sd_n ** 2), "qlike_rv5_model": M.qlike(rv5, s["sd"] ** 2),
            "corr_log_sd_abs_ret": float(np.corrcoef(np.log(s["sd"]), np.log(np.abs(R) + 1e-7))[0, 1]),
            "corr_log_sd_rv5_model": float(np.corrcoef(np.log(s["sd"] ** 2), np.log(rv5 + 1e-14))[0, 1]),
            "corr_log_sd_rv5_naive": float(np.corrcoef(np.log(sd_n ** 2), np.log(rv5 + 1e-14))[0, 1])}
    rep["volatility"] = vrep
    md.append("\n### Volatility / speed of movement\n")
    md.append("| metric | naive (5-min RV) | model |\n|---|---|---|")
    md.append(f"| QLIKE vs 5s-sampled realised var | {fmt(vrep['qlike_rv5_naive'])} | {fmt(vrep['qlike_rv5_model'])} |")
    md.append(f"| corr(log forecast var, log realised var) | {fmt(vrep['corr_log_sd_rv5_naive'])} | {fmt(vrep['corr_log_sd_rv5_model'])} |")

    # ---------------- 4. distribution / magnitude (quantiles) ----------------
    rng = np.random.default_rng(0)
    sub = np.sort(rng.choice(len(df), min(a.qsub, len(df)), replace=False))
    dsub = df.iloc[sub]
    ssub = {k: v[sub] for k, v in s.items()}
    probs = (0.05, 0.25, 0.5, 0.75, 0.95)
    Qf = hm.quantiles(dsub, probs, s=ssub)
    Qs = np.column_stack([st.quantile(pq, ssub["mu"], ssub["nu"]) * 0 + ssub["mu"] + ssub["sd"] * (st.t_scale(ssub["nu"]) * __import__("scipy").stats.t.ppf(pq, np.where(np.isfinite(ssub["nu"]), ssub["nu"], 1e9))) for pq in probs])
    Qn = np.column_stack([sd_n[sub] * special.ndtri(pq) for pq in probs])
    Rs = R[sub]
    qrep = {}
    md.append(f"\n### Magnitude: predictive quantiles of the log return (n={len(sub):,})\n")
    md.append("| model | mean pinball (bps) | 50% interval coverage | 90% interval coverage | 90% width (bps) |\n|---|---|---|---|---|")
    for name, Q in (("naive_rw", Qn), ("structural", Qs), ("full", Qf)):
        pb = np.mean([M.pinball(Rs, Q[:, k], pq) for k, pq in enumerate(probs)]) * 1e4
        c50 = np.mean((Rs >= Q[:, 1]) & (Rs <= Q[:, 3])); c90 = np.mean((Rs >= Q[:, 0]) & (Rs <= Q[:, 4]))
        w90 = np.median(Q[:, 4] - Q[:, 0]) * 1e4
        qrep[name] = {"pinball_bps": pb, "cov50": c50, "cov90": c90, "width90_bps": w90}
        md.append(f"| {name} | {pb:.4f} | {c50:.3f} | {c90:.3f} | {w90:.2f} |")
    rep["quantiles"] = qrep

    # ---------------- 5. threshold probabilities relative to K ----------------
    md.append("\n### Threshold probabilities at the horizon: P(S(t+h) ≥ K·(1+δ))\n")
    md.append("| δ (bps) | base rate | naive LL | structural LL | full LL | full AUC |\n|---|---|---|---|---|---|")
    trep = {}
    for dbp in (-20, -10, 10, 20):
        q = qK + dbp * 1e-4
        yt = (R >= q).astype(float)
        pf, ps = hm.predict_cdf(df, q, s=s)
        pn = special.ndtr(-q / sd_n)
        trep[dbp] = {"base": float(yt.mean()), "naive": M.logloss(yt, pn), "structural": M.logloss(yt, ps), "full": M.logloss(yt, pf), "auc": M.auc(yt, pf)}
        md.append(f"| {dbp:+d} | {yt.mean():.3f} | {fmt(trep[dbp]['naive'])} | {fmt(trep[dbp]['structural'])} | {fmt(trep[dbp]['full'])} | {fmt(trep[dbp]['auc'],3)} |")
    rep["thresholds"] = trep

    # ---------------- 6. touch probabilities of reference-anchored levels ----------------
    md.append("\n### Touch probabilities: P(price reaches K·(1±δ) before the horizon ends | not there now)\n")
    md.append("| level | n | base rate | naive LL | structural LL | full LL | full AUC |\n|---|---|---|---|---|---|---|")
    hi_ = df[f"y_hi_{H}"].to_numpy(np.float64); lo__ = df[f"y_lo_{H}"].to_numpy(np.float64)
    torep = {}
    for dbp in (5, 10, 20, 30):
        for side in (1, 0):
            lvl = (qK + dbp * 1e-4) if side == 1 else -(qK - dbp * 1e-4)  # distance from S (positive)
            m = lvl > 0
            if m.sum() < 1000:
                continue
            yt = ((hi_ >= lvl) if side == 1 else (lo__ <= -lvl))[m].astype(float)
            sm = {k: v[m] for k, v in s.items()}
            pf, ps = hm.predict_touch(df[m], lvl[m], np.full(m.sum(), side), s=sm)
            pn = st.prob_touch_up(lvl[m] / sd_n[m], 0.0)
            name = f"K{'+' if side else '-'}{dbp}bp"
            torep[name] = {"n": int(m.sum()), "base": float(yt.mean()), "naive": M.logloss(yt, pn), "structural": M.logloss(yt, ps), "full": M.logloss(yt, pf), "auc": M.auc(yt, pf)}
            r = torep[name]
            md.append(f"| {name} | {r['n']:,} | {r['base']:.3f} | {fmt(r['naive'])} | {fmt(r['structural'])} | {fmt(r['full'])} | {fmt(r['auc'],3)} |")
    rep["touch"] = torep

    # ---------------- 7. which comes first: +delta or -delta (from now) ----------------
    md.append("\n### First passage from the current price: P(+δ first), P(−δ first), P(neither) within the horizon\n")
    md.append("| δ (bps) | n | P(up first) obs | naive 3-class LL | structural LL | full LL | up-vs-down AUC (decided rows) |\n|---|---|---|---|---|---|---|")
    fprep = {}
    for dbp in FP_DELTAS:
        dd = np.full(len(df), dbp)
        yt, tie = hm._d4_target(df, dd)
        m = ~tie
        Pf, Ps = hm.predict_first(df[m], dbp, s={k: v[m] for k, v in s.items()})
        an = dbp * 1e-4 / sd_n[m]
        pu, pdn = st.prob_first_passage(an, an, np.zeros(m.sum()))
        Pn = np.column_stack([np.clip(1 - pu - pdn, 1e-6, 1), np.clip(pu, 1e-6, 1), np.clip(pdn, 1e-6, 1)])
        Pn /= Pn.sum(1, keepdims=True)
        ym_ = yt[m]
        dec = ym_ > 0
        au = M.auc((ym_[dec] == 1).astype(float), Pf[dec, 1] / (Pf[dec, 1] + Pf[dec, 2]))
        fprep[dbp] = {"n": int(m.sum()), "ties": int(tie.sum()), "p_up_obs": float(np.mean(ym_ == 1)), "naive": M.multi_logloss(ym_, Pn), "structural": M.multi_logloss(ym_, Ps), "full": M.multi_logloss(ym_, Pf), "auc_up_vs_down": au}
        r = fprep[dbp]
        md.append(f"| {dbp} | {r['n']:,} | {r['p_up_obs']:.3f} | {fmt(r['naive'])} | {fmt(r['structural'])} | {fmt(r['full'])} | {fmt(au,3)} |")
    rep["first_passage"] = fprep
    report["horizons"][H] = rep
    print(f"[{H}] done ({time.time()-t0:.0f}s)", flush=True)

out_json = mdir / f"report_{a.split}.json"
if out_json.exists():
    # merge with horizons evaluated in an earlier run (same split/protocol), newest wins
    old = json.load(open(out_json))
    if old.get("range") == list(report["range"]) or tuple(old.get("range", ())) == tuple(report["range"]):
        old["horizons"].update(report["horizons"])
        report = old
json.dump(report, open(out_json, "w"), indent=1, default=float)
suffix = "" if a.horizons == "T,30,60" else "_" + a.horizons.replace(",", "-")
(mdir / f"report_{a.split}{suffix}.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
