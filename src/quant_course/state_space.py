"""Teaching Kalman filter with one scalar observation per time step.

State convention: x_t = F x_(t-1) + eta_t, y_t = H_t x_t + epsilon_t.
Q is state-noise covariance, R is scalar observation-noise variance.
Inputs/parameters must already be available at the relevant observation time.
No parameter estimation, smoothing, execution or future-return prediction is
implied. A Gaussian initial state, temporally independent Gaussian process
and observation noises, mutual independence of both noises and independence
from the initial state give a conditional Gaussian posterior. The supplied
design must be known/exogenous for this observation model; correlated or
endogenous designs can invalidate the conditioning assumptions.
without those assumptions these arrays do not establish that posterior law.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

import numpy as np
import pandas as pd

from quant_course.time_series import validate_monthly_series


@dataclass(frozen=True)
class KalmanResult:
    """Row t's prior precedes observing y_t; filtered state includes y_t."""

    predicted_states: np.ndarray
    predicted_covariances: np.ndarray
    innovations: np.ndarray
    innovation_variances: np.ndarray
    gains: np.ndarray
    filtered_states: np.ndarray
    filtered_covariances: np.ndarray


def _real_array(values: object, name: str) -> np.ndarray:
    raw = np.asarray(values, dtype=object)
    if not all(isinstance(x, Real) and not isinstance(x, (bool, np.bool_))
               for x in raw.flat):
        raise TypeError(f"{name} must contain real numbers, not bool/text/complex")
    array = np.asarray(values, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite; missing observations are rejected")
    return array.copy()


def _psd(values: object, dimension: int, name: str) -> np.ndarray:
    matrix = _real_array(values, name)
    if matrix.shape != (dimension, dimension):
        raise ValueError(f"{name} must have shape ({dimension}, {dimension})")
    scale = float(np.max(np.abs(matrix)))
    if scale == 0:
        return matrix
    # Relative to the actual covariance scale, never a unit-size floor.
    normalized = matrix / scale
    if not np.allclose(normalized, normalized.T, rtol=0, atol=1e-12):
        raise ValueError(f"{name} must be symmetric")
    eigenvalues, eigenvectors = np.linalg.eigh((normalized + normalized.T) / 2)
    if eigenvalues.min() < -1e-12:
        raise ValueError(f"{name} must be positive semidefinite")
    # Clip only accepted relative roundoff, not material negative variance.
    return ((eigenvectors * np.maximum(eigenvalues, 0)) @ eigenvectors.T) * scale


def kalman_filter(
    observations: object,
    observation_design: object,
    *,
    initial_state: object,
    initial_covariance: object,
    transition: object,
    process_covariance: object,
    observation_variance: float,
) -> KalmanResult:
    """Filter a complete sequence, predicting before every observation.

    initial_state/P describe x_(-1), before the first transition. Shapes:
    observations (T,), design (T,d), state (d,), F/Q/P (d,d).
    All observations are mandatory: missing data cannot compress the clock.
    F/Q/R and initial_state/P are supplied parameters; fitting any of these
    on future rows leaks, even though the recursion itself is causal.
    K can exceed one because observation and state units may differ.
    """
    y = _real_array(observations, "observations")
    h = _real_array(observation_design, "observation_design")
    state = _real_array(initial_state, "initial_state")
    if y.ndim != 1 or y.size == 0:
        raise ValueError("observations must be a nonempty vector")
    if state.ndim != 1 or state.size == 0:
        raise ValueError("initial_state must be a nonempty vector")
    d, t_count = state.size, y.size
    if h.shape != (t_count, d):
        raise ValueError("observation_design must have shape (T,d)")
    f = _real_array(transition, "transition")
    if f.shape != (d, d):
        raise ValueError("transition must have shape (d,d)")
    covariance = _psd(initial_covariance, d, "initial_covariance")
    q = _psd(process_covariance, d, "process_covariance")
    if (not isinstance(observation_variance, Real)
        or isinstance(observation_variance, (bool, np.bool_))):
        raise TypeError("observation_variance must be a real scalar")
    r = float(observation_variance)
    if not np.isfinite(r) or r <= 0:
        raise ValueError("observation_variance must be finite and positive")
    predicted = np.empty((t_count, d))
    filtered = np.empty_like(predicted)
    predicted_p = np.empty((t_count, d, d))
    filtered_p = np.empty_like(predicted_p)
    innovations = np.empty(t_count)
    s_values = np.empty(t_count)
    gains = np.empty_like(predicted)
    identity = np.eye(d)
    for t in range(t_count):
        prior_state = f @ state
        prior_p = f @ covariance @ f.T + q
        prior_p = (prior_p + prior_p.T) / 2
        innovation = float(y[t] - h[t] @ prior_state)
        s = float(h[t] @ prior_p @ h[t] + r)
        if not np.isfinite(s) or s <= 0:
            raise ValueError("invalid innovation variance")
        # Scalar solve is division; never invert a covariance matrix.
        gain = prior_p @ h[t] / s
        state = prior_state + gain * innovation
        residual_map = identity - np.outer(gain, h[t])
        covariance = residual_map @ prior_p @ residual_map.T + r * np.outer(gain, gain)
        covariance = (covariance + covariance.T) / 2  # Joseph form
        if not np.isfinite(state).all() or not np.isfinite(covariance).all():
            raise ValueError("filter overflow: rescale inputs or inspect parameters")
        predicted[t], predicted_p[t] = prior_state, prior_p
        filtered[t], filtered_p[t] = state, covariance
        innovations[t], s_values[t], gains[t] = innovation, s, gain
    return KalmanResult(predicted, predicted_p, innovations, s_values, gains,
                        filtered, filtered_p)


def dynamic_beta_filter(
    asset_excess_returns: pd.Series,
    market_excess_returns: pd.Series,
    *,
    initial_beta: float,
    initial_variance: float,
    process_variance: float,
    observation_variance: float,
) -> pd.DataFrame:
    """Random-walk beta, zero alpha, monthly decimal excess returns.

    The row's market return is realized contemporaneously. predicted_beta is
    based on earlier observations; its contemporaneous fitted return requires
    the current market input, so it is not an ex-ante next-month forecast.
    filtered_beta is available only after BOTH month's returns are known.
    RF is not subtracted here: the caller supplies excess returns exactly once.
    """
    asset = validate_monthly_series(asset_excess_returns, min_observations=1)
    market = validate_monthly_series(market_excess_returns, min_observations=1)
    if not asset.index.equals(market.index):
        raise ValueError("asset and market months must match exactly")
    result = kalman_filter(
        asset.to_numpy(), market.to_numpy()[:, None],
        initial_state=[initial_beta], initial_covariance=[[initial_variance]],
        transition=[[1.0]], process_covariance=[[process_variance]],
        observation_variance=observation_variance,
    )
    return pd.DataFrame({
        "predicted_beta": result.predicted_states[:, 0],
        "filtered_beta": result.filtered_states[:, 0],
        "predicted_beta_variance": result.predicted_covariances[:, 0, 0],
        "filtered_beta_variance": result.filtered_covariances[:, 0, 0],
        "innovation": result.innovations,
        "innovation_variance": result.innovation_variances,
        "kalman_gain": result.gains[:, 0],
    }, index=asset.index)
