"""Momentum strategy building blocks for Chapter 25.

Windows come from ``factor_signals.formation_return`` (a signal at month s uses only months <= s - skip).
A weights row labelled ``s`` is the *target* portfolio decided at the end of month ``s`` and held during month ``s + 1``;
``strategy_returns`` pairs it with the next month's return and refuses to hide a missing return behind a zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant_course.factor_research import (
    _contiguous_periods, _nonneg_int, _panel, _positive_int, lead_return, quantile_long_short_weights,
)
from quant_course.factor_signals import formation_return

__all__ = ["cross_sectional_momentum_weights", "blend_vintages", "time_series_sign", "ex_ante_volatility",
           "tsmom_weights", "strategy_returns", "net_of_costs", "trailing_bear_state"]


def cross_sectional_momentum_weights(returns: pd.DataFrame, *, window: int, skip: int, n_buckets: int,
                                     hold_months: int = 1) -> pd.DataFrame:
    """Long the top bucket / short the bottom bucket of the formation return; ``hold_months`` overlapping vintages.

    Each month a new vintage (+1/n_top, -1/n_bottom) is formed from ``formation_return(returns, window, skip)`` and held for
    ``hold_months`` months; the portfolio is the average of the latest ``hold_months`` vintages (Jegadeesh-Titman style,
    1/K of the book is revised each month). Rows before ``hold_months`` vintages exist are NaN.
    """
    signal = formation_return(returns, window, skip)
    vintage = quantile_long_short_weights(signal, n_buckets)
    vintage[signal.notna().sum(axis=1) < n_buckets] = np.nan   # too few ranked assets to fill every bucket: undefined, not "flat"
    return blend_vintages(vintage, hold_months)


def blend_vintages(weights: pd.DataFrame, hold_months: int) -> pd.DataFrame:
    """Average of the latest ``hold_months`` rows of target weights; NaN until that many rows exist."""
    hold = _positive_int(hold_months, "hold_months")
    w = _panel(weights, "weights")
    return w.rolling(hold, min_periods=hold).mean()


def time_series_sign(excess_returns: pd.DataFrame, *, window: int, skip: int = 0) -> pd.DataFrame:
    """+1 / -1 / 0 by the sign of the asset's *own* compounded excess return over the formation window; NaN if undefined.

    Moskowitz-Ooi-Pedersen (2012, eq. 5) use the past 12 months including the latest month (``skip=0``).
    """
    past = formation_return(excess_returns, window, skip)
    return np.sign(past)


def ex_ante_volatility(returns: pd.DataFrame, *, window: int = 36, min_periods: int = 12, periods_per_year: int = 12) -> pd.DataFrame:
    """Annualized rolling standard deviation of monthly returns known at the end of month s (rows s-window+1..s).

    A monthly stand-in for the exponentially weighted daily estimator of the original paper (not the same estimator).
    """
    window = _positive_int(window, "window")
    min_periods = _positive_int(min_periods, "min_periods", minimum=2)
    if min_periods > window:
        raise ValueError("min_periods must not exceed window")
    r = _panel(returns, "returns")
    _contiguous_periods(r, "returns")
    return r.rolling(window, min_periods=min_periods).std(ddof=1) * np.sqrt(periods_per_year)


def tsmom_weights(signal: pd.DataFrame, volatility: pd.DataFrame, *, target_vol: float = 0.40) -> pd.DataFrame:
    """Position of asset i = signal * target_vol / vol, divided by the number of assets with a valid signal and vol.

    Each instrument alone would run at ``target_vol`` annualized ex-ante risk; the equal-weight average over the
    ``S_t`` valid instruments is the diversified portfolio. Non-positive volatility is rejected.
    """
    if isinstance(target_vol, bool) or not isinstance(target_vol, (int, float)) or not np.isfinite(target_vol) or target_vol <= 0:
        raise ValueError("target_vol must be a positive finite number")
    s, v = _panel(signal, "signal"), _panel(volatility, "volatility")
    if not s.index.equals(v.index) or not s.columns.equals(v.columns):
        raise ValueError("signal and volatility must share index and columns")
    if (v.to_numpy()[~np.isnan(v.to_numpy())] <= 0).any():
        raise ValueError("volatility must be strictly positive")
    raw = s * target_vol / v
    count = raw.notna().sum(axis=1).replace(0, np.nan)
    return raw.div(count, axis=0)


def strategy_returns(weights: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    """Return of the portfolio decided at the end of month s, earned in month s+1 (gross, no costs).

    A row whose weights are all NaN gives NaN. A NaN weight on one asset of a partly valid row means "not in the
    portfolio this month" and contributes 0 (``tsmom_weights`` has already divided by the number of valid assets).
    A *nonzero* weight on an asset whose next-month return is missing raises: silently treating it as zero would hide
    the loss of a position.
    """
    w = _panel(weights, "weights")
    label = lead_return(returns, 1).reindex(index=w.index, columns=w.columns)
    out = []
    for date in w.index:
        wr, rr = w.loc[date].to_numpy(), label.loc[date].to_numpy()
        if np.isnan(wr).all():
            out.append(np.nan); continue
        if np.isnan(rr).all():
            out.append(np.nan); continue
        bad = (np.nan_to_num(wr) != 0) & np.isnan(rr)
        if bad.any():
            raise ValueError(f"nonzero weight on an asset without a next-month return at {date}")
        out.append(float(np.nansum(np.nan_to_num(wr) * np.nan_to_num(rr))))
    return pd.Series(out, index=w.index, name="gross_return")


def net_of_costs(gross: pd.Series, weights: pd.DataFrame, *, cost_per_unit: float) -> pd.Series:
    """gross - cost_per_unit * sum|w_s - w_{s-1}| (target-to-target, buys plus sells, drift ignored); first row NaN."""
    if isinstance(cost_per_unit, bool) or not isinstance(cost_per_unit, (int, float)) or not np.isfinite(cost_per_unit) or cost_per_unit < 0:
        raise ValueError("cost_per_unit must be a non-negative finite number")
    w = _panel(weights, "weights")
    if not isinstance(gross, pd.Series) or not gross.index.equals(w.index):
        raise ValueError("gross and weights must share an identical row index")
    turnover = w.diff().abs().sum(axis=1, min_count=1)
    return (gross - cost_per_unit * turnover).rename("net_return")


def trailing_bear_state(market_total_returns: pd.Series, *, window: int = 24) -> pd.Series:
    """1.0 if the compounded market total return over the latest ``window`` months (including month s) is negative, else 0.0.

    The state at the end of month s uses months s-window+1..s only. NaN until ``window`` months exist.
    """
    window = _positive_int(window, "window")
    m = market_total_returns.astype(float)
    if not isinstance(m.index, pd.PeriodIndex) or not m.index.equals(pd.period_range(m.index[0], m.index[-1], freq=m.index.freq)):
        raise ValueError("market returns need a contiguous PeriodIndex")
    if (m < -1).any() or np.isinf(m).any():
        raise ValueError("market returns must be finite simple returns >= -100%")
    cumulative = np.expm1(np.log1p(m).rolling(window, min_periods=window).sum())
    return (cumulative < 0).astype(float).where(cumulative.notna())
