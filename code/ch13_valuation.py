"""Chapter 13 examples and figure generation; formulas live in src/quant_course."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.valuation import (  # noqa: E402
    Amount,
    FinancialVintage,
    MarketCapSnapshot,
    constructed_company_cases,
    discounted_cash_flow_value,
    enterprise_multiple,
    enterprise_value,
    earnings_yield,
    equity_from_enterprise_value,
    fcf_yield,
    gordon_terminal_value,
    industry_percentile_ranks,
    pit_fcf_yield,
    price_to_book,
    price_to_earnings,
    select_pit_vintage,
    weighted_average_cost_of_capital,
)


def _amount(case: dict[str, Amount | float | str], key: str) -> Amount:
    value = case[key]
    if not isinstance(value, Amount):
        raise TypeError(f"{key} is not an Amount")
    return value


def _save_figures(output_dir: Path) -> tuple[Path, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    cases = constructed_company_cases()
    bridge_path = output_dir / "ch13_ev_bridge.png"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10.0, 7.2))
    row_y: list[int] = []
    row_names: list[str] = []
    for company_index, company_name in enumerate(("Orion", "Lyra")):
        case = cases[company_name]
        components = [
            ("Equity market cap", _amount(case, "market_cap").value, "#235789"),
            ("Debt", _amount(case, "debt").value, "#3A86A8"),
            ("Preferred equity", _amount(case, "preferred").value, "#7BB3C8"),
            ("Noncontrolling interest", _amount(case, "nci").value, "#A8DADC"),
            ("Cash", -_amount(case, "cash").value, "#E76F51"),
            ("Nonoperating assets", -_amount(case, "nonoperating_assets").value, "#F4A261"),
        ]
        cumulative = 0.0
        base_y = 11 - company_index * 7
        for component_index, (component, value, color) in enumerate(components):
            y = base_y - component_index
            left = cumulative if value >= 0 else cumulative + value
            ax.barh(y, abs(value), left=left, height=0.54, color=color, edgecolor="white")
            if value != 0:
                ax.text(left + abs(value) / 2, y, f"{value:+.0f}", ha="center", va="center", fontsize=8)
            row_y.append(y)
            row_names.append(f"{company_name}: {component}")
            cumulative += value
        ev = enterprise_value(
            _amount(case, "market_cap"), _amount(case, "debt"), _amount(case, "cash"),
            noncontrolling_interest=_amount(case, "nci"),
            preferred_equity=_amount(case, "preferred"),
            nonoperating_assets=_amount(case, "nonoperating_assets"),
        )
        ax.plot([ev.value, ev.value], [base_y + 0.45, base_y - 5.45],
                color="#172A3A", linewidth=1.2, linestyle="--")
        ax.text(ev.value + 8, base_y - 2.5, f"EV = {ev.value:.0f}",
                va="center", fontsize=9, fontweight="bold")

    ax.set_yticks(row_y, row_names)
    ax.set_xlabel("USD millions; each bar adds to or subtracts from the prior total")
    ax.set_title("Enterprise value bridge for two constructed companies")
    ax.set_xlim(-20, 900)
    ax.grid(axis="x", alpha=0.2)
    fig.text(
        0.02, 0.015,
        "Constructed teaching inputs at one synthetic signal cut. Lyra also adds preferred equity and NCI, then subtracts cash and nonoperating assets.",
        fontsize=8, va="bottom",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(bridge_path, dpi=180)
    plt.close(fig)

    forecast = [Amount(value, "USD", "USD millions") for value in (40, 45, 50, 55, 60)]
    wacc_values = np.array([0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12])
    growth_values = np.array([0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06])
    shares = np.full((len(growth_values), len(wacc_values)), np.nan)
    for growth_index, growth in enumerate(growth_values):
        for wacc_index, rate in enumerate(wacc_values):
            if growth >= rate:
                continue
            tv = gordon_terminal_value(forecast[-1], rate, growth)
            total = discounted_cash_flow_value(
                forecast, rate, cash_flow_basis="FCFF", discount_rate_basis="WACC", terminal_value=tv
            )
            pv_tv = tv.value / (1.0 + rate) ** len(forecast)
            shares[growth_index, wacc_index] = pv_tv / total.value * 100.0

    terminal_path = output_dir / "ch13_terminal_sensitivity.png"
    fig, ax = plt.subplots(figsize=(9.0, 6.2))
    image = ax.imshow(shares, origin="lower", aspect="auto", cmap="viridis", vmin=55, vmax=100)
    ax.set_xticks(np.arange(len(wacc_values)), [f"{value:.0%}" for value in wacc_values])
    ax.set_yticks(np.arange(len(growth_values)), [f"{value:.0%}" for value in growth_values])
    ax.set_xlabel("WACC used for FCFF (annual rate)")
    ax.set_ylabel("Perpetual growth rate g (annual rate)")
    ax.set_title("Terminal value share of DCF enterprise value")
    fig.colorbar(image, ax=ax, label="PV of terminal value / total DCF value (%)")
    for growth_index, rate_index in zip(*np.where(np.isfinite(shares))):
        ax.text(rate_index, growth_index, f"{shares[growth_index, rate_index]:.0f}",
                ha="center", va="center", fontsize=7,
                color="white" if shares[growth_index, rate_index] < 84 else "black")
    ax.text(0.03, -0.20,
            "Forecast FCFF = 40, 45, 50, 55, 60 USD millions at years 1–5. Blank cells have g ≥ WACC and are undefined.",
            transform=ax.transAxes, fontsize=8)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(terminal_path, dpi=180)
    plt.close(fig)
    return bridge_path, terminal_path


def _constructed_vintages_and_market_caps() -> tuple[list[FinancialVintage], list[MarketCapSnapshot]]:
    utc = timezone.utc
    old = FinancialVintage(
        issuer_id="SIM-ORION", security_id="SIM-ORION-COMMON", fiscal_period="FY2024",
        period_end=date(2024, 12, 31), available_at=datetime(2025, 2, 15, 8, tzinfo=utc),
        ingested_at=datetime(2025, 2, 16, 10, tzinfo=utc), accession="SIM-ORION-FY24-V1",
        currency="USD", unit="USD millions", net_income_common=30, common_book_equity=180,
        ebit=50, ebitda=75, free_cash_flow=28, cash_flow_basis="FCFE", industry="Industrial software",
    )
    revised = FinancialVintage(
        issuer_id="SIM-ORION", security_id="SIM-ORION-COMMON", fiscal_period="FY2024",
        period_end=date(2024, 12, 31), available_at=datetime(2025, 4, 2, 8, tzinfo=utc),
        ingested_at=datetime(2025, 4, 2, 9, tzinfo=utc), accession="SIM-ORION-FY24-V2",
        currency="USD", unit="USD millions", net_income_common=27, common_book_equity=177,
        ebit=48, ebitda=73, free_cash_flow=25, cash_flow_basis="FCFE", industry="Industrial software",
    )
    market_caps = [
        MarketCapSnapshot(
            security_id="SIM-ORION-COMMON", as_of=datetime(2025, 3, 31, 20, tzinfo=utc),
            market_cap=Amount(600, "USD", "USD millions"),
        ),
        MarketCapSnapshot(
            security_id="SIM-ORION-COMMON", as_of=datetime(2025, 4, 2, 20, tzinfo=utc),
            market_cap=Amount(620, "USD", "USD millions"),
        ),
    ]
    return [old, revised], market_caps


def main() -> None:
    output_dir = ROOT / "runs" / ("ch13_valuation_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    print("Chapter 13: constructed valuation cases; no market price or backtest is asserted")
    cases = constructed_company_cases()
    for company, case in cases.items():
        market_cap = _amount(case, "market_cap")
        ev = enterprise_value(
            market_cap, _amount(case, "debt"), _amount(case, "cash"),
            noncontrolling_interest=_amount(case, "nci"),
            preferred_equity=_amount(case, "preferred"),
            nonoperating_assets=_amount(case, "nonoperating_assets"),
        )
        equity_check = equity_from_enterprise_value(
            ev, _amount(case, "debt"), _amount(case, "cash"),
            noncontrolling_interest=_amount(case, "nci"),
            preferred_equity=_amount(case, "preferred"),
            nonoperating_assets=_amount(case, "nonoperating_assets"),
        )
        pe = price_to_earnings(market_cap, _amount(case, "net_income"))
        pb = price_to_book(market_cap, _amount(case, "book_equity"))
        ev_ebitda = enterprise_multiple(ev, _amount(case, "ebitda"))
        ev_ebit = enterprise_multiple(ev, _amount(case, "ebit"))
        fcfe_yield = fcf_yield(
            _amount(case, "fcfe"), market_cap, cash_flow_basis="FCFE", claim_basis="Equity"
        )
        fcff_yield = fcf_yield(
            _amount(case, "fcff"), ev, cash_flow_basis="FCFF", claim_basis="EV"
        )
        print(
            f"{company}: cap={market_cap.value:.0f}, EV={ev.value:.0f}, bridge-back equity={equity_check.value:.0f}, "
            f"P/E={pe:.2f}x, P/B={pb:.2f}x, EV/EBITDA={ev_ebitda:.2f}x, "
            f"EV/EBIT={ev_ebit:.2f}x, FCFE/equity={fcfe_yield:.2%}, FCFF/EV={fcff_yield:.2%}"
        )
    orion = cases["Orion"]
    wacc = weighted_average_cost_of_capital(
        _amount(orion, "market_cap"), _amount(orion, "debt"),
        cost_of_equity=0.10, cost_of_debt=0.06, tax_rate=0.25,
    )
    print(f"Orion constructed market-value WACC with 25% tax assumption: {wacc:.4%}")

    forecast = [Amount(value, "USD", "USD millions") for value in (40, 45, 50, 55, 60)]
    rate, growth = 0.09, 0.03
    tv = gordon_terminal_value(forecast[-1], rate, growth)
    dcf = discounted_cash_flow_value(
        forecast, rate, cash_flow_basis="FCFF", discount_rate_basis="WACC", terminal_value=tv
    )
    pv_tv = tv.value / (1 + rate) ** len(forecast)
    print(
        f"Constructed FCFF DCF at WACC={rate:.1%}, g={growth:.1%}: TV={tv.value:.2f}, "
        f"EV={dcf.value:.2f}, PV(TV)/EV={pv_tv / dcf.value:.2%} USD millions"
    )

    vintages, caps = _constructed_vintages_and_market_caps()
    signal = datetime(2025, 3, 31, 20, tzinfo=timezone.utc)
    yield_value, vintage, cap = pit_fcf_yield(
        vintages, caps, security_id="SIM-ORION-COMMON", fiscal_period="FY2024", signal_time=signal
    )
    print(
        f"PIT demonstration at {signal.isoformat()}: accession={vintage.accession}, "
        f"market_cap_as_of={cap.as_of.isoformat()}, FCFE yield={yield_value:.2%}"
    )
    print("Synthetic trade_time is later than signal_time; no return interval or performance is calculated.")
    ranks = industry_percentile_ranks(
        {"SIM-A": 0.05, "SIM-B": 0.04, "SIM-C": 0.07, "SIM-D": None},
        {"SIM-A": "Software", "SIM-B": "Software", "SIM-C": "Banks", "SIM-D": "Software"},
    )
    print(f"Constructed same-date industry percentile ranks: {ranks}")
    bridge, sensitivity = _save_figures(output_dir)
    print(f"Saved figures: {bridge.relative_to(ROOT)}; {sensitivity.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
