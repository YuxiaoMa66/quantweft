"""Chapter 3: constructed split/dividend, PIT revision, and DST examples."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course import pit_asof_join


def main() -> None:
    output_dir = ROOT / "runs" / ("ch03_data_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    actions = pd.read_csv(ROOT / "data" / "fixtures" / "a1_corporate_actions.csv")
    action = actions.iloc[0]
    adjusted_value = action.split_ratio * action.post_action_price
    adjusted_dividend = action.split_ratio * action.new_share_cash_dividend
    action_return = (adjusted_value + adjusted_dividend) / action.pre_action_price - 1.0
    print("SIMULATED corporate-action example (constructed inputs; not market data)")
    print(
        f"2-for-1 split: {action.split_ratio:g} * {action.post_action_price:g} "
        f"+ {action.split_ratio:g} * {action.new_share_cash_dividend:g} "
        f"= {adjusted_value + adjusted_dividend:g}; return={action_return:.2%}"
    )

    signals = pd.read_csv(ROOT / "data" / "fixtures" / "a1_pit_signals.csv")
    versions = pd.read_csv(ROOT / "data" / "fixtures" / "a1_pit_versions.csv")
    signals["signal_time"] = pd.to_datetime(signals["signal_time"], utc=True)
    for column in ("available_at", "ingested_at"):
        versions[column] = pd.to_datetime(versions[column], utc=True)
    joined = pit_asof_join(signals, versions)
    print("PIT filing versions by signal time:")
    print(joined[["signal_id", "security_id", "signal_time", "version_id", "eps", "pit_effective_at"]].to_string(index=False))

    # In New York, local clocks jump from 01:59:59 EST to 03:00:00 EDT.
    dst = pd.to_datetime(
        ["2024-03-10T01:30:00-05:00", "2024-03-10T03:30:00-04:00"], utc=True
    ).tz_convert("America/New_York")
    elapsed_hours = (dst[1] - dst[0]).total_seconds() / 3600
    print(f"DST boundary: {dst[0]} -> {dst[1]}; elapsed UTC time={elapsed_hours:.0f} hour")

    fig, ax = plt.subplots(figsize=(9, 4.2))
    filing = joined[joined["security_id"] == "SIM-FILING-1"].copy()
    x = filing["signal_time"].dt.tz_convert("UTC")
    values = filing["eps"].to_numpy(dtype="float64", na_value=float("nan"))
    ax.step(x, values, where="post", color="#2878B5", linewidth=2, label="PIT-visible EPS")
    ax.scatter(x, values, color="#2878B5", zorder=3)
    ax.axvline(pd.Timestamp("2024-03-15T20:12:00Z"), color="#E38B2C", linestyle="--", label="Original ingested")
    ax.axvline(pd.Timestamp("2024-04-02T20:08:00Z"), color="#D9534F", linestyle="--", label="Restatement ingested")
    ax.set_title("Simulated filing: a restatement affects later signals only")
    ax.set_xlabel("signal time (UTC)")
    ax.set_ylabel("EPS visible at signal time (constructed currency/unit)")
    ax.grid(alpha=0.25)
    locator = mdates.AutoDateLocator(maxticks=5)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.legend()
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    output = output_dir / "ch03_timeline.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
