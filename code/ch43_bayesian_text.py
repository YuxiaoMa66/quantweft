#!/usr/bin/env python3
"""Chapter 43 CLI Runner: Bayesian Inference, Causal Analysis, and Text/PIT Pipeline.

Executes all 3 analytical pipelines, produces persistent figures, and writes summary JSON.
Refuses to overwrite existing output directories.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure workspace src is first in import path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = WORKSPACE_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist, norm as norm_dist

from quant_course.bayesian_text import (
    beta_binomial_posterior_predictive,
    compute_stratified_ate,
    demonstrate_collider_bias,
    downstream_execution_interface_spec,
    filter_pit_eligible_documents,
    generate_causal_dataset,
    generate_constructed_text_dataset,
    hand_embedding_matrix,
    llm_offline_audit_ledger,
    negation_sentiment_scorer,
    normal_hierarchical_partial_pooling,
    train_text_prediction_models,
)


def plot_bayesian_updating(bayes_res: dict, normal_res: dict, save_path: Path) -> None:
    """Generate 2-panel chart showing Beta-Binomial updating and Normal partial pooling shrinkage."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Panel 1: Beta-Binomial Updating
    p_grid = np.linspace(0.001, 0.999, 500)
    prior_dens = beta_dist.pdf(p_grid, bayes_res["alpha_prior"], bayes_res["beta_prior"])
    post_dens = beta_dist.pdf(p_grid, bayes_res["alpha_post"], bayes_res["beta_post"])

    # Likelihood proportional: p^8 * (1-p)^2 scaled to same peak for visual comparison
    lik_raw = (p_grid ** 8) * ((1.0 - p_grid) ** 2)
    lik_scaled = lik_raw / np.max(lik_raw) * np.max(post_dens)

    ax1 = axes[0]
    ax1.plot(p_grid, prior_dens, label="Prior Beta(2, 2)", color="#BE8A20", linestyle="--", linewidth=2)
    ax1.plot(p_grid, lik_scaled, label="Scaled Likelihood (8/10)", color="#27406B", linestyle=":", linewidth=2)
    ax1.plot(p_grid, post_dens, label=f"Posterior Beta({bayes_res['alpha_post']:.0f}, {bayes_res['beta_post']:.0f})", color="#9C2B2E", linewidth=2.5)
    ax1.axvline(bayes_res["posterior_mean"], color="#9C2B2E", linestyle="-.", alpha=0.7, label=f"Post Mean = {bayes_res['posterior_mean']:.3f}")
    ax1.set_title("Beta-Binomial Conjugate Updating", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Success Probability p", fontsize=11)
    ax1.set_ylabel("Density", fontsize=11)
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Hierarchical Normal Shrinkage
    ax2 = axes[1]
    g1 = normal_res["groups"][0]
    g2 = normal_res["groups"][1]
    mu = normal_res["prior_mean"]

    y_pos = [1.5, 0.5]
    group_labels = [f"Group 1 (n={g1['n']})", f"Group 2 (n={g2['n']})"]

    # Plot prior mean vertical line
    ax2.axvline(mu, color="#211C17", linestyle="--", linewidth=1.5, label=f"Prior Mean mu={mu}")

    # Plot sample mean vs posterior mean
    for idx, (g, y) in enumerate(zip([g1, g2], y_pos)):
        # Sample mean
        ax2.scatter(g["sample_mean"], y, color="#27406B", s=90, zorder=4, label="Sample Mean" if idx == 0 else "")
        # Posterior mean
        ax2.scatter(g["posterior_mean"], y, color="#9C2B2E", s=110, marker="D", zorder=4, label="Posterior Mean (Shrunk)" if idx == 0 else "")
        # Connecting arrow / line showing shrinkage direction
        ax2.annotate(
            "",
            xy=(g["posterior_mean"], y),
            xytext=(g["sample_mean"], y),
            arrowprops=dict(arrowstyle="->", color="#9C2B2E", lw=2),
        )
        ax2.text(g["sample_mean"], y + 0.18, f"y_bar={g['sample_mean']:.2f}", ha="center", fontsize=9, color="#27406B")
        ax2.text(g["posterior_mean"], y - 0.22, f"theta_hat={g['posterior_mean']:.3f}\n(w={g['shrinkage_weight']:.1f})", ha="center", fontsize=9, color="#9C2B2E")

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(group_labels, fontsize=11)
    ax2.set_ylim(-0.2, 2.2)
    ax2.set_xlim(-0.01, 0.045)
    ax2.set_title("Normal Partial Pooling Shrinkage (Known Hyperparameters)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Mean Return / Effect Size", fontsize=11)
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)


def plot_causal_simpson(causal_res: dict, save_path: Path) -> None:
    """Generate bar chart illustrating Simpson's paradox."""
    fig, ax = plt.subplots(figsize=(8, 5))

    categories = [
        "Stratum Z=High\n(Contrast = -0.10)",
        "Stratum Z=Low\n(Contrast = -0.10)",
        "Standardized ATE\n(Target P(Z)=0.5:0.5)",
        "Unadjusted Naive\n(Difference = +0.38)",
    ]
    values = [
        causal_res["stratum_stats"]["high"]["contrast"],
        causal_res["stratum_stats"]["low"]["contrast"],
        causal_res["standardized_ate"],
        causal_res["unadjusted_difference"],
    ]
    colors = ["#27406B", "#27406B", "#9C2B2E", "#BE8A20"]

    bars = ax.bar(categories, values, color=colors, width=0.55, edgecolor="#211C17", linewidth=1.2)
    ax.axhline(0, color="#211C17", linewidth=1)

    for bar, val in zip(bars, values):
        height = bar.get_height()
        y_pos = height + 0.02 if height >= 0 else height - 0.05
        ax.text(bar.get_x() + bar.get_width() / 2.0, y_pos, f"{val:+.2f}", ha="center", va="bottom" if height < 0 else "top", fontsize=11, fontweight="bold")

    ax.set_ylim(-0.25, 0.5)
    ax.set_ylabel("Treatment Contrast / ATE", fontsize=11)
    ax.set_title("Constructed Simpson Contrast: Standardized (-0.10) vs Unadjusted (+0.38)", fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)


def plot_pit_timeline(save_path: Path) -> None:
    """Generate visual schematic of Point-in-Time event/latency/signal/trade contract."""
    fig, ax = plt.subplots(figsize=(12, 3.8))

    events = [
        ("Public Release\n(16:05 NY)", 0.0, "#27406B"),
        ("Vendor Dissemination\n(16:25 NY, +20m)", 1.5, "#27406B"),
        ("DB Ingestion Complete\n(16:30 NY, +5m)", 2.5, "#27406B"),
        ("Signal Cutoff\n(Next 09:00 NY)", 5.5, "#BE8A20"),
        ("Trade Execution\n(Same 09:30 NY)", 6.5, "#9C2B2E"),
        ("Label Closes\n(Next 09:30 NY)", 9.5, "#9C2B2E"),
    ]

    ax.plot([0, 9.5], [1, 1], color="#211C17", lw=3, zorder=1)

    for event_index, (label, x, col) in enumerate(events):
        ax.scatter(x, 1, color=col, s=150, zorder=3, edgecolors="#211C17", lw=1.5)
        label_height = 1.35 if event_index % 2 == 0 else 1.85
        ax.text(x, label_height, label, ha="center", va="bottom", fontsize=10, fontweight="bold", color=col)

    # Shaded regions - clarify research internal DB availability
    ax.axvspan(0.0, 2.5, ymin=0.3, ymax=0.7, color="#27406B", alpha=0.15, label="Latency Gap (Unavailable in local research DB)")
    ax.axvspan(2.5, 5.5, ymin=0.3, ymax=0.7, color="#BE8A20", alpha=0.15, label="Eligible Staging Window (In DB & Pre-Signal)")
    ax.axvspan(6.5, 9.5, ymin=0.3, ymax=0.7, color="#9C2B2E", alpha=0.15, label="Return Measurement Interval")

    ax.set_xlim(-0.8, 10.5)
    ax.set_ylim(0.5, 2.65)
    ax.set_yticks([])
    ax.set_xlabel("Event order; horizontal distance does not measure elapsed time")
    ax.set_xticks([0, 1.5, 2.5, 5.5, 6.5, 9.5])
    ax.set_xticklabels(["D_k 16:05", "D_k 16:25", "D_k 16:30", "D_{k+1} 09:00", "D_{k+1} 09:30", "D_{k+2} 09:30"], rotation=15, fontsize=9)
    ax.set_title("Constructed PIT Sequence (NY Local Time; Schematic Spacing)", fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", framealpha=0.9, fontsize=9)
    ax.grid(axis="x", linestyle=":", alpha=0.4)

    plt.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)


def plot_text_prediction_metrics(text_res: dict, save_path: Path) -> None:
    """Generate 2-panel chart comparing Mean vs Ridge MSE and Spearman rank correlation."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Panel 1: MSE comparison
    ax1 = axes[0]
    models = ["Train Mean\nBenchmark", f"TF-IDF Ridge\n(alpha={text_res['best_alpha']})"]
    mses = [text_res["test_mean_mse"] * 1e4, text_res["test_ridge_mse"] * 1e4]

    bars = ax1.bar(models, mses, color=["#27406B", "#9C2B2E"], width=0.45, edgecolor="#211C17", linewidth=1.2)
    for b, m in zip(bars, mses):
        ax1.text(b.get_x() + b.get_width() / 2.0, b.get_height() + 0.05, f"{m:.4f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax1.set_ylabel("Test MSE (x 10^-4)", fontsize=11)
    ax1.set_title(f"Test MSE Comparison (R^2 = {text_res['test_r2_vs_mean']:.4f})", fontsize=11, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.3)

    # Panel 2: Pooled Spearman Rank Correlation
    ax2 = axes[1]
    ic_val = text_res["test_pooled_spearman"]
    bar_ic = ax2.bar(["Pooled Rank Corr"], [ic_val], color="#27406B" if ic_val >= 0 else "#9C2B2E", width=0.35, edgecolor="#211C17", linewidth=1.2)
    ax2.axhline(0, color="#211C17", linewidth=1)
    ax2.text(bar_ic[0].get_x() + bar_ic[0].get_width() / 2.0, ic_val + 0.01 if ic_val >= 0 else ic_val - 0.02, f"{ic_val:+.4f}", ha="center", va="bottom" if ic_val >= 0 else "top", fontsize=11, fontweight="bold")
    ax2.set_ylim(-0.15, 0.25)
    ax2.set_ylabel("Spearman Rank Correlation", fontsize=11)
    ax2.set_title("Pooled Rank Correlation (30 Rotating-Asset Documents)", fontsize=11, fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)


def plot_causal_dag(save_path: Path) -> None:
    """Generate 2-panel causal Directed Acyclic Graph (DAG) for Confounder and Collider."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Confounding DAG
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis("off")
    ax1.set_title("Confounding DAG (Backdoor Path)\nCondition on Z to block T <- Z -> Y", fontsize=12, fontweight="bold")

    # Nodes
    ax1.annotate("Z: Analyst Coverage\n(Confounder)", xy=(5, 8), xytext=(5, 8),
                 bbox=dict(boxstyle="round,pad=0.5", fc="#BE8A20", ec="#211C17", lw=1.5),
                 ha="center", va="center", fontsize=10, fontweight="bold", color="white")
    ax1.annotate("T: Extra Guidance\n(Binary Treatment)", xy=(2, 2.5), xytext=(2, 2.5),
                 bbox=dict(boxstyle="round,pad=0.5", fc="#27406B", ec="#211C17", lw=1.5),
                 ha="center", va="center", fontsize=10, fontweight="bold", color="white")
    ax1.annotate("Y: Success Indicator\n(Binary Outcome)", xy=(8, 2.5), xytext=(8, 2.5),
                 bbox=dict(boxstyle="round,pad=0.5", fc="#9C2B2E", ec="#211C17", lw=1.5),
                 ha="center", va="center", fontsize=10, fontweight="bold", color="white")

    # Arrows
    ax1.annotate("", xy=(2.5, 3.2), xytext=(4.3, 7.3),
                 arrowprops=dict(arrowstyle="->", lw=2, color="#27406B"))
    ax1.text(3.0, 5.5, "Z -> T\n(High cov. -> treatment)", fontsize=9, color="#27406B")

    ax1.annotate("", xy=(7.5, 3.2), xytext=(5.7, 7.3),
                 arrowprops=dict(arrowstyle="->", lw=2, color="#9C2B2E"))
    ax1.text(6.8, 5.5, "Z -> Y\n(High cov. -> success)", fontsize=9, color="#9C2B2E")

    ax1.annotate("", xy=(6.5, 2.5), xytext=(3.5, 2.5),
                 arrowprops=dict(arrowstyle="->", lw=2.5, color="#211C17"))
    ax1.text(5.0, 1.8, "T -> Y (Causal Interpretation Requires Assumptions)", ha="center", fontsize=9, fontweight="bold")

    # Panel 2: Collider DAG
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis("off")
    ax2.set_title("Collider DAG (Selection Bias)\nConditioning on C opens T -> [C] <- Y", fontsize=12, fontweight="bold")

    # Nodes
    ax2.annotate("T: Factor Signal A\n(e.g., Momentum)", xy=(2, 7.5), xytext=(2, 7.5),
                 bbox=dict(boxstyle="round,pad=0.5", fc="#27406B", ec="#211C17", lw=1.5),
                 ha="center", va="center", fontsize=10, fontweight="bold", color="white")
    ax2.annotate("Y: Factor Signal B\n(e.g., Quality Alpha)", xy=(8, 7.5), xytext=(8, 7.5),
                 bbox=dict(boxstyle="round,pad=0.5", fc="#9C2B2E", ec="#211C17", lw=1.5),
                 ha="center", va="center", fontsize=10, fontweight="bold", color="white")
    ax2.annotate("C: Portfolio Inclusion\n(Collider C = 1{T=1 or Y=1})", xy=(5, 2.5), xytext=(5, 2.5),
                 bbox=dict(boxstyle="round,pad=0.5", fc="#5A3E1B", ec="#211C17", lw=1.5),
                 ha="center", va="center", fontsize=10, fontweight="bold", color="white")

    # Arrows
    ax2.annotate("", xy=(4.2, 3.3), xytext=(2.6, 6.8),
                 arrowprops=dict(arrowstyle="->", lw=2, color="#27406B"))
    ax2.text(2.6, 4.8, "T -> C", fontsize=10, fontweight="bold", color="#27406B")

    ax2.annotate("", xy=(5.8, 3.3), xytext=(7.4, 6.8),
                 arrowprops=dict(arrowstyle="->", lw=2, color="#9C2B2E"))
    ax2.text(6.8, 4.8, "Y -> C", fontsize=10, fontweight="bold", color="#9C2B2E")

    ax2.text(5.0, 1.2, "Independent T, Y become negatively correlated:\nCov(T, Y | C=1) = -1/9 = -0.111", ha="center", fontsize=9, fontweight="bold", color="#9C2B2E")

    plt.tight_layout()
    fig.savefig(save_path, dpi=300)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chapter 43 Bayesian and Text Pipeline CLI Runner.")
    parser.add_argument("--out", type=str, required=True, help="New run output directory (must not exist).")
    parser.add_argument("--fig-dir", type=str, default=None, help="Directory to save persistent chapter figures.")
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    if out_dir.exists():
        sys.stderr.write(f"ERROR: Output directory '{out_dir}' already exists. Refusing to overwrite.\n")
        sys.exit(1)

    chapter_fig_dir = Path(args.fig_dir).resolve() if args.fig_dir else None
    if chapter_fig_dir is not None and (chapter_fig_dir.exists() or chapter_fig_dir == out_dir or chapter_fig_dir.is_relative_to(out_dir) or out_dir.is_relative_to(chapter_fig_dir)):
        raise FileExistsError("Persistent figures require a distinct new directory.")
    out_dir.mkdir(parents=True, exist_ok=False)
    run_fig_dir = out_dir / "figures"
    run_fig_dir.mkdir(parents=True, exist_ok=False)

    if chapter_fig_dir is not None:
        chapter_fig_dir.mkdir(parents=True, exist_ok=False)

    print(f"=== Starting Chapter 43 Pipeline Execution ===")
    print(f"Run Output: {out_dir}")
    print(f"Persistent Figures: {chapter_fig_dir}")

    # 1. Bayesian Beta-Binomial & Normal Partial Pooling
    print("-> Computing Bayesian conjugate updates...")
    bayes_res = beta_binomial_posterior_predictive(alpha_prior=2.0, beta_prior=2.0, successes=8, trials=10)

    groups_spec = [
        {"n": 4, "sample_mean": 0.03},
        {"n": 36, "sample_mean": 0.01},
    ]
    normal_res = normal_hierarchical_partial_pooling(prior_mean=0.0, prior_sd=0.02, observation_sd=0.04, groups=groups_spec)

    # 2. Causal DAG & Stratified ATE
    print("-> Computing Causal ATE under Simpson's confounding...")
    causal_df = generate_causal_dataset(seed=4301)
    causal_res = compute_stratified_ate(causal_df, z_col="Z", t_col="T", y_col="Y", target_p_z={"high": 0.5, "low": 0.5})
    collider_res = demonstrate_collider_bias(n=2000, seed=4301)

    # 3. PIT Calendar & Text Models
    print("-> Generating 120 constructed transcripts and training NLP pipeline...")
    base_text_df, invalid_cases_df = generate_constructed_text_dataset(seed=4302, n_documents=120)
    eligible_text_df = filter_pit_eligible_documents(base_text_df, cutoff_col="signal_time")

    train_slice = eligible_text_df.iloc[0:60]
    val_slice = eligible_text_df.iloc[60:90]
    test_slice = eligible_text_df.iloc[90:120]

    text_model_res = train_text_prediction_models(train_slice, val_slice, test_slice, alpha_grid=[0.1, 1.0, 10.0])

    # Downstream execution interface specification (prediction-only)
    downstream_spec = downstream_execution_interface_spec()

    # Embeddings & Negation
    df_emb, emb_sims = hand_embedding_matrix()
    neg_scoring = negation_sentiment_scorer("earnings performance did not improve showing no growth despite aggressive restructuring")
    llm_audit = llm_offline_audit_ledger()

    # 4. Generate Figures
    print("-> Rendering figures...")
    plot_bayesian_updating(bayes_res, normal_res, run_fig_dir / "fig43_1_bayesian_updating.png")
    if chapter_fig_dir is not None:
        plot_bayesian_updating(bayes_res, normal_res, chapter_fig_dir / "fig43_1_bayesian_updating.png")

    plot_causal_simpson(causal_res, run_fig_dir / "fig43_2_causal_simpson.png")
    if chapter_fig_dir is not None:
        plot_causal_simpson(causal_res, chapter_fig_dir / "fig43_2_causal_simpson.png")

    plot_pit_timeline(run_fig_dir / "fig43_3_pit_text_timeline.png")
    if chapter_fig_dir is not None:
        plot_pit_timeline(chapter_fig_dir / "fig43_3_pit_text_timeline.png")

    plot_text_prediction_metrics(text_model_res, run_fig_dir / "fig43_4_text_prediction_metrics.png")
    if chapter_fig_dir is not None:
        plot_text_prediction_metrics(text_model_res, chapter_fig_dir / "fig43_4_text_prediction_metrics.png")

    plot_causal_dag(run_fig_dir / "fig43_5_causal_dag.png")
    if chapter_fig_dir is not None:
        plot_causal_dag(chapter_fig_dir / "fig43_5_causal_dag.png")

    base_text_df.to_csv(out_dir / "constructed_documents.csv", index=False)
    causal_df.to_csv(out_dir / "causal_constructed.csv", index=False)
    df_emb.to_csv(out_dir / "constructed_embedding.csv")
    pd.DataFrame({"doc_id": test_slice["doc_id"].to_numpy(), "prediction": text_model_res["test_predictions"], "target": test_slice["target_return"].to_numpy()}).to_csv(out_dir / "test_predictions.csv", index=False)

    # 5. Export Summary JSON
    summary = {
        "status": "success",
        "chapter": 43,
        "bayes": {
            "beta_prior": [bayes_res["alpha_prior"], bayes_res["beta_prior"]],
            "beta_posterior": [bayes_res["alpha_post"], bayes_res["beta_post"]],
            "posterior_mean": bayes_res["posterior_mean"],
            "posterior_variance": bayes_res["posterior_variance"],
            "joint_two_successes_predictive": bayes_res["joint_two_successes"],
            "squared_posterior_mean": bayes_res["squared_mean"],
            "predictive_covariance": bayes_res["predictive_covariance"],
            "normal_partial_pooling": normal_res,
        },
        "causal": {
            "unadjusted_difference": causal_res["unadjusted_difference"],
            "stratum_high_contrast": causal_res["stratum_stats"]["high"]["contrast"],
            "stratum_low_contrast": causal_res["stratum_stats"]["low"]["contrast"],
            "standardized_ate": causal_res["standardized_ate"],
            "simpson_reversal": causal_res["simpson_reversal"],
            "collider_demonstration": collider_res,
        },
        "text_nlp": {
            "n_documents_total": 120,
            "n_train_eligible": text_model_res["n_train_eligible"],
            "n_val_eligible": text_model_res["n_val_eligible"],
            "n_test": text_model_res["n_test"],
            "vocab_size": text_model_res["vocab_size"],
            "best_ridge_alpha": text_model_res["best_alpha"],
            "train_mean": text_model_res["train_mean"],
            "test_mean_mse": text_model_res["test_mean_mse"],
            "test_ridge_mse": text_model_res["test_ridge_mse"],
            "test_r2_vs_mean": text_model_res["test_r2_vs_mean"],
            "test_pooled_spearman": text_model_res["test_pooled_spearman"],
            "daily_cross_sectional_ic_status": text_model_res["daily_cross_sectional_ic_status"],
            "mean_benchmark_rank_ic_status": text_model_res["mean_benchmark_rank_ic_status"],
            "downstream_interface_spec": downstream_spec,
            "negation_example": neg_scoring,
            "embedding_similarities": emb_sims,
            "llm_offline_audit": llm_audit,
        },
    }

    summary_file = out_dir / "ch43_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"=== Execution Completed Successfully ===")
    print(f"Summary written to: {summary_file}")


if __name__ == "__main__":
    main()
