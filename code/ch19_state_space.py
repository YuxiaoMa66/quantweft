"""Reproduce Chapter 19 state-space examples from frozen local French data.

The Kalman recursion is implemented only in ``quant_course.state_space``.
This workflow verifies immutable local inputs, runs fixed-parameter two-state
filters, writes requested teaching artifacts, and never downloads data. Returns
are monthly decimal simple excess returns; states are filtered through the row
shown, while ``predicted_*`` values precede that month's observation.
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

from quant_course.state_space import KalmanResult, kalman_filter  # noqa: E402
from quant_course.time_series import validate_monthly_series  # noqa: E402

INDUSTRIES_MANIFEST = ROOT / "data/manifests/french_industries_2026-10-05.json"
FACTORS_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"
SIMULATION_SEED = 20261019
SIMULATION_N = 480
ACTUAL_Q = np.diag([1e-6, 1e-5])
ACTUAL_R = 0.0004
ACTUAL_INITIAL_STATE = np.array([0.0, 1.0])
ACTUAL_INITIAL_COVARIANCE = np.diag([0.0004, 0.04])
SIMULATION_Q = np.diag([4e-6, 4e-5])
SIMULATION_R = 0.0004
SIMULATION_INITIAL_STATE = np.array([0.001, 0.9])
SIMULATION_INITIAL_COVARIANCE = np.diag([0.0001, 0.04])
SIMULATED_FIGURE_NAMES = (
    "ch19_simulated_latent_beta.png",
    "ch19_simulated_innovation_update.png",
)
FRENCH_FIGURE_NAMES = (
    "ch19_french_descriptive_beta.png",
    "ch19_french_state_uncertainty.png",
)
OUTPUT_NAMES = (
    "ch19_simulation.csv",
    "ch19_simulation_filter.csv",
    "ch19_french_filter.csv",
    "ch19_results.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Frozen French {label} is missing: {path}")
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Frozen French {label} SHA-256 differs from its manifest")
    return actual


def _read_frozen_inputs() -> tuple[pd.DataFrame, dict[str, str], dict[str, Any]]:
    """Read only local files and verify raw and processed bytes against manifests."""
    industry_manifest = json.loads(INDUSTRIES_MANIFEST.read_text(encoding="utf-8"))
    factors_manifest = json.loads(FACTORS_MANIFEST.read_text(encoding="utf-8"))
    ff3 = factors_manifest["datasets"]["ff3"]

    industry_paths = {
        "industry_raw_zip": ROOT / "data/raw/french/2026-10-05/10_Industry_Portfolios_CSV.zip",
        "industry_extracted_csv": ROOT / industry_manifest["raw_extracted_path"],
        "industry_processed_csv": ROOT / industry_manifest["processed_path"],
    }
    industry_expected = {
        "industry_raw_zip": industry_manifest["sha256"],
        "industry_extracted_csv": industry_manifest["extracted_sha256"],
        "industry_processed_csv": industry_manifest["processed_sha256"],
    }
    factor_paths = {
        "ff3_raw_zip": ROOT / ff3["raw_zip_path"],
        "ff3_raw_csv": ROOT / ff3["raw_csv_path"],
        "ff3_processed_csv": ROOT / ff3["processed_path"],
    }
    factor_expected = {
        "ff3_raw_zip": ff3["raw_zip_sha256"],
        "ff3_raw_csv": ff3["raw_csv_sha256"],
        "ff3_processed_csv": ff3["processed_sha256"],
    }
    hashes = {
        name: _verify(path, industry_expected[name], name)
        for name, path in industry_paths.items()
    }
    hashes.update({
        name: _verify(path, factor_expected[name], name)
        for name, path in factor_paths.items()
    })

    industries = pd.read_csv(industry_paths["industry_processed_csv"])
    factors = pd.read_csv(factor_paths["ff3_processed_csv"])
    if industries.columns[0] != "month" or "NoDur" not in industries:
        raise ValueError("Industry cache does not contain the declared NoDur monthly series")
    if factors.columns[0] != "month" or not {"Mkt-RF", "RF"}.issubset(factors.columns):
        raise ValueError("FF3 cache does not contain Mkt-RF and RF monthly series")
    for frame in (industries, factors):
        frame["month"] = pd.PeriodIndex(frame["month"].astype(str), freq="M")
        frame.set_index("month", inplace=True)
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ValueError("French monthly periods must be unique and ordered")
    if not industries.index.equals(factors.index):
        raise ValueError("Industry and FF3 factor snapshots must have exactly matching months")
    if str(industries.index[0]) != "1926-07" or str(industries.index[-1]) != "2026-08":
        raise ValueError("French cache period differs from the frozen manifests")

    no_dur = validate_monthly_series(industries["NoDur"], min_observations=12)
    market = validate_monthly_series(factors["Mkt-RF"], min_observations=12)
    rf = validate_monthly_series(factors["RF"], min_observations=12)
    if not no_dur.index.equals(market.index) or not market.index.equals(rf.index):
        raise ValueError("NoDur, Mkt-RF and RF months must match exactly")
    result = pd.DataFrame({
        "no_dur_total_return": no_dur,
        "market_excess_return": market,
        "risk_free_return": rf,
        "no_dur_excess_return": no_dur - rf,
    }, index=no_dur.index)
    for column in result:
        result[column] = validate_monthly_series(result[column], min_observations=12)
    provenance = {
        "snapshot_date": "2026-10-05",
        "source": "Kenneth R. French Data Library: monthly 10 Industry Portfolios and FF3 factors",
        "industry_processed_unit": industry_manifest["processed_unit"],
        "factor_processed_unit": ff3["processed_unit"],
        "start_month": str(result.index[0]),
        "end_month": str(result.index[-1]),
        "monthly_observations": int(len(result)),
        "vintage": ff3["source_file_vintage"]["header_line"],
        "is_point_in_time": False,
        "selection": "full common monthly period; figures show the 2010-01 onward slice",
        "limitations": (
            "Current revised historical snapshot; no historical vintages or receipt timestamps. "
            "Descriptive recursive state/risk illustration only; no historical PIT signal, "
            "ex-ante return forecast, tradable factor instrument, alpha test, or strategy return."
        ),
    }
    return result, hashes, provenance


def alpha_beta_filter(
    asset_excess: pd.Series | np.ndarray,
    market_excess: pd.Series | np.ndarray,
    *,
    initial_state: np.ndarray,
    initial_covariance: np.ndarray,
    process_covariance: np.ndarray,
    observation_variance: float,
) -> KalmanResult:
    """Run a supplied-parameter two-state random-walk alpha/beta filter."""
    y = np.asarray(asset_excess, dtype=float)
    f = np.asarray(market_excess, dtype=float)
    if y.ndim != 1 or f.ndim != 1 or y.size != f.size:
        raise ValueError("asset and market excess returns must be same-length vectors")
    design = np.column_stack((np.ones_like(f), f))
    return kalman_filter(
        y,
        design,
        initial_state=initial_state,
        initial_covariance=initial_covariance,
        transition=np.eye(2),
        process_covariance=process_covariance,
        observation_variance=observation_variance,
    )


def simulate_known_latent(*, n: int = SIMULATION_N, seed: int = SIMULATION_SEED) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Simulate a known two-state Gaussian DGP and a fixed-Q misspecification."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 24:
        raise ValueError("n must be an integer of at least 24 observations")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    rng = np.random.default_rng(seed)
    true_initial = rng.multivariate_normal(SIMULATION_INITIAL_STATE,
                                           SIMULATION_INITIAL_COVARIANCE)
    market = rng.normal(0.0, 0.04, n)
    latent = np.empty((n, 2), dtype=float)
    state = true_initial.copy()
    for t in range(n):
        state = state + rng.multivariate_normal(np.zeros(2), SIMULATION_Q)
        latent[t] = state
    observation_noise = rng.normal(0.0, np.sqrt(SIMULATION_R), n)
    asset = latent[:, 0] + latent[:, 1] * market + observation_noise
    index = pd.period_range("1980-01", periods=n, freq="M")
    simulated = pd.DataFrame({
        "market_excess_return": market,
        "asset_excess_return": asset,
        "observation_noise": observation_noise,
        "latent_alpha": latent[:, 0],
        "latent_beta": latent[:, 1],
    }, index=index)
    simulated.index.name = "month"

    correct = alpha_beta_filter(
        asset, market,
        initial_state=SIMULATION_INITIAL_STATE,
        initial_covariance=SIMULATION_INITIAL_COVARIANCE,
        process_covariance=SIMULATION_Q,
        observation_variance=SIMULATION_R,
    )
    misspecified_q = np.diag([SIMULATION_Q[0, 0], 0.0])
    misspecified = alpha_beta_filter(
        asset, market,
        initial_state=SIMULATION_INITIAL_STATE,
        initial_covariance=SIMULATION_INITIAL_COVARIANCE,
        process_covariance=misspecified_q,
        observation_variance=SIMULATION_R,
    )
    filtered = pd.DataFrame(index=index)
    for name, result in (("specified", correct), ("q_beta_zero", misspecified)):
        filtered[f"{name}_predicted_alpha"] = result.predicted_states[:, 0]
        filtered[f"{name}_predicted_beta"] = result.predicted_states[:, 1]
        filtered[f"{name}_filtered_alpha"] = result.filtered_states[:, 0]
        filtered[f"{name}_filtered_beta"] = result.filtered_states[:, 1]
        filtered[f"{name}_filtered_alpha_variance"] = result.filtered_covariances[:, 0, 0]
        filtered[f"{name}_filtered_beta_variance"] = result.filtered_covariances[:, 1, 1]
    filtered["innovation"] = correct.innovations
    filtered["innovation_variance"] = correct.innovation_variances
    filtered["standardized_innovation"] = (
        correct.innovations / np.sqrt(correct.innovation_variances)
    )
    filtered["alpha_gain"] = correct.gains[:, 0]
    filtered["beta_gain"] = correct.gains[:, 1]
    filtered.index.name = "month"
    metrics = {
        "seed": seed,
        "observations": n,
        "true_initial_state_draw": true_initial.tolist(),
        "true_process_covariance": SIMULATION_Q.tolist(),
        "true_observation_variance": SIMULATION_R,
        "correctly_specified_filter_beta_rmse_one_path": float(np.sqrt(np.mean(
            (correct.filtered_states[:, 1] - latent[:, 1]) ** 2))),
        "q_beta_zero_filter_beta_rmse_one_path": float(np.sqrt(np.mean(
            (misspecified.filtered_states[:, 1] - latent[:, 1]) ** 2))),
        "specified_filter_marginal_95_percent_band_coverage_one_path": float(np.mean(
            np.abs(correct.filtered_states[:, 1] - latent[:, 1])
            <= 1.96 * np.sqrt(correct.filtered_covariances[:, 1, 1]))),
        "interpretation": (
            "One seeded mechanism/misspecification illustration using known latent states. "
            "Single-path errors are not a general ranking or evidence of future predictive superiority."
        ),
    }
    return simulated, filtered, metrics


def _rolling_beta_prior(y: pd.Series, f: pd.Series, *, window: int = 60) -> pd.Series:
    """OLS slope with an intercept from the preceding window only."""
    if isinstance(window, bool) or not isinstance(window, int) or window < 2:
        raise ValueError("window must be an integer of at least 2 months")
    y = validate_monthly_series(y, min_observations=window + 1)
    f = validate_monthly_series(f, min_observations=window + 1)
    if not y.index.equals(f.index):
        raise ValueError("rolling beta inputs must have identical months")
    result = np.full(len(y), np.nan)
    y_values, f_values = y.to_numpy(), f.to_numpy()
    for t in range(window, len(y)):
        past_f = f_values[t - window:t]
        past_y = y_values[t - window:t]
        centered_f = past_f - past_f.mean()
        denominator = float(centered_f @ centered_f)
        if denominator > 0:
            result[t] = float(centered_f @ (past_y - past_y.mean()) / denominator)
    return pd.Series(result, index=y.index.copy(), name=f"trailing_{window}m_ols_beta")


def _frame_from_result(index: pd.PeriodIndex, result: KalmanResult) -> pd.DataFrame:
    frame = pd.DataFrame({
        "predicted_alpha": result.predicted_states[:, 0],
        "predicted_beta": result.predicted_states[:, 1],
        "filtered_alpha": result.filtered_states[:, 0],
        "filtered_beta": result.filtered_states[:, 1],
        "predicted_alpha_variance": result.predicted_covariances[:, 0, 0],
        "predicted_beta_variance": result.predicted_covariances[:, 1, 1],
        "filtered_alpha_variance": result.filtered_covariances[:, 0, 0],
        "filtered_beta_variance": result.filtered_covariances[:, 1, 1],
        "innovation": result.innovations,
        "innovation_variance": result.innovation_variances,
        "alpha_gain": result.gains[:, 0],
        "beta_gain": result.gains[:, 1],
    }, index=index.copy())
    frame.index.name = "month"
    return frame


def analyze() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the seeded DGP and descriptive full-snapshot French filter."""
    simulated, simulation_filter, simulation_metrics = simulate_known_latent()
    french, hashes, provenance = _read_frozen_inputs()
    french_result = alpha_beta_filter(
        french["no_dur_excess_return"],
        french["market_excess_return"],
        initial_state=ACTUAL_INITIAL_STATE,
        initial_covariance=ACTUAL_INITIAL_COVARIANCE,
        process_covariance=ACTUAL_Q,
        observation_variance=ACTUAL_R,
    )
    french_filter = _frame_from_result(french.index, french_result)
    french_filter["trailing_60m_ols_beta"] = _rolling_beta_prior(
        french["no_dur_excess_return"], french["market_excess_return"], window=60
    )
    french_filter["standardized_innovation"] = (
        french_filter["innovation"] / np.sqrt(french_filter["innovation_variance"])
    )
    summary: dict[str, Any] = {
        "chapter": 19,
        "workflow": "two-state alpha-beta filtering; no parameter estimation or smoothing",
        "simulation": {
            **simulation_metrics,
            "filter_initial_state_mean": SIMULATION_INITIAL_STATE.tolist(),
            "filter_initial_covariance": SIMULATION_INITIAL_COVARIANCE.tolist(),
            "misspecification": "set beta process variance to zero while data retain positive beta process variance",
        },
        "french_data": {
            **provenance,
            "sha256": hashes,
            "asset_series": "NoDur monthly value-weighted simple portfolio return minus French RF, in decimal returns",
            "market_series": "French Mkt-RF monthly market excess factor, in decimal returns",
            "observation_design": "[1, Mkt-RF_t]",
        },
        "french_filter_specification": {
            "initial_state_before_first_transition_alpha_beta": ACTUAL_INITIAL_STATE.tolist(),
            "initial_covariance_alpha_beta": ACTUAL_INITIAL_COVARIANCE.tolist(),
            "transition": np.eye(2).tolist(),
            "process_covariance_alpha_beta": ACTUAL_Q.tolist(),
            "observation_variance_decimal_return_squared": ACTUAL_R,
            "parameter_policy": "All initial values, Q and R are declared teaching inputs; none are fitted from the full sample.",
            "alpha_restriction": "Alpha is a latent state with fixed supplied process variance; no alpha significance test is performed.",
            "hedge_timing": (
                "predicted_beta at month t is based on data through t-1 and is the relevant descriptive pre-month ratio; "
                "filtered_beta at t requires both realized same-month returns and is only available after month-end."
            ),
        },
        "french_summary": {
            "mean_no_dur_excess_return_decimal": float(french["no_dur_excess_return"].mean()),
            "sd_no_dur_excess_return_decimal_ddof1": float(french["no_dur_excess_return"].std(ddof=1)),
            "mean_market_excess_return_decimal": float(french["market_excess_return"].mean()),
            "first_predicted_beta": float(french_filter["predicted_beta"].iloc[0]),
            "first_filtered_beta": float(french_filter["filtered_beta"].iloc[0]),
            "last_predicted_beta": float(french_filter["predicted_beta"].iloc[-1]),
            "last_filtered_beta": float(french_filter["filtered_beta"].iloc[-1]),
            "filtered_beta_min": float(french_filter["filtered_beta"].min()),
            "filtered_beta_max": float(french_filter["filtered_beta"].max()),
            "filtered_beta_sd_median": float(np.sqrt(french_filter["filtered_beta_variance"]).median()),
            "trailing_60m_beta_first_available_month": str(
                french_filter["trailing_60m_ols_beta"].first_valid_index()
            ),
            "trailing_60m_beta_valid_observations": int(french_filter["trailing_60m_ols_beta"].notna().sum()),
        },
        "scope_limit": (
            "The recursive historical display is descriptive, not a point-in-time or real-time backtest. "
            "The current revised French snapshot has no historical release/receipt timestamps. "
            "No signals, trades, executable instrument, costs, or net returns were constructed."
        ),
    }
    return summary, simulated, simulation_filter, french, french_filter


def _recent(frame: pd.DataFrame, start: str = "2010-01") -> pd.DataFrame:
    return frame.loc[pd.Period(start, freq="M"):].copy()


def _make_figures(
    simulated: pd.DataFrame,
    simulation_filter: pd.DataFrame,
    french: pd.DataFrame,
    french_filter: pd.DataFrame,
    figure_dir: Path,
) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    plt.style.use("seaborn-v0_8-whitegrid")

    dates_sim = simulated.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.plot(dates_sim, simulated["latent_beta"], color="#222222", lw=1.2,
            label="Known latent β")
    ax.plot(dates_sim, simulation_filter["specified_filtered_beta"],
            color="#27678f", lw=1.0, label="Filter with true Q and R")
    band = 1.96 * np.sqrt(simulation_filter["specified_filtered_beta_variance"])
    center = simulation_filter["specified_filtered_beta"]
    ax.fill_between(dates_sim, center - band, center + band, color="#27678f",
                    alpha=0.16, label="Model-based marginal ±1.96 SD")
    ax.plot(dates_sim, simulation_filter["q_beta_zero_filtered_beta"],
            color="#c25b3f", lw=0.9, alpha=0.9,
            label="Misspecified filter: Qββ = 0")
    ax.set(title="Seeded two-state simulation: latent and filtered hedge ratio",
           xlabel="Simulated month (seed 20261019)", ylabel="Beta (unitless)")
    ax.legend(ncol=2, fontsize=8)
    ax.text(0.01, 0.01,
            "Known-latent mechanism example; one path is not a model or forecast ranking.",
            transform=ax.transAxes, fontsize=8, va="bottom")
    fig.tight_layout()
    path = figure_dir / SIMULATED_FIGURE_NAMES[0]
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)

    dates_sim = simulated.index.to_timestamp()
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(dates_sim, simulated["latent_alpha"] * 100, color="#222222",
                 lw=1, label="Known latent α")
    axes[0].plot(dates_sim, simulation_filter["specified_filtered_alpha"] * 100,
                 color="#27678f", lw=0.9, label="Filtered α")
    axes[0].set_ylabel("Alpha (% / month)")
    axes[0].legend(fontsize=8)
    axes[1].plot(dates_sim, simulation_filter["standardized_innovation"],
                 color="#6d4e83", lw=0.8)
    axes[1].axhline(0, color="black", lw=0.7)
    axes[1].axhline(1.96, color="#bd6a37", lw=0.8, ls="--")
    axes[1].axhline(-1.96, color="#bd6a37", lw=0.8, ls="--")
    axes[1].set_ylabel("Innovation / √S\n(unitless)")
    axes[2].plot(dates_sim, simulation_filter["beta_gain"],
                 color="#2b806e", lw=0.8)
    axes[2].axhline(0, color="black", lw=0.7)
    axes[2].set_ylabel("Kβ (beta / return)")
    axes[2].set_xlabel("Simulated month (each row observes after state transition)")
    fig.suptitle("Simulation mechanics: latent level, innovation, and beta gain")
    fig.text(0.01, 0.01,
             "Dashed lines are reference levels, not a formal rejection test; gain is not a probability.",
             fontsize=8)
    fig.tight_layout(rect=(0, 0.025, 1, 0.97))
    path = figure_dir / SIMULATED_FIGURE_NAMES[1]
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)

    actual_recent = _recent(french_filter)
    dates_actual = actual_recent.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.plot(dates_actual, actual_recent["predicted_beta"], color="#27678f",
            lw=1.2, label="Kalman prior β (uses data through prior month)")
    ax.plot(dates_actual, actual_recent["trailing_60m_ols_beta"], color="#c25b3f",
            lw=1.0, label="60-month trailing OLS β (prior months only)")
    ax.set(title="French NoDur: descriptive pre-month beta estimates, 2010–2026",
           xlabel="Target month; source is current revised snapshot",
           ylabel="Beta (unitless)")
    ax.legend(fontsize=8)
    ax.text(0.01, 0.01,
            "Mkt-RF and NoDur-RF are same-month realized returns in the observation model; this is not a PIT backtest.",
            transform=ax.transAxes, fontsize=8, va="bottom")
    fig.tight_layout()
    path = figure_dir / FRENCH_FIGURE_NAMES[0]
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    alpha = actual_recent["filtered_alpha"] * 100
    alpha_sd = np.sqrt(actual_recent["filtered_alpha_variance"]) * 100
    axes[0].plot(dates_actual, alpha, color="#6d4e83", lw=1.0)
    axes[0].fill_between(dates_actual, alpha - 1.96 * alpha_sd,
                         alpha + 1.96 * alpha_sd, color="#6d4e83", alpha=0.16)
    axes[0].axhline(0, color="black", lw=0.7)
    axes[0].set_ylabel("Filtered α (% / month)")
    beta = actual_recent["filtered_beta"]
    beta_sd = np.sqrt(actual_recent["filtered_beta_variance"])
    axes[1].plot(dates_actual, beta, color="#27678f", lw=1.0)
    axes[1].fill_between(dates_actual, beta - 1.96 * beta_sd,
                         beta + 1.96 * beta_sd, color="#27678f", alpha=0.16)
    axes[1].set_ylabel("Filtered β ± 1.96 SD\n(unitless)")
    axes[1].set_xlabel("Month (2010-01 through 2026-08)")
    fig.suptitle("French NoDur: filtered state paths and conditional state uncertainty")
    fig.text(0.01, 0.01,
             "Bands reflect the fixed Gaussian state model only; they are not alpha tests or strategy confidence intervals.",
             fontsize=8)
    fig.tight_layout(rect=(0, 0.025, 1, 0.97))
    path = figure_dir / FRENCH_FIGURE_NAMES[1]
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    outputs.append(path)
    return outputs


def _all_target_paths(output_dir: Path, figure_dir: Path) -> list[Path]:
    return [output_dir / name for name in OUTPUT_NAMES] + [
        figure_dir / name for name in (*SIMULATED_FIGURE_NAMES, *FRENCH_FIGURE_NAMES)
    ]


def run(output_dir: Path, figure_dir: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Run workflow into explicitly requested directories; overwrite is opt-in."""
    output_dir = output_dir.expanduser().resolve()
    figure_dir = figure_dir.expanduser().resolve()
    targets = _all_target_paths(output_dir, figure_dir)
    collisions = [path for path in targets if path.exists()]
    if collisions and not overwrite:
        listed = ", ".join(str(path) for path in collisions)
        raise FileExistsError(f"Refusing to overwrite existing Chapter 19 artifacts: {listed}")
    summary, simulated, simulation_filter, french, french_filter = analyze()
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    simulated.to_csv(output_dir / OUTPUT_NAMES[0], index_label="month")
    simulation_filter.to_csv(output_dir / OUTPUT_NAMES[1], index_label="month")
    french_output = french.join(french_filter)
    french_output.to_csv(output_dir / OUTPUT_NAMES[2], index_label="month")
    figures = _make_figures(simulated, simulation_filter, french_output,
                            french_filter, figure_dir)
    summary["artifacts"] = {
        "simulation_csv": str(output_dir / OUTPUT_NAMES[0]),
        "simulation_filter_csv": str(output_dir / OUTPUT_NAMES[1]),
        "french_filter_csv": str(output_dir / OUTPUT_NAMES[2]),
        "figures": [str(path) for path in figures],
    }
    (output_dir / OUTPUT_NAMES[3]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch19_state_space_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=default_run / "results",
                        help="directory for CSV/JSON artifacts; existing files are preserved by default")
    parser.add_argument("--figure-dir", type=Path, default=default_run / "figures",
                        help="directory for four PNG figures; existing files are preserved by default")
    parser.add_argument("--overwrite", action="store_true",
                        help="explicitly replace this chapter's named artifacts in the chosen directories")
    args = parser.parse_args()
    summary = run(args.output_dir, args.figure_dir, overwrite=args.overwrite)
    print(json.dumps({
        "snapshot": summary["french_data"]["snapshot_date"],
        "monthly_observations": summary["french_data"]["monthly_observations"],
        "period": [summary["french_data"]["start_month"], summary["french_data"]["end_month"]],
        "simulation": summary["simulation"],
        "french_summary": summary["french_summary"],
        "artifacts": summary["artifacts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
