"""Chapter 7: estimation, intervals, p-values, bootstrap, and Bayes examples."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.statistics_tools import (  # noqa: E402
    beta_binomial_posterior,
    bootstrap_mean_confidence_interval,
    bootstrap_mean_draws,
    mean_t_confidence_interval,
    moving_block_bootstrap_mean_draws,
    normal_mle_estimates,
    one_sample_t_test,
    simulate_stationary_ar1,
    simulate_t_interval_coverage,
)


SEED = 20261007
PERIOD_UNIT = "return per constructed observation period"


def main() -> None:
    output_dir = ROOT / "runs" / ("ch07_statistics_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    # Spawn independent random streams from one visible master seed.
    seed_sequence = np.random.SeedSequence(SEED)
    normal_seed, coverage_seed, ar_seed, iid_seed, block_seed = seed_sequence.spawn(5)
    normal_rng = np.random.default_rng(normal_seed)
    coverage_rng = np.random.default_rng(coverage_seed)
    ar_rng = np.random.default_rng(ar_seed)
    iid_rng = np.random.default_rng(iid_seed)
    block_rng = np.random.default_rng(block_seed)

    sample_n = 40
    sample_mean = 0.002
    sample_std = 0.02
    normal_sample = normal_rng.normal(sample_mean, sample_std, size=sample_n)
    estimates = normal_mle_estimates(normal_sample)
    interval = mean_t_confidence_interval(normal_sample, confidence_level=0.95)
    test = one_sample_t_test(normal_sample, null_mean=0.0)

    print("CONSTRUCTED Chapter 7 examples; no market observations or performance claim")
    print(f"master seed: {SEED}; normal sample n: {sample_n}; unit: {PERIOD_UNIT}")
    print(
        "normal estimates: "
        f"mean={estimates.mean:.6f}, MLE variance (ddof=0)={estimates.variance_mle:.8f}, "
        f"unbiased variance (ddof=1)={estimates.variance_unbiased:.8f}"
    )
    print(
        f"95% Student-t mean CI: [{interval.lower:.6f}, {interval.upper:.6f}] "
        f"{PERIOD_UNIT}; df={sample_n - 1}"
    )
    print(
        f"two-sided t test H0: mean=0: t={test.t_statistic:.6f}, "
        f"p={test.p_value:.6f}; p is a tail probability under H0 and its assumptions, "
        "not the probability that H0 is true"
    )

    posterior = beta_binomial_posterior(6, 4, prior_alpha=2.0, prior_beta=2.0)
    print(
        "Beta-Binomial construction: prior Beta(2, 2), 6 wins, 4 losses -> "
        f"posterior Beta({posterior.posterior_alpha:.0f}, {posterior.posterior_beta:.0f}), "
        f"mean={posterior.posterior_mean:.6f} (success probability only; not positive EV)"
    )

    coverage_repetitions = 3000
    coverage_sizes = [10, 30, 100]
    coverage = simulate_t_interval_coverage(
        coverage_sizes,
        repetitions=coverage_repetitions,
        true_mean=0.001,
        true_std=0.02,
        confidence_level=0.95,
        rng=coverage_rng,
    )
    print(
        "normal coverage simulation: "
        f"true mean=0.001, true sd=0.02 {PERIOD_UNIT}, "
        f"nominal=95%, repetitions={coverage_repetitions}; rates={coverage}"
    )

    full_ar_n = 240
    train_n = 180
    phi = 0.70
    innovation_std = 0.01
    block_length = 12
    bootstrap_repetitions = 4000
    ar_series = simulate_stationary_ar1(
        full_ar_n,
        phi=phi,
        innovation_std=innovation_std,
        rng=ar_rng,
    )
    # Explicit chronological training slice: later observations are held out and
    # never passed into either bootstrap function.
    training = ar_series[:train_n]
    iid_draws = bootstrap_mean_draws(
        training,
        n_resamples=bootstrap_repetitions,
        rng=iid_rng,
    )
    block_draws = moving_block_bootstrap_mean_draws(
        training,
        block_length=block_length,
        n_resamples=bootstrap_repetitions,
        rng=block_rng,
    )
    iid_ci = bootstrap_mean_confidence_interval(iid_draws)
    block_ci = bootstrap_mean_confidence_interval(block_draws)
    effective_n_approx = train_n * (1.0 - phi) / (1.0 + phi)
    print(
        f"constructed stationary AR(1): n={full_ar_n}, phi={phi:.2f}, "
        f"innovation sd={innovation_std:.3f} {PERIOD_UNIT}; "
        f"training n={train_n}, held-out n={full_ar_n - train_n}"
    )
    print(
        f"AR(1) approximate effective n={effective_n_approx:.2f} using "
        "n(1-phi)/(1+phi); a dependence heuristic, not an estimated universal truth"
    )
    print(
        f"bootstrap means: repetitions={bootstrap_repetitions}; IID percentile 95% CI="
        f"[{iid_ci.lower:.6f}, {iid_ci.upper:.6f}], "
        f"moving-block (fixed L={block_length}) 95% CI="
        f"[{block_ci.lower:.6f}, {block_ci.upper:.6f}] {PERIOD_UNIT}"
    )
    print(
        "Moving-block bootstrap preserves adjacent order within sampled circular blocks. "
        "The fixed block length is illustrative, not a validity guarantee; inference "
        "depends on stationarity, weak-dependence conditions, and block-size choice."
    )

    _save_figure(
        output_dir=output_dir,
        coverage=coverage,
        nominal=0.95,
        coverage_repetitions=coverage_repetitions,
        iid_draws=iid_draws,
        block_draws=block_draws,
        block_length=block_length,
        train_n=train_n,
        phi=phi,
        bootstrap_repetitions=bootstrap_repetitions,
    )


def _save_figure(
    output_dir: Path,
    *,
    coverage: dict[int, float],
    nominal: float,
    coverage_repetitions: int,
    iid_draws: np.ndarray,
    block_draws: np.ndarray,
    block_length: int,
    train_n: int,
    phi: float,
    bootstrap_repetitions: int,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    sizes = np.array(list(coverage))
    rates = np.array([coverage[size] for size in sizes])
    axes[0].plot(sizes, rates * 100.0, marker="o", color="#235789")
    axes[0].axhline(nominal * 100.0, color="#C1292E", linestyle="--", label="Nominal 95%")
    axes[0].set_xlabel("Sample size n (constructed observations)")
    axes[0].set_ylabel("Intervals covering true mean (%)")
    axes[0].set_title(f"Student-t interval coverage; {coverage_repetitions:,} simulations")
    axes[0].set_ylim(85, 100)
    axes[0].grid(alpha=0.25)
    axes[0].legend(frameon=False)

    bins = 45
    axes[1].hist(iid_draws, bins=bins, density=True, alpha=0.52, label="IID bootstrap")
    axes[1].hist(
        block_draws,
        bins=bins,
        density=True,
        alpha=0.52,
        label=f"Moving blocks (L={block_length})",
    )
    axes[1].axvline(float(iid_draws.mean()), color="#235789", linestyle=":", linewidth=1.5)
    axes[1].set_xlabel("Bootstrap mean (return per constructed period)")
    axes[1].set_ylabel("Density (inverse return unit)")
    axes[1].set_title(
        f"AR(1) training n={train_n}, phi={phi:.2f}; "
        f"{bootstrap_repetitions:,} bootstrap draws"
    )
    axes[1].grid(alpha=0.2)
    axes[1].legend(frameon=False)

    fig.suptitle(
        f"Chapter 7 — constructed simulation only; master seed {SEED}; "
        "no empirical performance inference"
    )
    fig.tight_layout()
    output = output_dir / "ch07_statistics.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
