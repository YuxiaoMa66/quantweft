"""Plot constructed covariance geometry; contours are not confidence regions."""
from pathlib import Path
from uuid import uuid4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    output_dir = ROOT / "runs" / ("ch05_covariance_geometry_" + uuid4().hex)
    output_dir.mkdir(parents=True, exist_ok=False)
    covariance = np.array([[0.04, 0.01], [0.01, 0.09]])
    eigenvalues, directions = np.linalg.eigh(covariance)
    x_axis = np.linspace(-0.65, 0.65, 240)
    y_axis = np.linspace(-0.8, 0.8, 240)
    x, y = np.meshgrid(x_axis, y_axis)
    points = np.vstack([x.ravel(), y.ravel()])
    mapped = np.linalg.solve(covariance, points)
    quadratic = np.sum(points * mapped, axis=0).reshape(x.shape)
    fig, ax = plt.subplots(figsize=(7, 6))
    contours = ax.contour(100 * x, 100 * y, quadratic, levels=[1, 4],
                          colors=["#247F82", "#CF8951"])
    ax.clabel(contours, fmt={1: "q=1", 4: "q=4"})
    for index in range(2):
        endpoint = directions[:, index] * np.sqrt(eigenvalues[index]) * 100
        ax.annotate("", xy=endpoint, xytext=(0, 0),
                    arrowprops={"arrowstyle": "->", "color": "#142D36", "lw": 1.5})
        ax.text(endpoint[0], endpoint[1], f"  axis {index + 1}")
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    ax.set_xlabel("Asset A: one-year return deviation (percentage points)")
    ax.set_ylabel("Asset B: one-year return deviation (percentage points)")
    ax.set_title("Constructed covariance: quadratic contours and principal axes")
    ax.set_aspect("equal")
    ax.grid(alpha=0.15)
    fig.tight_layout()
    destination = output_dir / "ch05_covariance.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=160)
    plt.close(fig)
    print(destination)


if __name__ == "__main__":
    main()
