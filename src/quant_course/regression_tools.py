"""Validated time-series regression and training-only regularization examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class OLSInference:
    """One OLS coefficient fit with classical, HC3, and HAC covariance."""

    classical: Any
    hc3: Any
    hac: Any
    design_condition_number: float
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class CVFoldRange:
    """Timestamp boundaries and sizes for one chronological CV split."""

    train_start: pd.Timestamp
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp
    train_n: int
    validation_n: int
    gap_n: int


@dataclass(frozen=True)
class RegularizationSelection:
    """A best pipeline selected and refit using only the supplied past sample."""

    name: str
    estimator: Pipeline
    best_params: dict[str, Any]
    best_cv_mse: float
    training_n: int
    training_start: pd.Timestamp
    training_end: pd.Timestamp
    folds: tuple[CVFoldRange, ...]


def validate_time_index(index: pd.Index, *, name: str) -> pd.DatetimeIndex:
    """Require a non-empty, unique, ascending, timezone-aware datetime index."""

    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError(f"{name} must use a pandas DatetimeIndex")
    if index.tz is None:
        raise ValueError(f"{name} must be timezone-aware")
    if index.hasnans:
        raise ValueError(f"{name} must not contain NaT")
    if index.has_duplicates:
        raise ValueError(f"{name} must have unique timestamps")
    if not index.is_monotonic_increasing:
        raise ValueError(f"{name} must be sorted in ascending order")
    if len(index) < 2:
        raise ValueError(f"{name} must have at least two timestamps")
    return index


def _validated_xy(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    require_equal_spacing: bool,
) -> tuple[pd.DataFrame, pd.Series]:
    if not isinstance(features, pd.DataFrame):
        raise TypeError("features must be a pandas DataFrame with timestamps")
    if not isinstance(target, pd.Series):
        raise TypeError("target must be a pandas Series with timestamps")
    x_index = validate_time_index(features.index, name="feature index")
    y_index = validate_time_index(target.index, name="target index")
    if x_index.tz != y_index.tz:
        raise ValueError("feature and target indexes must use the same timezone")
    if not x_index.equals(y_index):
        raise ValueError("feature and target timestamps must align exactly")
    if features.empty or features.shape[1] == 0:
        raise ValueError("features must contain at least one column")
    if not features.columns.is_unique:
        raise ValueError("feature names must be unique")
    if "const" in features.columns:
        raise ValueError("do not pass a const feature; the OLS helper adds an intercept")
    if np.iscomplexobj(features.to_numpy()) or np.iscomplexobj(target.to_numpy()):
        raise TypeError("features and target must contain real, not complex, values")
    try:
        x = features.astype(float).copy()
        y = target.astype(float).copy()
    except (TypeError, ValueError) as exc:
        raise TypeError("features and target must contain real numeric values") from exc
    x_values = x.to_numpy()
    y_values = y.to_numpy()
    if not np.isfinite(x_values).all() or not np.isfinite(y_values).all():
        raise ValueError("features and target must be finite; missing values are not dropped")
    constant_columns = [column for column in x.columns if x[column].nunique(dropna=False) <= 1]
    if constant_columns:
        raise ValueError(f"constant feature columns are not allowed: {constant_columns}")
    if require_equal_spacing and len(x_index) > 2:
        differences = np.diff(x_index.asi8)
        if not np.all(differences == differences[0]):
            raise ValueError("HAC and time-series validation require equally spaced timestamps")
    return x, y


def fit_ols_with_robust_covariance(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    hac_maxlags: int = 5,
) -> OLSInference:
    """Fit an intercept OLS model and attach classical, HC3, and HAC results.

    The point estimates are common across covariance choices.  HC3 changes
    heteroskedasticity-robust inference; HAC also allows serial dependence under
    additional regularity assumptions.  ``hac_maxlags`` is a declared teaching
    setting, not an automatically optimal bandwidth.  This teaching helper
    requires consecutive observations with equal elapsed timestamp spacing.
    HC3 denominators must be distinguishable from zero at machine precision
    times the largest design dimension; unit-leverage observations are rejected.
    Missing periods and irregular event data must not be silently compressed
    into row-based HAC lags; do not fabricate observations to pass the check.
    """

    x, y = _validated_xy(features, target, require_equal_spacing=True)
    if isinstance(hac_maxlags, (bool, np.bool_)) or not isinstance(
        hac_maxlags, (int, np.integer)
    ):
        raise TypeError("hac_maxlags must be an integer")
    if not 1 <= hac_maxlags < len(x):
        raise ValueError("hac_maxlags must be at least 1 and smaller than nobs")
    design = sm.add_constant(x, has_constant="add")
    design_values = design.to_numpy(dtype=float)
    parameter_count = design_values.shape[1]
    if len(design_values) <= parameter_count:
        raise ValueError("OLS requires more observations than design columns")
    rank = int(np.linalg.matrix_rank(design_values))
    if rank < parameter_count:
        raise ValueError(
            f"OLS design is rank deficient: rank {rank} < {parameter_count} columns"
        )
    condition = float(np.linalg.cond(design_values))
    model = sm.OLS(y, design, missing="raise", hasconst=True)
    classical = model.fit()
    # SVD row norms avoid forming the ill-conditioned Gram inverse for leverage.
    left_vectors = np.linalg.svd(design_values, full_matrices=False)[0]
    leverage = np.sum(left_vectors * left_vectors, axis=1)
    unit_leverage_tolerance = np.finfo(float).eps * max(design_values.shape)
    if np.any(1.0 - leverage <= unit_leverage_tolerance):
        raise ValueError("HC3 requires leverage numerically distinguishable below one")
    hc3 = classical.get_robustcov_results(cov_type="HC3", use_t=True)
    hac = classical.get_robustcov_results(
        cov_type="HAC",
        maxlags=int(hac_maxlags),
        kernel="bartlett",
        use_correction=True,
        use_t=True,
    )
    return OLSInference(
        classical=classical,
        hc3=hc3,
        hac=hac,
        design_condition_number=condition,
        feature_names=tuple(str(name) for name in x.columns),
    )


def select_regularized_models(
    training_features: pd.DataFrame,
    training_target: pd.Series,
    *,
    n_splits: int = 5,
    gap: int = 5,
    test_size: int = 30,
    alphas: Sequence[float] = (1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 2e-2),
    l1_ratios: Sequence[float] = (0.2, 0.5, 0.8),
) -> dict[str, RegularizationSelection]:
    """Select Ridge/Lasso/ElasticNet only inside an ordered training window.

    A ``StandardScaler`` is part of every searched pipeline, so each fold's
    means and scales are fit only on that fold's training rows.  The returned
    best estimator is refit on all supplied training rows.  This function takes
    no holdout argument; callers evaluate a reserved holdout only after
    selection is complete.
    """

    x, y = _validated_xy(training_features, training_target, require_equal_spacing=True)
    splits_count = _positive_int(n_splits, "n_splits")
    gap_n = _nonnegative_int(gap, "gap")
    validation_n = _positive_int(test_size, "test_size")
    if splits_count < 2:
        raise ValueError("n_splits must be at least 2")
    if len(x) < (splits_count * (validation_n + gap_n) + 2):
        raise ValueError("training sample is too short for the requested time-series folds")
    alpha_values = _positive_finite_values(alphas, "alphas")
    ratio_values = _positive_finite_values(l1_ratios, "l1_ratios")
    if any(not 0.0 < ratio < 1.0 for ratio in ratio_values):
        raise ValueError("l1_ratios must be strictly between 0 and 1")

    splitter = TimeSeriesSplit(n_splits=splits_count, gap=gap_n, test_size=validation_n)
    splits = tuple(splitter.split(x))
    fold_ranges: list[CVFoldRange] = []
    for train_indices, validation_indices in splits:
        if train_indices[-1] >= validation_indices[0]:
            raise RuntimeError("time-series CV fold trains on a validation observation")
        actual_gap = int(validation_indices[0] - train_indices[-1] - 1)
        if actual_gap != gap_n:
            raise RuntimeError("time-series CV fold does not preserve the requested gap")
        fold_ranges.append(
            CVFoldRange(
                train_start=x.index[train_indices[0]],
                train_end=x.index[train_indices[-1]],
                validation_start=x.index[validation_indices[0]],
                validation_end=x.index[validation_indices[-1]],
                train_n=len(train_indices),
                validation_n=len(validation_indices),
                gap_n=actual_gap,
            )
        )

    model_specs = {
        "Ridge": (Ridge(), {"model__alpha": alpha_values}),
        "Lasso": (
            Lasso(max_iter=100_000, tol=1e-5, selection="cyclic"),
            {"model__alpha": alpha_values},
        ),
        "ElasticNet": (
            ElasticNet(max_iter=100_000, tol=1e-5, selection="cyclic"),
            {"model__alpha": alpha_values, "model__l1_ratio": ratio_values},
        ),
    }
    selected: dict[str, RegularizationSelection] = {}
    for name, (regressor, parameter_grid) in model_specs.items():
        pipeline = Pipeline([("scaler", StandardScaler()), ("model", regressor)])
        search = GridSearchCV(
            estimator=pipeline,
            param_grid=parameter_grid,
            scoring="neg_mean_squared_error",
            cv=splits,
            refit=True,
            n_jobs=1,
            error_score="raise",
        )
        search.fit(x, y)
        selected[name] = RegularizationSelection(
            name=name,
            estimator=search.best_estimator_,
            best_params=dict(search.best_params_),
            best_cv_mse=float(-search.best_score_),
            training_n=len(x),
            training_start=x.index[0],
            training_end=x.index[-1],
            folds=tuple(fold_ranges),
        )
    return selected


def simulate_capm_like_data(
    n: int = 400,
    *,
    seed: int = 20261008,
    alpha: float = 0.0001,
    beta: float = 1.2,
    ar_phi: float = 0.55,
) -> pd.DataFrame:
    """Create a fictional daily-return panel with heteroskedastic AR(1) noise.

    ``market_near_duplicate`` is a constructed, nearly collinear second feature
    for regularization instruction.  It is not a second measured market factor.
    No output from this function is empirical CAPM evidence.
    """

    size = _positive_int(n, "n")
    if size < 20:
        raise ValueError("n must be at least 20 for the teaching split")
    for value, name in ((alpha, "alpha"), (beta, "beta")):
        if isinstance(value, (bool, np.bool_)) or not np.isfinite(value):
            raise ValueError(f"{name} must be a finite real number")
    if (
        isinstance(ar_phi, (bool, np.bool_))
        or not np.isfinite(ar_phi)
        or abs(ar_phi) >= 1.0
    ):
        raise ValueError("ar_phi must be finite and strictly between -1 and 1")
    generator = np.random.default_rng(seed)
    market = generator.normal(loc=0.0002, scale=0.012, size=size)
    conditional_sd = 0.002 + 0.30 * np.abs(market)
    innovations = generator.normal(loc=0.0, scale=conditional_sd, size=size)
    residuals = np.empty(size, dtype=float)
    residuals[0] = innovations[0]
    for index in range(1, size):
        residuals[index] = ar_phi * residuals[index - 1] + innovations[index]
    asset = alpha + beta * market + residuals
    near_duplicate = market + generator.normal(loc=0.0, scale=1e-5, size=size)
    index = pd.date_range(
        "2024-01-02", periods=size, freq="D", tz="UTC", name="date"
    )
    data = pd.DataFrame(
        {
            "market_excess": market,
            "market_near_duplicate": near_duplicate,
            "asset_excess": asset,
            "constructed_residual": residuals,
            "constructed_conditional_sd": conditional_sd,
        },
        index=index,
    )
    data.attrs.update(
        {
            "provenance": "constructed teaching data; not empirical market observations",
            "seed": int(seed),
            "true_alpha": float(alpha),
            "true_beta": float(beta),
            "ar_phi": float(ar_phi),
        }
    )
    return data


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return int(value)


def _nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return int(value)


def _positive_finite_values(values: Sequence[float], name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result or not all(np.isfinite(value) and value > 0.0 for value in result):
        raise ValueError(f"{name} must contain positive finite values")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    return result
