"""CAPM relationships and transparent single-factor teaching calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CAPMFit:
    """OLS point estimates for a single asset excess return and market excess return."""

    alpha: float
    beta: float
    r_squared: float
    nobs: int
    residuals: tuple[float, ...]
    fitted_excess_returns: tuple[float, ...]
    market_excess_mean: float
    asset_excess_mean: float


def _real_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional vector")
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numeric values")
    result = raw.astype(float, copy=True)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite; missing values are not dropped")
    return result


def beta_from_covariance(
    asset_excess: Sequence[float] | np.ndarray,
    market_excess: Sequence[float] | np.ndarray,
) -> float:
    """Return sample covariance(asset, market) / sample variance(market)."""

    asset = _real_vector(asset_excess, "asset_excess")
    market = _real_vector(market_excess, "market_excess")
    if asset.size != market.size or asset.size < 2:
        raise ValueError("asset and market vectors must have the same length of at least 2")
    market_variance = float(np.var(market, ddof=1))
    if market_variance <= 0:
        raise ValueError("market excess return must have positive sample variance")
    covariance = float(np.cov(asset, market, ddof=1)[0, 1])
    return covariance / market_variance


def capm_expected_return(
    risk_free_return: float,
    beta: float,
    expected_market_return: float,
) -> float:
    """Apply CAPM to same-horizon expected simple returns in decimal units."""

    values = np.asarray([risk_free_return, beta, expected_market_return])
    if values.dtype.kind not in "iuf" or not np.isfinite(values).all():
        raise ValueError("CAPM inputs must be finite real scalars")
    rf, exposure, market_mean = map(float, values)
    return rf + exposure * (market_mean - rf)


def fit_capm_excess(
    asset_excess: pd.Series | Sequence[float] | np.ndarray,
    market_excess: pd.Series | Sequence[float] | np.ndarray,
) -> CAPMFit:
    """Fit the intercept and beta by the one-predictor OLS identities.

    This small core calculation returns point estimates only. Time-indexed
    inference belongs to the monthly factor-model helper or the chapter 8
    equal-spacing regression helper, as appropriate for the observation clock.
    """

    if isinstance(asset_excess, pd.Series) != isinstance(market_excess, pd.Series):
        raise TypeError("asset_excess and market_excess must both be Series or both be arrays")
    if isinstance(asset_excess, pd.Series) and isinstance(market_excess, pd.Series):
        if not asset_excess.index.equals(market_excess.index):
            raise ValueError("asset and market observation indexes must match exactly")
    asset = _real_vector(
        asset_excess.to_numpy() if isinstance(asset_excess, pd.Series) else asset_excess,
        "asset_excess",
    )
    market = _real_vector(
        market_excess.to_numpy() if isinstance(market_excess, pd.Series) else market_excess,
        "market_excess",
    )
    if asset.size != market.size or asset.size < 3:
        raise ValueError("CAPM requires aligned asset and market samples with at least 3 rows")
    beta = beta_from_covariance(asset, market)
    alpha = float(asset.mean() - beta * market.mean())
    fitted = alpha + beta * market
    residuals = asset - fitted
    total_sum_squares = float(np.square(asset - asset.mean()).sum())
    if total_sum_squares <= 0:
        raise ValueError("R-squared is undefined for a constant asset excess-return sample")
    r_squared = 1.0 - float(np.square(residuals).sum()) / total_sum_squares
    return CAPMFit(
        alpha=alpha,
        beta=beta,
        r_squared=r_squared,
        nobs=len(asset),
        residuals=tuple(float(value) for value in residuals),
        fitted_excess_returns=tuple(float(value) for value in fitted),
        market_excess_mean=float(market.mean()),
        asset_excess_mean=float(asset.mean()),
    )


def fit_capm(
    asset_returns: pd.Series,
    market_excess: pd.Series,
    risk_free_returns: pd.Series,
) -> CAPMFit:
    """Fit CAPM point estimates after subtracting same-interval RF once."""

    if not all(
        isinstance(item, pd.Series)
        for item in (asset_returns, market_excess, risk_free_returns)
    ):
        raise TypeError("asset_returns, market_excess, and risk_free_returns must be Series")
    if not asset_returns.index.equals(market_excess.index) or not asset_returns.index.equals(
        risk_free_returns.index
    ):
        raise ValueError("asset, market excess, and RF indexes must match exactly")
    asset = _real_vector(asset_returns.to_numpy(), "asset_returns")
    market = _real_vector(market_excess.to_numpy(), "market_excess")
    risk_free = _real_vector(risk_free_returns.to_numpy(), "risk_free_returns")
    return fit_capm_excess(
        pd.Series(asset - risk_free, index=asset_returns.index, name="asset_excess"),
        pd.Series(market, index=market_excess.index, name="market_excess"),
    )


def constructed_two_asset_sample() -> pd.DataFrame:
    """Return four deliberately constructed, unweighted observations."""

    risk_free = np.full(4, 0.02)
    market_excess = np.array([-0.04, 0.01, 0.11, 0.16])
    centered_market = market_excess - market_excess.mean()
    residual = np.array([0.01, -0.02, 0.02, -0.01])
    asset_a = 0.07 + 0.5 * centered_market + residual
    asset_b = 0.07 + 1.5 * centered_market + residual
    return pd.DataFrame(
        {
            "RF": risk_free,
            "Mkt-RF": market_excess,
            "Asset_A": asset_a,
            "Asset_B": asset_b,
            "constructed_residual": residual,
        },
        index=pd.Index(["row_1", "row_2", "row_3", "row_4"], name="constructed_row"),
    )
