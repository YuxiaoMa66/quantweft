"""Practical portfolio-construction calculations for Chapter 21 and Project 3.

All inputs share one return interval and unit (e.g. monthly decimal returns).
Covariances are single-period covariance matrices of those returns. Weights
are fractions of the portfolio's net asset value at the rebalance instant.
Nothing here estimates when data become available; callers must slice a
training window that ends no later than the decision time.

Reused rather than duplicated:
* ``quant_course.portfolio_theory`` for the unconstrained closed forms;
* ``quant_course.optimization_tools.solve_mean_variance`` for long-only
  (optionally capped) minimum variance, by passing zero expected returns.
"""
from __future__ import annotations

from dataclasses import dataclass

import cvxpy as cp
import numpy as np
from numpy.typing import ArrayLike, NDArray

from quant_course.optimization_tools import OptimizationError

FloatArray = NDArray[np.float64]


def _real_array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must contain real numeric values") from exc
    # This also rejects bool, object, text, and complex arrays before a lossy cast.
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numeric values (not bool, text, or complex values)")
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{name} must be representable as float64") from exc
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite")
    return result


def _real_scalar(value: object, name: str) -> float:
    result = _real_array(value, name)
    if result.ndim != 0:
        raise ValueError(f"{name} must be a scalar")
    return float(result)


def _vector(values: ArrayLike, name: str) -> FloatArray:
    result = _real_array(values, name)
    if result.ndim != 1 or result.size == 0:
        raise ValueError(f"{name} must be a nonempty real one-dimensional array")
    return result


def _matrix(values: ArrayLike, name: str) -> FloatArray:
    result = _real_array(values, name)
    if result.ndim != 2 or result.shape[0] == 0 or result.shape[1] == 0:
        raise ValueError(f"{name} must be a nonempty real two-dimensional matrix")
    return result


def _finite_result(values: object, name: str, *, error: type[Exception] = ValueError):
    if not np.isfinite(np.asarray(values, dtype=float)).all():
        raise error(f"{name} contains a non-finite result")


def _covariance(values: ArrayLike, n: int | None = None, *, definite: bool = True) -> FloatArray:
    cov = _matrix(values, "covariance")
    if cov.shape[0] != cov.shape[1]:
        raise ValueError("covariance must be square")
    if n is not None and cov.shape[0] != n:
        raise ValueError("covariance dimension must match the vector length")
    scale = float(np.max(np.abs(cov)))
    if scale == 0:
        raise ValueError("covariance must be nonzero")
    normalized = cov / scale
    if not np.allclose(normalized, normalized.T, rtol=0, atol=1e-12):
        raise ValueError("covariance must be nonzero and symmetric")
    cov = 0.5 * cov + 0.5 * cov.T
    try:
        eig = np.linalg.eigvalsh(cov / scale)
    except np.linalg.LinAlgError as exc:
        raise ValueError("covariance eigenvalue check did not converge") from exc
    if not np.isfinite(eig).all():
        raise ValueError("covariance eigenvalues must be finite")
    spectral_scale = float(np.max(np.abs(eig)))
    if eig.min() < -1e-12 * spectral_scale:
        raise ValueError("covariance must be positive semidefinite")
    if definite and (eig.max() <= 0 or eig.min() <= 1e-12 * eig.max()):
        raise ValueError("this calculation requires a numerically positive definite covariance")
    return cov


# ---------------------------------------------------------------- shrinkage
@dataclass(frozen=True)
class ShrinkageResult:
    covariance: FloatArray        # shrunk estimate, same unit as returns squared
    sample_covariance: FloatArray  # demeaned S = X'X / T (divisor T, not T-1)
    intensity: float               # weight on the scaled-identity target, in [0, 1]
    target_scale: float            # m = trace(S) / p


def ledoit_wolf_identity(returns: ArrayLike) -> ShrinkageResult:
    """Ledoit-Wolf (2004) shrinkage of S towards m*I with estimated intensity.

    ``returns`` is a T x p matrix of one training window (rows = periods).
    Columns are demeaned with the window's own mean. With the Frobenius norm
    divided by p, m = <S, I>, d2 = ||S-mI||^2, bbar2 = T^-2 sum_t
    ||x_t x_t' - S||^2, b2 = min(bbar2, d2), and the estimate is
    (b2/d2) m I + (1 - b2/d2) S. The intensity is estimated from the same
    window; no future period enters. If every return is constant, the centered
    sample covariance is zero and the returned estimate remains singular:
    this estimator cannot invent variation absent from the input.
    """
    x = _matrix(returns, "returns")
    if x.shape[0] < 2:
        raise ValueError("returns must have T >= 2 rows")
    t, p = x.shape
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        x = x - x.mean(axis=0)
        sample = x.T @ x / t
        m = float(np.trace(sample) / p)
        d2 = float(np.sum((sample - m * np.eye(p)) ** 2) / p)
    _finite_result(sample, "sample covariance")
    _finite_result([m, d2], "Ledoit-Wolf intermediate")
    if d2 == 0.0:
        # Constant returns have no estimated variation. The result is zero and
        # singular; shrinkage cannot make it positive definite in this case.
        return ShrinkageResult(sample.copy(), sample, 0.0, m)
    # sum_t ||x_t x_t' - S||^2 = sum_t ||x_t||^4 - T ||S||^2 (cross term = T||S||^2).
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        row_norm_sq = np.sum(x ** 2, axis=1)
        bbar2 = float((np.sum(row_norm_sq ** 2) - t * np.sum(sample ** 2)) / (t ** 2 * p))
    _finite_result([bbar2], "Ledoit-Wolf intensity numerator")
    b2 = min(max(bbar2, 0.0), d2)
    intensity = b2 / d2
    with np.errstate(over="ignore", invalid="ignore"):
        shrunk = intensity * m * np.eye(p) + (1.0 - intensity) * sample
    _finite_result(shrunk, "shrunk covariance")
    return ShrinkageResult(shrunk, sample, float(intensity), m)


# --------------------------------------------------------- risk decomposition
@dataclass(frozen=True)
class RiskDecomposition:
    volatility: float          # sqrt(w' Sigma w), return units per period
    marginal: FloatArray       # d sigma / d w_i = (Sigma w)_i / sigma
    contributions: FloatArray  # w_i * marginal_i; sums to volatility (Euler)
    fractions: FloatArray      # contributions / volatility; sums to one


def risk_contributions(weights: ArrayLike, covariance: ArrayLike) -> RiskDecomposition:
    """Euler decomposition of portfolio volatility; works for any signed weights."""
    w = _vector(weights, "weights")
    cov = _covariance(covariance, w.size, definite=False)
    with np.errstate(over="ignore", invalid="ignore"):
        variance = float(w @ cov @ w)
    if not np.isfinite(variance):
        raise ValueError("portfolio variance is non-finite")
    if variance <= 0:
        raise ValueError("risk contributions are undefined for zero portfolio volatility")
    sigma = np.sqrt(variance)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        marginal = cov @ w / sigma
        contributions = w * marginal
        fractions = contributions / sigma
    _finite_result([sigma], "portfolio volatility")
    _finite_result(marginal, "marginal risk contributions")
    _finite_result(contributions, "risk contributions")
    _finite_result(fractions, "risk contribution fractions")
    return RiskDecomposition(float(sigma), marginal, contributions, fractions)


@dataclass(frozen=True)
class RiskBudgetResult:
    weights: FloatArray
    iterations: int
    max_budget_error: float  # max_i |fraction_i - budget_i|


def risk_budget_weights(
    covariance: ArrayLike,
    budgets: ArrayLike | None = None,
    *,
    tolerance: float = 1e-10,
    max_iterations: int = 200,
) -> RiskBudgetResult:
    """Long-only weights whose volatility fractions equal ``budgets``.

    Newton's method on the strictly convex f(y) = y'Sigma y / 2 - sum b_i ln y_i
    (y > 0). Its first-order condition y_i (Sigma y)_i = b_i makes each risk
    contribution proportional to b_i; normalizing x = y / sum(y) keeps the
    proportions because contributions are homogeneous of degree two in y.
    ``budgets=None`` gives equal risk contribution (ERC). Sigma must be
    positive definite: a zero-variance long-only direction has no minimizer.
    """
    tol = _real_scalar(tolerance, "tolerance")
    if tol <= 0:
        raise ValueError("tolerance must be finite and strictly positive")
    raw_iterations = _real_scalar(max_iterations, "max_iterations")
    if not float(raw_iterations).is_integer() or raw_iterations <= 0:
        raise ValueError("max_iterations must be a positive finite integer")
    max_iterations = int(raw_iterations)
    cov = _covariance(covariance)
    n = cov.shape[0]
    b = np.full(n, 1.0 / n) if budgets is None else _vector(budgets, "budgets")
    if b.size != n or (b <= 0).any():
        raise ValueError("budgets must be positive and match the covariance dimension")
    b_scale = float(np.max(b))
    b = b / b_scale
    b = b / b.sum()
    cov_scale = float(np.max(np.abs(cov)))
    sigma = cov / cov_scale
    sigma_trace = float(np.trace(sigma) / n)
    if not np.isfinite(sigma_trace) or sigma_trace <= 0:
        raise ValueError("covariance must have a positive finite average variance")
    sigma = sigma / sigma_trace  # weights are invariant to scaling Sigma
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        y = 1.0 / np.sqrt(np.diag(sigma))
        y = y / np.sqrt(y @ sigma @ y)
    _finite_result(y, "risk-budget initial point", error=OptimizationError)
    for iteration in range(1, max_iterations + 1):
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            gradient = sigma @ y - b / y
        _finite_result(gradient, "risk-budget gradient", error=OptimizationError)
        if np.max(np.abs(gradient * y)) <= tol:
            break
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            hessian = sigma + np.diag(b / y ** 2)
        _finite_result(hessian, "risk-budget Hessian", error=OptimizationError)
        try:
            step = np.linalg.solve(hessian, -gradient)
        except np.linalg.LinAlgError as exc:
            raise OptimizationError("risk-budget Newton system is singular") from exc
        _finite_result(step, "risk-budget Newton step", error=OptimizationError)
        decrement = float(-(gradient @ step))
        _finite_result([decrement], "Newton decrement", error=OptimizationError)
        if decrement <= 1e-14:
            # Newton decrement lambda^2 = -g'step bounds f - f* by about lambda^2/2
            # (Boyd-Vandenberghe 9.5); smaller decreases are not representable in f.
            break
        objective = float(0.5 * y @ sigma @ y - b @ np.log(y))
        _finite_result([objective], "risk-budget objective", error=OptimizationError)
        size = 1.0
        while True:
            candidate = y + size * step
            if (candidate > 0).all():
                value = float(0.5 * candidate @ sigma @ candidate - b @ np.log(candidate))
                if not np.isfinite(value):
                    size /= 2
                    if size < 1e-16:
                        raise OptimizationError("risk-budget Newton line search failed")
                    continue
                if value <= objective + 1e-4 * size * (gradient @ step):
                    break
            size /= 2
            if size < 1e-16:
                raise OptimizationError("risk-budget Newton line search failed")
        y = candidate
    else:
        raise OptimizationError("risk-budget Newton iteration did not converge")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        weights = y / y.sum()
    _finite_result(weights, "risk-budget weights", error=OptimizationError)
    fractions = risk_contributions(weights, cov).fractions
    error = float(np.max(np.abs(fractions - b)))
    _finite_result([error], "risk-budget error", error=OptimizationError)
    if error > 1e-6:
        raise OptimizationError(f"risk-budget fractions miss budgets by {error:.2e}")
    return RiskBudgetResult(weights, iteration, error)


# ------------------------------------------------------------- max Sharpe
@dataclass(frozen=True)
class MaxSharpeResult:
    weights: FloatArray
    sharpe: float          # per-period (mu - rf)'w / sqrt(w' Sigma w) using the inputs
    solver_status: str


def max_sharpe_long_only(
    expected_returns: ArrayLike,
    covariance: ArrayLike,
    *,
    risk_free_return: float,
    max_weight: float | None = None,
) -> MaxSharpeResult:
    """Long-only fully invested maximum-Sharpe portfolio via a convex QP.

    The ratio objective is not concave. Substituting y = kappa w with
    kappa = 1 / ((mu-rf)'w) > 0 maps each feasible w with positive expected
    excess return to (mu-rf)'y = 1, y >= 0, sum(y) = kappa, y <= cap*kappa,
    and y'Sigma y = 1 / Sharpe(w)^2. Minimizing y'Sigma y is a convex QP; its
    solution divided by kappa maximizes Sharpe. If no asset has a positive
    expected excess return the long-only set contains no positive-Sharpe
    portfolio and OptimizationError is raised (callers log a fallback).
    """
    mu = _vector(expected_returns, "expected_returns")
    cov = _covariance(covariance, mu.size)
    rf = _real_scalar(risk_free_return, "risk_free_return")
    with np.errstate(over="ignore", invalid="ignore"):
        excess = mu - rf
    _finite_result(excess, "expected excess returns")
    if not (excess > 0).any():
        raise OptimizationError("no long-only portfolio has positive expected excess return",
                                solver_status="infeasible_by_inputs")
    cap = None if max_weight is None else _real_scalar(max_weight, "max_weight")
    if cap is not None and not (0 < cap <= 1 and cap * mu.size >= 1):
        raise ValueError("max_weight must lie in (0, 1] and allow a fully invested portfolio")
    if max_weight is not None:
        # Highest excess mean on the capped simplex: fill the best assets up to the cap.
        best, room = 0.0, 1.0
        for value in np.sort(excess)[::-1]:
            take = min(cap, room)
            best, room = best + take * value, room - take
        if best <= 0:
            raise OptimizationError("no capped long-only portfolio has positive expected excess return",
                                    solver_status="infeasible_by_inputs")
    scale = float(np.max(np.abs(excess)))
    sigma = cov / float(np.max(np.abs(cov)))
    y = cp.Variable(mu.size)
    kappa = cp.Variable()
    constraints = [(excess / scale) @ y == 1, y >= 0, cp.sum(y) == kappa]
    if max_weight is not None:
        constraints.append(y <= cap * kappa)
    problem = cp.Problem(cp.Minimize(cp.quad_form(y, cp.psd_wrap(sigma))), constraints)
    try:
        problem.solve(solver=cp.CLARABEL)
    except cp.error.SolverError as exc:
        raise OptimizationError(f"solver failed: {exc}", solver_status="solver_error") from exc
    status = str(problem.status)
    if status != cp.OPTIMAL or y.value is None or kappa.value is None:
        raise OptimizationError(f"max-Sharpe QP status {status!r}", solver_status=status)
    if not np.isfinite(kappa.value) or kappa.value <= 0:
        raise OptimizationError("max-Sharpe QP returned a non-finite or nonpositive scale", solver_status=status)
    y_value = np.asarray(y.value, dtype=float)
    if y_value.shape != (mu.size,) or not np.isfinite(y_value).all():
        raise OptimizationError("max-Sharpe QP returned malformed or non-finite y", solver_status=status)
    weights = np.maximum(y_value, 0.0)
    weights_sum = float(weights.sum())
    if not np.isfinite(weights_sum) or weights_sum <= 0:
        raise OptimizationError("max-Sharpe QP returned invalid total weight", solver_status=status)
    weights = weights / weights_sum
    _finite_result(weights, "max-Sharpe weights", error=OptimizationError)
    if cap is not None and weights.max() > cap + 1e-6:
        raise OptimizationError("max-Sharpe cap residual exceeds tolerance", solver_status=status)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        variance = float(weights @ cov @ weights)
        sharpe = float(excess @ weights / np.sqrt(variance))
    if not np.isfinite(variance) or variance <= 0 or not np.isfinite(sharpe):
        raise OptimizationError("max-Sharpe solution has non-finite return or risk", solver_status=status)
    return MaxSharpeResult(weights, sharpe, status)


# --------------------------------------------------------- Black-Litterman
@dataclass(frozen=True)
class BlackLittermanResult:
    equilibrium_returns: FloatArray  # Pi = delta Sigma w_mkt
    posterior_mean: FloatArray       # mean of the expected-return vector after views
    posterior_mean_covariance: FloatArray  # covariance of that mean, not of returns
    weights: FloatArray              # (delta Sigma)^-1 posterior_mean, unconstrained


def black_litterman(
    covariance: ArrayLike,
    market_weights: ArrayLike,
    *,
    risk_aversion: float,
    tau: float,
    view_matrix: ArrayLike,
    view_returns: ArrayLike,
    view_covariance: ArrayLike,
) -> BlackLittermanResult:
    """He-Litterman (1999) form: prior mu ~ N(Pi, tau Sigma), views P mu = Q + e, e ~ N(0, Omega).

    Uses the algebraically equal update form
    mean = Pi + tau Sigma P'(P tau Sigma P' + Omega)^-1 (Q - P Pi),
    which allows a singular Omega (a view held with certainty) only when the
    middle matrix is nonsingular. Redundant exact views are rejected. Weights
    use Sigma, as in He-Litterman's Appendix B; some implementations add the
    posterior-mean covariance to Sigma. Market weights need not be long-only.
    """
    cov = _covariance(covariance)
    n = cov.shape[0]
    w_mkt = _vector(market_weights, "market_weights")
    if w_mkt.size != n:
        raise ValueError("market_weights must match covariance")
    delta = _real_scalar(risk_aversion, "risk_aversion")
    tau = _real_scalar(tau, "tau")
    if not (delta > 0 and tau > 0):
        raise ValueError("risk_aversion and tau must be finite and positive")
    p_raw = _real_array(view_matrix, "view_matrix")
    q_raw = _real_array(view_returns, "view_returns")
    omega_raw = _real_array(view_covariance, "view_covariance")
    p = p_raw.reshape(1, -1) if p_raw.ndim == 1 else p_raw
    q = q_raw.reshape(1) if q_raw.ndim == 0 else q_raw
    omega = omega_raw.reshape(1, 1) if omega_raw.ndim == 0 else omega_raw
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("view_matrix must have shape (k, n) with k > 0 and n > 0")
    k = p.shape[0]
    if p.shape != (k, n) or q.ndim != 1 or q.shape != (k,) or omega.shape != (k, k):
        raise ValueError("views need P (k x n), Q (k,), Omega (k x k)")
    omega_scale = float(np.max(np.abs(omega)))
    if omega_scale == 0.0:
        omega = omega.copy()
    elif not np.allclose(omega / omega_scale, omega.T / omega_scale, rtol=0, atol=1e-12):
        raise ValueError("Omega must be symmetric positive semidefinite")
    if omega_scale > 0:
        omega = 0.5 * omega + 0.5 * omega.T
        try:
            omega_eig = np.linalg.eigvalsh(omega / omega_scale)
        except np.linalg.LinAlgError as exc:
            raise ValueError("Omega eigenvalue check did not converge") from exc
        eig_scale = float(np.max(np.abs(omega_eig)))
        if not np.isfinite(omega_eig).all() or omega_eig.min() < -1e-12 * eig_scale:
            raise ValueError("Omega must be symmetric positive semidefinite at its actual scale")
    with np.errstate(over="ignore", invalid="ignore"):
        pi = delta * (cov @ w_mkt)
        prior = tau * cov
        middle = p @ prior @ p.T + omega
    _finite_result(pi, "Black-Litterman equilibrium returns")
    _finite_result(prior, "Black-Litterman prior covariance")
    _finite_result(middle, "Black-Litterman view covariance")
    middle = 0.5 * middle + 0.5 * middle.T
    try:
        middle_cond = float(np.linalg.cond(middle))
    except np.linalg.LinAlgError as exc:
        raise ValueError("P tau Sigma P' + Omega is singular; views are redundant") from exc
    if not np.isfinite(middle_cond) or middle_cond > 1e12:
        raise ValueError("P tau Sigma P' + Omega is singular or ill-conditioned; exact views are redundant")
    with np.errstate(over="ignore", invalid="ignore"):
        cross = prior @ p.T
    _finite_result(cross, "Black-Litterman prior/view cross covariance")
    try:
        gain = np.linalg.solve(middle, cross.T).T
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "P tau Sigma P' + Omega must be invertible; repeated exact views are redundant"
        ) from exc
    with np.errstate(over="ignore", invalid="ignore"):
        mean = pi + gain @ (q - p @ pi)
        posterior_cov = prior - gain @ p @ prior
        posterior_cov = 0.5 * posterior_cov + 0.5 * posterior_cov.T
        weights = np.linalg.solve(delta * cov, mean)
    _finite_result(mean, "Black-Litterman posterior mean")
    _finite_result(posterior_cov, "Black-Litterman posterior covariance")
    _finite_result(weights, "Black-Litterman portfolio weights")
    return BlackLittermanResult(pi, mean, posterior_cov, weights)


def he_litterman_view_covariance(view_matrix: ArrayLike, covariance: ArrayLike, *, tau: float) -> FloatArray:
    """Omega = diag(tau p_k' Sigma p_k): the omega/tau = p'Sigma p calibration of He-Litterman."""
    p_raw = _real_array(view_matrix, "view_matrix")
    p = p_raw.reshape(1, -1) if p_raw.ndim == 1 else p_raw
    if p.ndim != 2 or p.shape[0] == 0 or p.shape[1] == 0:
        raise ValueError("view_matrix must have shape (k, n) with k > 0 and n > 0")
    cov = _covariance(covariance, p.shape[1], definite=False)
    tau_value = _real_scalar(tau, "tau")
    if tau_value <= 0:
        raise ValueError("tau must be finite and strictly positive")
    with np.errstate(over="ignore", invalid="ignore"):
        variances = tau_value * np.einsum("ij,jk,ik->i", p, cov, p)
    _finite_result(variances, "view variances")
    if (variances < -1e-12 * max(float(np.max(np.abs(variances))), 1e-300)).any():
        raise ValueError("view variances must be nonnegative")
    return np.diag(np.maximum(variances, 0.0))


# ------------------------------------------------------------------ Kelly
def kelly_binary_fraction(win_probability: float, net_odds: float) -> float:
    """Growth-optimal stake f* = p - (1-p)/b for a bet paying b per unit staked or losing the stake.

    Returns 0 when the bet has nonpositive edge (no bet). Kelly (1956) treats
    the even-odds case b = 1, where f* = 2p - 1.
    """
    p = _real_scalar(win_probability, "win_probability")
    b = _real_scalar(net_odds, "net_odds")
    if not (0 < p < 1 and b > 0):
        raise ValueError("need finite 0 < win_probability < 1 and positive net_odds")
    result = max(p - (1 - p) / b, 0.0)
    _finite_result([result], "binary Kelly fraction")
    return result


def binary_log_growth(fraction: float, win_probability: float, net_odds: float) -> float:
    """Expected log growth per bet, p ln(1 + b f) + (1-p) ln(1 - f), for 0 <= f < 1."""
    f = _real_scalar(fraction, "fraction")
    p = _real_scalar(win_probability, "win_probability")
    b = _real_scalar(net_odds, "net_odds")
    if not 0 <= f < 1:
        raise ValueError("fraction must lie in [0, 1); f = 1 risks total loss")
    if not (0 < p < 1 and b > 0):
        raise ValueError("need finite 0 < win_probability < 1 and positive net_odds")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        result = float(p * np.log1p(b * f) + (1 - p) * np.log1p(-f))
    _finite_result([result], "binary expected log growth")
    return result


def gaussian_kelly_weights(excess_returns: ArrayLike, covariance: ArrayLike, *, fraction: float = 1.0) -> FloatArray:
    """c * Sigma^-1 (mu - rf): maximizer of the quadratic log-growth approximation.

    Weights are on risky assets; 1 - sum(weights) sits in the risk-free asset
    (negative means borrowing). The approximation g = rf + w'm - w'Sigma w / 2
    assumes small per-period returns and known moments; it ignores
    estimation error, fat tails, margin calls and financing limits.
    """
    m = _vector(excess_returns, "excess_returns")
    cov = _covariance(covariance, m.size)
    c = _real_scalar(fraction, "fraction")
    if not 0 < c <= 1:
        raise ValueError("fraction must lie in (0, 1]")
    with np.errstate(over="ignore", invalid="ignore"):
        weights = c * np.linalg.solve(cov, m)
    _finite_result(weights, "Gaussian Kelly weights")
    return weights


def quadratic_log_growth(weights: ArrayLike, excess_returns: ArrayLike, covariance: ArrayLike,
                         *, risk_free_return: float = 0.0) -> float:
    w = _vector(weights, "weights")
    m = _vector(excess_returns, "excess_returns")
    cov = _covariance(covariance, w.size, definite=False)
    rf = _real_scalar(risk_free_return, "risk_free_return")
    with np.errstate(over="ignore", invalid="ignore"):
        result = float(rf + w @ m - 0.5 * w @ cov @ w)
    _finite_result([result], "quadratic log-growth approximation")
    return result


# ------------------------------------------------- exposures and neutrality
@dataclass(frozen=True)
class ExposureReport:
    net: float               # sum w: dollar (capital) exposure
    gross: float             # sum |w|
    beta: float              # beta' w
    sector_net: dict[str, float]


def exposure_report(weights: ArrayLike, betas: ArrayLike, sectors: list[str]) -> ExposureReport:
    w = _vector(weights, "weights")
    beta = _vector(betas, "betas")
    if beta.size != w.size or len(sectors) != w.size:
        raise ValueError("betas and sectors must match weights")
    if any(not isinstance(sector, str) for sector in sectors):
        raise TypeError("sector labels must be strings")
    names = sorted(set(sectors))
    with np.errstate(over="ignore", invalid="ignore"):
        sector_net = {s: float(sum(wi for wi, si in zip(w, sectors) if si == s)) for s in names}
        net = float(w.sum())
        gross = float(np.abs(w).sum())
        beta_exposure = float(beta @ w)
    _finite_result([net, gross, beta_exposure, *sector_net.values()], "portfolio exposures")
    return ExposureReport(net, gross, beta_exposure, sector_net)


def project_to_constraints(weights: ArrayLike, constraint_matrix: ArrayLike,
                           targets: ArrayLike | None = None) -> FloatArray:
    """Closest weights in Euclidean norm satisfying A w = targets (default 0).

    Closed form w - A'(A A')^-1 (A w - targets) from the Lagrangian of
    min ||v - w||^2 s.t. A v = targets. Rows of A are exposures: a row of
    ones (dollar), betas (beta) or a sector indicator (sector). Requires
    linearly independent rows. Minimizes weight distance, not risk or cost.
    """
    w = _vector(weights, "weights")
    a_raw = _real_array(constraint_matrix, "constraint_matrix")
    a = a_raw.reshape(1, -1) if a_raw.ndim == 1 else a_raw
    if a.ndim != 2 or a.shape[0] == 0 or a.shape[1] == 0:
        raise ValueError("constraint_matrix must have shape (m, n) with m > 0 and n > 0")
    if a.shape[1] != w.size:
        raise ValueError("constraint columns must match weights")
    if targets is None:
        b = np.zeros(a.shape[0])
    else:
        b_raw = _real_array(targets, "targets")
        b = b_raw.reshape(1) if b_raw.ndim == 0 else b_raw
        if b.ndim != 1 or b.shape != (a.shape[0],):
            raise ValueError("targets must be a finite vector with one value per constraint row")
    if np.linalg.matrix_rank(a) < a.shape[0]:
        raise ValueError("constraint rows are linearly dependent")
    with np.errstate(over="ignore", invalid="ignore"):
        gram = a @ a.T
        projected = w - a.T @ np.linalg.solve(gram, a @ w - b)
    _finite_result(projected, "projected weights")
    return projected


# ------------------------------------------------------- drift and turnover
def drift_weights(weights: ArrayLike, asset_returns: ArrayLike) -> FloatArray:
    """End-of-interval weights of a fully invested buy-and-hold portfolio.

    w_i (1 + r_i) / (1 + w'r): weights at the start of the interval, simple
    returns over the same interval. Requires sum(w) = 1 and 1 + w'r > 0.
    """
    w = _vector(weights, "weights")
    r = _vector(asset_returns, "asset_returns")
    total_weight = float(w.sum())
    if not np.isfinite(total_weight) or r.size != w.size or not np.isclose(total_weight, 1.0, atol=1e-10, rtol=0):
        raise ValueError("need matching vectors and fully invested weights")
    if (r < -1.0).any():
        raise ValueError("simple asset returns cannot be below -100%")
    with np.errstate(over="ignore", invalid="ignore"):
        growth = float(1.0 + w @ r)
    if not np.isfinite(growth) or growth <= 0:
        raise ValueError("portfolio value is nonpositive; weights are undefined")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        result = w * (1.0 + r) / growth
    _finite_result(result, "drifted weights")
    return result


def turnover(pre_trade_weights: ArrayLike, target_weights: ArrayLike) -> float:
    """Traded fraction of NAV, buys plus sells: sum_i |target_i - pre_i| (not halved).

    A cost rate c per unit of value traded, on either side, costs c * turnover.
    """
    pre = _vector(pre_trade_weights, "pre_trade_weights")
    target = _vector(target_weights, "target_weights")
    if pre.size != target.size:
        raise ValueError("weight vectors must match")
    with np.errstate(over="ignore", invalid="ignore"):
        result = float(np.abs(target - pre).sum())
    _finite_result([result], "turnover")
    return result
