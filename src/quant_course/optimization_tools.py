"""Validated convex optimization helpers for the A2 portfolio chapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cvxpy as cp
import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


class OptimizationError(RuntimeError):
    """Raised when a modeled problem is not solved to an acceptable status."""

    def __init__(self, message: str, *, solver_status: str | None = None) -> None:
        super().__init__(message)
        self.solver_status = solver_status


@dataclass(frozen=True)
class MeanVarianceResult:
    """A mean-variance solution and independently recomputed diagnostics."""

    weights: FloatArray
    expected_return: float
    variance: float
    objective: float
    solver_status: str
    solver_name: str
    budget_residual: float
    nonnegativity_violation: float
    max_weight_violation: float
    stationarity_residual: float
    complementarity_residual: float
    budget_dual: float
    lower_bound_duals: FloatArray
    upper_bound_duals: FloatArray


def _real_vector(values: ArrayLike, *, name: str) -> FloatArray:
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a numeric one-dimensional array") from exc
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numeric values")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must contain real, not complex, values")
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{name} must convert to float64") from exc
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain only finite values")
    return result


def _real_matrix(values: ArrayLike, *, name: str) -> FloatArray:
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a numeric two-dimensional matrix") from exc
    if raw.ndim != 2 or raw.shape[0] == 0 or raw.shape[1] == 0:
        raise ValueError(f"{name} must be a non-empty two-dimensional matrix")
    if raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numeric values")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must contain real, not complex, values")
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{name} must convert to float64") from exc
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain only finite values")
    return result


def _positive_scalar(value: float, *, name: str) -> float:
    raw = np.asarray(value)
    if raw.ndim != 0 or raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must be a real numeric scalar")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must be a real numeric scalar")
    result = float(raw)
    if not np.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return result


def solve_mean_variance(
    expected_returns: ArrayLike,
    covariance: ArrayLike,
    risk_aversion: float = 1.0,
    *,
    max_weight: float | None = None,
    solver: str | None = None,
    feasibility_tolerance: float = 1e-6,
) -> MeanVarianceResult:
    """Solve a long-only, fully invested mean-variance quadratic program.

    The optimization objective is

    ``0.5 * risk_aversion * w.T @ covariance @ w - expected_returns @ w``.

    ``expected_returns`` and ``covariance`` must use the same horizon and
    return scale. ``risk_aversion`` is strictly positive. ``max_weight``, if
    supplied, caps every asset weight at the same value. A solver must report
    ``optimal`` and the independently recomputed primal residuals must satisfy
    ``feasibility_tolerance``; otherwise an :class:`OptimizationError` is
    raised. Covariance eigenvalues that are negative only within the stated
    relative PSD tolerance (1e-10 times its spectral scale, with no absolute
    floor) are clipped to zero before modeling. Dual
    multipliers are returned for KKT inspection.
    """
    mu = _real_vector(expected_returns, name="expected_returns")
    sigma = _real_matrix(covariance, name="covariance")
    risk = _positive_scalar(risk_aversion, name="risk_aversion")
    tolerance = _positive_scalar(feasibility_tolerance, name="feasibility_tolerance")
    n_assets = mu.size
    if sigma.shape != (n_assets, n_assets):
        raise ValueError(
            "covariance must have shape (n_assets, n_assets) matching expected_returns"
        )
    matrix_scale = float(np.max(np.abs(sigma)))
    if float(np.max(np.abs(sigma - sigma.T))) > 1e-10 * matrix_scale:
        raise ValueError("covariance must be symmetric relative to its matrix scale")
    sigma = 0.5 * (sigma + sigma.T)
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(sigma)
        minimum_eigenvalue = float(eigenvalues.min())
    except np.linalg.LinAlgError as exc:
        raise ValueError("covariance eigenvalue check did not converge") from exc
    if not np.isfinite(eigenvalues).all():
        raise ValueError("covariance eigenvalues must be finite")
    covariance_scale = float(np.max(np.abs(eigenvalues)))
    psd_tolerance = 1e-10 * covariance_scale
    if minimum_eigenvalue < -psd_tolerance:
        raise ValueError(
            "covariance must be positive semidefinite; "
            f"minimum eigenvalue is {minimum_eigenvalue:.6g}"
        )
    if minimum_eigenvalue < 0.0:
        # Remove roundoff-scale negative curvature so psd_wrap marks a matrix
        # that is actually PSD rather than merely close to one.
        sigma = (eigenvectors * np.maximum(eigenvalues, 0.0)) @ eigenvectors.T
        sigma = 0.5 * (sigma + sigma.T)

    cap: float | None = None
    if max_weight is not None:
        raw_cap = np.asarray(max_weight)
        if (
            raw_cap.ndim != 0
            or raw_cap.dtype == np.bool_
            or not np.issubdtype(raw_cap.dtype, np.number)
            or np.issubdtype(raw_cap.dtype, np.complexfloating)
        ):
            raise TypeError("max_weight must be a real numeric scalar")
        cap = float(raw_cap)
        if not np.isfinite(cap) or cap <= 0.0 or cap > 1.0:
            raise ValueError("max_weight must be finite and in (0, 1]")

    if solver is not None and (not isinstance(solver, str) or not solver.strip()):
        raise TypeError("solver must be a non-empty string or None")
    chosen_solver = solver.strip().upper() if solver is not None else None
    if chosen_solver is not None and chosen_solver not in cp.installed_solvers():
        raise OptimizationError(
            f"requested solver {chosen_solver!r} is not installed; "
            f"available solvers are {cp.installed_solvers()}"
        )

    weights_var = cp.Variable(n_assets, name="portfolio_weights")
    budget_constraint = cp.sum(weights_var) == 1.0
    long_only_constraint = weights_var >= 0.0
    constraints: list[Any] = [budget_constraint, long_only_constraint]
    cap_constraint = None
    if cap is not None:
        cap_constraint = weights_var <= cap
        constraints.append(cap_constraint)

    # psd_wrap is safe here because symmetry and positive semidefiniteness have
    # already been checked numerically above. It avoids a second, independent
    # symbolic eigenvalue test in CVXPY.
    objective_expression = (
        0.5 * risk * cp.quad_form(weights_var, cp.psd_wrap(sigma)) - mu @ weights_var
    )
    problem = cp.Problem(cp.Minimize(objective_expression), constraints)
    if not problem.is_dcp():
        raise OptimizationError("mean-variance formulation is not disciplined convex")
    try:
        problem.solve(solver=chosen_solver)
    except cp.error.SolverError as exc:
        raise OptimizationError(f"solver failed: {exc}") from exc

    status = str(problem.status)
    if status != cp.OPTIMAL:
        raise OptimizationError(
            f"solver returned status {status!r}; only 'optimal' is accepted",
            solver_status=status,
        )
    if weights_var.value is None:
        raise OptimizationError("solver reported optimal but returned no weights", solver_status=status)
    weights = np.asarray(weights_var.value, dtype=np.float64).reshape(-1)
    if weights.shape != (n_assets,) or not np.isfinite(weights).all():
        raise OptimizationError("solver returned malformed or non-finite weights", solver_status=status)

    budget_residual = abs(float(weights.sum()) - 1.0)
    nonnegativity_violation = max(0.0, -float(weights.min()))
    max_weight_violation = 0.0 if cap is None else max(0.0, float(weights.max()) - cap)
    if max(budget_residual, nonnegativity_violation, max_weight_violation) > tolerance:
        raise OptimizationError(
            "solver reported optimal but primal constraint residual exceeds tolerance",
            solver_status=status,
        )

    if long_only_constraint.dual_value is None or budget_constraint.dual_value is None:
        raise OptimizationError("solver returned optimal without required dual values", solver_status=status)
    lower_duals = np.asarray(long_only_constraint.dual_value, dtype=np.float64).reshape(-1)
    if cap_constraint is None:
        upper_duals = np.zeros(n_assets, dtype=np.float64)
    else:
        if cap_constraint.dual_value is None:
            raise OptimizationError("solver returned optimal without cap dual values", solver_status=status)
        upper_duals = np.asarray(cap_constraint.dual_value, dtype=np.float64).reshape(-1)
    equality_dual = float(np.asarray(budget_constraint.dual_value, dtype=np.float64))
    if (
        lower_duals.shape != (n_assets,)
        or upper_duals.shape != (n_assets,)
        or not np.isfinite(lower_duals).all()
        or not np.isfinite(upper_duals).all()
        or not np.isfinite(equality_dual)
    ):
        raise OptimizationError("solver returned malformed or non-finite dual values", solver_status=status)
    gradient = risk * sigma @ weights - mu
    stationarity = gradient + equality_dual - lower_duals + upper_duals
    lower_complementarity = weights * lower_duals
    if cap is None:
        upper_complementarity = np.zeros(n_assets, dtype=np.float64)
    else:
        upper_complementarity = (cap - weights) * upper_duals
    complementarity_residual = max(
        float(np.max(np.abs(lower_complementarity))),
        float(np.max(np.abs(upper_complementarity))),
    )
    stationarity_residual = float(np.linalg.norm(stationarity, ord=np.inf))
    if not np.isfinite([stationarity_residual, complementarity_residual]).all():
        raise OptimizationError("recomputed KKT residuals are non-finite", solver_status=status)

    expected_return = float(mu @ weights)
    variance = float(weights @ sigma @ weights)
    objective_value = float(0.5 * risk * variance - expected_return)
    if not np.isfinite([expected_return, variance, objective_value]).all():
        raise OptimizationError("recomputed solution metrics are non-finite", solver_status=status)
    solver_stats = problem.solver_stats
    solver_name = str(solver_stats.solver_name) if solver_stats is not None else "unknown"
    return MeanVarianceResult(
        weights=weights.copy(),
        expected_return=expected_return,
        variance=variance,
        objective=objective_value,
        solver_status=status,
        solver_name=solver_name,
        budget_residual=budget_residual,
        nonnegativity_violation=nonnegativity_violation,
        max_weight_violation=max_weight_violation,
        stationarity_residual=stationarity_residual,
        complementarity_residual=complementarity_residual,
        budget_dual=equality_dual,
        lower_bound_duals=lower_duals.copy(),
        upper_bound_duals=upper_duals.copy(),
    )
