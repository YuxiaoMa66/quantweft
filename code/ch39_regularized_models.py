"""Chapter 39 teaching computations: OLS, Ridge, Lasso and Elastic Net under scikit-learn's scaling conventions.

All data are CONSTRUCTED teaching data; nothing here is market evidence.

scikit-learn 1.9.1 objectives (verified from the installed docstrings, see part07/chapter39/source_notes.md):
  Ridge       ||y - Xw||^2 + alpha ||w||_2^2
  Lasso       (1/(2n)) ||y - Xw||^2 + alpha ||w||_1
  ElasticNet  (1/(2n)) ||y - Xw||^2 + alpha*l1_ratio ||w||_1 + 0.5*alpha*(1-l1_ratio) ||w||_2^2
The intercept is never penalised. Panel case: signal_time = close D[k], trade_time = label_start = close D[k+1],
label = 5-day simple return; portfolio NAV marked daily at closes by the Chapter 29 ledger.

Run:  .venv/bin/python code/ch39_regularized_models.py --out build/batches/A8-A/r1/runs/<run-id>/cli
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
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge, lasso_path
from sklearn.preprocessing import StandardScaler

from quant_course import ml_pipeline as mp

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "runs" / "figures"

HAND_X = np.array([[1.0, 1.0], [1.0, -1.0], [-1.0, 1.0], [-1.0, -1.0]])
HAND_Y = np.array([3.0, 1.0, -1.0, -3.0])


def soft_threshold(z: np.ndarray, t: float) -> np.ndarray:
    """S(z, t) = sign(z) * max(|z| - t, 0)."""
    return np.sign(z) * np.maximum(np.abs(z) - t, 0.0)


def hand_example() -> dict[str, object]:
    """Orthogonal n=4 design with X'X = 4I, column means 0 and population SD 1 (so StandardScaler is identity)."""
    n = HAND_X.shape[0]
    z = HAND_X.T @ HAND_Y / n
    closed = {"ols": (HAND_X.T @ HAND_Y) / n,
              "ridge_alpha4": HAND_X.T @ HAND_Y / (n + 4.0),
              "lasso_alpha1.5": soft_threshold(z, 1.5),
              "enet_alpha1_l1ratio0.5": soft_threshold(z, 1.0 * 0.5) / (1 + 1.0 * 0.5)}
    fitted = {"ols": LinearRegression().fit(HAND_X, HAND_Y).coef_,
              "ridge_alpha4": Ridge(alpha=4.0).fit(HAND_X, HAND_Y).coef_,
              "lasso_alpha1.5": Lasso(alpha=1.5, tol=1e-12, max_iter=100_000).fit(HAND_X, HAND_Y).coef_,
              "enet_alpha1_l1ratio0.5": ElasticNet(alpha=1.0, l1_ratio=0.5, tol=1e-12, max_iter=100_000).fit(HAND_X, HAND_Y).coef_}
    scaled = StandardScaler().fit_transform(HAND_X)
    return {"X": HAND_X.tolist(), "y": HAND_Y.tolist(), "z_equals_Xty_over_n": z.tolist(),
            "closed_form": {k: v.tolist() for k, v in closed.items()},
            "sklearn": {k: v.tolist() for k, v in fitted.items()},
            "max_abs_diff": float(max(np.max(np.abs(closed[k] - fitted[k])) for k in closed)),
            "standard_scaler_is_identity": bool(np.allclose(scaled, HAND_X))}


def bias_variance(n: int, w: float, sigma: float, alphas: np.ndarray, n_sims: int, seed: int) -> dict[str, object]:
    """One standardised regressor (x'x = n, mean 0), Ridge with intercept-free centred data.

    w_hat = x'y / (n + alpha);  bias = -alpha w / (n + alpha);  var = sigma^2 n / (n + alpha)^2;
    MSE is minimised at alpha* = sigma^2 / w^2.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    x = (x - x.mean()) / x.std()            # population SD 1 -> x'x = n exactly
    theory, sim = [], []
    draws = rng.normal(0.0, sigma, (n_sims, n))
    for a in alphas:
        theory.append(float((a * w / (n + a)) ** 2 + sigma ** 2 * n / (n + a) ** 2))
        est = (x @ (w * x[:, None] + draws.T)) / (n + a)
        sim.append(float(np.mean((est - w) ** 2)))
    a_star = sigma ** 2 / w ** 2
    return {"n": n, "w": w, "sigma": sigma, "alphas": alphas.tolist(), "mse_theory": theory, "mse_sim": sim,
            "alpha_star": a_star, "mse_at_alpha_star": float((a_star * w / (n + a_star)) ** 2 + sigma ** 2 * n / (n + a_star) ** 2),
            "mse_ols": sigma ** 2 / n, "seed": seed, "n_sims": n_sims}


def collinearity(n: int, rho: float, n_rep: int, seed: int) -> dict[str, object]:
    """y = x1 + x2 + e, corr(x1, x2) = rho; coefficient spread over repeated samples."""
    rng = np.random.default_rng(seed)
    cov = np.array([[1.0, rho], [rho, 1.0]])
    coefs = {"ols": [], "ridge_alpha10": [], "lasso_alpha0.1": []}
    for _ in range(n_rep):
        X = rng.multivariate_normal([0.0, 0.0], cov, n)
        y = X @ np.array([1.0, 1.0]) + rng.normal(0.0, 1.0, n)
        Xs = StandardScaler().fit_transform(X)
        coefs["ols"].append(LinearRegression().fit(Xs, y).coef_)
        coefs["ridge_alpha10"].append(Ridge(alpha=10.0).fit(Xs, y).coef_)
        coefs["lasso_alpha0.1"].append(Lasso(alpha=0.1, max_iter=100_000).fit(Xs, y).coef_)
    out = {}
    for k, v in coefs.items():
        arr = np.array(v)
        out[k] = {"mean": arr.mean(0).tolist(), "sd": arr.std(0, ddof=1).tolist(),
                  "share_one_coef_zero": float(np.mean((np.abs(arr) < 1e-10).any(axis=1))),
                  "share_sign_flip": float(np.mean((arr < 0).any(axis=1)))}
    return {"n": n, "rho": rho, "n_rep": n_rep, "seed": seed, "vif": 1 / (1 - rho ** 2), "results": out}


def path_data(seed: int) -> dict[str, object]:
    """15 standardised features, 3 with true loadings (0.6, 0.4, -0.3), 12 noise; n = 120."""
    rng = np.random.default_rng(seed)
    n, p = 120, 15
    X = StandardScaler().fit_transform(rng.normal(size=(n, p)))
    w = np.zeros(p)
    w[:3] = [0.6, 0.4, -0.3]
    y = X @ w + rng.normal(0.0, 1.0, n)
    y = y - y.mean()
    alphas_l, coefs_l, _ = lasso_path(X, y, alphas=np.logspace(0, -3, 60))
    alphas_r = np.logspace(-1, 4, 60)
    coefs_r = np.array([Ridge(alpha=a, fit_intercept=False).fit(X, y).coef_ for a in alphas_r]).T
    first_entry = [float(alphas_l[np.argmax(np.abs(coefs_l[j]) > 0)]) if (np.abs(coefs_l[j]) > 0).any() else None
                   for j in range(p)]
    return {"n": n, "p": p, "true_w": w.tolist(), "lasso_alphas": alphas_l.tolist(), "lasso_coefs": coefs_l.tolist(),
            "ridge_alphas": alphas_r.tolist(), "ridge_coefs": coefs_r.tolist(), "lasso_entry_alpha": first_entry,
            "seed": seed}


GRIDS = {
    "zero": [{}], "train_mean": [{}], "ols": [{}],
    "ridge": [{"alpha": a} for a in (1e2, 1e3, 1e4, 1e5, 1e6, 1e7)],
    "lasso": [{"alpha": a} for a in (3e-3, 1e-3, 3e-4, 1e-4, 3e-5)],
    "elasticnet": [{"alpha": a, "l1_ratio": r} for a in (3e-3, 1e-3, 3e-4, 1e-4) for r in (0.2, 0.5, 0.8)],
}


def panel_case(seed: int) -> dict[str, object]:
    """3 true characteristics + 40 noise + 3 price features; date walk-forward; costs 0 and 10 bp one-way."""
    close, chars = mp.simulate_return_panel(n_assets=40, n_days=1260, n_signal=3, n_noise=40,
                                            signal_loading=0.0004, seed=seed)
    labels = mp.make_forward_labels(close, horizon=5, execution_lag=1)
    X = mp.stack_features({**mp.price_features(close), **chars}, labels.index)
    folds = mp.date_walk_forward(labels.index.get_level_values(0), labels["label_start"], labels["label_end"],
                                 labels["label_available_at"], min_train_dates=504, test_dates=63)
    preds, records = {}, {}
    for model, grid in GRIDS.items():
        pred, fr = mp.walk_forward_predict(X, labels, folds, model=model, param_grid=grid, inner_val_dates=63,
                                           inner_folds=2, inner_min_train_dates=252)
        preds[model] = pred
        records[model] = [{"fit_time": str(r.fit_time.date()), "chosen": r.chosen_params} for r in fr]
    out = {}
    for model, pred in preds.items():
        m = mp.prediction_metrics(labels, pred, horizon=5, train_mean_pred=preds["train_mean"])
        port = {}
        for fee in (0.0, 0.001):
            port[f"fee_{fee}"] = mp.backtest_predictions(close, pred, rebalance_every=5, fee_rate=fee)["metrics"]
        out[model] = {"prediction": m, "portfolio": port, "chosen_by_fold": [r["chosen"] for r in records[model]]}
    # sparsity of the lasso refit on each fold's training rows with the chosen alpha (for the figure)
    return {"seed": seed, "n_features": int(X.shape[1]), "n_true": 3, "n_noise": 40, "n_folds": len(folds),
            "first_fit_time": str(folds[0].fit_time.date()), "results": out}


def lasso_support(seed: int, panel: dict) -> list[int]:
    """Number of non-zero lasso coefficients after refitting each fold with its chosen alpha."""
    close, chars = mp.simulate_return_panel(n_assets=40, n_days=1260, n_signal=3, n_noise=40,
                                            signal_loading=0.0004, seed=seed)
    labels = mp.make_forward_labels(close, horizon=5, execution_lag=1)
    X = mp.stack_features({**mp.price_features(close), **chars}, labels.index)
    folds = mp.date_walk_forward(labels.index.get_level_values(0), labels["label_start"], labels["label_end"],
                                 labels["label_available_at"], min_train_dates=504, test_dates=63)
    counts = []
    for f, chosen in zip(folds, panel["results"]["lasso"]["chosen_by_fold"]):
        xt, yt = X.iloc[f.train_rows], labels["y"].iloc[f.train_rows]
        ok = xt.notna().all(axis=1) & yt.notna()
        model = Lasso(alpha=chosen["alpha"], max_iter=100_000).fit(StandardScaler().fit_transform(xt[ok]), yt[ok])
        counts.append(int((model.coef_ != 0).sum()))
    return counts


def build_figures(paths_: dict, bv: dict, panel: dict) -> list[str]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4))
    colors = ["#247F82", "#C0504D", "#E0A458"] + ["#BBBBBB"] * 12
    for j in range(paths_["p"]):
        axes[0].plot(paths_["ridge_alphas"], paths_["ridge_coefs"][j], color=colors[j], lw=2 if j < 3 else 0.8)
        axes[1].plot(paths_["lasso_alphas"], paths_["lasso_coefs"][j], color=colors[j], lw=2 if j < 3 else 0.8)
    axes[0].set_xscale("log")
    axes[1].set_xscale("log")
    axes[0].set_title("Ridge: ||y-Xw||^2 + alpha||w||^2", fontsize=10)
    axes[1].set_title("Lasso: (1/2n)||y-Xw||^2 + alpha||w||_1", fontsize=10)
    for ax in axes:
        ax.set_xlabel("alpha (log scale; sklearn convention of each estimator)")
        ax.set_ylabel("Coefficient (per 1 SD of feature)")
        ax.axhline(0, color="#444444", lw=0.6)
        ax.invert_xaxis()
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Regularisation paths: coloured = 3 true features (0.6, 0.4, -0.3), grey = 12 noise features", fontsize=10)
    fig.text(0.01, 0.01, f"CONSTRUCTED: n=120, standardised X, noise SD 1, seed {paths_['seed']}. alpha decreases to the right.",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    p = FIG_DIR / "fig39_1_paths.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    out.append(p)

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    a = np.array(bv["alphas"])
    ax.plot(a, bv["mse_theory"], color="#247F82", lw=2, label="Theory: bias^2 + variance")
    ax.plot(a, bv["mse_sim"], "o", color="#C0504D", ms=4, label=f"Simulation ({bv['n_sims']} samples)")
    ax.axvline(bv["alpha_star"], color="#444444", ls="--", lw=1)
    ax.axhline(bv["mse_ols"], color="#999999", ls=":", lw=1, label="OLS (alpha = 0)")
    ax.text(bv["alpha_star"] * 1.1, max(bv["mse_theory"]) * 0.9, f"alpha* = sigma^2/w^2 = {bv['alpha_star']:.0f}", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("Ridge alpha (sklearn convention, x'x = n)")
    ax.set_ylabel("MSE of the coefficient estimate")
    ax.set_title(f"Bias-variance of one Ridge coefficient: n={bv['n']}, w={bv['w']}, sigma={bv['sigma']}", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "CONSTRUCTED. MSE = (alpha w/(n+alpha))^2 + sigma^2 n/(n+alpha)^2.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = FIG_DIR / "fig39_2_bias_variance.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    out.append(p)

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.4))
    models = list(panel["results"])
    res = panel["results"]
    r2z = [100 * res[m]["prediction"]["oos_r2_vs_zero"] for m in models]
    ic = [res[m]["prediction"]["ic_mean"] for m in models]
    sh_g = [res[m]["portfolio"]["fee_0.0"]["sharpe"] for m in models]
    sh_n = [res[m]["portfolio"]["fee_0.001"]["sharpe"] for m in models]
    x = np.arange(len(models))
    axes[0].bar(x, r2z, color=["#C0504D" if v < 0 else "#247F82" for v in r2z])
    axes[0].set_ylabel("R2_OS vs zero forecast (%)")
    axes[1].bar(x, [0 if np.isnan(v) else v for v in ic], color="#247F82")
    axes[1].set_ylabel("Mean daily Spearman IC")
    axes[2].bar(x - 0.18, [0 if np.isnan(v) else v for v in sh_g], 0.36, color="#9BBFC0", label="before costs")
    axes[2].bar(x + 0.18, [0 if np.isnan(v) else v for v in sh_n], 0.36, color="#247F82", label="10 bp one-way")
    axes[2].set_ylabel("Annualised Sharpe of dollar-neutral book")
    axes[2].legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.set_xticks(x, models, rotation=35, fontsize=8)
        ax.axhline(0, color="#444444", lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"43 characteristics (3 true, 40 noise) + 3 price features, {panel['n_folds']} walk-forward folds; "
                 "zero/train_mean books are flat", fontsize=10)
    fig.text(0.01, 0.01, f"CONSTRUCTED panel, seed {panel['seed']}; rebalance every 5 signal dates, fills at next close; "
             "borrow/financing not modelled.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    p = FIG_DIR / "fig39_3_model_comparison.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    out.append(p)
    return [str(q.relative_to(FIG_DIR.parent)) for q in out]


def main() -> None:
    global FIG_DIR
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    FIG_DIR = a.out.resolve() / "figures"
    target = a.out / "ch39_results.json"
    if target.exists():
        raise SystemExit(f"refusing to overwrite {target}")
    a.out.mkdir(parents=True, exist_ok=True)
    hand = hand_example()
    bv = bias_variance(n=50, w=0.2, sigma=1.0, alphas=np.logspace(-1, 3, 25), n_sims=4000, seed=3901)
    col = collinearity(n=40, rho=0.99, n_rep=500, seed=3902)
    paths_ = path_data(seed=3903)
    panel = panel_case(seed=3904)
    panel["lasso_nonzero_by_fold"] = lasso_support(3904, panel)
    results = {"chapter": 39, "data_class": "CONSTRUCTED", "hand_example": hand, "bias_variance": bv,
               "collinearity": col, "paths": paths_, "panel_case": panel}
    results["figures"] = build_figures(paths_, bv, panel)
    text = json.dumps(results, indent=1, default=float)
    target.write_text(text, encoding="utf-8")
    (FIG_DIR / "ch39_results.json").write_text(text, encoding="utf-8")
    print("hand:", hand["closed_form"], "max diff vs sklearn", hand["max_abs_diff"])
    print("bias-variance: alpha*", bv["alpha_star"], "mse*", round(bv["mse_at_alpha_star"], 6), "ols", bv["mse_ols"])
    print("collinearity:", {k: (np.round(v["mean"], 3).tolist(), np.round(v["sd"], 3).tolist(), v["share_one_coef_zero"],
                                v["share_sign_flip"]) for k, v in col["results"].items()})
    print("lasso entry alphas (first 5):", [None if e is None else round(e, 4) for e in paths_["lasso_entry_alpha"][:5]])
    for m, r in panel["results"].items():
        pr, g, n = r["prediction"], r["portfolio"]["fee_0.0"], r["portfolio"]["fee_0.001"]
        print(f"{m:11s} R2z {100 * pr['oos_r2_vs_zero']:+.3f}% R2m {100 * pr.get('oos_r2_vs_train_mean', float('nan')):+.3f}% "
              f"IC {pr['ic_mean']:+.4f} t {pr['ic_t']:+.2f} | gross ret {100 * g['total_return']:+.2f}% SR {g['sharpe']:+.2f} | "
              f"net ret {100 * n['total_return']:+.2f}% SR {n['sharpe']:+.2f} turnover {n['turnover_ann']:.1f} mdd {100 * n['max_drawdown']:.2f}%")
    print("lasso nonzero by fold:", panel["lasso_nonzero_by_fold"])


if __name__ == "__main__":
    main()
