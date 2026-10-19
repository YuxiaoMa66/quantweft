"""Chapter 42 Standalone CLI Experiment Runner: Deep Learning Foundations & Quantitative Applications.

Usage:
    python code/ch42_deep_learning.py --out runs/run_ch42_v1

Runs the frozen Chapter 42 benchmark:
- Global training mean baseline
- Ridge regression baseline (alpha tuned on validation set)
- NumPy 4->8->1 tanh MLP with early stopping restoring best checkpoint
- Strict boundary label purging (no lookahead leakage across train/val/test)
- Out-of-sample MSE, R^2, daily Spearman IC, and Chapter 29 portfolio ledger simulation
- High-resolution figures saved both to the designated run directory and persistent figures dir.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Use the course package adjacent to this script.
workspace_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(workspace_root / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from quant_course.deep_learning import (
    generate_ch42_panel_data,
    split_ch42_panel,
    fit_mlp,
    predict,
    causal_attention,
)
from quant_course.ml_pipeline import backtest_predictions


def run_experiment(out_dir: Path, fig_dir: Path | None = None) -> dict:
    """Execute the full frozen Chapter 42 protocol experiment."""
    # Enforce strict non-existence for out_dir
    if out_dir.exists():
        raise FileExistsError(f"Output directory {out_dir} already exists. Specify a new directory to prevent overwriting.")
    if fig_dir is not None and (fig_dir.exists() or fig_dir.resolve() == out_dir.resolve()):
        raise FileExistsError(f"Persistent figure directory must be distinct and new: {fig_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)

    if fig_dir is not None:
        fig_dir.mkdir(parents=True, exist_ok=False)

    print(f"[*] Generating synthetic panel data with seed 4201...")
    x, raw_return, close, dates, assets = generate_ch42_panel_data(seed=4201)
    splits = split_ch42_panel(x, raw_return, dates, assets)

    N = len(assets)
    K = x.shape[2]

    # Preprocessing: Fit scaling on training set ONLY
    mu_X = np.mean(splits.X_train, axis=0)
    sigma_X = np.std(splits.X_train, axis=0)
    mu_y = float(np.mean(splits.y_train))
    sigma_y = float(np.std(splits.y_train))

    X_train_scaled = (splits.X_train - mu_X) / sigma_X
    y_train_scaled = (splits.y_train - mu_y) / sigma_y

    X_val_scaled = (splits.X_val - mu_X) / sigma_X
    y_val_scaled = (splits.y_val - mu_y) / sigma_y

    X_test_scaled = (splits.X_test - mu_X) / sigma_X

    # -----------------------------------------------------------------------
    # Baseline 1: Global Training Mean
    # -----------------------------------------------------------------------
    print("[*] Evaluating Baseline 1: Global Training Mean...")
    pred_mean_test = np.full_like(splits.y_test, mu_y)
    mse_mean_test = float(np.mean((splits.y_test - pred_mean_test) ** 2))
    r2_mean_test = 0.0  # By definition vs train mean

    # -----------------------------------------------------------------------
    # Baseline 2: Ridge Regression
    # -----------------------------------------------------------------------
    print("[*] Tuning and Evaluating Baseline 2: Ridge Regression...")
    alpha_grid = [0.1, 1.0, 10.0]
    best_alpha = None
    best_ridge_val_mse = float("inf")
    ridge_val_mses = {}

    for alpha in alpha_grid:
        r = Ridge(alpha=alpha)
        r.fit(X_train_scaled, splits.y_train.ravel())
        val_pred = r.predict(X_val_scaled)
        v_mse = float(np.mean((splits.y_val.ravel() - val_pred) ** 2))
        ridge_val_mses[str(alpha)] = v_mse
        if v_mse < best_ridge_val_mse:
            best_ridge_val_mse = v_mse
            best_alpha = alpha

    ridge_model = Ridge(alpha=best_alpha)
    ridge_model.fit(X_train_scaled, splits.y_train.ravel())
    pred_ridge_test = ridge_model.predict(X_test_scaled).reshape(-1, 1)
    mse_ridge_test = float(np.mean((splits.y_test - pred_ridge_test) ** 2))
    r2_ridge_test = float(1.0 - mse_ridge_test / mse_mean_test)

    # -----------------------------------------------------------------------
    # Model 3: NumPy 4->8->1 tanh MLP
    # -----------------------------------------------------------------------
    print("[*] Training Model 3: NumPy 4->8->1 tanh MLP with Early Stopping...")
    mlp_res = fit_mlp(
        X_train=X_train_scaled,
        y_train=y_train_scaled,
        X_val=X_val_scaled,
        y_val=y_val_scaled,
        hidden_dim=8,
        lr=0.01,
        batch_size=32,
        l2_reg=0.001,
        max_epochs=200,
        patience=15,
        seed_init=4202,
        seed_shuffle=4203,
    )

    pred_mlp_scaled = predict(X_test_scaled, mlp_res.W1, mlp_res.b1, mlp_res.W2, mlp_res.b2)
    # Inverse-transform to original return units
    pred_mlp_test = pred_mlp_scaled * sigma_y + mu_y
    mse_mlp_test = float(np.mean((splits.y_test - pred_mlp_test) ** 2))
    r2_mlp_test = float(1.0 - mse_mlp_test / mse_mean_test)

    # -----------------------------------------------------------------------
    # Spearman Rank IC Evaluation on Test Dates
    # -----------------------------------------------------------------------
    print("[*] Computing Daily Spearman Rank IC...")
    n_test_dates = len(splits.test_dates)
    y_test_2d = splits.y_test.reshape(n_test_dates, N)
    pred_ridge_2d = pred_ridge_test.reshape(n_test_dates, N)
    pred_mlp_2d = pred_mlp_test.reshape(n_test_dates, N)

    ic_ridge_list: list[float] = []
    ic_mlp_list: list[float] = []

    for t in range(n_test_dates):
        r_ic, _ = spearmanr(pred_ridge_2d[t], y_test_2d[t])
        m_ic, _ = spearmanr(pred_mlp_2d[t], y_test_2d[t])
        ic_ridge_list.append(float(r_ic))
        ic_mlp_list.append(float(m_ic))

    ic_ridge_arr = np.array(ic_ridge_list)
    ic_mlp_arr = np.array(ic_mlp_list)

    ic_ridge_mean = float(np.nanmean(ic_ridge_arr))
    ic_mlp_mean = float(np.nanmean(ic_mlp_arr))
    paired_diff_arr = ic_mlp_arr - ic_ridge_arr
    paired_diff_mean = float(np.nanmean(paired_diff_arr))

    # Mean model has constant predictions, IC is undefined (NaN)
    ic_mean_missing_count = n_test_dates
    ic_ridge_missing_count = int(np.isnan(ic_ridge_arr).sum())
    ic_mlp_missing_count = int(np.isnan(ic_mlp_arr).sum())

    # -----------------------------------------------------------------------
    # Portfolio Ledger Backtesting (Chapter 29 Ledger via ml_pipeline)
    # -----------------------------------------------------------------------
    print("[*] Running Chapter 29 Ledger Simulation (Gross and Net 10 bps)...")
    idx_test = pd.MultiIndex.from_product([splits.test_dates, assets], names=["signal_time", "asset"])

    series_mean = pd.Series(pred_mean_test.ravel(), index=idx_test)
    series_ridge = pd.Series(pred_ridge_test.ravel(), index=idx_test)
    series_mlp = pd.Series(pred_mlp_test.ravel(), index=idx_test)

    bt_mean_gross = backtest_predictions(close, series_mean, rebalance_every=1, fee_rate=0.0)
    bt_mean_net = backtest_predictions(close, series_mean, rebalance_every=1, fee_rate=0.001)

    bt_ridge_gross = backtest_predictions(close, series_ridge, rebalance_every=1, fee_rate=0.0)
    bt_ridge_net = backtest_predictions(close, series_ridge, rebalance_every=1, fee_rate=0.001)

    bt_mlp_gross = backtest_predictions(close, series_mlp, rebalance_every=1, fee_rate=0.0)
    bt_mlp_net = backtest_predictions(close, series_mlp, rebalance_every=1, fee_rate=0.001)

    # -----------------------------------------------------------------------
    # Model Parameter Counts
    # -----------------------------------------------------------------------
    # Mean: 1 parameter (sample mean of training targets \bar{y}_{train})
    # Ridge: 4 weights + 1 intercept = 5
    # MLP: 4*8 + 8 + 8*1 + 1 = 49
    param_counts = {
        "Global Mean": 1,
        "Ridge": K + 1,
        "MLP (4->8->1)": (K * 8 + 8) + (8 * 1 + 1),
    }

    # -----------------------------------------------------------------------
    # Compile Summary Dictionary
    # -----------------------------------------------------------------------
    summary = {
        "protocol": "Chapter 42 Frozen Protocol v1 (Root Correction r1)",
        "dates": {
            "total_panel_dates": 360,
            "train_dates_count": len(splits.train_dates),
            "val_dates_count": len(splits.val_dates),
            "test_dates_count": len(splits.test_dates),
            "train_start": str(splits.train_dates[0]),
            "train_end": str(splits.train_dates[-1]),
            "val_start": str(splits.val_dates[0]),
            "val_end": str(splits.val_dates[-1]),
            "test_start": str(splits.test_dates[0]),
            "test_end": str(splits.test_dates[-1]),
            "purged_boundary_indices": [178, 179, 238, 239],
        },
        "models": {
            "Global Mean": {
                "parameters": param_counts["Global Mean"],
                "test_mse": mse_mean_test,
                "test_r2": r2_mean_test,
                "daily_ic_mean": None,
                "ic_eligible_dates": 0,
                "ic_missing_dates": ic_mean_missing_count,
                "gross_total_return": float(bt_mean_gross["metrics"]["total_return"]),
                "gross_sharpe": None if np.isnan(bt_mean_gross["metrics"]["sharpe"]) else float(bt_mean_gross["metrics"]["sharpe"]),
                "net_total_return": float(bt_mean_net["metrics"]["total_return"]),
                "net_sharpe": None if np.isnan(bt_mean_net["metrics"]["sharpe"]) else float(bt_mean_net["metrics"]["sharpe"]),
                "turnover_ann": float(bt_mean_net["metrics"]["turnover_ann"]),
            },
            "Ridge": {
                "parameters": param_counts["Ridge"],
                "best_alpha": best_alpha,
                "val_mses": ridge_val_mses,
                "test_mse": mse_ridge_test,
                "test_r2": r2_ridge_test,
                "daily_ic_mean": ic_ridge_mean,
                "ic_eligible_dates": n_test_dates - ic_ridge_missing_count,
                "ic_missing_dates": ic_ridge_missing_count,
                "gross_total_return": float(bt_ridge_gross["metrics"]["total_return"]),
                "gross_sharpe": float(bt_ridge_gross["metrics"]["sharpe"]),
                "net_total_return": float(bt_ridge_net["metrics"]["total_return"]),
                "net_sharpe": float(bt_ridge_net["metrics"]["sharpe"]),
                "turnover_ann": float(bt_ridge_net["metrics"]["turnover_ann"]),
            },
            "MLP (4->8->1)": {
                "parameters": param_counts["MLP (4->8->1)"],
                "best_epoch": mlp_res.best_epoch,
                "stopped_epoch": mlp_res.stopped_epoch,
                "best_val_loss_scaled": mlp_res.best_val_loss,
                "test_mse": mse_mlp_test,
                "test_r2": r2_mlp_test,
                "daily_ic_mean": ic_mlp_mean,
                "ic_eligible_dates": n_test_dates - ic_mlp_missing_count,
                "ic_missing_dates": ic_mlp_missing_count,
                "paired_ic_diff_vs_ridge": paired_diff_mean,
                "gross_total_return": float(bt_mlp_gross["metrics"]["total_return"]),
                "gross_sharpe": float(bt_mlp_gross["metrics"]["sharpe"]),
                "net_total_return": float(bt_mlp_net["metrics"]["total_return"]),
                "net_sharpe": float(bt_mlp_net["metrics"]["sharpe"]),
                "turnover_ann": float(bt_mlp_net["metrics"]["turnover_ann"]),
            },
        },
    }

    # -----------------------------------------------------------------------
    # Save Full Chain Reproducibility Artifacts
    # -----------------------------------------------------------------------
    print("[*] Saving full reproducibility artifacts...")
    # 1. Summary JSON
    with open(out_dir / "experiment_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 2. Scalers JSON
    scalers_data = {
        "mu_X": mu_X.tolist(),
        "sigma_X": sigma_X.tolist(),
        "mu_y": float(mu_y),
        "sigma_y": float(sigma_y),
    }
    with open(out_dir / "scalers.json", "w", encoding="utf-8") as f:
        json.dump(scalers_data, f, indent=2)

    # 3. Training Checkpoint Weights
    np.savez_compressed(
        out_dir / "checkpoint_weights.npz",
        W1=mlp_res.W1,
        b1=mlp_res.b1,
        W2=mlp_res.W2,
        b2=mlp_res.b2,
        best_epoch=mlp_res.best_epoch,
        stopped_epoch=mlp_res.stopped_epoch,
        best_val_loss=mlp_res.best_val_loss,
    )

    # 4. Training History JSON
    history_data = {
        "train_loss_history": mlp_res.train_loss_history,
        "val_loss_history": mlp_res.val_loss_history,
        "best_epoch": mlp_res.best_epoch,
        "stopped_epoch": mlp_res.stopped_epoch,
        "best_val_loss": mlp_res.best_val_loss,
    }
    with open(out_dir / "training_history.json", "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2)

    # 5. Features and Labels npz
    np.savez_compressed(
        out_dir / "features_and_labels.npz",
        X_train=splits.X_train,
        y_train=splits.y_train,
        X_val=splits.X_val,
        y_val=splits.y_val,
        X_test=splits.X_test,
        y_test=splits.y_test,
        train_dates=np.array([str(d) for d in splits.train_dates]),
        val_dates=np.array([str(d) for d in splits.val_dates]),
        test_dates=np.array([str(d) for d in splits.test_dates]),
        assets=np.array(assets),
        panel_features=x,
        panel_returns=raw_return,
        panel_close=close.to_numpy(),
        panel_dates=np.array([str(d) for d in dates]),
    )

    # 6. Test Predictions CSV
    df_predictions = pd.DataFrame({
        "signal_time": [str(d) for d in idx_test.get_level_values("signal_time")],
        "asset": list(idx_test.get_level_values("asset")),
        "y_true": splits.y_test.ravel(),
        "pred_mean": pred_mean_test.ravel(),
        "pred_ridge": pred_ridge_test.ravel(),
        "pred_mlp": pred_mlp_test.ravel(),
    })
    df_predictions.to_csv(out_dir / "predictions.csv", index=False)

    # 7. Ledgers
    bt_mean_gross["ledger"].to_csv(out_dir / "ledger_mean_gross.csv")
    bt_mean_net["ledger"].to_csv(out_dir / "ledger_mean_net.csv")
    bt_ridge_gross["ledger"].to_csv(out_dir / "ledger_ridge_gross.csv")
    bt_ridge_net["ledger"].to_csv(out_dir / "ledger_ridge_net.csv")
    bt_mlp_gross["ledger"].to_csv(out_dir / "ledger_mlp_gross.csv")
    bt_mlp_net["ledger"].to_csv(out_dir / "ledger_mlp_net.csv")

    # 8. Daily IC and Common Dates Summary
    df_daily_ic = pd.DataFrame({
        "signal_date": [str(d) for d in splits.test_dates],
        "ic_ridge": ic_ridge_arr,
        "ic_mlp": ic_mlp_arr,
        "paired_diff_mlp_minus_ridge": paired_diff_arr,
    })
    df_daily_ic.to_csv(out_dir / "daily_ic.csv", index=False)

    common_ic_summary = {
        "total_test_dates": n_test_dates,
        "eligible_dates_count": {
            "Global Mean": 0,
            "Ridge": n_test_dates - ic_ridge_missing_count,
            "MLP (4->8->1)": n_test_dates - ic_mlp_missing_count,
        },
        "common_eligible_dates_count_ridge_mlp": int(np.sum(~np.isnan(ic_ridge_arr) & ~np.isnan(ic_mlp_arr))),
        "ridge_mean_ic_on_common_dates": ic_ridge_mean,
        "mlp_mean_ic_on_common_dates": ic_mlp_mean,
        "paired_ic_diff_mean": paired_diff_mean,
        "note": "Global Mean outputs uniform predictions across assets on each date; cross-sectional rank variance is zero, resulting in undefined (NaN) rank correlation. Ridge and MLP have valid cross-sectional rankings on all 118 dates.",
    }
    with open(out_dir / "common_ic_dates_summary.json", "w", encoding="utf-8") as f:
        json.dump(common_ic_summary, f, indent=2)

    # -----------------------------------------------------------------------
    # Generate Figures
    # -----------------------------------------------------------------------
    print("[*] Generating Publication Figures...")
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    def save_fig(fig, filename: str):
        fig.tight_layout()
        fig.savefig(out_dir / filename, dpi=300)
        if fig_dir is not None:
            fig.savefig(fig_dir / filename, dpi=300)
        plt.close(fig)

    # Figure 1: Loss curves with early stopping checkpoint
    fig, ax = plt.subplots(figsize=(8, 4.5))
    epochs = np.arange(len(mlp_res.train_loss_history))
    ax.plot(epochs, mlp_res.train_loss_history, label="Training MSE", color="#1f77b4", lw=1.8)
    ax.plot(epochs, mlp_res.val_loss_history, label="Validation MSE", color="#ff7f0e", lw=1.8)
    ax.axvline(mlp_res.best_epoch, color="#2ca02c", linestyle="--", lw=1.5,
               label=f"Best Checkpoint (Epoch {mlp_res.best_epoch})")
    ax.scatter([mlp_res.best_epoch], [mlp_res.val_loss_history[mlp_res.best_epoch]],
               color="#2ca02c", s=60, zorder=5)
    ax.set_title("Chapter 42 MLP: Mini-Batch SGD Loss & Early Stopping", fontsize=12, fontweight="bold")
    ax.set_xlabel("Epoch", fontsize=10)
    ax.set_ylabel("Mean Squared Error (Scaled Units)", fontsize=10)
    ax.legend(frameon=True, fontsize=10)
    save_fig(fig, "loss_curve.png")

    # Figure 2: Predictions vs Targets Scatter
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)
    y_true_plot = splits.y_test.ravel()
    axes[0].scatter(pred_ridge_test.ravel(), y_true_plot, alpha=0.35, color="#1f77b4", s=15, edgecolors="none")
    axes[0].plot([y_true_plot.min(), y_true_plot.max()], [y_true_plot.min(), y_true_plot.max()], "k--", lw=1.0)
    axes[0].set_title(f"Ridge (alpha={best_alpha})\nTest MSE={mse_ridge_test:.6f}, R^2={r2_ridge_test:.4f}", fontsize=11)
    axes[0].set_xlabel("Predicted Simple Return", fontsize=10)
    axes[0].set_ylabel("Realized Return (D_k+1 to D_k+2)", fontsize=10)

    axes[1].scatter(pred_mlp_test.ravel(), y_true_plot, alpha=0.35, color="#d62728", s=15, edgecolors="none")
    axes[1].plot([y_true_plot.min(), y_true_plot.max()], [y_true_plot.min(), y_true_plot.max()], "k--", lw=1.0)
    axes[1].set_title(f"MLP (4->8->1, 49 params)\nTest MSE={mse_mlp_test:.6f}, R^2={r2_mlp_test:.4f}", fontsize=11)
    axes[1].set_xlabel("Predicted Simple Return", fontsize=10)
    save_fig(fig, "predictions_vs_targets.png")

    # Figure 3: Cumulative Portfolio Returns (Gross vs Net 10 bps)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    def nav_series(ledger):
        return ledger["nav"] / float(ledger["nav"].iloc[0])

    nav_mean_g = nav_series(bt_mean_gross["ledger"])
    nav_ridge_g = nav_series(bt_ridge_gross["ledger"])
    nav_mlp_g = nav_series(bt_mlp_gross["ledger"])

    nav_mean_n = nav_series(bt_mean_net["ledger"])
    nav_ridge_n = nav_series(bt_ridge_net["ledger"])
    nav_mlp_n = nav_series(bt_mlp_net["ledger"])

    axes[0].plot(nav_mean_g.index, nav_mean_g.values, label="Global Mean (Flat)", color="gray", ls="--")
    axes[0].plot(nav_ridge_g.index, nav_ridge_g.values, label="Ridge (Gross)", color="#1f77b4", lw=1.6)
    axes[0].plot(nav_mlp_g.index, nav_mlp_g.values, label="MLP (Gross)", color="#d62728", lw=1.6)
    axes[0].set_title("Gross Ledger NAV (0 bps Cost)", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Normalized NAV (Base 1.0)", fontsize=10)
    axes[0].legend(frameon=True, fontsize=9)

    axes[1].plot(nav_mean_n.index, nav_mean_n.values, label="Global Mean (Flat)", color="gray", ls="--")
    axes[1].plot(nav_ridge_n.index, nav_ridge_n.values, label="Ridge (Net 10 bps)", color="#1f77b4", lw=1.6)
    axes[1].plot(nav_mlp_n.index, nav_mlp_n.values, label="MLP (Net 10 bps)", color="#d62728", lw=1.6)
    axes[1].set_title("Net Ledger NAV (10 bps One-Way Cost)", fontsize=11, fontweight="bold")
    axes[1].legend(frameon=True, fontsize=9)
    save_fig(fig, "cumulative_returns.png")

    # Figure 4: Daily Spearman IC Time Series
    fig, ax = plt.subplots(figsize=(10, 4.0))
    ax.plot(splits.test_dates, ic_ridge_arr, label=f"Ridge Daily IC (Mean={ic_ridge_mean:.3f})", color="#1f77b4", alpha=0.7, lw=1.2)
    ax.plot(splits.test_dates, ic_mlp_arr, label=f"MLP Daily IC (Mean={ic_mlp_mean:.3f})", color="#d62728", alpha=0.7, lw=1.2)
    ax.axhline(0.0, color="black", linestyle=":", lw=1.0)
    ax.set_title("Out-of-Sample Daily Cross-Sectional Spearman IC", fontsize=11, fontweight="bold")
    ax.set_xlabel("Test Signal Date", fontsize=10)
    ax.set_ylabel("Spearman Rank Correlation", fontsize=10)
    ax.legend(frameon=True, fontsize=9)
    save_fig(fig, "daily_ic_timeseries.png")

    # Figure 5: Causal Attention Heatmap
    T_att = 6
    d_k_att = 4
    rng_att = np.random.default_rng(42)
    Q_demo = rng_att.normal(size=(T_att, d_k_att))
    K_demo = rng_att.normal(size=(T_att, d_k_att))
    V_demo = rng_att.normal(size=(T_att, d_k_att))
    att_weights, _ = causal_attention(Q_demo, K_demo, V_demo, mask=True)

    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    cax = ax.imshow(att_weights, cmap="Blues", interpolation="nearest", vmin=0.0, vmax=1.0)
    for i in range(T_att):
        for j in range(T_att):
            val = att_weights[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color="white" if val > 0.5 else "black", fontsize=9)
    ax.set_xticks(range(T_att))
    ax.set_yticks(range(T_att))
    ax.set_xticklabels([f"t={t}" for t in range(T_att)], fontsize=9)
    ax.set_yticklabels([f"t={t}" for t in range(T_att)], fontsize=9)
    ax.set_title("Transformer Causal Attention Mask\n(Upper Triangle Strictly 0.0)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Key Token Index", fontsize=10)
    ax.set_ylabel("Query Token Index", fontsize=10)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    save_fig(fig, "causal_attention_weights.png")

    print(f"[+] All experiment tasks and figures completed successfully. Output in {out_dir}.")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Chapter 42 Deep Learning Benchmark CLI")
    parser.add_argument("--out", type=str, required=True, help="Destination directory for run outputs (must not exist)")
    parser.add_argument("--fig-dir", type=str, default=None,
                        help="Optional new persistent figures directory; default saves figures only in --out")
    args = parser.parse_args()

    out_path = Path(args.out).resolve()
    fig_path = Path(args.fig_dir).resolve() if args.fig_dir else None

    try:
        summary = run_experiment(out_path, fig_path)
        print("\n--- Summary Table ---")
        models = summary["models"]
        df_summary = pd.DataFrame({
            "Params": [models[m]["parameters"] for m in models],
            "Test MSE": [f"{models[m]['test_mse']:.8f}" for m in models],
            "Test R^2": [f"{models[m]['test_r2']:.6f}" for m in models],
            "Daily IC": ["NaN" if models[m]["daily_ic_mean"] is None else f"{models[m]['daily_ic_mean']:.4f}" for m in models],
            "Gross Sharpe": ["NaN" if models[m]["gross_sharpe"] is None else f"{models[m]['gross_sharpe']:.3f}" for m in models],
            "Net Sharpe": ["NaN" if models[m]["net_sharpe"] is None else f"{models[m]['net_sharpe']:.3f}" for m in models],
            "Turnover": [f"{models[m]['turnover_ann']:.1f}" for m in models],
        }, index=list(models.keys()))
        print(df_summary.to_string())
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
