"""Chapter 1: a simulated signal-to-PnL lifecycle with gross and net returns."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course import compute_returns


def main() -> None:
    output_dir = ROOT / "runs" / ("ch01_lifecycle_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    # Constructed New York timestamps: the schedule is a simplified teaching
    # convention, not actual security trading or a live exchange calendar.
    # The 16:05 signal follows the regular 16:00 close; 09:30 is the next open.
    timeline = {
        "signal_time": "2024-01-02 16:05 America/New_York",
        "trade_time": "2024-01-03 09:30 America/New_York",
        "return_interval": "2024-01-03 09:30 to 2024-01-04 09:30 America/New_York",
    }
    holding_times = pd.date_range(
        "2024-01-03 09:30", periods=2, freq="D", tz="America/New_York"
    )
    prices = pd.DataFrame(
        {"asset_a": [100.0, 102.0], "asset_b": [100.0, 99.0]},
        index=holding_times,
    )
    asset_returns = np.array(
        [compute_returns(prices[asset]).iloc[-1] for asset in prices.columns]
    )
    weights = np.array([0.6, 0.2])
    cash_weight = 0.2
    cash_return = 0.0
    gross = float(np.dot(weights, asset_returns) + cash_weight * cash_return)

    # A 10 bp fee is charged on 20% gross traded notional (buys + sells, not halved).
    trade_increments = np.array([0.1, -0.1])
    total_traded_notional_ratio = float(np.abs(trade_increments).sum())
    cost_rate = 10 / 10_000
    cost = total_traded_notional_ratio * cost_rate
    net = gross - cost
    nav0 = 100_000.0
    nav1 = nav0 * (1.0 + net)

    print("SIMULATED lifecycle example (constructed inputs; not market data)")
    for key, value in timeline.items():
        print(f"{key}: {value}")
    print(f"gross return: {gross:.4%}")
    print(f"total traded notional ratio (buys + sells): {total_traded_notional_ratio:.1%}")
    print(f"transaction cost: {cost:.4%} of NAV (10 bp per traded notional)")
    print(f"net return: {net:.4%}")
    print(f"NAV: {nav0:,.0f} -> {nav1:,.0f} capital units")

    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["Gross return", "Trading cost", "Net return"]
    values = [gross * 100, -cost * 100, net * 100]
    colors = ["#2878B5", "#D9534F", "#4C9F70"]
    bars = ax.bar(labels, values, color=colors)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylabel("Return (%)")
    ax.set_title("Simulated one-period gross and net return")
    ax.bar_label(bars, fmt="%.2f%%")
    fig.tight_layout()
    output = output_dir / "ch01_gross_net.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
