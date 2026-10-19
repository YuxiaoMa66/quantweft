"""Run the reproducible simulations and monthly-data example for Chapter 16."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.time_series import (  # noqa: E402
    ar1_theoretical_moments,
    rolling_origin_forecast,
    sample_acf_pacf,
    simulate_stationary_pair,
    validate_monthly_series,
)


def load_french_no_dur() -> pd.Series:
    """Read the frozen monthly 10-industry snapshot as decimal returns."""
    path = ROOT / "data/processed/french_10_industries_monthly.csv"
    table = pd.read_csv(path, dtype={"month": "string"})
    if "month" not in table or "NoDur" not in table:
        raise ValueError("the French snapshot must contain month and NoDur columns")
    index = pd.PeriodIndex(table.pop("month"), freq="M", name="month")
    series = pd.Series(table["NoDur"].to_numpy(dtype=float), index=index, name="NoDur")
    return validate_monthly_series(series, min_observations=24)


def create_figure(data: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    series_specs = [
        (axes[0, 0], axes[1, 0], data["iid"], "Gaussian IID", np.zeros(18)),
        (
            axes[0, 1],
            axes[1, 1],
            data["ar1"],
            "Stationary AR(1), $\\phi=0.70$",
            np.array([0.7**lag for lag in range(1, 19)]),
        ),
    ]
    month_axis = data.index.to_timestamp(how="start")
    for path_ax, acf_ax, series, title, theoretical_acf in series_specs:
        path_ax.plot(month_axis, series.to_numpy() * 100.0, lw=0.8, color="#176B87")
        path_ax.axhline(0.0, color="0.35", lw=0.7)
        path_ax.set_title(title)
        path_ax.set_ylabel("Monthly return (%)")
        path_ax.xaxis.set_major_locator(mdates.YearLocator(10))
        path_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        path_ax.grid(alpha=0.18)

        estimated = sample_acf_pacf(series, lags=18)["acf"].to_numpy()
        lags = np.arange(1, len(estimated) + 1)
        acf_ax.axhline(0.0, color="0.35", lw=0.7)
        acf_ax.vlines(lags, 0.0, estimated, color="#176B87", lw=1.3, label="Sample ACF")
        acf_ax.scatter(lags, estimated, color="#176B87", s=13)
        acf_ax.plot(lags, theoretical_acf, color="#D05A36", marker="o", ms=3, lw=1.0, label="Theoretical ACF")
        acf_ax.set_xlabel("Lag (months)")
        acf_ax.set_ylabel("Autocorrelation")
        acf_ax.set_xticks([1, 3, 6, 9, 12, 15, 18])
        acf_ax.grid(alpha=0.18)
        acf_ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Same theoretical mean and variance, different serial dependence", fontsize=13)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch16_time_series_" + uuid.uuid4().hex)
    import argparse
    argparse.ArgumentParser(description="Historical chapter CLI; French route requires separate rights and authorization; use the notebook for default offline teaching").parse_args()
    data = simulate_stationary_pair(
        n=480, seed=20261016, mean=0.005, marginal_sd=0.04, phi=0.7, start="1980-01"
    )
    theory = ar1_theoretical_moments(
        mean=0.005,
        phi=0.7,
        innovation_sd=0.04 * np.sqrt(1.0 - 0.7**2),
        max_lag=3,
    )
    output = default_run / "figures" / "ch16_stationarity_acf.png"
    create_figure(data, output)

    print("CONSTRUCTED SIMULATION; seed=20261016; monthly PeriodIndex; 480 observations")
    print(f"AR(1) theoretical mean={theory.mean:.6f}, variance={theory.variance:.6f}, ACF[1:4]={theory.autocorrelations[1:]}")
    print("sample mean, sd, lag-1 ACF:")
    for name in ("iid", "ar1"):
        values = data[name]
        acf_values = sample_acf_pacf(values, lags=12)
        print(
            f"  {name}: mean={values.mean():.6f}, sd={values.std(ddof=1):.6f}, "
            f"ACF(1)={acf_values.loc[1, 'acf']:.6f}"
        )

    held_out = rolling_origin_forecast(data["ar1"], initial_train_size=360, order=(1, 0, 0))
    mean_predictions = np.array(
        [data["ar1"].iloc[:position].mean() for position in range(360, len(data))]
    )
    ar_rmse = float(np.sqrt(np.mean((held_out["actual"].to_numpy() - held_out["forecast"].to_numpy()) ** 2)))
    mean_rmse = float(np.sqrt(np.mean((held_out["actual"].to_numpy() - mean_predictions) ** 2)))
    interval_coverage = float(
        ((held_out["actual"] >= held_out["lower"]) & (held_out["actual"] <= held_out["upper"]))
        .mean()
    )
    print(
        f"SIMULATED expanding-window one-step holdout: {held_out.index[0]}–{held_out.index[-1]}, "
        f"initial train=360 months"
    )
    print(f"  ARIMA(1,0,0) RMSE={ar_rmse:.6f}; expanding training-mean RMSE={mean_rmse:.6f}; 95% interval coverage={interval_coverage:.3f}")
    print("  This is a known-parameter simulation exercise, not evidence of market predictability.")

    french = load_french_no_dur()
    french_acf = sample_acf_pacf(french, lags=12)
    print("FRENCH 10 INDUSTRY SNAPSHOT; descriptive only; current published vintage, not point-in-time")
    print(
        f"  NoDur: n={len(french)}, sample={french.index[0]}–{french.index[-1]}, "
        f"unit=decimal monthly return, mean={french.mean():.6f}, sd={french.std(ddof=1):.6f}, "
        f"ACF(1)={french_acf.loc[1, 'acf']:.6f}, ACF(12)={french_acf.loc[12, 'acf']:.6f}"
    )
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
