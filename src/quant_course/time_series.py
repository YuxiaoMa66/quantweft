"""Validated monthly time-series helpers for Chapter 16.

All observations are indexed by consecutive calendar months.  The helpers
reject gaps and missing/non-finite values rather than compressing time or
silently imputing data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.arima_process import ArmaProcess
from statsmodels.tsa.stattools import acf, pacf


ARIMAOrder = tuple[int, int, int]


@dataclass(frozen=True)
class AR1Moments:
    mean: float
    variance: float
    autocovariances: tuple[float, ...]
    autocorrelations: tuple[float, ...]


@dataclass(frozen=True)
class FittedARIMA:
    """A statsmodels fit plus residuals restored to decimal-return units."""

    result: Any
    index: pd.PeriodIndex
    scale: float

    @property
    def residuals(self) -> pd.Series:
        return pd.Series(
            np.asarray(self.result.resid, dtype=float) / self.scale,
            index=self.index.copy(),
            name="arima_residual",
        )


def validate_monthly_series(
    values: pd.Series,
    *,
    min_observations: int = 2,
) -> pd.Series:
    """Return a float64 copy of a complete, ordered monthly series.

    A ``PeriodIndex(freq="M")`` represents calendar-month steps directly;
    this intentionally avoids treating unequal month lengths as equal days.
    """
    if not isinstance(values, pd.Series):
        raise TypeError("values must be a pandas Series")
    if not isinstance(values.index, pd.PeriodIndex):
        raise TypeError('values must use a monthly PeriodIndex with freq="M"')
    if values.index.freqstr != "M":
        raise ValueError('values must use a monthly PeriodIndex with freq="M"')
    if values.index.hasnans:
        raise ValueError("monthly index must not contain NaT")
    if not values.index.is_monotonic_increasing:
        raise ValueError("monthly index must be ordered increasingly")
    if values.index.has_duplicates:
        raise ValueError("monthly index must be unique")
    if len(values) < min_observations:
        raise ValueError(f"at least {min_observations} observations are required")
    expected = pd.period_range(values.index[0], periods=len(values), freq="M")
    if not values.index.equals(expected):
        raise ValueError("monthly index must be contiguous; missing months are rejected")
    if not is_numeric_dtype(values.dtype) or is_bool_dtype(values.dtype):
        raise TypeError("values must be a real numeric series, not boolean")
    if np.iscomplexobj(values.to_numpy()):
        raise TypeError("values must be real, not complex")
    try:
        numeric = pd.Series(
            values.to_numpy(dtype="float64", na_value=np.nan),
            index=values.index.copy(),
            name=values.name,
        )
    except (TypeError, ValueError) as exc:
        raise TypeError("values must convert to float64") from exc
    array = numeric.to_numpy()
    if not np.isfinite(array).all():
        raise ValueError("values must be finite and contain no missing observations")
    return numeric


def split_monthly_series(
    values: pd.Series,
    *,
    train_size: int,
) -> tuple[pd.Series, pd.Series]:
    """Split a complete monthly series by row count, preserving chronology."""
    series = validate_monthly_series(values, min_observations=3)
    if isinstance(train_size, bool) or not isinstance(train_size, int):
        raise TypeError("train_size must be an integer count of months")
    if train_size < 2 or train_size >= len(series):
        raise ValueError("train_size must leave at least 2 training and 1 test month")
    return series.iloc[:train_size].copy(), series.iloc[train_size:].copy()


def ar1_theoretical_moments(
    *,
    mean: float,
    phi: float,
    innovation_sd: float,
    max_lag: int,
) -> AR1Moments:
    """Compute stationary AR(1) moments for y_t-mu=phi(y_{t-1}-mu)+e_t."""
    if not np.isfinite([mean, phi, innovation_sd]).all():
        raise ValueError("mean, phi, and innovation_sd must be finite")
    if abs(phi) >= 1.0:
        raise ValueError("a stationary AR(1) requires abs(phi) < 1")
    if innovation_sd <= 0:
        raise ValueError("innovation_sd must be positive")
    if isinstance(max_lag, bool) or not isinstance(max_lag, int) or max_lag < 0:
        raise ValueError("max_lag must be a non-negative integer")
    variance = innovation_sd**2 / (1.0 - phi**2)
    autocorrelations = tuple(phi**lag for lag in range(max_lag + 1))
    autocovariances = tuple(variance * value for value in autocorrelations)
    return AR1Moments(
        mean=float(mean),
        variance=float(variance),
        autocovariances=autocovariances,
        autocorrelations=autocorrelations,
    )


def sample_acf_pacf(values: pd.Series, *, lags: int) -> pd.DataFrame:
    """Estimate ACF and PACF at lags 1..L from a complete monthly series."""
    series = validate_monthly_series(values, min_observations=8)
    if isinstance(lags, bool) or not isinstance(lags, int) or lags < 1:
        raise ValueError("lags must be a positive integer")
    if lags >= len(series) // 2:
        raise ValueError("lags must be less than half the sample length")
    autocorrelation = acf(
        series.to_numpy(), nlags=lags, adjusted=False, fft=False, missing="raise"
    )
    partial = pacf(series.to_numpy(), nlags=lags, method="ywadjusted")
    return pd.DataFrame(
        {"acf": autocorrelation[1:], "pacf": partial[1:]},
        index=pd.Index(range(1, lags + 1), name="lag_months"),
    )


def simulate_stationary_pair(
    *,
    n: int = 480,
    seed: int = 20261016,
    mean: float = 0.005,
    marginal_sd: float = 0.04,
    phi: float = 0.7,
    start: str = "1980-01",
) -> pd.DataFrame:
    """Simulate IID Gaussian and stationary AR(1) series with equal moments.

    The marginal standard deviation is matched in theory, not forced to match
    in finite samples.  ``start`` is the first monthly period.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n < 32:
        raise ValueError("n must be an integer of at least 32 months")
    if not np.isfinite([mean, marginal_sd, phi]).all():
        raise ValueError("mean, marginal_sd, and phi must be finite")
    if marginal_sd <= 0:
        raise ValueError("marginal_sd must be positive")
    if abs(phi) >= 1.0:
        raise ValueError("a stationary AR(1) requires abs(phi) < 1")
    index = pd.period_range(start=start, periods=n, freq="M")
    rng = np.random.default_rng(seed)
    white_noise = rng.normal(loc=mean, scale=marginal_sd, size=n)
    innovation_sd = marginal_sd * np.sqrt(1.0 - phi**2)
    ar_values = np.empty(n, dtype=float)
    ar_values[0] = rng.normal(loc=mean, scale=marginal_sd)
    innovations = rng.normal(loc=0.0, scale=innovation_sd, size=n - 1)
    for t in range(1, n):
        ar_values[t] = mean + phi * (ar_values[t - 1] - mean) + innovations[t - 1]
    return pd.DataFrame(
        {"iid": white_noise, "ar1": ar_values}, index=index
    )


def _validate_order(order: ARIMAOrder) -> ARIMAOrder:
    if not isinstance(order, tuple) or len(order) != 3:
        raise TypeError("order must be a three-integer tuple (p, d, q)")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in order):
        raise TypeError("ARIMA orders p, d, q must be integers")
    p, d, q = order
    if p < 0 or q < 0 or d not in {0, 1}:
        raise ValueError("p and q must be non-negative and this chapter supports d in {0, 1}")
    return order


def fit_arima(
    train: pd.Series,
    *,
    order: ARIMAOrder = (1, 0, 0),
) -> FittedARIMA:
    """Fit ARIMA on supplied monthly decimal returns, without future rows.

    The likelihood optimizer works in percentage points for conditioning;
    the wrapper exposes residuals in the original decimal-return units.
    """
    series = validate_monthly_series(train, min_observations=12)
    p, d, q = _validate_order(order)
    if len(series) <= p + q + d + 2:
        raise ValueError("training series is too short for the requested order")
    scale = 100.0
    model = ARIMA(
        series * scale,
        order=(p, d, q),
        trend="c" if d == 0 else "n",
        enforce_stationarity=True,
        enforce_invertibility=True,
        missing="raise",
    )
    result = model.fit()
    if hasattr(result, "mle_retvals") and not bool(result.mle_retvals.get("converged", True)):
        raise RuntimeError("ARIMA maximum-likelihood fit did not converge")
    return FittedARIMA(result=result, index=series.index.copy(), scale=scale)


def forecast_arima(
    train: pd.Series,
    *,
    steps: int = 1,
    order: ARIMAOrder = (1, 0, 0),
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Fit only on ``train`` and return monthly means and prediction limits."""
    series = validate_monthly_series(train, min_observations=12)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer number of months")
    if not np.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between 0 and 1")
    fitted = fit_arima(series, order=order)
    prediction = fitted.result.get_forecast(steps=steps)
    confidence = prediction.conf_int(alpha=alpha)
    index = pd.period_range(series.index[-1] + 1, periods=steps, freq="M")
    result = pd.DataFrame(
        {
            "forecast": np.asarray(prediction.predicted_mean, dtype=float) / fitted.scale,
            "lower": np.asarray(confidence.iloc[:, 0], dtype=float) / fitted.scale,
            "upper": np.asarray(confidence.iloc[:, 1], dtype=float) / fitted.scale,
        },
        index=index,
    )
    result.index.name = "target_period"
    if not np.isfinite(result.to_numpy()).all():
        raise RuntimeError("ARIMA forecast returned non-finite values")
    if not ((result["lower"] <= result["forecast"]) & (result["forecast"] <= result["upper"])).all():
        raise RuntimeError("ARIMA prediction limits do not bracket the forecast")
    return result


def training_mean_forecast(train: pd.Series, *, steps: int = 1) -> pd.Series:
    """Forecast the training-sample mean as a simple return-series baseline."""
    series = validate_monthly_series(train, min_observations=2)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer number of months")
    index = pd.period_range(series.index[-1] + 1, periods=steps, freq="M")
    return pd.Series(series.mean(), index=index, name="training_mean_forecast")


def rolling_origin_forecast(
    values: pd.Series,
    *,
    initial_train_size: int,
    order: ARIMAOrder = (1, 0, 0),
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Generate one-step forecasts from expanding, past-only training windows."""
    series = validate_monthly_series(values, min_observations=14)
    _validate_order(order)
    if isinstance(initial_train_size, bool) or not isinstance(initial_train_size, int):
        raise TypeError("initial_train_size must be an integer count of months")
    if initial_train_size < 12 or initial_train_size >= len(series):
        raise ValueError("initial_train_size must be at least 12 and leave a test month")
    rows: list[dict[str, Any]] = []
    for target_pos in range(initial_train_size, len(series)):
        train = series.iloc[:target_pos]
        prediction = forecast_arima(train, steps=1, order=order, alpha=alpha).iloc[0]
        rows.append(
            {
                "origin_period": train.index[-1],
                "actual": float(series.iloc[target_pos]),
                "forecast": float(prediction["forecast"]),
                "lower": float(prediction["lower"]),
                "upper": float(prediction["upper"]),
            }
        )
    result = pd.DataFrame(rows, index=series.index[initial_train_size:].copy())
    result.index.name = "target_period"
    return result


def ljung_box_diagnostic(
    residuals: pd.Series,
    *,
    model_df: int,
    lag: int,
) -> pd.DataFrame:
    """Test joint residual autocorrelation through one chosen monthly lag."""
    values = validate_monthly_series(residuals, min_observations=8)
    if isinstance(model_df, bool) or not isinstance(model_df, int) or model_df < 0:
        raise ValueError("model_df must be a non-negative integer")
    if isinstance(lag, bool) or not isinstance(lag, int) or lag <= model_df:
        raise ValueError("lag must be an integer greater than model_df")
    if lag >= len(values):
        raise ValueError("lag must be smaller than the residual sample length")
    return acorr_ljungbox(
        values.to_numpy(), lags=[lag], model_df=model_df, return_df=True
    )


__all__ = [
    "AR1Moments",
    "FittedARIMA",
    "ar1_theoretical_moments",
    "fit_arima",
    "forecast_arima",
    "ljung_box_diagnostic",
    "rolling_origin_forecast",
    "sample_acf_pacf",
    "simulate_stationary_pair",
    "split_monthly_series",
    "training_mean_forecast",
    "validate_monthly_series",
]
