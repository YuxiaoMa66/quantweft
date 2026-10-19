"""Chapter 15 workflow for frozen monthly French factor attribution."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.factor_models import MonthlyFactorFit, fit_monthly_factor_model  # noqa: E402
from quant_course.market_data import load_monthly_snapshot  # noqa: E402


INDUSTRY_MANIFEST_PATH = Path("data/manifests/french_industries_2026-10-05.json")
FACTOR_MANIFEST_PATH = Path("data/manifests/french_factors_2026-10-05.json")
SAMPLE_INDEX = pd.period_range("2010-01", "2019-12", freq="M", name="month")
MODEL_FACTORS: dict[str, tuple[str, ...]] = {
    "capm": ("Mkt-RF",),
    "ff3": ("Mkt-RF", "SMB", "HML"),
    "ff5": ("Mkt-RF", "SMB", "HML", "RMW", "CMA"),
}
MODEL_FRAME = {"capm": "ff3", "ff3": "ff3", "ff5": "ff5"}
HAC_SENSITIVITY_LAGS = (3, 6, 12)

PALETTE = {
    "paper": "#FAF7F0",
    "ink": "#173C40",
    "teal": "#176B6F",
    "teal_light": "#77A9A5",
    "teal_mid": "#3F8886",
    "orange": "#CF7548",
    "orange_light": "#E1A080",
    "orange_dark": "#A95538",
    "gray": "#777B78",
    "grid": "#DDD7CB",
}


def _source_manifests() -> tuple[dict[str, Any], dict[str, Any]]:
    industry = json.loads((ROOT / INDUSTRY_MANIFEST_PATH).read_text(encoding="utf-8"))
    factor_manifest = json.loads((ROOT / FACTOR_MANIFEST_PATH).read_text(encoding="utf-8"))
    return industry, factor_manifest


def load_sample() -> tuple[pd.Series, dict[str, pd.DataFrame]]:
    """Load the SHA-verified NoDur and FF3/FF5 snapshots for 2010–2019.

    The snapshots already contain decimal monthly simple returns. No data is
    downloaded, converted, filled, shifted, or joined on a reduced sample.
    """
    industry_manifest, factor_manifest = _source_manifests()
    industry = load_monthly_snapshot(
        ROOT / industry_manifest["processed_path"],
        industry_manifest["processed_sha256"],
        ["NoDur"],
    )
    total = industry.loc[SAMPLE_INDEX, "NoDur"].copy()
    total.name = "NoDur"

    frames: dict[str, pd.DataFrame] = {}
    for name, columns in MODEL_FACTORS.items():
        if name == "capm":
            continue
        manifest = factor_manifest["datasets"][name]
        frame = load_monthly_snapshot(
            ROOT / manifest["processed_path"],
            manifest["processed_sha256"],
            [*columns, "RF"],
        )
        frames[name] = frame.loc[SAMPLE_INDEX].copy()

    if not total.index.equals(SAMPLE_INDEX):
        raise ValueError("NoDur must contain exactly the declared 120 monthly periods")
    if set(frames) != {"ff3", "ff5"} or any(
        not frame.index.equals(SAMPLE_INDEX) for frame in frames.values()
    ):
        raise ValueError("FF3 and FF5 must each contain exactly the declared 120 months")
    if not np.isfinite(total.to_numpy(dtype=float)).all() or any(
        not np.isfinite(frame.to_numpy(dtype=float)).all() for frame in frames.values()
    ):
        raise ValueError("the selected frozen sample contains missing or infinite values")
    return total, frames


def fit_models(
    total: pd.Series,
    frames: Mapping[str, pd.DataFrame],
    hac_maxlags: int = 6,
) -> dict[str, MonthlyFactorFit]:
    """Fit CAPM, FF3, and FF5 with the shared monthly regression function."""
    missing = {"ff3", "ff5"}.difference(frames)
    if missing:
        raise ValueError(f"factor frames are missing: {', '.join(sorted(missing))}")
    return {
        name: fit_monthly_factor_model(
            total,
            frames[MODEL_FRAME[name]],
            factor_columns=columns,
            hac_maxlags=hac_maxlags,
        )
        for name, columns in MODEL_FACTORS.items()
    }


def _plain_number(value: Any) -> float:
    return float(value)


def _manifest_references() -> dict[str, Any]:
    industry, factors = _source_manifests()
    result: dict[str, Any] = {
        "industry": {
            "manifest_path": INDUSTRY_MANIFEST_PATH.as_posix(),
            "source_url": industry["source_url"],
            "source_details": industry["source_details"],
            "snapshot_date": industry["snapshot"],
            "processed_path": industry["processed_path"],
            "processed_sha256": industry["processed_sha256"],
            "processed_unit": industry["processed_unit"],
            "selected_table": industry["selected_table"],
        }
    }
    for name in ("ff3", "ff5"):
        manifest = factors["datasets"][name]
        result[name] = {
            "manifest_path": FACTOR_MANIFEST_PATH.as_posix(),
            "source_name": manifest["name"],
            "source_url": manifest["source_url"],
            "method_page": manifest["method_page"],
            "downloaded_at_utc": manifest["http_response"]["downloaded_at_utc"],
            "declared_crsp_database_month": manifest["source_file_vintage"][
                "declared_crsp_database_month"
            ],
            "processed_path": manifest["processed_path"],
            "processed_sha256": manifest["processed_sha256"],
            "processed_unit": manifest["processed_unit"],
        }
    return result


def _coefficient_dict(table: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {
        str(coefficient): {str(column): _plain_number(value) for column, value in row.items()}
        for coefficient, row in table.iterrows()
    }


def build_summary(
    total: pd.Series,
    frames: Mapping[str, pd.DataFrame],
    fits: Mapping[str, MonthlyFactorFit],
    *,
    sensitivity_lags: tuple[int, ...] = HAC_SENSITIVITY_LAGS,
    constructed: bool = False,
) -> dict[str, Any]:
    """Create the auditable result record, including HAC bandwidth sensitivity."""
    models: dict[str, Any] = {}
    for name, factor_columns in MODEL_FACTORS.items():
        frame = frames[MODEL_FRAME[name]]
        fit = fits[name]
        excess = total - frame["RF"]
        variance_total = float(excess.var(ddof=1))
        variance_fitted = float(fit.fitted_excess.var(ddof=1))
        variance_residual = float(fit.residuals.var(ddof=1))
        if not np.isclose(
            variance_total,
            variance_fitted + variance_residual,
            rtol=1e-10,
            atol=1e-15,
        ):
            raise ArithmeticError(f"sample variance decomposition failed for {name}")

        alpha_sensitivity: dict[str, dict[str, float]] = {}
        for lag in sensitivity_lags:
            sensitivity_fit = fit_monthly_factor_model(
                total,
                frame,
                factor_columns=factor_columns,
                hac_maxlags=lag,
            )
            alpha_sensitivity[str(lag)] = {
                str(column): _plain_number(value)
                for column, value in sensitivity_fit.coefficient_table.loc["const"].items()
            }
            if not np.allclose(
                fit.coefficient_table["estimate"].to_numpy(),
                sensitivity_fit.coefficient_table["estimate"].to_numpy(),
                rtol=0,
                atol=1e-12,
            ):
                raise ArithmeticError("changing HAC bandwidth changed the OLS point estimates")

        models[name] = {
            "factors": list(factor_columns),
            "factor_snapshot": MODEL_FRAME[name],
            "coefficients": _coefficient_dict(fit.coefficient_table),
            "r_squared": fit.r_squared,
            "adjusted_r_squared": fit.adjusted_r_squared,
            "nobs": fit.nobs,
            "condition_number": fit.condition_number,
            "hac": {
                "kernel": "Bartlett",
                "maxlags": fit.hac_maxlags,
                "lag_unit": "monthly observation rows",
                "finite_sample_correction": True,
                "t_reference_intervals_and_p_values": "approximations; assumptions are not verified by this computation",
            },
            "sample_variance_decomposition_ddof1": {
                "observed_excess_return": variance_total,
                "fitted_excess_return": variance_fitted,
                "residual": variance_residual,
                "sum_fitted_plus_residual": variance_fitted + variance_residual,
                "identity_holds_within_tolerance": True,
            },
            "mean_monthly_residual": float(fit.residuals.mean()),
            "alpha_hac_lag_sensitivity": alpha_sensitivity,
        }

    ff3, ff5 = frames["ff3"], frames["ff5"]
    common_columns = ("Mkt-RF", "SMB", "HML", "RF")
    differences = {
        column: float((ff3[column] - ff5[column]).abs().max())
        for column in common_columns
    }
    return {
        "status": "CONSTRUCTED teaching demonstration" if constructed else "chapter support draft; empirical artifacts only",
        "scope": "CONSTRUCTED method demonstration only" if constructed else "descriptive regression on a frozen current published snapshot; not ex-ante or point-in-time evidence, a forecast, a trading strategy, or net alpha",
        "sample": {
            "asset": "CONSTRUCTED asset" if constructed else "Kenneth R. French value-weighted 10-industry NoDur total return",
            "start_month": str(total.index[0]),
            "end_month": str(total.index[-1]),
            "frequency": "monthly PeriodIndex intervals",
            "n_months": int(len(total)),
            "index_type": "pandas.PeriodIndex",
            "index_frequency": "M",
            "currency_convention": "USD return series as documented by the frozen source preparation",
        },
        "units_and_alignment": {
            "returns_and_factors": "decimal simple monthly returns / factor spreads",
            "asset_target": "CONSTRUCTED total return minus RF exactly once" if constructed else "NoDur total return minus same-month RF exactly once",
            "published_factor_columns": "Mkt-RF, SMB, HML, RMW, CMA are passed through unchanged",
            "alignment": "same 120 consecutive monthly PeriodIndex labels; no inner join, fill, or shift",
        },
        "source_manifests": ({"data_class": "CONSTRUCTED", "seed": 20261015} if constructed else _manifest_references()),
        "models": models,
        "factor_series_maximum_absolute_differences_ff3_vs_ff5": differences,
        "model_comparison_limitations": ["CONSTRUCTED data only; no French snapshot inference"] if constructed else [
            "The FF3 and FF5 snapshots have different published Mkt-RF and SMB values in this window; the upstream reason is unresolved.",
            "The FF3 and FF5 fits are not treated as strictly nested for an F-test because their shared-name factor series differ.",
            "Do not attribute the entire R-squared change to RMW and CMA; this workflow does not isolate the incremental contribution of those factors.",
        ],
        "interpretation_limitations": [
            "Monthly intercepts are model-conditional historical estimates, not future returns or cost-adjusted strategy alpha.",
            "A current revised snapshot is not a point-in-time archive of what was available in each historical month.",
            "The ddof=1 variance identity is an in-sample OLS decomposition; it does not establish future residual independence or predictability.",
            "HAC confidence intervals and p-values use a t reference and finite-sample correction; assumptions and economic realizability are not established here.",
            "The cumulative contribution chart is an arithmetic sum of monthly return terms, not compounded wealth, NAV, or a zero-dollar factor portfolio.",
        ],
    }


def _set_chart_theme() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": PALETTE["paper"],
            "axes.facecolor": PALETTE["paper"],
            "savefig.facecolor": PALETTE["paper"],
            "text.color": PALETTE["ink"],
            "axes.labelcolor": PALETTE["ink"],
            "axes.edgecolor": PALETTE["grid"],
            "xtick.color": PALETTE["ink"],
            "ytick.color": PALETTE["ink"],
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        }
    )


def _finish_axis(axis: plt.Axes) -> None:
    axis.grid(axis="x", color=PALETTE["grid"], linewidth=0.8, alpha=0.72)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_visible(False)
    axis.tick_params(axis="y", length=0)


def _save_figure(fig: plt.Figure, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    width, height = _png_dimensions(destination)
    plt.close(fig)
    return {
        "path": destination.relative_to(ROOT).as_posix(),
        "width_px": width,
        "height_px": height,
        "format": "PNG",
    }


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG image: {path}")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def make_figures(
    total: pd.Series,
    frames: Mapping[str, pd.DataFrame],
    fits: Mapping[str, MonthlyFactorFit],
    *,
    output_dir: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Write the three chapter figures using the frozen sample and shared fits."""
    _set_chart_theme()
    import uuid
    folder = output_dir or ROOT / "runs" / ("cli_ch15_factor_models_" + uuid.uuid4().hex) / "figures"

    # 1. Model-conditional monthly intercepts with HAC uncertainty and fit.
    fig, axis = plt.subplots(figsize=(8.2, 4.6), constrained_layout=True)
    labels = {"capm": "CAPM", "ff3": "Fama–French 3-factor", "ff5": "Fama–French 5-factor"}
    for row, name in enumerate(("capm", "ff3", "ff5")):
        fit = fits[name]
        alpha = fit.coefficient_table.loc["const"]
        estimate = float(alpha["estimate"]) * 100
        low = float(alpha["ci_low_hac"]) * 100
        high = float(alpha["ci_high_hac"]) * 100
        axis.errorbar(
            estimate,
            row,
            xerr=np.array([[estimate - low], [high - estimate]]),
            fmt="o",
            color=PALETTE["orange"],
            ecolor=PALETTE["teal"],
            capsize=4,
            markersize=7,
            linewidth=2,
            zorder=3,
        )
        axis.text(
            0.98,
            row,
            f"R² = {fit.r_squared:.3f}",
            transform=axis.get_yaxis_transform(),
            ha="right",
            va="center",
            color=PALETTE["ink"],
            fontsize=9,
        )
    axis.axvline(0, color=PALETTE["gray"], linewidth=1, linestyle="--")
    axis.set_yticks(range(3), [labels[name] for name in ("capm", "ff3", "ff5")])
    interval_lows = [
        float(fits[name].coefficient_table.loc["const", "ci_low_hac"]) * 100
        for name in ("capm", "ff3", "ff5")
    ]
    interval_highs = [
        float(fits[name].coefficient_table.loc["const", "ci_high_hac"]) * 100
        for name in ("capm", "ff3", "ff5")
    ]
    axis.set_xlim(min(interval_lows) - 0.05, max(interval_highs) + 0.23)
    axis.invert_yaxis()
    axis.set_xlabel("Monthly alpha estimate and HAC 95% CI (% per month)")
    axis.set_title(f"{total.name} intercept changes with the factor benchmark", loc="left", weight="bold")
    axis.text(
        0,
        -0.20,
        "Bartlett HAC; 6 monthly observation-row lags. Intervals use a t reference.",
        transform=axis.transAxes,
        color=PALETTE["gray"],
        fontsize=8,
    )
    _finish_axis(axis)
    alpha_figure = _save_figure(fig, folder / "ch15_alpha_model_comparison.png")

    # 2. FF5 exposure estimates, with the shared core's HAC intervals.
    ff5 = fits["ff5"].coefficient_table.drop(index="const")
    fig, axis = plt.subplots(figsize=(7.8, 4.7), constrained_layout=True)
    for row, (factor, values) in enumerate(ff5.iterrows()):
        estimate = float(values["estimate"])
        low = float(values["ci_low_hac"])
        high = float(values["ci_high_hac"])
        axis.errorbar(
            estimate,
            row,
            xerr=np.array([[estimate - low], [high - estimate]]),
            fmt="o",
            color=PALETTE["orange"],
            ecolor=PALETTE["teal"],
            capsize=4,
            markersize=7,
            linewidth=2,
            zorder=3,
        )
    axis.axvline(0, color=PALETTE["gray"], linewidth=1, linestyle="--")
    axis.set_yticks(range(len(ff5)), list(ff5.index))
    axis.invert_yaxis()
    axis.set_xlabel("FF5 factor loading (unitless; HAC 95% CI)")
    axis.set_title(f"{total.name} estimated FF5 exposures", loc="left", weight="bold")
    axis.text(
        0,
        -0.17,
        "Monthly returns; 120 observations; Bartlett HAC with 6 monthly row lags.",
        transform=axis.transAxes,
        color=PALETTE["gray"],
        fontsize=8,
    )
    _finish_axis(axis)
    ff5_figure = _save_figure(fig, folder / "ch15_ff5_loadings.png")

    # 3. Arithmetic cumulative sums: alpha + factor terms + residual = observed.
    fit = fits["ff5"]
    frame = frames["ff5"]
    index = total.index.to_timestamp(how="end")
    alpha = float(fit.coefficient_table.loc["const", "estimate"])
    contributions: dict[str, pd.Series] = {
        factor: fit.coefficient_table.loc[factor, "estimate"] * frame[factor]
        for factor in MODEL_FACTORS["ff5"]
    }
    contributions["Constant"] = pd.Series(alpha, index=total.index)
    cumulative = {name: (values.cumsum() * 100).to_numpy() for name, values in contributions.items()}
    cumulative["Residual"] = (fit.residuals.cumsum() * 100).to_numpy()
    cumulative["Fitted excess"] = (fit.fitted_excess.cumsum() * 100).to_numpy()
    cumulative["Observed excess"] = ((total - frame["RF"]).cumsum() * 100).to_numpy()

    colors = {
        "Mkt-RF": PALETTE["teal"],
        "SMB": PALETTE["orange"],
        "HML": PALETTE["teal_light"],
        "RMW": PALETTE["orange_light"],
        "CMA": PALETTE["teal_mid"],
        "Constant": PALETTE["gray"],
        "Residual": PALETTE["orange_dark"],
        "Fitted excess": PALETTE["ink"],
        "Observed excess": "#555C5A",
    }
    fig, axis = plt.subplots(figsize=(10.2, 6.2), constrained_layout=True)
    for label in MODEL_FACTORS["ff5"]:
        axis.plot(index, cumulative[label], color=colors[label], linewidth=1.45, label=label)
    axis.plot(
        index,
        cumulative["Constant"],
        color=colors["Constant"],
        linewidth=1.35,
        linestyle=":",
        label="Constant (alpha)",
    )
    axis.plot(
        index,
        cumulative["Residual"],
        color=colors["Residual"],
        linewidth=1.5,
        linestyle="--",
        label="Residual",
    )
    axis.plot(
        index,
        cumulative["Fitted excess"],
        color=colors["Fitted excess"],
        linewidth=2.5,
        label="Fitted excess (sum of model terms)",
    )
    axis.plot(
        index,
        cumulative["Observed excess"],
        color=colors["Observed excess"],
        linewidth=1.7,
        linestyle="--",
        label="Observed excess",
    )
    axis.axhline(0, color=PALETTE["grid"], linewidth=1)
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axis.set_xlabel("Monthly period")
    axis.set_ylabel("Arithmetic cumulative contribution (percentage points)")
    axis.set_title("FF5 arithmetic attribution of monthly excess returns", loc="left", weight="bold")
    axis.text(
        0,
        -0.20,
        "Cumulative sums of monthly terms; not NAV, compounded wealth, or a zero-dollar factor portfolio.",
        transform=axis.transAxes,
        color=PALETTE["gray"],
        fontsize=8,
    )
    axis.legend(frameon=False, ncol=3, fontsize=8, loc="upper left")
    _finish_axis(axis)
    attribution_figure = _save_figure(fig, folder / "ch15_ff5_arithmetic_attribution.png")

    return {
        "alpha_model_comparison": alpha_figure,
        "ff5_loadings": ff5_figure,
        "ff5_arithmetic_attribution": attribution_figure,
    }


def write_artifacts(
    fits: Mapping[str, MonthlyFactorFit],
    summary: dict[str, Any],
    *,
    coefficients_path: Path | None = None,
    summary_path: Path | None = None,
) -> dict[str, str]:
    """Write a long-form coefficient CSV and a source-linked JSON summary."""
    import uuid
    default_run = ROOT / "runs" / ("cli_ch15_factor_models_" + uuid.uuid4().hex)
    coefficients_path = coefficients_path or default_run / "results/ch15_factor_model_coefficients.csv"
    summary_path = summary_path or default_run / "results/ch15_artifacts_summary.json"
    rows: list[dict[str, Any]] = []
    for name, fit in fits.items():
        for coefficient, values in fit.coefficient_table.iterrows():
            rows.append(
                {
                    "model": name,
                    "coefficient": coefficient,
                    **{column: float(value) for column, value in values.items()},
                    "r_squared": fit.r_squared,
                    "adjusted_r_squared": fit.adjusted_r_squared,
                    "nobs": fit.nobs,
                    "hac_maxlags_months": fit.hac_maxlags,
                }
            )
    coefficients_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(coefficients_path, index=False, float_format="%.12g")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return {
        "coefficients_csv": coefficients_path.relative_to(ROOT).as_posix(),
        "summary_json": summary_path.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch15_factor_models_" + uuid.uuid4().hex)
    import argparse
    argparse.ArgumentParser(description="Historical chapter CLI; French route requires separate rights and authorization; use the notebook for default offline teaching").parse_args()
    total, frames = load_sample()
    fits = fit_models(total, frames, hac_maxlags=6)
    summary = build_summary(total, frames, fits)
    summary["generated_artifacts"] = {
        "coefficients_csv": (default_run / "results/ch15_factor_model_coefficients.csv").relative_to(ROOT).as_posix(),
        "summary_json": (default_run / "results/ch15_artifacts_summary.json").relative_to(ROOT).as_posix(),
        "figures": make_figures(total, frames, fits, output_dir=default_run / "figures"),
    }
    outputs = write_artifacts(fits, summary, coefficients_path=default_run / "results/ch15_factor_model_coefficients.csv", summary_path=default_run / "results/ch15_artifacts_summary.json")
    print(f"sample: {summary['sample']['start_month']} to {summary['sample']['end_month']} ({summary['sample']['n_months']} months)")
    for name, model in summary["models"].items():
        alpha = model["coefficients"]["const"]
        print(
            f"{name}: alpha={alpha['estimate']:.9f}, "
            f"HAC95%CI=({alpha['ci_low_hac']:.9f}, {alpha['ci_high_hac']:.9f}), "
            f"R2={model['r_squared']:.6f}"
        )
    print(f"wrote {outputs['coefficients_csv']} and {outputs['summary_json']}")


if __name__ == "__main__":
    main()
