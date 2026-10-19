"""Chapter 18 variance recursions and a deliberately small Gaussian QML fit.

Returns are monthly decimals. Variances are squared monthly decimals.
This module does not produce orders or reconstruct historical availability.
Training fitted variances are ex-post estimates, not real-time forecasts.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from quant_course.time_series import validate_monthly_series


def _real(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real scalar")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive(value: float, name: str) -> float:
    result = _real(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _vector(values: Sequence[float], name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1 or len(array) == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional vector")
    if array.dtype.kind not in "iuf" or np.iscomplexobj(array):
        raise TypeError(f"{name} must contain real numbers, not boolean or text")
    array = array.astype(float)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite, without missing observations")
    return array


@dataclass(frozen=True)
class GARCHParameters:
    omega: float
    alpha: float
    beta: float

    def __post_init__(self) -> None:
        for name in ("omega", "alpha", "beta"):
            object.__setattr__(self, name, _real(getattr(self, name), name))
        if self.omega <= 0 or min(self.alpha, self.beta) < 0:
            raise ValueError("omega must be positive; alpha and beta nonnegative")
        if self.alpha + self.beta >= 1:
            raise ValueError("this finite-second-moment model requires alpha+beta < 1")

    @property
    def persistence(self) -> float:
        return self.alpha + self.beta

    @property
    def unconditional_variance(self) -> float:
        return self.omega / (1 - self.persistence)


@dataclass(frozen=True)
class GARCHFit:
    parameters: GARCHParameters
    mean: float
    training_end: pd.Period
    training_observations: int
    next_variance: float
    objective: float
    converged_starts: int
    fitted_variances: pd.Series


def realized_variance(intraperiod_log_returns: Sequence[float]) -> float:
    """Sum squared intraperiod log returns, without annualizing or demeaning.

    The caller must specify the measured interval and sampling scheme.
    This is not a Bessel-corrected sample variance or the square of a
    single period's net return. No high-frequency consistency is promised.
    """
    returns = _vector(intraperiod_log_returns, "intraperiod_log_returns")
    result = float(returns @ returns)
    if not np.isfinite(result):
        raise ValueError("realized variance overflowed")
    return result


def ewma_variance_path(
    innovations: pd.Series, *, decay: float, initial_variance: float
) -> pd.Series:
    """h[t] uses shocks only BEFORE t; the first h is caller supplied.

    For a real-time claim initial_variance and the mean used to form
    innovations must already be known before the first measured period.
    """
    shocks = validate_monthly_series(innovations)
    lam = _real(decay, "decay")
    if not 0 < lam < 1:
        raise ValueError("decay must lie strictly between zero and one")
    variance = _positive(initial_variance, "initial_variance")
    path = np.empty(len(shocks))
    for t, shock in enumerate(shocks.to_numpy()):
        path[t] = variance
        variance = lam * variance + (1 - lam) * shock**2
    if not np.isfinite(path).all() or (path <= 0).any():
        raise RuntimeError("EWMA variance became invalid")
    return pd.Series(path, index=shocks.index.copy(), name="ewma_variance")


def _garch_path(
    shocks: np.ndarray, parameters: GARCHParameters, initial_variance: float
) -> np.ndarray:
    path = np.empty(len(shocks))
    variance = initial_variance
    for t, shock in enumerate(shocks):
        path[t] = variance
        variance = parameters.omega + parameters.alpha * shock**2 + parameters.beta * variance
    return path


def garch_variance_path(
    innovations: pd.Series, parameters: GARCHParameters, *, initial_variance: float
) -> pd.Series:
    """Return h[t]=omega+alpha*eps[t-1]^2+beta*h[t-1].

    ARCH(1) is obtained with beta=0. Caller-supplied parameters and the
    first variance determine the information boundary.
    """
    if not isinstance(parameters, GARCHParameters):
        raise TypeError("parameters must be GARCHParameters")
    shocks = validate_monthly_series(innovations)
    initial = _positive(initial_variance, "initial_variance")
    path = _garch_path(shocks.to_numpy(), parameters, initial)
    if not np.isfinite(path).all() or (path <= 0).any():
        raise RuntimeError("GARCH variance became invalid")
    return pd.Series(path, index=shocks.index.copy(), name="garch_variance")


def rolling_variance_forecast(returns: pd.Series, *, window: int) -> pd.Series:
    """A next-month proxy from trailing returns, indexed by target month.

    The target row's return is excluded. The first window targets are NaN
    because the required preceding history is not supplied. This estimates
    local historical variance, not a universally valid conditional model.
    """
    series = validate_monthly_series(returns)
    if isinstance(window, bool) or not isinstance(window, int) or window < 2:
        raise ValueError("window must be an integer of at least two months")
    return series.rolling(window, min_periods=window).var(ddof=1).shift(1).rename("rolling_variance")


def fit_garch11(train: pd.Series) -> GARCHFit:
    """Estimate variance parameters on train only with a fixed sample mean.

    Gaussian conditional QML objective, not joint mean/variance MLE.
    Train variance initializes the recursion and scales innovations for
    optimization. Three starts mitigate, but do not rule out, local optima.
    There are no parameter standard errors or global-optimality claims.
    """
    series = validate_monthly_series(train, min_observations=60)
    mean = float(series.mean())
    shocks = series.to_numpy() - mean
    scale_squared = float(np.mean(shocks**2))
    _positive(scale_squared, "training variance")
    normalized = shocks / np.sqrt(scale_squared)

    def objective(values: np.ndarray) -> float:
        omega, alpha, beta = values
        if omega <= 0 or min(alpha, beta) < 0 or alpha + beta >= 1:
            return 1e30
        params = GARCHParameters(omega, alpha, beta)
        path = _garch_path(normalized, params, 1.0)
        if not np.isfinite(path).all() or (path <= 0).any():
            return 1e30
        return float(0.5 * np.mean(np.log(path) + normalized**2 / path))

    candidates = []
    for alpha, beta in ((0.05, 0.90), (0.10, 0.50), (0.20, 0.20)):
        result = minimize(
            objective, np.array([1 - alpha - beta, alpha, beta]),
            method="SLSQP", bounds=((1e-8, 10.0), (0.0, 0.999), (0.0, 0.999)),
            constraints={"type": "ineq", "fun": lambda x: 0.999 - x[1] - x[2]},
            options={"maxiter": 1000, "ftol": 1e-10},
        )
        if result.success and np.isfinite(result.fun) and result.fun < 1e29:
            if result.x[1] >= 0 and result.x[2] >= 0 and result.x[1] + result.x[2] <= 0.999 + 1e-10:
                candidates.append(result)
    if not candidates:
        raise RuntimeError("no GARCH starting point converged to a feasible solution")
    best = min(candidates, key=lambda result: result.fun)
    parameters = GARCHParameters(best.x[0] * scale_squared, best.x[1], best.x[2])
    path = garch_variance_path(series - mean, parameters, initial_variance=scale_squared)
    next_variance = parameters.omega + parameters.alpha * shocks[-1]**2 + parameters.beta * path.iloc[-1]
    return GARCHFit(parameters, mean, series.index[-1], len(series), float(next_variance),
                    float(best.fun), len(candidates), path)


def garch_variance_forecast(fit: GARCHFit, *, steps: int) -> pd.Series:
    """Multi-step expected one-period variances; not variance of a sum."""
    if not isinstance(fit, GARCHFit):
        raise TypeError("fit must be GARCHFit")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")
    level = fit.parameters.unconditional_variance
    horizon = np.arange(steps)
    values = level + fit.parameters.persistence**horizon * (fit.next_variance - level)
    return pd.Series(values, index=pd.period_range(fit.training_end + 1, periods=steps, freq="M"),
                     name="garch_expected_variance")


def qlike_loss(variance_proxy: Sequence[float], variance_forecast: Sequence[float]) -> float:
    """Mean log(h)+proxy/h; omit proxy-only constants (zero proxy allowed).

    Proxy and forecast must have the same units and row order. Equal rows
    do not verify timestamps; align observations before calling this helper.
    A squared shock is a noisy variance proxy, not observed true volatility.
    """
    proxy = _vector(variance_proxy, "variance_proxy")
    forecast = _vector(variance_forecast, "variance_forecast")
    if proxy.shape != forecast.shape or (proxy < 0).any() or (forecast <= 0).any():
        raise ValueError("same-sized nonnegative proxies and positive forecasts are required")
    return float(np.mean(np.log(forecast) + proxy / forecast))


def simulate_garch11(
    parameters: GARCHParameters, *, n: int, seed: int = 20261018,
    mean: float = 0.005, burn: int = 500, start: str = "1980-01"
) -> pd.DataFrame:
    """Seeded Gaussian shocks, true conditional variance retained for teaching."""
    if not isinstance(parameters, GARCHParameters):
        raise TypeError("parameters must be GARCHParameters")
    if isinstance(n, bool) or not isinstance(n, int) or n < 2:
        raise ValueError("n must be an integer of at least two")
    if isinstance(burn, bool) or not isinstance(burn, int) or burn < 0:
        raise ValueError("burn must be a nonnegative integer")
    mu = _real(mean, "mean")
    rng = np.random.default_rng(seed)
    shocks = np.empty(n + burn)
    variances = np.empty(n + burn)
    variance = parameters.unconditional_variance
    for t, z in enumerate(rng.normal(size=n + burn)):
        variances[t] = variance
        shocks[t] = np.sqrt(variance) * z
        variance = parameters.omega + parameters.alpha * shocks[t]**2 + parameters.beta * variance
    if not np.isfinite(shocks).all() or not np.isfinite(variances).all():
        raise RuntimeError("simulation overflowed")
    return pd.DataFrame({"return": mu + shocks[burn:], "innovation": shocks[burn:],
                         "true_variance": variances[burn:]},
                        index=pd.period_range(start, periods=n, freq="M"))
