"""Chapter 14 CAPM examples and the frozen French monthly regression."""

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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.asset_pricing import (  # noqa: E402
    beta_from_covariance,
    capm_expected_return,
    constructed_two_asset_sample,
    fit_capm_excess,
)
from quant_course.factor_models import fit_monthly_factor_model  # noqa: E402
from quant_course.market_data import load_monthly_snapshot  # noqa: E402


def load_french_sample() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    industry_manifest = json.loads(
        (ROOT / "data/manifests/french_industries_2026-10-05.json").read_text()
    )
    factor_manifest = json.loads(
        (ROOT / "data/manifests/french_factors_2026-10-05.json").read_text()
    )["datasets"]["ff3"]
    industry = load_monthly_snapshot(
        ROOT / industry_manifest["processed_path"],
        industry_manifest["processed_sha256"],
        ["NoDur"],
    )
    factors = load_monthly_snapshot(
        ROOT / factor_manifest["processed_path"],
        factor_manifest["processed_sha256"],
        ["Mkt-RF", "RF"],
    )
    combined = industry.join(factors, how="inner", validate="one_to_one")
    sample = combined.loc["2010-01":"2019-12"].copy()
    expected = pd.period_range("2010-01", "2019-12", freq="M", name="month")
    if not sample.index.equals(expected) or sample.isna().any().any():
        raise ValueError("the frozen French inputs do not form the declared 120-month sample")
    if not np.isfinite(sample.to_numpy(dtype=float)).all():
        raise ValueError("the French sample contains non-finite values")
    return sample, industry_manifest, factor_manifest


def constructed_report() -> dict[str, Any]:
    rows = constructed_two_asset_sample()
    market = rows["Mkt-RF"]
    rf = rows["RF"]
    series = pd.DataFrame(
        {
            "Mkt-RF": market,
            "Asset_A_excess": rows["Asset_A"] - rf,
            "Asset_B_excess": rows["Asset_B"] - rf,
        }
    )
    assets: dict[str, Any] = {}
    for name in ("Asset_A", "Asset_B"):
        excess = rows[name] - rf
        fit = fit_capm_excess(excess, market)
        assets[name] = {
            "mean_total_return": float(rows[name].mean()),
            "mean_excess_return": fit.asset_excess_mean,
            "beta_covariance_over_variance": beta_from_covariance(excess, market),
            "alpha_ols": fit.alpha,
            "r_squared": fit.r_squared,
            "residuals": list(fit.residuals),
            "fitted_excess_returns": list(fit.fitted_excess_returns),
        }
    centered = market.to_numpy() - market.mean()
    return {
        "kind": "constructed four-row single-period teaching sample; rows are not probability-weighted scenarios or market observations",
        "risk_free_return": float(rf.iloc[0]),
        "series_order": list(series.columns),
        "sample_mean_vector_equal_row_weights": {
            name: float(value) for name, value in series.mean().items()
        },
        "sample_covariance_matrix_ddof_1": {
            row: {column: float(value) for column, value in values.items()}
            for row, values in series.cov().iterrows()
        },
        "market_excess_mean": float(market.mean()),
        "market_variance_population": float(np.mean(centered**2)),
        "covariance_population": {
            name: float(
                np.mean(
                    (rows[name].to_numpy() - rf.to_numpy() - (rows[name].mean() - rf.mean()))
                    * centered
                )
            )
            for name in ("Asset_A", "Asset_B")
        },
        "assets": assets,
    }


def french_report(
    sample: pd.DataFrame,
    industry_manifest: dict[str, Any],
    factor_manifest: dict[str, Any],
) -> tuple[dict[str, Any], Any]:
    fit = fit_monthly_factor_model(
        sample["NoDur"],
        sample[["Mkt-RF", "RF"]],
        factor_columns=("Mkt-RF",),
        hac_maxlags=5,
    )
    coefficients = fit.coefficient_table
    alpha = coefficients.loc["const"]
    beta = coefficients.loc["Mkt-RF"]
    report = {
        "source": "Kenneth R. French Data Library current published snapshot",
        "industry_source_url": industry_manifest["source_url"],
        "factor_source_url": factor_manifest["source_url"],
        "industry_downloaded_at_utc": industry_manifest["downloaded_at_utc"],
        "factor_downloaded_at_utc": factor_manifest["http_response"]["downloaded_at_utc"],
        "industry_processed_sha256": industry_manifest["processed_sha256"],
        "factor_processed_sha256": factor_manifest["processed_sha256"],
        "factor_declared_crsp_database_month": factor_manifest["source_file_vintage"][
            "declared_crsp_database_month"
        ],
        "sample_start": str(sample.index[0]),
        "sample_end": str(sample.index[-1]),
        "frequency": "monthly",
        "n_months": fit.nobs,
        "asset": "NoDur value-weighted 10-industry portfolio total return",
        "market": "French Mkt-RF, published monthly market excess return",
        "risk_free_proxy": "same-month French RF; source describes a 1-month Treasury-bill proxy",
        "unit": "decimal simple return per month; beta is dimensionless; alpha is per month",
        "hac": {
            "kernel": "Bartlett",
            "maxlags": fit.hac_maxlags,
            "lag_unit": "monthly observation rows",
            "finite_sample_correction": True,
        },
        "alpha_monthly": float(alpha["estimate"]),
        "alpha_hac_se_monthly": float(alpha["standard_error_hac"]),
        "alpha_hac_t_reference": float(alpha["t_hac"]),
        "alpha_hac_p_reference": float(alpha["p_hac"]),
        "alpha_hac_95ci_monthly": [
            float(alpha["ci_low_hac"]),
            float(alpha["ci_high_hac"]),
        ],
        "beta": float(beta["estimate"]),
        "beta_hac_se": float(beta["standard_error_hac"]),
        "beta_hac_t_reference": float(beta["t_hac"]),
        "beta_hac_p_reference": float(beta["p_hac"]),
        "beta_hac_95ci": [float(beta["ci_low_hac"]), float(beta["ci_high_hac"])],
        "r_squared": fit.r_squared,
        "adjusted_r_squared": fit.adjusted_r_squared,
        "mean_NoDur_total_return_monthly": float(sample["NoDur"].mean()),
        "mean_RF_monthly": float(sample["RF"].mean()),
        "mean_NoDur_excess_return_monthly": float(
            (sample["NoDur"] - sample["RF"]).mean()
        ),
        "mean_market_excess_return_monthly": float(sample["Mkt-RF"].mean()),
        "condition_number": fit.condition_number,
        "scope": (
            "descriptive regression on a 2026 current snapshot; not a point-in-time test, "
            "forecast, strategy, cost-adjusted result, or proof of CAPM validity"
        ),
    }
    return report, fit


def make_sml_cml_figure(destination: Path) -> None:
    rf = 0.02
    market_mean = 0.08
    market_premium = market_mean - rf
    market_sigma = float(np.sqrt(0.00625))
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), constrained_layout=True)

    efficient_weights = np.linspace(0.0, 1.0, 70)
    borrowing_weights = np.linspace(1.0, 1.5, 35)
    axes[0].plot(
        efficient_weights * market_sigma * 100,
        (rf + efficient_weights * market_premium) * 100,
        color="#247F82",
        label="Lending / market mix (0 ≤ w ≤ 1)",
    )
    axes[0].plot(
        borrowing_weights * market_sigma * 100,
        (rf + borrowing_weights * market_premium) * 100,
        color="#247F82",
        linestyle="--",
        label="Borrowing extension (w > 1)",
    )
    axes[0].scatter([0, market_sigma * 100], [rf * 100, market_mean * 100],
                    color=["#CF8951", "#247F82"], zorder=3)
    axes[0].annotate("RF", (0, rf * 100), xytext=(5, 5), textcoords="offset points")
    axes[0].annotate("Market", (market_sigma * 100, market_mean * 100),
                     xytext=(5, 5), textcoords="offset points")
    axes[0].axvline(market_sigma * 100, color="#777777", linestyle=":", linewidth=1)
    axes[0].set(
        title="Capital Market Line (CML)",
        xlabel="Portfolio standard deviation (% per period)",
        ylabel="Expected simple return (% per period)",
    )
    axes[0].text(
        0.03, 0.97,
        "w is the market-portfolio weight.\nExtension assumes borrowing at RF.",
        transform=axes[0].transAxes, va="top", fontsize=8,
    )
    axes[0].legend(frameon=False, fontsize=7, loc="lower right")

    betas = np.linspace(-0.2, 2.0, 100)
    expected = np.array([capm_expected_return(rf, b, market_mean) for b in betas])
    axes[1].plot(betas, expected * 100, color="#247F82", label="CAPM expected return")
    for beta, name in ((0.5, "Asset A"), (1.5, "Asset B")):
        return_value = capm_expected_return(rf, beta, market_mean)
        axes[1].scatter([beta], [return_value * 100], zorder=3, label=f"{name}, β={beta:.1f}")
    axes[1].axvline(1.0, color="#777777", linestyle=":", linewidth=1)
    axes[1].set(
        title="Security Market Line (SML)",
        xlabel="Market beta (unitless)",
        ylabel="Expected simple return (% per period)",
    )
    axes[1].legend(frameon=False, fontsize=8)
    for axis in axes:
        axis.grid(alpha=0.22)
    fig.suptitle(
        "Constructed one-period inputs: RF 2%, E[Rm] 8%, σm 7.91%",
        fontsize=10,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def make_beta_scatter_figure(destination: Path) -> None:
    rows = constructed_two_asset_sample()
    rf = float(rows["RF"].iloc[0])
    market_mean = rf + float(rows["Mkt-RF"].mean())
    labels = ("Asset_A", "Asset_B")
    betas: list[float] = []
    sample_means: list[float] = []
    implied_means: list[float] = []
    for name in labels:
        fit = fit_capm_excess(rows[name] - rows["RF"], rows["Mkt-RF"])
        betas.append(fit.beta)
        sample_means.append(float(rows[name].mean()))
        implied_means.append(capm_expected_return(rf, fit.beta, market_mean))
    beta_grid = np.linspace(0.0, 1.8, 100)
    sml = np.array([capm_expected_return(rf, b, market_mean) for b in beta_grid])

    fig, axis = plt.subplots(figsize=(7.5, 5), constrained_layout=True)
    axis.plot(beta_grid, sml * 100, color="#247F82", label="CAPM-implied expected return")
    axis.scatter(
        betas, np.asarray(sample_means) * 100, marker="o", s=55,
        color="#CF8951", label="Observed mean across 4 constructed rows",
        zorder=3,
    )
    for beta, mean, implied, name in zip(betas, sample_means, implied_means, labels):
        axis.annotate(
            f"{name}: β={beta:.1f}, sample mean={mean:.0%}\nSML={implied:.0%}",
            (beta, mean * 100), xytext=(7, 7), textcoords="offset points", fontsize=8,
        )
    axis.set(
        title="Same constructed sample mean, different market sensitivity",
        xlabel="Beta estimated from the same four constructed rows (unitless)",
        ylabel="Return (% per single period)",
    )
    axis.text(
        0.02, 0.02,
        "Dots are realized sample means; the line is a model expectation.\nRows have equal arithmetic weight and are not a probability model.",
        transform=axis.transAxes, fontsize=8, va="bottom",
    )
    axis.legend(frameon=False, fontsize=8)
    axis.grid(alpha=0.22)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def make_french_regression_figure(
    sample: pd.DataFrame,
    fit: Any,
    destination: Path,
) -> None:
    x = sample["Mkt-RF"]
    y = sample["NoDur"] - sample["RF"]
    coefficients = fit.coefficient_table
    alpha = float(coefficients.loc["const", "estimate"])
    beta = float(coefficients.loc["Mkt-RF", "estimate"])
    fitted = fit.fitted_excess
    residuals = fit.residuals
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), constrained_layout=True)
    axes[0].scatter(x * 100, y * 100, s=22, alpha=0.65, color="#247F82")
    x_grid = np.linspace(float(x.min()), float(x.max()), 120)
    axes[0].plot(x_grid * 100, (alpha + beta * x_grid) * 100,
                 color="#CF8951", linewidth=2)
    axes[0].set(
        title=f"NoDur monthly CAPM fit: β={beta:.3f}, α={alpha:.4%}",
        xlabel="Mkt-RF (% per month)",
        ylabel="NoDur − RF (% per month)",
    )
    axes[0].text(
        0.03, 0.97,
        f"n={fit.nobs}, R²={fit.r_squared:.3f}\nCurrent snapshot; 2010–2019",
        transform=axes[0].transAxes, va="top", fontsize=8,
    )
    axes[1].axhline(0, color="#555555", linewidth=1)
    axes[1].plot(
        residuals.index.to_timestamp(how="end"),
        residuals.to_numpy() * 100,
        color="#247F82", linewidth=1,
    )
    axes[1].set(
        title="OLS residual by return month",
        xlabel="Return month label",
        ylabel="Residual (% per month)",
    )
    for axis in axes:
        axis.grid(alpha=0.22)
    fig.suptitle("French NoDur industry return on the published market excess factor",
                 fontsize=10)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch14_asset_pricing_" + uuid.uuid4().hex)
    import argparse
    argparse.ArgumentParser(description="Historical chapter CLI; French route requires separate rights and authorization; use the notebook for default offline teaching").parse_args()
    construction = constructed_report()
    sample, industry_manifest, factor_manifest = load_french_sample()
    real, fit = french_report(sample, industry_manifest, factor_manifest)
    print("CONSTRUCTED FOUR-ROW EXAMPLE")
    print(json.dumps(construction, ensure_ascii=False, indent=2))
    print("FRENCH 2010-01 TO 2019-12 MONTHLY CAPM")
    print(json.dumps(real, ensure_ascii=False, indent=2))
    (default_run / "results").mkdir(parents=True, exist_ok=True)
    (default_run / "results" / "ch14_constructed_checks.json").write_text(
        json.dumps(construction, ensure_ascii=False, indent=2) + "\n"
    )
    (default_run / "results" / "ch14_french_capm_2010_2019.json").write_text(
        json.dumps(real, ensure_ascii=False, indent=2) + "\n"
    )
    make_sml_cml_figure(default_run / "figures" / "ch14_sml_cml.png")
    make_beta_scatter_figure(default_run / "figures" / "ch14_beta_scatter.png")
    make_french_regression_figure(
        sample, fit, default_run / "figures" / "ch14_nodur_regression_residuals.png"
    )


if __name__ == "__main__":
    main()
