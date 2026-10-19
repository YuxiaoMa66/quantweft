"""Chapter 6: probability models and reproducible teaching simulations.

Every sample generated here is synthetic. Random state lives in a local
``numpy.random.Generator``; importing this module does not alter global state.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm


from uuid import uuid4
CLI_RUN = Path(__file__).resolve().parents[1] / "runs" / ("cli_ch06_probability_" + uuid4().hex)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIGURE_DIR = CLI_RUN / "figures" / "a2"


def _probability(value: float, name: str) -> float:
    """Return a finite probability in [0, 1], with a useful error message."""
    number = float(value)
    if not np.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def posterior_given_positive(
    prior_probability: float,
    sensitivity: float,
    false_positive_rate: float,
) -> float:
    """Compute P(event | positive signal) by Bayes' rule.

    ``sensitivity`` is P(positive | event), and ``false_positive_rate`` is
    P(positive | no event). Raise ValueError when a positive signal has
    probability zero, so the requested conditional probability is undefined.
    """
    prior = _probability(prior_probability, "prior_probability")
    true_positive = _probability(sensitivity, "sensitivity")
    false_positive = _probability(false_positive_rate, "false_positive_rate")

    joint_positive_event = prior * true_positive
    positive_probability = joint_positive_event + (1.0 - prior) * false_positive
    if positive_probability == 0.0:
        raise ValueError("the positive signal has zero probability")
    return joint_positive_event / positive_probability


def bernoulli_moments(probability: float) -> tuple[float, float]:
    """Return the mean and variance of a Bernoulli(p) random variable."""
    p = _probability(probability, "probability")
    return p, p * (1.0 - p)


def binomial_moments(trials: int, probability: float) -> tuple[float, float]:
    """Return the mean and variance of a Binomial(n, p) random variable."""
    if isinstance(trials, (bool, np.bool_)) or not isinstance(trials, (int, np.integer)):
        raise ValueError("trials must be a non-negative integer")
    if trials < 0:
        raise ValueError("trials must be a non-negative integer")
    p = _probability(probability, "probability")
    return float(trials) * p, float(trials) * p * (1.0 - p)


def simulate_lln_paths(
    probability: float = 0.30,
    n_paths: int = 24,
    n_steps: int = 1000,
    seed: int = 641,
) -> tuple[np.ndarray, np.ndarray]:
    """Return Bernoulli sample-mean paths and sample sizes 1..n_steps."""
    p = _probability(probability, "probability")
    paths = _positive_integer(n_paths, "n_paths")
    steps = _positive_integer(n_steps, "n_steps")
    rng = np.random.default_rng(seed)
    draws = rng.binomial(1, p, size=(paths, steps))
    sample_sizes = np.arange(1, steps + 1)
    sample_means = np.cumsum(draws, axis=1) / sample_sizes[None, :]
    return sample_sizes, sample_means


def simulate_clt_standardized_means(
    probability: float = 0.30,
    sample_size: int = 120,
    replications: int = 30_000,
    seed: int = 642,
) -> np.ndarray:
    """Return standardized Bernoulli sample means for a CLT illustration.

    For X_i ~ Bernoulli(p), the returned values are
    sqrt(n) * (mean(X) - p) / sqrt(p * (1-p)).
    The distribution is discrete at finite n; the standard normal overlay is
    a limiting approximation, not an exact finite-sample identity.
    """
    p = _probability(probability, "probability")
    n = _positive_integer(sample_size, "sample_size")
    reps = _positive_integer(replications, "replications")
    variance = p * (1.0 - p)
    if variance == 0.0:
        raise ValueError("probability must be strictly between 0 and 1 for CLT scaling")

    rng = np.random.default_rng(seed)
    successes = rng.binomial(1, p, size=(reps, n)).sum(axis=1)
    return (successes - n * p) / np.sqrt(n * variance)


def simulate_random_walk_paths(
    n_paths: int = 18,
    n_steps: int = 300,
    seed: int = 643,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate independent symmetric +/-1 walks, including position at 0."""
    paths = _positive_integer(n_paths, "n_paths")
    steps = _positive_integer(n_steps, "n_steps")
    rng = np.random.default_rng(seed)
    increments = 2 * rng.integers(0, 2, size=(paths, steps), dtype=np.int8) - 1
    positions = np.concatenate(
        [np.zeros((paths, 1), dtype=np.int64), np.cumsum(increments, axis=1)],
        axis=1,
    )
    return np.arange(steps + 1), positions


def simulate_poisson_process_paths(
    rate: float = 0.70,
    horizon: float = 12.0,
    n_intervals: int = 240,
    n_paths: int = 14,
    seed: int = 644,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate a homogeneous Poisson process through independent increments.

    ``rate`` is measured in events per time unit. A zero rate is allowed and
    produces the degenerate zero-count process.
    """
    lam = float(rate)
    duration = float(horizon)
    if not np.isfinite(lam) or lam < 0.0:
        raise ValueError("rate must be finite and non-negative")
    if not np.isfinite(duration) or duration <= 0.0:
        raise ValueError("horizon must be finite and positive")
    intervals = _positive_integer(n_intervals, "n_intervals")
    paths = _positive_integer(n_paths, "n_paths")

    rng = np.random.default_rng(seed)
    times = np.linspace(0.0, duration, intervals + 1)
    dt = duration / intervals
    increments = rng.poisson(lam=lam * dt, size=(paths, intervals))
    counts = np.concatenate(
        [np.zeros((paths, 1), dtype=np.int64), np.cumsum(increments, axis=1)],
        axis=1,
    )
    return times, counts


def generate_figures(
    output_dir: str | Path = DEFAULT_FIGURE_DIR,
    seed: int = 641,
) -> dict[str, Path]:
    """Create four fixed-seed, constructed probability figures."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    figures: dict[str, Path] = {}

    probability = 0.30
    sample_sizes, mean_paths = simulate_lln_paths(
        probability=probability, n_paths=24, n_steps=1000, seed=seed
    )
    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    for path in mean_paths:
        ax.plot(sample_sizes, path, color="#4277A5", alpha=0.32, linewidth=0.85)
    ax.axhline(probability, color="#C05A47", linestyle="--", linewidth=1.8, label="True mean p = 0.30")
    ax.set_xlabel("Sample size n (Bernoulli trials)")
    ax.set_ylabel("Sample mean (unitless proportion)")
    ax.set_title(f"LLN: Bernoulli sample means | constructed, seed={seed}")
    ax.set_xlim(1, sample_sizes[-1])
    ax.set_ylim(0.0, 1.0)
    ax.legend(frameon=False)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    figures["lln"] = output / "ch06_lln.png"
    fig.savefig(figures["lln"], dpi=170)
    plt.close(fig)

    standardized = simulate_clt_standardized_means(
        probability=probability, sample_size=120, replications=30_000, seed=seed + 1
    )
    x = np.linspace(-4.0, 4.0, 401)
    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    ax.hist(
        standardized,
        bins=51,
        density=True,
        color="#72A98F",
        alpha=0.66,
        label="Simulated standardized means",
    )
    ax.plot(x, norm.pdf(x), color="#303A73", linewidth=2.1, label="Standard normal density")
    ax.set_xlabel("Standardized sample mean (unitless)")
    ax.set_ylabel("Density (unitless standardized variable)")
    ax.set_title(f"CLT approximation: n=120, 30,000 replications | seed={seed + 1}")
    ax.legend(frameon=False)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    figures["clt"] = output / "ch06_clt.png"
    fig.savefig(figures["clt"], dpi=170)
    plt.close(fig)

    steps, walks = simulate_random_walk_paths(n_paths=18, n_steps=300, seed=seed + 2)
    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    for path in walks:
        ax.plot(steps, path, linewidth=0.9, alpha=0.68)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Step n (unit-time increments)")
    ax.set_ylabel("Position Sₙ (step units)")
    ax.set_title(f"Symmetric random walk | constructed, seed={seed + 2}")
    ax.grid(alpha=0.18)
    fig.tight_layout()
    figures["random_walk"] = output / "ch06_random_walk.png"
    fig.savefig(figures["random_walk"], dpi=170)
    plt.close(fig)

    rate = 0.70
    times, counts = simulate_poisson_process_paths(
        rate=rate, horizon=12.0, n_intervals=240, n_paths=14, seed=seed + 3
    )
    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    for path in counts:
        ax.step(times, path, where="post", linewidth=0.95, alpha=0.64)
    ax.plot(times, rate * times, color="#B24C3B", linestyle="--", linewidth=2.0, label="E[N(t)] = λt")
    ax.set_xlabel("Elapsed time t (constructed time units)")
    ax.set_ylabel("Cumulative event count N(t) (events)")
    ax.set_title(f"Homogeneous Poisson process, λ={rate:.2f} events/time | seed={seed + 3}")
    ax.legend(frameon=False)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    figures["poisson"] = output / "ch06_poisson_process.png"
    fig.savefig(figures["poisson"], dpi=170)
    plt.close(fig)
    return figures


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_FIGURE_DIR,
        help="directory for the four constructed teaching figures",
    )
    parser.add_argument("--seed", type=int, default=641)
    args = parser.parse_args(argv)

    posterior = posterior_given_positive(0.005, 0.95, 0.05)
    mean, variance = bernoulli_moments(0.30)
    binomial_mean, binomial_variance = binomial_moments(20, 0.30)
    figures = generate_figures(args.output_dir, seed=args.seed)

    print("CONSTRUCTED probability examples; no market observations")
    print(f"rare-event posterior after positive flag: {posterior:.8%}")
    print(f"Bernoulli(p=0.30): mean={mean:.4f}, variance={variance:.4f}")
    print(f"Binomial(n=20,p=0.30): mean={binomial_mean:.4f}, variance={binomial_variance:.4f}")
    for name, path in figures.items():
        print(f"{name} figure: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


if __name__ == "__main__":
    main()
