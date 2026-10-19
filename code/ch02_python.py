"""Chapter 2: Python, NumPy, pandas, Polars, SciPy, and plotting examples."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course import compute_returns


def main() -> None:
    output_dir = ROOT / "runs" / ("ch02_python_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    fixture = ROOT / "data" / "fixtures" / "a1_prices.csv"
    long = pd.read_csv(fixture, parse_dates=["timestamp"])
    long["timestamp"] = pd.to_datetime(long["timestamp"], utc=True)

    # Basic Python and NumPy: a list comprehension, an array, and vectorized math.
    example_prices = [100.0, 110.0, 99.0]
    price_array = np.asarray(example_prices, dtype=float)
    hand_returns = price_array[1:] / price_array[:-1] - 1.0
    hand_cumulative_return = float(np.prod(1.0 + hand_returns) - 1.0)

    # Pivot keeps one timestamp index; the shared src function applies the same
    # return contract separately to each security column.
    panel = long.pivot(index="timestamp", columns="security_id", values="close").sort_index()
    returns = panel.apply(compute_returns)
    rolling_mean = returns.rolling(window=2, min_periods=2).mean()
    expanding_vol = returns.expanding(min_periods=2).std(ddof=1)
    lagged_returns = returns.shift(1)
    cross_section_rank = returns.rank(axis=1, method="average", pct=True)
    security_mean = long.groupby("security_id", sort=True)["close"].mean()
    monthly_input = long.assign(observation_time=long["timestamp"]).set_index("timestamp")
    monthly_sample = (
        monthly_input.groupby("security_id")
        .resample("ME")[["observation_time", "close"]]
        .last(skipna=False)
    )
    monthly_sample.index = monthly_sample.index.set_names(["security_id", "period_end"])

    # Polars expressions perform within-security shift and ranking after sorting.
    pl_long = pl.read_csv(fixture).with_columns(
        pl.col("timestamp").str.to_datetime(time_zone="UTC", strict=True)
    ).sort(["security_id", "timestamp"])
    pl_panel = pl_long.with_columns(
        (pl.col("close") / pl.col("close").shift(1).over("security_id") - 1.0)
        .alias("simple_return")
    ).with_columns(
        pl.col("simple_return").rank(method="average").over("timestamp").alias("date_rank")
    )
    pl_means = pl_long.group_by("security_id").agg(pl.col("close").mean().alias("mean_close"))

    print("SIMULATED Python toolkit examples (constructed prices; not market data)")
    print(
        f"hand-check prices={example_prices}; vectorized simple returns={hand_returns.tolist()}; "
        f"cumulative return={hand_cumulative_return:.2%}"
    )
    print("pandas returns:")
    print(returns.to_string())
    print("rolling 2-row mean:")
    print(rolling_mean.to_string())
    print("expanding sample volatility:")
    print(expanding_vol.to_string())
    print("one-row shift (earlier information):")
    print(lagged_returns.to_string())
    print("same-date percentile ranks:")
    print(cross_section_rank.to_string())
    print("grouped mean closes:")
    print(security_mean.to_string())
    print("resample bins: period_end is a bin label; observation_time is the last actual input row:")
    print(monthly_sample.to_string())
    paired_returns = returns[["SIM-ALPHA", "SIM-BETA"]].dropna()
    rho = float(spearmanr(paired_returns["SIM-ALPHA"], paired_returns["SIM-BETA"]).statistic)
    print(f"SciPy Spearman rho on pairwise-aligned returns: {rho:.4f}")
    print("Polars grouped mean closes:")
    print(pl_means)
    print("Polars shifted returns and same-date ranks:")
    print(pl_panel.select("security_id", "timestamp", "simple_return", "date_rank"))

    ax = returns.plot(marker="o", figsize=(8, 4), title="Simulated daily simple returns")
    ax.set_xlabel("UTC close timestamp")
    ax.set_ylabel("Simple return")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.grid(alpha=0.25)
    fig = ax.get_figure()
    fig.tight_layout()
    output = output_dir / "ch02_returns.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
