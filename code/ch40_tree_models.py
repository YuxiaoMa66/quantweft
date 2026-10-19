"""Chapter 40 (Tree-Based Models): hand examples, the constructed running case and the figures.

    .venv/bin/python code/ch40_tree_models.py --out <new dir> [--figures-dir course/zh/chapters/ch40/figures]

Every number is CONSTRUCTED teaching data. Registered before the first run (A8-B DECISION_LOG D08):
interaction panel = tree_models.simulate_interaction_panel(n_assets=40, n_days=1260, n_noise=20, signal_loading=4e-4,
seed=4001); linear panel = ml_pipeline.simulate_return_panel(same sizes, n_signal=3, seed=4001); features = rev_5,
mom_60_5, vol_20 + all characteristics; h=5, lag=1; outer walk-forward 504/63; inner 252/63, 2 folds; model grids =
Project 6 v2 grids; model seed 4001; dollar-neutral, rebalance every 5 signal dates, fees 0/10/20 bp one way.
Clock: features at the close of signal_time D[k]; fills at the close of D[k+1]; label return D[k+1] -> D[k+6] close.
Missing values: rows with a missing feature/label are dropped from training; test rows with a missing feature are flat.
Post-hoc (D11, added after the registered runs were seen): the same two panels with signal_loading 2e-3 (5x), applied
equally to both panels, to show the mechanism when the signal is detectable; the 4e-4 runs remain the primary result.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor

from quant_course import ml_pipeline as mp
from quant_course import tree_models as tm

ROOT = Path(__file__).resolve().parents[1]
SEED = 4001
H, LAG = 5, 1
WF = {"min_train_dates": 504, "test_dates": 63}
INNER = {"inner_val_dates": 63, "inner_folds": 2, "inner_min_train_dates": 252}
FEES = (0.0, 0.001, 0.002)
LINEAR_GRIDS = {"zero": [{}], "train_mean": [{}], "ols": [{}],
                "ridge": [{"alpha": a} for a in (1e2, 1e3, 1e4, 1e5, 1e6, 1e7)]}
TREE_GRIDS = {
    "tree": [{"max_depth": d, "min_samples_leaf": 1000} for d in (2, 3, 4, 6)],
    "rf": [{"n_estimators": 200, "max_features": 0.33, "min_samples_leaf": leaf, "max_samples": 0.5} for leaf in (500, 2000)],
    "gbm": [{"max_iter": 300, "learning_rate": 0.05, "max_depth": 2, "min_samples_leaf": 500},
            {"max_iter": 300, "learning_rate": 0.05, "max_depth": 3, "min_samples_leaf": 500},
            {"max_iter": 300, "learning_rate": 0.02, "max_depth": 3, "min_samples_leaf": 500}],
}
PRICE = ["rev_5", "mom_60_5", "vol_20"]

# ---------------------------------------------------------------------------------------------------------------------
# Hand examples (Sections 3, 6, 8)
# ---------------------------------------------------------------------------------------------------------------------
X8 = np.arange(1, 9, dtype=float)
Y8 = np.array([-2, -1, -1, 0, 2, 1, 3, 2], dtype=float)  # next-week return, %


def sse(v: np.ndarray) -> float:
    return float(((v - v.mean()) ** 2).sum()) if v.size else 0.0


def split_table(x: np.ndarray, y: np.ndarray, min_leaf: int = 1) -> list[dict]:
    """Every threshold between sorted x values: left/right means, SSE, gain and the closed form n_L n_R/n (dy)^2."""
    order = np.argsort(x, kind="stable")
    x, y = x[order], y[order]
    rows = []
    for s in range(1, len(y)):
        left, right = y[:s], y[s:]
        gain = sse(y) - sse(left) - sse(right)
        closed = s * (len(y) - s) / len(y) * (left.mean() - right.mean()) ** 2
        rows.append({"threshold": float((x[s - 1] + x[s]) / 2), "n_left": s, "mean_left": float(left.mean()),
                     "mean_right": float(right.mean()), "sse_left": sse(left), "sse_right": sse(right),
                     "gain": gain, "gain_closed_form": float(closed), "allowed": bool(min(s, len(y) - s) >= min_leaf)})
    return rows


def boosting_by_hand(x: np.ndarray, y: np.ndarray, nu: float, rounds: int) -> list[dict]:
    """Stump boosting on squared loss: F0 = mean, each round fits the residual with the best single split."""
    F = np.full_like(y, y.mean())
    out = [{"round": 0, "F": F.round(6).tolist(), "train_mse": float(((y - F) ** 2).mean())}]
    for m in range(1, rounds + 1):
        r = y - F
        best = max(split_table(x, r), key=lambda row: (row["gain"], -row["n_left"]))
        h = np.where(x <= best["threshold"], best["mean_left"], best["mean_right"])
        F = F + nu * h
        out.append({"round": m, "threshold": best["threshold"], "leaf_left": best["mean_left"],
                    "leaf_right": best["mean_right"], "F": F.round(6).tolist(), "train_mse": float(((y - F) ** 2).mean())})
    return out


def sklearn_checks() -> dict:
    """The same hand examples through sklearn 1.9.1."""
    stump = DecisionTreeRegressor(max_depth=1).fit(X8[:, None], Y8)
    hgb = HistGradientBoostingRegressor(max_iter=2, learning_rate=0.5, max_leaf_nodes=2, min_samples_leaf=1,
                                        early_stopping=False, max_bins=255).fit(X8[:, None], Y8)
    return {"stump_threshold": float(stump.tree_.threshold[0]), "stump_leaves": stump.predict([[1], [8]]).tolist(),
            "hgb_round2_pred": hgb.predict(X8[:, None]).round(6).tolist(),
            "hgb_l2_leaf_check": HistGradientBoostingRegressor(max_iter=1, learning_rate=1.0, max_depth=1, min_samples_leaf=1,
                                                               l2_regularization=4.0, early_stopping=False)
            .fit(X8[:, None], Y8).predict([[1], [8]]).round(6).tolist()}


def forest_variance(rho: float, sigma2: float, B: int | float) -> float:
    return rho * sigma2 + (1 - rho) * sigma2 / B if B != math.inf else rho * sigma2


def shapley_two(f, x: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """Exact interventional Shapley values for p=2 with a single background point b."""
    v0, v1, v2, v12 = f(*b), f(x[0], b[1]), f(b[0], x[1]), f(*x)
    return 0.5 * (v1 - v0) + 0.5 * (v12 - v2), 0.5 * (v2 - v0) + 0.5 * (v12 - v1)


def permutation_toy() -> dict:
    """Twin features x2 = x1 inside one date; the model uses x1 only. Fixed permutation: shift by two rows."""
    x1 = np.array([-1.5, -0.5, 0.5, 1.5])
    y = np.array([-0.9, -0.4, 0.2, 1.1])  # %
    pred = lambda a, b: 0.6 * a  # noqa: E731 - fitted model uses x1 only (its coefficient on x2 is 0)
    base = float(((y - pred(x1, x1)) ** 2).mean())
    perm = np.roll(np.arange(4), 2)
    out = {"x1": x1.tolist(), "y": y.tolist(), "base_mse": base, "perm": perm.tolist(),
           "mse_perm_x1": float(((y - pred(x1[perm], x1)) ** 2).mean()),
           "mse_perm_x2": float(((y - pred(x1, x1[perm])) ** 2).mean()),
           "mse_perm_group": float(((y - pred(x1[perm], x1[perm])) ** 2).mean())}
    out.update({k.replace("mse_perm", "imp"): out[k] - base for k in ("mse_perm_x1", "mse_perm_x2", "mse_perm_group")})
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Running case
# ---------------------------------------------------------------------------------------------------------------------

PANELS = {"interaction": ("interaction", 4e-4), "linear": ("linear", 4e-4),
          # post-hoc sensitivity (D11): 5x signal on both panels, added after the registered 4e-4 runs were seen
          "interaction_strong": ("interaction", 2e-3), "linear_strong": ("linear", 2e-3)}


def build_panel(name: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    kind, loading = PANELS[name]
    if kind == "interaction":
        close, chars = tm.simulate_interaction_panel(n_assets=40, n_days=1260, n_noise=20, signal_loading=loading, seed=SEED)
    else:
        close, chars = mp.simulate_return_panel(n_assets=40, n_days=1260, n_signal=3, n_noise=20, signal_loading=loading, seed=SEED)
    labels = mp.make_forward_labels(close, horizon=H, execution_lag=LAG)
    X = mp.stack_features({**mp.price_features(close), **chars}, labels.index)
    return close, labels, X


def folds_for(labels: pd.DataFrame) -> list:
    return mp.date_walk_forward(labels.index.get_level_values(0), labels["label_start"], labels["label_end"],
                                labels["label_available_at"], **WF)


def run_models(close, labels, X, folds, *, importance: bool) -> dict:
    preds, records = {}, {}
    for model, grid in LINEAR_GRIDS.items():
        preds[model], fr = mp.walk_forward_predict(X, labels, folds, model=model, param_grid=grid, **INNER)
        records[model] = [{"fit_time": str(r.fit_time.date()), "chosen": r.chosen_params} for r in fr]
    tree_results = {}
    for model, grid in TREE_GRIDS.items():
        reps = 3 if importance and model in ("rf", "gbm") else 0
        preds[model], fr = tm.walk_forward_predict_tree(X, labels, folds, model=model, param_grid=grid, seed=SEED,
                                                        n_jobs=-1, importance_repeats=reps, **INNER)
        tree_results[model] = fr
        records[model] = [{"fit_time": str(r.fit_time.date()), "chosen": r.chosen_params} for r in fr]
    metrics = {}
    for model, pred in preds.items():
        pm = mp.prediction_metrics(labels, pred, horizon=H, train_mean_pred=preds["train_mean"])
        port = {}
        for fee in FEES:
            port[f"{fee:g}"] = mp.backtest_predictions(close, pred, rebalance_every=5, fee_rate=fee,
                                                       execution_lag=LAG)["metrics"]
        metrics[model] = {"prediction": pm, "portfolio": port}
    return {"preds": preds, "records": records, "metrics": metrics, "tree_results": tree_results}


def early_stopping_demo(labels: pd.DataFrame, X: pd.DataFrame, folds: list, gbm_folds: list) -> list[dict]:
    """Section 12.1: sklearn's built-in early stopping (random 10% holdout of panel rows) vs date-grouped rounds."""
    rows = []
    params = {"learning_rate": 0.05, "max_depth": 3, "min_samples_leaf": 500}
    for f, gfr in zip(folds, gbm_folds):
        xtr, ytr = X.iloc[f.train_rows], labels["y"].iloc[f.train_rows]
        ok = xtr.notna().all(axis=1) & ytr.notna()
        xte, yte = X.iloc[f.test_rows], labels["y"].iloc[f.test_rows]
        okt = xte.notna().all(axis=1) & yte.notna()
        auto = HistGradientBoostingRegressor(max_iter=1000, early_stopping=True, validation_fraction=0.1,
                                             n_iter_no_change=20, random_state=SEED, **params).fit(xtr[ok], ytr[ok])
        val_mse = -2.0 * float(np.max(auto.validation_score_))  # scoring='loss' stores -(half squared error)
        test_mse_auto = float(((yte[okt] - auto.predict(xte[okt])) ** 2).mean())
        dated = gfr.predictions.reindex(yte[okt].index)
        rows.append({"fit_time": str(f.fit_time.date()), "auto_rounds": int(auto.n_iter_),
                     "auto_best_holdout_mse": val_mse, "auto_test_mse": test_mse_auto,
                     "dated_rounds": int(gfr.chosen_params["max_iter"]), "dated_params": gfr.chosen_params,
                     "dated_test_mse": float(((yte[okt] - dated) ** 2).mean()),
                     "zero_test_mse": float((yte[okt] ** 2).mean())})
    return rows


def rounds_on_test_demo(labels, X, folds) -> dict:
    """Section 12.2: choosing the number of rounds on the outer test window (forbidden) vs inner validation."""
    params = {"learning_rate": 0.05, "max_depth": 3, "min_samples_leaf": 500, "early_stopping": False, "random_state": SEED}
    sse_best, sse_fixed, ssy = 0.0, 0.0, 0.0
    picked = []
    for f in folds:
        xtr, ytr = X.iloc[f.train_rows], labels["y"].iloc[f.train_rows]
        ok = xtr.notna().all(axis=1) & ytr.notna()
        xte, yte = X.iloc[f.test_rows], labels["y"].iloc[f.test_rows]
        okt = xte.notna().all(axis=1) & yte.notna()
        est = HistGradientBoostingRegressor(max_iter=300, **params).fit(xtr[ok], ytr[ok])
        curve = [float(((yte[okt] - p) ** 2).sum()) for p in est.staged_predict(xte[okt])]
        j = int(np.argmin(curve))
        picked.append(j + 1)
        sse_best += curve[j]
        sse_fixed += curve[-1]
        ssy += float((yte[okt] ** 2).sum())
    return {"rounds_picked_on_test": picked, "r2_vs_zero_test_picked": 1 - sse_best / ssy,
            "r2_vs_zero_all_300_rounds": 1 - sse_fixed / ssy}


def importance_summary(tree_results: list, X_cols: list[str]) -> dict:
    imp = pd.DataFrame({r.fit_time: r.inner_importance["d_mse_mean"] for r in tree_results if r.inner_importance is not None})
    ranks = imp.rank(ascending=False)
    consec = [float(ranks.iloc[:, j].corr(ranks.iloc[:, j + 1], method="spearman")) for j in range(ranks.shape[1] - 1)]
    top10 = (ranks <= 10).sum(axis=1).sort_values(ascending=False)
    return {"mean_d_mse": imp.mean(axis=1).sort_values(ascending=False).to_dict(),
            "consecutive_rank_corr": consec, "top10_frequency": top10.to_dict(), "n_folds": int(imp.shape[1])}


def mdi_vs_permutation(labels, X, folds) -> dict:
    """Final-fold rf: MDI on the outer training rows vs within-date permutation on the last inner validation window."""
    f = folds[-1]
    res = tm.fit_select_predict_tree(X, labels, f, model="rf", param_grid=TREE_GRIDS["rf"][:1], seed=SEED, n_jobs=-1,
                                     importance_repeats=5, **INNER)
    xtr, ytr = X.iloc[f.train_rows], labels["y"].iloc[f.train_rows]
    ok = xtr.notna().all(axis=1) & ytr.notna()
    est = tm.make_estimator("rf", res.chosen_params, seed=SEED, n_jobs=-1).fit(xtr[ok], ytr[ok])
    mdi = pd.Series(est.feature_importances_, index=X.columns)
    return {"mdi": mdi.sort_values(ascending=False).to_dict(),
            "perm_d_mse": res.inner_importance["d_mse_mean"].sort_values(ascending=False).to_dict(),
            "perm_d_mse_std": res.inner_importance["d_mse_std"].to_dict(), "fit_time": str(f.fit_time.date())}


# ---------------------------------------------------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------------------------------------------------

def make_figures(res: dict, figdir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figdir.mkdir(parents=True, exist_ok=True)
    note = "CONSTRUCTED teaching data, not market evidence."
    paths = []

    fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.6))
    tab = res["hand"]["split_table"]
    ax[0].bar([r["threshold"] for r in tab], [r["gain"] for r in tab], width=0.6, color="#247F82")
    ax[0].set_xlabel("Threshold s (split x <= s vs x > s)")
    ax[0].set_ylabel("SSE reduction (%^2)")
    ax[0].set_title("Split gain, 8 stocks", fontsize=10)
    for B_rho in (0.0, 0.1, 0.3, 0.6):
        Bs = np.arange(1, 201)
        ax[1].plot(Bs, [forest_variance(B_rho, 1.0, b) for b in Bs], label=f"rho = {B_rho}")
    ax[1].set_xscale("log")
    ax[1].set_xlabel("Number of trees B (log scale)")
    ax[1].set_ylabel("Variance of the average (sigma^2 = 1)")
    ax[1].set_title("rho*sigma^2 + (1-rho)*sigma^2/B", fontsize=10)
    ax[1].legend(frameon=False, fontsize=8)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, note + " Left: Section 3 example. Right: formula of Section 6.2.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig40_1_split_and_forest.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)

    curves = res["interaction_strong"]["gbm_curves_last_fold"]
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    for key, curve in curves["curves"].items():
        c = np.asarray(curve) * 1e4
        ax.plot(np.arange(1, len(c) + 1), c, lw=1.4, label=key.replace("'", ""))
    ax.axvline(curves["chosen_rounds"], color="#444444", ls=":", lw=1)
    ax.set_xlabel("Boosting rounds")
    ax.set_ylabel("Mean inner validation MSE (x 1e-4)")
    ax.set_title(f"Inner date-grouped validation curves, outer fold fitted {curves['fit_time']} (dotted: chosen rounds)",
                 fontsize=9.5)
    ax.legend(frameon=False, fontsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, note + " Interaction panel, 5x signal sensitivity (loading 2e-3), seed 4001.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig40_2_boosting_rounds.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)

    models = ["ols", "ridge", "tree", "rf", "gbm"]
    fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.8))
    cols = {"interaction": "#9CC9C6", "linear": "#EBC7A6", "interaction_strong": "#247F82", "linear_strong": "#CF8951"}
    for j, panel in enumerate(cols):
        m = res[panel]["metrics"]
        ic = [m[k]["prediction"]["ic_mean"] for k in models]
        sr = [m[k]["portfolio"]["0.001"]["sharpe"] for k in models]
        xs = np.arange(len(models))
        lab = panel.replace("_strong", " 5x")
        ax[0].bar(xs + (j - 1.5) * 0.2, ic, 0.2, label=lab, color=cols[panel])
        ax[1].bar(xs + (j - 1.5) * 0.2, sr, 0.2, label=lab, color=cols[panel])
    for a, lab in zip(ax, ("Mean daily Spearman IC (test)", "Sharpe after 10 bp one-way cost")):
        a.set_xticks(np.arange(len(models)), models)
        a.set_ylabel(lab)
        a.axhline(0, color="#444444", lw=0.6)
        a.spines[["top", "right"]].set_visible(False)
    ax[0].legend(frameon=False, fontsize=8)
    ax[0].set_title("Prediction (same folds and rows)", fontsize=10)
    ax[1].set_title("Dollar-neutral book, rebalance every 5 days", fontsize=10)
    fig.text(0.01, 0.01, note + " Zero/train_mean books are flat. Borrow, financing and impact not modelled.",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig40_3_model_comparison.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)

    mv = res["interaction_strong"]["mdi_vs_permutation"]
    top = list(mv["perm_d_mse"].keys())[:8] + [k for k in list(mv["mdi"].keys())[:8] if k not in list(mv["perm_d_mse"].keys())[:8]]
    fig, ax = plt.subplots(1, 2, figsize=(9.0, 4.0), sharey=True)
    ys = np.arange(len(top))
    ax[0].barh(ys, [mv["mdi"][k] for k in top], color="#7F7F7F")
    ax[0].set_xlabel("MDI share (training rows)")
    ax[1].barh(ys, [mv["perm_d_mse"][k] * 1e4 for k in top],
               xerr=[(mv["perm_d_mse_std"][k] or 0) * 1e4 for k in top], color="#247F82")
    ax[1].set_xlabel("Permutation MSE increase x 1e-4 (inner validation)")
    ax[0].set_yticks(ys, top)
    ax[0].invert_yaxis()
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    ax[0].set_title(f"Random forest, outer fold fitted {mv['fit_time']}", fontsize=10)
    fig.text(0.01, 0.01, note + " Interaction panel 5x signal; q_1..q_3 carry signal, noise_* do not (known only because constructed).",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig40_4_importance.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--figures-dir", type=Path, default=None, help="also write the figures here (chapter figures)")
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    t0 = time.time()
    res = {"data_class": "CONSTRUCTED", "seed": SEED, "hand": {
        "split_table": split_table(X8, Y8), "split_table_min_leaf_3": split_table(X8, Y8, min_leaf=3),
        "boosting_nu_0.5": boosting_by_hand(X8, Y8, 0.5, 4), "sklearn": sklearn_checks(),
        "forest_variance": {f"rho{rho}_B{B}": forest_variance(rho, 1.0, B)
                            for rho, B in itertools.product((0.3,), (1, 10, 100, math.inf))},
        "forest_variance_decorrelated": {"rho0.1_sigma2_1.2_Binf": forest_variance(0.1, 1.2, math.inf)},
        "shapley_product": shapley_two(lambda a, b: 2 * a * b, (1.0, 1.0), (0.0, 0.0)),
        "shapley_x1_only_twin": shapley_two(lambda a, b: 0.6 * a, (1.5, 1.5), (0.0, 0.0)),
        "permutation_toy": permutation_toy()}}
    for panel in PANELS:
        close, labels, X = build_panel(panel)
        folds = folds_for(labels)
        out = run_models(close, labels, X, folds, importance=panel.startswith("interaction"))
        res[panel] = {"n_folds": len(folds), "n_rows": int(len(labels)), "features": list(X.columns),
                      "metrics": out["metrics"], "records": out["records"]}
        last = out["tree_results"]["gbm"][-1]
        res[panel]["gbm_curves_last_fold"] = {"fit_time": str(last.fit_time.date()), "curves": last.inner_curves,
                                              "chosen_rounds": int(last.chosen_params["max_iter"])}
        if panel.startswith("interaction"):
            res[panel]["importance_rf"] = importance_summary(out["tree_results"]["rf"], list(X.columns))
            res[panel]["importance_gbm"] = importance_summary(out["tree_results"]["gbm"], list(X.columns))
            res[panel]["mdi_vs_permutation"] = mdi_vs_permutation(labels, X, folds)
        if panel == "interaction":
            res[panel]["early_stopping_demo"] = early_stopping_demo(labels, X, folds, out["tree_results"]["gbm"])
            res[panel]["rounds_on_test_demo"] = rounds_on_test_demo(labels, X, folds)
    a.out.mkdir(parents=True)
    figs = make_figures(res, a.out)
    if a.figures_dir is not None:
        a.figures_dir.mkdir(parents=True, exist_ok=True)
        for p in figs:
            (a.figures_dir / p.name).write_bytes(p.read_bytes())
    res["seconds"] = round(time.time() - t0, 1)
    (a.out / "results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    for panel in PANELS:
        print(f"[{panel}] folds {res[panel]['n_folds']}")
        for model, m in res[panel]["metrics"].items():
            p, n = m["prediction"], m["portfolio"]["0.001"]
            print(f"  {model:10s} R2z {100 * p['oos_r2_vs_zero']:+.3f}% R2tm {100 * p.get('oos_r2_vs_train_mean', float('nan')):+.3f}% "
                  f"IC {p['ic_mean']:+.4f} (t {p['ic_t']:+.2f}) | net10 SR {n['sharpe']:+.2f} TO {n['turnover_ann']:.1f}")
    print(f"done in {res['seconds']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
