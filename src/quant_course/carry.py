"""Carry arithmetic for Chapter 27: FX forwards, zero-coupon bond roll-down, commodity curves, futures rolls.

Carry follows Koijen-Moskowitz-Pedersen-Vrugt (NBER w19325, eq. 4-5, 7, 9-10, 13-15): the return an instrument earns
if its market conditions (spot price, yield curve) stay unchanged. Prices must be positive; array-likes are matched by
position (not by index label) and a scalar input returns a Python float.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant_course.factor_research import _panel

__all__ = ["futures_carry", "forward_premium", "fx_carry_from_rates", "commodity_curve_carry", "zero_coupon_carry",
           "roll_down_approximation", "portfolio_carry", "held_contract_returns", "naive_splice_returns"]


def _real(values: object, name: str, *, positive: bool = False, above: float | None = None) -> np.ndarray:
    a = np.asarray(values)
    if a.dtype.kind not in "iuf":
        raise TypeError(f"{name} must be real numeric (no bool/text/complex/object)")
    a = a.astype(float)
    if not np.isfinite(a).all():
        raise ValueError(f"{name} must be finite")
    if positive and (a <= 0).any():
        raise ValueError(f"{name} must be positive")
    if above is not None and (a <= above).any():
        raise ValueError(f"{name} must exceed {above}")
    return a


def _out(a: np.ndarray):
    return float(a) if a.ndim == 0 else a


def futures_carry(spot: object, futures: object, collateral: object | None = None):
    """C = (S - F) / X, KMPV eq. (4); ``collateral`` X defaults to F (fully collateralised, eq. 5).

    S, F and X are prices in the same units (quote currency per unit of the underlying). The result is the return over
    the futures' remaining life if the spot price does not move; the caller converts it to the holding period wanted.
    """
    s = _real(spot, "spot", positive=True)
    f = _real(futures, "futures", positive=True)
    x = f if collateral is None else _real(collateral, "collateral", positive=True)
    return _out((s - f) / x)


def forward_premium(spot: object, forward: object):
    """F / S - 1: positive when the forward price of the underlying is above its spot price."""
    s = _real(spot, "spot", positive=True)
    f = _real(forward, "forward", positive=True)
    return _out(f / s - 1.0)


def fx_carry_from_rates(local_rate: object, foreign_rate: object):
    """KMPV eq. (7): carry of a long-foreign-currency forward is (r* - r) / (1 + r), rates per holding period.

    The quote is local currency per unit of foreign currency; ``local_rate`` is the rate of the currency the quote is
    expressed in. Covered interest parity F = S (1 + r) / (1 + r*) is assumed.
    """
    r = _real(local_rate, "local_rate", above=-1.0)
    rf = _real(foreign_rate, "foreign_rate", above=-1.0)
    return _out((rf - r) / (1.0 + r))


def commodity_curve_carry(f_near: object, f_next: object, t_near: object, t_next: object):
    """KMPV eq. (10): (F1 - F2) / (F2 (T2 - T1)), the per-unit-of-time carry of the second contract.

    0 <= T1 < T2 are times to maturity in the unit the result is quoted per (e.g. months; T1 = 0 with F1 = S gives the spot-to-futures
    slope). Positive means backwardation.
    """
    f1 = _real(f_near, "f_near", positive=True)
    f2 = _real(f_next, "f_next", positive=True)
    t1 = _real(t_near, "t_near")
    if (t1 < 0).any():
        raise ValueError("t_near must not be negative (0 means the spot price)")
    t2 = _real(t_next, "t_next", positive=True)
    if (t2 <= t1).any():
        raise ValueError("t_next must exceed t_near")
    return _out((f1 - f2) / (f2 * (t2 - t1)))


def zero_coupon_carry(maturities: object, yields: object, maturity: float, horizon: float,
                      financing_rate: float | None = None) -> dict[str, float]:
    """Constant-curve carry of an annually compounded zero-coupon bond held for ``horizon`` years.

    P(T) = (1 + y_T)^(-T). With the curve unchanged the bond becomes a (T - h)-year bond priced at y_(T-h). Then
    (1 + total) = (1 + y_T)^h * [(1 + y_T)/(1 + y_(T-h))]^(T-h) = (1 + yield_component)(1 + roll_down_component).
    Yields are linearly interpolated on ``maturities`` (years, strictly increasing, covering T and T - h). The excess
    figures subtract ``(1 + financing_rate)^h - 1`` additively when a financing rate is given.
    """
    m = _real(maturities, "maturities", positive=True)
    y = _real(yields, "yields", above=-1.0)
    if m.ndim != 1 or m.shape != y.shape or len(m) < 2 or (np.diff(m) <= 0).any():
        raise ValueError("maturities and yields must be equal-length 1-D with strictly increasing maturities")
    t = float(_real(maturity, "maturity", positive=True))
    h = float(_real(horizon, "horizon", positive=True))
    if not h < t:
        raise ValueError("horizon must be shorter than the bond's maturity")
    if t > m[-1] or t - h < m[0]:
        raise ValueError("the curve must cover both T and T - h")
    y_t = float(np.interp(t, m, y))
    y_r = float(np.interp(t - h, m, y))
    price_now = (1.0 + y_t) ** (-t)
    price_later = (1.0 + y_r) ** (-(t - h))
    out = {"yield_T": y_t, "yield_rolled": y_r, "price_now": price_now, "price_later": price_later,
           "total": price_later / price_now - 1.0, "yield_component": (1.0 + y_t) ** h - 1.0,
           "roll_down_component": ((1.0 + y_t) / (1.0 + y_r)) ** (t - h) - 1.0}
    if financing_rate is not None:
        fr = float(_real(financing_rate, "financing_rate", above=-1.0))
        out["financing"] = (1.0 + fr) ** h - 1.0
        out["excess_total"] = out["total"] - out["financing"]
    return out


def roll_down_approximation(modified_duration: object, yield_now: object, yield_rolled: object):
    """KMPV eq. (15) last line: roll-down ~ -D_mod * (y_(T-h) - y_T)."""
    d = _real(modified_duration, "modified_duration")
    a = _real(yield_now, "yield_now")
    b = _real(yield_rolled, "yield_rolled")
    return _out(-d * (b - a))


def portfolio_carry(weights: pd.Series, carry: pd.Series) -> float:
    """KMPV eq. (24): sum_i w_i C_i over identical labels; a missing carry on a nonzero weight raises."""
    if not isinstance(weights, pd.Series) or not isinstance(carry, pd.Series):
        raise TypeError("weights and carry must be pandas Series")
    if not weights.index.equals(carry.index):
        raise ValueError("weights and carry must have identical labels in the same order")
    for name, s in (("weights", weights), ("carry", carry)):
        if s.dtype.kind not in "iuf":
            raise TypeError(f"{name} must be real numeric (no bool/text/complex/object)")
        if np.isinf(s.to_numpy(dtype=float)).any():
            raise ValueError(f"{name} must not contain infinite values (NaN allowed only for carry)")
    w = weights.to_numpy(dtype=float)
    c = carry.to_numpy(dtype=float)
    if np.isnan(w).any():
        raise ValueError("weights must not contain NaN")
    if (np.isnan(c) & (w != 0)).any():
        raise ValueError("a position has no carry estimate")
    return float(np.sum(w[w != 0] * c[w != 0]))


def _contract_table(prices: pd.DataFrame, chosen: pd.Series, name: str) -> pd.DataFrame:
    p = _panel(prices, "prices")
    values = p.to_numpy(dtype=float)
    if (values[~np.isnan(values)] <= 0).any():
        raise ValueError("prices must be positive")
    if not isinstance(chosen, pd.Series) or not chosen.index.equals(p.index):
        raise ValueError(f"{name} must be a Series on the same row index as prices")
    unknown = set(chosen.dropna()) - set(p.columns)
    if unknown:
        raise ValueError(f"{name} names contracts missing from prices: {sorted(unknown)}")
    return p


def held_contract_returns(prices: pd.DataFrame, held: pd.Series) -> pd.Series:
    """Tradable fully collateralised excess return from row t to t+1 of the contract chosen at t: F[t+1, c]/F[t, c] - 1.

    ``held`` gives the contract label held from t to t+1 (NaN = flat, return 0). Both prices come from the same
    contract; a held contract with a missing price at t or t+1 raises instead of being treated as a zero return. The
    last row is NaN (its next-period price is unknown).
    """
    p = _contract_table(prices, held, "held")
    values = p.to_numpy(dtype=float)
    col = {c: j for j, c in enumerate(p.columns)}
    out = np.full(len(p), np.nan)
    for i in range(len(p) - 1):
        c = held.iloc[i]
        if pd.isna(c):
            out[i] = 0.0
            continue
        a, b = values[i, col[c]], values[i + 1, col[c]]
        if np.isnan(a) or np.isnan(b):
            raise ValueError(f"held contract {c!r} has no price at row {i} or {i + 1}")
        out[i] = b / a - 1.0
    return pd.Series(out, index=p.index, dtype=float)


def naive_splice_returns(prices: pd.DataFrame, front: pd.Series) -> pd.Series:
    """The return of the stitched 'continuous' price series, S[t+1] / S[t] - 1 with S[t] = F[t, front_t].

    At a roll (front_{t+1} != front_t) the ratio compares two different contracts, so it contains the price gap between
    them that no trader can earn. The last row is NaN.
    """
    p = _contract_table(prices, front, "front")
    if front.isna().any():
        raise ValueError("front must name a contract on every row")
    values = p.to_numpy(dtype=float)
    col = {c: j for j, c in enumerate(p.columns)}
    stitched = np.array([values[i, col[c]] for i, c in enumerate(front)], dtype=float)
    if np.isnan(stitched).any():
        raise ValueError("the front contract has no price on some row")
    out = np.full(len(p), np.nan)
    out[:-1] = stitched[1:] / stitched[:-1] - 1.0
    return pd.Series(out, index=p.index, dtype=float)
