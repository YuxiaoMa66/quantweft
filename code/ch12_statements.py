"""Chapter 12 CLI and figure generation; calculations live in src package."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.statement_metrics import (  # noqa: E402
    apple_example_rows,
    apple_facts,
    derive_accounting_factors,
    fcf_from_statement_lines,
    fcf_yield,
    point_in_time_revision_demo,
    revenue_growth,
    spire_cash_flow_facts,
)


def _save_figures(output_dir: Path) -> tuple[Path, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    apple = apple_example_rows()

    years = ["FY2023", "FY2024"]
    cfo = np.array([apple[2023]["cfo"], apple[2024]["cfo"]])
    capex = -np.array([apple[2023]["capex_cash_flow"], apple[2024]["capex_cash_flow"]])
    fcf = cfo - capex
    x = np.arange(len(years))
    width = 0.24
    fig, ax = plt.subplots(figsize=(9.2, 5.8))
    fig.subplots_adjust(bottom=0.22, top=0.88)
    bars = [
        ax.bar(x - width, cfo, width, label="CFO", color="#235789"),
        ax.bar(x, capex, width, label="CapEx spend (positive)", color="#F0A202"),
        ax.bar(x + width, fcf, width, label="Defined FCF", color="#2A9D8F"),
    ]
    for group in bars:
        ax.bar_label(group, fmt="%.0f", padding=2, fontsize=8)
    ax.set_xticks(x, years)
    ax.set_xlabel("Fiscal year (FY2023 ended Sep 30; FY2024 ended Sep 28)")
    ax.set_ylabel("USD millions")
    ax.set_ylim(0, 132_000)
    ax.set_title("Apple FY2023–FY2024 operating cash and defined free cash flow")
    ax.legend(frameon=False, ncols=3, loc="upper left")
    ax.grid(axis="y", alpha=0.22)
    fig.text(
        0.02,
        0.025,
        "Source: Apple FY2024 Form 10-K, accession 0000320193-24-000123.\n"
        "FCF = CFO − positive PP&E purchases; a teaching definition, not a standardized GAAP line.",
        fontsize=8,
        va="bottom",
    )
    apple_path = output_dir / "ch12_apple_cashflow.png"
    fig.savefig(apple_path, dpi=180)
    plt.close(fig)

    versions = ["Original 2023 10-K", "Restated 2023 10-K/A"]
    spire_facts = [spire_cash_flow_facts(version) for version in ("original", "restated")]
    spire_cfo = np.array([cfo.value for cfo, _ in spire_facts])
    spire_capex = np.array([-capex.value for _, capex in spire_facts])
    spire_fcf = np.array(
        [fcf_from_statement_lines(cfo, capex) for cfo, capex in spire_facts]
    )
    x = np.arange(len(versions))
    fig, ax = plt.subplots(figsize=(9.2, 5.8))
    fig.subplots_adjust(bottom=0.22, top=0.88)
    groups = [
        ax.bar(x - width, spire_cfo, width, label="CFO", color="#235789"),
        ax.bar(x, spire_capex, width, label="CapEx spend (positive)", color="#F0A202"),
        ax.bar(x + width, spire_fcf, width, label="Defined FCF", color="#2A9D8F"),
    ]
    for group in groups:
        ax.bar_label(group, fmt="%.0f", padding=2, fontsize=8)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylim(-70_000, 42_000)
    ax.set_xticks(x, versions)
    ax.set_ylabel("USD thousands")
    ax.set_title("Spire FY2023 cash flow values before and after restatement")
    ax.legend(frameon=False, ncols=3, loc="upper right")
    ax.grid(axis="y", alpha=0.22)
    fig.text(
        0.02,
        0.025,
        "Sources: original 10-K accession 0000950170-24-027164; amended 10-K/A accession 0000950170-25-030856.\n"
        "CapEx is plotted as positive spend; FCF = CFO − CapEx. Values are USD thousands.",
        fontsize=8,
        va="bottom",
    )
    spire_path = output_dir / "ch12_spire_revision.png"
    fig.savefig(spire_path, dpi=180)
    plt.close(fig)
    return apple_path, spire_path


def main() -> None:
    output_dir = ROOT / "runs" / ("ch12_statements_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    print("Chapter 12: source-identified filings plus clearly labeled constructed inputs")
    print("Apple statement amounts are USD millions; source is the FY2024 10-K.")
    rows: dict[int, dict[str, float | None]] = {}
    apple = apple_example_rows()
    for year in (2023, 2024):
        rows[year] = derive_accounting_factors(apple_facts(year))
        print(
            f"FY{year}: revenue={apple[year]['revenue']:.0f}, "
            f"CFO={rows[year]['cfo_margin'] * apple[year]['revenue']:.0f}, "
            f"CapEx={rows[year]['capex_spend']:.0f}, FCF={rows[year]['fcf']:.0f}, "
            f"FCF margin={rows[year]['fcf_margin']:.4%}, "
            f"net debt={rows[year]['net_debt']:.0f}"
        )
    growth = revenue_growth(apple_facts(2024)["revenue"], apple_facts(2023)["revenue"])
    print(f"FY2024 revenue growth vs FY2023: {growth:.4%}")
    constructed_yield = fcf_yield(
        rows[2024]["fcf"],
        4_000_000.0,
        currency="USD",
        statement_unit="USD millions",
        market_cap_currency="USD",
        market_cap_unit="USD millions",
        market_cap_label="constructed teaching value",
    )
    print(
        "Constructed market-cap illustration: FCF yield at USD 4,000,000 million = "
        f"{constructed_yield:.4%}"
    )
    for version in ("original", "restated"):
        cfo_fact, capex_fact = spire_cash_flow_facts(version)
        fcf = fcf_from_statement_lines(cfo_fact, capex_fact)
        print(
            f"Spire FY2023 {version}: CFO={cfo_fact.value:.0f}, "
            f"CapEx={-capex_fact.value:.0f}, defined FCF={fcf:.0f} USD thousands"
        )
    print("\nConstructed PIT timestamps; ISO strings with Z are synthetic UTC inputs.")
    pit = point_in_time_revision_demo()
    print(pit[["signal_time", "accession", "revision_status", "cfo_usd_millions"]].to_string(index=False))
    apple_figure, spire_figure = _save_figures(output_dir)
    print(f"\nSaved figures: {apple_figure.relative_to(ROOT)}; {spire_figure.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
