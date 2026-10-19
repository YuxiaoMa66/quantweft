"""Beta estimation and betting-against-beta (BAB) building blocks for Chapter 27.

Follows Frazzini and Pedersen (draft of 2013-05-10): beta = rho * sigma_i / sigma_m with separate volatility and
correlation windows (eq. 14), Vasicek-style shrinkage toward 1 (eq. 15), rank-weighted low-beta / high-beta legs
(eq. 16) and the beta-neutral self-financing BAB return (eq. 17). A row labelled ``s`` uses information up to the end
of month ``s``; the BAB return in that row is earned during month ``s + 1`` (same convention as ``momentum``).
All returns are *excess* returns over the risk-free rate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant_course.factor_research import (
    _contiguous_periods, _panel, _positive_int, lead_return, rank_cross_section,
)

__all__ = ["rolling_beta", "vol_corr_beta", "vasicek_shrink", "bab_weights", "bab_returns", "state_beta"]


def _market(market: pd.Series, assets: pd.DataFrame) -> pd.Series:
    if not isinstance(market, pd.Series):
        raise TypeError("market must be a pandas Series")
    if market.dtype.kind not in "iuf" or not np.isfinite(market.to_numpy(dtype=float)).all():
        raise ValueError("market must be real finite numeric with no missing months")
    if not market.index.equals(assets.index):
        raise ValueError("market and assets must have identical row labels")
    return market.astype(float)


def rolling_beta(assets: pd.DataFrame, market: pd.Series, *, window: int, min_periods: int) -> pd.DataFrame:
    """OLS slope Cov(r_i, r_m) / Var(r_m) over rows s-window+1..s, using months where the asset is observed."""
    a = _panel(assets, "assets")
    m = _market(market, a)
    window = _positive_int(window, "window", minimum=3)
    min_periods = _positive_int(min_periods, "min_periods", minimum=3)
    if min_periods > window:
        raise ValueError("min_periods must not exceed window")
    out = {}
    for c in a.columns:
        mm = m.where(a[c].notna())
        cov = a[c].rolling(window, min_periods=min_periods).cov(mm)
        var = mm.rolling(window, min_periods=min_periods).var()
        out[c] = cov / var.where(var > 0)
    return pd.DataFrame(out, index=a.index)


def vol_corr_beta(assets: pd.DataFrame, market: pd.Series, *, vol_window: int = 12, corr_window: int = 60,
                  min_vol: int = 12, min_corr: int = 36) -> pd.DataFrame:
    """beta = rho * sigma_i / sigma_m with volatility over ``vol_window`` months and correlation over ``corr_window``.

    Monthly analogue of Frazzini-Pedersen eq. (14) (they use daily data when available; their monthly fallback is the
    1- and 5-year windows with at least 12 and 36 observations, which are the defaults here).
    """
    a = _panel(assets, "assets")
    m = _market(market, a)
    vol_window = _positive_int(vol_window, "vol_window", minimum=3)
    corr_window = _positive_int(corr_window, "corr_window", minimum=3)
    min_vol = _positive_int(min_vol, "min_vol", minimum=3)
    min_corr = _positive_int(min_corr, "min_corr", minimum=3)
    if min_vol > vol_window or min_corr > corr_window:
        raise ValueError("a minimum observation count must not exceed its window")
    out = {}
    for c in a.columns:
        mm_v = m.where(a[c].notna())
        sig_i = a[c].rolling(vol_window, min_periods=min_vol).std()
        sig_m = mm_v.rolling(vol_window, min_periods=min_vol).std()
        mm_c = m.where(a[c].notna())
        rho = a[c].rolling(corr_window, min_periods=min_corr).corr(mm_c)
        out[c] = rho * sig_i / sig_m.where(sig_m > 0)
    return pd.DataFrame(out, index=a.index)


def vasicek_shrink(beta: pd.DataFrame | pd.Series, weight: float = 0.6, prior: float = 1.0):
    """w * beta + (1 - w) * prior, eq. (15) with the paper's constants (w = 0.6, prior = 1) as defaults.

    A common weight does not change the ranks of the betas, only the leverage ratios used to scale the legs.
    """
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0.0 <= weight <= 1.0:
        raise ValueError("weight must be a real number in [0, 1]")
    if isinstance(prior, bool) or not isinstance(prior, (int, float)) or not np.isfinite(prior):
        raise ValueError("prior must be a finite real number")
    return weight * beta + (1.0 - weight) * float(prior)


def bab_weights(beta_row: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Eq. (16): w_H = k (z - zbar)^+, w_L = k (z - zbar)^-, z = average-tie rank of beta, k = 2 / sum|z - zbar|.

    Each leg sums to 1 (the low-beta leg overweights the lowest betas, the high-beta leg the highest). Securities with
    a missing beta get weight 0 and are not counted in n. Raises when fewer than two securities are ranked or all
    ranks tie.
    """
    if not isinstance(beta_row, pd.Series):
        raise TypeError("beta_row must be a pandas Series")
    z = pd.Series(rank_cross_section(beta_row.to_numpy()), index=beta_row.index)
    ok = z.notna()
    if ok.sum() < 2:
        raise ValueError("need at least two securities with a beta")
    dev = z - z[ok].mean()
    scale = dev[ok].abs().sum()
    if scale == 0:
        raise ValueError("all betas tie: the low/high legs are undefined")
    k = 2.0 / scale
    high = (k * dev.clip(lower=0.0)).where(ok, 0.0)
    low = (k * (-dev).clip(lower=0.0)).where(ok, 0.0)
    return low, high


def bab_returns(excess_returns: pd.DataFrame, betas: pd.DataFrame, *, borrow_spread: float = 0.0) -> pd.DataFrame:
    """Eq. (17) month by month: r_BAB = (r_L - rf)/beta_L - (r_H - rf)/beta_H, returned in excess form.

    ``betas`` are the (already shrunk) betas known at the end of month s; legs are weighted by ``bab_weights`` and
    paired with the *next* month's excess return. ``beta_L`` / ``beta_H`` are the legs' weighted betas and must be
    positive. ``borrow_spread`` (per month) is charged on leverage above one on each leg: the long leg borrows
    max(1/beta_L - 1, 0), the short leg max(1/beta_H - 1, 0). Rows with fewer than two betas stay NaN; a nonzero weight
    on a missing next-month return raises.
    """
    r = _panel(excess_returns, "excess_returns")
    b = _panel(betas, "betas")
    if not r.index.equals(b.index) or not r.columns.equals(b.columns):
        raise ValueError("excess_returns and betas must have identical labels")
    _contiguous_periods(r, "excess_returns")
    if isinstance(borrow_spread, bool) or not isinstance(borrow_spread, (int, float)) or not np.isfinite(borrow_spread) or borrow_spread < 0:
        raise ValueError("borrow_spread must be a finite non-negative number")
    nxt = lead_return(r, 1)
    cols = ["bab", "long_leg", "short_leg", "beta_low", "beta_high", "long_leverage", "short_leverage"]
    out = pd.DataFrame(np.nan, index=r.index, columns=cols)
    for s in r.index:
        row = b.loc[s]
        if row.notna().sum() < 2:
            continue
        w_low, w_high = bab_weights(row)
        used = (w_low > 0) | (w_high > 0)
        future = nxt.loc[s]
        if future[used].isna().any():
            if s == r.index[-1]:
                continue                      # the final row has no next month by construction
            raise ValueError(f"a held security has no return in the month after {s}")
        beta_l = float((w_low * row.fillna(0.0)).sum())
        beta_h = float((w_high * row.fillna(0.0)).sum())
        if beta_l <= 0 or beta_h <= 0:
            raise ValueError(f"leg beta must be positive to lever it to one (month {s})")
        r_l = float((w_low * future.fillna(0.0)).sum())
        r_h = float((w_high * future.fillna(0.0)).sum())
        cost = borrow_spread * (max(1.0 / beta_l - 1.0, 0.0) + max(1.0 / beta_h - 1.0, 0.0))
        out.loc[s] = [r_l / beta_l - r_h / beta_h - cost, r_l, r_h, beta_l, beta_h, 1.0 / beta_l, 1.0 / beta_h]
    return out


def state_beta(asset: pd.Series, market: pd.Series, condition: pd.Series) -> dict[str, float]:
    """OLS slope and intercept of ``asset`` on ``market`` within the months where the boolean ``condition`` holds."""
    for name, s in (("asset", asset), ("market", market)):
        if not isinstance(s, pd.Series) or s.dtype.kind not in "iuf":
            raise TypeError(f"{name} must be a real numeric pandas Series")
    if not isinstance(condition, pd.Series) or condition.dtype != bool:
        raise TypeError("condition must be a boolean pandas Series")
    if not (asset.index.equals(market.index) and asset.index.equals(condition.index)):
        raise ValueError("asset, market and condition must share one index")
    keep = condition & asset.notna() & market.notna()
    x = market[keep].to_numpy(dtype=float)
    y = asset[keep].to_numpy(dtype=float)
    if len(x) < 3 or np.ptp(x) == 0:
        raise ValueError("need at least three months with a varying market return")
    slope = float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1))
    return {"slope": slope, "intercept": float(y.mean() - slope * x.mean()), "months": int(len(x))}
