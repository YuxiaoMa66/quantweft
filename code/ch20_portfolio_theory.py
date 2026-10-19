"""Reproduce Chapter 20 mean-variance examples and figures.

Closed forms come from ``quant_course.portfolio_theory``; the long-only
frontier reuses the Chapter 9 QP ``solve_mean_variance`` (zero shorting).
Constructed examples use annual decimal moments chosen for teaching. The
French part estimates monthly moments on two fixed historical windows of the
frozen current-revision snapshot and is descriptive only: no window is used to
pick weights for a later window here (rolling out-of-sample tests are in
Project 3). Nothing is downloaded.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.optimization_tools import solve_mean_variance  # noqa: E402
from quant_course.portfolio_theory import (  # noqa: E402
    global_minimum_variance_weights, minimum_variance_target_weights,
    portfolio_moments, tangency_weights,
)

TWO_MU = np.array([0.06, 0.10])
TWO_SIGMA = np.array([0.15, 0.25])
TWO_RHO = 0.2
TWO_RF = 0.02
THREE_MU = np.array([0.05, 0.08, 0.12])
THREE_SIGMA = np.array([0.12, 0.18, 0.28])
THREE_CORR = np.array([[1.0, 0.3, 0.1], [0.3, 1.0, 0.4], [0.1, 0.4, 1.0]])
THREE_RF = 0.02
WINDOWS = {"2000-01..2009-12": ("2000-01", "2009-12"), "2010-01..2019-12": ("2010-01", "2019-12")}
FIGURES = ("ch20_two_asset_correlation.png", "ch20_frontier_cml.png", "ch20_french_estimated_frontiers.png")
OUTPUTS = ("ch20_results.json", "ch20_french_window_weights.csv")


def cov_from(sigma: np.ndarray, corr: np.ndarray) -> np.ndarray:
    return np.outer(sigma, sigma) * corr


def frontier_constants(mu: np.ndarray, cov: np.ndarray) -> dict[str, float]:
    """A=1'S^-1 1, B=1'S^-1 mu, C=mu'S^-1 mu, D=AC-B^2 for the hyperbola var(m)=(A m^2-2Bm+C)/D."""
    ones = np.ones(mu.size)
    inv_one = np.linalg.solve(cov, ones)
    inv_mu = np.linalg.solve(cov, mu)
    a, b, c = float(ones @ inv_one), float(ones @ inv_mu), float(mu @ inv_mu)
    return {"A": a, "B": b, "C": c, "D": a * c - b * b}


def frontier_variance(target: np.ndarray, k: dict[str, float]) -> np.ndarray:
    return (k["A"] * target ** 2 - 2 * k["B"] * target + k["C"]) / k["D"]


def two_asset_example() -> dict[str, Any]:
    cov = cov_from(TWO_SIGMA, np.array([[1, TWO_RHO], [TWO_RHO, 1]]))
    gmv = global_minimum_variance_weights(cov)
    target = minimum_variance_target_weights(TWO_MU, cov, target_return=0.08)
    tangent = tangency_weights(TWO_MU, cov, risk_free_return=TWO_RF)
    k = frontier_constants(TWO_MU, cov)
    out: dict[str, Any] = {"covariance": cov.tolist(), "constants": k}
    for name, w in (("gmv", gmv), ("target_0.08", target), ("tangency", tangent)):
        m = portfolio_moments(w, TWO_MU, cov)
        out[name] = {"weights": w.tolist(), "mean": m.expected_return,
                     "variance": m.variance, "volatility": m.volatility}
    out["tangency"]["sharpe"] = (out["tangency"]["mean"] - TWO_RF) / out["tangency"]["volatility"]
    out["max_sharpe_squared_formula"] = k["C"] - 2 * TWO_RF * k["B"] + TWO_RF ** 2 * k["A"]
    out["frontier_variance_at_0.08"] = float(frontier_variance(np.array(0.08), k))
    return out


def long_only_frontier(mu: np.ndarray, cov: np.ndarray, n: int = 40) -> np.ndarray:
    """Trace long-only efficient points by sweeping the Ch9 utility risk aversion."""
    points = []
    for gamma in np.logspace(-3.0, 3.5, n) / max(np.max(np.abs(cov)), 1e-300):
        r = solve_mean_variance(mu, cov, risk_aversion=float(gamma))
        points.append((np.sqrt(r.variance), r.expected_return))
    return np.array(sorted(points))


def plot_two_asset(path: Path) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    w1 = np.linspace(-0.5, 1.5, 401)
    rows = {}
    for rho, color in zip((-1.0, -0.5, 0.0, 0.5, 1.0), ("#1b4f72", "#2e86c1", "#17a589", "#ca6f1e", "#922b21")):
        mean = w1 * TWO_MU[0] + (1 - w1) * TWO_MU[1]
        var = (w1 * TWO_SIGMA[0]) ** 2 + ((1 - w1) * TWO_SIGMA[1]) ** 2 + 2 * w1 * (1 - w1) * rho * TWO_SIGMA.prod()
        vol = np.sqrt(np.maximum(var, 0))
        inside = (w1 >= 0) & (w1 <= 1)
        ax.plot(100 * vol[inside], 100 * mean[inside], color=color, lw=2, label=f"rho={rho:+.1f}")
        ax.plot(100 * vol[w1 < 0], 100 * mean[w1 < 0], color=color, lw=1, ls="--")
        ax.plot(100 * vol[w1 > 1], 100 * mean[w1 > 1], color=color, lw=1, ls="--")
        rows[f"{rho:+.1f}"] = float(vol[inside].min())
    ax.scatter(100 * TWO_SIGMA, 100 * TWO_MU, color="black", zorder=5)
    for s, m, name in zip(TWO_SIGMA, TWO_MU, ("asset 1", "asset 2")):
        ax.annotate(name, (100 * s, 100 * m), textcoords="offset points", xytext=(6, -10), fontsize=8)
    ax.set_xlabel("portfolio volatility (annual, %)")
    ax.set_ylabel("expected return (annual, %)")
    ax.set_title("Two constructed assets: correlation bends the risk-return curve")
    ax.set_xlim(0, 36)
    ax.legend(fontsize=8, ncol=3)
    ax.text(0.01, 0.01, "solid: 0<=w1<=1 (long only); dashed: one asset shorted", transform=ax.transAxes, fontsize=8)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return {"min_long_only_volatility_by_rho": rows}


def plot_frontier_cml(path: Path) -> dict[str, Any]:
    cov = cov_from(THREE_SIGMA, THREE_CORR)
    k = frontier_constants(THREE_MU, cov)
    targets = np.linspace(0.0, 0.16, 400)
    vol = np.sqrt(frontier_variance(targets, k))
    gmv_mean = k["B"] / k["A"]
    tangent = tangency_weights(THREE_MU, cov, risk_free_return=THREE_RF)
    tm = portfolio_moments(tangent, THREE_MU, cov)
    sharpe = (tm.expected_return - THREE_RF) / tm.volatility
    lo = long_only_frontier(THREE_MU, cov)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.plot(100 * vol[targets >= gmv_mean], 100 * targets[targets >= gmv_mean], color="#1b4f72", lw=2,
            label="efficient branch (shorts allowed)")
    ax.plot(100 * vol[targets < gmv_mean], 100 * targets[targets < gmv_mean], color="#1b4f72", lw=1.2, ls=":",
            label="inefficient branch (mean below GMV)")
    ax.plot(100 * lo[:, 0], 100 * lo[:, 1], color="#ca6f1e", lw=2, label="long-only efficient (Ch9 QP)")
    xs = np.linspace(0, 30, 50)
    ax.plot(xs, 100 * THREE_RF + sharpe * xs, color="#922b21", lw=1.3, label="optimal capital allocation line (RF borrow=lend)")
    ax.scatter([100 / np.sqrt(k["A"])], [100 * gmv_mean], color="#1b4f72", zorder=5)
    ax.annotate("GMV", (100 / np.sqrt(k["A"]), 100 * gmv_mean), xytext=(6, -10), textcoords="offset points", fontsize=8)
    ax.scatter([100 * tm.volatility], [100 * tm.expected_return], color="#922b21", zorder=5)
    ax.annotate("tangency", (100 * tm.volatility, 100 * tm.expected_return), xytext=(6, -10), textcoords="offset points", fontsize=8)
    ax.scatter(100 * THREE_SIGMA, 100 * THREE_MU, color="black", zorder=5)
    ax.set_xlim(0, 32); ax.set_ylim(0, 16)
    ax.set_xlabel("volatility (annual, %)"); ax.set_ylabel("expected return (annual, %)")
    ax.set_title("Constructed 3-asset moments: frontier, GMV, tangency and CAL")
    ax.legend(fontsize=8, loc="upper left")
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return {"constants": k, "gmv_mean": gmv_mean, "gmv_volatility": 1 / np.sqrt(k["A"]),
            "tangency_weights": tangent.tolist(), "tangency_mean": tm.expected_return,
            "tangency_volatility": tm.volatility, "tangency_sharpe": sharpe,
            "long_only_points": int(len(lo))}


def french_windows(returns: pd.DataFrame, rf: pd.Series) -> tuple[dict[str, Any], pd.DataFrame]:
    summary: dict[str, Any] = {}
    rows = []
    for label, (start, end) in WINDOWS.items():
        window = returns.loc[start:end]
        if len(window) != 120:
            raise ValueError(f"window {label} must contain 120 months")
        mu = window.mean().to_numpy()
        cov = window.cov().to_numpy()  # ddof=1 sample covariance, monthly decimal^2
        rf_mean = float(rf.loc[start:end].mean())
        gmv = global_minimum_variance_weights(cov)
        tangent = tangency_weights(mu, cov, risk_free_return=rf_mean)
        # Zero means make this long-only minimum variance. Rescaling Sigma leaves the
        # weights unchanged but keeps the solver's absolute tolerances meaningful:
        # unscaled monthly variances (~1e-3) failed the Ch9 residual check.
        lo = solve_mean_variance(np.zeros(mu.size), cov / np.max(np.abs(cov)))
        k = frontier_constants(mu, cov)
        t_m = portfolio_moments(tangent, mu, cov)
        summary[label] = {
            "months": int(len(window)), "mean_rf_monthly": rf_mean,
            "gmv_monthly_volatility": float(np.sqrt(1 / k["A"])),
            "gmv_monthly_mean": k["B"] / k["A"],
            "tangency_in_sample_monthly_sharpe": float((t_m.expected_return - rf_mean) / t_m.volatility),
            "tangency_gross_exposure": float(np.abs(tangent).sum()),
            "tangency_max_abs_weight": float(np.abs(tangent).max()),
            "long_only_min_variance_volatility": float(np.sqrt(lo.weights @ cov @ lo.weights)),
            "condition_number": float(np.linalg.cond(cov)),
        }
        for name, w in (("gmv", gmv), ("tangency", tangent), ("long_only_min_var", lo.weights)):
            rows.append(pd.Series(w, index=returns.columns, name=f"{label}:{name}"))
    return summary, pd.DataFrame(rows)


def plot_french(path: Path, returns: pd.DataFrame, rf: pd.Series) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True)
    for ax, (label, (start, end)) in zip(axes, WINDOWS.items()):
        window = returns.loc[start:end]
        mu, cov = window.mean().to_numpy(), window.cov().to_numpy()
        rf_mean = float(rf.loc[start:end].mean())
        k = frontier_constants(mu, cov)
        targets = np.linspace(-0.005, 0.03, 300)
        vol = np.sqrt(frontier_variance(targets, k))
        gmv_mean = k["B"] / k["A"]
        eff = targets >= gmv_mean
        ax.plot(100 * vol[eff], 100 * targets[eff], color="#1b4f72", lw=2, label="estimated frontier, shorts")
        ax.plot(100 * vol[~eff], 100 * targets[~eff], color="#1b4f72", ls=":", lw=1)
        lo = long_only_frontier(mu, cov, n=30)
        ax.plot(100 * lo[:, 0], 100 * lo[:, 1], color="#ca6f1e", lw=2, label="estimated long-only frontier")
        ax.scatter(100 * window.std().to_numpy(), 100 * mu, color="black", s=12)
        for name, s, m in zip(returns.columns, window.std(), mu):
            ax.annotate(name, (100 * s, 100 * m), fontsize=6, xytext=(2, 2), textcoords="offset points")
        sharpe = np.sqrt(k["C"] - 2 * rf_mean * k["B"] + rf_mean ** 2 * k["A"])
        xs = np.linspace(0, 9, 30)
        ax.plot(xs, 100 * rf_mean + sharpe * xs, color="#922b21", lw=1, label="in-sample tangency line")
        ax.set_title(f"French 10 industries, {label} (120 months)", fontsize=9)
        ax.set_xlabel("monthly volatility (%)")
        ax.set_xlim(0, 9); ax.set_ylim(-0.5, 3.0)
    axes[0].set_ylabel("monthly mean return (%)")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("Estimated frontiers from sample moments: descriptive, not out-of-sample", fontsize=10)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def run(output_dir: Path, figure_dir: Path, *, overwrite: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    targets = [output_dir / n for n in OUTPUTS] + [figure_dir / n for n in FIGURES]
    if any(p.exists() for p in targets) and not overwrite:
        raise FileExistsError("Refusing to overwrite Chapter 20 artifacts; pass --overwrite")
    returns, rf, provenance = load_industries_and_rf()
    result: dict[str, Any] = {"two_asset": two_asset_example()}
    result["two_asset_figure"] = plot_two_asset(figure_dir / FIGURES[0])
    result["three_asset"] = plot_frontier_cml(figure_dir / FIGURES[1])
    french, weights = french_windows(returns, rf)
    plot_french(figure_dir / FIGURES[2], returns, rf)
    result["french_windows"] = french
    result["provenance"] = provenance
    weights.to_csv(output_dir / OUTPUTS[1], float_format="%.8f")
    (output_dir / OUTPUTS[0]).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch20_portfolio_theory_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=default_run / "results")
    parser.add_argument("--figure-dir", type=Path, default=default_run / "figures")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = run(args.output_dir, args.figure_dir, overwrite=args.overwrite)
    print(json.dumps({k: result[k] for k in ("two_asset", "french_windows")}, indent=1))


if __name__ == "__main__":
    main()
