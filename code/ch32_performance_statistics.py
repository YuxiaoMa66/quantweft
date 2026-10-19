"""Chapter 32 CLI: Performance Statistics and Inferential Metrics.

Runs and benchmarks:
1. Pinned hand descriptive metrics (6-period return series) and arithmetic vs geometric mean.
2. Literature replication: PSR (Bailey & López de Prado 2012a) and DSR (Bailey & López de Prado 2014).
3. Pinned hand CSCV example (8 periods x 3 strategies, S=4, all 6 splits).
4. Running champion experiment: M=200 zero-skill trials, T=1250 daily returns across 3 seeds.
5. Boundary experiments: AR(1) dependence coverage distortion and correlated trials.
6. Real market illustration: Kenneth French 10 Industries (1926-2026, 1200 months, S=12).

Outputs:
- qa/a6/codex_resume/ch32/results/ch32_results.json
- qa/a6/codex_resume/ch32/figures/ch32_*.png
Refuses to overwrite existing files.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import matplotlib
if "inline" not in matplotlib.get_backend().lower():
    try:
        matplotlib.use("Agg")
    except Exception:
        pass
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.backtest import BacktestConfig, run_backtest  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.inference import (  # noqa: E402
    annualized_volatility,
    cagr,
    calmar_ratio,
    deflated_sharpe_ratio,
    equal_weighted_average_correlation,
    hit_rate,
    implied_independent_trials,
    information_ratio,
    max_drawdown,
    pbo_cscv,
    per_period_sharpe,
    probabilistic_sharpe_ratio,
    profit_factor,
    sharpe_ratio,
    sortino_ratio,
    tracking_error,
    turnover_from_ledger,
    wealth_index,
)
from quant_course.research_protocol import (  # noqa: E402
    benjamini_hochberg_adjust,
    bonferroni_adjust,
    expected_max_standard_normal,
    expected_max_standard_normal_exact,
    holm_adjust,
)

SEEDS = [20261032, 20261033, 20261034]
FIGURES = (
    "ch32_hand_cscv_splits.png",
    "ch32_psr_surface.png",
    "ch32_dsr_trials_haircut.png",
    "ch32_champion_overfitting.png",
)


# ------------------------------------------------------------------ 1. Descriptive Metrics
def run_descriptive_metrics_hand_example() -> dict:
    """Evaluate 6-period hand example and arithmetic vs geometric mean."""
    r = np.array([0.04, -0.02, 0.03, -0.01, 0.05, -0.03], dtype=np.float64)
    rf = np.full(6, 0.002, dtype=np.float64)
    rb = np.array([0.02, -0.01, 0.01, 0.00, 0.03, -0.01], dtype=np.float64)
    ann_periods = 12.0
    elapsed_years = 0.5
    initial_wealth = 1000.0

    w = wealth_index(r, initial_capital=initial_wealth)
    cagr_val = cagr(initial_wealth, w[-1], elapsed_years)
    mdd = max_drawdown(w)
    calm = calmar_ratio(cagr_val, mdd)
    vol_ann = annualized_volatility(r, ann_periods)
    sr_per = per_period_sharpe(r, rf)
    sr_ann = sharpe_ratio(r, rf, ann_periods)
    sort_per = sortino_ratio(r, target_return=0.0)
    sort_ann = sortino_ratio(r, target_return=0.0, periods_per_year=ann_periods)
    hit_strict = hit_rate(r, include_zero=False)
    hit_all = hit_rate(r, include_zero=True)
    pf = profit_factor(r)
    te = tracking_error(r, rb, ann_periods)
    ir = information_ratio(r, rb, ann_periods)

    # Arithmetic vs geometric mean: +50%, -50%
    r_two = np.array([0.50, -0.50])
    w_two = wealth_index(r_two, initial_capital=1.0)
    arith_mean = float(r_two.mean())
    geom_mean = math.sqrt(1.5 * 0.5) - 1.0

    # Chapter 29 frozen backtest ledger turnover
    d_idx = pd.date_range("2026-01-05", periods=4, freq="B")
    mark = pd.DataFrame({"A": [10.0, 11.0, 12.1, 12.0], "B": [20.0, 19.0, 19.0, 21.0]}, index=d_idx)
    execp = pd.DataFrame({"A": [10.0, 10.0, 12.0, 12.0], "B": [20.0, 20.0, 19.5, 20.0]}, index=d_idx)
    tw = pd.DataFrame({"A": [0.5, 0.5], "B": [0.3, 0.3]}, index=[d_idx[0], d_idx[2]])
    cfg = BacktestConfig(initial_cash=1000.0, fee_rate=0.002)
    res_bt = run_backtest(mark, tw, cfg, exec_prices=execp)
    turnover_series = turnover_from_ledger(res_bt.ledger)

    return {
        "hand_returns": r.tolist(),
        "hand_rf": rf.tolist(),
        "hand_benchmark": rb.tolist(),
        "annualization_factor_A": ann_periods,
        "elapsed_years": elapsed_years,
        "wealth_path": [round(x, 6) for x in w.tolist()],
        "cagr": round(cagr_val, 6),
        "max_drawdown": round(mdd, 6),
        "calmar_ratio": round(calm, 6),
        "annualized_volatility": round(vol_ann, 6),
        "per_period_sharpe": round(sr_per, 6),
        "annualized_sharpe": round(sr_ann, 6),
        "per_period_sortino": round(sort_per, 6),
        "annualized_sortino": round(sort_ann, 6),
        "hit_rate_strict": round(hit_strict, 6),
        "hit_rate_all": round(hit_all, 6),
        "profit_factor": round(pf, 6),
        "tracking_error": round(te, 6),
        "information_ratio": round(ir, 6),
        "arithmetic_vs_geometric": {
            "returns": [0.50, -0.50],
            "terminal_wealth": round(float(w_two[-1]), 6),
            "arithmetic_mean": round(arith_mean, 6),
            "geometric_mean": round(geom_mean, 6),
        },
        "ch29_ledger_turnover": {
            "trade_dates": [str(d.date()) for d in d_idx],
            "turnover_values": [round(float(x), 6) for x in turnover_series.tolist()],
            "traded_notional_sum": round(float(res_bt.ledger["traded_notional"].sum()), 6),
        },
    }


# ------------------------------------------------------------------ 2. Paper Replications
def run_paper_replications() -> dict:
    """Verify PSR and DSR examples from primary literature."""
    # PSR: Bailey & López de Prado (2012a, pp. 9-10)
    sr_hat = 0.458
    n_24 = 24
    psr_norm = probabilistic_sharpe_ratio(sr_hat, 0.0, n_24, skew=0.0, kurt=3.0)
    psr_non_norm_24 = probabilistic_sharpe_ratio(sr_hat, 0.0, n_24, skew=-2.448, kurt=10.164)
    psr_non_norm_36 = probabilistic_sharpe_ratio(sr_hat, 0.0, 36, skew=-2.448, kurt=10.164)

    # DSR: Bailey & López de Prado (2014, pp. 7-10)
    t_obs = 1250
    ann_factor = 250.0
    var_sr_daily = 0.5 / ann_factor
    sr_daily = 2.5 / math.sqrt(ann_factor)
    skew_dsr = -3.0
    kurt_dsr = 10.0

    dsr_100, sr0_100 = deflated_sharpe_ratio(sr_daily, var_sr_daily, 100, t_obs, skew=skew_dsr, kurt=kurt_dsr)
    dsr_46, sr0_46 = deflated_sharpe_ratio(sr_daily, var_sr_daily, 46, t_obs, skew=skew_dsr, kurt=kurt_dsr)
    dsr_88_norm, sr0_88_norm = deflated_sharpe_ratio(sr_daily, var_sr_daily, 88, t_obs, skew=0.0, kurt=3.0)

    # Sensitivity across N
    n_grid = [2, 5, 10, 20, 46, 50, 88, 100, 200, 500]
    n_sensitivity = []
    for n_val in n_grid:
        d_val, s0_val = deflated_sharpe_ratio(sr_daily, var_sr_daily, n_val, t_obs, skew=skew_dsr, kurt=kurt_dsr)
        d_norm, s0_norm = deflated_sharpe_ratio(sr_daily, var_sr_daily, n_val, t_obs, skew=0.0, kurt=3.0)
        n_sensitivity.append({
            "n_trials": n_val,
            "sr0_daily": round(s0_val, 6),
            "sr0_annualized": round(s0_val * math.sqrt(ann_factor), 6),
            "dsr_skewed": round(d_val, 6),
            "dsr_normal": round(d_norm, 6),
        })

    # Implied independent trials sensitivity (App. A.3)
    corr_grid = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
    corr_sensitivity = []
    for rho in corr_grid:
        n_hat = implied_independent_trials(100, rho)
        corr_sensitivity.append({"avg_corr": rho, "m_trials": 100, "implied_n": round(n_hat, 4)})

    # Expected max standard normal comparison
    ev_comparison = []
    for n_val in [10, 50, 100]:
        exact = expected_max_standard_normal_exact(n_val)
        approx = expected_max_standard_normal(n_val)
        ev_comparison.append({
            "n_trials": n_val,
            "exact_integral": round(exact, 6),
            "bldp_approx": round(approx, 6),
            "difference": round(approx - exact, 6),
        })

    return {
        "psr_replication": {
            "sample_months_initial": n_24,
            "observed_monthly_sharpe": sr_hat,
            "psr_normal": round(psr_norm, 6),
            "psr_non_normal_n24": round(psr_non_norm_24, 6),
            "psr_non_normal_n36": round(psr_non_norm_36, 6),
        },
        "dsr_replication": {
            "sample_length_t": t_obs,
            "annualized_sharpe": 2.5,
            "daily_sharpe": round(sr_daily, 6),
            "var_sharpe_daily": round(var_sr_daily, 6),
            "n100": {"sr0_daily": round(sr0_100, 6), "dsr": round(dsr_100, 6)},
            "n46": {"sr0_daily": round(sr0_46, 6), "dsr": round(dsr_46, 6)},
            "n88_normal": {"sr0_daily": round(sr0_88_norm, 6), "dsr": round(dsr_88_norm, 6)},
            "n_sensitivity": n_sensitivity,
        },
        "implied_independent_trials_sensitivity": corr_sensitivity,
        "expected_max_standard_normal_comparison": ev_comparison,
    }


# ------------------------------------------------------------------ 3. Pinned Hand CSCV Example
def run_pinned_hand_cscv() -> dict:
    """Evaluate the pinned 8x3 matrix with S=4 across all 6 combinations."""
    rows = [
        [0.02, 0.01, -0.01],
        [0.01, 0.00, 0.02],
        [-0.01, 0.02, 0.00],
        [0.03, -0.01, 0.01],
        [0.00, 0.01, 0.02],
        [-0.02, 0.03, 0.01],
        [0.01, -0.02, 0.03],
        [0.02, 0.00, -0.01]
    ]
    mat = np.array(rows, dtype=np.float64)
    res = pbo_cscv(mat, n_blocks=4)

    splits_info = []
    for p in res.partitions:
        splits_info.append({
            "split_index": p.split_index,
            "is_blocks": list(p.is_blocks),
            "oos_blocks": list(p.oos_blocks),
            "best_strategy_index": p.best_strategy_index,
            "is_sharpe_best": round(p.is_sharpe_best, 6),
            "oos_sharpe_best": round(p.oos_sharpe_best, 6),
            "oos_rank_best": round(p.oos_rank_best, 2),
            "relative_rank_omega": round(p.relative_rank_omega, 4),
            "logit_lambda": round(p.logit_lambda, 6),
            "is_overfit_cscv": p.is_overfit_cscv,
            "is_overfit_strict": p.is_overfit_strict,
            "is_loss": p.is_loss,
        })

    return {
        "matrix_shape": list(mat.shape),
        "n_blocks_s": 4,
        "n_splits": res.n_splits,
        "pbo_cscv": round(res.pbo_cscv, 6),
        "pbo_strict": round(res.pbo_strict, 6),
        "prob_loss": round(res.prob_loss, 6),
        "mean_is_sharpe": round(res.mean_is_sharpe, 6),
        "mean_oos_sharpe": round(res.mean_oos_sharpe, 6),
        "mean_degradation": round(res.mean_degradation, 6),
        "degradation_slope": round(res.degradation_slope, 6),
        "splits": splits_info,
    }


# ------------------------------------------------------------------ 4. Champion Overfitting Experiment
def run_champion_experiment(seeds: list[int]) -> dict:
    """Simulate M=200 zero-skill trials over T=1250 daily periods across multiple seeds."""
    t_obs = 1250
    m_trials = 200
    s_blocks = 10
    ann_factor = 250.0

    seed_results = []
    for s in seeds:
        rng = np.random.default_rng(s)
        mat = rng.normal(0.0, 0.01, (t_obs, m_trials))

        per_sr = np.mean(mat, axis=0) / np.std(mat, axis=0, ddof=1)
        ann_sr = per_sr * math.sqrt(ann_factor)

        champ_idx = int(np.argmax(per_sr))
        champ_ann_sr = float(ann_sr[champ_idx])
        champ_per_sr = float(per_sr[champ_idx])

        champ_ret = mat[:, champ_idx]
        champ_skew = float(stats.skew(champ_ret, bias=False))
        champ_kurt = float(stats.kurtosis(champ_ret, fisher=False, bias=False))

        # Unadjusted p-value for H0: true SR <= 0
        t_stat = champ_per_sr * math.sqrt(t_obs)
        p_unadj = float(1.0 - stats.norm.cdf(t_stat))

        # Adjusted p-values
        all_t = per_sr * math.sqrt(t_obs)
        all_p = 1.0 - stats.norm.cdf(all_t)
        p_bonf = float(bonferroni_adjust(all_p)[champ_idx])
        p_holm = float(holm_adjust(all_p)[champ_idx])
        p_bh = float(benjamini_hochberg_adjust(all_p)[champ_idx])

        # DSR
        var_sr = float(np.var(per_sr, ddof=1))
        dsr_val, sr0_val = deflated_sharpe_ratio(
            champ_per_sr, var_sr, m_trials, t_obs, skew=champ_skew, kurt=champ_kurt
        )

        # CSCV on 1250 x 200 with S=10 (252 splits)
        cscv_res = pbo_cscv(mat, n_blocks=s_blocks)

        seed_results.append({
            "seed": s,
            "champion_index": champ_idx,
            "champion_annualized_sharpe": round(champ_ann_sr, 4),
            "champion_per_period_sharpe": round(champ_per_sr, 6),
            "champion_skewness": round(champ_skew, 4),
            "champion_raw_kurtosis": round(champ_kurt, 4),
            "unadjusted_p_value": round(p_unadj, 6),
            "bonferroni_adjusted_p": round(p_bonf, 6),
            "holm_adjusted_p": round(p_holm, 6),
            "benjamini_hochberg_p": round(p_bh, 6),
            "var_sharpe_per_period": round(var_sr, 6),
            "dsr_threshold_sr0_daily": round(sr0_val, 6),
            "dsr_threshold_sr0_ann": round(sr0_val * math.sqrt(ann_factor), 4),
            "deflated_sharpe_ratio": round(dsr_val, 6),
            "cscv_pbo": round(cscv_res.pbo_cscv, 6),
            "cscv_pbo_strict": round(cscv_res.pbo_strict, 6),
            "cscv_prob_loss": round(cscv_res.prob_loss, 6),
            "cscv_mean_is_sharpe_ann": round(cscv_res.mean_is_sharpe * math.sqrt(ann_factor), 4),
            "cscv_mean_oos_sharpe_ann": round(cscv_res.mean_oos_sharpe * math.sqrt(ann_factor), 4),
            "cscv_mean_degradation_ann": round(cscv_res.mean_degradation * math.sqrt(ann_factor), 4),
            "cscv_degradation_slope": round(cscv_res.degradation_slope, 4),
        })

    return {
        "trials_m": m_trials,
        "sample_length_t": t_obs,
        "s_blocks": s_blocks,
        "n_splits": 252,
        "seeds_evaluated": seed_results,
    }


# ------------------------------------------------------------------ 5. Boundary Experiments
def run_boundary_experiments(seed: int = 20261032) -> dict:
    """Evaluate AR(1) dependence coverage distortion and correlated trials."""
    rng = np.random.default_rng(seed)
    t_obs = 1000
    n_sims = 2000
    phi_grid = [-0.3, 0.0, 0.3, 0.5]

    dependence_results = []
    for phi in phi_grid:
        var_inflation = (1.0 + phi) / (1.0 - phi)
        se_inflation = math.sqrt(var_inflation)

        # Simulate n_sims AR(1) series with true mean 0
        z_stats_naive = []
        for _ in range(n_sims):
            eps = rng.normal(0, 1, t_obs + 200)
            x = np.empty(t_obs + 200)
            x[0] = 0.0
            for t in range(1, len(x)):
                x[t] = phi * x[t - 1] + eps[t]
            series = x[200:]
            sr_hat = float(series.mean() / np.std(series, ddof=1))
            # Naive test stat assuming iid normal
            z_naive = sr_hat * math.sqrt(t_obs) / math.sqrt(1.0 + 0.5 * sr_hat ** 2)
            z_stats_naive.append(z_naive)

        z_arr = np.array(z_stats_naive)
        # Two-tailed 95% nominal rejection rate (should be 5% under null)
        type_1_error = float(np.mean(np.abs(z_arr) > 1.959964))

        dependence_results.append({
            "ar1_phi": phi,
            "theoretical_var_inflation": round(var_inflation, 4),
            "theoretical_se_inflation": round(se_inflation, 4),
            "simulated_type_1_error_at_nominal_5pct": round(type_1_error, 4),
        })

    # Correlated trials experiment
    m_trials = 200
    target_corr = 0.5
    # Build equicorrelated covariance matrix: Sigma = (1 - rho)*I + rho*11'
    sigma = (1.0 - target_corr) * np.eye(m_trials) + target_corr * np.ones((m_trials, m_trials))
    l_factor = np.linalg.cholesky(sigma)

    # Sample 1250 daily returns with rho = 0.5
    uncorr = rng.normal(0, 0.01, (1250, m_trials))
    corr_mat = uncorr @ l_factor.T
    emp_corr = np.corrcoef(corr_mat, rowvar=False)
    rho_hat = equal_weighted_average_correlation(emp_corr)
    n_hat = implied_independent_trials(m_trials, rho_hat)

    # Sharpes of correlated trials
    per_sr_corr = np.mean(corr_mat, axis=0) / np.std(corr_mat, axis=0, ddof=1)
    max_sr_corr = float(np.max(per_sr_corr))
    var_sr_corr = float(np.var(per_sr_corr, ddof=1))

    dsr_naive, sr0_naive = deflated_sharpe_ratio(max_sr_corr, var_sr_corr, m_trials, 1250)
    dsr_adj, sr0_adj = deflated_sharpe_ratio(max_sr_corr, var_sr_corr, int(round(n_hat)), 1250)

    return {
        "ar1_dependence": dependence_results,
        "ar1_simulation": {
            "seed": seed,
            "sample_length_t": t_obs,
            "n_simulations": n_sims,
            "test_sides": 2,
            "nominal_alpha": 0.05,
        },
        "correlated_trials": {
            "m_trials": m_trials,
            "target_correlation": target_corr,
            "sample_average_correlation": round(rho_hat, 4),
            "implied_independent_n": round(n_hat, 2),
            "observed_max_daily_sharpe": round(max_sr_corr, 6),
            "sr0_naive_n200": round(sr0_naive, 6),
            "dsr_naive_n200": round(dsr_naive, 6),
            "sr0_adjusted_n_hat": round(sr0_adj, 6),
            "dsr_adjusted_n_hat": round(dsr_adj, 6),
        },
    }


# ------------------------------------------------------------------ 6. Real Market Example
def run_french_market_example() -> dict:
    """Evaluate French industry excess returns over RF across 1200 monthly observations."""
    df_ind, rf, meta = load_industries_and_rf()
    # Take last 1200 months (100 years, divisible by S=12)
    sample_df = df_ind.iloc[-1200:].copy()
    sample_rf = rf.iloc[-1200:]
    excess_df = sample_df.sub(sample_rf, axis=0)
    mat = excess_df.to_numpy()
    ann_factor = 12.0

    # Per-period and annualized Sharpes on matched monthly excess returns.
    per_sr = np.mean(mat, axis=0) / np.std(mat, axis=0, ddof=1)
    ann_sr = per_sr * math.sqrt(ann_factor)

    industry_stats = []
    for col_idx, col_name in enumerate(excess_df.columns):
        industry_stats.append({
            "industry": col_name,
            "annualized_excess_return": round(float(excess_df[col_name].mean() * ann_factor), 4),
            "annualized_vol": round(float(excess_df[col_name].std(ddof=1) * math.sqrt(ann_factor)), 4),
            "annualized_sharpe": round(float(ann_sr[col_idx]), 4),
        })

    # CSCV with S=12 -> 924 splits
    cscv_res = pbo_cscv(mat, n_blocks=12)

    return {
        "dataset_name": meta.get("source", "Kenneth French 10 Industries"),
        "snapshot_date": meta["snapshot_date"],
        "risk_free_benchmark": "matched monthly FF3 RF; industry total returns converted to excess returns",
        "is_point_in_time": meta["is_point_in_time"],
        "source_limitation": meta["limitation"],
        "sample_start": str(sample_df.index[0]),
        "sample_end": str(sample_df.index[-1]),
        "sample_months": 1200,
        "n_industries": 10,
        "s_blocks": 12,
        "n_splits": cscv_res.n_splits,
        "industry_statistics": industry_stats,
        "pbo_cscv": round(cscv_res.pbo_cscv, 6),
        "pbo_strict": round(cscv_res.pbo_strict, 6),
        "prob_loss": round(cscv_res.prob_loss, 6),
        "mean_is_sharpe_ann": round(cscv_res.mean_is_sharpe * math.sqrt(ann_factor), 4),
        "mean_oos_sharpe_ann": round(cscv_res.mean_oos_sharpe * math.sqrt(ann_factor), 4),
        "mean_degradation_ann": round(cscv_res.mean_degradation * math.sqrt(ann_factor), 4),
        "degradation_slope": round(cscv_res.degradation_slope, 4),
    }


# ------------------------------------------------------------------ 7. Figure Generation
def generate_figures(results: dict, fig_dir: Path) -> None:
    """Generate 4 figures with explicit axes, units, samples, and sources."""
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. ch32_hand_cscv_splits.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    hand_splits = results["pinned_hand_cscv"]["splits"]
    split_indices = [s["split_index"] for s in hand_splits]
    ranks = [s["oos_rank_best"] for s in hand_splits]
    logits = [s["logit_lambda"] for s in hand_splits]

    ax1.bar(split_indices, ranks, color="#2b5c8f", alpha=0.85, edgecolor="black")
    ax1.axhline(1.5, color="#d95f02", linestyle="--", linewidth=1.5, label="Strict Definition 2.2 threshold (N/2 = 1.5)")
    ax1.set_xlabel("CSCV Split Index c (1 to 6)", fontsize=10)
    ax1.set_ylabel("OOS Rank of IS Champion (Best=3)", fontsize=10)
    ax1.set_title("OOS Ranks Across 6 CSCV Splits\n[Sample: 8 periods x 3 strategies; Source: Hand CSCV]", fontsize=11)
    ax1.set_xticks(split_indices)
    ax1.set_ylim(0, 3.5)
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(True, linestyle=":", alpha=0.6)

    colors = ["#d95f02" if l <= 0 else "#2b5c8f" for l in logits]
    ax2.bar(split_indices, logits, color=colors, alpha=0.85, edgecolor="black")
    ax2.axhline(0.0, color="black", linestyle="-", linewidth=1.2, label=r"PBO boundary $\lambda \leq 0$")
    ax2.set_xlabel("CSCV Split Index c (1 to 6)", fontsize=10)
    ax2.set_ylabel(r"Logit Relative Rank $\lambda_c = \ln(\bar{\omega}_c / (1 - \bar{\omega}_c))$", fontsize=10)
    ax2.set_title(r"Logit Relative Rank $\lambda_c$ Distribution" + "\n" + r"[All 6 splits $\leq 0 \to \mathrm{PBO}=1.0$]", fontsize=11)
    ax2.set_xticks(split_indices)
    ax2.legend(loc="lower right", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(fig_dir / "ch32_hand_cscv_splits.png", dpi=300)
    plt.close(fig)

    # 2. ch32_psr_surface.png
    fig, ax = plt.subplots(figsize=(8, 5))
    n_months = np.linspace(6, 60, 100)
    sr_val = 0.458  # Monthly Sharpe from paper

    psr_norm = [probabilistic_sharpe_ratio(sr_val, 0.0, int(round(n)), skew=0.0, kurt=3.0) for n in n_months]
    psr_mild = [probabilistic_sharpe_ratio(sr_val, 0.0, int(round(n)), skew=-1.0, kurt=5.0) for n in n_months]
    psr_hedge = [probabilistic_sharpe_ratio(sr_val, 0.0, int(round(n)), skew=-2.448, kurt=10.164) for n in n_months]

    ax.plot(n_months, psr_norm, label=r"Normal ($\gamma_3=0, \gamma_4=3$)", color="#2b5c8f", linewidth=2.0)
    ax.plot(n_months, psr_mild, label=r"Mild Non-Normal ($\gamma_3=-1, \gamma_4=5$)", color="#7570b3", linewidth=2.0, linestyle="--")
    ax.plot(n_months, psr_hedge, label=r"Paper Track Record ($\gamma_3=-2.448, \gamma_4=10.164$)", color="#d95f02", linewidth=2.2)

    ax.axhline(0.95, color="red", linestyle=":", linewidth=1.5, label="95% Confidence Threshold")
    ax.scatter([24, 24, 36], [
        results["paper_replications"]["psr_replication"]["psr_normal"],
        results["paper_replications"]["psr_replication"]["psr_non_normal_n24"],
        results["paper_replications"]["psr_replication"]["psr_non_normal_n36"],
    ], color=["#2b5c8f", "#d95f02", "#d95f02"], s=60, zorder=5)

    ax.set_xlabel("Sample Length n (Monthly Return Intervals)", fontsize=10)
    ax.set_ylabel("Probabilistic Sharpe Ratio PSR(0)", fontsize=10)
    ax.set_title("Probabilistic Sharpe Ratio vs Sample Length and Non-Normality\n[Monthly SR=0.458; Source: Bailey & López de Prado (2012a)]", fontsize=11)
    ax.legend(loc="lower right", fontsize=9)
    ax.set_ylim(0.70, 1.01)
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(fig_dir / "ch32_psr_surface.png", dpi=300)
    plt.close(fig)

    # 3. ch32_dsr_trials_haircut.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    dsr_sens = results["paper_replications"]["dsr_replication"]["n_sensitivity"]
    n_vals = [d["n_trials"] for d in dsr_sens]
    sr0_ann = [d["sr0_annualized"] for d in dsr_sens]
    dsr_skew = [d["dsr_skewed"] for d in dsr_sens]
    dsr_norm = [d["dsr_normal"] for d in dsr_sens]

    ax1.plot(n_vals, sr0_ann, marker="o", color="#2b5c8f", linewidth=2.0)
    ax1.set_xlabel("Number of Independent Trials N", fontsize=10)
    ax1.set_ylabel(r"Deflated Hurdle $SR_0$ (Annualized)", fontsize=10)
    ax1.set_title(r"Expected Max Sharpe Hurdle $SR_0$ vs $N$" + "\n" + r"[T=1250 days; Source: Bailey & López de Prado (2014)]", fontsize=11)
    ax1.grid(True, linestyle=":", alpha=0.6)

    ax2.plot(n_vals, dsr_skew, marker="s", color="#d95f02", linewidth=2.0, label=r"Skewed ($\gamma_3=-3, \gamma_4=10$)")
    ax2.plot(n_vals, dsr_norm, marker="^", color="#2b5c8f", linewidth=2.0, linestyle="--", label=r"Normal ($\gamma_3=0, \gamma_4=3$)")
    ax2.axhline(0.95, color="red", linestyle=":", linewidth=1.5, label="95% Acceptance Threshold")
    ax2.set_xlabel("Number of Independent Trials N", fontsize=10)
    ax2.set_ylabel("Deflated Sharpe Ratio DSR", fontsize=10)
    ax2.set_title("Deflated Sharpe Ratio vs Number of Trials N\n[Annualized SR=2.5; T=1250 days]", fontsize=11)
    ax2.legend(loc="lower left", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(fig_dir / "ch32_dsr_trials_haircut.png", dpi=300)
    plt.close(fig)

    # 4. ch32_champion_overfitting.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    # Use seed 1 from champion experiment
    champ_seed1 = results["champion_experiment"]["seeds_evaluated"][0]
    s1 = champ_seed1["seed"]
    rng = np.random.default_rng(s1)
    mat1 = rng.normal(0, 0.01, (1250, 200))
    ann_sr_all = (np.mean(mat1, axis=0) / np.std(mat1, axis=0, ddof=1)) * math.sqrt(250.0)

    ax1.hist(ann_sr_all, bins=25, color="#a6bddb", edgecolor="black", alpha=0.8, density=True)
    champ_sr = champ_seed1["champion_annualized_sharpe"]
    sr0_champ = champ_seed1["dsr_threshold_sr0_ann"]
    ax1.axvline(champ_sr, color="#d95f02", linewidth=2.5, label=f"Observed Champion ({champ_sr:.2f})")
    ax1.axvline(sr0_champ, color="black", linestyle="--", linewidth=2.0, label=f"DSR Hurdle SR0 ({sr0_champ:.2f})")
    ax1.set_xlabel("Annualized Sharpe Ratio", fontsize=10)
    ax1.set_ylabel("Density across 200 Trials", fontsize=10)
    ax1.set_title(f"Trial Distribution vs Champion Selection\n[Seed {s1}; M=200 Zero-Skill Strategies; T=1250]", fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # CSCV logit distribution for seed 1
    cscv_seed1 = pbo_cscv(mat1, n_blocks=10)
    logits_seed1 = [p.logit_lambda for p in cscv_seed1.partitions]
    ax2.hist(logits_seed1, bins=20, color="#fc8d62", edgecolor="black", alpha=0.8, density=True)
    ax2.axvline(0.0, color="black", linestyle="-", linewidth=2.0, label=r"PBO boundary $\lambda \leq 0$")
    ax2.set_xlabel(r"CSCV Logit $\lambda_c$", fontsize=10)
    ax2.set_ylabel("Density across 252 Splits", fontsize=10)
    ax2.set_title(f"CSCV Logit Distribution (PBO = {cscv_seed1.pbo_cscv:.2%})\n[S=10 blocks; C(10,5)=252 splits]", fontsize=11)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(fig_dir / "ch32_champion_overfitting.png", dpi=300)
    plt.close(fig)


# ------------------------------------------------------------------ 8. Run & Main
def run(out_dir: Path, fig_dir: Path) -> dict:
    """Execute all Chapter 32 experiments and persist results."""
    out_file = out_dir / "ch32_results.json"

    # Refuse to overwrite policy
    if out_file.exists():
        raise FileExistsError(f"Refusing to overwrite existing results file: {out_file}")
    for fig_name in FIGURES:
        fig_path = fig_dir / fig_name
        if fig_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing figure: {fig_path}")

    print("Running Chapter 32 Performance Statistics experiments...")

    print("1. Running Hand Descriptive Metrics and Mean Comparison...")
    hand_metrics = run_descriptive_metrics_hand_example()

    print("2. Running Literature Replications (PSR and DSR)...")
    paper_rep = run_paper_replications()

    print("3. Running Pinned Hand CSCV Example (8x3, S=4)...")
    hand_cscv = run_pinned_hand_cscv()

    print("4. Running Champion Overfitting Experiment across 3 seeds...")
    champ_exp = run_champion_experiment(SEEDS)

    print("5. Running Boundary Experiments (AR(1) Dependence & Correlated Trials)...")
    boundary_exp = run_boundary_experiments(SEEDS[0])

    print("6. Running Real Market Illustration on French 10 Industries...")
    french_exp = run_french_market_example()

    results = {
        "chapter": 32,
        "title": "Performance Statistics and Inference",
        "hand_descriptive_metrics": hand_metrics,
        "paper_replications": paper_rep,
        "pinned_hand_cscv": hand_cscv,
        "champion_experiment": champ_exp,
        "boundary_experiments": boundary_exp,
        "french_market_experiment": french_exp,
    }

    print(f"Generating figures to {fig_dir}...")
    generate_figures(results, fig_dir)

    print(f"Writing results JSON to {out_file}...")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Chapter 32 CLI execution completed successfully.")
    return results


def main(args_list: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chapter 32 CLI: Performance Statistics and Inference.")
    parser.add_argument("--out", type=Path, default=ROOT / "qa/a6/codex_resume/ch32/results", help="Output directory for results JSON")
    parser.add_argument("--figures", type=Path, default=ROOT / "qa/a6/codex_resume/ch32/figures", help="Output directory for generated figures")
    args = parser.parse_args(args_list)

    try:
        run(args.out, args.figures)
    except FileExistsError as err:
        raise SystemExit(str(err)) from err


if __name__ == "__main__":
    main()
