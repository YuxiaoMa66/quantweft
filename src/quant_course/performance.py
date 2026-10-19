"""Return-path metrics with explicit units and missing-data contracts.

These functions consume ordered, equal-length return intervals in decimal
units. They do not infer a trading calendar, create prices, fill gaps, or
establish point-in-time availability. Clock and source-version checks belong
to the caller. Square-root annualization is a stated convention, not a
general theorem for serially dependent or nonstationary returns.
"""
from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def _real_vector(values: ArrayLike, name: str) -> FloatArray:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional vector")
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numeric values, not bool or complex")
    array = raw.astype(np.float64, copy=True)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite values; gaps cannot be silently dropped")
    return array


def _positive(value: float, name: str) -> float:
    raw = np.asarray(value)
    if raw.ndim != 0 or raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must be a real scalar")
    number = float(raw)
    if not np.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return number


def _simple_returns(values: ArrayLike) -> FloatArray:
    array = _real_vector(values, "returns")
    if (array < -1).any():
        raise ValueError("simple returns below -100% require a separate negative-wealth model")
    return array


def wealth_index(returns: ArrayLike, initial_capital: float = 1.0) -> FloatArray:
    """Compound simple decimal returns, including capital before return 1.

    Output length is N+1. The caller supplies the corresponding initial
    timestamp and N interval-end timestamps. No external contributions or
    withdrawals are allowed. A -100% return sends wealth to zero; subsequent
    multiplicative returns cannot revive an unfunded bankrupt account.
    """
    array = _simple_returns(returns)
    capital = _positive(initial_capital, "initial_capital")
    with np.errstate(over="ignore", invalid="ignore"):
        path = capital * np.concatenate(([1.0], np.cumprod(1.0 + array)))
    if not np.isfinite(path).all():
        raise ValueError("compounded wealth is outside finite float64 range")
    return path


def geometric_mean_return(returns: ArrayLike) -> float:
    """Per-interval geometric mean for equal-length simple-return intervals."""
    array = _simple_returns(returns)
    if (array == -1).any():
        return -1.0
    with np.errstate(over="ignore"):
        mean = float(np.expm1(np.log1p(array).mean()))
    if not np.isfinite(mean):
        raise ValueError("geometric return is outside finite float64 range")
    return mean


def cagr(initial_wealth: float, final_wealth: float, elapsed_years: float) -> float:
    """Endpoint compound growth per year, using caller-defined elapsed years.

    No external cash flows. Zero final wealth gives -100%; positive initial
    wealth is required. This function does not replace time-weighted or
    money-weighted return calculations for an account with external flows.
    """
    initial = _positive(initial_wealth, "initial_wealth")
    years = _positive(elapsed_years, "elapsed_years")
    raw = np.asarray(final_wealth)
    if raw.ndim != 0 or raw.dtype.kind not in "iuf":
        raise TypeError("final_wealth must be a real scalar")
    final = float(raw)
    if not np.isfinite(final) or final < 0:
        raise ValueError("final_wealth must be nonnegative and finite")
    if final == 0:
        return -1.0
    with np.errstate(over="ignore"):
        result = float(np.expm1((np.log(final) - np.log(initial)) / years))
    if not np.isfinite(result):
        raise ValueError("CAGR is outside finite float64 range")
    return result


def drawdown_path(wealth: ArrayLike) -> FloatArray:
    """Negative drawdown with positive included initial capital; zero allowed.

    This is the nonnegative-wealth extension of the earlier positive-only
    Series API. Index validation remains the caller's responsibility.
    """
    path = _real_vector(wealth, "wealth")
    if path[0] <= 0 or (path < 0).any():
        raise ValueError("wealth must start positive and remain nonnegative")
    return path / np.maximum.accumulate(path) - 1.0


def annualized_volatility(returns: ArrayLike, periods_per_year: float) -> float:
    """Sample SD (ddof=1) times sqrt(A), a stated equal-interval convention.

    For additive increments, exact variance aggregation additionally requires
    suitable identical variance and zero cross-covariance assumptions. For
    compounded simple returns this is not an exact annual-return SD identity.
    """
    array = _simple_returns(returns)
    annual_periods = _positive(periods_per_year, "periods_per_year")
    if array.size < 2:
        raise ValueError("sample volatility needs at least two observations")
    with np.errstate(over="ignore", invalid="ignore"):
        result = float(np.std(array, ddof=1) * np.sqrt(annual_periods))
    if not np.isfinite(result):
        raise ValueError("volatility is outside finite float64 range")
    return result


def sharpe_ratio(
    returns: ArrayLike,
    risk_free_returns: ArrayLike,
    periods_per_year: float,
) -> float:
    """Annualized convention: sqrt(A) * mean(R-RF) / sample_SD(R-RF).

    RF must be a same-length vector of same-interval simple decimal returns;
    callers explicitly expand any genuinely constant RF. No implicit date
    alignment, scalar broadcasting, frequency conversion or gap dropping.
    Zero excess-return SD is undefined and raises ValueError. This is not a
    serial-correlation-adjusted Sharpe estimator or a strategy-validity test.
    """
    array = _simple_returns(returns)
    risk_free = _simple_returns(risk_free_returns)
    annual_periods = _positive(periods_per_year, "periods_per_year")
    if array.shape != risk_free.shape:
        raise ValueError("returns and RF must have identical interval counts")
    if array.size < 2:
        raise ValueError("Sharpe needs at least two observations")
    with np.errstate(over="ignore", invalid="ignore"):
        excess = array - risk_free
        deviation = float(np.std(excess, ddof=1))
        result = float(np.sqrt(annual_periods) * excess.mean() / deviation) if deviation > 0 else np.nan
    if not np.isfinite(deviation):
        raise ValueError("excess-return volatility exceeds finite float64 range")
    if deviation == 0:
        raise ValueError("Sharpe is undefined for zero excess-return volatility")
    if not np.isfinite(result):
        raise ValueError("Sharpe inputs or result exceed finite float64 range")
    return result
