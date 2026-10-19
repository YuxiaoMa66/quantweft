"""Chapter 38-39 / Project 6 panel ML pipeline (A8-A; contract qa/a8/ch37_ch39_batch/INTERFACE_CONTRACT.md).

Draft by the AMC implementer job implementer-1791633884-17b7062f; integrated and revised by the host
(availability boundary, flat-portfolio Sharpe, constructed panel simulator, feature stacking).

This module implements the A8-A interface contract (v1) for panel ML workflows:
- Forward label construction with explicit execution lag and prediction horizon.
- Date-based chronological walk-forward splitting with strict label-availability purging.
- Sklearn pipeline fitting, nested hyperparameter selection, and out-of-sample prediction.
- Dollar-neutral gross-constrained target weight formation.
- Point-in-time prediction evaluation (MSE, out-of-sample R^2, Spearman IC with Newey-West variance).
- Portfolio backtest ledger attribution and performance metrics.

Time Conventions:
- Daily trading calendar index D[0] < D[1] < ... < D[N-1] (sorted, unique).
- Each date D[k] represents the close of that trading day.
- Features X are computed up to the close of signal_time = D[k].
- Fills execute at trade_time = label_start = D[k + lag], with lag >= 1.
- Holding period lasts h periods, ending at label_end = D[k + lag + h].
- Return y is simple decimal return: close[label_end] / close[label_start] - 1.
- Label becomes available after close of label_end: label_available_at = label_end.
- A training row is usable at fit_time (= test_dates[0], the close at which the first test prediction is
  formed) only if label_available_at <= fit_time. Features and labels observed at the same close are treated
  as equally available, so signal date D[k] is usable iff k + lag + h <= s and the last lag + h - 1 signal
  dates before the test block are excluded. A stricter house rule (label_available_at < fit_time) would
  exclude one more date; it is not leakage either way.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from quant_course.factor_research import ic_series, ic_summary
from quant_course.performance import annualized_volatility, drawdown_path, sharpe_ratio
from quant_course.validation import intervals_overlap

__all__ = [
    "DateFold",
    "FoldResult",
    "make_forward_labels",
    "date_walk_forward",
    "fit_select_predict",
    "walk_forward_predict",
    "predictions_to_target_weights",
    "prediction_metrics",
    "portfolio_metrics",
    "simulate_return_panel",
    "price_features",
    "stack_features",
    "backtest_predictions",
]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _check_positive_int(val: object, name: str) -> int:
    """Validate that val is a positive integer, rejecting booleans."""
    if isinstance(val, (bool, np.bool_)) or not isinstance(val, (int, np.integer)) or int(val) < 1:
        raise ValueError(f"{name} must be a positive integer, got {val!r}")
    return int(val)


def _check_no_inf(arr: np.ndarray, name: str) -> None:
    """Raise ValueError if array contains inf or -inf."""
    if np.isinf(arr).any():
        raise ValueError(f"{name} contains infinite values")


# ---------------------------------------------------------------------------
# Forward labels
# ---------------------------------------------------------------------------

def make_forward_labels(
    close: pd.DataFrame,
    horizon: int,
    execution_lag: int = 1,
) -> pd.DataFrame:
    """Compute point-in-time forward return labels from a close price panel.

    Parameters
    ----------
    close : pd.DataFrame
        Date x asset panel of close prices. Row index must be strictly monotonic
        increasing and unique. Values must be strictly positive and finite or NaN.
    horizon : int
        Holding horizon in trading days (h >= 1). Simple return over (k+lag, k+lag+h].
    execution_lag : int, default=1
        Execution delay from signal close to fill close (lag >= 1).

    Returns
    -------
    pd.DataFrame
        Long format with MultiIndex (signal_time, asset), sorted lexicographically.
        Columns:
        - trade_time: Timestamp of execution (D[k+lag]) or NaT.
        - label_start: Timestamp of label interval start (= trade_time).
        - label_end: Timestamp of label interval end (D[k+lag+h]) or NaT.
        - label_available_at: Timestamp when label is known (= label_end) or NaT.
        - y: Simple decimal return (close[label_end] / close[label_start] - 1) or NaN.
    """
    if not isinstance(close, pd.DataFrame):
        raise TypeError("close must be a pandas DataFrame")
    if close.empty:
        raise ValueError("close must not be empty")
    if not close.index.is_unique or not close.index.is_monotonic_increasing:
        raise ValueError("close index must be unique and strictly increasing")
    if not close.columns.is_unique:
        raise ValueError("close columns must be unique")

    h = _check_positive_int(horizon, "horizon")
    lag = _check_positive_int(execution_lag, "execution_lag")

    for col in close.columns:
        if close[col].dtype.kind not in "iuf":
            raise TypeError(f"close[{col!r}] must be numeric, got {close[col].dtype}")

    vals = close.to_numpy(dtype=float)
    _check_no_inf(vals, "close")
    if (vals <= 0).any():
        raise ValueError("close prices must be strictly positive")

    n_dates = len(close.index)
    dates = pd.DatetimeIndex(close.index)
    assets = list(close.columns)

    trade_times = [dates[k + lag] if k + lag < n_dates else pd.NaT for k in range(n_dates)]
    trade_time_map = pd.Series(trade_times, index=dates, dtype="datetime64[ns]")

    label_ends = [dates[k + lag + h] if k + lag + h < n_dates else pd.NaT for k in range(n_dates)]
    label_end_map = pd.Series(label_ends, index=dates, dtype="datetime64[ns]")

    start_prices = close.shift(-lag)
    end_prices = close.shift(-(lag + h))
    y_wide = end_prices / start_prices - 1.0

    idx = pd.MultiIndex.from_product([dates, assets], names=["signal_time", "asset"])
    df = pd.DataFrame(index=idx).sort_index()

    signal_dates = df.index.get_level_values(0)
    df["trade_time"] = signal_dates.map(trade_time_map)
    df["label_start"] = df["trade_time"]
    df["label_end"] = signal_dates.map(label_end_map)
    df["label_available_at"] = df["label_end"]

    y_series = y_wide.unstack().swaplevel(0, 1)
    y_series.index.names = ["signal_time", "asset"]
    df["y"] = y_series.reindex(df.index)

    return df


# ---------------------------------------------------------------------------
# Walk-forward fold structure & splitting
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DateFold:
    """Chronological walk-forward fold specification.

    Attributes
    ----------
    fit_time : pd.Timestamp
        Signal time of the first date in the test block (test_dates[0]).
    train_dates : tuple[pd.Timestamp, ...]
        Sorted tuple of unique dates belonging to the candidate training block.
    test_dates : tuple[pd.Timestamp, ...]
        Sorted tuple of unique dates belonging to the test evaluation block.
    train_rows : np.ndarray
        Positional indices (ascending) of usable training samples whose label is
        available at the fit close (label_available_at <= fit_time).
    test_rows : np.ndarray
        Positional indices (ascending) of all test samples.
    n_excluded_unavailable : int
        Number of samples falling in train_dates whose label_available_at > fit_time
        or is NaT (label not yet known when the model is fitted).
    """
    fit_time: pd.Timestamp
    train_dates: tuple[pd.Timestamp, ...]
    test_dates: tuple[pd.Timestamp, ...]
    train_rows: np.ndarray
    test_rows: np.ndarray
    n_excluded_unavailable: int


def _check_label_times(signal: pd.Series, start: pd.Series, end: pd.Series, avail: pd.Series) -> None:
    """Enforce the label-time contract documented in ``date_walk_forward`` (raises ValueError)."""
    sig, st, en, av = (pd.DatetimeIndex(x) for x in (signal, start, end, avail))
    if sig.hasnans:
        raise ValueError("signal_time must not contain NaT")
    has_s, has_e, has_a = ~st.isna(), ~en.isna(), ~av.isna()
    problems = {
        "label_end without label_available_at": has_e & ~has_a,
        "label_available_at without label_end": has_a & ~has_e,
        "label_end without label_start": has_e & ~has_s,
        "label_start not after signal_time": has_s & ~(st > sig),
        "label_end not after label_start": has_e & has_s & ~(en > st),
        "label_available_at earlier than label_end": has_e & has_a & (av < en),
    }
    for message, mask in problems.items():
        bad = np.flatnonzero(np.asarray(mask))
        if bad.size:
            raise ValueError(f"invalid label times ({message}) at row positions {bad[:5].tolist()}")


def date_walk_forward(
    signal_time: Sequence | np.ndarray | pd.Series,
    label_start: Sequence | np.ndarray | pd.Series,
    label_end: Sequence | np.ndarray | pd.Series,
    label_available_at: Sequence | np.ndarray | pd.Series,
    *,
    min_train_dates: int,
    test_dates: int,
    step: int | None = None,
    expanding: bool = True,
    max_train_dates: int | None = None,
) -> list[DateFold]:
    """Generate chronological walk-forward folds grouped by unique dates.

    All rows for any single date are strictly placed on the same side of the split.
    Training rows whose label is not yet known at the fit close (label_available_at > fit_time or NaT)
    are excluded; the count follows from each row's actual label interval, not from a fixed gap.

    Label-time contract, validated per row on entry (``ValueError`` otherwise; inputs are never altered):

    * complete label: ``signal_time < label_start < label_end <= label_available_at``. Availability may lag
      the label end (delayed data); it may never precede it, because a label cannot be known before its
      return interval has ended.
    * unfinished label (e.g. the sample tail): ``label_end`` and ``label_available_at`` are both NaT;
      ``label_start`` may be NaT or a valid trade time after ``signal_time``. Such rows are never trainable.
    * any other missing-value combination (end without availability, availability without end, end without
      start) is rejected.

    Parameters
    ----------
    signal_time, label_start, label_end, label_available_at : array-like
        Equal-length 1D arrays or Series. signal_time must be non-decreasing.
    min_train_dates : int
        Minimum number of distinct dates in the training window (>= 1).
    test_dates : int
        Number of distinct dates in each test block (>= 1).
    step : int, optional
        Step size by which the test block advances (default: test_dates).
    expanding : bool, default=True
        If True, training window expands from the first date to fit_time.
        If False, training window rolls with fixed date length.
    max_train_dates : int, optional
        Maximum training dates in rolling or capped expanding mode.

    Returns
    -------
    list[DateFold]
        List of generated walk-forward folds.
    """
    s_time = pd.Series(signal_time)
    l_start = pd.Series(label_start)
    l_end = pd.Series(label_end)
    l_avail = pd.Series(label_available_at)

    n_samples = len(s_time)
    if not (n_samples == len(l_start) == len(l_end) == len(l_avail)):
        raise ValueError("signal_time, label_start, label_end, and label_available_at must have equal length")
    if n_samples == 0:
        raise ValueError("inputs must not be empty")

    s_time_dt = pd.to_datetime(s_time)
    if not s_time_dt.is_monotonic_increasing:
        raise ValueError("signal_time must be non-decreasing")

    min_tr = _check_positive_int(min_train_dates, "min_train_dates")
    te_dates = _check_positive_int(test_dates, "test_dates")
    step_size = te_dates if step is None else _check_positive_int(step, "step")

    if not isinstance(expanding, (bool, np.bool_)):
        raise TypeError("expanding must be a boolean")
    expanding_bool = bool(expanding)

    if max_train_dates is not None:
        max_tr = _check_positive_int(max_train_dates, "max_train_dates")
        if max_tr < min_tr:
            raise ValueError(f"max_train_dates ({max_tr}) cannot be less than min_train_dates ({min_tr})")
    else:
        max_tr = None

    unique_dates = pd.DatetimeIndex(s_time_dt.unique())
    n_unique = len(unique_dates)

    if min_tr + te_dates > n_unique:
        raise ValueError(f"min_train_dates ({min_tr}) + test_dates ({te_dates}) > unique dates ({n_unique})")

    l_start_dt = pd.to_datetime(l_start)
    l_end_dt = pd.to_datetime(l_end)
    l_avail_dt = pd.to_datetime(l_avail)
    _check_label_times(s_time_dt, l_start_dt, l_end_dt, l_avail_dt)

    folds: list[DateFold] = []
    s = min_tr

    while s + te_dates <= n_unique:
        test_u = unique_dates[s : s + te_dates]
        if expanding_bool:
            if max_tr is not None:
                train_u = unique_dates[max(0, s - max_tr) : s]
            else:
                train_u = unique_dates[:s]
        else:
            win = max_tr if max_tr is not None else min_tr
            train_u = unique_dates[max(0, s - win) : s]

        fit_time = pd.Timestamp(test_u[0])
        train_dates_tuple = tuple(pd.Timestamp(d) for d in train_u)
        test_dates_tuple = tuple(pd.Timestamp(d) for d in test_u)

        in_train_dates = s_time_dt.isin(train_u).to_numpy()
        in_test_dates = s_time_dt.isin(test_u).to_numpy()

        # Usable training row: label known at the fit close (NaT means never known in sample).
        usable_label = (l_avail_dt <= fit_time).to_numpy() & l_avail_dt.notna().to_numpy()

        train_mask = in_train_dates & usable_label
        excluded_mask = in_train_dates & ~usable_label

        train_rows = np.flatnonzero(train_mask)
        test_rows = np.flatnonzero(in_test_dates)
        n_excluded = int(excluded_mask.sum())

        # Defensive assertion: No training interval (label_start, label_end] can overlap
        # any test interval (label_start, label_end].
        if len(train_rows) > 0 and len(test_rows) > 0:
            test_valid = (l_start_dt.iloc[test_rows].notna().to_numpy() &
                          l_end_dt.iloc[test_rows].notna().to_numpy())
            if test_valid.any():
                t_tr = l_start_dt.iloc[train_rows].to_numpy(dtype="datetime64[ns]").astype(np.int64)
                e_tr = l_end_dt.iloc[train_rows].to_numpy(dtype="datetime64[ns]").astype(np.int64)

                test_valid_rows = test_rows[test_valid]
                t_te = l_start_dt.iloc[test_valid_rows].to_numpy(dtype="datetime64[ns]").astype(np.int64)
                e_te = l_end_dt.iloc[test_valid_rows].to_numpy(dtype="datetime64[ns]").astype(np.int64)

                # Overlap between (t_tr, e_tr] and (t_te, e_te]. Panel rows of one date share an interval, so test
                # unique intervals only (a row-by-row broadcast is ~N_train x N_test and reached GB scale).
                tr_u = np.unique(np.column_stack([t_tr, e_tr]), axis=0)
                te_u = np.unique(np.column_stack([t_te, e_te]), axis=0)
                overlap = intervals_overlap(tr_u[:, :1], tr_u[:, 1:], te_u[:, 0][None, :], te_u[:, 1][None, :])
                if np.any(overlap):
                    raise RuntimeError("Defensive check failed: training label interval overlaps test label interval")

        fold = DateFold(
            fit_time=fit_time,
            train_dates=train_dates_tuple,
            test_dates=test_dates_tuple,
            train_rows=train_rows,
            test_rows=test_rows,
            n_excluded_unavailable=n_excluded,
        )
        folds.append(fold)
        s += step_size

    return folds


# ---------------------------------------------------------------------------
# Model fitting, tuning, prediction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FoldResult:
    """Out-of-sample evaluation result for a single walk-forward fold.

    Attributes
    ----------
    fit_time : pd.Timestamp
        Signal time of the start of the evaluation block.
    model : str
        Model identifier.
    chosen_params : dict
        Hyperparameters selected by inner validation.
    inner_scores : dict[str, float]
        str(params) -> average inner validation MSE.
    n_train_used : int
        Number of outer training rows used for final fitting after missing-data drops.
    n_train_dropped_missing : int
        Number of outer training rows dropped due to NaN in features or label.
    n_test_unpredictable : int
        Number of test rows where prediction is NaN due to missing feature(s).
    predictions : pd.Series
        Out-of-sample predictions indexed by test MultiIndex (signal_time, asset).
    """
    fit_time: pd.Timestamp
    model: str
    chosen_params: dict
    inner_scores: dict[str, float]
    n_train_used: int
    n_train_dropped_missing: int
    n_test_unpredictable: int
    predictions: pd.Series


def _build_model_pipeline(model: str, params: dict) -> Pipeline:
    """Build StandardScaler + linear estimator pipeline."""
    if model == "ols":
        est = LinearRegression(**params)
    elif model == "ridge":
        est = Ridge(**params)
    elif model == "lasso":
        p = {"max_iter": 100_000, **params}
        est = Lasso(**p)
    elif model == "elasticnet":
        p = {"max_iter": 100_000, **params}
        est = ElasticNet(**p)
    else:
        raise ValueError(f"Unknown model for pipeline: {model}")
    return Pipeline([("scaler", StandardScaler()), ("model", est)])


def fit_select_predict(
    X: pd.DataFrame,
    labels: pd.DataFrame,
    fold: DateFold,
    *,
    model: str,
    param_grid: Sequence[dict] = ({},),
    inner_val_dates: int,
    inner_folds: int = 1,
    inner_min_train_dates: int,
) -> FoldResult:
    """Fit a model on a walk-forward fold with nested parameter tuning and predict test rows.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix indexed by MultiIndex (signal_time, asset).
    labels : pd.DataFrame
        Label table with column 'y' and identical MultiIndex to X.
    fold : DateFold
        Walk-forward split specifying train_rows and test_rows.
    model : str
        One of {"zero", "train_mean", "ols", "ridge", "lasso", "elasticnet"}.
    param_grid : Sequence[dict], default=({},)
        Hyperparameter combinations to search over inner validation.
    inner_val_dates : int
        Validation date window size for inner walk-forward folds.
    inner_folds : int, default=1
        Number of inner validation folds to evaluate (takes the last inner_folds).
    inner_min_train_dates : int
        Minimum training dates for inner walk-forward folds.

    Returns
    -------
    FoldResult
        Fold fitting and out-of-sample prediction results.
    """
    valid_models = {"zero", "train_mean", "ols", "ridge", "lasso", "elasticnet"}
    if model not in valid_models:
        raise ValueError(f"model must be one of {valid_models}, got {model!r}")

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

    # Drop training rows with missing feature or missing target
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

    if model in ("zero", "train_mean"):
        chosen_params: dict = {}
        inner_scores: dict[str, float] = {}
        if te_predictable_mask.any():
            if model == "zero":
                test_pred_series.loc[te_predictable_mask] = 0.0
            else:
                mean_val = float(y_tr_clean.mean())
                test_pred_series.loc[te_predictable_mask] = mean_val
    else:
        # Inner walk-forward parameter tuning
        i_min_tr = _check_positive_int(inner_min_train_dates, "inner_min_train_dates")
        i_val = _check_positive_int(inner_val_dates, "inner_val_dates")
        i_folds_req = _check_positive_int(inner_folds, "inner_folds")

        inner_all_folds = date_walk_forward(
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
        inner_scores = {}

        for p_dict in param_grid:
            p_key = str(p_dict)
            fold_mses: list[float] = []
            for i_fold in active_inner_folds:
                xi_tr = x_tr_clean.iloc[i_fold.train_rows]
                yi_tr = y_tr_clean.iloc[i_fold.train_rows]
                xi_val = x_tr_clean.iloc[i_fold.test_rows]
                yi_val = y_tr_clean.iloc[i_fold.test_rows]

                pipe_inner = _build_model_pipeline(model, p_dict)
                pipe_inner.fit(xi_tr, yi_tr)
                pred_val = pipe_inner.predict(xi_val)
                fold_mses.append(float(np.mean((yi_val.to_numpy(dtype=float) - pred_val) ** 2)))

            inner_scores[p_key] = float(np.mean(fold_mses))

        # Select parameter with minimal average inner MSE (ties preserve earlier candidate)
        chosen_params = min(param_grid, key=lambda p: inner_scores[str(p)])

        # Refit on all clean outer training samples
        final_pipe = _build_model_pipeline(model, chosen_params)
        final_pipe.fit(x_tr_clean, y_tr_clean)

        # Predict predictable test rows
        if te_predictable_mask.any():
            test_preds = final_pipe.predict(x_te[te_predictable_mask])
            test_pred_series.loc[te_predictable_mask] = test_preds

    return FoldResult(
        fit_time=fold.fit_time,
        model=model,
        chosen_params=chosen_params,
        inner_scores=inner_scores,
        n_train_used=n_train_used,
        n_train_dropped_missing=n_train_dropped,
        n_test_unpredictable=n_test_unpredictable,
        predictions=test_pred_series,
    )


def walk_forward_predict(
    X: pd.DataFrame,
    labels: pd.DataFrame,
    folds: list[DateFold],
    *,
    model: str,
    param_grid: Sequence[dict] = ({},),
    inner_val_dates: int,
    inner_folds: int = 1,
    inner_min_train_dates: int,
) -> tuple[pd.Series, list[FoldResult]]:
    """Execute walk-forward prediction across a sequence of folds.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    labels : pd.DataFrame
        Label table.
    folds : list[DateFold]
        Sequence of walk-forward folds.
    model : str
        Model identifier.
    param_grid : Sequence[dict], default=({},)
        Parameter grid for inner tuning.
    inner_val_dates, inner_folds, inner_min_train_dates : int
        Inner validation parameters.

    Returns
    -------
    tuple[pd.Series, list[FoldResult]]
        Concatenated out-of-sample predictions and fold result objects.
    """
    fold_results: list[FoldResult] = []
    for f in folds:
        res = fit_select_predict(
            X=X,
            labels=labels,
            fold=f,
            model=model,
            param_grid=param_grid,
            inner_val_dates=inner_val_dates,
            inner_folds=inner_folds,
            inner_min_train_dates=inner_min_train_dates,
        )
        fold_results.append(res)

    all_preds = pd.concat([res.predictions for res in fold_results])
    if not all_preds.index.is_unique:
        raise ValueError("Concatenated predictions have duplicate indices across test folds")

    return all_preds, fold_results


# ---------------------------------------------------------------------------
# Target weights
# ---------------------------------------------------------------------------

def predictions_to_target_weights(
    pred: pd.Series,
    *,
    gross: float = 1.0,
    rebalance_every: int = 1,
    min_names: int = 2,
) -> pd.DataFrame:
    """Translate raw return predictions into dollar-neutral target weights.

    Parameters
    ----------
    pred : pd.Series
        Predictions indexed by MultiIndex (signal_time, asset).
    gross : float, default=1.0
        Target portfolio gross exposure (sum |w_i| = gross). Must be positive finite.
    rebalance_every : int, default=1
        Rebalance frequency in trading days. Target weights are formed only on
        rebalance dates (every rebalance_every dates, starting from the first).
    min_names : int, default=2
        Minimum finite predictions required on a date to enter positions.

    Returns
    -------
    pd.DataFrame
        Signal_time x asset panel of target weights. Rows are rebalance dates.
        Dollar-neutral (sum w_i = 0) and gross exposure = gross or 0.
    """
    if not isinstance(pred, pd.Series):
        raise TypeError("pred must be a pandas Series")
    if not isinstance(pred.index, pd.MultiIndex) or pred.index.nlevels != 2:
        raise ValueError("pred index must be a MultiIndex with levels (signal_time, asset)")

    if isinstance(gross, (bool, np.bool_)) or not isinstance(gross, (int, float)) or not np.isfinite(gross) or gross <= 0:
        raise ValueError("gross must be a positive finite number")

    reb_freq = _check_positive_int(rebalance_every, "rebalance_every")
    min_n = _check_positive_int(min_names, "min_names")

    vals = pred.to_numpy(dtype=float)
    _check_no_inf(vals, "pred")

    unique_dates = pd.DatetimeIndex(pred.index.get_level_values(0).unique()).sort_values()
    unique_assets = sorted(pred.index.get_level_values(1).unique())

    if len(unique_dates) == 0 or len(unique_assets) == 0:
        return pd.DataFrame(index=pd.DatetimeIndex([]), columns=unique_assets, dtype=float)

    rebalance_dates = unique_dates[::reb_freq]

    rows: list[dict[str, float]] = []
    for d in rebalance_dates:
        sub = pred.loc[d]
        valid = sub.dropna()
        row_dict = {a: 0.0 for a in unique_assets}

        if len(valid) >= min_n:
            p = valid.to_numpy(dtype=float)
            demeaned = p - p.mean()
            demeaned -= demeaned.mean()  # second pass: tiny dispersion around a large level loses precision
            sum_abs = float(np.abs(demeaned).sum())
            # Identical predictions carry no cross-sectional information. Test the range exactly: demeaning
            # equal floats can leave ~1e-19 residues that would otherwise be scaled up to full gross exposure.
            if np.ptp(p) > 0 and sum_abs > 0:
                weights = gross * demeaned / sum_abs
                for a, w in zip(valid.index, weights):
                    row_dict[a] = float(w)

        rows.append(row_dict)

    df_out = pd.DataFrame(rows, index=rebalance_dates, columns=unique_assets, dtype=float)
    df_out.index.name = "signal_time"
    return df_out


# ---------------------------------------------------------------------------
# Prediction & Portfolio Metrics
# ---------------------------------------------------------------------------

def prediction_metrics(
    labels: pd.DataFrame,
    pred: pd.Series,
    *,
    horizon: int,
    train_mean_pred: pd.Series | None = None,
) -> dict:
    """Compute point-in-time accuracy, R^2, and information coefficient metrics.

    Parameters
    ----------
    labels : pd.DataFrame
        Label DataFrame containing column 'y' and MultiIndex (signal_time, asset).
    pred : pd.Series
        Model predictions with MultiIndex (signal_time, asset).
    horizon : int
        Prediction horizon h (used for Newey-West lag nw_lags = horizon - 1).
    train_mean_pred : pd.Series, optional
        Baseline predictions from the train_mean benchmark model.

    Returns
    -------
    dict
        Evaluation metrics including n_rows, n_dates, mse, mse_zero,
        oos_r2_vs_zero, oos_r2_vs_train_mean (if provided), ic_mean,
        ic_t (Newey-West t-statistic), ic_dates, and hit_rate.
    """
    if not isinstance(labels, pd.DataFrame) or "y" not in labels.columns:
        raise ValueError("labels must be a DataFrame with column 'y'")
    if not isinstance(pred, pd.Series):
        raise TypeError("pred must be a pandas Series")

    h = _check_positive_int(horizon, "horizon")

    common_idx = pred.index.intersection(labels.index)
    p_aligned = pred.reindex(common_idx)
    y_aligned = labels.loc[common_idx, "y"]

    p_arr = p_aligned.to_numpy(dtype=float)
    y_arr = y_aligned.to_numpy(dtype=float)
    _check_no_inf(p_arr, "pred")
    _check_no_inf(y_arr, "labels['y']")

    valid_mask = (~np.isnan(p_arr)) & (~np.isnan(y_arr))
    if not valid_mask.any():
        raise ValueError("No overlapping finite predictions and labels found")

    p = p_aligned[valid_mask]
    y = y_aligned[valid_mask]

    n_rows = int(len(p))
    n_dates = int(len(p.index.get_level_values(0).unique()))

    sse = float(((y - p) ** 2).sum())
    mse = float(((y - p) ** 2).mean())
    mse_zero = float((y ** 2).mean())
    sum_y2 = float((y ** 2).sum())
    oos_r2_vs_zero = float(1.0 - sse / sum_y2) if sum_y2 > 0 else float("nan")

    # Hit rate on non-zero predictions
    p_nonzero = p[p != 0]
    y_nonzero = y[p != 0]
    if len(p_nonzero) > 0:
        hit_rate = float((np.sign(p_nonzero) == np.sign(y_nonzero)).mean())
    else:
        hit_rate = float("nan")

    # IC series and Newey-West summary
    p_wide = p.unstack(level=1)
    y_wide = y.unstack(level=1)
    ic_df = ic_series(p_wide, y_wide, method="spearman")
    nw_lags = max(0, h - 1)

    try:
        summary = ic_summary(ic_df["ic"], nw_lags=nw_lags)
        ic_mean = float(summary.mean)
        ic_t = float(summary.t_nw)
        ic_dates = int(summary.n_dates)
    except ValueError:
        ic_mean = float("nan")
        ic_t = float("nan")
        ic_dates = int(ic_df["ic"].dropna().size)

    metrics = {
        "n_rows": n_rows,
        "n_dates": n_dates,
        "mse": mse,
        "mse_zero": mse_zero,
        "oos_r2_vs_zero": oos_r2_vs_zero,
        "ic_mean": ic_mean,
        "ic_t": ic_t,
        "ic_t_stat": ic_t,
        "ic_dates": ic_dates,
        "ic_n_dates": ic_dates,
        "hit_rate": hit_rate,
    }

    if train_mean_pred is not None:
        if not isinstance(train_mean_pred, pd.Series):
            raise TypeError("train_mean_pred must be a pandas Series")
        tm_aligned = train_mean_pred.reindex(p.index)
        tm_arr = tm_aligned.to_numpy(dtype=float)
        _check_no_inf(tm_arr, "train_mean_pred")
        # Both SSEs must use the same rows; a missing benchmark row must not silently shrink one sum.
        both = ~np.isnan(tm_arr)
        if not both.any():
            raise ValueError("train_mean_pred has no finite value on the evaluated rows")
        sse_both = float(((y[both] - p[both]) ** 2).sum())
        sse_tm = float(((y[both] - tm_aligned[both]) ** 2).sum())
        metrics["oos_r2_vs_train_mean"] = float(1.0 - sse_both / sse_tm) if sse_tm > 0 else float("nan")
        metrics["n_rows_vs_train_mean"] = int(both.sum())

    return metrics


def portfolio_metrics(
    ledger: pd.DataFrame,
    initial_cash: float,
    *,
    periods_per_year: int = 252,
) -> dict:
    """Compute cumulative performance, risk, drawdown, and turnover from backtest ledger.

    Parameters
    ----------
    ledger : pd.DataFrame
        Ledger produced by run_backtest with columns 'nav', 'ret', 'fees',
        'traded_notional', and 'nav_pre_trade'.
    initial_cash : float
        Starting account capital (> 0).
    periods_per_year : int, default=252
        Annualization multiplier (default: 252 for daily trading days).

    Returns
    -------
    dict
        Portfolio performance summary including n_returns, total_return,
        ann_mean, ann_vol, sharpe, max_drawdown, total_fees, and turnover_ann.
    """
    if not isinstance(ledger, pd.DataFrame):
        raise TypeError("ledger must be a pandas DataFrame")
    if ledger.empty:
        raise ValueError("ledger must not be empty")

    required_cols = {"nav", "ret", "fees", "traded_notional", "nav_pre_trade"}
    missing = required_cols - set(ledger.columns)
    if missing:
        raise ValueError(f"ledger is missing required columns: {sorted(missing)}")

    if isinstance(initial_cash, (bool, np.bool_)) or not isinstance(initial_cash, (int, float)) or not np.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be a positive finite number")

    ppy = _check_positive_int(periods_per_year, "periods_per_year")

    n_returns = len(ledger)
    final_nav = float(ledger["nav"].iloc[-1])
    total_return = float(final_nav / initial_cash - 1.0)

    # N returns correspond to N+1 wealth points
    wealth = np.concatenate(([float(initial_cash)], ledger["nav"].to_numpy(dtype=float)))
    returns = ledger["ret"].to_numpy(dtype=float)

    ann_mean = float(returns.mean() * ppy)
    ann_vol = annualized_volatility(returns, ppy)
    # A flat book (zero / train_mean baselines) has zero volatility: Sharpe is undefined, report NaN.
    sharpe = sharpe_ratio(returns, np.zeros_like(returns), ppy) if np.std(returns, ddof=1) > 0 else float("nan")

    dd_path = drawdown_path(wealth)
    max_drawdown = float(dd_path.min())

    total_fees = float(ledger["fees"].sum())

    # Annualized turnover = sum(traded_notional / nav_pre_trade) / years
    years = float(n_returns / ppy)
    traded = ledger["traded_notional"].to_numpy(dtype=float)
    nav_pre = ledger["nav_pre_trade"].to_numpy(dtype=float)
    valid_rebalance = (traded > 0) & (nav_pre > 0)

    if valid_rebalance.any():
        turnover_ratio = float((traded[valid_rebalance] / nav_pre[valid_rebalance]).sum())
    else:
        turnover_ratio = 0.0

    turnover_ann = float(turnover_ratio / years) if years > 0 else 0.0

    return {
        "n_returns": n_returns,
        "total_return": total_return,
        "ann_mean": ann_mean,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "total_fees": total_fees,
        "turnover_ann": turnover_ann,
    }


# ---------------------------------------------------------------------------
# Constructed teaching panel and feature helpers (host addition, A8-A)
# ---------------------------------------------------------------------------

def simulate_return_panel(*, n_assets: int = 40, n_days: int = 1260, n_signal: int = 2, n_noise: int = 20,
                          signal_loading: float = 0.0004, char_rho: float = 0.98, idio_vol: float = 0.02,
                          market_vol: float = 0.01, regime_break: float | None = None,
                          start: str = "2015-01-02", seed: int = 0) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """CONSTRUCTED daily panel: closes and slow characteristics observed at each close (teaching data only).

    r[i,t+1] = beta_i * m[t+1] + s_t * signal_loading * sum_j 0.5**j * q_j[i,t] + e[i,t+1]   (simple daily returns)

    * q_j (j = 1..n_signal) and noise_k (k = 1..n_noise) are independent stationary AR(1) characteristics with
      unit variance and coefficient ``char_rho``; noise_k has zero loading by construction.
    * beta_i ~ U(0.8, 1.2), m ~ N(0, market_vol), e ~ N(0, idio_vol), all iid; closes start at 100.
    * s_t = +1, or -1 from date index int(regime_break * n_days) on (a regime flip of the true loading).
    * Characteristic values dated t are known at the close of t (available_at = signal_time).
    Returns ``(close, characteristics)``; close is dates x assets on a business-day index.
    """
    for name, value in (("n_assets", n_assets), ("n_days", n_days), ("n_signal", n_signal)):
        _check_positive_int(value, name)
    if isinstance(n_noise, (bool, np.bool_)) or not isinstance(n_noise, (int, np.integer)) or n_noise < 0:
        raise ValueError("n_noise must be a non-negative integer")
    if not (0 <= char_rho < 1) or idio_vol <= 0 or market_vol < 0 or not np.isfinite(signal_loading):
        raise ValueError("need 0 <= char_rho < 1, idio_vol > 0, market_vol >= 0, finite signal_loading")
    if regime_break is not None and not 0 < regime_break < 1:
        raise ValueError("regime_break must be a fraction in (0, 1) or None")
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n_days)
    assets = [f"A{i:02d}" for i in range(n_assets)]

    def ar1(k: int) -> np.ndarray:
        x = np.empty((k, n_days, n_assets))
        x[:, 0] = rng.normal(size=(k, n_assets))
        shock = rng.normal(scale=np.sqrt(1 - char_rho ** 2), size=(k, n_days, n_assets))
        for t in range(1, n_days):
            x[:, t] = char_rho * x[:, t - 1] + shock[:, t]
        return x

    q, noise = ar1(n_signal), ar1(n_noise)
    beta = rng.uniform(0.8, 1.2, n_assets)
    m = rng.normal(0.0, market_vol, n_days)
    e = rng.normal(0.0, idio_vol, (n_days, n_assets))
    sign = np.ones(n_days)
    if regime_break is not None:
        sign[int(regime_break * n_days):] = -1.0
    alpha = np.zeros((n_days, n_assets))
    alpha[1:] = signal_loading * sign[:-1, None] * np.tensordot(0.5 ** np.arange(n_signal), q[:, :-1], axes=1)
    ret = beta[None, :] * m[:, None] + alpha + e
    ret[0] = 0.0
    if (ret <= -1).any():
        raise ValueError("simulated simple return <= -100%; lower the volatilities")
    close = pd.DataFrame(100.0 * np.cumprod(1.0 + ret, axis=0), index=dates, columns=assets)
    chars = {f"q_{j + 1}": pd.DataFrame(q[j], index=dates, columns=assets) for j in range(n_signal)}
    chars.update({f"noise_{k + 1:02d}": pd.DataFrame(noise[k], index=dates, columns=assets) for k in range(n_noise)})
    return close, chars


def price_features(close: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Close-based features known at each close t (NaN until enough history exists).

    rev_5 = -(close[t]/close[t-5] - 1); mom_60_5 = close[t-5]/close[t-60] - 1 (skips the latest 5 days);
    vol_20 = sample SD (ddof=1) of the last 20 daily simple returns ending at t.
    """
    if not isinstance(close, pd.DataFrame) or not close.index.is_monotonic_increasing or not close.index.is_unique:
        raise ValueError("close must be a DataFrame with a unique increasing index")
    if np.isinf(close.to_numpy(dtype=float)).any() or (close.to_numpy(dtype=float) <= 0).any():
        raise ValueError("close prices must be positive and finite (NaN allowed)")
    daily = close / close.shift(1) - 1.0
    return {"rev_5": -(close / close.shift(5) - 1.0),
            "mom_60_5": close.shift(5) / close.shift(60) - 1.0,
            "vol_20": daily.rolling(20, min_periods=20).std(ddof=1)}


def stack_features(features: dict[str, pd.DataFrame], index: pd.MultiIndex) -> pd.DataFrame:
    """Stack date x asset feature panels into a (signal_time, asset) table aligned to ``index`` (e.g. labels.index).

    Missing (date, asset) cells become NaN; no forward filling.
    """
    if not features:
        raise ValueError("features must not be empty")
    cols = {name: panel.stack(future_stack=True).reindex(index) for name, panel in features.items()}
    out = pd.DataFrame(cols, index=index)
    if np.isinf(out.to_numpy(dtype=float)).any():
        raise ValueError("features contain infinite values")
    return out


def backtest_predictions(close: pd.DataFrame, pred: pd.Series, *, rebalance_every: int, fee_rate: float,
                         gross: float = 1.0, execution_lag: int = 1, initial_cash: float = 1_000_000.0,
                         periods_per_year: int = 252) -> dict:
    """Prediction -> dollar-neutral targets -> Chapter 29 ledger (lagged fills, proportional fees) -> metrics.

    Targets are formed on every ``rebalance_every``-th signal date of ``pred`` (``predictions_to_target_weights``)
    and filled ``execution_lag`` trading dates later at the close (``run_backtest``; E = P). The ledger starts at
    the first signal date of ``pred`` so that the flat pre-test history does not dilute the statistics; NAV is
    marked daily from closes, independently of the label horizon. Borrow fees, financing spreads, impact and
    capacity are NOT modelled (``allow_short=True`` credits full short proceeds to cash, Chapter 29 contract).
    Returns ``{"weights", "ledger", "metrics"}``; metrics come from ``portfolio_metrics`` (N returns, N+1 wealth).
    """
    from quant_course.backtest import BacktestConfig, run_backtest  # local: keep import cost off the hot path

    weights = predictions_to_target_weights(pred, gross=gross, rebalance_every=rebalance_every)
    start = weights.index[0]
    prices = close.loc[start:, list(weights.columns)]
    cfg = BacktestConfig(initial_cash=float(initial_cash), fee_rate=float(fee_rate), lag=int(execution_lag),
                         allow_short=True, max_gross=float(gross) + 1e-9)
    result = run_backtest(prices, weights.loc[weights.index.isin(prices.index)], cfg)
    return {"weights": weights, "ledger": result.ledger,
            "metrics": portfolio_metrics(result.ledger, float(initial_cash), periods_per_year=periods_per_year)}
