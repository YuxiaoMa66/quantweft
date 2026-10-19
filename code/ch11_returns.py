"""Chapter 11: exact constructed cases and descriptive published returns.

Run from the course root. Market inputs are frozen French monthly published
portfolio returns, not prices, OHLCV or point-in-time strategy forecasts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from uuid import uuid4
CLI_RUN = Path(__file__).resolve().parents[1] / "runs" / ("cli_ch11_returns_" + uuid4().hex)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from quant_course.market_data import load_monthly_snapshot
from quant_course.performance import (
    annualized_volatility, cagr, drawdown_path, geometric_mean_return,
    sharpe_ratio, wealth_index,
)


def monthly_example() -> pd.DataFrame:
    industry = json.loads((ROOT / "data/manifests/french_industries_2026-10-05.json").read_text())
    factors = json.loads((ROOT / "data/manifests/french_factors_2026-10-05.json").read_text())["datasets"]["ff3"]
    returns = load_monthly_snapshot(
        ROOT / industry["processed_path"], industry["processed_sha256"], ["NoDur"]
    )
    rf = load_monthly_snapshot(
        ROOT / factors["processed_path"], factors["processed_sha256"], ["RF"]
    )
    sample = returns.loc["2010-01":"2019-12"].join(rf, how="left", validate="one_to_one")
    required = pd.period_range("2010-01", "2019-12", freq="M", name="month")
    if not sample.index.equals(required) or sample.isna().any().any():
        raise ValueError("the declared 120-month sample or same-month RF is incomplete")
    if (sample.to_numpy() <= -1).any():
        raise ValueError("the log-return example requires strictly positive gross returns")
    return sample


def summarize_monthly(sample: pd.DataFrame) -> dict[str, Any]:
    returns = sample["NoDur"].to_numpy(dtype=float)
    rf = sample["RF"].to_numpy(dtype=float)
    wealth = wealth_index(returns)
    return {
        "sample_start": str(sample.index[0]), "sample_end": str(sample.index[-1]),
        "n_months": len(sample), "frequency": "monthly",
        "wealth_initial": 1.0, "wealth_final": float(wealth[-1]),
        "simple_mean_per_month": float(returns.mean()),
        "log_mean_per_month": float(np.log1p(returns).mean()),
        "geometric_mean_per_month": geometric_mean_return(returns),
        "cagr_month_period_convention": cagr(1.0, float(wealth[-1]), len(sample) / 12),
        "sample_sd_per_month": float(returns.std(ddof=1)),
        "volatility_sqrt12_convention": annualized_volatility(returns, 12),
        "rf_mean_per_month": float(rf.mean()),
        "excess_mean_per_month": float((returns - rf).mean()),
        "sharpe_sqrt12_convention": sharpe_ratio(returns, rf, 12),
        "maximum_drawdown_positive_loss": -float(drawdown_path(wealth).min()),
        "scope": "descriptive current published snapshot; not ex-ante, PIT or tradable strategy",
    }


def make_figure(sample: pd.DataFrame, destination: Path) -> None:
    returns = sample["NoDur"]
    # The preceding month labels chosen initial capital, not an observed price.
    wealth_months = pd.period_range(sample.index[0] - 1, sample.index[-1], freq="M")
    dates = wealth_months.to_timestamp(how="end")
    wealth = wealth_index(returns.to_numpy())
    return_dates = sample.index.to_timestamp(how="end")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    axes[0, 0].plot(dates, wealth, color="#247F82")
    axes[0, 0].set(title="Published NoDur total-return wealth index", ylabel="Initial capital = 1")
    axes[0, 1].hist(returns, bins=20, color="#247F82", edgecolor="white")
    axes[0, 1].set(title="Monthly simple returns", xlabel="Decimal return per month", ylabel="Month count")
    rolling = returns.rolling(12, min_periods=12).std(ddof=1) * np.sqrt(12)
    axes[1, 0].plot(return_dates, rolling, color="#CF8951")
    axes[1, 0].set(title="12-month rolling volatility", ylabel="SD × sqrt(12) convention")
    axes[1, 1].fill_between(dates, drawdown_path(wealth), 0, color="#CF8951", alpha=0.55)
    axes[1, 1].set(title="Drawdown including initial capital", ylabel="Negative fraction below prior peak")
    for i, ax in enumerate(axes.flat):
        ax.grid(alpha=0.2)
        if i != 1:
            ax.set_xlabel("Calendar month end (interval label)")
    fig.suptitle("French current snapshot | 2010–2019 | descriptive analysis, no strategy claim", fontsize=11)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main() -> None:
    print("Constructed: +50%, then -50%; capital 100")
    print("wealth", wealth_index([0.5, -0.5], 100))
    print("arithmetic mean", np.mean([0.5, -0.5]))
    print("geometric mean", geometric_mean_return([0.5, -0.5]))
    print("2-year CAGR", cagr(100, 75, 2))
    sample = monthly_example()
    report = summarize_monthly(sample)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    output = CLI_RUN / "ch11_actual_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    make_figure(sample, CLI_RUN / "figures/a3/ch11_returns_dashboard.png")


if __name__ == "__main__":
    main()
