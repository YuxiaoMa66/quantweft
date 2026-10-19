"""Small risk calculations used by Chapter 33.

Losses are positive when value is lost. Returns passed to ``scenario_pnl`` are
simple returns over one explicitly chosen holding interval.
"""
from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import stats

FloatArray = NDArray[np.float64]


def _vector(values: ArrayLike, name: str) -> FloatArray:
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0 or raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must be a nonempty one-dimensional real vector")
    out = raw.astype(np.float64, copy=True)
    if not np.isfinite(out).all():
        raise ValueError(f"{name} must contain only finite values")
    return out


def _scalar(value: object, name: str) -> float:
    raw = np.asarray(value)
    if raw.ndim != 0 or raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must be a real scalar")
    out = float(raw)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def _alpha(value: float) -> float:
    alpha = _scalar(value, "alpha")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")
    return alpha


def empirical_var_es(losses: ArrayLike, alpha: float) -> tuple[float, float]:
    """Lower empirical quantile and ES with fractional mass at the VaR point.

    Scenarios are equally weighted. The quantile is the smallest observation
    whose empirical CDF is at least ``alpha``.
    """
    x = np.sort(_vector(losses, "losses"))
    a = _alpha(alpha)
    # Compare the empirical CDF directly: alpha*n can round above an integer.
    index = int(np.searchsorted(np.arange(1, x.size + 1) / x.size, a, side="left"))
    var = float(x[index])
    below_or_at = float(np.count_nonzero(x <= var) / x.size)
    strictly_above = x[x > var]
    tail_numerator = float(strictly_above.sum() / x.size + var * (below_or_at - a))
    es = tail_numerator / (1.0 - a)
    if not math.isfinite(es):
        raise ValueError("empirical ES is not finite")
    return var, float(es)


def normal_var_es(mean_loss: float, std_loss: float, alpha: float) -> tuple[float, float]:
    """Normal-model VaR and ES for positive-is-loss observations."""
    mu, sigma, a = _scalar(mean_loss, "mean_loss"), _scalar(std_loss, "std_loss"), _alpha(alpha)
    if sigma <= 0:
        raise ValueError("std_loss must be positive")
    z = float(stats.norm.ppf(a))
    var = mu + sigma * z
    es = mu + sigma * float(stats.norm.pdf(z)) / (1.0 - a)
    if not math.isfinite(var) or not math.isfinite(es):
        raise ValueError("normal VaR and ES must be finite")
    return float(var), float(es)


def student_t_var_es(
    mean_loss: float, std_loss: float, degrees_freedom: float, alpha: float,
) -> tuple[float, float]:
    """Student-t VaR and ES, parameterized by loss mean and standard deviation.

    Degrees of freedom must exceed two so that the stated standard deviation
    exists. The Student-t scale is adjusted to keep that standard deviation
    fixed when comparing tail shape with a normal model.
    """
    mu = _scalar(mean_loss, "mean_loss")
    sigma = _scalar(std_loss, "std_loss")
    df = _scalar(degrees_freedom, "degrees_freedom")
    a = _alpha(alpha)
    if sigma <= 0 or df <= 2:
        raise ValueError("std_loss must be positive and degrees_freedom must exceed 2")
    scale = sigma * math.sqrt((df - 2.0) / df)
    q = float(stats.t.ppf(a, df))
    var = mu + scale * q
    # E[T | T > q] = ((df + q^2)/(df - 1)) f_df(q) / (1 - alpha).
    conditional_tail_mean = (
        (df + q * q) / (df - 1.0) * float(stats.t.pdf(q, df)) / (1.0 - a)
    )
    es = mu + scale * conditional_tail_mean
    if not math.isfinite(var) or not math.isfinite(es):
        raise ValueError("Student-t VaR and ES must be finite")
    return float(var), float(es)


def simulate_student_t_losses(
    mean_loss: float, std_loss: float, degrees_freedom: float, n_obs: int, seed: int,
) -> FloatArray:
    """Draw reproducible Student-t losses with the requested mean and standard deviation."""
    mu = _scalar(mean_loss, "mean_loss")
    sigma = _scalar(std_loss, "std_loss")
    df = _scalar(degrees_freedom, "degrees_freedom")
    if isinstance(n_obs, (bool, np.bool_)) or not isinstance(n_obs, (int, np.integer)) or n_obs < 1:
        raise ValueError("n_obs must be a positive integer")
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer")
    if sigma <= 0 or df <= 2:
        raise ValueError("std_loss must be positive and degrees_freedom must exceed 2")
    rng = np.random.default_rng(int(seed))
    draws = rng.standard_t(df, size=int(n_obs)) * sigma * math.sqrt((df - 2.0) / df) + mu
    if not np.isfinite(draws).all():
        raise ValueError("simulated losses are not finite")
    return draws.astype(np.float64, copy=False)


def scenario_pnl(quantities: ArrayLike, prices: ArrayLike, simple_returns: ArrayLike) -> FloatArray:
    """Revalue positions item by item for one simple-return scenario; return currency PnL."""
    q = _vector(quantities, "quantities")
    p = _vector(prices, "prices")
    r = _vector(simple_returns, "simple_returns")
    if q.size != p.size or q.size != r.size:
        raise ValueError("quantities, prices and simple_returns must have equal lengths")
    if (p <= 0).any() or (r < -1.0).any():
        raise ValueError("prices must be positive and simple returns cannot be below -100%")
    with np.errstate(over="ignore", invalid="ignore"):
        pnl = q * p * r
    if not np.isfinite(pnl).all():
        raise ValueError("scenario PnL is not finite")
    return pnl


def lagged_rolling_var(losses: ArrayLike, window: int, alpha: float) -> FloatArray:
    """Forecast each loss from the immediately preceding ``window`` observations.

    The returned value at position zero corresponds to input position
    ``window``; the current observation is never included in its own forecast.
    """
    x = _vector(losses, "losses")
    a = _alpha(alpha)
    if isinstance(window, (bool, np.bool_)) or not isinstance(window, (int, np.integer)) or window < 1:
        raise ValueError("window must be a positive integer")
    if x.size <= window:
        raise ValueError("losses must contain at least one observation after the window")
    forecasts = np.empty(x.size - window, dtype=np.float64)
    for j, end in enumerate(range(window, x.size)):
        forecasts[j] = empirical_var_es(x[end - window:end], a)[0]
    return forecasts


def kupiec_pof(exceedances: int, n_obs: int, alpha: float) -> dict[str, float | int]:
    """Kupiec unconditional-coverage likelihood-ratio test.

    An exceedance is a realized loss strictly above its forecast VaR. Boundary
    counts zero and ``n_obs`` use the continuous likelihood limit 0 log 0 = 0.
    """
    a = _alpha(alpha)
    for value, name in ((exceedances, "exceedances"), (n_obs, "n_obs")):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer")
    if n_obs < 1 or not 0 <= exceedances <= n_obs:
        raise ValueError("require n_obs >= 1 and 0 <= exceedances <= n_obs")
    q = 1.0 - a
    x = int(exceedances)
    n = int(n_obs)

    def term(count: int, probability: float) -> float:
        return 0.0 if count == 0 else count * math.log(count / (n * probability))

    lr = 2.0 * (term(x, q) + term(n - x, a))
    lr = max(0.0, lr)  # remove only a possible negative round-off at the null.
    p_value = float(stats.chi2.sf(lr, df=1))
    return {"exceedances": x, "n_obs": n, "expected_probability": q,
            "lr_uc": float(lr), "p_value": p_value}


def liquidation_days(quantity: float, adv: float, participation_rate: float) -> float:
    """Trading sessions to liquidate ``quantity`` shares at a fixed ADV participation rate."""
    q = _scalar(quantity, "quantity")
    volume = _scalar(adv, "adv")
    participation = _scalar(participation_rate, "participation_rate")
    if volume <= 0 or not 0.0 < participation <= 1.0:
        raise ValueError("adv must be positive and participation_rate must be in (0, 1]")
    days = abs(q) / (participation * volume)
    if not math.isfinite(days):
        raise ValueError("liquidation days must be finite")
    return float(days)


def margin_requirements(
    gross_market_value: float, nav: float, initial_rate: float, maintenance_rate: float,
) -> dict[str, float]:
    """Apply explicitly supplied constructed initial and maintenance rates to gross exposure."""
    gross = _scalar(gross_market_value, "gross_market_value")
    equity = _scalar(nav, "nav")
    initial = _scalar(initial_rate, "initial_rate")
    maintenance = _scalar(maintenance_rate, "maintenance_rate")
    if gross < 0 or equity <= 0 or not 0.0 <= maintenance <= initial:
        raise ValueError("require gross_market_value >= 0, nav > 0 and 0 <= maintenance_rate <= initial_rate")
    if initial > 1.0:
        raise ValueError("initial_rate cannot exceed 1")
    initial_req = gross * initial
    maintenance_req = gross * maintenance
    result = {"initial_requirement": initial_req, "maintenance_requirement": maintenance_req,
              "initial_headroom": equity - initial_req, "maintenance_headroom": equity - maintenance_req}
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError("margin requirements must be finite")
    return result
