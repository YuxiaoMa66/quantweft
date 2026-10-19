"""Version-aware accounting facts and financial statement metrics.

Apple and Spire values are transcribed from the cited SEC filings. The PIT
timestamps and market-cap example are constructed teaching inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import re
from typing import Mapping

import pandas as pd

from quant_course.pit import pit_asof_join

APPLE_10K = (
    "https://www.sec.gov/Archives/edgar/data/320193/"
    "000032019324000123/aapl-20240928.htm"
)
SPIRE_ORIGINAL_10K = (
    "https://www.sec.gov/Archives/edgar/data/1816017/"
    "000095017024027164/spir-20231231.htm"
)
SPIRE_AMENDED_10K = (
    "https://www.sec.gov/Archives/edgar/data/1816017/"
    "000095017025030856/spir-20231231.htm"
)


@dataclass(frozen=True)
class FinancialFact:
    """One reported value with issuer, period, version, currency, and unit."""

    name: str
    value: float
    issuer_id: str
    fiscal_period: str
    currency: str
    unit: str
    accession: str
    revision_status: str
    source: str

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise TypeError(f"{self.name} must be a real numeric value")
        if not isfinite(float(self.value)):
            raise ValueError(f"{self.name} must be finite")
        for field_name in (
            "name",
            "issuer_id",
            "fiscal_period",
            "currency",
            "unit",
            "accession",
            "revision_status",
            "source",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")


APPLE_VALUES: dict[int, dict[str, float]] = {
    2024: {
        "revenue": 391_035.0,
        "gross_profit": 180_683.0,
        "operating_income": 123_216.0,
        "depreciation_amortization": 11_445.0,
        "net_income": 93_736.0,
        "cfo": 118_254.0,
        "capex_cash_flow": -9_447.0,
        "cash_and_equivalents": 29_943.0,
        "commercial_paper": 9_967.0,
        "current_term_debt": 10_912.0,
        "noncurrent_term_debt": 85_750.0,
        "total_assets": 364_980.0,
        "total_liabilities": 308_030.0,
        "total_equity": 56_950.0,
        "accounts_receivable": 33_410.0,
        "vendor_receivables": 32_833.0,
        "inventory": 7_286.0,
        "other_current_assets": 14_287.0,
        "accounts_payable": 68_960.0,
        "deferred_revenue": 8_249.0,
    },
    2023: {
        "revenue": 383_285.0,
        "gross_profit": 169_148.0,
        "operating_income": 114_301.0,
        "depreciation_amortization": 11_519.0,
        "net_income": 96_995.0,
        "cfo": 110_543.0,
        "capex_cash_flow": -10_959.0,
        "cash_and_equivalents": 29_965.0,
        "commercial_paper": 5_985.0,
        "current_term_debt": 9_822.0,
        "noncurrent_term_debt": 95_281.0,
        "total_assets": 352_583.0,
        "total_liabilities": 290_437.0,
        "total_equity": 62_146.0,
        "accounts_receivable": 29_508.0,
        "vendor_receivables": 31_477.0,
        "inventory": 6_331.0,
        "other_current_assets": 14_695.0,
        "accounts_payable": 62_611.0,
        "deferred_revenue": 8_061.0,
    },
}


def apple_facts(year: int) -> dict[str, FinancialFact]:
    """Return FY2024 10-K facts for FY2024 or its FY2023 comparator.

    Amounts are USD millions. Both annual columns come from the same 2024 10-K
    accession. The 2023 period end is 2023-09-30; 2024 ended 2024-09-28.
    """
    if year not in APPLE_VALUES:
        raise ValueError("year must be 2023 or 2024")
    return {
        name: FinancialFact(
            name=name,
            value=value,
            issuer_id="CIK0000320193",
            fiscal_period=f"FY{year}",
            currency="USD",
            unit="USD millions",
            accession="0000320193-24-000123",
            revision_status="as-filed 2024 Form 10-K",
            source=APPLE_10K,
        )
        for name, value in APPLE_VALUES[year].items()
    }


def spire_cash_flow_facts(version: str) -> tuple[FinancialFact, FinancialFact]:
    """Return Spire FY2023 CFO and PP&E-purchase facts in USD thousands."""
    if version == "original":
        accession = "0000950170-24-027164"
        status = "original 2023 Form 10-K"
        source = SPIRE_ORIGINAL_10K
        cfo_value, capex_value = -23_622.0, -30_037.0
    elif version == "restated":
        accession = "0000950170-25-030856"
        status = "restated 2023 Form 10-K/A"
        source = SPIRE_AMENDED_10K
        cfo_value, capex_value = -36_307.0, -17_352.0
    else:
        raise ValueError("version must be 'original' or 'restated'")
    cfo = FinancialFact(
        "cfo", cfo_value, "CIK0001816017", "FY2023", "USD", "USD thousands",
        accession, status, source,
    )
    capex = FinancialFact(
        "capex_cash_flow", capex_value, "CIK0001816017", "FY2023", "USD",
        "USD thousands", accession, status, source,
    )
    return cfo, capex


def _require_same_version(facts: list[FinancialFact]) -> None:
    if not facts:
        raise ValueError("at least one fact is required")
    first = facts[0]
    expected = (
        first.issuer_id, first.fiscal_period, first.currency, first.unit,
        first.accession, first.revision_status,
    )
    for fact in facts[1:]:
        actual = (
            fact.issuer_id, fact.fiscal_period, fact.currency, fact.unit,
            fact.accession, fact.revision_status,
        )
        if actual != expected:
            raise ValueError(
                "facts must match issuer, fiscal period, currency, unit, and filing version"
            )


def fcf_from_statement_lines(cfo: FinancialFact, capex_cash_flow: FinancialFact) -> float:
    """Compute teaching FCF = CFO - CapEx from a negative cash-flow line."""
    _require_same_version([cfo, capex_cash_flow])
    if cfo.name != "cfo" or capex_cash_flow.name != "capex_cash_flow":
        raise ValueError("expected facts named 'cfo' and 'capex_cash_flow'")
    if capex_cash_flow.value > 0:
        raise ValueError("capex_cash_flow must use the statement outflow sign")
    capex_spend = -float(capex_cash_flow.value)
    return float(cfo.value) - capex_spend


def derive_accounting_factors(
    facts: Mapping[str, FinancialFact],
) -> dict[str, float | None]:
    """Derive margins, balance-sheet ratios, and a defined selected NWC proxy."""
    required = {
        "revenue", "gross_profit", "operating_income", "depreciation_amortization",
        "net_income", "cfo", "capex_cash_flow", "cash_and_equivalents",
        "commercial_paper", "current_term_debt", "noncurrent_term_debt",
        "total_assets", "total_liabilities", "total_equity", "accounts_receivable",
        "vendor_receivables", "inventory", "other_current_assets", "accounts_payable",
        "deferred_revenue",
    }
    missing = required.difference(facts)
    if missing:
        raise ValueError(f"missing statement facts: {sorted(missing)}")
    selected = [facts[name] for name in sorted(required)]
    if any(fact.name != key for key, fact in facts.items() if key in required):
        raise ValueError("fact mapping keys must match each fact's line-item name")
    _require_same_version(selected)

    revenue = float(facts["revenue"].value)
    if revenue <= 0:
        raise ValueError("revenue must be positive to calculate margins")
    ebit = float(facts["operating_income"].value)
    depreciation_amortization = float(facts["depreciation_amortization"].value)
    ebitda_proxy = ebit + depreciation_amortization
    fcf = fcf_from_statement_lines(facts["cfo"], facts["capex_cash_flow"])
    gross_debt = sum(
        float(facts[name].value)
        for name in ("commercial_paper", "current_term_debt", "noncurrent_term_debt")
    )
    assets = float(facts["total_assets"].value)
    if assets <= 0:
        raise ValueError("total_assets must be positive")
    balance_sheet_residual = (
        assets - float(facts["total_liabilities"].value) - float(facts["total_equity"].value)
    )
    selected_operating_nwc = (
        float(facts["accounts_receivable"].value)
        + float(facts["vendor_receivables"].value)
        + float(facts["inventory"].value)
        + float(facts["other_current_assets"].value)
        - float(facts["accounts_payable"].value)
        - float(facts["deferred_revenue"].value)
    )
    net_debt = gross_debt - float(facts["cash_and_equivalents"].value)
    net_debt_to_ebitda = net_debt / ebitda_proxy if ebitda_proxy > 0 else None
    return {
        "gross_margin": float(facts["gross_profit"].value) / revenue,
        "operating_margin": ebit / revenue,
        "ebitda_proxy": ebitda_proxy,
        "ebitda_proxy_margin": ebitda_proxy / revenue,
        "net_income_margin": float(facts["net_income"].value) / revenue,
        "cfo_margin": float(facts["cfo"].value) / revenue,
        "capex_spend": -float(facts["capex_cash_flow"].value),
        "fcf": fcf,
        "fcf_margin": fcf / revenue,
        "gross_debt": gross_debt,
        "net_debt": net_debt,
        "debt_to_assets": gross_debt / assets,
        "net_debt_to_ebitda_proxy": net_debt_to_ebitda,
        "selected_operating_nwc": selected_operating_nwc,
        "balance_sheet_residual": balance_sheet_residual,
    }


def revenue_growth(current: FinancialFact, previous: FinancialFact) -> float:
    """Calculate growth for matching revenue facts from a common snapshot."""
    if current.name != "revenue" or previous.name != "revenue":
        raise ValueError("both facts must be revenue")
    if (
        current.issuer_id != previous.issuer_id
        or current.currency != previous.currency
        or current.unit != previous.unit
        or current.accession != previous.accession
        or current.revision_status != previous.revision_status
    ):
        raise ValueError("revenue facts must share issuer, units, and source snapshot")
    current_year = re.fullmatch(r"FY(\d{4})", current.fiscal_period)
    previous_year = re.fullmatch(r"FY(\d{4})", previous.fiscal_period)
    if not current_year or not previous_year:
        raise ValueError("fiscal periods must use FYYYYY labels")
    if int(current_year.group(1)) <= int(previous_year.group(1)):
        raise ValueError("current period must follow previous period")
    if previous.value == 0:
        raise ValueError("previous revenue must not be zero")
    return float(current.value) / float(previous.value) - 1.0


def fcf_yield(
    fcf: float,
    market_cap: float,
    *,
    currency: str,
    statement_unit: str,
    market_cap_currency: str,
    market_cap_unit: str,
    market_cap_label: str,
) -> float:
    """Divide FCF by same-currency and same-unit market cap with provenance."""
    if not isfinite(fcf) or not isfinite(market_cap):
        raise ValueError("FCF and market_cap must be finite")
    if market_cap <= 0:
        raise ValueError("market_cap must be positive")
    if currency != market_cap_currency or statement_unit != market_cap_unit:
        raise ValueError("FCF and market_cap must use the same currency and unit")
    if not market_cap_label.strip():
        raise ValueError("label whether market_cap is constructed or sourced")
    return fcf / market_cap


def point_in_time_revision_demo() -> pd.DataFrame:
    """Run a fully constructed, timezone-aware two-clock filing-version example."""
    signals = pd.DataFrame(
        {
            "issuer_cik": ["SIM-ISSUER-1"] * 4,
            "fiscal_period": ["FY2023"] * 4,
            "signal_time": [
                "2024-01-10T14:15:00Z", "2024-01-10T14:45:00Z",
                "2024-03-20T12:05:00Z", "2024-03-20T12:15:00Z",
            ],
        }
    )
    versions = pd.DataFrame(
        {
            "issuer_cik": ["SIM-ISSUER-1", "SIM-ISSUER-1"],
            "fiscal_period": ["FY2023", "FY2023"],
            "available_at": ["2024-01-10T14:00:00Z", "2024-03-20T12:00:00Z"],
            "ingested_at": ["2024-01-10T14:30:00Z", "2024-03-20T12:10:00Z"],
            "accession": ["SIM-ORIGINAL", "SIM-RESTATED"],
            "revision_status": ["original", "restated"],
            "cfo_usd_millions": [20.0, 14.0],
        }
    )
    for frame, column in (
        (signals, "signal_time"),
        (versions, "available_at"),
        (versions, "ingested_at"),
    ):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return pit_asof_join(
        signals,
        versions,
        security_col="issuer_cik",
        period_col="fiscal_period",
        signal_time_col="signal_time",
        available_at_col="available_at",
        ingested_at_col="ingested_at",
    )


def apple_example_rows() -> dict[int, dict[str, float]]:
    """Return a fresh copy of the filing values for notebooks and tests."""
    return {year: values.copy() for year, values in APPLE_VALUES.items()}
