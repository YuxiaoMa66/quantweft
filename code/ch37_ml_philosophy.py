"""Chapter 37 teaching computations: prediction accuracy versus decision value.

All inputs are constructed teaching data (``data_class = CONSTRUCTED``); nothing here is market evidence.

Time convention for the ten-day case: the direction forecast for day t is formed after the close of day t-1
(``signal_time``), the position is entered at the open of day t (``trade_time``), and ``r_t`` is the simple
open-to-open return from day t to day t+1 (``return interval``). Positions are -1, 0 or +1 units of wealth.
Cost is ``cost_per_unit`` (decimal of wealth) per unit of |position change|; the initial entry from 0 is
charged, the final open position is not liquidated.

Run:  .venv/bin/python code/ch37_ml_philosophy.py --out build/batches/A8-A/r1/runs/<run-id>/cli
Writes ``ch37_results.json`` to --out (refuses to overwrite) and the three chapter figures plus a copy of the
JSON into ``course/zh/chapters/ch37/figures``.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from quant_course.research_protocol import expected_max_standard_normal, expected_max_standard_normal_exact

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "runs" / "figures"

# Ten-day case, decimals (0.004 = 0.4%). Days 5 and 10 are the two large down days.
TEN_DAY_RETURNS = np.array([0.004, 0.003, -0.002, 0.005, -0.030, 0.004, 0.002, -0.001, 0.003, -0.025])
POSITIONS = {
    # Model B: right on every small day, wrong on both large down days ("80% accurate").
    "B_high_accuracy": np.array([1, 1, -1, 1, 1, 1, 1, -1, 1, 1]),
    # Model A: wrong on three small days, right on both large down days ("70% accurate").
    "A_lower_accuracy": np.array([1, 1, 1, 1, -1, -1, -1, -1, 1, -1]),
    "buy_and_hold": np.ones(10, dtype=int),
    "zero_position": np.zeros(10, dtype=int),
}
COST_PER_UNIT = 0.001  # 10 bp of wealth per unit of |position change|


def _checked(returns: np.ndarray, positions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    r = np.asarray(returns, dtype=float)
    p = np.asarray(positions, dtype=float)
    if r.ndim != 1 or r.shape != p.shape or r.size == 0:
        raise ValueError("returns and positions must be equal-length non-empty vectors")
    if not np.isfinite(r).all() or not np.isfinite(p).all():
        raise ValueError("returns and positions must be finite")
    if (r <= -1).any():
        raise ValueError("simple returns must exceed -100%")
    return r, p


def direction_accuracy(returns: np.ndarray, positions: np.ndarray) -> float:
    """Share of days with position != 0 whose sign matches the realised return sign (zero returns excluded)."""
    r, p = _checked(returns, positions)
    use = (p != 0) & (r != 0)
    if not use.any():
        return float("nan")
    return float((np.sign(p[use]) == np.sign(r[use])).mean())


def decision_ledger(returns: np.ndarray, positions: np.ndarray, cost_per_unit: float) -> dict[str, object]:
    """Daily gross/net returns, turnover and the N+1 wealth points of a +-1/0 position path.

    net_t = pos_t * r_t - cost_per_unit * |pos_t - pos_{t-1}|, with pos_0 = 0 before day 1.
    Wealth W_0 = 1 and W_t = W_{t-1} * (1 + net_t): N daily returns give N+1 wealth points.
    """
    r, p = _checked(returns, positions)
    if not np.isfinite(cost_per_unit) or cost_per_unit < 0:
        raise ValueError("cost_per_unit must be a finite non-negative decimal")
    turnover = np.abs(np.diff(np.concatenate([[0.0], p])))
    gross = p * r
    net = gross - cost_per_unit * turnover
    if (net <= -1).any():
        raise ValueError("a daily loss of 100% or more ends the path")
    wealth = np.concatenate([[1.0], np.cumprod(1.0 + net)])
    return {
        "gross": gross, "net": net, "turnover": turnover, "wealth": wealth,
        "sum_gross": float(gross.sum()), "sum_cost": float(cost_per_unit * turnover.sum()),
        "total_turnover": float(turnover.sum()), "final_wealth": float(wealth[-1]),
    }


def magnitude_identity(returns: np.ndarray, positions: np.ndarray) -> dict[str, float]:
    """For +-1 positions: sum(pos*r) = sum(|r| * (2*correct - 1)). Accuracy weights days equally, PnL by |r|."""
    r, p = _checked(returns, positions)
    if not np.isin(p, (-1.0, 1.0)).all():
        raise ValueError("the identity is stated for +-1 positions")
    correct = (np.sign(p) == np.sign(r)).astype(float)
    return {
        "lhs_sum_pos_r": float((p * r).sum()),
        "rhs_abs_weighted": float((np.abs(r) * (2 * correct - 1)).sum()),
        "accuracy": float(correct.mean()),
        "magnitude_weighted_accuracy": float((np.abs(r) * correct).sum() / np.abs(r).sum()),
    }


def ten_day_case() -> dict[str, object]:
    out: dict[str, object] = {}
    for name, pos in POSITIONS.items():
        led = decision_ledger(TEN_DAY_RETURNS, pos, COST_PER_UNIT)
        row = {
            "positions": pos.tolist(),
            "accuracy": direction_accuracy(TEN_DAY_RETURNS, pos),
            "sum_gross": led["sum_gross"],
            "total_turnover": led["total_turnover"],
            "sum_cost": led["sum_cost"],
            "sum_net_approx": led["sum_gross"] - led["sum_cost"],
            "final_wealth_exact": led["final_wealth"],
            "compound_net_return_exact": led["final_wealth"] - 1.0,
            "wealth_points": led["wealth"].tolist(),
        }
        if np.isin(pos, (-1, 1)).all():
            row["identity"] = magnitude_identity(TEN_DAY_RETURNS, pos)
        out[name] = row
    return out


def overlap_autocorrelation(h: int, n_days: int, seed: int) -> dict[str, object]:
    """h-day overlapping sums of iid daily returns sampled daily: theory rho_k = (h-k)/h for k < h."""
    rng = np.random.default_rng(seed)
    daily = rng.normal(0.0, 0.01, n_days + h)
    overlap = np.convolve(daily, np.ones(h), mode="valid")[:n_days]
    x = overlap - overlap.mean()
    sample = [float((x[k:] @ x[:-k]) / (x @ x)) for k in range(1, h + 1)]
    theory = [(h - k) / h for k in range(1, h + 1)]
    # Variance of the mean of n overlapping labels relative to the iid formula (large-n limit):
    # sum_{k=-(h-1)}^{h-1} (h-|k|)/h = h, so the effective sample size is about n / h.
    return {"h": h, "n_days": n_days, "seed": seed, "sample_rho": sample, "theory_rho": theory,
            "variance_inflation_limit": float(h)}


def max_null_sharpe(n_strategies: tuple[int, ...], n_days: int, n_sims: int, seed: int) -> dict[str, object]:
    """Best annualised Sharpe among N zero-mean strategies, and what that best one does in a holdout.

    Each strategy's daily returns are iid N(0, 1%). Annualised Sharpe = sqrt(252) * mean / sd.
    Under the null the estimate is approximately N(0, 252 / n_days), so E[max] ~ sqrt(252/n_days) * E[max Z_N].
    """
    rng = np.random.default_rng(seed)
    rows = []
    for n in n_strategies:
        best_in, best_out = [], []
        for _ in range(n_sims):
            ins = rng.normal(0.0, 0.01, (n_days, n))
            outs = rng.normal(0.0, 0.01, (n_days, n))
            sr_in = np.sqrt(252) * ins.mean(0) / ins.std(0, ddof=1)
            k = int(np.argmax(sr_in))
            best_in.append(float(sr_in[k]))
            best_out.append(float(np.sqrt(252) * outs[:, k].mean() / outs[:, k].std(ddof=1)))
        scale = np.sqrt(252 / n_days)
        approx = scale * (expected_max_standard_normal(n) if n >= 2 else 0.0)
        exact = scale * expected_max_standard_normal_exact(n)
        rows.append({"n_strategies": n, "mean_best_in_sample": float(np.mean(best_in)),
                     "mean_holdout_of_selected": float(np.mean(best_out)),
                     "formula_bailey_lopez_de_prado": float(approx), "formula_exact_quadrature": float(exact),
                     "best_in_sample_draws": best_in, "holdout_draws": best_out})
    return {"n_days": n_days, "n_sims": n_sims, "seed": seed, "rows": rows}


def regime_shift(n_per_regime: int, slope: float, seed: int) -> dict[str, object]:
    """y = b_t x + e with b = +slope in regime 1 and -slope in regime 2; train OLS on regime 1 only.

    Out-of-sample R^2 against the zero forecast: R2_OS = 1 - SSE_model / sum(y^2) on regime 2.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, 2 * n_per_regime)
    e = rng.normal(0.0, 1.0, 2 * n_per_regime)
    b = np.where(np.arange(2 * n_per_regime) < n_per_regime, slope, -slope)
    y = b * x + e
    tr, te = slice(0, n_per_regime), slice(n_per_regime, None)
    xt, yt = x[tr], y[tr]
    beta = float(((xt - xt.mean()) @ (yt - yt.mean())) / ((xt - xt.mean()) @ (xt - xt.mean())))
    alpha = float(yt.mean() - beta * xt.mean())
    pred = alpha + beta * x[te]
    y2 = y[te]
    r2_os_zero = float(1 - ((y2 - pred) ** 2).sum() / (y2 ** 2).sum())
    r2_in = float(1 - ((yt - alpha - beta * xt) ** 2).sum() / ((yt - yt.mean()) ** 2).sum())
    window = 250
    rolling = [float(np.polyfit(x[i - window:i], y[i - window:i], 1)[0]) for i in range(window, 2 * n_per_regime + 1, 25)]
    return {"n_per_regime": n_per_regime, "true_slope_regime1": slope, "true_slope_regime2": -slope,
            "population_r2_each_regime": slope ** 2 / (slope ** 2 + 1.0), "seed": seed,
            "train_beta": beta, "train_alpha": alpha, "in_sample_r2": r2_in, "oos_r2_vs_zero_regime2": r2_os_zero,
            "rolling_window": window, "rolling_beta": rolling}


def build_figures(case: dict, regime: dict, mt: dict) -> list[str]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    # Figure 37-1: wealth paths of the ten-day case.
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    styles = {"A_lower_accuracy": ("#247F82", "A: 70% accurate"), "B_high_accuracy": ("#C0504D", "B: 80% accurate"),
              "buy_and_hold": ("#7F7F7F", "Buy and hold"), "zero_position": ("#BBBBBB", "Zero position")}
    for name, (color, label) in styles.items():
        w = case[name]["wealth_points"]
        ax.plot(range(len(w)), w, marker="o", ms=4, lw=2, color=color,
                label=f"{label} (net {100 * case[name]['compound_net_return_exact']:+.2f}%)")
    for d in (5, 10):
        ax.axvspan(d - 0.5, d + 0.5, color="#F2DCDB", alpha=0.6, lw=0)
    ax.set_xlabel("Wealth point t (0 = start; point t is after day t's open-to-open return)")
    ax.set_ylabel("Wealth (start = 1.0), after 10 bp per unit turnover")
    ax.set_title("Constructed 10-day case: higher hit rate, lower net wealth")
    ax.grid(axis="y", color="#dddddd", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.text(0.01, 0.01, "Shaded: days 5 and 10 (returns -3.0% and -2.5%). CONSTRUCTED teaching data, not market evidence.",
             fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = FIG_DIR / "fig37_1_decision_case.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    paths.append(p)
    # Figure 37-2: rolling slope through a regime change.
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    n, step, win = regime["n_per_regime"], 25, regime["rolling_window"]
    ends = list(range(win, 2 * n + 1, step))
    ax.plot(ends, regime["rolling_beta"], color="#247F82", lw=2, label=f"Rolling OLS slope ({win} obs)")
    ax.step([0, n, 2 * n], [regime["true_slope_regime1"], regime["true_slope_regime2"], regime["true_slope_regime2"]],
            where="post", color="#C0504D", lw=1.6, ls="--", label="True slope")
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axvline(n, color="#999999", lw=0.8, ls=":")
    ax.set_xlabel("Observation index at window end")
    ax.set_ylabel("Slope (units of y per unit of x)")
    ax.set_title(f"Regime shift: trained slope {regime['train_beta']:+.3f}, regime-2 R2_OS vs zero "
                 f"{100 * regime['oos_r2_vs_zero_regime2']:+.2f}%")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.text(0.01, 0.01, "CONSTRUCTED: x, e ~ N(0,1) iid; population R2 in each regime "
             f"{100 * regime['population_r2_each_regime']:.2f}%.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = FIG_DIR / "fig37_2_regime_shift.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    paths.append(p)
    # Figure 37-3: max null Sharpe vs number of strategies and the selected strategy's holdout.
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    ns = [r["n_strategies"] for r in mt["rows"]]
    axes[0].plot(ns, [r["mean_best_in_sample"] for r in mt["rows"]], "o-", color="#C0504D", label="Simulated mean of best in-sample")
    axes[0].plot(ns, [r["formula_exact_quadrature"] for r in mt["rows"]], "s--", color="#444444", ms=4,
                 label="sqrt(252/T) x E[max of N normals]")
    axes[0].plot(ns, [r["mean_holdout_of_selected"] for r in mt["rows"]], "^-", color="#247F82", label="Same strategy, holdout")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Number of zero-mean strategies tried (N, log scale)")
    axes[0].set_ylabel("Annualised Sharpe ratio")
    axes[0].legend(frameon=False, fontsize=7.5)
    axes[0].spines[["top", "right"]].set_visible(False)
    last = mt["rows"][-1]
    axes[1].scatter(last["best_in_sample_draws"], last["holdout_draws"], s=10, color="#247F82", alpha=0.6)
    axes[1].axhline(0, color="#999999", lw=0.8)
    axes[1].set_xlabel(f"Best in-sample Sharpe among N={last['n_strategies']}")
    axes[1].set_ylabel("Holdout Sharpe of that strategy")
    axes[1].spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Selection without true signal: T={mt['n_days']} days per sample, {mt['n_sims']} simulations", fontsize=10)
    fig.text(0.01, 0.01, "CONSTRUCTED: daily returns iid N(0, 1%), all true Sharpe ratios are 0.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    p = FIG_DIR / "fig37_3_max_sharpe.png"
    fig.savefig(p, dpi=200)
    plt.close(fig)
    paths.append(p)
    return [str(x.relative_to(FIG_DIR.parent)) for x in paths]


def main() -> None:
    global FIG_DIR
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True, help="fresh run directory for ch37_results.json")
    args = ap.parse_args()
    FIG_DIR = args.out.resolve() / "figures"
    out = args.out / "ch37_results.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    args.out.mkdir(parents=True, exist_ok=True)
    case = ten_day_case()
    regime = regime_shift(n_per_regime=1000, slope=0.1, seed=3701)
    mt = max_null_sharpe((1, 10, 100, 1000), n_days=504, n_sims=200, seed=3702)
    overlap = overlap_autocorrelation(h=5, n_days=100_000, seed=3703)
    results = {"chapter": 37, "data_class": "CONSTRUCTED", "cost_per_unit": COST_PER_UNIT,
               "ten_day_returns": TEN_DAY_RETURNS.tolist(), "ten_day_case": case, "regime_shift": regime,
               "multiple_testing": mt, "overlap": overlap}
    results["figures"] = build_figures(case, regime, mt)
    text = json.dumps(results, indent=1)
    out.write_text(text, encoding="utf-8")
    (FIG_DIR / "ch37_results.json").write_text(text, encoding="utf-8")
    for name in ("A_lower_accuracy", "B_high_accuracy", "buy_and_hold"):
        r = case[name]
        print(f"{name}: accuracy {r['accuracy']:.2f}, gross {r['sum_gross']:+.4f}, turnover {r['total_turnover']:.0f}, "
              f"net(approx) {r['sum_net_approx']:+.4f}, net(exact) {r['compound_net_return_exact']:+.6f}")
    print(f"regime: train beta {regime['train_beta']:+.4f}, R2_OS vs zero {regime['oos_r2_vs_zero_regime2']:+.4f}")
    for r in mt["rows"]:
        print(f"N={r['n_strategies']}: best in-sample {r['mean_best_in_sample']:.3f}, formula {r['formula_exact_quadrature']:.3f}, "
              f"holdout {r['mean_holdout_of_selected']:+.3f}")
    print(f"overlap rho sample {np.round(overlap['sample_rho'], 3).tolist()} theory {overlap['theory_rho']}")


if __name__ == "__main__":
    main()
