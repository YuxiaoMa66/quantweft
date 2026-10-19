"""Reproduce Chapter 18 volatility examples from the frozen French cache.

The script is intentionally a workflow around ``quant_course.volatility``;
it does not implement a second estimator. Returns are monthly decimals and
forecasts are one-month-ahead variances in decimal-return squared units.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from quant_course.volatility import (  # noqa: E402
    GARCHParameters,
    ewma_variance_path,
    fit_garch11,
    garch_variance_forecast,
    garch_variance_path,
    qlike_loss,
    rolling_variance_forecast,
    simulate_garch11,
)

INDUSTRY_CSV = ROOT / "data/processed/french_10_industries_monthly.csv"
MANIFEST = ROOT / "data/manifests/french_industries_2026-10-05.json"
RAW_ZIP = ROOT / "data/raw/french/2026-10-05/10_Industry_Portfolios_CSV.zip"
RAW_CSV = ROOT / "data/raw/french/2026-10-05/extracted/10_Industry_Portfolios.csv"
TRAIN_START, TRAIN_END = "1990-01", "2006-12"
EVAL_START, EVAL_END = "2007-01", "2009-12"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_industries() -> tuple[pd.DataFrame, dict[str, str]]:
    """Load local data only and refuse a modified or substituted snapshot."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {"raw_zip": RAW_ZIP, "extracted_csv": RAW_CSV, "processed_csv": INDUSTRY_CSV}
    expected = {
        "raw_zip": manifest["sha256"],
        "extracted_csv": manifest["extracted_sha256"],
        "processed_csv": manifest["processed_sha256"],
    }
    actual: dict[str, str] = {}
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Frozen French input missing: {path}")
        actual[name] = sha256(path)
        if actual[name] != expected[name]:
            raise ValueError(f"Frozen French {name} hash differs from manifest")
    frame = pd.read_csv(INDUSTRY_CSV, parse_dates=False)
    if frame.columns[0] != "month" or "NoDur" not in frame:
        raise ValueError("French cache does not match the declared monthly industry schema")
    frame["month"] = pd.PeriodIndex(frame["month"].astype(str), freq="M")
    frame = frame.set_index("month").sort_index()
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("French monthly periods must be unique and ordered")
    if str(frame.index[0]) != manifest["first_month"][:4] + "-" + manifest["first_month"][4:]:
        raise ValueError("French first period differs from manifest")
    return frame, actual


def _monthly_slice(series: pd.Series, start: str, end: str) -> pd.Series:
    selected = series.loc[pd.Period(start, freq="M"):pd.Period(end, freq="M")].copy()
    expected = pd.period_range(start, end, freq="M")
    if not selected.index.equals(expected):
        raise ValueError(f"Expected a complete monthly sample from {start} to {end}")
    return selected


def _acf(values: np.ndarray, max_lag: int = 24) -> np.ndarray:
    centered = np.asarray(values, dtype=float) - np.mean(values)
    denominator = centered @ centered
    if denominator <= 0:
        raise ValueError("ACF is undefined for a constant series")
    return np.array([centered[lag:] @ centered[:-lag] / denominator
                     for lag in range(1, max_lag + 1)])


def _params_dict(fit: Any) -> dict[str, float | int | str]:
    p = fit.parameters
    return {
        "mean_monthly_decimal": fit.mean,
        "omega_decimal_return_squared": p.omega,
        "alpha": p.alpha,
        "beta": p.beta,
        "persistence_alpha_plus_beta": p.persistence,
        "unconditional_variance_decimal_squared": p.unconditional_variance,
        "next_variance_decimal_squared": fit.next_variance,
        "training_end": str(fit.training_end),
        "training_observations": fit.training_observations,
        "converged_starts": fit.converged_starts,
        "normalized_average_qml_objective_without_constants": fit.objective,
    }


def analyze() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run a prespecified historical attribution exercise and seeded DGP."""
    industries, hashes = load_frozen_industries()
    full = _monthly_slice(industries["NoDur"], TRAIN_START, EVAL_END)
    train = _monthly_slice(full, TRAIN_START, TRAIN_END)
    evaluation = _monthly_slice(full, EVAL_START, EVAL_END)
    train_mean = float(train.mean())
    train_variance = float(np.mean((train - train_mean) ** 2))
    actual_fit = fit_garch11(train)
    actual_innovations = full - train_mean
    actual_ewma = ewma_variance_path(actual_innovations, decay=0.94,
                                     initial_variance=train_variance)
    actual_rolling = {window: rolling_variance_forecast(full, window=window)
                      for window in (24, 60, 120)}
    actual_garch = garch_variance_path(
        evaluation - actual_fit.mean, actual_fit.parameters,
        initial_variance=actual_fit.next_variance,
    )
    forecast = pd.DataFrame(index=evaluation.index)
    forecast["return_decimal"] = evaluation
    forecast["innovation_squared_proxy_decimal_squared"] = (evaluation - actual_fit.mean) ** 2
    forecast["rolling_60_variance"] = actual_rolling[60].loc[evaluation.index]
    forecast["ewma_0_94_variance"] = actual_ewma.loc[evaluation.index]
    forecast["garch_1_1_variance"] = actual_garch
    for window, path in actual_rolling.items():
        if window != 60:
            forecast[f"rolling_{window}_variance"] = path.loc[evaluation.index]
    if forecast.isna().any().any() or (forecast.filter(like="variance") <= 0).any().any():
        raise ValueError("Evaluation forecasts must be aligned, finite and positive")
    actual_proxy = forecast["innovation_squared_proxy_decimal_squared"].to_numpy()
    actual_scores = {
        f"rolling_{window}": qlike_loss(actual_proxy, actual_rolling[window].loc[evaluation.index])
        for window in (24, 60, 120)
    }
    for decay in (0.80, 0.90, 0.94, 0.97):
        path = ewma_variance_path(actual_innovations, decay=decay,
                                  initial_variance=train_variance).loc[evaluation.index]
        actual_scores[f"ewma_{decay:.2f}"] = qlike_loss(actual_proxy, path)
    actual_scores["garch_1_1"] = qlike_loss(actual_proxy, actual_garch)

    sim_params = GARCHParameters(1e-5, 0.10, 0.80)
    simulation = simulate_garch11(sim_params, n=360, seed=20261018, mean=0.005, burn=500)
    sim_train = simulation["return"].iloc[:240]
    sim_evaluation = simulation.iloc[240:]
    sim_fit = fit_garch11(sim_train)
    sim_forecasts = garch_variance_path(
        sim_evaluation["return"] - sim_fit.mean, sim_fit.parameters,
        initial_variance=sim_fit.next_variance,
    )
    sim_proxy = (sim_evaluation["return"] - sim_fit.mean) ** 2
    simulation_path = pd.DataFrame({
        "return_decimal": simulation["return"],
        "true_variance_decimal_squared": simulation["true_variance"],
        "sample_role": ["training_prefix" if i < len(sim_train) else "heldout_evaluation"
                        for i in range(len(simulation))],
        "garch_forecast_decimal_squared": np.nan,
        "innovation_squared_proxy_decimal_squared": (simulation["return"] - sim_fit.mean) ** 2,
    })
    simulation_path.loc[sim_evaluation.index, "garch_forecast_decimal_squared"] = sim_forecasts
    simulation_summary = {
        "seed": 20261018,
        "observations": len(simulation),
        "burn_in": 500,
        "burn_in_note": "Initial h is the finite-second-moment long-run level; burn-in reduces initialization effects but does not guarantee an exact stationary draw.",
        "true_parameters": {"omega": sim_params.omega, "alpha": sim_params.alpha,
                            "beta": sim_params.beta, "mean": 0.005},
        "train_observations": len(sim_train),
        "evaluation_observations": len(sim_evaluation),
        "estimated_parameters": _params_dict(sim_fit),
        "evaluation_qlike_using_true_variance": qlike_loss(
            sim_evaluation["true_variance"], sim_forecasts),
        "evaluation_qlike_using_squared_innovation_proxy": qlike_loss(
            sim_proxy, sim_forecasts),
    }
    acf = pd.DataFrame({
        "lag_months": np.arange(1, 25),
        "return_acf": _acf((train - train_mean).to_numpy()),
        "squared_innovation_acf": _acf(((train - train_mean) ** 2).to_numpy()),
    })
    summary: dict[str, Any] = {
        "project": "Chapter 18 monthly volatility workflow",
        "data": {
            "source": "Kenneth R. French Data Library, 10 Industry Portfolios, average value-weighted monthly returns",
            "source_url": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_CSV.zip",
            "downloaded_at_utc": "2026-10-05T19:18:24.585420+00:00",
            "snapshot": "2026-10-05; revised present snapshot, not historical point-in-time vintages",
            "portfolio": "NoDur (Consumer Non-Durables), total simple return",
            "unit": "monthly decimal simple return; forecasts are decimal-return squared per month",
            "hashes_sha256": hashes,
            "train_start": TRAIN_START,
            "train_end": TRAIN_END,
            "evaluation_start": EVAL_START,
            "evaluation_end": EVAL_END,
            "train_n": len(train),
            "evaluation_n": len(evaluation),
            "training_mean_decimal": train_mean,
            "training_population_variance_decimal_squared": train_variance,
            "training_sample_standard_deviation_decimal": float(train.std(ddof=1)),
        },
        "design_boundary": (
            "A fixed training window followed by historical evaluation for descriptive attribution. "
            "This is not preregistered, historical PIT, an actual live out-of-sample record, or an ex-ante forecast: "
            "the frozen current snapshot is revised, and evaluation-month shocks are only known after each month closes. "
            "Fixed parameters are fitted on training; recursion updates for target t use only shocks through t-1."
        ),
        "actual_garch_fit": _params_dict(actual_fit),
        "actual_evaluation_proxy_mean": float(actual_proxy.mean()),
        "actual_evaluation_qlike_by_method": actual_scores,
        "actual_qlike_note": (
            "The proxy is (r_t - training_mean)^2, not observed conditional variance. "
            "It can be conditionally biased, especially if the mean shifts. No winner or statistical inference is claimed. "
            "Scores are comparable only on this aligned sample and unit; the proxy-only constant is omitted."
        ),
        "simulation": simulation_summary,
        "costs_and_trading": (
            "No trading ledger, position rule, turnover, financing, borrow, bid-ask, impact, capacity, or execution data were used; "
            "transaction costs and net strategy returns are not applicable to this variance-attribution exercise. "
            "Forecast diagnostics do not establish a future trading advantage."
        ),
    }
    return summary, forecast, simulation_path, acf


def analyze_constructed() -> tuple[dict[str, Any], pd.DataFrame]:
    """CONSTRUCTED GARCH DGP; no French inputs or market research."""
    sim_params = GARCHParameters(1e-5, 0.10, 0.80)
    simulation = simulate_garch11(sim_params, n=360, seed=20261018, mean=0.005, burn=500)
    sim_train = simulation["return"].iloc[:240]
    sim_evaluation = simulation.iloc[240:]
    sim_fit = fit_garch11(sim_train)
    sim_forecasts = garch_variance_path(
        sim_evaluation["return"] - sim_fit.mean, sim_fit.parameters,
        initial_variance=sim_fit.next_variance,
    )
    sim_proxy = (sim_evaluation["return"] - sim_fit.mean) ** 2
    simulation_path = pd.DataFrame({
        "return_decimal": simulation["return"],
        "true_variance_decimal_squared": simulation["true_variance"],
        "sample_role": ["training_prefix" if i < len(sim_train) else "heldout_evaluation"
                        for i in range(len(simulation))],
        "garch_forecast_decimal_squared": np.nan,
        "innovation_squared_proxy_decimal_squared": (simulation["return"] - sim_fit.mean) ** 2,
    })
    simulation_path.loc[sim_evaluation.index, "garch_forecast_decimal_squared"] = sim_forecasts
    simulation_summary = {
        "seed": 20261018,
        "observations": len(simulation),
        "burn_in": 500,
        "burn_in_note": "Initial h is the finite-second-moment long-run level; burn-in reduces initialization effects but does not guarantee an exact stationary draw.",
        "true_parameters": {"omega": sim_params.omega, "alpha": sim_params.alpha,
                            "beta": sim_params.beta, "mean": 0.005},
        "train_observations": len(sim_train),
        "evaluation_observations": len(sim_evaluation),
        "estimated_parameters": _params_dict(sim_fit),
        "evaluation_qlike_using_true_variance": qlike_loss(
            sim_evaluation["true_variance"], sim_forecasts),
        "evaluation_qlike_using_squared_innovation_proxy": qlike_loss(
            sim_proxy, sim_forecasts),
    }
    return {"data_class": "CONSTRUCTED", "simulation": simulation_summary}, simulation_path


def _make_figures(forecast: pd.DataFrame, simulation: pd.DataFrame, acf: pd.DataFrame,
                  scores: dict[str, float], figure_dir: Path) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    axes[0].plot(simulation.index.to_timestamp(), 100 * simulation["return_decimal"],
                 color="#315a7d", lw=0.8)
    axes[0].set_ylabel("Monthly return (%)")
    axes[0].set_title("Seeded simulated GARCH(1,1): clustered returns and known conditional scale")
    axes[1].plot(simulation.index.to_timestamp(),
                 100 * np.sqrt(simulation["true_variance_decimal_squared"]),
                 color="#bd5d38", lw=1.1)
    axes[1].set_ylabel("Conditional σ (% per month)")
    axes[1].set_xlabel("Month (simulated; seed 20261018)")
    fig.tight_layout()
    path = figure_dir / "ch18_volatility_clustering.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.axhline(0, color="black", lw=0.8)
    ax.plot(acf["lag_months"], acf["return_acf"], marker="o", ms=3,
            label="NoDur centered returns")
    ax.plot(acf["lag_months"], acf["squared_innovation_acf"], marker="s", ms=3,
            label="Squared centered innovations")
    ax.set(title="NoDur training sample: raw-return dependence versus volatility dependence",
           xlabel="Lag (months)", ylabel="Autocorrelation (unitless)")
    ax.legend(frameon=True)
    fig.tight_layout()
    path = figure_dir / "ch18_return_squared_acf.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1.5]})
    dates = forecast.index.to_timestamp()
    axes[0].bar(dates, forecast["return_decimal"] * 100, width=22,
                color=np.where(forecast["return_decimal"] >= 0, "#4b8068", "#ba6655"))
    axes[0].axhline(0, color="black", lw=0.7)
    axes[0].set_ylabel("Monthly return (%)")
    axes[0].set_title("NoDur historical crisis slice: target-month returns and one-month variance forecasts")
    axes[1].plot(dates, forecast["innovation_squared_proxy_decimal_squared"] * 10000,
                 color="#999999", marker="o", ms=3, ls="none", alpha=0.65,
                 label="Squared train-demeaned return proxy")
    for column, label, color in (
        ("rolling_60_variance", "Rolling 60-month", "#315a7d"),
        ("ewma_0_94_variance", "EWMA λ=0.94", "#d08b32"),
        ("garch_1_1_variance", "GARCH(1,1), fixed training fit", "#794c8a"),
    ):
        axes[1].plot(dates, forecast[column] * 10000, lw=1.5, label=label, color=color)
    axes[1].set_ylabel("Variance (% monthly return)²")
    axes[1].set_xlabel("Target month (forecast uses information through prior month)")
    axes[1].legend(ncol=2, fontsize=8)
    fig.tight_layout()
    path = figure_dir / "ch18_forecast_comparison.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)

    fig, ax = plt.subplots(figsize=(11, 5.4))
    labels, values, colors = [], [], []
    for method, value in scores.items():
        labels.append(method.replace("_", " "))
        values.append(value)
        colors.append("#794c8a" if method == "garch_1_1" else
                      "#d08b32" if method.startswith("ewma") else "#315a7d")
    ax.bar(np.arange(len(labels)), values, color=colors)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=28, ha="right")
    ax.set_xlabel("Fixed model / window setting")
    ax.set_ylabel("Mean QLIKE (log variance + proxy / variance; lower is better)")
    ax.set_title("NoDur 2007–2009 proxy-loss sensitivity; descriptive, 36 monthly targets")
    ax.axhline(0, color="black", lw=0.7)
    ax.set_ylim(min(values) - 0.72, 0.12)
    for index, value in enumerate(values):
        ax.text(index, value - 0.12, f"{value:.2f}", ha="center", va="top", fontsize=8)
    fig.text(0.01, 0.008,
             "Proxy: (return − training mean)²; not observed conditional variance. No winner inference.",
             fontsize=8, va="bottom")
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    path = figure_dir / "ch18_qlike_sensitivity.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)
    return outputs


def run(output_dir: Path, figure_dir: Path) -> dict[str, Any]:
    summary, forecast, simulation, acf = analyze()
    output_dir.mkdir(parents=True, exist_ok=True)
    forecast.to_csv(output_dir / "ch18_actual_forecasts.csv", index_label="month")
    simulation.to_csv(output_dir / "ch18_simulation_path.csv", index_label="month")
    acf.to_csv(output_dir / "ch18_training_acf.csv", index=False)
    figures = _make_figures(forecast, simulation, acf,
                            summary["actual_evaluation_qlike_by_method"], figure_dir)
    summary["generated_artifacts"] = {
        "actual_forecasts_csv": str(output_dir / "ch18_actual_forecasts.csv"),
        "simulation_csv": str(output_dir / "ch18_simulation_path.csv"),
        "training_acf_csv": str(output_dir / "ch18_training_acf.csv"),
        "figures": [str(path) for path in figures],
    }
    (output_dir / "ch18_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch18_volatility_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=default_run / "results")
    parser.add_argument("--figure-dir", type=Path, default=default_run / "figures")
    args = parser.parse_args()
    summary = run(args.output_dir.resolve(), args.figure_dir.resolve())
    print(json.dumps({
        "train_n": summary["data"]["train_n"],
        "evaluation_n": summary["data"]["evaluation_n"],
        "actual_garch_fit": summary["actual_garch_fit"],
        "actual_evaluation_qlike_by_method": summary["actual_evaluation_qlike_by_method"],
        "artifacts": summary["generated_artifacts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
