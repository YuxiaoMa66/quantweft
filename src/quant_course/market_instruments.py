"""Unit-explicit cash-flow arithmetic for Chapter 10 market instruments.

These teaching helpers reject missing and non-finite numeric inputs. They do
not price instruments, model execution, taxes, financing, clearing, or product
rules beyond the assumptions stated on each function.
"""

from __future__ import annotations

import math
from numbers import Real
from typing import Literal, Sequence


def _finite_real(name: str, value: Real) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite; missing values are not filled")
    return result


def _positive_integer(name: str, value: int, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    minimum = 0 if allow_zero else 1
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def equity_total_return(
    shares: Real,
    price_start: Real,
    price_end: Real,
    dividend_per_share: Real = 0.0,
) -> float:
    """Simple holding-period return including an entitled cash dividend.

    Prices and dividend must use the same currency per share. The caller must
    establish that the dividend entitlement belongs to the holding interval.
    """
    quantity = _finite_real("shares", shares)
    start = _finite_real("price_start", price_start)
    end = _finite_real("price_end", price_end)
    dividend = _finite_real("dividend_per_share", dividend_per_share)
    if quantity <= 0 or start <= 0 or end < 0 or dividend < 0:
        raise ValueError("shares and start price must be positive; end price and dividend cannot be negative")
    wealth_start = quantity * start
    wealth_end = quantity * end + quantity * dividend
    return wealth_end / wealth_start - 1.0


def bond_coupon_cashflow(
    face_value: Real, annual_coupon_rate: Real, payments_per_year: int
) -> float:
    """Coupon amount in currency per payment date for a plain fixed-rate bond."""
    face = _finite_real("face_value", face_value)
    rate = _finite_real("annual_coupon_rate", annual_coupon_rate)
    frequency = _positive_integer("payments_per_year", payments_per_year)
    if face <= 0 or rate < 0:
        raise ValueError("face value must be positive and coupon rate non-negative")
    return face * rate / frequency


def fx_convert_base_to_quote(amount_base: Real, quote_per_base: Real) -> float:
    """Convert base-currency amount using a quote stated as quote/base."""
    amount = _finite_real("amount_base", amount_base)
    rate = _finite_real("quote_per_base", quote_per_base)
    if rate <= 0:
        raise ValueError("quote_per_base must be positive")
    return amount * rate


def covered_fx_forward_quote(
    spot_quote_per_base: Real,
    domestic_rate: Real,
    foreign_rate: Real,
    tenor_years: Real,
) -> float:
    """Simple-interest covered-parity reference quote.

    The pair is quote currency per one unit of base currency. ``domestic_rate``
    is the quote-currency rate and ``foreign_rate`` the base-currency rate.
    The formula assumes matched dates, simple deposit factors, no bid/ask,
    credit, tax, capital, collateral, or cross-currency basis adjustments.
    """
    spot = _finite_real("spot_quote_per_base", spot_quote_per_base)
    domestic = _finite_real("domestic_rate", domestic_rate)
    foreign = _finite_real("foreign_rate", foreign_rate)
    tenor = _finite_real("tenor_years", tenor_years)
    if spot <= 0 or tenor <= 0:
        raise ValueError("spot and tenor must be positive")
    domestic_factor = 1.0 + domestic * tenor
    foreign_factor = 1.0 + foreign * tenor
    if domestic_factor <= 0 or foreign_factor <= 0:
        raise ValueError("simple accumulation factors must be positive")
    return spot * domestic_factor / foreign_factor


def futures_variation_margin_usd(
    signed_contracts: int,
    multiplier_usd_per_point: Real,
    settlement_price_changes_points: Sequence[Real],
) -> tuple[float, ...]:
    """Signed USD settlement cash flows for successive futures price moves."""
    if isinstance(signed_contracts, bool) or not isinstance(signed_contracts, int):
        raise TypeError("signed_contracts must be an integer")
    _positive_integer("absolute contract count", abs(signed_contracts), allow_zero=True)
    multiplier = _finite_real("multiplier_usd_per_point", multiplier_usd_per_point)
    if multiplier <= 0:
        raise ValueError("multiplier_usd_per_point must be positive")
    changes = tuple(
        _finite_real(f"settlement_price_changes_points[{index}]", value)
        for index, value in enumerate(settlement_price_changes_points)
    )
    return tuple(signed_contracts * multiplier * change for change in changes)


def listed_option_pnl(
    underlying_at_expiry: Real,
    strike: Real,
    premium_per_underlying_unit: Real,
    signed_contracts: int,
    units_per_contract: int,
    option_type: Literal["call", "put"],
) -> float:
    """Expiry P&L with positive signed contract count for a long position.

    Premium and payoff share a quote currency per underlying unit. Contract
    size is explicit because adjusted contracts can differ from standard size.
    """
    underlying = _finite_real("underlying_at_expiry", underlying_at_expiry)
    strike_value = _finite_real("strike", strike)
    premium = _finite_real("premium_per_underlying_unit", premium_per_underlying_unit)
    if underlying < 0 or strike_value <= 0 or premium < 0:
        raise ValueError("underlying must be non-negative; strike positive; premium non-negative")
    if isinstance(signed_contracts, bool) or not isinstance(signed_contracts, int):
        raise TypeError("signed_contracts must be an integer")
    units = _positive_integer("units_per_contract", units_per_contract)
    if option_type == "call":
        intrinsic = max(underlying - strike_value, 0.0)
    elif option_type == "put":
        intrinsic = max(strike_value - underlying, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    return signed_contracts * units * (intrinsic - premium)


def repo_cash_advanced(collateral_market_value: Real, haircut: Real) -> float:
    """Simple cash principal for a repo haircut convention in one currency."""
    value = _finite_real("collateral_market_value", collateral_market_value)
    haircut_value = _finite_real("haircut", haircut)
    if value <= 0 or not 0 <= haircut_value < 1:
        raise ValueError("collateral value must be positive and haircut in [0, 1)")
    return value * (1.0 - haircut_value)


def interest_rate_swap_net_cashflow(
    notional: Real,
    fixed_rate: Real,
    floating_rate: Real,
    accrual_fraction: Real,
    position: Literal["receive_float_pay_fixed", "pay_float_receive_fixed"] = "receive_float_pay_fixed",
) -> float:
    """One-period net coupon in the notional currency for a plain rate swap.

    The notional is a calculation reference and is not exchanged. Rates are
    simple annual rates and accrual_fraction is a year fraction. This excludes
    discounting, day-count details, fees, collateral, and counterparty effects.
    """
    principal = _finite_real("notional", notional)
    fixed = _finite_real("fixed_rate", fixed_rate)
    floating = _finite_real("floating_rate", floating_rate)
    accrual = _finite_real("accrual_fraction", accrual_fraction)
    if principal <= 0 or accrual <= 0:
        raise ValueError("notional and accrual_fraction must be positive")
    if position == "receive_float_pay_fixed":
        sign = 1.0
    elif position == "pay_float_receive_fixed":
        sign = -1.0
    else:
        raise ValueError("position must specify the received and paid legs")
    return sign * principal * (floating - fixed) * accrual


__all__ = [
    "bond_coupon_cashflow",
    "covered_fx_forward_quote",
    "equity_total_return",
    "fx_convert_base_to_quote",
    "futures_variation_margin_usd",
    "interest_rate_swap_net_cashflow",
    "listed_option_pnl",
    "repo_cash_advanced",
]
