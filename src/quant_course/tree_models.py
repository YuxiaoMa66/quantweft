"""Chapter 40-41 tree-based models and non-linear panel ML pipeline (A8-B).

Conventions and time indexing (aligned with A8-A contract v1.1 and ml_pipeline):
- Daily trading calendar index D[0] < D[1] < ... < D[N-1] (sorted, unique).
- Features X are computed up to the close of signal_time = D[k].
- Fills execute at trade_time = label_start = D[k + lag], with lag >= 1.
- Holding period lasts h periods, ending at label_end = D[k + lag + h].
- Return y is simple decimal return: close[label_end] / close[label_start] - 1.
- Label becomes available after close of label_end: label_available_at = label_end.
- Outer and inner training splits respect label_available_at <= fit_time.
- Test rows are strictly out-of-sample; outer test labels are never accessed during
  inner folding, hyperparameter selection, round selection, permutation importance,
  or feature selection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

from quant_course import ml_pipeline as mp

__all__ = [
    "MODELS",
    "TreeFoldResult",
    "make_estimator",
    "fit_select_predict_tree",
    "walk_forward_predict_tree",
    "permutation_importance_by_date",
    "simulate_interaction_panel",
]

MODELS: tuple[str, ...] = ("tree", "rf", "gbm", "pca_ridge")

_GBM_FORBIDDEN_PARAMS: frozenset[str] = frozenset({
    "early_stopping",
    "validation_fraction",
    "n_iter_no_change",
    "scoring",
    "tol",
})


def _check_positive_int(val: object, name: str) -> int:
    """Validate that val is a positive integer, rejecting booleans."""
    if isinstance(val, (bool, np.bool_)) or not isinstance(val, (int, np.integer)) or int(val) < 1:
        raise ValueError(f"{name} must be a positive integer, got {val!r}")
    return int(val)


def _check_nonneg_int(val: object, name: str) -> int:
    """Validate that val is a non-negative integer, rejecting booleans."""
    if isinstance(val, (bool, np.bool_)) or not isinstance(val, (int, np.integer)) or int(val) < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {val!r}")
    return int(val)


def _check_no_inf(arr: np.ndarray, name: str) -> None:
    """Raise ValueError if array contains inf or -inf."""
    if np.isinf(arr).any():
        raise ValueError(f"{name} contains infinite values")


def make_estimator(model: str, params: dict, *, seed: int, n_jobs: int = 1):
    """Instantiate a scikit-learn regressor or pipeline according to model type.

    Parameters
    ----------
    model : str
        One of {"tree", "rf", "gbm", "pca_ridge"}.
    params : dict
        Hyperparameters passed to the estimator.
    seed : int
        Random state seed for reproducibility.
    n_jobs : int, default=1
        Number of parallel jobs for multi-threaded estimators (rf).

    Returns
    -------
    sklearn estimator or Pipeline
        Configured regressor.

    Raises
    ------
    ValueError
        If model is unknown, contains forbidden keys, or parameters are invalid.
    """
    if model not in MODELS:
        raise ValueError(f"Unknown model {model!r}, must be one of {MODELS}")
    if not isinstance(params, dict):
        raise TypeError(f"params must be a dict, got {type(params).__name__}")

    p = params.copy()

    if model == "tree":
        return DecisionTreeRegressor(random_state=seed, **p)

    if model == "rf":
        return RandomForestRegressor(random_state=seed, n_jobs=n_jobs, **p)

    if model == "gbm":
        forbidden_present = set(p.keys()) & _GBM_FORBIDDEN_PARAMS
        if forbidden_present:
            raise ValueError(
                f"Forbidden parameter(s) for gbm: {sorted(forbidden_present)}. "
                "Early stopping is managed via date-grouped inner walk-forward validation."
            )
        return HistGradientBoostingRegressor(early_stopping=False, random_state=seed, **p)

    if model == "pca_ridge":
        if "n_components" not in p or "alpha" not in p:
            raise ValueError("pca_ridge requires 'n_components' and 'alpha' in params")
        k = p.pop("n_components")
        alpha = p.pop("alpha")
        if p:
            raise ValueError(f"Unknown parameter(s) for pca_ridge: {sorted(p.keys())}")
        return Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=k, svd_solver="full")),
            ("model", Ridge(alpha=alpha, random_state=seed)),
        ])

    raise ValueError(f"Unsupported model {model!r}")


@dataclass(frozen=True)
class TreeFoldResult:
    """Out-of-sample prediction and inner tuning results for one walk-forward fold.

    Attributes
    ----------
    fit_time : pd.Timestamp
        Availability cutoff timestamp for training observations.
    model : str
        Model identifier from MODELS.
    seed : int
        Random seed used in fold fitting.
    chosen_params : dict
        Hyperparameters chosen by inner validation (for gbm, contains selected 'max_iter').
    inner_scores : dict[str, float]
        str(params) -> mean inner validation MSE across inner folds.
    inner_curves : dict[str, list[float]]
        For gbm: str(params) -> mean inner validation MSE across rounds 1..max_iter.
        For other models: empty dict {}.
    features : tuple[str, ...]
        Feature column names used in the final fit (after top-k selection if enabled).
    inner_importance : pd.DataFrame | None
        Permutation importance computed on the last inner fold validation set, or None.
    n_train_used : int
        Number of valid training rows used in outer fit.
    n_train_dropped_missing : int
        Number of training rows dropped due to NaN in features or target.
    n_test_unpredictable : int
        Number of test rows where prediction could not be formed due to NaN features.
    predictions : pd.Series
        Out-of-sample predictions indexed by (signal_time, asset).
    """

    fit_time: pd.Timestamp
    model: str
    seed: int
    chosen_params: dict
    inner_scores: dict[str, float]
    inner_curves: dict[str, list[float]]
    features: tuple[str, ...]
    inner_importance: pd.DataFrame | None
    n_train_used: int
    n_train_dropped_missing: int
    n_test_unpredictable: int
    predictions: pd.Series


def fit_select_predict_tree(
    X: pd.DataFrame,
    labels: pd.DataFrame,
    fold: mp.DateFold,
    *,
    model: str,
    param_grid: Sequence[dict] = ({},),
    inner_val_dates: int,
    inner_folds: int = 1,
    inner_min_train_dates: int,
    seed: int = 0,
    n_jobs: int = 1,
    importance_repeats: int = 0,
    importance_groups: dict[str, list[str]] | None = None,
    select_top_k: int | None = None,
) -> TreeFoldResult:
    """Fit a tree-based or baseline model on a walk-forward fold with inner validation.

    Outer test labels are strictly unreferenced during model training, hyperparameter
    selection, round selection, permutation importance, and feature selection.

    Parameters
    ----------
    X : pd.DataFrame
        Panel feature matrix with MultiIndex (signal_time, asset).
    labels : pd.DataFrame
        Label DataFrame with column 'y' and identical MultiIndex to X.
    fold : mp.DateFold
        Walk-forward fold specifying train_rows and test_rows.
    model : str
        Model architecture identifier in MODELS.
    param_grid : Sequence[dict], default=({},)
        Hyperparameter grid evaluated on date-grouped inner folds.
    inner_val_dates : int
        Validation window length in trading dates for inner folds.
    inner_folds : int, default=1
        Number of inner validation folds evaluated (uses the last inner_folds folds).
    inner_min_train_dates : int
        Minimum training window length in trading dates for inner folds.
    seed : int, default=0
        Random state seed.
    n_jobs : int, default=1
        Number of parallel jobs for random forest estimators.
    importance_repeats : int, default=0
        Number of permutation repeats on the last inner fold. If > 0, computes
        inner_importance.
    importance_groups : dict[str, list[str]] | None, default=None
        Group specification for grouped permutation importance.
    select_top_k : int | None, default=None
        If specified, selects top k features by d_mse_mean from inner_importance
        before final refit. Requires importance_repeats > 0 and importance_groups is None.

    Returns
    -------
    TreeFoldResult
        Fold fitting and out-of-sample prediction results.
    """
    if model not in MODELS:
        raise ValueError(f"model must be one of {MODELS}, got {model!r}")
    if not isinstance(X, pd.DataFrame) or not isinstance(labels, pd.DataFrame):
        raise TypeError("X and labels must be pandas DataFrames")
    if not X.index.equals(labels.index):
        raise ValueError("X and labels must have identical MultiIndex and ordering")
    if "y" not in labels.columns:
        raise ValueError("labels must contain column 'y'")

    x_vals = X.to_numpy(dtype=float)
    _check_no_inf(x_vals, "X")
    y_vals = labels["y"].to_numpy(dtype=float)
    _check_no_inf(y_vals, "labels['y']")

    # Outer training rows
    tr_indices = fold.train_rows
    x_tr = X.iloc[tr_indices]
    y_tr = labels["y"].iloc[tr_indices]

    tr_clean_mask = (~x_tr.isna().any(axis=1)) & (~y_tr.isna())
    n_train_dropped = int((~tr_clean_mask).sum())
    n_train_used = int(tr_clean_mask.sum())

    if n_train_used == 0:
        raise ValueError("No valid training observations available in fold")

    x_tr_clean = x_tr[tr_clean_mask]
    y_tr_clean = y_tr[tr_clean_mask]
    labels_tr_clean = labels.iloc[tr_indices][tr_clean_mask]

    # Outer test rows
    te_indices = fold.test_rows
    x_te = X.iloc[te_indices]
    te_predictable_mask = ~x_te.isna().any(axis=1)
    n_test_unpredictable = int((~te_predictable_mask).sum())

    test_pred_series = pd.Series(np.nan, index=x_te.index, dtype=float)

    # Inner walk-forward validation
    i_min_tr = _check_positive_int(inner_min_train_dates, "inner_min_train_dates")
    i_val = _check_positive_int(inner_val_dates, "inner_val_dates")
    i_folds_req = _check_positive_int(inner_folds, "inner_folds")

    inner_all_folds = mp.date_walk_forward(
        signal_time=labels_tr_clean.index.get_level_values(0),
        label_start=labels_tr_clean["label_start"],
        label_end=labels_tr_clean["label_end"],
        label_available_at=labels_tr_clean["label_available_at"],
        min_train_dates=i_min_tr,
        test_dates=i_val,
        step=i_val,
        expanding=True,
    )

    if len(inner_all_folds) < i_folds_req:
        raise ValueError(
            f"Requested {i_folds_req} inner folds, but only {len(inner_all_folds)} available"
        )

    active_inner_folds = inner_all_folds[-i_folds_req:]
    inner_scores: dict[str, float] = {}
    inner_curves: dict[str, list[float]] = {}

    if model == "gbm":
        candidates_info = []
        for p_idx, p_dict in enumerate(param_grid):
            p_key = str(p_dict)
            max_rounds = p_dict.get("max_iter", 100)
            fold_curves: list[list[float]] = []

            for i_fold in active_inner_folds:
                xi_tr = x_tr_clean.iloc[i_fold.train_rows]
                yi_tr = y_tr_clean.iloc[i_fold.train_rows]
                xi_val = x_tr_clean.iloc[i_fold.test_rows]
                yi_val = y_tr_clean.iloc[i_fold.test_rows]

                est_inner = make_estimator(model, p_dict, seed=seed, n_jobs=n_jobs)
                est_inner.fit(xi_tr, yi_tr)
                yi_val_arr = yi_val.to_numpy(dtype=float)

                stage_mses = [
                    float(np.mean((yi_val_arr - pred_m) ** 2))
                    for pred_m in est_inner.staged_predict(xi_val)
                ]
                fold_curves.append(stage_mses)

            mean_curve = [
                float(np.mean([fold_curves[f_i][m_i] for f_i in range(len(active_inner_folds))]))
                for m_i in range(max_rounds)
            ]
            inner_curves[p_key] = mean_curve
            best_round = int(np.argmin(mean_curve)) + 1
            best_mse = mean_curve[best_round - 1]
            inner_scores[p_key] = best_mse
            candidates_info.append((best_mse, p_idx, best_round, p_dict))

        # Select parameter and round: minimal MSE, tie breaks to earlier param then fewer rounds
        chosen_cand = min(candidates_info, key=lambda c: (c[0], c[1]))
        chosen_params = chosen_cand[3].copy()
        chosen_params["max_iter"] = chosen_cand[2]

    else:
        for p_dict in param_grid:
            p_key = str(p_dict)
            fold_mses: list[float] = []

            for i_fold in active_inner_folds:
                xi_tr = x_tr_clean.iloc[i_fold.train_rows]
                yi_tr = y_tr_clean.iloc[i_fold.train_rows]
                xi_val = x_tr_clean.iloc[i_fold.test_rows]
                yi_val = y_tr_clean.iloc[i_fold.test_rows]

                est_inner = make_estimator(model, p_dict, seed=seed, n_jobs=n_jobs)
                est_inner.fit(xi_tr, yi_tr)
                pred_val = est_inner.predict(xi_val)
                fold_mses.append(float(np.mean((yi_val.to_numpy(dtype=float) - pred_val) ** 2)))

            inner_scores[p_key] = float(np.mean(fold_mses))

        chosen_params = min(param_grid, key=lambda p: inner_scores[str(p)]).copy()

    # Inner permutation importance on the last inner fold
    inner_importance: pd.DataFrame | None = None
    if importance_repeats > 0:
        last_inner_fold = active_inner_folds[-1]
        xi_tr = x_tr_clean.iloc[last_inner_fold.train_rows]
        yi_tr = y_tr_clean.iloc[last_inner_fold.train_rows]
        xi_val = x_tr_clean.iloc[last_inner_fold.test_rows]
        yi_val = y_tr_clean.iloc[last_inner_fold.test_rows]

        est_imp = make_estimator(model, chosen_params, seed=seed, n_jobs=n_jobs)
        est_imp.fit(xi_tr, yi_tr)
        inner_importance = permutation_importance_by_date(
            est_imp.predict,
            xi_val,
            yi_val,
            groups=importance_groups,
            n_repeats=importance_repeats,
            seed=seed,
        )

    # Top-k feature selection
    if select_top_k is not None:
        if importance_repeats <= 0:
            raise ValueError("select_top_k requires importance_repeats > 0")
        if importance_groups is not None:
            raise ValueError("select_top_k requires importance_groups is None")
        k = _check_positive_int(select_top_k, "select_top_k")
        if k > len(X.columns):
            raise ValueError(
                f"select_top_k={k} exceeds number of available features {len(X.columns)}"
            )
        assert inner_importance is not None
        sorted_cols = sorted(
            X.columns,
            key=lambda c: inner_importance.loc[c, "d_mse_mean"],
            reverse=True,
        )
        selected_cols = tuple(sorted_cols[:k])
    else:
        selected_cols = tuple(X.columns)

    # Refit final model on all outer training data using selected features
    final_est = make_estimator(model, chosen_params, seed=seed, n_jobs=n_jobs)
    final_est.fit(x_tr_clean[list(selected_cols)], y_tr_clean)

    # Predict test rows
    if te_predictable_mask.any():
        test_preds = final_est.predict(x_te.loc[te_predictable_mask, list(selected_cols)])
        test_pred_series.loc[te_predictable_mask] = test_preds

    return TreeFoldResult(
        fit_time=fold.fit_time,
        model=model,
        seed=seed,
        chosen_params=chosen_params,
        inner_scores=inner_scores,
        inner_curves=inner_curves,
        features=selected_cols,
        inner_importance=inner_importance,
        n_train_used=n_train_used,
        n_train_dropped_missing=n_train_dropped,
        n_test_unpredictable=n_test_unpredictable,
        predictions=test_pred_series,
    )


def walk_forward_predict_tree(
    X: pd.DataFrame,
    labels: pd.DataFrame,
    folds: list[mp.DateFold],
    **kwargs,
) -> tuple[pd.Series, list[TreeFoldResult]]:
    """Execute walk-forward prediction across a sequence of folds using tree models.

    Parameters
    ----------
    X : pd.DataFrame
        Panel feature matrix.
    labels : pd.DataFrame
        Label DataFrame.
    folds : list[mp.DateFold]
        Sequence of walk-forward folds.
    **kwargs
        Keyword arguments forwarded to fit_select_predict_tree.

    Returns
    -------
    tuple[pd.Series, list[TreeFoldResult]]
        Concatenated out-of-sample predictions and fold result objects.

    Raises
    ------
    ValueError
        If concatenated predictions contain duplicate indices across test folds.
    """
    fold_results: list[TreeFoldResult] = []
    for f in folds:
        res = fit_select_predict_tree(X, labels, f, **kwargs)
        fold_results.append(res)

    if not fold_results:
        return pd.Series(dtype=float, index=X.index[:0]), []

    all_preds = pd.concat([res.predictions for res in fold_results])
    if not all_preds.index.is_unique:
        raise ValueError("Concatenated predictions have duplicate indices across test folds")

    return all_preds, fold_results


def _compute_daily_spearman_ic(
    y_series: pd.Series,
    pred_series: pd.Series,
    unique_dates: Sequence[pd.Timestamp],
) -> float:
    """Compute mean cross-sectional Spearman IC across dates with >= 3 non-constant assets."""
    daily_ics: list[float] = []
    for d in unique_dates:
        yd = y_series.loc[d].to_numpy(dtype=float)
        pd_val = pred_series.loc[d].to_numpy(dtype=float)
        if len(yd) >= 3 and np.ptp(pd_val) > 0.0 and np.ptp(yd) > 0.0:
            ry = rankdata(yd)
            rp = rankdata(pd_val)
            corr = float(np.corrcoef(rp, ry)[0, 1])
            if np.isfinite(corr):
                daily_ics.append(corr)

    if daily_ics:
        return float(np.mean(daily_ics))
    return float("nan")


def permutation_importance_by_date(
    predict: Callable[[pd.DataFrame], np.ndarray | Sequence[float]],
    X: pd.DataFrame,
    y: pd.Series,
    *,
    groups: dict[str, list[str]] | None = None,
    n_repeats: int = 5,
    seed: int = 0,
) -> pd.DataFrame:
    """Compute cross-sectional feature or group permutation importance by date.

    Permutations are executed strictly within the same signal_time date, shuffling
    assets cross-sectionally without mixing dates. For grouped permutations, columns
    within the same group share identical row permutations, preserving intra-group
    joint structure.

    Parameters
    ----------
    predict : Callable[[pd.DataFrame], np.ndarray | Sequence[float]]
        Model predict function accepting a DataFrame of features matching X.
    X : pd.DataFrame
        Panel feature DataFrame with MultiIndex (signal_time, asset).
    y : pd.Series
        Target series with identical index to X.
    groups : dict[str, list[str]] | None, default=None
        Mapping of group name to list of feature column names. If None, each column
        is treated as its own group.
    n_repeats : int, default=5
        Number of shuffle repeats per group.
    seed : int, default=0
        Random state seed.

    Returns
    -------
    pd.DataFrame
        Summary table with index as group names and columns:
        [base_mse, d_mse_mean, d_mse_std, base_ic, d_ic_mean, d_ic_std, n_rows, n_dates].
    """
    if not callable(predict):
        raise TypeError("predict must be callable")
    if not isinstance(X, pd.DataFrame) or not isinstance(y, pd.Series):
        raise TypeError("X must be a pandas DataFrame and y must be a pandas Series")
    if not X.index.equals(y.index):
        raise ValueError("X and y must have identical index")

    x_vals = X.to_numpy(dtype=float)
    _check_no_inf(x_vals, "X")
    y_vals = y.to_numpy(dtype=float)
    _check_no_inf(y_vals, "y")

    if np.isnan(x_vals).any():
        raise ValueError("X contains NaN")
    if np.isnan(y_vals).any():
        raise ValueError("y contains NaN")

    n_reps = _check_positive_int(n_repeats, "n_repeats")

    if groups is None:
        group_dict = {col: [col] for col in X.columns}
    else:
        if not isinstance(groups, dict):
            raise TypeError("groups must be a dict")
        group_dict = groups
        for g_name, g_cols in group_dict.items():
            for c in g_cols:
                if c not in X.columns:
                    raise ValueError(f"Feature {c!r} in group {g_name!r} not in X columns")

    dates = X.index.get_level_values(0).unique()
    n_dates = len(dates)
    n_rows = len(X)

    # Base performance metrics
    base_pred = np.asarray(predict(X), dtype=float)
    if base_pred.shape != (n_rows,):
        raise ValueError(f"predict returned shape {base_pred.shape}, expected {(n_rows,)}")

    base_mse = float(np.mean((y_vals - base_pred) ** 2))
    base_pred_s = pd.Series(base_pred, index=X.index)
    base_ic = _compute_daily_spearman_ic(y, base_pred_s, dates)

    # Pre-calculate row positions for each date
    signal_times = X.index.get_level_values(0).to_numpy()
    date_row_indices = {d: np.where(signal_times == d)[0] for d in dates}

    rng = np.random.default_rng(seed)
    results_rows: list[dict[str, float]] = []

    for g_name, g_cols in group_dict.items():
        col_indices = [X.columns.get_loc(c) for c in g_cols]
        d_mse_list: list[float] = []
        d_ic_list: list[float] = []

        for _ in range(n_reps):
            X_perm_vals = x_vals.copy()

            for d in dates:
                rows_d = date_row_indices[d]
                if len(rows_d) > 1:
                    p = rng.permutation(len(rows_d))
                    shuffled_rows = rows_d[p]
                    X_perm_vals[rows_d[:, None], col_indices] = x_vals[shuffled_rows[:, None], col_indices]
                elif len(rows_d) == 1:
                    # Single observation has only trivial permutation
                    _ = rng.permutation(1)

            X_perm = pd.DataFrame(X_perm_vals, index=X.index, columns=X.columns)
            perm_pred = np.asarray(predict(X_perm), dtype=float)
            mse_perm = float(np.mean((y_vals - perm_pred) ** 2))
            perm_pred_s = pd.Series(perm_pred, index=X.index)
            ic_perm = _compute_daily_spearman_ic(y, perm_pred_s, dates)

            d_mse = mse_perm - base_mse
            d_mse_list.append(d_mse)

            if np.isfinite(base_ic) and np.isfinite(ic_perm):
                d_ic = base_ic - ic_perm
            else:
                d_ic = float("nan")
            d_ic_list.append(d_ic)

        d_mse_mean = float(np.mean(d_mse_list))
        d_mse_std = float(np.std(d_mse_list, ddof=1)) if n_reps > 1 else float("nan")

        finite_d_ic = [v for v in d_ic_list if np.isfinite(v)]
        if finite_d_ic:
            d_ic_mean = float(np.mean(finite_d_ic))
            d_ic_std = float(np.std(finite_d_ic, ddof=1)) if len(finite_d_ic) > 1 else float("nan")
        else:
            d_ic_mean = float("nan")
            d_ic_std = float("nan")

        results_rows.append({
            "base_mse": base_mse,
            "d_mse_mean": d_mse_mean,
            "d_mse_std": d_mse_std,
            "base_ic": base_ic,
            "d_ic_mean": d_ic_mean,
            "d_ic_std": d_ic_std,
            "n_rows": float(n_rows),
            "n_dates": float(n_dates),
        })

    out_df = pd.DataFrame(results_rows, index=list(group_dict.keys()))
    return out_df


def simulate_interaction_panel(
    *,
    n_assets: int = 40,
    n_days: int = 1260,
    n_noise: int = 20,
    signal_loading: float = 4e-4,
    char_rho: float = 0.98,
    idio_vol: float = 0.02,
    market_vol: float = 0.01,
    start: str = "2015-01-02",
    seed: int = 0,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Simulate a constructed daily panel with non-linear interaction signal (Chapter 40).

    Condition mean of simple return:
        r[i, t+1] = beta_i * m[t+1] + signal_loading * g(q[:, t]) + e[i, t+1]
        g = q_1 * 1{q_2 > 0} + 0.8 * (|q_3| - sqrt(2/pi))

    Parameters
    ----------
    n_assets : int, default=40
        Number of cross-sectional assets.
    n_days : int, default=1260
        Number of business days simulated.
    n_noise : int, default=20
        Number of pure noise AR(1) characteristics with zero signal loading.
    signal_loading : float, default=4e-4
        Strength of non-linear alpha component.
    char_rho : float, default=0.98
        Autoregressive coefficient for characteristics.
    idio_vol : float, default=0.02
        Standard deviation of idiosyncratic shock e.
    market_vol : float, default=0.01
        Standard deviation of market shock m.
    start : str, default="2015-01-02"
        Start business day date string.
    seed : int, default=0
        Random seed.

    Returns
    -------
    tuple[pd.DataFrame, dict[str, pd.DataFrame]]
        (close_prices, characteristics_dict), where close starts at 100 on day 0
        and characteristics has keys q_1, q_2, q_3, noise_01..
    """
    _check_positive_int(n_assets, "n_assets")
    _check_positive_int(n_days, "n_days")
    _check_nonneg_int(n_noise, "n_noise")
    if not (0 <= char_rho < 1) or idio_vol <= 0 or market_vol < 0 or not np.isfinite(signal_loading):
        raise ValueError("need 0 <= char_rho < 1, idio_vol > 0, market_vol >= 0, finite signal_loading")

    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n_days)
    assets = [f"A{i:02d}" for i in range(n_assets)]

    def ar1(k: int) -> np.ndarray:
        if k == 0:
            return np.empty((0, n_days, n_assets))
        x = np.empty((k, n_days, n_assets))
        x[:, 0] = rng.normal(size=(k, n_assets))
        shock = rng.normal(scale=np.sqrt(1 - char_rho ** 2), size=(k, n_days, n_assets))
        for t in range(1, n_days):
            x[:, t] = char_rho * x[:, t - 1] + shock[:, t]
        return x

    q = ar1(3)
    noise = ar1(n_noise)
    beta = rng.uniform(0.8, 1.2, n_assets)
    m = rng.normal(0.0, market_vol, n_days)
    e = rng.normal(0.0, idio_vol, (n_days, n_assets))

    # g = q_1 * 1{q_2 > 0} + 0.8 * (|q_3| - sqrt(2/pi))
    q1 = q[0]
    q2 = q[1]
    q3 = q[2]
    g = q1 * (q2 > 0.0).astype(float) + 0.8 * (np.abs(q3) - np.sqrt(2.0 / np.pi))

    alpha = np.zeros((n_days, n_assets))
    alpha[1:] = signal_loading * g[:-1]

    ret = beta[None, :] * m[:, None] + alpha + e
    ret[0] = 0.0
    if (ret <= -1.0).any():
        raise ValueError("simulated simple return <= -100%; lower the volatilities")

    close = pd.DataFrame(100.0 * np.cumprod(1.0 + ret, axis=0), index=dates, columns=assets)
    chars = {f"q_{j + 1}": pd.DataFrame(q[j], index=dates, columns=assets) for j in range(3)}
    chars.update({
        f"noise_{k + 1:02d}": pd.DataFrame(noise[k], index=dates, columns=assets)
        for k in range(n_noise)
    })

    return close, chars
