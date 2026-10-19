"""Monthly unit-root, cointegration, VAR, and pair-screening helpers.

This module is intentionally narrow: it exposes the statistical tests and
time-boundary helpers used by Chapter 17.  It does not imply that a rejected
unit-root null or a small cointegration p-value is an investment signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from numbers import Real
from typing import Any, Literal
import warnings

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import CollinearityWarning
from statsmodels.tsa.stattools import adfuller, coint, grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR

from quant_course.time_series import validate_monthly_series


ADFRegression = Literal["n", "c", "ct", "ctt"]
DeterministicTrend = Literal["n", "c", "ct", "ctt"]


@dataclass(frozen=True)
class ADFTestResult:
    statistic: float
    pvalue: float
    used_lag: int
    nobs: int
    critical_values: dict[str, float]
    regression: str


@dataclass(frozen=True)
class CointegrationTestResult:
    statistic: float
    pvalue: float
    critical_values: dict[str, float]
    trend: str


@dataclass(frozen=True)
class GrangerTestResult:
    caused: str
    causing: str
    lag: int
    f_statistic: float
    pvalue: float
    denominator_df: float
    numerator_df: float


def validate_monthly_frame(
    values: pd.DataFrame,
    *,
    min_observations: int = 2,
) -> pd.DataFrame:
    """Validate a complete monthly panel and return a float64 copy.

    Every column uses the same strictly increasing, contiguous monthly index.
    Missing data are rejected rather than dropped, forward-filled, or treated
    as if adjacent observations were one month apart.
    """
    if not isinstance(values, pd.DataFrame):
        raise TypeError("values must be a pandas DataFrame")
    if values.empty or values.shape[1] < 1:
        raise ValueError("values must contain at least one column")
    if not values.columns.is_unique:
        raise ValueError("column names must be unique")
    if any(not isinstance(column, str) or not column for column in values.columns):
        raise TypeError("column names must be non-empty strings")
    checked: dict[str, pd.Series] = {}
    for column in values.columns:
        checked[column] = validate_monthly_series(
            values[column], min_observations=min_observations
        )
    first = next(iter(checked.values()))
    for column, series in checked.items():
        if not series.index.equals(first.index):
            raise ValueError(f"column {column!r} does not share the common monthly index")
    return pd.DataFrame(checked, index=first.index.copy())


def _validate_choice(value: str, choices: tuple[str, ...], name: str) -> str:
    if value not in choices:
        raise ValueError(f"{name} must be one of {choices}")
    return value


def adf_test(
    series: pd.Series,
    *,
    regression: ADFRegression = "c",
    max_lag: int | None = None,
    autolag: Literal["AIC", "BIC", "t-stat"] | None = "AIC",
) -> ADFTestResult:
    """Run an augmented Dickey-Fuller test on one complete monthly series.

    The null is a unit root.  ``regression`` determines included deterministic
    terms; it must be chosen from the data-generating question, not searched
    until a desired p-value appears.
    """
    values = validate_monthly_series(series, min_observations=12)
    regression = _validate_choice(regression, ("n", "c", "ct", "ctt"), "regression")
    if max_lag is not None and (
        isinstance(max_lag, bool) or not isinstance(max_lag, int) or max_lag < 0
    ):
        raise ValueError("max_lag must be a non-negative integer or None")
    if autolag not in {"AIC", "BIC", "t-stat", None}:
        raise ValueError("autolag must be AIC, BIC, t-stat, or None")
    result = adfuller(
        values.to_numpy(),
        maxlag=max_lag,
        regression=regression,
        autolag=autolag,
        result_object=True,
    )
    return ADFTestResult(
        statistic=float(result.statistic),
        pvalue=float(result.pvalue),
        used_lag=int(result.lags),
        nobs=int(result.nobs),
        critical_values={key: float(value) for key, value in result.critical_values.items()},
        regression=regression,
    )


def engle_granger_test(
    dependent: pd.Series,
    regressor: pd.Series,
    *,
    trend: DeterministicTrend = "c",
    max_lag: int | None = None,
    autolag: Literal["AIC", "BIC", "t-stat"] | None = "AIC",
) -> CointegrationTestResult:
    """Run the augmented Engle-Granger test with its cointegration null law.

    This calls ``statsmodels.coint`` rather than applying ordinary ADF
    critical values to first-stage estimated residuals.
    """
    y = validate_monthly_series(dependent, min_observations=24)
    x = validate_monthly_series(regressor, min_observations=24)
    if not y.index.equals(x.index):
        raise ValueError("dependent and regressor must have identical monthly indexes")
    trend = _validate_choice(trend, ("n", "c", "ct", "ctt"), "trend")
    if max_lag is not None and (
        isinstance(max_lag, bool) or not isinstance(max_lag, int) or max_lag < 0
    ):
        raise ValueError("max_lag must be a non-negative integer or None")
    if autolag not in {"AIC", "BIC", "t-stat", None}:
        raise ValueError("autolag must be AIC, BIC, t-stat, or None")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", CollinearityWarning)
        result = coint(
            y.to_numpy(),
            x.to_numpy(),
            trend=trend,
            maxlag=max_lag,
            autolag=autolag,
            return_results=False,
        )
    if any(isinstance(item.message, CollinearityWarning) for item in caught):
        raise ValueError(
            "Engle-Granger test is unreliable for perfectly or nearly collinear series"
        )
    if hasattr(result, "coint_t"):
        statistic, pvalue, critical_values = (
            result.coint_t,
            result.pvalue,
            result.critical_values,
        )
    else:  # Compatibility with statsmodels versions returning the legacy tuple.
        statistic, pvalue, critical_values = result[:3]
    if not np.isfinite(statistic) or not np.isfinite(pvalue):
        raise ValueError("Engle-Granger test returned a non-finite statistic or p-value")
    return CointegrationTestResult(
        statistic=float(statistic),
        pvalue=float(pvalue),
        critical_values={
            key: float(value) for key, value in zip(("1%", "5%", "10%"), critical_values)
        },
        trend=trend,
    )


def total_return_index_proxy(monthly_returns: pd.DataFrame) -> pd.DataFrame:
    """Compound published decimal monthly returns into teaching TR-index proxies.

    The first row is the index value after that month's return, from a base of
    100 immediately before the sample.  This is a descriptive transformation,
    not an investable or point-in-time price history.
    """
    returns = validate_monthly_frame(monthly_returns, min_observations=2)
    if (returns <= -1.0).any().any():
        raise ValueError("simple returns must be greater than -1 to compound an index")
    index = 100.0 * (1.0 + returns).cumprod()
    index.columns = [f"{column}_TR_proxy" for column in returns.columns]
    return index


def simulate_noncointegrated_common_trend(
    *,
    n: int = 600,
    seed: int = 20261017,
    common_step_sd: float = 1.0,
    idiosyncratic_step_sd: float = 0.2,
    start: str = "1970-01",
) -> pd.DataFrame:
    """Construct highly correlated I(1) series with no stationary linear spread."""
    _validate_simulation_args(n, seed, common_step_sd, idiosyncratic_step_sd)
    rng = np.random.default_rng(seed)
    common = np.cumsum(rng.normal(0.0, common_step_sd, size=n))
    idio_x = np.cumsum(rng.normal(0.0, idiosyncratic_step_sd, size=n))
    idio_y = np.cumsum(rng.normal(0.0, idiosyncratic_step_sd, size=n))
    index = pd.period_range(start, periods=n, freq="M", name="month")
    return pd.DataFrame(
        {"x": common + idio_x, "y": common + idio_y, "common_trend": common},
        index=index,
    )


def simulate_cointegrated_pair(
    *,
    n: int = 600,
    seed: int = 20261018,
    beta: float = 1.4,
    spread_phi: float = 0.65,
    common_step_sd: float = 1.0,
    spread_innovation_sd: float = 0.35,
    start: str = "1970-01",
) -> pd.DataFrame:
    """Construct I(1) x and y=alpha+beta*x+stationary AR(1) spread."""
    _validate_simulation_args(n, seed, common_step_sd, spread_innovation_sd)
    if isinstance(beta, (bool, np.bool_)) or not isinstance(beta, Real):
        raise TypeError("beta must be a non-boolean real scalar")
    if not np.isfinite(beta) or beta == 0:
        raise ValueError("beta must be finite and non-zero")
    if not np.isfinite(spread_phi) or abs(spread_phi) >= 1:
        raise ValueError("a stationary spread requires abs(spread_phi) < 1")
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.normal(0.0, common_step_sd, size=n))
    innovations = rng.normal(0.0, spread_innovation_sd, size=n)
    spread = np.empty(n, dtype=float)
    spread[0] = innovations[0] / np.sqrt(1.0 - spread_phi**2)
    for t in range(1, n):
        spread[t] = spread_phi * spread[t - 1] + innovations[t]
    y = 0.25 + beta * x + spread
    index = pd.period_range(start, periods=n, freq="M", name="month")
    return pd.DataFrame({"x": x, "y": y, "spread": spread}, index=index)


def _validate_simulation_args(
    n: int,
    seed: int,
    common_sd: float,
    idio_sd: float,
) -> None:
    if isinstance(n, bool) or not isinstance(n, int) or n < 48:
        raise ValueError("n must be an integer of at least 48 months")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not np.isfinite([common_sd, idio_sd]).all() or common_sd <= 0 or idio_sd <= 0:
        raise ValueError("simulation step standard deviations must be positive and finite")


def fit_var_forecast(
    training: pd.DataFrame,
    *,
    lags: int,
    steps: int = 1,
    trend: DeterministicTrend = "c",
) -> pd.DataFrame:
    """Fit a fixed-order VAR on training rows and forecast future months.

    Stationarity/model-form checks are a caller responsibility.  The function
    never accepts a separate test frame, so future observations cannot enter
    estimation through this interface.
    """
    panel = validate_monthly_frame(training, min_observations=12)
    if isinstance(lags, bool) or not isinstance(lags, int) or lags < 1:
        raise ValueError("lags must be a positive integer")
    if len(panel) <= 2 + lags * panel.shape[1]:
        raise ValueError("too few training observations for this VAR order and dimension")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer number of months")
    trend = _validate_choice(trend, ("n", "c", "ct", "ctt"), "trend")
    fitted = VAR(panel).fit(maxlags=lags, ic=None, trend=trend)
    values = fitted.forecast(panel.to_numpy()[-lags:], steps=steps)
    index = pd.period_range(panel.index[-1] + 1, periods=steps, freq="M", name="month")
    return pd.DataFrame(values, index=index, columns=panel.columns)


def granger_test(
    *,
    caused: pd.Series,
    causing: pd.Series,
    max_lag: int,
) -> GrangerTestResult:
    """Test whether ``causing`` adds lagged predictive content for ``caused``.

    statsmodels expects columns as [caused, causing]; reversing them changes
    the question.  A small p-value is predictive evidence for this fitted
    information set, not evidence of a structural intervention effect.
    """
    y = validate_monthly_series(caused, min_observations=24)
    x = validate_monthly_series(causing, min_observations=24)
    if not y.index.equals(x.index):
        raise ValueError("caused and causing series must have identical monthly indexes")
    if y.name is None or x.name is None:
        raise ValueError("caused and causing series must have names")
    if y.name == x.name:
        raise ValueError("caused and causing series must have distinct names")
    if isinstance(max_lag, bool) or not isinstance(max_lag, int) or max_lag < 1:
        raise ValueError("max_lag must be a positive integer")
    if len(y) <= 3 * max_lag + 10:
        raise ValueError("sample is too short for the requested Granger lag")
    results = grangercausalitytests(
        np.column_stack((y.to_numpy(), x.to_numpy())),
        maxlag=max_lag,
        addconst=True,
    )
    f_stat, pvalue, denominator_df, numerator_df = results[max_lag][0]["ssr_ftest"]
    return GrangerTestResult(
        caused=str(y.name),
        causing=str(x.name),
        lag=max_lag,
        f_statistic=float(f_stat),
        pvalue=float(pvalue),
        denominator_df=float(denominator_df),
        numerator_df=float(numerator_df),
    )


def screen_cointegration_pairs(
    levels: pd.DataFrame,
    *,
    training_end: pd.Period,
    trend: DeterministicTrend = "c",
) -> pd.DataFrame:
    """Test every unordered column pair using observations through training_end.

    Benjamini-Hochberg adjusted p-values (often called q-values) are returned
    as an exploratory false-discovery-rate (FDR) adjustment.  The usual BH FDR
    guarantee requires independent tests or an applicable positive-dependence
    condition such as PRDS. Pair tests here share series, and that condition is
    not established. These values are not a family-wise error-rate (FWER)
    adjustment and do not address structural instability.
    """
    panel = validate_monthly_frame(levels, min_observations=24)
    if panel.shape[1] < 2:
        raise ValueError("levels must contain at least two series")
    trend = _validate_choice(trend, ("n", "c", "ct", "ctt"), "trend")
    if not isinstance(training_end, pd.Period) or training_end.freqstr != "M":
        raise TypeError('training_end must be a pandas monthly Period with freq="M"')
    train = panel.loc[:training_end]
    if len(train) < 24:
        raise ValueError("training interval must contain at least 24 months")
    if train.index[-1] != training_end:
        raise ValueError("training_end must be an observed month in the panel")
    rows: list[dict[str, Any]] = []
    for left, right in combinations(train.columns, 2):
        result = engle_granger_test(train[left], train[right], trend=trend)
        rows.append(
            {
                "series_1": left,
                "series_2": right,
                "n_train": len(train),
                "training_end": str(training_end),
                "statistic": result.statistic,
                "pvalue": result.pvalue,
            }
        )
    result_frame = pd.DataFrame(rows)
    result_frame["qvalue_bh"] = _benjamini_hochberg(result_frame["pvalue"].to_numpy())
    return result_frame.sort_values(["pvalue", "series_1", "series_2"], ignore_index=True)


def _benjamini_hochberg(pvalues: np.ndarray) -> np.ndarray:
    if not np.isfinite(pvalues).all() or ((pvalues < 0) | (pvalues > 1)).any():
        raise ValueError("p-values must be finite and lie in [0, 1]")
    count = len(pvalues)
    order = np.argsort(pvalues)
    ranked = pvalues[order] * count / np.arange(1, count + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    output = np.empty(count, dtype=float)
    output[order] = np.minimum(adjusted, 1.0)
    return output
