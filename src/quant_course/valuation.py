"""Claim-consistent valuation examples for Chapter 13.

All amounts passed to an individual function must use one currency and one
unit. The module intentionally does not download market data or filings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
from numbers import Real
from typing import Iterable, Literal, Sequence


@dataclass(frozen=True)
class Amount:
    """A finite signed amount with explicit currency and scale."""

    value: float
    currency: str
    unit: str

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, Real):
            raise ValueError("amount must be a real number, not bool")
        try:
            numeric_value = float(self.value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError("amount must be finite") from exc
        if not math.isfinite(numeric_value):
            raise ValueError("amount must be finite")
        object.__setattr__(self, "value", numeric_value)
        if not self.currency.strip() or not self.unit.strip():
            raise ValueError("currency and unit must be explicit")


def _same_scale(amounts: Iterable[Amount]) -> tuple[str, str]:
    items = tuple(amounts)
    if not items:
        raise ValueError("at least one amount is required")
    scale = (items[0].currency, items[0].unit)
    if any((item.currency, item.unit) != scale for item in items):
        raise ValueError("amounts must use the same currency and unit")
    return scale


def market_cap_from_price(
    price_per_share: float,
    shares_millions: float,
    *,
    currency: str = "USD",
) -> Amount:
    """Multiply a price in currency/share by shares in millions of shares."""
    if not math.isfinite(price_per_share) or price_per_share < 0:
        raise ValueError("price_per_share must be finite and non-negative")
    if not math.isfinite(shares_millions) or shares_millions < 0:
        raise ValueError("shares_millions must be finite and non-negative")
    return Amount(price_per_share * shares_millions, currency, f"{currency} millions")


def enterprise_value(
    equity_market_cap: Amount,
    debt: Amount,
    cash: Amount,
    *,
    noncontrolling_interest: Amount | None = None,
    preferred_equity: Amount | None = None,
    nonoperating_assets: Amount | None = None,
) -> Amount:
    """Return EV under an explicit bridge; cash and nonoperating assets are subtracted."""
    zero = Amount(0.0, equity_market_cap.currency, equity_market_cap.unit)
    nci = noncontrolling_interest or zero
    preferred = preferred_equity or zero
    nonop = nonoperating_assets or zero
    scale = _same_scale((equity_market_cap, debt, cash, nci, preferred, nonop))
    if any(value.value < 0 for value in (equity_market_cap, debt, cash, nci, preferred, nonop)):
        raise ValueError("bridge components must be non-negative amounts")
    value = (
        equity_market_cap.value + debt.value + nci.value + preferred.value
        - cash.value - nonop.value
    )
    return Amount(value, *scale)


def equity_from_enterprise_value(
    ev: Amount,
    debt: Amount,
    cash: Amount,
    *,
    noncontrolling_interest: Amount | None = None,
    preferred_equity: Amount | None = None,
    nonoperating_assets: Amount | None = None,
) -> Amount:
    """Invert the EV bridge to the value attributable to common equity."""
    zero = Amount(0.0, ev.currency, ev.unit)
    nci = noncontrolling_interest or zero
    preferred = preferred_equity or zero
    nonop = nonoperating_assets or zero
    scale = _same_scale((ev, debt, cash, nci, preferred, nonop))
    if any(value.value < 0 for value in (debt, cash, nci, preferred, nonop)):
        raise ValueError("bridge components must be non-negative amounts")
    return Amount(
        ev.value - debt.value - nci.value - preferred.value + cash.value + nonop.value,
        *scale,
    )


def _positive_denominator(value: Amount) -> bool:
    return value.value > 0


def price_to_earnings(equity_market_cap: Amount, net_income_common: Amount) -> float | None:
    """P/E; non-positive common earnings are not ranked as a conventional multiple."""
    _same_scale((equity_market_cap, net_income_common))
    if equity_market_cap.value <= 0 or net_income_common.value <= 0:
        return None
    return equity_market_cap.value / net_income_common.value


def price_to_book(equity_market_cap: Amount, common_book_equity: Amount) -> float | None:
    """P/B; non-positive common book equity is marked unavailable."""
    _same_scale((equity_market_cap, common_book_equity))
    if equity_market_cap.value <= 0 or common_book_equity.value <= 0:
        return None
    return equity_market_cap.value / common_book_equity.value


def enterprise_multiple(enterprise_value_amount: Amount, operating_earnings: Amount) -> float | None:
    """EV/EBITDA or EV/EBIT; caller names and aligns the operating denominator."""
    _same_scale((enterprise_value_amount, operating_earnings))
    if enterprise_value_amount.value <= 0 or operating_earnings.value <= 0:
        return None
    return enterprise_value_amount.value / operating_earnings.value


def earnings_yield(equity_market_cap: Amount, net_income_common: Amount) -> float | None:
    """Signed earnings yield; losses remain visible as negative values."""
    _same_scale((equity_market_cap, net_income_common))
    if equity_market_cap.value <= 0:
        return None
    return net_income_common.value / equity_market_cap.value


def fcf_yield(
    free_cash_flow: Amount,
    claim_value: Amount,
    *,
    cash_flow_basis: Literal["FCFF", "FCFE"],
    claim_basis: Literal["EV", "Equity"],
) -> float | None:
    """Yield with an explicit claim match: FCFF/EV or FCFE/equity value."""
    _same_scale((free_cash_flow, claim_value))
    required_claim = "EV" if cash_flow_basis == "FCFF" else "Equity"
    if cash_flow_basis not in ("FCFF", "FCFE"):
        raise ValueError("cash_flow_basis must be FCFF or FCFE")
    if claim_basis != required_claim:
        raise ValueError("FCFF pairs with EV; FCFE pairs with Equity")
    if claim_value.value <= 0:
        return None
    return free_cash_flow.value / claim_value.value


def _is_finite_real(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def _validate_rate(name: str, value: float, *, lower: float = -1.0, upper: float | None = None) -> None:
    if not _is_finite_real(value) or value <= lower or (upper is not None and value > upper):
        bound = f" and <= {upper}" if upper is not None else ""
        raise ValueError(f"{name} must be finite, > {lower}{bound}")


def _validate_tax_rate(value: float) -> None:
    if not _is_finite_real(value) or value < 0.0 or value > 1.0:
        raise ValueError("tax_rate must be finite and between 0 and 1 inclusive")


def weighted_average_cost_of_capital(
    equity_market_value: Amount,
    debt_market_value: Amount,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float,
    *,
    preferred_market_value: Amount | None = None,
    cost_of_preferred: float = 0.0,
) -> float:
    """Market-value weighted WACC with an explicit after-tax debt cost.

    For consolidated FCFF, equity market value must cover operating common
    equity including NCI. This formula assigns included NCI the same
    ``cost_of_equity`` assumption; model NCI separately when that assumption
    does not fit.
    """
    preferred = preferred_market_value or Amount(0.0, equity_market_value.currency, equity_market_value.unit)
    _same_scale((equity_market_value, debt_market_value, preferred))
    _validate_rate("cost_of_equity", cost_of_equity)
    _validate_rate("cost_of_debt", cost_of_debt)
    _validate_rate("cost_of_preferred", cost_of_preferred)
    _validate_tax_rate(tax_rate)
    values = (equity_market_value.value, debt_market_value.value, preferred.value)
    if any(value < 0 for value in values) or sum(values) <= 0:
        raise ValueError("capital market values must be non-negative with a positive total")
    total = sum(values)
    return (
        equity_market_value.value / total * cost_of_equity
        + debt_market_value.value / total * cost_of_debt * (1.0 - tax_rate)
        + preferred.value / total * cost_of_preferred
    )


def _same_amount_scale(amounts: Sequence[Amount]) -> tuple[str, str]:
    return _same_scale(amounts)


def fcff_from_ebit(
    ebit: Amount,
    tax_rate: float,
    depreciation_amortization: Amount,
    capex_spend: Amount,
    change_in_nwc: Amount,
) -> Amount:
    """FCFF proxy = EBIT(1-T) + D&A - CapEx - increase in operating NWC."""
    scale = _same_amount_scale((ebit, depreciation_amortization, capex_spend, change_in_nwc))
    _validate_tax_rate(tax_rate)
    if depreciation_amortization.value < 0 or capex_spend.value < 0:
        raise ValueError("D&A and CapEx must be non-negative expense/spend amounts")
    return Amount(
        ebit.value * (1.0 - tax_rate)
        + depreciation_amortization.value
        - capex_spend.value
        - change_in_nwc.value,
        *scale,
    )


def fcfe_from_net_income(
    net_income_common: Amount,
    depreciation_amortization: Amount,
    capex_spend: Amount,
    change_in_nwc: Amount,
    net_borrowing: Amount,
) -> Amount:
    """FCFE proxy for one common-stock claim plus debt.

    Net income, D&A, CapEx, NWC change, and net borrowing must all use the same
    ownership scope.
    """
    scale = _same_amount_scale(
        (net_income_common, depreciation_amortization, capex_spend, change_in_nwc, net_borrowing)
    )
    if depreciation_amortization.value < 0 or capex_spend.value < 0:
        raise ValueError("D&A and CapEx must be non-negative expense/spend amounts")
    return Amount(
        net_income_common.value + depreciation_amortization.value
        - capex_spend.value - change_in_nwc.value + net_borrowing.value,
        *scale,
    )


def gordon_terminal_value(
    final_forecast_cash_flow: Amount,
    discount_rate: float,
    perpetual_growth: float,
) -> Amount:
    """Terminal value at year N, with growth above -100% and below the rate."""
    _validate_rate("discount_rate", discount_rate)
    if not _is_finite_real(perpetual_growth):
        raise ValueError("perpetual_growth must be a finite real number")
    if perpetual_growth <= -1.0:
        raise ValueError("perpetual_growth must be greater than -1")
    if perpetual_growth >= discount_rate:
        raise ValueError("perpetual_growth must be below the discount rate")
    return Amount(
        final_forecast_cash_flow.value * (1.0 + perpetual_growth)
        / (discount_rate - perpetual_growth),
        final_forecast_cash_flow.currency,
        final_forecast_cash_flow.unit,
    )


def discounted_cash_flow_value(
    forecast_cash_flows: Sequence[Amount],
    discount_rate: float,
    *,
    cash_flow_basis: Literal["FCFF", "FCFE"],
    discount_rate_basis: Literal["WACC", "cost_of_equity"],
    terminal_value: Amount | None = None,
) -> Amount:
    """PV annual end-of-period flows; terminal value, if present, is at year N."""
    if not forecast_cash_flows:
        raise ValueError("at least one forecast cash flow is required")
    _validate_rate("discount_rate", discount_rate)
    required_rate = "WACC" if cash_flow_basis == "FCFF" else "cost_of_equity"
    if cash_flow_basis not in ("FCFF", "FCFE"):
        raise ValueError("cash_flow_basis must be FCFF or FCFE")
    if discount_rate_basis != required_rate:
        raise ValueError("FCFF pairs with WACC; FCFE pairs with cost_of_equity")
    amounts = tuple(forecast_cash_flows) + ((terminal_value,) if terminal_value is not None else ())
    scale = _same_scale(amounts)
    n = len(forecast_cash_flows)
    present_value = sum(
        cash_flow.value / (1.0 + discount_rate) ** period
        for period, cash_flow in enumerate(forecast_cash_flows, start=1)
    )
    if terminal_value is not None:
        present_value += terminal_value.value / (1.0 + discount_rate) ** n
    return Amount(present_value, *scale)


@dataclass(frozen=True)
class FinancialVintage:
    """One internally consistent filing version for a security and fiscal period."""

    issuer_id: str
    security_id: str
    fiscal_period: str
    period_end: date
    available_at: datetime
    ingested_at: datetime
    accession: str
    currency: str
    unit: str
    net_income_common: float
    common_book_equity: float
    ebit: float
    ebitda: float
    free_cash_flow: float
    cash_flow_basis: Literal["FCFF", "FCFE"]
    industry: str

    def __post_init__(self) -> None:
        for name, value in (("available_at", self.available_at), ("ingested_at", self.ingested_at)):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        numbers = (
            self.net_income_common, self.common_book_equity, self.ebit,
            self.ebitda, self.free_cash_flow,
        )
        if any(not math.isfinite(value) for value in numbers):
            raise ValueError("financial vintage values must be finite")
        if self.cash_flow_basis not in ("FCFF", "FCFE"):
            raise ValueError("cash_flow_basis must be FCFF or FCFE")


@dataclass(frozen=True)
class MarketCapSnapshot:
    """A market snapshot with explicit point-in-time clocks.

    If availability or ingestion is omitted, ``as_of`` is used as the
    illustrative assumption that the snapshot was already usable then.
    """

    security_id: str
    as_of: datetime
    market_cap: Amount
    enterprise_value: Amount | None = None
    enterprise_value_accession: str | None = None
    available_at: datetime | None = None
    ingested_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("market-cap as_of must be timezone-aware")
        for name in ("available_at", "ingested_at"):
            timestamp = getattr(self, name)
            if timestamp is None:
                object.__setattr__(self, name, self.as_of)
            elif timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError(f"market-cap {name} must be timezone-aware")
        if self.market_cap.value < 0:
            raise ValueError("market capitalization must be non-negative")
        if self.enterprise_value is not None:
            _same_scale((self.market_cap, self.enterprise_value))
            if not self.enterprise_value_accession or not self.enterprise_value_accession.strip():
                raise ValueError("enterprise value requires its financial accession")
        elif self.enterprise_value_accession is not None:
            raise ValueError("enterprise value accession requires an enterprise value")


def select_pit_vintage(
    vintages: Sequence[FinancialVintage],
    *,
    security_id: str,
    fiscal_period: str,
    signal_time: datetime,
) -> FinancialVintage | None:
    """Select the latest eligible version for one exact security and period."""
    if signal_time.tzinfo is None or signal_time.utcoffset() is None:
        raise ValueError("signal_time must be timezone-aware")
    eligible = [
        row for row in vintages
        if row.security_id == security_id
        and row.fiscal_period == fiscal_period
        and row.available_at <= signal_time
        and row.ingested_at <= signal_time
    ]
    if not eligible:
        return None
    latest = max(row.available_at for row in eligible)
    latest_rows = [row for row in eligible if row.available_at == latest]
    if len({row.accession for row in latest_rows}) > 1:
        raise ValueError("conflicting filing versions share the latest available_at")
    economic_values = {
        (
            row.issuer_id, row.security_id, row.fiscal_period, row.period_end,
            row.available_at, row.accession, row.currency, row.unit,
            row.net_income_common, row.common_book_equity, row.ebit, row.ebitda,
            row.free_cash_flow, row.cash_flow_basis, row.industry,
        )
        for row in latest_rows
    }
    if len(economic_values) > 1:
        raise ValueError("conflicting financial values share the latest filing accession")
    return max(latest_rows, key=lambda row: row.ingested_at)


def select_pit_market_cap(
    market_caps: Sequence[MarketCapSnapshot],
    *,
    security_id: str,
    signal_time: datetime,
) -> MarketCapSnapshot | None:
    """Use snapshots whose observation, availability, and ingestion precede the cut.

    Legacy snapshots without explicit clocks treat ``as_of`` as already usable.
    """
    if signal_time.tzinfo is None or signal_time.utcoffset() is None:
        raise ValueError("signal_time must be timezone-aware")
    eligible = [
        row for row in market_caps
        if row.security_id == security_id
        and row.as_of <= signal_time
        and (row.available_at or row.as_of) <= signal_time
        and (row.ingested_at or row.as_of) <= signal_time
    ]
    if not eligible:
        return None
    latest_time = max(row.as_of for row in eligible)
    latest = [row for row in eligible if row.as_of == latest_time]
    economic_values = {
        (
            row.market_cap.value, row.market_cap.currency, row.market_cap.unit,
            None if row.enterprise_value is None else row.enterprise_value.value,
            None if row.enterprise_value is None else row.enterprise_value.currency,
            None if row.enterprise_value is None else row.enterprise_value.unit,
            row.enterprise_value_accession,
        )
        for row in latest
    }
    if len(economic_values) > 1:
        raise ValueError("conflicting market-cap or enterprise-value inputs share the latest timestamp")
    return max(
        latest,
        key=lambda row: (row.available_at or row.as_of, row.ingested_at or row.as_of),
    )


def pit_fcf_yield(
    vintages: Sequence[FinancialVintage],
    market_caps: Sequence[MarketCapSnapshot],
    *,
    security_id: str,
    fiscal_period: str,
    signal_time: datetime,
) -> tuple[float | None, FinancialVintage | None, MarketCapSnapshot | None]:
    """Return a point-in-time yield and the exact filing/market inputs selected."""
    vintage = select_pit_vintage(
        vintages, security_id=security_id, fiscal_period=fiscal_period, signal_time=signal_time
    )
    market_cap = select_pit_market_cap(market_caps, security_id=security_id, signal_time=signal_time)
    if vintage is None or market_cap is None:
        return None, vintage, market_cap
    flow = Amount(vintage.free_cash_flow, vintage.currency, vintage.unit)
    basis = vintage.cash_flow_basis
    if basis == "FCFF":
        claim_value = market_cap.enterprise_value
        if claim_value is None or market_cap.enterprise_value_accession != vintage.accession:
            return None, vintage, market_cap
        claim_basis: Literal["EV", "Equity"] = "EV"
    else:
        claim_value = market_cap.market_cap
        claim_basis = "Equity"
    value = fcf_yield(flow, claim_value, cash_flow_basis=basis, claim_basis=claim_basis)
    return value, vintage, market_cap


def industry_percentile_ranks(
    values: dict[str, float | None],
    industries: dict[str, str],
) -> dict[str, float | None]:
    """Average-tie percentile ranks within one cross-section, grouped by industry."""
    if set(values) != set(industries):
        raise ValueError("values and industries must contain the same security IDs")
    groups: dict[str, list[tuple[str, float]]] = {}
    result: dict[str, float | None] = {security_id: None for security_id in values}
    for security_id, value in values.items():
        if value is None:
            continue
        if not math.isfinite(value):
            raise ValueError("non-finite values must be represented as None")
        groups.setdefault(industries[security_id], []).append((security_id, value))
    for rows in groups.values():
        ordered = sorted(rows, key=lambda item: item[1])
        count = len(ordered)
        index = 0
        while index < count:
            end = index + 1
            while end < count and ordered[end][1] == ordered[index][1]:
                end += 1
            average_zero_based_rank = (index + end - 1) / 2.0
            percentile = 0.5 if count == 1 else average_zero_based_rank / (count - 1)
            for security_id, _ in ordered[index:end]:
                result[security_id] = percentile
            index = end
    return result


def constructed_company_cases() -> dict[str, dict[str, Amount | float | str]]:
    """Two synthetic same-industry companies for the bridge and multiple examples."""
    unit = "USD millions"
    return {
        "Orion": {
            "industry": "Industrial software",
            "price": 60.0,
            "shares_millions": 10.0,
            "market_cap": market_cap_from_price(60.0, 10.0),
            "debt": Amount(100.0, "USD", unit),
            "cash": Amount(50.0, "USD", unit),
            "nci": Amount(0.0, "USD", unit),
            "preferred": Amount(0.0, "USD", unit),
            "nonoperating_assets": Amount(0.0, "USD", unit),
            "net_income": Amount(30.0, "USD", unit),
            "book_equity": Amount(180.0, "USD", unit),
            "ebitda": Amount(75.0, "USD", unit),
            "ebit": Amount(50.0, "USD", unit),
            "fcfe": Amount(28.0, "USD", unit),
            "fcff": Amount(40.0, "USD", unit),
        },
        "Lyra": {
            "industry": "Industrial software",
            "price": 24.0,
            "shares_millions": 20.0,
            "market_cap": market_cap_from_price(24.0, 20.0),
            "debt": Amount(260.0, "USD", unit),
            "cash": Amount(30.0, "USD", unit),
            "nci": Amount(40.0, "USD", unit),
            "preferred": Amount(20.0, "USD", unit),
            "nonoperating_assets": Amount(20.0, "USD", unit),
            "net_income": Amount(20.0, "USD", unit),
            "book_equity": Amount(120.0, "USD", unit),
            "ebitda": Amount(75.0, "USD", unit),
            "ebit": Amount(50.0, "USD", unit),
            "fcfe": Amount(18.0, "USD", unit),
            "fcff": Amount(40.0, "USD", unit),
        },
    }
