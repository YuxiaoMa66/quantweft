"""Reproduce Chapter 17's fixed-seed simulations and descriptive data figures."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.cointegration import (  # noqa: E402
    engle_granger_test,
    screen_cointegration_pairs,
    simulate_cointegrated_pair,
    simulate_noncointegrated_common_trend,
    total_return_index_proxy,
    validate_monthly_frame,
)


FRENCH_SHA256 = "3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950"
INDUSTRIES = ["NoDur", "Durbl", "Manuf", "Enrgy", "HiTec", "Telcm", "Shops", "Hlth", "Utils", "Other"]


def load_french_monthly_returns(path: Path) -> pd.DataFrame:
    """Load and hash-check the frozen ten-industry decimal-return snapshot."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != FRENCH_SHA256:
        raise RuntimeError(f"French snapshot hash mismatch: {digest}")
    table = pd.read_csv(path, dtype={"month": "string"})
    if table.columns.tolist() != ["month", *INDUSTRIES]:
        raise ValueError("unexpected columns in frozen French 10-industry file")
    index = pd.PeriodIndex(table.pop("month"), freq="M", name="month")
    returns = pd.DataFrame(table.to_numpy(dtype=float), index=index, columns=INDUSTRIES)
    return validate_monthly_frame(returns, min_observations=24)


def create_simulation_figure(
    independent: pd.DataFrame,
    related: pd.DataFrame,
    output: Path,
) -> None:
    """Compare high-correlation I(1) levels with a known stationary spread."""
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    cases = [
        (independent, "Shared stochastic trend; no cointegration", None),
        (related, "Constructed cointegration; beta = 1.40", 1.4),
    ]
    for column, (frame, title, beta) in enumerate(cases):
        periods = frame.index.to_timestamp(how="start")
        axes[0, column].plot(periods, frame["x"], lw=0.8, color="#176B87", label="x(t)")
        axes[0, column].plot(periods, frame["y"], lw=0.8, color="#D05A36", label="y(t)")
        axes[0, column].set_title(title)
        axes[0, column].set_ylabel("Constructed level (arbitrary units)")
        axes[0, column].xaxis.set_major_locator(mdates.YearLocator(10))
        axes[0, column].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axes[0, column].grid(alpha=0.2)
        axes[0, column].legend(frameon=False)
        if beta is None:
            residual = frame["x"] - frame["y"]
            residual_label = "x − y (still I(1))"
        else:
            residual = frame["spread"]
            residual_label = "known y − 0.25 − 1.40x (I(0))"
        axes[1, column].plot(periods, residual, lw=0.8, color="#654A8B")
        axes[1, column].axhline(0.0, color="0.35", lw=0.7)
        axes[1, column].set_ylabel(residual_label + "\n(arbitrary units)")
        axes[1, column].set_xlabel("Calendar month")
        axes[1, column].xaxis.set_major_locator(mdates.YearLocator(10))
        axes[1, column].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axes[1, column].grid(alpha=0.2)
    figure.suptitle(
        "Constructed monthly processes: common movement is not enough; a stationary combination is",
        fontsize=12,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(figure)


def create_french_figure(index_proxy: pd.DataFrame, output: Path) -> None:
    """Plot all ten frozen industry TR-index proxies on a log vertical scale."""
    rebased = index_proxy.div(index_proxy.iloc[0]).mul(100.0)
    dates = rebased.index.to_timestamp(how="start")
    figure, axis = plt.subplots(figsize=(12, 6.5), constrained_layout=True)
    colors = plt.get_cmap("tab10").colors
    for color, column in zip(colors, rebased.columns):
        label = column.removesuffix("_TR_proxy")
        axis.plot(dates, rebased[column], lw=0.8, alpha=0.85, color=color, label=label)
    axis.set_yscale("log")
    axis.set_title("French 10-industry monthly returns compounded into teaching TR-index proxies")
    axis.set_xlabel("Month of published portfolio return")
    axis.set_ylabel("Index proxy (first available month rebased to 100; log scale)")
    axis.xaxis.set_major_locator(mdates.YearLocator(10))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axis.grid(alpha=0.2, which="both")
    axis.legend(ncol=5, frameon=False, fontsize=8, loc="upper left")
    figure.text(
        0.5,
        -0.01,
        "Source: 2026-10-05 frozen Kenneth French Data Library value-weighted monthly industry returns; descriptive, not PIT or tradable prices.",
        ha="center",
        fontsize=8,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    output_dir = ROOT / "runs" / ("ch17_time_series_ii_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--french-data", type=Path, help="User-authorized local frozen French CSV; exact SHA/columns required. No download.")
    args = parser.parse_args()
    independent = simulate_noncointegrated_common_trend(n=900, seed=20261017)
    related = simulate_cointegrated_pair(n=900, seed=20261018)
    independent_test = engle_granger_test(independent["x"], independent["y"], trend="c")
    related_test = engle_granger_test(related["y"], related["x"], trend="c")
    figure_sim = output_dir / "ch17_cointegration_simulation.png"
    create_simulation_figure(independent, related, figure_sim)

    print("CONSTRUCTED SIMULATIONS; not market evidence")
    print(
        f"noncointegrated common trend: seed=20261017, n=900, corr(levels)="
        f"{independent['x'].corr(independent['y']):.4f}, EG p={independent_test.pvalue:.6g}, "
        f"5% EG critical={independent_test.critical_values['5%']:.4f}"
    )
    print(
        f"cointegrated construction: seed=20261018, n=900, corr(levels)="
        f"{related['x'].corr(related['y']):.4f}, EG p={related_test.pvalue:.6g}, "
        f"5% EG critical={related_test.critical_values['5%']:.4f}"
    )

    print(f"figure: {figure_sim.relative_to(ROOT)}")
    if args.french_data is None:
        print("SKIPPED French branch: no authorized local --french-data supplied; no download or substitute data.")
        return
    returns = load_french_monthly_returns(args.french_data)
    index_proxy = total_return_index_proxy(returns)
    figure_french = output_dir / "ch17_french_industry_trindex.png"
    create_french_figure(index_proxy, figure_french)
    training_end = pd.Period("2000-12", freq="M")
    screen = screen_cointegration_pairs(index_proxy, training_end=training_end, trend="c")
    print("FRENCH INDUSTRY RETURNS COMPOUNDED TO TR-INDEX PROXIES; descriptive only")
    print(
        f"monthly observations={len(returns)}, sample={returns.index[0]}–{returns.index[-1]}, "
        f"columns={len(returns.columns)}, source decimal returns; not single stocks, not PIT"
    )
    print(
        f"all {len(screen)} unordered pairs screened only through {training_end}: "
        f"minimum EG p={screen['pvalue'].min():.6g}; median EG p={screen['pvalue'].median():.6g}; "
        f"nominal p<.05={(screen['pvalue'] < 0.05).sum()}; BH q<.05={(screen['qvalue_bh'] < 0.05).sum()}"
    )
    print(screen.to_string(index=False))  # P03: retain every pair, not only significant ones.
    print("  Pair tests are exploratory and multiple comparisons remain; no pair is selected for trading.")
    print(f"figures: {figure_sim.relative_to(ROOT)}, {figure_french.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
