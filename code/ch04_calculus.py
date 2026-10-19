"""Chapter 4: derivatives, finite differences, and Taylor approximation."""

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

from quant_course.math_tools import finite_difference_gradient, finite_difference_hessian


SIGMA = np.array([[0.04, 0.01], [0.01, 0.09]])
MU = np.array([0.05, 0.08])


def zero_coupon_price(point: np.ndarray) -> float:
    return 100.0 / (1.0 + point[0]) ** 2


def quadratic_loss(point: np.ndarray) -> float:
    return float(0.5 * point @ SIGMA @ point - MU @ point)


def main() -> None:
    output_dir = ROOT / "runs" / ("ch04_calculus_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    y = 0.05
    price = 100.0 / (1.0 + y) ** 2
    first_derivative = -200.0 / (1.0 + y) ** 3
    second_derivative = 600.0 / (1.0 + y) ** 4
    numeric_first = finite_difference_gradient(zero_coupon_price, [y], step=1e-4)[0]
    numeric_second = finite_difference_hessian(zero_coupon_price, [y], step=1e-3)[0, 0]
    print("CONSTRUCTED calculus examples; no market observations")
    print(f"P(y) at y={y:.2%}: {price:.10f}")
    print(f"P'(y) analytic/numeric: {first_derivative:.10f} / {numeric_first:.10f}")
    print(f"P''(y) analytic/numeric: {second_derivative:.10f} / {numeric_second:.10f}")

    point = np.array([0.6, 0.4])
    exact_gradient = SIGMA @ point - MU
    exact_hessian = SIGMA.copy()
    numeric_gradient = finite_difference_gradient(quadratic_loss, point)
    numeric_hessian = finite_difference_hessian(quadratic_loss, point)
    print(f"quadratic loss at w=[0.6, 0.4]: {quadratic_loss(point):.10f}")
    print(f"gradient analytic: {exact_gradient}")
    print(f"gradient numeric:  {numeric_gradient}")
    print(f"Hessian analytic:\n{exact_hessian}")
    print(f"Hessian numeric:\n{numeric_hessian}")

    direction = np.array([1.0, -0.5])
    base_value = quadratic_loss(point)
    steps = np.geomspace(1e-5, 0.25, 80)
    first_order_errors = []
    second_order_errors = []
    for step in steps:
        displacement = step * direction
        actual = quadratic_loss(point + displacement)
        first_order = base_value + exact_gradient @ displacement
        second_order = first_order + 0.5 * displacement @ exact_hessian @ displacement
        first_order_errors.append(abs(actual - first_order))
        second_order_errors.append(abs(actual - second_order))

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.loglog(steps, first_order_errors, label="First-order Taylor error", color="#2878B5")
    ax.loglog(steps, second_order_errors, label="Second-order Taylor residual", color="#D9534F")
    ax.loglog(
        steps,
        0.5 * (direction @ SIGMA @ direction) * steps**2,
        linestyle="--",
        color="#555555",
        label="Quadratic O(h²) reference",
    )
    ax.set_xlabel("Step size h along direction [1, -0.5]")
    ax.set_ylabel("Absolute approximation error")
    ax.set_title("Taylor approximation error for the constructed quadratic loss")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    output = output_dir / "ch04_taylor_error.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"figure: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
