"""Closed-form single-period mean-variance teaching calculations.

These functions use supplied population moments or explicitly labelled
estimates. They impose only sum(weights)=1: shorts/leverage are possible.
They do not impose trading constraints or establish out-of-sample returns.
Use the Chapter 9 convex optimizer for its long-only utility formulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

import numpy as np


@dataclass(frozen=True)
class PortfolioMoments:
    expected_return: float
    variance: float
    volatility: float


def _array(value: object, name: str) -> np.ndarray:
    raw = np.asarray(value, dtype=object)
    if not all(isinstance(x, Real) and not isinstance(x, (bool, np.bool_)) for x in raw.flat):
        raise TypeError(f"{name} requires real numeric values")
    result = np.asarray(value, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite")
    return result.copy()


def _moments(expected_returns: object, covariance: object, *, positive_definite: bool):
    mu = _array(expected_returns, "expected_returns")
    cov = _array(covariance, "covariance")
    if mu.ndim != 1 or mu.size == 0 or cov.shape != (mu.size, mu.size):
        raise ValueError("require mu shape (n,) and covariance shape (n,n)")
    scale = float(np.max(np.abs(cov)))
    if scale == 0:
        if positive_definite:
            raise ValueError("closed form requires positive definite covariance")
        return mu, cov
    normalized = cov / scale
    if not np.allclose(normalized, normalized.T, rtol=0, atol=1e-12):
        raise ValueError("covariance must be symmetric at its actual scale")
    cov = (cov + cov.T) / 2
    eig = np.linalg.eigvalsh(cov / scale)
    if eig.min() < -1e-12 * np.max(np.abs(eig)):
        raise ValueError("covariance must be positive semidefinite")
    if positive_definite and eig.min() <= 1e-12 * eig.max():
        raise ValueError("closed form requires numerically positive definite covariance")
    return mu, cov


def portfolio_moments(weights: object, expected_returns: object, covariance: object) -> PortfolioMoments:
    """All moments refer to the same holding interval and return units."""
    mu, cov = _moments(expected_returns, covariance, positive_definite=False)
    w = _array(weights, "weights")
    if w.shape != mu.shape:
        raise ValueError("weights must match expected_returns shape")
    if not np.isclose(w.sum(), 1, rtol=0, atol=1e-10):
        raise ValueError("risky-asset weights must sum to one")
    variance = float(w @ cov @ w)
    expected = float(w @ mu)
    if not np.isfinite([variance, expected]).all():
        raise ValueError("portfolio moments overflow; inspect units and leverage")
    # Accepted matrix roundoff can give a tiny negative scalar.
    variance = max(variance, 0.0)
    return PortfolioMoments(expected, variance, float(np.sqrt(variance)))


def global_minimum_variance_weights(covariance: object) -> np.ndarray:
    """Unconstrained fully invested GMV; solve Sigma z=1, then normalize."""
    raw = _array(covariance, "covariance")
    if raw.ndim != 2 or raw.shape[0] == 0:
        raise ValueError("covariance must be a nonempty square matrix")
    _, cov = _moments(np.zeros(raw.shape[0]), raw, positive_definite=True)
    direction = np.linalg.solve(cov / np.max(np.abs(cov)), np.ones(cov.shape[0]))
    return direction / direction.sum()


def minimum_variance_target_weights(
    expected_returns: object, covariance: object, *, target_return: float,
) -> np.ndarray:
    """Minimum variance with exact return target, budget=1, shorts allowed.

    Below the GMV expected return this traces the inefficient lower branch.
    Different expected returns are necessary for the two equality constraints
    to be independent. Use a constrained QP for long-only target feasibility.
    """
    mu, cov = _moments(expected_returns, covariance, positive_definite=True)
    target = _array(target_return, "target_return")
    if target.ndim != 0:
        raise ValueError("target_return must be scalar")
    # Rescale and centre the return constraint, avoiding cancellation in AC-B².
    center = float(mu.mean())
    spread = float(np.max(np.abs(mu - center)))
    if spread == 0:
        raise ValueError("equal asset means do not identify a target-return frontier")
    design = np.column_stack((np.ones(mu.size), (mu - center) / spread))
    solved = np.linalg.solve(cov / np.max(np.abs(cov)), design)
    gram = design.T @ solved
    if np.linalg.cond(gram) >= 1e12:
        raise ValueError("target constraints are numerically degenerate")
    multipliers = np.linalg.solve(gram, [1, (float(target) - center) / spread])
    return solved @ multipliers


def tangency_weights(expected_returns: object, covariance: object, *, risk_free_return: float) -> np.ndarray:
    """Positive-Sharpe risky fund, unlimited shorts, common borrowing/lending RF.

    Uses Sigma^-1(mu-RF*1) by a solve. Its budget normalizer must be positive;
    otherwise this closed-form positive-premium fund is not available under
    the stated normalization. No fallback or bounded-short claim is made.
    """
    mu, cov = _moments(expected_returns, covariance, positive_definite=True)
    rf = _array(risk_free_return, "risk_free_return")
    if rf.ndim != 0:
        raise ValueError("risk_free_return must be scalar")
    direction = np.linalg.solve(cov / np.max(np.abs(cov)), mu - float(rf))
    normalizer = float(direction.sum())
    if normalizer <= 1e-12 * np.linalg.norm(direction, ord=1):
        raise ValueError("no positive normalizer for the stated positive-Sharpe risky fund")
    return direction / normalizer
