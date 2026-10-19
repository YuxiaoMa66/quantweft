"""Chapter 9: constructed QP, least-squares, and LP teaching examples."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import cvxpy as cp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.optimization_tools import solve_mean_variance  # noqa: E402


ANNUAL_EXPECTED_RETURNS = np.array([0.05, 0.08], dtype=np.float64)
ANNUAL_COVARIANCE = np.array([[0.04, 0.01], [0.01, 0.09]], dtype=np.float64)
RISK_AVERSION = 1.0


def main() -> None:
    output_dir = ROOT / "runs" / ("ch09_optimization_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    print("CONSTRUCTED teaching inputs only; no market observations or backtest")
    print(
        "Portfolio horizon: one year; expected returns are annual simple-return decimals; "
        "covariance entries are annual return covariance; risk_aversion=1 per decimal-return unit."
    )
    print(f"CVXPY {cp.__version__}; installed solvers={cp.installed_solvers()}")

    mean_variance = solve_mean_variance(
        ANNUAL_EXPECTED_RETURNS,
        ANNUAL_COVARIANCE,
        risk_aversion=RISK_AVERSION,
    )
    minimum_variance = solve_mean_variance(
        np.zeros(2),
        ANNUAL_COVARIANCE,
        risk_aversion=1.0,
    )
    print("\nTwo-asset mean-variance QP")
    print(f"  status={mean_variance.solver_status}; solver={mean_variance.solver_name}")
    print(f"  weights={mean_variance.weights}; objective={mean_variance.objective:.12f}")
    print(
        f"  annual expected return={mean_variance.expected_return:.12f}; "
        f"annual variance={mean_variance.variance:.12f}"
    )
    print(
        "  residuals: budget={:.3g}, nonnegative={:.3g}, stationarity={:.3g}, "
        "complementarity={:.3g}".format(
            mean_variance.budget_residual,
            mean_variance.nonnegativity_violation,
            mean_variance.stationarity_residual,
            mean_variance.complementarity_residual,
        )
    )
    print("  minimum-variance weights with expected_returns=0:", minimum_variance.weights)
    print(f"  minimum annual variance={minimum_variance.variance:.12f}")

    expected_weights = np.array([5 / 11, 6 / 11])
    if not np.allclose(mean_variance.weights, expected_weights, atol=1e-7, rtol=0.0):
        raise AssertionError("mean-variance weights do not match the analytic solution")
    if not np.allclose(minimum_variance.weights, [8 / 11, 3 / 11], atol=1e-7, rtol=0.0):
        raise AssertionError("minimum-variance weights do not match the analytic solution")

    # Least squares: four explicitly constructed observations, with y in an
    # arbitrary teaching-unit scale. The fitted coefficients minimize SSE.
    design = np.column_stack([np.ones(4), np.array([0.0, 1.0, 2.0, 3.0])])
    observed = np.array([1.0, 2.0, 4.0, 5.0])
    numpy_beta, *_ = np.linalg.lstsq(design, observed, rcond=None)
    beta = cp.Variable(2, name="intercept_and_slope")
    least_squares_problem = cp.Problem(
        cp.Minimize(cp.sum_squares(design @ beta - observed))
    )
    least_squares_problem.solve()
    if least_squares_problem.status != cp.OPTIMAL or beta.value is None:
        raise RuntimeError(f"least-squares solver status: {least_squares_problem.status}")
    if not np.allclose(beta.value, numpy_beta, atol=1e-7, rtol=0.0):
        raise AssertionError("CVXPY least squares and NumPy least squares disagree")
    print("\nConstructed ordinary least squares example")
    print(f"  observations y={observed}; predictor x=[0, 1, 2, 3]")
    print(f"  coefficients [intercept, slope]={np.asarray(beta.value)}")
    print(f"  SSE={float(least_squares_problem.value):.12f}; solver={least_squares_problem.solver_stats.solver_name}")

    # Production LP: x and y are lots produced per day; each lot contributes
    # kEUR/lot, so the objective is kEUR/day. Resource constraints are
    # machine-hours/day and labor-hours/day.
    production = cp.Variable(2, nonneg=True, name="lots_per_day")
    machine_hours = 2.0 * production[0] + production[1] <= 100.0
    labor_hours = production[0] + 2.0 * production[1] <= 80.0
    lp_problem = cp.Problem(
        cp.Maximize(np.array([3.0, 2.0]) @ production),
        [machine_hours, labor_hours],
    )
    lp_problem.solve(solver="CLARABEL")
    if lp_problem.status != cp.OPTIMAL or production.value is None:
        raise RuntimeError(f"production LP solver status: {lp_problem.status}")
    if not np.allclose(production.value, [40.0, 20.0], atol=1e-6, rtol=0.0):
        raise AssertionError("production LP did not return the analytic intersection")
    print("\nConstructed production linear program")
    print("  decisions: lots of product A/day and product B/day")
    print("  maximize 3 kEUR/lot-A * lot-A/day + 2 kEUR/lot-B * lot-B/day = kEUR/day")
    print("  limits: 2 machine-hours per A lot, 1 per B lot; capacity 100 machine-hours/day")
    print("          1 labor-hour per A lot, 2 per B lot; capacity 80 labor-hours/day")
    print(f"  production={np.asarray(production.value)} lots/day; contribution={lp_problem.value:.6f} kEUR/day")
    print(f"  status={lp_problem.status}; solver={lp_problem.solver_stats.solver_name}")

    _save_objective_curve(mean_variance.weights, output_dir)


def _save_objective_curve(optimal_weights: np.ndarray, output_dir: Path) -> None:
    first_weight = np.linspace(0.0, 1.0, 501)
    weights = np.column_stack([first_weight, 1.0 - first_weight])
    objective = (
        0.5 * RISK_AVERSION * np.einsum("ni,ij,nj->n", weights, ANNUAL_COVARIANCE, weights)
        - weights @ ANNUAL_EXPECTED_RETURNS
    )
    optimum_x = float(optimal_weights[0])
    optimum_y = float(
        0.5 * RISK_AVERSION * (optimal_weights @ ANNUAL_COVARIANCE @ optimal_weights)
        - ANNUAL_EXPECTED_RETURNS @ optimal_weights
    )

    fig, ax = plt.subplots(figsize=(8.2, 5.0), constrained_layout=True)
    ax.plot(first_weight, objective, color="#235789", linewidth=2.2)
    ax.scatter([optimum_x], [optimum_y], marker="*", s=190, color="#C1292E", zorder=3)
    ax.axvline(optimum_x, color="#C1292E", linestyle="--", linewidth=1.0, alpha=0.75)
    ax.annotate(
        f"QP optimum: w₁={optimum_x:.4f}, w₂={1.0 - optimum_x:.4f}",
        xy=(optimum_x, optimum_y),
        xytext=(optimum_x + 0.08, optimum_y + 0.0015),
        arrowprops={"arrowstyle": "->", "color": "#C1292E"},
        fontsize=9,
    )
    ax.set_title("Two-asset QP objective for a fixed constructed annual model")
    ax.set_xlabel("Weight in asset 1, w₁ (asset 2 weight is 1 − w₁)")
    ax.set_ylabel("Objective: ½ λ wᵀΣw − μᵀw (decimal annual-return scale)")
    ax.grid(alpha=0.22)
    ax.text(
        0.02,
        0.96,
        "Constructed inputs; this curve is model geometry, not market performance.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#4F5D75",
        verticalalignment="top",
    )
    output = output_dir / "ch09_objective_curve.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f"\nSaved objective curve: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
