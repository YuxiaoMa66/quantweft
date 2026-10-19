"""Small, explicit statistical examples for the quantitative finance course.

All resampling functions require a caller-owned ``numpy.random.Generator`` so
randomness and seeds remain visible in the calling example.  The functions
operate only on the sample supplied by the caller; they do not fetch or infer
future observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class NormalEstimates:
    """Location and two scale estimates for one finite sample."""

    mean: float
    variance_mle: float
    variance_unbiased: float
    n: int


@dataclass(frozen=True)
class ConfidenceInterval:
    """A two-sided interval for a scalar mean, in the input sample's units."""

    estimate: float
    lower: float
    upper: float
    confidence_level: float
    standard_error: float


@dataclass(frozen=True)
class TTestResult:
    """Two-sided one-sample Student t test result."""

    sample_mean: float
    null_mean: float
    t_statistic: float
    p_value: float
    degrees_of_freedom: int


@dataclass(frozen=True)
class BetaPosterior:
    """Beta prior and posterior parameters for a Bernoulli success rate."""

    prior_alpha: float
    prior_beta: float
    successes: int
    failures: int
    posterior_alpha: float
    posterior_beta: float

    @property
    def posterior_mean(self) -> float:
        return self.posterior_alpha / (self.posterior_alpha + self.posterior_beta)


def _sample_vector(sample: object, *, minimum_n: int = 2) -> np.ndarray:
    values = np.asarray(sample)
    if np.iscomplexobj(values):
        raise TypeError("sample must contain real values, not complex values")
    if values.dtype == np.bool_ or not np.issubdtype(values.dtype, np.number):
        raise TypeError("sample must contain real numeric values, not text or booleans")
    try:
        values = values.astype(float, copy=False)
    except (TypeError, ValueError) as exc:
        raise TypeError("sample must be a one-dimensional real numeric sequence") from exc
    if values.ndim != 1:
        raise ValueError("sample must be one-dimensional")
    if values.size < minimum_n:
        raise ValueError(f"sample must contain at least {minimum_n} observations")
    if not np.isfinite(values).all():
        raise ValueError("sample values must all be finite; handle missing values explicitly")
    return values


def _confidence_level(value: float) -> float:
    if isinstance(value, (bool, np.bool_)) or not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError("confidence_level must be finite and strictly between 0 and 1")
    return float(value)


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return int(value)


def _generator(rng: np.random.Generator) -> np.random.Generator:
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator")
    return rng


def normal_mle_estimates(sample: object) -> NormalEstimates:
    """Return the Gaussian MLE mean/variance and the ddof=1 variance estimate.

    The MLE variance divides the sum of squared deviations by ``n``.  The
    unbiased sample variance divides by ``n - 1``. A constant sample is
    rejected: under the regular Gaussian model with strictly positive variance,
    its likelihood is unbounded as variance approaches zero, so no finite MLE
    exists. This is distinct from the descriptive zero sample variance.
    """

    values = _sample_vector(sample)
    variance_mle = float(values.var(ddof=0))
    if variance_mle <= 0.0 or not np.isfinite(variance_mle):
        raise ValueError("Gaussian MLE requires positive finite sample variance")
    return NormalEstimates(
        mean=float(values.mean()),
        variance_mle=variance_mle,
        variance_unbiased=float(values.var(ddof=1)),
        n=int(values.size),
    )


def mean_t_confidence_interval(
    sample: object, *, confidence_level: float = 0.95
) -> ConfidenceInterval:
    """Student-t mean interval, exact for IID Gaussian samples.

    For other distributions, coverage needs separate justification; dependent
    returns cannot use the IID standard error by default.
    """

    values = _sample_vector(sample)
    confidence = _confidence_level(confidence_level)
    standard_error = float(values.std(ddof=1) / np.sqrt(values.size))
    if not np.isfinite(standard_error) or standard_error <= 0.0:
        raise ValueError("t interval requires positive finite sample standard deviation")
    critical = float(stats.t.ppf((1.0 + confidence) / 2.0, df=values.size - 1))
    estimate = float(values.mean())
    half_width = critical * standard_error
    return ConfidenceInterval(
        estimate=estimate,
        lower=estimate - half_width,
        upper=estimate + half_width,
        confidence_level=confidence,
        standard_error=standard_error,
    )


def one_sample_t_test(sample: object, *, null_mean: float = 0.0) -> TTestResult:
    """Two-sided mean test with the IID Gaussian Student-t reference law.

    This computes a reference tail probability, not a posterior probability
    that the null holds. Normality/independence are modeling assumptions.
    """

    values = _sample_vector(sample)
    if isinstance(null_mean, (bool, np.bool_)) or not np.isfinite(null_mean):
        raise ValueError("null_mean must be a finite real number")
    standard_error = float(values.std(ddof=1) / np.sqrt(values.size))
    if not np.isfinite(standard_error) or standard_error <= 0.0:
        raise ValueError("t test requires positive finite sample standard deviation")
    sample_mean = float(values.mean())
    statistic = (sample_mean - float(null_mean)) / standard_error
    p_value = float(2.0 * stats.t.sf(abs(statistic), df=values.size - 1))
    return TTestResult(
        sample_mean=sample_mean,
        null_mean=float(null_mean),
        t_statistic=float(statistic),
        p_value=p_value,
        degrees_of_freedom=int(values.size - 1),
    )


def bootstrap_mean_draws(
    sample: object,
    *,
    n_resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """IID nonparametric bootstrap draws of the sample mean."""

    values = _sample_vector(sample)
    repetitions = _positive_integer(n_resamples, "n_resamples")
    generator = _generator(rng)
    indices = generator.integers(0, values.size, size=(repetitions, values.size))
    return values[indices].mean(axis=1)


def moving_block_bootstrap_mean_draws(
    sample: object,
    *,
    block_length: int,
    n_resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Circular moving-block bootstrap draws for a scalar sample mean.

    Consecutive observations inside each sampled block retain their order.
    Blocks are circular at the sample boundary, concatenated, and truncated to
    the original sample length.  This is an instructional fixed-block method,
    not a universal validity guarantee; block size and dependence assumptions
    must be justified for a real application.
    """

    values = _sample_vector(sample)
    repetitions = _positive_integer(n_resamples, "n_resamples")
    if isinstance(block_length, (bool, np.bool_)) or not isinstance(
        block_length, (int, np.integer)
    ):
        raise TypeError("block_length must be an integer")
    if not 1 <= block_length <= values.size:
        raise ValueError("block_length must be between 1 and the sample size")
    generator = _generator(rng)
    blocks_per_draw = int(np.ceil(values.size / int(block_length)))
    starts = generator.integers(0, values.size, size=(repetitions, blocks_per_draw))
    offsets = np.arange(int(block_length))
    indices = (starts[..., None] + offsets) % values.size
    resampled = values[indices].reshape(repetitions, -1)[:, : values.size]
    return resampled.mean(axis=1)


def bootstrap_mean_confidence_interval(
    draws: object, *, confidence_level: float = 0.95
) -> ConfidenceInterval:
    """Percentile interval from caller-supplied bootstrap mean draws.

    ``estimate`` is the mean of the bootstrap draws, not the original sample
    mean. Keep the original point estimate separately; finite resampling noise
    can make these two means differ. ``standard_error`` is the draws' sample
    standard deviation, an estimate of sampling uncertainty.
    """

    values = _sample_vector(draws)
    confidence = _confidence_level(confidence_level)
    tail = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(values, [tail, 1.0 - tail])
    return ConfidenceInterval(
        estimate=float(values.mean()),
        lower=float(lower),
        upper=float(upper),
        confidence_level=confidence,
        standard_error=float(values.std(ddof=1)),
    )


def simulate_t_interval_coverage(
    sample_sizes: Sequence[int],
    *,
    repetitions: int,
    true_mean: float,
    true_std: float,
    confidence_level: float,
    rng: np.random.Generator,
) -> dict[int, float]:
    """Simulate normal-sample coverage of the unknown-variance t interval."""

    reps = _positive_integer(repetitions, "repetitions")
    confidence = _confidence_level(confidence_level)
    if isinstance(true_mean, (bool, np.bool_)) or not np.isfinite(true_mean):
        raise ValueError("true_mean must be finite")
    if isinstance(true_std, (bool, np.bool_)) or not np.isfinite(true_std) or true_std <= 0:
        raise ValueError("true_std must be positive and finite")
    generator = _generator(rng)
    sizes = [_positive_integer(size, "sample size") for size in sample_sizes]
    if not sizes or any(size < 2 for size in sizes):
        raise ValueError("sample_sizes must contain values of at least 2")
    results: dict[int, float] = {}
    for size in sizes:
        draws = generator.normal(true_mean, true_std, size=(reps, size))
        means = draws.mean(axis=1)
        standard_errors = draws.std(axis=1, ddof=1) / np.sqrt(size)
        critical = stats.t.ppf((1.0 + confidence) / 2.0, df=size - 1)
        lower = means - critical * standard_errors
        upper = means + critical * standard_errors
        results[size] = float(np.mean((lower <= true_mean) & (true_mean <= upper)))
    return results


def simulate_stationary_ar1(
    n: int,
    *,
    phi: float,
    innovation_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate a zero-mean stationary Gaussian AR(1) teaching series."""

    size = _positive_integer(n, "n")
    if size < 2:
        raise ValueError("n must be at least 2")
    if isinstance(phi, (bool, np.bool_)) or not np.isfinite(phi) or abs(phi) >= 1.0:
        raise ValueError("phi must be finite and strictly between -1 and 1")
    if (
        isinstance(innovation_std, (bool, np.bool_))
        or not np.isfinite(innovation_std)
        or innovation_std <= 0.0
    ):
        raise ValueError("innovation_std must be positive and finite")
    generator = _generator(rng)
    values = np.empty(size, dtype=float)
    stationary_std = innovation_std / np.sqrt(1.0 - phi**2)
    values[0] = generator.normal(0.0, stationary_std)
    innovations = generator.normal(0.0, innovation_std, size=size - 1)
    for index in range(1, size):
        values[index] = phi * values[index - 1] + innovations[index - 1]
    return values


def beta_binomial_posterior(
    successes: int,
    failures: int,
    *,
    prior_alpha: float = 2.0,
    prior_beta: float = 2.0,
) -> BetaPosterior:
    """Update a Beta prior with Bernoulli success/failure counts."""

    wins = _count(successes, "successes")
    losses = _count(failures, "failures")
    if (
        isinstance(prior_alpha, (bool, np.bool_))
        or isinstance(prior_beta, (bool, np.bool_))
        or not np.isfinite(prior_alpha)
        or not np.isfinite(prior_beta)
        or prior_alpha <= 0.0
        or prior_beta <= 0.0
    ):
        raise ValueError("Beta prior parameters must be positive and finite")
    return BetaPosterior(
        prior_alpha=float(prior_alpha),
        prior_beta=float(prior_beta),
        successes=wins,
        failures=losses,
        posterior_alpha=float(prior_alpha + wins),
        posterior_beta=float(prior_beta + losses),
    )


def _count(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return int(value)
