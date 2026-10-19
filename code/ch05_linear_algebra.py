"""Chapter 5: covariance geometry, linear solves, SVD, and training-only PCA."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.math_tools import pca_fit_transform


SIGMA = np.array([[0.04, 0.01], [0.01, 0.09]])
MU = np.array([0.05, 0.08])


def main() -> None:
    output_dir = ROOT / "runs" / ("ch05_linear_algebra_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    weights = np.array([0.6, 0.4])
    variance = float(weights @ SIGMA @ weights)
    eigenvalues, eigenvectors = np.linalg.eigh(SIGMA)
    rank = int(np.linalg.matrix_rank(SIGMA))
    condition = float(np.linalg.cond(SIGMA, p=2))
    solution = np.linalg.solve(SIGMA, MU)
    residual = float(np.linalg.norm(SIGMA @ solution - MU))

    print("CONSTRUCTED linear algebra examples; no market observations")
    print(f"w=[0.6, 0.4] variance w'Σw: {variance:.8f}")
    print(f"Σ eigenvalues: {eigenvalues}")
    print(f"PSD: {bool(np.all(eigenvalues >= 0))}; PD: {bool(np.all(eigenvalues > 0))}")
    print(f"rank(Σ): {rank}; 2-norm condition number: {condition:.8f}")
    print(f"eigh eigenvectors (columns):\n{eigenvectors}")
    print(f"solve Σx=μ: x={solution}; residual norm={residual:.3e}")
    print("The linear-system solution is a matrix example, not a portfolio recommendation.")

    # Constructed weekday returns: columns are four fictitious assets. There is
    # no exchange holiday calendar and no external or empirical price source.
    rng = np.random.default_rng(20261005)
    observations = 252
    market = rng.normal(0.0, 0.012, observations)
    rates = rng.normal(0.0, 0.006, observations)
    style = rng.normal(0.0, 0.007, observations)
    idiosyncratic = rng.normal(
        0.0, [0.005, 0.007, 0.006, 0.008], size=(observations, 4)
    )
    constructed_returns = (
        market[:, None] * np.array([1.0, 0.8, 0.25, 0.1])
        + rates[:, None] * np.array([0.15, -0.2, 0.7, 0.4])
        + style[:, None] * np.array([-0.1, 0.2, -0.2, 0.5])
        + idiosyncratic
    )
    dates = pd.date_range("2024-01-02", periods=observations, freq="B", tz="UTC")
    returns = pd.DataFrame(
        constructed_returns,
        index=dates,
        columns=["SIM-A", "SIM-B", "SIM-C", "SIM-D"],
    )
    train = returns.iloc[:180]
    later_window = returns.iloc[180:]
    pca = pca_fit_transform(train.to_numpy(), n_components=4)
    print(
        f"PCA fit rows: {len(train)} ({train.index[0].date()} to {train.index[-1].date()}); "
        f"later rows held out: {len(later_window)} (first {later_window.index[0].date()})"
    )
    print(f"feature dimension p={train.shape[1]}, training center: {pca.center}")
    print(f"PCA components shape (k, p): {pca.components.shape}")
    print(f"training projection shape (n, k): {pca.projection.shape}")
    print(f"sample explained variance (ddof=1): {pca.explained_variance}")
    print(f"explained variance ratio: {pca.explained_variance_ratio}")
    print("PCA center/components were fit only on the first 180 rows; later rows were not used.")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    scatter = axes[0].scatter(
        pca.projection[:, 0],
        pca.projection[:, 1],
        c=np.arange(len(train)),
        cmap="viridis",
        s=18,
        alpha=0.8,
    )
    axes[0].set_xlabel("PC1 score (return units)")
    axes[0].set_ylabel("PC2 score (return units)")
    axes[0].set_title("Training-window projections only")
    fig.colorbar(scatter, ax=axes[0], label="Training row")
    components = np.arange(1, len(pca.explained_variance_ratio) + 1)
    axes[1].bar(components, pca.explained_variance_ratio, color="#4C9F70")
    axes[1].set_xlabel("Principal component")
    axes[1].set_ylabel("Share of training sample variance")
    axes[1].set_xticks(components)
    axes[1].set_title("SVD-based PCA (sample variance, ddof=1)")
    fig.suptitle("Constructed daily return sample; fixed seed 20261005")
    fig.tight_layout()
    output = output_dir / "ch05_pca.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
