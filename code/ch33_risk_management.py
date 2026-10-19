"""Chapter 33 CLI: losses, exposures, stress, liquidity, margin and VaR backtesting."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
if "inline" not in matplotlib.get_backend().lower():
    try:
        matplotlib.use("Agg")
    except Exception:
        pass
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.backtest import BacktestConfig, run_backtest  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.portfolio_construction import exposure_report  # noqa: E402
from quant_course.risk import (  # noqa: E402
    empirical_var_es,
    kupiec_pof,
    lagged_rolling_var,
    liquidation_days,
    margin_requirements,
    normal_var_es,
    scenario_pnl,
    simulate_student_t_losses,
    student_t_var_es,
)

FIGURES = (
    "ch33_discrete_quantile_es.png",
    "ch33_loss_model_comparison.png",
    "ch33_ledger_stress.png",
    "ch33_pof_test_window.png",
)

INPUTS = {
    "pinned_discrete": {
        "loss_values": [-10.0, 0.0, 5.0, 20.0],
        "probabilities": [0.50, 0.30, 0.15, 0.05],
        "alpha": 0.90,
        "horizon": "one scenario interval",
    },
    "portfolio_dgp": {
        "asset_names": ["A", "B"],
        "weights": [0.60, 0.40],
        "mean_returns": [0.0015, 0.0020],
        "standard_deviations": [0.04, 0.06],
        "correlation": 0.45,
        "student_t_degrees_freedom": 5.0,
        "n_historical_scenarios": 3000,
        "historical_seed": 20261033,
        "alpha": 0.99,
        "horizon": "one constructed month; simple returns",
        "n_monte_carlo_scenarios": 50000,
        "monte_carlo_seed": 20261034,
    },
    "rolling_backtest": {
        "estimation_observations": 1500,
        "test_observations": 1500,
        "rolling_window": 250,
        "alpha": 0.95,
        "horizon": "one constructed month; simple returns",
    },
    "ledger_stress": {
        "dates": ["2026-01-30", "2026-02-02", "2026-02-27", "2026-03-02"],
        "initial_cash_currency": 1000.0,
        "fee_rate": 0.002,
        "cash_rate_per_period": 0.0,
        "initial_target_weights": [0.50, 0.30],
        "mark_prices": {"A": [10.0, 11.0, 12.1, 12.0], "B": [20.0, 19.0, 19.0, 21.0]},
        "execution_prices": {"A": [10.0, 10.0, 12.0, 12.0], "B": [20.0, 20.0, 19.5, 20.0]},
        "overnight_gap_returns": [-0.15, -0.25],
        "baseline_correlation": 0.45,
        "stress_correlation_assumption": 0.90,
        "normal_adv_shares_per_session": {"A": 150.0, "B": 60.0},
        "stress_adv_fraction": 0.25,
        "participation_rate": 0.10,
        "normal_initial_margin_rate": 0.55,
        "normal_maintenance_margin_rate": 0.35,
        "stress_initial_margin_rate": 0.85,
        "stress_maintenance_margin_rate": 0.75,
        "stress_loss_limit_fraction_of_nav": 0.08,
        "factor_names": ["Market", "Value"],
        "factor_loadings_by_asset": {"A": [1.00, 0.40], "B": [1.20, -0.20]},
        "betas": [1.00, 1.20],
        "sectors": ["Technology", "Financials"],
        "concentration_weights": [0.50, 0.30],
        "neutrality_example_weights": [0.50, -0.50],
        "neutrality_example_betas": [1.50, 0.30],
        "neutrality_example_sectors": ["Same sector", "Same sector"],
    },
    "french_real_example": {
        "equal_weights": "1 / number of industry portfolios",
        "estimation_observations": 120,
        "alpha": 0.95,
        "horizon": "one published calendar month; simple return",
    },
}


def _finite_round(value: float, digits: int = 8) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError("analysis produced a non-finite value")
    return round(out, digits)


def _synthetic_asset_returns() -> np.ndarray:
    spec = INPUTS["portfolio_dgp"]
    vols = np.asarray(spec["standard_deviations"], dtype=float)
    corr = float(spec["correlation"])
    cov = np.outer(vols, vols) * np.array([[1.0, corr], [corr, 1.0]])
    rng = np.random.default_rng(int(spec["historical_seed"]))
    z = rng.multivariate_normal(np.zeros(2), cov, size=int(spec["n_historical_scenarios"]))
    df = float(spec["student_t_degrees_freedom"])
    scale = np.sqrt((df - 2.0) / rng.chisquare(df, size=len(z)))
    returns = np.asarray(spec["mean_returns"], dtype=float) + z * scale[:, None]
    if not np.isfinite(returns).all():
        raise ValueError("constructed asset returns are not finite")
    return returns


def _discrete_case() -> dict[str, object]:
    spec = INPUTS["pinned_discrete"]
    values = np.asarray(spec["loss_values"], dtype=float)
    probs = np.asarray(spec["probabilities"], dtype=float)
    counts = np.rint(probs * 20).astype(int)
    losses = np.repeat(values, counts)
    var, es = empirical_var_es(losses, float(spec["alpha"]))
    strict = float(losses[losses > var].mean())
    inclusive = float(losses[losses >= var].mean())
    cdf_at_var = float(probs[values <= var].sum())
    return {
        "loss_values": values.tolist(),
        "probabilities": probs.tolist(),
        "alpha": float(spec["alpha"]),
        "horizon": spec["horizon"],
        "scenario_count": int(len(losses)),
        "var": _finite_round(var),
        "es": _finite_round(es),
        "cdf_at_var": _finite_round(cdf_at_var),
        "strict_tail_conditional_mean": _finite_round(strict),
        "inclusive_tail_conditional_mean": _finite_round(inclusive),
    }


def _portfolio_comparison() -> tuple[dict[str, object], dict[str, np.ndarray]]:
    spec = INPUTS["portfolio_dgp"]
    asset_returns = _synthetic_asset_returns()
    weights = np.asarray(spec["weights"], dtype=float)
    portfolio_returns = asset_returns @ weights
    losses = -portfolio_returns
    alpha = float(spec["alpha"])
    hist_var, hist_es = empirical_var_es(losses, alpha)
    loss_mean = float(losses.mean())
    loss_std = float(losses.std(ddof=1))
    normal_var, normal_es = normal_var_es(loss_mean, loss_std, alpha)
    df = float(spec["student_t_degrees_freedom"])
    student_var, student_es = student_t_var_es(loss_mean, loss_std, df, alpha)
    z = float(stats.norm.ppf(alpha))
    scaled_normal_std = (student_var - loss_mean) / z
    scaled_normal_es = normal_var_es(loss_mean, scaled_normal_std, alpha)[1]
    mc_losses = simulate_student_t_losses(
        loss_mean,
        loss_std,
        df,
        int(spec["n_monte_carlo_scenarios"]),
        int(spec["monte_carlo_seed"]),
    )
    mc_var, mc_es = empirical_var_es(mc_losses, alpha)
    out = {
        "asset_names": list(spec["asset_names"]),
        "portfolio_weights": weights.tolist(),
        "mean_returns": list(spec["mean_returns"]),
        "asset_standard_deviations": list(spec["standard_deviations"]),
        "dgp_correlation": float(spec["correlation"]),
        "sample_correlation": _finite_round(np.corrcoef(asset_returns, rowvar=False)[0, 1]),
        "student_t_degrees_freedom": df,
        "n_historical_scenarios": int(len(losses)),
        "historical_seed": int(spec["historical_seed"]),
        "alpha": alpha,
        "horizon": spec["horizon"],
        "historical": {
            "mean_loss": _finite_round(loss_mean), "std_loss": _finite_round(loss_std),
            "var": _finite_round(hist_var), "es": _finite_round(hist_es),
        },
        "normal_fitted": {
            "mean_loss": _finite_round(loss_mean), "std_loss": _finite_round(loss_std),
            "var": _finite_round(normal_var), "es": _finite_round(normal_es),
        },
        "student_t_fitted": {
            "mean_loss": _finite_round(loss_mean), "std_loss": _finite_round(loss_std),
            "degrees_freedom": df, "var": _finite_round(student_var), "es": _finite_round(student_es),
        },
        "monte_carlo": {
            "n_scenarios": int(spec["n_monte_carlo_scenarios"]),
            "seed": int(spec["monte_carlo_seed"]), "var": _finite_round(mc_var), "es": _finite_round(mc_es),
        },
        "variance_matched_tail_counterexample": {
            "normal_var": _finite_round(normal_var), "student_t_var": _finite_round(student_var),
            "normal_es": _finite_round(normal_es), "student_t_es": _finite_round(student_es),
            "std_loss_shared": _finite_round(loss_std),
            "normal_std_required_to_match_student_t_var": _finite_round(scaled_normal_std),
            "scaled_normal_es_at_matched_var": _finite_round(scaled_normal_es),
        },
    }
    return out, {"losses": losses, "mc_losses": mc_losses, "asset_returns": asset_returns}


def _exposures(stress_spec: dict[str, object]) -> dict[str, object]:
    assets = ["A", "B"]
    weights = np.asarray(stress_spec["initial_target_weights"], dtype=float)
    report = exposure_report(weights, np.asarray(stress_spec["betas"], dtype=float), list(stress_spec["sectors"]))
    gross = float(np.abs(weights).sum())
    net = float(weights.sum())
    normalized = np.abs(weights) / gross
    loading = np.asarray([stress_spec["factor_loadings_by_asset"][a] for a in assets], dtype=float)
    neutral_w = np.asarray(stress_spec["neutrality_example_weights"], dtype=float)
    neutral_report = exposure_report(
        neutral_w,
        np.asarray(stress_spec["neutrality_example_betas"], dtype=float),
        list(stress_spec["neutrality_example_sectors"]),
    )
    return {
        "basis": "risk-asset weights per NAV; cash is reported separately",
        "risk_asset_weights": weights.tolist(),
        "net_exposure": _finite_round(report.net),
        "gross_exposure": _finite_round(report.gross),
        "net_leverage_on_nav": _finite_round(net),
        "gross_leverage_on_nav": _finite_round(gross),
        "cash_weight": _finite_round(1.0 - net),
        "market_beta": _finite_round(report.beta),
        "factor_names": list(stress_spec["factor_names"]),
        "factor_loadings_by_asset": stress_spec["factor_loadings_by_asset"],
        "factor_exposures": {
            name: _finite_round(value)
            for name, value in zip(stress_spec["factor_names"], loading.T @ weights)
        },
        "sector_net_exposures": {k: _finite_round(v) for k, v in report.sector_net.items()},
        "concentration_hhi_within_gross_risk_assets": _finite_round(float(normalized @ normalized)),
        "largest_risk_asset_share_of_gross": _finite_round(float(normalized.max())),
        "neutrality_counterexample": {
            "weights": neutral_w.tolist(), "net_exposure": _finite_round(neutral_report.net),
            "gross_exposure": _finite_round(neutral_report.gross),
            "net_leverage_on_nav": _finite_round(float(neutral_w.sum())),
            "gross_leverage_on_nav": _finite_round(float(np.abs(neutral_w).sum())),
            "beta": _finite_round(neutral_report.beta),
            "sector_net_exposures": {k: _finite_round(v) for k, v in neutral_report.sector_net.items()},
        },
    }


def _ledger_stress() -> tuple[dict[str, object], dict[str, object]]:
    spec = INPUTS["ledger_stress"]
    dates = pd.DatetimeIndex(spec["dates"])
    names = ["A", "B"]
    marks = pd.DataFrame(spec["mark_prices"], index=dates, columns=names, dtype=float)
    execs = pd.DataFrame(spec["execution_prices"], index=dates, columns=names, dtype=float)
    initial = np.asarray(spec["initial_target_weights"], dtype=float)
    base_targets = pd.DataFrame([initial], index=[dates[0]], columns=names)
    cfg = BacktestConfig(
        initial_cash=float(spec["initial_cash_currency"]), fee_rate=float(spec["fee_rate"]),
        cash_rate=float(spec["cash_rate_per_period"]),
    )

    # First run retrieves the actual Chapter 29 shares at the signal date. The second run sends
    # the risk-limited target through the same delayed execution ledger.
    initial_book = run_backtest(marks, base_targets, cfg, exec_prices=execs)
    signal_date = dates[-2]
    nav = float(initial_book.ledger.loc[signal_date, "nav"])
    quantities = initial_book.positions.loc[signal_date].to_numpy(dtype=float)
    current_weights = initial_book.weights.loc[signal_date].to_numpy(dtype=float)
    current_marks = marks.loc[signal_date].to_numpy(dtype=float)
    shocks = np.asarray(spec["overnight_gap_returns"], dtype=float)
    pnl_by_asset = scenario_pnl(quantities, current_marks, shocks)
    stress_loss = -float(pnl_by_asset.sum())
    stressed_nav = nav - stress_loss
    gross_before = float(np.abs(quantities * current_marks).sum())
    stressed_gross = float(np.abs(quantities * current_marks * (1.0 + shocks)).sum())

    adv = np.asarray([spec["normal_adv_shares_per_session"][a] for a in names], dtype=float)
    adv_stress = adv * float(spec["stress_adv_fraction"])
    participation = float(spec["participation_rate"])
    days_normal = [liquidation_days(q, v, participation) for q, v in zip(quantities, adv)]
    days_stress = [liquidation_days(q, v, participation) for q, v in zip(quantities, adv_stress)]
    normal_margin = margin_requirements(
        gross_before, nav, float(spec["normal_initial_margin_rate"]),
        float(spec["normal_maintenance_margin_rate"]),
    )
    stress_margin = margin_requirements(
        stressed_gross, stressed_nav, float(spec["stress_initial_margin_rate"]),
        float(spec["stress_maintenance_margin_rate"]),
    )

    loss_cap = nav * float(spec["stress_loss_limit_fraction_of_nav"])
    breached = stress_loss > loss_cap
    scale = min(1.0, loss_cap / stress_loss) if stress_loss > 0 else 1.0
    target = current_weights * scale
    targets = pd.DataFrame([initial, target], index=[dates[0], signal_date], columns=names)
    constrained_book = run_backtest(marks, targets, cfg, exec_prices=execs)
    fills = constrained_book.fills[constrained_book.fills["trade_time"] == dates[-1]]
    trade_rows = [
        {"asset": row.asset, "quantity": _finite_round(row.quantity), "price": _finite_round(row.price),
         "notional": _finite_round(row.notional), "fee": _finite_round(row.fee)}
        for row in fills.itertuples(index=False)
    ]
    actual_post_trade_weights = constrained_book.weights.loc[dates[-1]].to_numpy(dtype=float)
    out = {
        "source_ledger": "Chapter 29 run_backtest with frozen two-asset teaching ledger inputs",
        "currency": "USD",
        "financing": {
            "cash_rate_per_period": float(spec["cash_rate_per_period"]),
            "short_borrow_fees_rebates_and_margin_interest": "not modelled",
        },
        "signal_date": str(signal_date.date()),
        "execution_date": str(dates[-1].date()),
        "nav_at_signal_currency": _finite_round(nav, 4),
        "positions_at_signal_shares": {a: _finite_round(q, 8) for a, q in zip(names, quantities)},
        "mark_prices_at_signal_currency_per_share": {a: _finite_round(p, 4) for a, p in zip(names, current_marks)},
        "current_actual_risk_weights": {a: _finite_round(w, 8) for a, w in zip(names, current_weights)},
        "overnight_gap_simple_returns": {a: float(r) for a, r in zip(names, shocks)},
        "pnl_by_asset_currency": {a: _finite_round(v, 4) for a, v in zip(names, pnl_by_asset)},
        "conditional_stress_loss_currency": _finite_round(stress_loss, 4),
        "conditional_stress_loss_fraction_of_nav": _finite_round(stress_loss / nav),
        "stressed_nav_currency_before_risk_cut": _finite_round(stressed_nav, 4),
        "correlation_assumptions": {
            "baseline": float(spec["baseline_correlation"]),
            "stress": float(spec["stress_correlation_assumption"]),
            "interpretation": "constructed dependence-state assumptions, not probabilities",
        },
        "liquidity": {
            "participation_rate": participation,
            "normal_adv_shares_per_session": spec["normal_adv_shares_per_session"],
            "stress_adv_fraction": float(spec["stress_adv_fraction"]),
            "stress_adv_shares_per_session": {a: _finite_round(v) for a, v in zip(names, adv_stress)},
            "normal_days_to_liquidate": {a: _finite_round(v) for a, v in zip(names, days_normal)},
            "stress_days_to_liquidate": {a: _finite_round(v) for a, v in zip(names, days_stress)},
        },
        "margin": {
            "parameters_are_constructed": True,
            "normal_rates": {
                "initial": float(spec["normal_initial_margin_rate"]),
                "maintenance": float(spec["normal_maintenance_margin_rate"]),
            },
            "normal_gross_exposure_currency": _finite_round(gross_before, 4),
            "normal": {k: _finite_round(v, 4) for k, v in normal_margin.items()},
            "stress_rates": {
                "initial": float(spec["stress_initial_margin_rate"]),
                "maintenance": float(spec["stress_maintenance_margin_rate"]),
            },
            "stress_gross_exposure_currency": _finite_round(stressed_gross, 4),
            "stress": {k: _finite_round(v, 4) for k, v in stress_margin.items()},
            "maintenance_call_after_stress": stress_margin["maintenance_headroom"] < 0,
        },
        "risk_limit": {
            "rule": "maximum conditional gap loss as a fraction of current NAV",
            "limit_fraction": float(spec["stress_loss_limit_fraction_of_nav"]),
            "loss_cap_currency": _finite_round(loss_cap, 4),
            "breached_before_trade": bool(breached),
            "scale_factor": _finite_round(scale),
            "target_weights_after_limit": {a: _finite_round(w, 8) for a, w in zip(names, target)},
            "stress_loss_after_linear_resizing_currency": _finite_round(stress_loss * scale, 4),
            "signal_to_execution_lag_sessions": 1,
            "actual_execution_fills": trade_rows,
            "actual_close_weights_after_execution": {
                a: _finite_round(w, 8) for a, w in zip(names, actual_post_trade_weights)
            },
        },
    }
    return out, {
        "asset_names": names, "quantities": quantities, "prices": current_marks,
        "shocks": shocks, "pnl_by_asset": pnl_by_asset, "stress": out,
    }


def _pof_and_rolling(losses: np.ndarray) -> tuple[dict[str, object], dict[str, np.ndarray]]:
    spec = INPUTS["rolling_backtest"]
    train_n = int(spec["estimation_observations"])
    test_n = int(spec["test_observations"])
    alpha = float(spec["alpha"])
    window = int(spec["rolling_window"])
    if train_n + test_n > len(losses):
        raise ValueError("configured estimation and test windows exceed the constructed sample")
    training = losses[:train_n]
    test = losses[train_n:train_n + test_n]
    var, es = empirical_var_es(training, alpha)
    exceptions = int(np.count_nonzero(test > var))
    pof = kupiec_pof(exceptions, len(test), alpha)
    rolling = lagged_rolling_var(losses, window, alpha)
    out = {
        "loss_sign": "positive means loss; losses equal negative portfolio simple returns",
        "horizon": spec["horizon"],
        "alpha": alpha,
        "exception_probability_q": 1.0 - alpha,
        "estimation_window": {
            "start_index_inclusive": 0, "end_index_exclusive": train_n,
            "observations": train_n, "var_currency_per_nav": _finite_round(var),
            "es_currency_per_nav": _finite_round(es),
        },
        "test_window": {
            "start_index_inclusive": train_n, "end_index_exclusive": train_n + test_n,
            "observations": test_n, "realized_exceedances": exceptions,
            "expected_exceedance_count_under_null": _finite_round(test_n * (1.0 - alpha)),
            "lr_uc": _finite_round(float(pof["lr_uc"])),
            "p_value": float(pof["p_value"]),
        },
        "boundary_count_checks": {
            "zero_exceedances": kupiec_pof(0, len(test), alpha),
            "all_exceedances": kupiec_pof(len(test), len(test), alpha),
            "interpretation": "continuous likelihood limits; the chi-square p-values remain asymptotic diagnostics",
        },
        "kupiec_test": "unconditional coverage only; it does not test clustering, tail severity or model stability",
        "rolling_quantile_alignment": {
            "window_observations": window,
            "alpha": alpha,
            "first_forecast_target_index": window,
            "first_forecast_var": _finite_round(float(rolling[0])),
            "first_forecast_uses_loss_indices_inclusive": [0, window - 1],
            "first_realized_loss": _finite_round(float(losses[window])),
            "forecast_count": int(len(rolling)),
        },
    }
    return out, {"test_losses": test, "fixed_var": np.full(len(test), var), "rolling_forecasts": rolling}


def _french_real_example() -> dict[str, object]:
    spec = INPUTS["french_real_example"]
    industries, _rf, meta = load_industries_and_rf()
    portfolio_returns = industries.mean(axis=1).to_numpy(dtype=float)
    losses = -portfolio_returns
    n_train = int(spec["estimation_observations"])
    if len(losses) <= n_train:
        raise ValueError("French snapshot is too short for the configured training window")
    alpha = float(spec["alpha"])
    var, es = empirical_var_es(losses[:n_train], alpha)
    test = losses[n_train:]
    pof = kupiec_pof(int(np.count_nonzero(test > var)), len(test), alpha)
    return {
        "source": meta["source"],
        "snapshot_date": meta["snapshot_date"],
        "sha256": meta["sha256"],
        "sample_start": str(industries.index[0]),
        "sample_end": str(industries.index[-1]),
        "number_of_months": int(len(industries)),
        "number_of_industry_portfolios": int(industries.shape[1]),
        "portfolio_rule": "equal weight across the published industry portfolios each month",
        "horizon": spec["horizon"], "alpha": alpha,
        "estimation_observations": n_train,
        "estimation_start": str(industries.index[0]),
        "estimation_end": str(industries.index[n_train - 1]),
        "test_observations": int(len(test)),
        "test_start": str(industries.index[n_train]),
        "test_end": str(industries.index[-1]),
        "historical_var": _finite_round(var), "historical_es": _finite_round(es),
        "exceedances": int(pof["exceedances"]),
        "expected_exceedance_probability": _finite_round(float(pof["expected_probability"])),
        "kupiec_lr_uc": _finite_round(float(pof["lr_uc"])),
        "kupiec_p_value": float(pof["p_value"]),
        "boundary": meta["limitation"],
    }


def analyze(*, include_french: bool = False) -> tuple[dict[str, object], dict[str, object]]:
    """Compute JSON-ready outputs and the arrays used to render the figures."""
    discrete = _discrete_case()
    comparison, comparison_arrays = _portfolio_comparison()
    stress, stress_arrays = _ledger_stress()
    pof, pof_arrays = _pof_and_rolling(comparison_arrays["losses"])
    exposures = _exposures(INPUTS["ledger_stress"])
    french = _french_real_example() if include_french else {"status": "SKIPPED: permissions unknown; no French data bundled"}
    result = {
        "chapter": 33,
        "title": "Risk Management",
        "units_and_conventions": {
            "currency": "USD for the ledger example",
            "return": "simple decimal return per stated interval",
            "loss": "negative change in portfolio value; positive means loss",
            "position": "shares; price is currency per share; ADV is shares per session",
            "confidence_and_horizon": "always reported together",
        },
        "teaching_inputs": INPUTS,
        "pinned_discrete_case": discrete,
        "same_portfolio_risk_methods": comparison,
        "exposures": exposures,
        "ledger_stress_and_limit": stress,
        "risk_model_backtest": pof,
        "french_real_example": french,
        "artifacts": {"figure_files": list(FIGURES), "figure_count": len(FIGURES)},
    }
    arrays = {"comparison": comparison_arrays, "stress": stress_arrays, "pof": pof_arrays}
    return result, arrays


def generate_figures(results: dict[str, object], arrays: dict[str, object], fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)

    # The empirical quantile function is a step function; the shaded rectangles
    # visualize exactly the fractional tail mass used in the ES calculation.
    d = results["pinned_discrete_case"]
    values = np.asarray(d["loss_values"], dtype=float)
    probs = np.asarray(d["probabilities"], dtype=float)
    edges = np.concatenate(([0.0], np.cumsum(probs)))
    alpha = float(d["alpha"])
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for i, value in enumerate(values):
        left, right = float(edges[i]), float(edges[i + 1])
        ax.hlines(value, left, right, color="#285f87", linewidth=3)
        tail_left = max(left, alpha)
        if right > tail_left:
            ax.fill_between([tail_left, right], [0, 0], [value, value], color="#d77b31", alpha=0.28)
    ax.axvline(alpha, color="#d77b31", linestyle="--", label=f"confidence level α = {alpha:.2f}")
    ax.set_xlabel("Quantile level u (dimensionless)")
    ax.set_ylabel("Loss L (scenario units; positive = loss)")
    ax.set_title("Discrete quantile function and fractional ES tail integral")
    ax.text(0.02, 0.98, f"VaR = {d['var']}; ES = {d['es']}; tail = 1 − α",
            transform=ax.transAxes, va="top", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(fig_dir / FIGURES[0], dpi=180)
    plt.close(fig)

    c = results["same_portfolio_risk_methods"]
    losses = arrays["comparison"]["losses"]
    mc_losses = arrays["comparison"]["mc_losses"]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.hist(losses, bins=70, density=True, color="#9fb9cc", alpha=0.55, label="historical constructed scenarios")
    ax.hist(mc_losses, bins=70, density=True, histtype="step", color="#39825a", linewidth=1.5,
            label="Student-t Monte Carlo")
    lo = float(np.quantile(losses, 0.005))
    hi = float(np.quantile(losses, 0.995))
    grid = np.linspace(lo, hi, 500)
    mu = float(c["historical"]["mean_loss"])
    sigma = float(c["historical"]["std_loss"])
    df = float(c["student_t_degrees_freedom"])
    scale = sigma * math.sqrt((df - 2.0) / df)
    ax.plot(grid, stats.norm.pdf(grid, loc=mu, scale=sigma), color="#252525", linewidth=1.8,
            label="fitted normal density")
    ax.plot(grid, stats.t.pdf((grid - mu) / scale, df) / scale, color="#b44a36", linewidth=1.8,
            label=f"fitted Student-t density (df={df:g})")
    for name, model, color in [
        ("historical", c["historical"], "#285f87"),
        ("normal", c["normal_fitted"], "#252525"),
        ("Student-t", c["student_t_fitted"], "#b44a36"),
        ("Monte Carlo", c["monte_carlo"], "#39825a"),
    ]:
        ax.axvline(float(model["var"]), color=color, linestyle="--", alpha=0.8, label=f"{name} VaR")
    ax.set_xlabel("Portfolio loss (negative monthly simple return; decimal)")
    ax.set_ylabel("Density (per unit of loss)")
    ax.set_title("Historical, parametric and Monte Carlo risk for one portfolio")
    ax.text(0.98, 0.02, f"α = {c['alpha']:.2f}; n = {c['n_historical_scenarios']}",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(fig_dir / FIGURES[1], dpi=180)
    plt.close(fig)

    s = results["ledger_stress_and_limit"]
    by_asset = s["pnl_by_asset_currency"]
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    assets = list(by_asset)
    contributions = [float(by_asset[a]) for a in assets]
    bars = ax.bar(assets, contributions, color=["#285f87" if x >= 0 else "#b44a36" for x in contributions])
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Chapter 29 ledger asset")
    ax.set_ylabel("Scenario PnL (USD; positive = gain, negative = loss)")
    corr = s["correlation_assumptions"]
    ax.set_title("Conditional overnight gap: PnL from specified asset shocks\n"
                 f"Correlation {corr['baseline']:.2f} → {corr['stress']:.2f} is background only; not a probability")
    for bar, value in zip(bars, contributions):
        ax.annotate(f"{value:.2f}", (bar.get_x() + bar.get_width() / 2, value),
                    xytext=(0, 4 if value >= 0 else -13), textcoords="offset points", ha="center", fontsize=9)
    ax.margins(y=0.15)
    ax.grid(True, axis="y", linestyle=":", alpha=0.45)
    fig.tight_layout()
    fig.savefig(fig_dir / FIGURES[2], dpi=180)
    plt.close(fig)

    p = results["risk_model_backtest"]
    test_losses = arrays["pof"]["test_losses"]
    var = float(p["estimation_window"]["var_currency_per_nav"])
    exceed = test_losses > var
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    x = np.arange(len(test_losses))
    ax.plot(x, test_losses, color="#7d98aa", linewidth=0.8, label="test losses")
    ax.scatter(x[exceed], test_losses[exceed], color="#b44a36", s=15, label="VaR exceedances", zorder=3)
    ax.axhline(var, color="#252525", linestyle="--", label="fixed VaR from estimation window")
    ax.set_xlabel("Test-window month index (one observation per month)")
    ax.set_ylabel("Loss (fraction of NAV per month)")
    ax.set_title("Kupiec coverage test with separate estimation and test windows")
    ax.text(0.02, 0.98,
            f"train n = {p['estimation_window']['observations']}; test n = {p['test_window']['observations']}; "
            f"exceptions = {p['test_window']['realized_exceedances']}; p = {p['test_window']['p_value']:.3f}",
            transform=ax.transAxes, va="top", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / FIGURES[3], dpi=180)
    plt.close(fig)


def run(out_dir: Path, fig_dir: Path) -> dict[str, object]:
    out_file = out_dir / "ch33_results.json"
    if out_file.exists():
        raise FileExistsError(f"Refusing to overwrite existing results file: {out_file}")
    for name in FIGURES:
        path = fig_dir / name
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing figure: {path}")
    results, arrays = analyze(include_french=False)
    generate_figures(results, arrays, fig_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results


def main(args_list: list[str] | None = None) -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch33_risk_management_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description="Chapter 33: CONSTRUCTED risk teaching; French skipped")
    parser.add_argument("--out", type=Path, default=default_run / "results")
    parser.add_argument("--figures", type=Path, default=default_run / "figures")
    args = parser.parse_args(args_list)
    try:
        run(args.out, args.figures)
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Wrote {args.out / 'ch33_results.json'} and {len(FIGURES)} figures to {args.figures}")


if __name__ == "__main__":
    main()
