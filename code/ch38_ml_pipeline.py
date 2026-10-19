"""Chapter 38 teaching computations: the financial ML pipeline contract on a constructed daily panel.

All data are CONSTRUCTED teaching data (``quant_course.ml_pipeline.simulate_return_panel`` or hand-typed prices);
nothing here is market evidence. Frequency: trading days. signal_time = close of D[k]; trade_time = label_start =
close of D[k+lag]; label_end = label_available_at = close of D[k+lag+h]. NaN policy: see ml_pipeline.

Run:  .venv/bin/python code/ch38_ml_pipeline.py --out build/batches/A8-A/r1/runs/<run-id>/cli
Writes ch38_results.json to --out (refuses to overwrite) and figures + a JSON copy to course/zh/chapters/ch38/figures.

Sections 3 deliberately run *wrong* procedures (shuffled K-fold, full-sample feature selection) to measure
how much they flatter a model; those code paths are labelled WRONG and never used for model selection.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from quant_course import ml_pipeline as mp
from quant_course.validation import purged_kfold_splits

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "runs" / "figures"

HAND_CLOSE = {
    "A": [100.0, 101.0, 103.0, 102.0, 104.0, 106.0, 105.0, 107.0, 110.0, 108.0, 111.0, 112.0],
    "B": [50.0, 50.5, 50.0, 49.5, 49.0, 49.5, 50.0, 51.0, 51.5, 52.0, 51.0, 52.5],
    "C": [20.0, 20.0, 20.2, 20.4, 20.2, 20.0, 20.4, 20.6, 20.6, 20.8, 21.0, 20.8],
}


def hand_example() -> dict[str, object]:
    """3 assets x 12 dates, lag=1, h=2; one fold with 6 training dates and 3 test dates."""
    dates = pd.bdate_range("2026-03-02", periods=12)
    close = pd.DataFrame(HAND_CLOSE, index=dates)
    labels = mp.make_forward_labels(close, horizon=2, execution_lag=1)
    fold = mp.date_walk_forward(labels.index.get_level_values(0), labels["label_start"], labels["label_end"],
                                labels["label_available_at"], min_train_dates=6, test_dates=3)[0]
    used_dates = sorted(set(labels.index.get_level_values(0)[fold.train_rows]))
    table = []
    for (d, a), row in labels.iterrows():
        k = dates.get_loc(d)
        table.append({"k": int(k + 1), "signal_time": str(d.date()), "asset": a,
                      "label_end_k": None if pd.isna(row["label_end"]) else int(dates.get_loc(row["label_end"]) + 1),
                      "y": None if pd.isna(row["y"]) else round(float(row["y"]), 6)})
    return {"dates": [str(d.date()) for d in dates], "close": HAND_CLOSE, "lag": 1, "h": 2, "labels": table,
            "fit_time_k": int(dates.get_loc(fold.fit_time) + 1),
            "train_dates_k": [int(dates.get_loc(d) + 1) for d in fold.train_dates],
            "used_train_dates_k": [int(dates.get_loc(d) + 1) for d in used_dates],
            "test_dates_k": [int(dates.get_loc(d) + 1) for d in fold.test_dates],
            "n_train_rows": int(fold.train_rows.size), "n_excluded_unavailable": fold.n_excluded_unavailable}


def _panel(seed: int, n_noise: int, signal_loading: float, n_assets: int = 40, n_days: int = 1260):
    close, chars = mp.simulate_return_panel(n_assets=n_assets, n_days=n_days, n_signal=2, n_noise=n_noise,
                                            signal_loading=signal_loading, seed=seed)
    labels = mp.make_forward_labels(close, horizon=5, execution_lag=1)
    X = mp.stack_features({**mp.price_features(close), **chars}, labels.index)
    return close, labels, X


def _r2(y: np.ndarray, p: np.ndarray, base: float | np.ndarray = 0.0) -> float:
    return float(1 - ((y - p) ** 2).sum() / ((y - base) ** 2).sum())


def validation_schemes(seed: int) -> dict[str, object]:
    """Pure-noise features (true loading 0), persistent AR(1) characteristics, overlapping 5-day labels."""
    _, labels, X = _panel(seed, n_noise=20, signal_loading=0.0)
    cols = [c for c in X.columns if c.startswith(("q_", "noise_"))]
    ok = labels["y"].notna() & X[cols].notna().all(axis=1)
    lab, Xv = labels[ok], X.loc[ok, cols].to_numpy()
    y = lab["y"].to_numpy()
    dates = lab.index.get_level_values(0)
    learners = {"ridge": lambda: Pipeline([("s", StandardScaler()), ("m", Ridge(alpha=1.0))]),
                "knn": lambda: Pipeline([("s", StandardScaler()), ("m", KNeighborsRegressor(n_neighbors=5))])}
    out: dict[str, dict[str, float]] = {}
    for name, make in learners.items():
        res = {}
        # WRONG: rows shuffled, same-date panel rows and overlapping labels on both sides.
        pred = np.empty_like(y)
        for tr, te in KFold(5, shuffle=True, random_state=0).split(Xv):
            pred[te] = make().fit(Xv[tr], y[tr]).predict(Xv[te])
        res["shuffled_kfold_r2_vs_zero"] = _r2(y, pred)
        # Purged K-fold over contiguous date blocks (Ch31), embargo 0: a diagnostic, still trains on the future.
        t = dates.map(lambda d: d.toordinal()).to_numpy(float)
        e = pd.DatetimeIndex(lab["label_end"]).map(lambda d: d.toordinal()).to_numpy(float)
        pred = np.empty_like(y)
        for tr, te in purged_kfold_splits(len(y), 5, t, e, groups_date=t):
            pred[te] = make().fit(Xv[tr], y[tr]).predict(Xv[te])
        res["purged_date_kfold_r2_vs_zero"] = _r2(y, pred)
        # Deployment-style: expanding date walk-forward with label-availability exclusion.
        folds = mp.date_walk_forward(dates, lab["label_start"], lab["label_end"], lab["label_available_at"],
                                     min_train_dates=504, test_dates=63)
        ps, ys = [], []
        for f in folds:
            ps.append(make().fit(Xv[f.train_rows], y[f.train_rows]).predict(Xv[f.test_rows]))
            ys.append(y[f.test_rows])
        res["walk_forward_r2_vs_zero"] = _r2(np.concatenate(ys), np.concatenate(ps))
        res["n_walk_forward_folds"] = len(folds)
        out[name] = res
    return {"seed": seed, "n_rows": int(len(y)), "features": cols, "true_loading": 0.0, "results": out}


def selection_leak(seed: int, n_noise: int = 200, k: int = 10) -> dict[str, object]:
    """Choose k of n_noise pure-noise features by |corr| with y: on the full sample (WRONG) vs inside training."""
    _, labels, X = _panel(seed, n_noise=n_noise, signal_loading=0.0, n_assets=30, n_days=756)
    cols = [c for c in X.columns if c.startswith("noise_")]
    ok = labels["y"].notna()
    lab, Xv = labels[ok], X.loc[ok, cols].to_numpy()
    y = lab["y"].to_numpy()
    dates = lab.index.get_level_values(0)
    folds = mp.date_walk_forward(dates, lab["label_start"], lab["label_end"], lab["label_available_at"],
                                 min_train_dates=378, test_dates=63)
    full_scores = np.abs(np.corrcoef(Xv.T, y)[-1, :-1])
    chosen_full = np.argsort(full_scores)[-k:]                     # WRONG: uses test-period labels
    res = {}
    for name in ("full_sample_selection", "train_only_selection"):
        ps, ys = [], []
        for f in folds:
            if name == "full_sample_selection":
                model = Pipeline([("s", StandardScaler()), ("m", Ridge(alpha=1.0))])
                model.fit(Xv[f.train_rows][:, chosen_full], y[f.train_rows])
                ps.append(model.predict(Xv[f.test_rows][:, chosen_full]))
            else:
                model = Pipeline([("s", StandardScaler()), ("k", SelectKBest(f_regression, k=k)),
                                  ("m", Ridge(alpha=1.0))])
                model.fit(Xv[f.train_rows], y[f.train_rows])
                ps.append(model.predict(Xv[f.test_rows]))
            ys.append(y[f.test_rows])
        yy, pp = np.concatenate(ys), np.concatenate(ps)
        res[name] = {"r2_vs_zero": _r2(yy, pp),
                     "mean_daily_spearman_ic": float(pd.DataFrame({"p": pp, "y": yy, "d": np.concatenate(
                         [dates[f.test_rows] for f in folds])}).groupby("d").apply(
                         lambda g: g["p"].corr(g["y"], method="spearman"), include_groups=False).mean())}
    return {"seed": seed, "n_noise": n_noise, "k": k, "n_folds": len(folds), "results": res}


def panel_case(seed: int) -> dict[str, object]:
    """Constructed panel with two true characteristics, 20 noise characteristics and three price features."""
    close, labels, X = _panel(seed, n_noise=20, signal_loading=0.0004)
    folds = mp.date_walk_forward(labels.index.get_level_values(0), labels["label_start"], labels["label_end"],
                                 labels["label_available_at"], min_train_dates=504, test_dates=63)
    grid = [{"alpha": a} for a in (1e2, 1e3, 1e4, 1e5, 1e6, 1e7)]
    pred, fr = mp.walk_forward_predict(X, labels, folds, model="ridge", param_grid=grid, inner_val_dates=63,
                                       inner_folds=2, inner_min_train_dates=252)
    base, _ = mp.walk_forward_predict(X, labels, folds, model="train_mean", inner_val_dates=63,
                                      inner_min_train_dates=252)
    metrics = mp.prediction_metrics(labels, pred, horizon=5, train_mean_pred=base)
    ok = pred.notna() & labels["y"].reindex(pred.index).notna()
    p, y = pred[ok].to_numpy(), labels["y"].reindex(pred.index)[ok].to_numpy()
    slope = float(np.cov(p, y, ddof=1)[0, 1] / np.var(p, ddof=1))
    d = pred[ok].index.get_level_values(0)
    p_dm = p - pd.Series(p).groupby(d).transform("mean").to_numpy()
    y_dm = y - pd.Series(y).groupby(d).transform("mean").to_numpy()
    xs_r2 = float(1 - ((y_dm - p_dm) ** 2).sum() / (y_dm ** 2).sum())
    xs_slope = float((p_dm @ y_dm) / (p_dm @ p_dm))
    within = pd.DataFrame({"d": d, "p": p, "y_dm": y_dm})
    within["b"] = within.groupby("d")["p"].transform(lambda v: pd.qcut(v.rank(method="first"), 10, labels=False))
    rel_xs = within.groupby("b")["y_dm"].mean()
    deciles = pd.qcut(p, 10, labels=False)
    rel = pd.DataFrame({"p": p, "y": y, "b": deciles}).groupby("b").mean()
    return {"seed": seed, "n_folds": len(folds), "first_fit_time": str(folds[0].fit_time.date()),
            "excluded_rows_per_fold": sorted({f.n_excluded_unavailable for f in folds}),
            "chosen_alpha_by_fold": [r.chosen_params["alpha"] for r in fr],
            "train_rows_dropped_missing_first_fold": fr[0].n_train_dropped_missing,
            "metrics": metrics, "calibration_slope_y_on_pred": slope,
            "cross_sectional_r2_demeaned": xs_r2, "cross_sectional_calibration_slope": xs_slope,
            "reliability": {"pred_mean": rel["p"].tolist(), "y_mean": rel["y"].tolist()},
            "within_date_decile_mean_demeaned_y": rel_xs.tolist(),
            "pred_sd": float(p.std(ddof=1)), "y_sd": float(y.std(ddof=1))}


def build_figures(hand: dict, schemes: dict, panel: dict) -> list[str]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    # 38-1 timeline of the hand example for asset rows of each signal date.
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    fit = hand["fit_time_k"]
    for k in range(1, 13):
        start, end = k + 1, k + 3
        if k in hand["test_dates_k"]:
            color, label = "#C0504D", "test row"
        elif k in hand["used_train_dates_k"]:
            color, label = "#247F82", "training row (label known by fit close)"
        elif k in hand["train_dates_k"]:
            color, label = "#E0A458", "excluded: label ends after fit close"
        else:
            color, label = "#BBBBBB", "not used in this fold"
        ax.plot([k], [k], "o", color=color, ms=6)
        if end <= 12:
            ax.plot([start, end], [k, k], color=color, lw=3, solid_capstyle="butt", label=label)
    ax.axvline(fit, color="#444444", ls="--", lw=1)
    ax.text(fit + 0.1, 0.6, f"fit_time = close of D{fit}", fontsize=8)
    handles, labels_ = ax.get_legend_handles_labels()
    uniq = dict(zip(labels_, handles))
    ax.legend(uniq.values(), uniq.keys(), frameon=False, fontsize=8, loc="upper left")
    ax.set_xlabel("Trading date index k (each date = a close)")
    ax.set_ylabel("Signal date of the row")
    ax.set_xticks(range(1, 13))
    ax.set_yticks(range(1, 13))
    ax.set_title("lag=1, h=2: dot = signal close, bar = label interval (trade close, label end]")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Hand example, 3 assets per date (all share the same times). CONSTRUCTED.",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = FIG_DIR / "fig38_1_label_timeline.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    paths.append(p)
    # 38-2 validation schemes on pure noise.
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    keys = [("shuffled_kfold_r2_vs_zero", "Shuffled K-fold\n(WRONG)"),
            ("purged_date_kfold_r2_vs_zero", "Purged date-block\nK-fold (diagnostic)"),
            ("walk_forward_r2_vs_zero", "Date walk-forward\n(deployment)")]
    x = np.arange(len(keys))
    for j, (learner, color) in enumerate((("ridge", "#247F82"), ("knn", "#C0504D"))):
        vals = [100 * schemes["results"][learner][k] for k, _ in keys]
        bars = ax.bar(x + (j - 0.5) * 0.36, vals, 0.34, color=color, label=f"{learner} (5 neighbours)" if learner == "knn" else "ridge (alpha=1)")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + (1 if v >= 0 else -4), f"{v:+.1f}", ha="center", fontsize=8)
    ax.axhline(0, color="#444444", lw=0.8)
    ax.set_xticks(x, [k for _, k in keys])
    ax.set_ylabel("Out-of-sample R2 vs zero forecast (%)")
    ax.set_title("Pure-noise features (true loading 0): what each validation scheme reports")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, f"CONSTRUCTED: 40 assets x 1260 days, 22 AR(1) characteristics (rho 0.98), 5-day labels, seed {schemes['seed']}.",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = FIG_DIR / "fig38_2_validation_schemes.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    paths.append(p)
    # 38-3 left: pooled-level reliability; right: within-date sorting check (what a dollar-neutral book trades).
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.6))
    rel = panel["reliability"]
    pm, ym = 100 * np.array(rel["pred_mean"]), 100 * np.array(rel["y_mean"])
    axes[0].plot(pm, ym, "o-", color="#247F82", label="Decile means (test folds pooled)")
    lim = [min(pm.min(), ym.min()) - 0.05, max(pm.max(), ym.max()) + 0.05]
    axes[0].plot(lim, lim, "--", color="#999999", label="45-degree line")
    axes[0].set_xlabel("Mean prediction in pooled decile (%, 5-day)")
    axes[0].set_ylabel("Mean realised 5-day return (%)")
    axes[0].set_title(f"Pooled levels: slope {panel['calibration_slope_y_on_pred']:.2f}", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8)
    dec = 100 * np.array(panel["within_date_decile_mean_demeaned_y"])
    axes[1].bar(np.arange(1, 11), dec, color=["#C0504D" if v < 0 else "#247F82" for v in dec])
    axes[1].axhline(0, color="#444444", lw=0.8)
    axes[1].set_xticks(range(1, 11))
    axes[1].set_xlabel("Prediction decile within each date (1 = lowest)")
    axes[1].set_ylabel("Mean date-demeaned 5-day return (%)")
    axes[1].set_title(f"Within-date sort; demeaned slope {panel['cross_sectional_calibration_slope']:.2f}", fontsize=10)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Ridge walk-forward on a constructed panel: levels vs cross-sectional ordering", fontsize=10)
    fig.text(0.01, 0.01, "CONSTRUCTED panel, 40 assets (4 per within-date decile), 2 true characteristics; slope = cov(y, pred) / var(pred).",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    p = FIG_DIR / "fig38_3_calibration.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    paths.append(p)
    return [str(x.relative_to(FIG_DIR.parent)) for x in paths]


def main() -> None:
    global FIG_DIR
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    FIG_DIR = a.out.resolve() / "figures"
    out = a.out / "ch38_results.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    a.out.mkdir(parents=True, exist_ok=True)
    hand = hand_example()
    schemes = validation_schemes(seed=3801)
    leak = selection_leak(seed=3802)
    panel = panel_case(seed=3803)
    results = {"chapter": 38, "data_class": "CONSTRUCTED", "hand_example": hand, "validation_schemes": schemes,
               "selection_leak": leak, "panel_case": panel}
    results["figures"] = build_figures(hand, schemes, panel)
    text = json.dumps(results, indent=1, default=float)
    out.write_text(text, encoding="utf-8")
    (FIG_DIR / "ch38_results.json").write_text(text, encoding="utf-8")
    print("hand: fit_time k", hand["fit_time_k"], "used train dates", hand["used_train_dates_k"],
          "excluded rows", hand["n_excluded_unavailable"])
    for learner, r in schemes["results"].items():
        print(learner, {k: round(v * 100, 2) if isinstance(v, float) else v for k, v in r.items()})
    for name, r in leak["results"].items():
        print(name, {k: round(v * 100, 3) for k, v in r.items()})
    m = panel["metrics"]
    print("panel:", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in m.items()},
          "slope", round(panel["calibration_slope_y_on_pred"], 3), "xs_r2", round(panel["cross_sectional_r2_demeaned"], 5),
          "xs_slope", round(panel["cross_sectional_calibration_slope"], 3), "alphas", panel["chosen_alpha_by_fold"])


if __name__ == "__main__":
    main()
