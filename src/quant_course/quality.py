"""Quality (profitability, leverage, accruals, stability) field definitions for Chapter 26.

Every function takes date x asset panels built from ONE filing version per cell (see ``factor_signals.latest_available_values``):
numerator and denominator must come from the same version, never a restated numerator over an older denominator.
Ratios return NaN, not zero or infinity, where a denominator is not usable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant_course.factor_research import _panel, _positive_int

__all__ = ["average_balance", "guarded_ratio", "dupont", "gross_profit_to_assets", "operating_profitability",
           "accrual_ratio", "leverage_ratio", "earnings_stability", "roe_from_leverage"]


def _same(*frames: tuple[str, pd.DataFrame]) -> list[pd.DataFrame]:
    checked = [_panel(f, name) for name, f in frames]
    for (name, _), f in zip(frames[1:], checked[1:]):
        if not f.index.equals(checked[0].index) or not f.columns.equals(checked[0].columns):
            raise ValueError(f"{name} must have the same index and columns as {frames[0][0]}")
    return checked


def average_balance(current: pd.DataFrame, previous: pd.DataFrame, *, floor: float | None = None) -> pd.DataFrame:
    """(current + previous) / 2 where both fiscal-year-end balances exist (both come from the same filing: a 10-K reports both).

    With ``floor`` given, NaN wherever either balance is not strictly above it (use ``floor=0.0`` for equity): averaging a
    negative year-end balance with a positive one can give a positive "average" that hides insolvency.
    """
    c, p = _same(("current", current), ("previous", previous))
    avg = (c + p) / 2.0
    if floor is None:
        return avg
    if isinstance(floor, bool) or not isinstance(floor, (int, float)) or not np.isfinite(floor):
        raise ValueError("floor must be a finite number")
    return avg.where((c > floor) & (p > floor))


def guarded_ratio(numerator: pd.DataFrame, denominator: pd.DataFrame, *, floor: "pd.DataFrame | float" = 0.0) -> pd.DataFrame:
    """numerator / denominator, NaN where the denominator is not strictly above ``floor`` or an input is missing.

    ``floor`` can be a number or a panel (for example 2% of assets for equity): a denominator close to zero turns a
    ratio into noise, and a negative one turns it into a sign error. The numerator keeps its sign.
    """
    n, d = _same(("numerator", numerator), ("denominator", denominator))
    if isinstance(floor, pd.DataFrame):
        (f,) = _same(("denominator", d), ("floor", floor))[1:]
        threshold = f
    elif isinstance(floor, bool) or not isinstance(floor, (int, float)) or not np.isfinite(floor) or floor < 0:
        raise ValueError("floor must be a non-negative finite number or a panel")
    else:
        threshold = float(floor)
    return (n / d).where((d > threshold) & (d > 0.0))        # a panel floor can be negative; the denominator must still be positive


def dupont(net_income: pd.DataFrame, sales: pd.DataFrame, assets: pd.DataFrame, equity: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """ROE = (NI/Sales) * (Sales/Assets) * (Assets/Equity).

    Each component is NaN unless the inputs it uses are strictly positive (margin: sales; turnover: sales and assets;
    multiplier: assets and equity); ``roe`` is NaN unless sales, assets and equity are all positive.
    Returns net margin, asset turnover, equity multiplier (leverage) and their product ``roe``. Use one filing version for all
    four panels and the same balance convention (ending or average) for assets and equity.
    """
    ni, s, a, e = _same(("net_income", net_income), ("sales", sales), ("assets", assets), ("equity", equity))
    s, a, e = s.where(s > 0.0), a.where(a > 0.0), e.where(e > 0.0)     # every component, not only the final ROE, is NaN unless all three are positive
    margin = guarded_ratio(ni, s)
    turnover = guarded_ratio(s, a)
    multiplier = guarded_ratio(a, e)
    return {"net_margin": margin, "asset_turnover": turnover, "equity_multiplier": multiplier, "roe": margin * turnover * multiplier}


def gross_profit_to_assets(revenue: pd.DataFrame, cogs: pd.DataFrame, assets: pd.DataFrame) -> pd.DataFrame:
    """(revenue - cost of goods sold) / total assets (Novy-Marx scales by assets so that interest does not enter).

    The function does not average: pass average assets if that is the definition in use.
    """
    r, c, a = _same(("revenue", revenue), ("cogs", cogs), ("assets", assets))
    return guarded_ratio(r - c, a)


def operating_profitability(revenue: pd.DataFrame, cogs: pd.DataFrame, sga: pd.DataFrame, interest: pd.DataFrame,
                            book_equity: pd.DataFrame) -> pd.DataFrame:
    """Fama-French (2015) OP: (revenue - COGS - SG&A - interest expense) / book equity; positive book equity only.

    The published factor requires revenue and at least one cost item; this function requires all four numerators so that a
    missing cost does not silently raise profitability.
    """
    r, c, g, i, e = _same(("revenue", revenue), ("cogs", cogs), ("sga", sga), ("interest", interest), ("book_equity", book_equity))
    return guarded_ratio(r - c - g - i, e)


def accrual_ratio(net_income: pd.DataFrame, cfo: pd.DataFrame, assets: pd.DataFrame) -> pd.DataFrame:
    """(net income - net cash flow from operating activities) / assets: the accrual gap between earnings and operating cash flow.

    Higher = lower earnings quality under the accrual hypothesis. The function does not average: pass average assets.
    """
    ni, cf, a = _same(("net_income", net_income), ("cfo", cfo), ("assets", assets))
    return guarded_ratio(ni - cf, a)


def leverage_ratio(debt: pd.DataFrame, assets: pd.DataFrame) -> pd.DataFrame:
    """debt / total assets, defined for strictly positive assets; debt must not be negative."""
    d, a = _same(("debt", debt), ("assets", assets))
    if (d.to_numpy()[~np.isnan(d.to_numpy())] < 0).any():
        raise ValueError("debt must not be negative")
    return guarded_ratio(d, a)


def earnings_stability(history: pd.DataFrame, *, window: int = 5, min_years: int | None = None) -> pd.Series:
    """Sample standard deviation (ddof=1) of the last ``window`` rows of an annual ratio history, per asset (rows = fiscal years, oldest first).

    NaN when fewer than ``min_years`` (default ``window``) valid values exist. Lower is more stable. The history must have been built
    from versions known at the signal time; this function cannot check that.
    """
    window = _positive_int(window, "window", minimum=2)
    min_years = window if min_years is None else _positive_int(min_years, "min_years", minimum=2)
    if min_years > window:
        raise ValueError("min_years must not exceed window")
    h = _panel(history, "history").iloc[-window:]
    out = h.std(ddof=1)
    return out.where(h.notna().sum() >= min_years)


def roe_from_leverage(operating_return: float, after_tax_cost_of_debt: float, debt_to_equity: float) -> float:
    """ROE = rho + (rho - i) * D/E for operating return on assets rho, after-tax cost of debt i, and E = A - D > 0."""
    values = (operating_return, after_tax_cost_of_debt, debt_to_equity)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) for v in values):
        raise ValueError("inputs must be finite real numbers")
    if debt_to_equity < 0:
        raise ValueError("debt_to_equity must not be negative")
    return operating_return + (operating_return - after_tax_cost_of_debt) * debt_to_equity
