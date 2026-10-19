"""Chapter 31 CLI: Financial Model Validation.

Implements and benchmarks:
1. Pinned hand example (single-series purge/embargo, gap=h-1 equivalence vs panel gap failure).
2. Data leakage study across validation schemes (Shuffled K-fold, Naive TimeSeriesSplit gap=0,
   TimeSeriesSplit gap=4 with global scaling, and Purged Walk-Forward with train-only scaling).
3. Purged K-fold vs Purged Walk-Forward comparison on contiguous time blocks.
4. Honest nested hyperparameter selection vs naive test-tuning.
5. Real market illustration on Kenneth French 10 Industries (1926-2026, 3-month overlapping labels).

Outputs:
- build/codex_a6/final_learning_review/ch31/results/ch31_results.json
- build/codex_a6/final_learning_review/ch31/figures/ch31_*.png
Refuses to overwrite existing files.

Reader packaging note: paths above document historical source outputs only.
Current CLI defaults write to one unique runs/cli_<chapter>_<uuid>/results and figures.
French CLI branches require separate rights and execution authorization;
use the adapted Notebook for the default offline constructed teaching route.
"""
from __future__ import annotations

import argparse
import json
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
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, TimeSeriesSplit
from sklearn.neighbors import KNeighborsRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.validation import (  # noqa: E402
    check_label_intervals,
    embargo,
    intervals_overlap,
    nested_hyperparameter_evaluation,
    purge,
    purged_kfold_splits,
    temporal_train_test_split,
    walk_forward_splits,
)

SEEDS = [20261031, 20261032, 20261033, 20261034, 20261035]
FIGURES = (
    "ch31_hand_label_intervals.png",
    "ch31_leakage_comparison.png",
    "ch31_gap_vs_purge_panel.png",
    "ch31_french_rolling_validation.png",
)


# ------------------------------------------------------------------ 1. Hand Example
def run_hand_example() -> dict:
    """The frozen A6 contract hand example:

    One asset, observation dates t = 0..14, horizon h = 5 => I_t = (t, t+5].
    Test block: t in {6, 7, 8} => intervals (6, 11], (7, 12], (8, 13].
    Candidate training: all other t => {0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14}.
    Look-back window m = 3.
    """
    t = np.arange(15, dtype=float)
    h = 5
    e = t + h

    test_idx = np.array([6, 7, 8])
    cand_train = np.array([0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14])

    purged_train = purge(cand_train, test_idx, t, e)
    removed_by_purge = np.setdiff1d(cand_train, purged_train)

    # Embargo with m = 3
    final_train = embargo(purged_train, test_idx, t, e, m=3)
    removed_by_embargo = np.setdiff1d(purged_train, final_train)

    # Gap on single series: TimeSeriesSplit(gap=4)
    # Forward walk-forward: candidate train 0..5, test 6..8
    gap = h - 1
    tss_single = TimeSeriesSplit(n_splits=2, test_size=3, gap=gap)
    train_tss_single, test_tss_single = next(tss_single.split(np.arange(12)))

    # Gap on 3-asset panel: dates 0..14, 3 assets each => 45 rows
    # Ordered by (date, asset)
    dates_panel = np.repeat(np.arange(15), 3)
    e_panel = dates_panel + h
    test_panel_idx = np.arange(18, 27)  # dates 6, 7, 8 (9 rows)
    cand_train_panel = np.arange(18)  # dates 0..5 (18 rows)

    purged_panel = purge(cand_train_panel, test_panel_idx, dates_panel, e_panel)

    tss_panel = TimeSeriesSplit(n_splits=2, test_size=9, gap=gap)
    train_tss_panel, test_tss_panel = next(tss_panel.split(np.arange(36)))

    overlapping_rows_in_tss = [
        int(idx) for idx in train_tss_panel if dates_panel[idx] in {2, 3, 4, 5}
    ]

    return {
        "observations": list(range(15)),
        "horizon_h": h,
        "test_indices": test_idx.tolist(),
        "candidate_train_indices": cand_train.tolist(),
        "purged_train_indices": purged_train.tolist(),
        "removed_by_purge": removed_by_purge.tolist(),
        "removed_by_purge_pre_test": [2, 3, 4, 5],
        "removed_by_purge_post_test": [9, 10, 11, 12],
        "touching_index_kept": 1,
        "embargo_m": 3,
        "e_max_test": 13,
        "embargo_interval": [13, 16],
        "removed_by_embargo": removed_by_embargo.tolist(),
        "final_train_indices": final_train.tolist(),
        "single_series_gap": gap,
        "single_series_tss_train": train_tss_single.tolist(),
        "single_series_gap_matches_purge": bool(np.array_equal(train_tss_single, [0, 1])),
        "panel_assets": 3,
        "panel_purged_train_indices": purged_panel.tolist(),
        "panel_tss_train_indices": train_tss_panel.tolist(),
        "panel_tss_overlapping_rows": overlapping_rows_in_tss,
        "panel_tss_overlapping_count": len(overlapping_rows_in_tss),
    }


# ------------------------------------------------------------------ 2. Data Leakage Study
def generate_synthetic_panel(seed: int, n_assets: int = 20, n_dates: int = 500) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic daily panel with known DGP.

    DGP:
    - 20 assets across 500 trading dates.
    - True factor f_t ~ AR(1) with rho=0.8, sigma=1.0.
    - Feature X0: asset loading * f_t + noise (persistent factor).
    - Feature X1: past 10-day return momentum.
    - Feature X2: pure Gaussian noise.
    - Daily return: r_{i, t+1} = 0.02 * X0_{i, t} + eps_{i, t+1} (weak signal).
    - Synthetic label: 5-day forward additive-return approximation
      y_{i, t} = sum_{k=1}^5 r_{i, t+k}. This differs from the chapter's formal
      compounded-simple-return label but retains the same interval geometry.
    """
    rng = np.random.RandomState(seed)

    # Simulate latent market factor AR(1)
    f = np.zeros(n_dates)
    f_innov = rng.normal(0, 1, size=n_dates)
    for t_step in range(1, n_dates):
        f[t_step] = 0.8 * f[t_step - 1] + f_innov[t_step]

    # Asset loadings
    betas = rng.uniform(0.5, 1.5, size=n_assets)

    # Features and returns
    X0 = np.zeros((n_dates, n_assets))
    for i in range(n_assets):
        X0[:, i] = betas[i] * f + rng.normal(0, 0.5, size=n_dates)

    daily_returns = np.zeros((n_dates, n_assets))
    for t_step in range(n_dates - 1):
        daily_returns[t_step + 1] = 0.02 * X0[t_step] + rng.normal(0, 0.02, size=n_assets)

    # Feature X1: 10-day momentum
    X1 = np.zeros((n_dates, n_assets))
    for t_step in range(10, n_dates):
        X1[t_step] = np.sum(daily_returns[t_step - 9 : t_step + 1], axis=0)

    # Feature X2: noise
    X2 = rng.normal(0, 1, size=(n_dates, n_assets))

    # 5-day forward additive-return approximation over next 5 trading days
    # y_{i, t} = sum_{k=1}^5 daily_returns_{i, t+k}
    h = 5
    valid_dates = n_dates - h
    y_mat = np.zeros((valid_dates, n_assets))
    for t_step in range(valid_dates):
        y_mat[t_step] = np.sum(daily_returns[t_step + 1 : t_step + 1 + h], axis=0)

    # Flatten to (N_samples, P) ordered by (date, asset)
    # Samples: valid_dates * n_assets
    date_indices = []
    asset_indices = []
    X_rows = []
    y_rows = []

    for t_step in range(valid_dates):
        for i in range(n_assets):
            date_indices.append(t_step)
            asset_indices.append(i)
            X_rows.append([X0[t_step, i], X1[t_step, i], X2[t_step, i]])
            y_rows.append(y_mat[t_step, i])

    t_obs = np.array(date_indices, dtype=float)
    e_obs = t_obs + h
    X = np.array(X_rows, dtype=float)
    y = np.array(y_rows, dtype=float)
    dates = np.array(date_indices, dtype=int)

    return X, y, t_obs, e_obs, dates


def evaluate_split_scheme(
    X: np.ndarray,
    y: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
    scale_training_only: bool,
    global_X_scaled: np.ndarray | None = None,
) -> dict[str, float]:
    """Evaluate Ridge regression across splits and return aggregated metrics."""
    mse_list = []
    r2_list = []
    ic_list = []

    for train_idx, test_idx in splits:
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue

        if scale_training_only:
            X_tr_raw = X[train_idx]
            X_te_raw = X[test_idx]
            mean = np.mean(X_tr_raw, axis=0, keepdims=True)
            std = np.std(X_tr_raw, axis=0, keepdims=True)
            std = np.where(std < 1e-12, 1.0, std)
            X_tr = (X_tr_raw - mean) / std
            X_te = (X_te_raw - mean) / std
        else:
            X_tr = global_X_scaled[train_idx]
            X_te = global_X_scaled[test_idx]

        y_tr = y[train_idx]
        y_te = y[test_idx]

        model = Ridge(alpha=1.0)
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)

        # Metrics
        mse = float(np.mean((preds - y_te) ** 2))
        var_y = float(np.var(y_te))
        r2 = 1.0 - (mse / var_y) if var_y > 1e-12 else 0.0

        # Rank IC (Spearman correlation)
        if len(y_te) > 2 and np.std(preds) > 1e-12 and np.std(y_te) > 1e-12:
            ic = float(stats.spearmanr(preds, y_te).statistic)
        else:
            ic = 0.0

        mse_list.append(mse)
        r2_list.append(r2)
        ic_list.append(ic)

    return {
        "mse": float(np.mean(mse_list)),
        "r2": float(np.mean(r2_list)),
        "rank_ic": float(np.mean(ic_list)),
    }


def run_leakage_study(seeds: list[int] = SEEDS) -> dict:
    """Run data leakage comparison across multiple seeds."""
    schemes = [
        "shuffled_kfold",
        "naive_tss_gap0",
        "tss_gap4_global_scale",
        "purged_walk_forward",
    ]
    raw_by_seed = {scheme: [] for scheme in schemes}

    for seed in seeds:
        X, y, t_obs, e_obs, dates = generate_synthetic_panel(seed=seed, n_assets=20, n_dates=500)
        n_samples = len(y)

        # Global scaled X for leaky schemes
        g_mean = np.mean(X, axis=0, keepdims=True)
        g_std = np.std(X, axis=0, keepdims=True)
        g_std = np.where(g_std < 1e-12, 1.0, g_std)
        X_global = (X - g_mean) / g_std

        # 1. Shuffled K-Fold (5 folds) - LEAKY
        kf = KFold(n_splits=5, shuffle=True, random_state=seed)
        splits_kf = list(kf.split(X))
        res_kf = evaluate_split_scheme(X, y, splits_kf, scale_training_only=False, global_X_scaled=X_global)
        raw_by_seed["shuffled_kfold"].append(res_kf)

        # 2. Naive TimeSeriesSplit (gap=0, global scale) - LEAKY
        tss0 = TimeSeriesSplit(n_splits=5, gap=0)
        splits_tss0 = list(tss0.split(X))
        res_tss0 = evaluate_split_scheme(X, y, splits_tss0, scale_training_only=False, global_X_scaled=X_global)
        raw_by_seed["naive_tss_gap0"].append(res_tss0)

        # 3. TimeSeriesSplit with gap=4, global scale - LEAKY
        tss4 = TimeSeriesSplit(n_splits=5, gap=4)
        splits_tss4 = list(tss4.split(X))
        res_tss4 = evaluate_split_scheme(X, y, splits_tss4, scale_training_only=False, global_X_scaled=X_global)
        raw_by_seed["tss_gap4_global_scale"].append(res_tss4)

        # 4. Purged Walk-Forward (expanding, temporal purge, embargo m=3, train-only scale) - HONEST
        # Group by unique dates so time blocks are contiguous in dates
        unique_dates = np.unique(dates)
        n_dates = len(unique_dates)
        fold_size_dates = n_dates // 6  # 5 test blocks
        splits_pwf = []
        for fold_i in range(1, 6):
            test_date_start = fold_i * fold_size_dates
            test_date_end = min((fold_i + 1) * fold_size_dates, n_dates)
            test_mask = (dates >= test_date_start) & (dates < test_date_end)
            test_idx = np.where(test_mask)[0]

            cand_train_mask = dates < test_date_start
            cand_train_idx = np.where(cand_train_mask)[0]

            # Purge overlapping labels
            purged_tr = purge(cand_train_idx, test_idx, t_obs, e_obs)
            # Embargo (0 for pre-test training, but explicitly check)
            embargoed_tr = embargo(purged_tr, test_idx, t_obs, e_obs, m=3)
            splits_pwf.append((embargoed_tr, test_idx))

        res_pwf = evaluate_split_scheme(X, y, splits_pwf, scale_training_only=True)
        raw_by_seed["purged_walk_forward"].append(res_pwf)

    # Summarize mean and std across seeds
    summary = {}
    for scheme in schemes:
        r2_vals = [r["r2"] for r in raw_by_seed[scheme]]
        mse_vals = [r["mse"] for r in raw_by_seed[scheme]]
        ic_vals = [r["rank_ic"] for r in raw_by_seed[scheme]]
        summary[scheme] = {
            "r2_mean": float(np.mean(r2_vals)),
            "r2_std": float(np.std(r2_vals)),
            "mse_mean": float(np.mean(mse_vals)),
            "mse_std": float(np.std(mse_vals)),
            "rank_ic_mean": float(np.mean(ic_vals)),
            "rank_ic_std": float(np.std(ic_vals)),
            "per_seed": raw_by_seed[scheme],
        }

    return {
        "seeds": seeds,
        "schemes": summary,
        "optimism_bias_r2": float(summary["shuffled_kfold"]["r2_mean"] - summary["purged_walk_forward"]["r2_mean"]),
        "optimism_bias_ic": float(summary["shuffled_kfold"]["rank_ic_mean"] - summary["purged_walk_forward"]["rank_ic_mean"]),
    }


def run_overlap_memorization_study(seeds: list[int] = SEEDS) -> dict:
    """Constructed example where label overlap affects a 1-NN score.

    In this specified synthetic design, persistent asset states let 1-NN match a
    test asset to a recent training observation. Adjacent five-period additive
    labels share four returns, so the unpurged score can reflect shared outcomes.
    The values describe this DGP, model, seeds, and evaluation window; they do not
    establish a monotone relationship between model capacity and leakage
    inflation, nor a universal purged out-of-sample score.
    """
    unp_ic_seeds = []
    pur_ic_seeds = []
    unp_r2_seeds = []
    pur_r2_seeds = []
    per_seed_results = []

    h = 5
    n_dates = 120
    n_assets = 30

    for seed in seeds:
        rng = np.random.RandomState(seed)
        # Persistent state for each asset
        S = np.zeros((n_dates, n_assets))
        for t_step in range(1, n_dates):
            S[t_step] = 0.95 * S[t_step - 1] + rng.normal(0, 0.1, size=n_assets)

        # Unpredictable idiosyncratic daily returns
        r = rng.normal(0, 0.02, size=(n_dates, n_assets))

        # 5-day cumulative forward return label
        y_mat = np.zeros((n_dates - h, n_assets))
        for t_step in range(n_dates - h):
            y_mat[t_step] = np.sum(r[t_step + 1 : t_step + 1 + h], axis=0)

        # Flatten samples
        dates = []
        X_list = []
        y_list = []
        for t_step in range(n_dates - h):
            for i in range(n_assets):
                dates.append(t_step)
                X_list.append([S[t_step, i], float(i)])
                y_list.append(y_mat[t_step, i])

        X = np.array(X_list, dtype=float)
        y = np.array(y_list, dtype=float)
        dates_arr = np.array(dates, dtype=int)

        # Walk-forward evaluation across dates 60 to 100
        unp_ics = []
        pur_ics = []
        unp_r2s = []
        pur_r2s = []

        for t_test in range(60, 100):
            te_mask = dates_arr == t_test
            cand_mask = dates_arr < t_test
            pur_mask = dates_arr < (t_test - (h - 1))

            knn_unp = KNeighborsRegressor(n_neighbors=1)
            knn_unp.fit(X[cand_mask], y[cand_mask])
            p_unp = knn_unp.predict(X[te_mask])

            knn_pur = KNeighborsRegressor(n_neighbors=1)
            knn_pur.fit(X[pur_mask], y[pur_mask])
            p_pur = knn_pur.predict(X[te_mask])

            y_te = y[te_mask]
            var_y = float(np.var(y_te))

            ic_unp = float(stats.spearmanr(p_unp, y_te).statistic)
            ic_pur = float(stats.spearmanr(p_pur, y_te).statistic)
            r2_unp = 1.0 - float(np.mean((p_unp - y_te) ** 2)) / var_y if var_y > 1e-12 else 0.0
            r2_pur = 1.0 - float(np.mean((p_pur - y_te) ** 2)) / var_y if var_y > 1e-12 else 0.0

            unp_ics.append(ic_unp)
            pur_ics.append(ic_pur)
            unp_r2s.append(r2_unp)
            pur_r2s.append(r2_pur)

        seed_res = {
            "seed": seed,
            "unpurged_rank_ic": float(np.nanmean(unp_ics)),
            "purged_rank_ic": float(np.nanmean(pur_ics)),
            "unpurged_r2": float(np.mean(unp_r2s)),
            "purged_r2": float(np.mean(pur_r2s)),
        }
        per_seed_results.append(seed_res)
        unp_ic_seeds.append(seed_res["unpurged_rank_ic"])
        pur_ic_seeds.append(seed_res["purged_rank_ic"])
        unp_r2_seeds.append(seed_res["unpurged_r2"])
        pur_r2_seeds.append(seed_res["purged_r2"])

    return {
        "seeds": seeds,
        "model": "1-Nearest-Neighbor (K=1)",
        "assets": n_assets,
        "eval_dates": 40,
        "unpurged_rank_ic_mean": float(np.mean(unp_ic_seeds)),
        "unpurged_rank_ic_std": float(np.std(unp_ic_seeds)),
        "purged_rank_ic_mean": float(np.mean(pur_ic_seeds)),
        "purged_rank_ic_std": float(np.std(pur_ic_seeds)),
        "rank_ic_inflation": float(np.mean(unp_ic_seeds) - np.mean(pur_ic_seeds)),
        "unpurged_r2_mean": float(np.mean(unp_r2_seeds)),
        "purged_r2_mean": float(np.mean(pur_r2_seeds)),
        "interpretation_scope": (
            "Finite-seed result for this synthetic overlap mechanism and 1-NN model; "
            "not a general capacity effect or a true-score guarantee."
        ),
        "per_seed": per_seed_results,
    }


# ------------------------------------------------------------------ 3. Purged K-Fold vs Walk-Forward
def run_purged_kfold_vs_walkforward(seed: int = 20261031) -> dict:
    """Compare Purged K-Fold (train on past and future contiguous blocks) vs Walk-Forward."""
    X, y, t_obs, e_obs, dates = generate_synthetic_panel(seed=seed, n_assets=20, n_dates=500)
    n_samples = len(y)

    # Purged K-Fold (5 folds on unique dates)
    splits_pkf = purged_kfold_splits(n_samples, n_splits=5, t=t_obs, e=e_obs, embargo_m=3, groups_date=dates)
    res_pkf = evaluate_split_scheme(X, y, splits_pkf, scale_training_only=True)

    # Compute training sample retention percentage
    pkf_retention = [len(tr) / (n_samples - len(te)) for tr, te in splits_pkf]

    # Walk-forward 5 folds
    unique_dates = np.unique(dates)
    n_dates = len(unique_dates)
    fold_size_dates = n_dates // 6
    splits_pwf = []
    pwf_retention = []
    for fold_i in range(1, 6):
        test_mask = (dates >= fold_i * fold_size_dates) & (dates < min((fold_i + 1) * fold_size_dates, n_dates))
        test_idx = np.where(test_mask)[0]
        cand_tr = np.where(dates < fold_i * fold_size_dates)[0]
        purged_tr = purge(cand_tr, test_idx, t_obs, e_obs)
        splits_pwf.append((purged_tr, test_idx))
        pwf_retention.append(len(purged_tr) / len(cand_tr))

    res_pwf = evaluate_split_scheme(X, y, splits_pwf, scale_training_only=True)

    return {
        "seed": seed,
        "purged_kfold": {
            **res_pkf,
            "mean_retention_rate": float(np.mean(pkf_retention)),
        },
        "purged_walk_forward": {
            **res_pwf,
            "mean_retention_rate": float(np.mean(pwf_retention)),
        },
        "interpretation": (
            "Purged K-Fold utilizes both past and future blocks without label leakage, "
            "evaluating parameter stability across regimes; however, it cannot substitute for "
            "time-ordered Walk-Forward in evaluating operational deployment performance."
        ),
    }


# ------------------------------------------------------------------ 4. Nested Hyperparameter Selection
def run_nested_selection_study(seed: int = 20261031) -> dict:
    """Compare overlap-purged nested selection with test-set tuning in a synthetic DGP."""
    X, y, t_obs, e_obs, dates = generate_synthetic_panel(seed=seed, n_assets=20, n_dates=500)
    a_obs = e_obs.copy()  # Synthetic labels are available at their interval end.

    # 3 Outer Walk-Forward splits
    unique_dates = np.unique(dates)
    n_dates = len(unique_dates)
    outer_splits = []
    for fold_i in [2, 3, 4]:
        test_start = fold_i * 80
        test_end = (fold_i + 1) * 80
        test_mask = (dates >= test_start) & (dates < test_end)
        test_idx = np.where(test_mask)[0]
        cand_tr = np.where(dates < test_start)[0]
        prediction_time = np.min(t_obs[test_idx])
        eligible_tr = cand_tr[a_obs[cand_tr] <= prediction_time]
        outer_splits.append((eligible_tr, test_idx))

    param_grid = [{"alpha": a} for a in [0.01, 0.1, 1.0, 10.0, 100.0]]

    def inner_split_fn(out_train_idx, t_arr, e_arr):
        # 2-fold inner time split
        n = len(out_train_idx)
        mid = n // 2
        in_tr = np.arange(0, mid)
        in_val = np.arange(mid, n)
        prediction_time = np.min(t_arr[out_train_idx[in_val]])
        in_tr = in_tr[a_obs[out_train_idx[in_tr]] <= prediction_time]
        return [(in_tr, in_val)]

    def model_factory(p):
        return Ridge(alpha=p["alpha"])

    def scorer(model, X_val, y_val):
        preds = model.predict(X_val)
        return -float(np.mean((preds - y_val) ** 2))  # negative MSE

    nested_res = nested_hyperparameter_evaluation(
        X, y, t_obs, e_obs, outer_splits, inner_split_fn, param_grid, model_factory, scorer, scale_features=True
    )

    # Naive Cheat: select alpha with best test-set score directly
    naive_test_scores = []
    for split in nested_res["outer_splits_used"]:
        out_tr = np.asarray(split["train_idx"], dtype=int)
        out_te = np.asarray(split["test_idx"], dtype=int)
        X_tr = X[out_tr]
        X_te = X[out_te]
        m_tr = np.mean(X_tr, axis=0, keepdims=True)
        s_tr = np.std(X_tr, axis=0, keepdims=True)
        s_tr = np.where(s_tr < 1e-12, 1.0, s_tr)
        X_tr_sc = (X_tr - m_tr) / s_tr
        X_te_sc = (X_te - m_tr) / s_tr

        best_score = -np.inf
        for p in param_grid:
            m = model_factory(p)
            m.fit(X_tr_sc, y[out_tr])
            sc = scorer(m, X_te_sc, y[out_te])
            if sc > best_score:
                best_score = sc
        naive_test_scores.append(best_score)

    return {
        "seed": seed,
        "nested_outer_mse": [-s for s in nested_res["outer_scores"]],
        "mean_nested_outer_mse": float(np.mean([-s for s in nested_res["outer_scores"]])),
        "naive_cheating_mse": [-s for s in naive_test_scores],
        "mean_naive_cheating_mse": float(np.mean([-s for s in naive_test_scores])),
        "best_params_per_fold": nested_res["best_params_per_fold"],
        "outer_splits_used": nested_res["outer_splits_used"],
        "inner_splits_used": nested_res["inner_splits_used"],
        "interpretation_scope": (
            "Synthetic five-day additive-return labels; reported folds are overlap-purged. "
            "These values illustrate this configuration and do not establish a universal effect."
        ),
    }


# ------------------------------------------------------------------ 5. Real Market Example
def run_french_market_study() -> dict:
    """Real market illustration: Kenneth French 10 Industries monthly returns.

    1202 months (1926-07 to 2026-08).
    Overlapping 3-month forward returns: y_{i, t} = prod_{k=1}^3 (1 + R_{i, t+k}) - 1.
    Features: 12-month momentum and 1-month reversal.
    Rolling walk-forward: 120-month train window, 12-month test blocks, step 12 months.
    Compare:
    - Naive walk-forward (no purge: train labels leak 2 months into test).
    - Purged walk-forward (purge overlapping 2 months).
    """
    ind_returns, rf, prov = load_industries_and_rf()
    n_months, n_assets = ind_returns.shape

    # 3-month overlapping label
    h = 3
    valid_months = n_months - h
    y_df = pd.DataFrame(index=ind_returns.index[:valid_months], columns=ind_returns.columns, dtype=float)
    for i_m in range(valid_months):
        sub = ind_returns.iloc[i_m + 1 : i_m + 1 + h]
        y_df.iloc[i_m] = (1.0 + sub).prod(axis=0) - 1.0

    # Features:
    # X0: past 12-month momentum: prod_{k=0}^11 (1 + R_{t-k}) - 1
    # X1: 1-month reversal: R_t
    X0_df = pd.DataFrame(index=ind_returns.index, columns=ind_returns.columns, dtype=float)
    for i_m in range(12, n_months):
        sub = ind_returns.iloc[i_m - 11 : i_m + 1]
        X0_df.iloc[i_m] = (1.0 + sub).prod(axis=0) - 1.0

    X1_df = ind_returns.copy()

    # Align samples from month 12 to valid_months
    start_m = 12
    end_m = valid_months
    dates_idx = np.arange(start_m, end_m)

    X_list = []
    y_list = []
    t_list = []
    month_labels = []

    for m_idx in dates_idx:
        for a_idx, col in enumerate(ind_returns.columns):
            X_list.append([X0_df.iloc[m_idx, a_idx], X1_df.iloc[m_idx, a_idx]])
            y_list.append(y_df.iloc[m_idx, a_idx])
            t_list.append(m_idx)
            month_labels.append(str(ind_returns.index[m_idx]))

    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=float)
    t_obs = np.array(t_list, dtype=float)
    e_obs = t_obs + h

    # Rolling walk-forward: 120-month train, 12-month test, step 12
    train_win_months = 120
    test_win_months = 12
    step_months = 12

    unique_m = np.unique(t_obs)
    n_unique = len(unique_m)

    naive_mse = []
    naive_ic = []
    purged_mse = []
    purged_ic = []

    curr_test_start = train_win_months
    while curr_test_start + test_win_months <= n_unique:
        test_m_vals = unique_m[curr_test_start : curr_test_start + test_win_months]
        train_m_vals = unique_m[curr_test_start - train_win_months : curr_test_start]

        test_idx = np.where(np.isin(t_obs, test_m_vals))[0]
        cand_train_idx = np.where(np.isin(t_obs, train_m_vals))[0]

        # Naive: no purge
        res_naive = evaluate_split_scheme(X, y, [(cand_train_idx, test_idx)], scale_training_only=True)
        naive_mse.append(res_naive["mse"])
        naive_ic.append(res_naive["rank_ic"])

        # Purged: remove training samples whose 3-month label overlaps test
        purged_train_idx = purge(cand_train_idx, test_idx, t_obs, e_obs)
        res_purged = evaluate_split_scheme(X, y, [(purged_train_idx, test_idx)], scale_training_only=True)
        purged_mse.append(res_purged["mse"])
        purged_ic.append(res_purged["rank_ic"])

        curr_test_start += step_months

    return {
        "dataset": prov["source"],
        "sample_period": f"{prov['first_month']} to {prov['last_month']}",
        "total_months": prov["months"],
        "label_horizon_months": h,
        "train_window_months": train_win_months,
        "test_window_months": test_win_months,
        "eval_blocks": len(naive_mse),
        "naive_walk_forward": {
            "mse_mean": float(np.mean(naive_mse)),
            "rank_ic_mean": float(np.mean(naive_ic)),
        },
        "purged_walk_forward": {
            "mse_mean": float(np.mean(purged_mse)),
            "rank_ic_mean": float(np.mean(purged_ic)),
        },
        "interpretation_scope": (
            "Descriptive averages for this revised-history dataset, feature set, model, and windows; "
            "no mean-Rank-IC significance test or inference of absent predictive ability is reported."
        ),
        "provenance": prov,
    }


def plot_hand_example(h_data: dict, ax: plt.Axes | None = None) -> tuple[plt.Figure, plt.Axes]:
    """Plot the Chapter 31 hand example label intervals, purging, and embargo.

    Can be used by CLI to save figures or in Jupyter notebooks with plt.show()
    without writing files to disk.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    else:
        fig = ax.figure

    t_obs = np.array(h_data["observations"])
    h = h_data["horizon_h"]

    # Categories
    purged_set = set(h_data["removed_by_purge"])
    embargo_set = set(h_data["removed_by_embargo"])
    test_set = set(h_data["test_indices"])
    kept_set = set(h_data["final_train_indices"])

    for idx in t_obs:
        t_start = idx
        t_end = idx + h

        if idx in test_set:
            color = "#c0392b"  # Crimson for test
            label = "Test Block" if idx == 6 else ""
            alpha = 0.9
            lw = 3
        elif idx in kept_set:
            color = "#2980b9"  # Blue for kept train
            label = "Kept Training" if idx == 0 else ""
            alpha = 0.9
            lw = 2.5
        elif idx in embargo_set:
            color = "#8e44ad"  # Purple for embargoed
            label = "Embargoed (Look-back m=3)" if idx == 13 else ""
            alpha = 0.8
            lw = 2.0
        elif idx in purged_set:
            color = "#e67e22"  # Orange for purged
            label = "Purged (Overlapping Label)" if idx == 2 else ""
            alpha = 0.8
            lw = 2.0
        else:
            color = "#bdc3c7"
            label = ""
            alpha = 0.5
            lw = 1.5

        # Draw half-open interval (t, t+5]
        ax.plot([t_start, t_end], [idx, idx], color=color, linewidth=lw, alpha=alpha)
        # Open circle at t (left endpoint)
        ax.scatter([t_start], [idx], facecolors="white", edgecolors=color, s=40, zorder=3)
        # Solid circle at t+h (right endpoint)
        ax.scatter([t_end], [idx], facecolors=color, edgecolors=color, s=40, zorder=3)

    # Highlight touching point at t=1 vs t=6
    ax.annotate(
        "Touching point e_1 = t_6 = 6\n(Not overlap; sample 1 kept)",
        xy=(6, 1),
        xytext=(8, 2.5),
        arrowprops=dict(facecolor="#2980b9", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9,
        fontweight="bold",
        color="#1a5276",
        bbox=dict(boxstyle="round,pad=0.3", fc="#ebf5fb", ec="#2980b9", lw=1),
    )

    # Vertical shading for test label span: from min(t_test)=6 to max(e_test)=13
    ax.axvspan(6, 13, color="#c0392b", alpha=0.10, label="Test Label Interval Span (6, 13]")
    # Shading for embargo span: [13, 16)
    ax.axvspan(13, 16, color="#8e44ad", alpha=0.10, label="Embargo Span [13, 16)")

    ax.set_xlabel("Trading Date Index (t)", fontsize=11)
    ax.set_ylabel("Sample Observation Index (i)", fontsize=11)
    ax.set_title("Chapter 31 Pinned Hand Example: 5-Day Forward Label Intervals with Purging & Embargo", fontsize=12)
    ax.set_yticks(t_obs)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", framealpha=0.9, fontsize=9)
    fig.tight_layout()
    return fig, ax


# ------------------------------------------------------------------ 6. Plotting Figures
def generate_figures(results: dict, fig_dir: Path) -> None:
    """Generate the 4 required figures for Chapter 31."""
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: ch31_hand_label_intervals.png
    fig, ax = plot_hand_example(results["hand_example"])
    fig.savefig(fig_dir / "ch31_hand_label_intervals.png")
    plt.close(fig)

    # Figure 2: ch31_leakage_comparison.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    leak_data = results["leakage_experiment"]["schemes"]

    schemes_keys = ["shuffled_kfold", "naive_tss_gap0", "tss_gap4_global_scale", "purged_walk_forward"]
    display_names = [
        "Shuffled K-Fold\n(Leaky)",
        "Naive TSS (gap=0)\n(Leaky)",
        "TSS (gap=4)\n(Global Scale)",
        "Purged Walk-Forward\n(Honest)",
    ]
    colors = ["#e74c3c", "#e67e22", "#f39c12", "#27ae60"]

    r2_means = [leak_data[k]["r2_mean"] for k in schemes_keys]
    r2_stds = [leak_data[k]["r2_std"] for k in schemes_keys]
    ic_means = [leak_data[k]["rank_ic_mean"] for k in schemes_keys]
    ic_stds = [leak_data[k]["rank_ic_std"] for k in schemes_keys]

    ax1.bar(display_names, r2_means, yerr=r2_stds, capsize=5, color=colors, alpha=0.85, edgecolor="black")
    ax1.set_ylabel("Out-of-Sample R²", fontsize=11)
    ax1.set_title("Out-of-Sample R² across Validation Schemes", fontsize=11)
    ax1.grid(True, linestyle=":", alpha=0.5, axis="y")

    ax2.bar(display_names, ic_means, yerr=ic_stds, capsize=5, color=colors, alpha=0.85, edgecolor="black")
    ax2.set_ylabel("Out-of-Sample Rank IC", fontsize=11)
    ax2.set_title("Out-of-Sample Rank IC across Validation Schemes", fontsize=11)
    ax2.grid(True, linestyle=":", alpha=0.5, axis="y")

    fig.suptitle("Data Leakage Study: Inflation of Test Scores in Leaky vs Purged Validation", fontsize=13)
    fig.tight_layout()
    fig.savefig(fig_dir / "ch31_leakage_comparison.png")
    plt.close(fig)

    # Figure 3: ch31_gap_vs_purge_panel.png
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), dpi=300)

    # Subplot 1: Single Asset Series
    ax1.set_title("Single Regular Series: sklearn gap = h - 1 = 4 Exactly Equals Purge", fontsize=11)
    for idx in range(9):
        # 0..5 candidate train, 6..8 test
        if idx in {6, 7, 8}:
            col = "#c0392b"
            lbl = "Test Block" if idx == 6 else None
        elif idx in {0, 1}:
            col = "#27ae60"
            lbl = "Kept Train (gap=4 & purge)" if idx == 0 else None
        else:
            col = "#e67e22"
            lbl = "Excluded (gap=4 & purge)" if idx == 2 else None
        ax1.plot([idx, idx + 5], [idx, idx], color=col, lw=2.5, label=lbl)
        ax1.scatter([idx, idx + 5], [idx, idx], color=col, s=30)
    ax1.set_ylabel("Sample Index", fontsize=10)
    ax1.set_yticks(range(9))
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, linestyle=":", alpha=0.4)

    # Subplot 2: 3-Asset Panel
    ax2.set_title("3-Asset Panel: sklearn gap = 4 Rows Leaves 8 Overlapping Rows in Training!", fontsize=11)
    panel_dates = np.repeat(np.arange(9), 3)
    # Total 27 rows. Test is rows 18..26 (dates 6, 7, 8).
    # Gap=4 excludes rows 14, 15, 16, 17.
    # Rows 0..13 remain. Overlapping remaining: rows 6..13 (dates 2, 3, 4).
    for row in range(27):
        d = panel_dates[row]
        asset_id = row % 3
        y_pos = row
        if row >= 18:
            col = "#c0392b"
            lbl = "Test Block (Dates 6-8, 9 rows)" if row == 18 else None
        elif row in range(6, 14):
            col = "#d35400"  # Leaked overlapping rows
            lbl = "Leaked Overlapping Rows in Train (Dates 2-4, 8 rows)" if row == 6 else None
        elif row in range(14, 18):
            col = "#95a5a6"
            lbl = "Excluded by gap=4 rows (4 rows)" if row == 14 else None
        else:
            col = "#27ae60"
            lbl = "Clean Train (Dates 0-1, 6 rows)" if row == 0 else None
        ax2.plot([d, d + 5], [y_pos, y_pos], color=col, lw=1.8, label=lbl)
        ax2.scatter([d, d + 5], [y_pos, y_pos], color=col, s=15)

    ax2.set_xlabel("Trading Date (t)", fontsize=10)
    ax2.set_ylabel("Panel Row Index (date, asset)", fontsize=10)
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(True, linestyle=":", alpha=0.4)

    fig.tight_layout()
    fig.savefig(fig_dir / "ch31_gap_vs_purge_panel.png")
    plt.close(fig)

    # Figure 4: ch31_french_rolling_validation.png
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), dpi=300)
    f_data = results["french_market_experiment"]

    # This JSON stores block means only, not a rolling path; plot exactly those means.
    naive_m = f_data["naive_walk_forward"]
    purged_m = f_data["purged_walk_forward"]
    labels = ["Naive WF", "Purged WF"]
    colors = ["#c67755", "#397e77"]
    for ax, key, ylabel, digits in (
        (ax1, "rank_ic_mean", "Mean Rank IC", 5),
        (ax2, "mse_mean", "Mean test MSE", 6),
    ):
        values = [naive_m[key], purged_m[key]]
        bars = ax.bar(labels, values, color=colors, width=0.5)
        ax.bar_label(bars, labels=[f"{value:.{digits}f}" for value in values], padding=4)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.margins(y=0.2)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax1.set_title(f"Kenneth French 10 Industries: means across {f_data['eval_blocks']} test blocks", fontsize=11)
    ax2.set_xlabel("Validation method (summary, not a rolling path)", fontsize=11)

    fig.tight_layout()
    fig.savefig(fig_dir / "ch31_french_rolling_validation.png")
    plt.close(fig)


# ------------------------------------------------------------------ Execution & Run
def run(out_dir: Path, fig_dir: Path) -> dict:
    """Run all Chapter 31 experiments and save results and figures."""
    out_file = out_dir / "ch31_results.json"

    # Refuse to overwrite policy
    if out_file.exists():
        raise FileExistsError(f"Refusing to overwrite existing results file: {out_file}")
    for fig_name in FIGURES:
        fig_path = fig_dir / fig_name
        if fig_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing figure: {fig_path}")

    print("Running Chapter 31 Model Validation experiments...")

    print("1. Running Pinned Hand Example...")
    hand_res = run_hand_example()

    print("2. Running Data Leakage Study across 5 seeds...")
    leakage_res = run_leakage_study(SEEDS)

    print("3. Running Overlap Memorization Study (1-NN) across 5 seeds...")
    overlap_mem_res = run_overlap_memorization_study(SEEDS)

    print("4. Running Purged K-Fold vs Walk-Forward Study...")
    pkf_res = run_purged_kfold_vs_walkforward(SEEDS[0])

    print("5. Running Nested Selection Study...")
    nested_res = run_nested_selection_study(SEEDS[0])

    print("6. Running Real Market Illustration on French 10 Industries...")
    french_res = run_french_market_study()

    results = {
        "chapter": 31,
        "title": "Financial Model Validation",
        "hand_example": hand_res,
        "leakage_experiment": leakage_res,
        "overlap_memorization_experiment": overlap_mem_res,
        "purged_kfold_vs_walkforward": pkf_res,
        "nested_selection": nested_res,
        "french_market_experiment": french_res,
    }

    print(f"Generating figures to {fig_dir}...")
    generate_figures(results, fig_dir)

    print(f"Writing results JSON to {out_file}...")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Chapter 31 experiments completed successfully.")
    return results


def main(args_list: list[str] | None = None) -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch31_model_validation_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description="Chapter 31 CLI: Financial Model Validation.")
    review_root = default_run
    parser.add_argument("--out", type=Path, default=review_root / "results", help="Output directory for results JSON")
    parser.add_argument("--figures", type=Path, default=review_root / "figures", help="Output directory for figures")
    args = parser.parse_args(args_list)

    try:
        run(args.out, args.figures)
    except FileExistsError as err:
        raise SystemExit(str(err)) from err


if __name__ == "__main__":
    main()
