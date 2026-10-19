"""Project 3: rolling out-of-sample comparison of four long-only portfolios.

Timing contract (idealized month boundaries on a current-revision snapshot):
* month label t = simple return over calendar month t;
* decision and trade for holding month t occur at the end of month t-1 using
  only the W months [t-lag-W, t-lag-1]; with lag=0 this assumes month t-1's
  return is known at its own month end, which French publication timing does
  not provide historically (the snapshot is not point-in-time);
* trades fill at the end of month t-1 at the prices implied by the returns,
  then the portfolio is held through month t without intra-month trading;
* the weight-change proxy fee = c * sum|target - pre-trade weights| is
  taken from NAV before holding returns (not an exact traded-notional model),
  so net return = (1 - cost)(1 + gross) - 1; weights then drift with returns.
No cash, borrowing or shorting. RF is used only to form excess returns.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_course.french_frozen import load_industries_and_rf
from quant_course.optimization_tools import OptimizationError, solve_mean_variance
from quant_course.performance import cagr, drawdown_path, sharpe_ratio, wealth_index
from quant_course.portfolio_construction import (
    drift_weights, ledoit_wolf_identity, max_sharpe_long_only,
    risk_budget_weights, risk_contributions, turnover,
)
from quant_course.statistics_tools import (
    bootstrap_mean_confidence_interval, moving_block_bootstrap_mean_draws,
)

PROJECT = Path(__file__).resolve().parents[1]
STRATEGIES = ("equal_weight", "min_variance", "max_sharpe", "erc")


@dataclass(frozen=True)
class Spec:
    window: int = 60
    covariance: str = "ledoit_wolf"
    max_weight: float = 0.4
    lag: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.window, (bool, np.bool_)) or not isinstance(self.window, (int, np.integer)) or self.window < 2:
            raise ValueError("window must be an integer >= 2")
        if isinstance(self.lag, (bool, np.bool_)) or not isinstance(self.lag, (int, np.integer)) or self.lag < 0:
            raise ValueError("lag must be a nonnegative integer")
        if self.covariance not in {"sample", "ledoit_wolf"}:
            raise ValueError("unknown covariance estimator")
        raw = np.asarray(self.max_weight)
        if raw.ndim != 0 or raw.dtype.kind not in "iuf" or not np.isfinite(raw) or not 0 < float(raw) <= 1:
            raise ValueError("max_weight must be a finite real scalar in (0, 1]")

    def label(self) -> str:
        return f"W{self.window}_{self.covariance}_lag{self.lag}"


def load_config(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or PROJECT / "configs/project03.json").read_text(encoding="utf-8"))


def estimate_covariance(window: np.ndarray, method: str) -> np.ndarray:
    if method == "sample":
        return np.atleast_2d(np.cov(window, rowvar=False, ddof=1))
    if method == "ledoit_wolf":
        return ledoit_wolf_identity(window).covariance
    raise ValueError(f"unknown covariance method {method!r}")


def target_weights(strategy: str, window_returns: np.ndarray, window_excess: np.ndarray,
                   spec: Spec) -> tuple[np.ndarray, str]:
    """Return (weights, status). Status 'ok' or 'fallback:<reason>' (equal weight)."""
    n = window_returns.shape[1]
    equal = np.full(n, 1.0 / n)
    if strategy == "equal_weight":
        return equal, "ok"
    cov = estimate_covariance(window_returns, spec.covariance)
    try:
        if strategy == "min_variance":
            # Zero means turn the Ch9 utility QP into minimum variance; rescaling
            # Sigma keeps the solver tolerances meaningful and leaves weights unchanged.
            result = solve_mean_variance(np.zeros(n), cov / np.max(np.abs(cov)), max_weight=spec.max_weight)
            return result.weights, "ok"
        if strategy == "max_sharpe":
            mean_excess = window_excess.mean(axis=0)
            return max_sharpe_long_only(mean_excess, cov, risk_free_return=0.0,
                                        max_weight=spec.max_weight).weights, "ok"
        if strategy == "erc":
            return risk_budget_weights(cov).weights, "ok"
    except (OptimizationError, ValueError, np.linalg.LinAlgError) as exc:
        return equal, f"fallback:{type(exc).__name__}:{exc}"
    raise ValueError(f"unknown strategy {strategy!r}")


def run_strategy(strategy: str, returns: pd.DataFrame, rf: pd.Series, spec: Spec,
                 start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly ledger and target weights for one strategy; costs are applied later."""
    if strategy not in STRATEGIES:
        raise ValueError("unknown strategy")
    if not isinstance(returns.index, pd.PeriodIndex) or returns.index.freqstr != "M":
        raise ValueError("returns require calendar-month PeriodIndex")
    if returns.empty or returns.shape[1] == 0 or returns.columns.has_duplicates:
        raise ValueError("returns must have nonempty unique asset columns")
    if not returns.index.equals(pd.period_range(returns.index[0], periods=len(returns), freq="M")):
        raise ValueError("return months must be unique, ordered and consecutive")
    if not isinstance(rf, pd.Series) or not rf.index.equals(returns.index):
        raise ValueError("RF must align exactly with the return months")
    for data in (returns.to_numpy(), rf.to_numpy()):
        if data.dtype.kind not in "iuf" or not np.isfinite(data).all() or (data <= -1).any():
            raise ValueError("returns and RF must be finite real simple returns greater than -1")
    if strategy in {"min_variance", "max_sharpe"} and spec.max_weight * returns.shape[1] < 1:
        raise ValueError("cap makes full investment, including the fallback, infeasible")
    if start not in returns.index or end not in returns.index:
        raise ValueError("evaluation bounds must exist in the monthly input")
    months = returns.loc[start:end].index
    if months.empty:
        raise ValueError("evaluation window must not be empty")
    values = returns.to_numpy()
    excess = (returns.sub(rf, axis=0)).to_numpy()
    position = {m: i for i, m in enumerate(returns.index)}
    pre = np.zeros(returns.shape[1])  # start in cash: first trade buys the whole portfolio
    rows, targets = [], []
    for month in months:
        i = position[month]
        first, last = i - spec.lag - spec.window, i - spec.lag - 1
        if first < 0:
            raise ValueError(f"not enough history before {month} for window {spec.window}")
        weights, status = target_weights(strategy, values[first:last + 1], excess[first:last + 1], spec)
        traded = turnover(pre, weights)
        gross = float(weights @ values[i])
        decomposition = risk_contributions(weights, estimate_covariance(values[first:last + 1], spec.covariance))
        rows.append({
            "holding_month": str(month),
            "train_start": str(returns.index[first]), "train_end": str(returns.index[last]),
            "decision_at": f"end of {returns.index[i - 1]}",
            "information_cutoff": str(returns.index[last]),
            "trade_at": f"end of {returns.index[i - 1]}",
            "return_interval_start": f"end of {returns.index[i - 1]}",
            "return_interval_end": f"end of {month}",
            "pre_trade_cash_weight": 1.0 if not rows else 0.0,
            **{f"pre_weight_{name}": float(v) for name, v in zip(returns.columns, pre)},
            **{f"target_weight_{name}": float(v) for name, v in zip(returns.columns, weights)},
            "status": status, "turnover": traded, "gross_return": gross,
            "risk_free": float(rf.iloc[i]),
            "max_weight": float(weights.max()), "effective_n": float(1.0 / np.sum(weights ** 2)),
            "max_risk_fraction_ex_ante": float(decomposition.fractions.max()),
        })
        targets.append(pd.Series(weights, index=returns.columns, name=str(month)))
        pre = drift_weights(weights, values[i])
    return pd.DataFrame(rows), pd.DataFrame(targets)


def apply_costs(ledger: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    raw = np.asarray(cost_bps)
    if raw.ndim != 0 or raw.dtype.kind not in "iuf" or not np.isfinite(raw) or float(raw) < 0:
        raise ValueError("cost_bps must be a finite nonnegative real scalar")
    out = ledger.copy()
    values = out[["turnover", "gross_return", "risk_free"]].to_numpy()
    if values.dtype.kind not in "iuf" or not np.isfinite(values).all() or (out["turnover"] < 0).any() or (out["gross_return"] <= -1).any():
        raise ValueError("ledger needs finite nonnegative turnover and valid simple returns")
    c = float(raw) / 10_000
    out["cost"] = c * out["turnover"]
    if (out["cost"] >= 1).any():
        raise ValueError("fees exhaust portfolio NAV")
    out["net_return"] = (1 - out["cost"]) * (1 + out["gross_return"]) - 1
    out["net_excess"] = out["net_return"] - out["risk_free"]
    return out


def metrics(ledger: pd.DataFrame, *, includes_initial_purchase: bool = True) -> dict[str, float]:
    """Summary statistics. Average turnover drops row 0 only when it is the initial purchase from cash."""
    net = ledger["net_return"].to_numpy()
    rf = ledger["risk_free"].to_numpy()
    wealth = wealth_index(net)
    years = len(net) / 12
    return {
        "months": int(len(net)),
        "ann_mean_net_excess": float(12 * (net - rf).mean()),
        "ann_vol_net": float(np.sqrt(12) * np.std(net, ddof=1)),
        "sharpe_net_ann": sharpe_ratio(net, rf, 12),
        "sharpe_gross_ann": sharpe_ratio(ledger["gross_return"].to_numpy(), rf, 12),
        "cagr_net": cagr(1.0, float(wealth[-1]), years),
        "max_drawdown_net": float(drawdown_path(wealth).min()),
        "avg_monthly_turnover": float(ledger["turnover"].iloc[1 if includes_initial_purchase else 0:].mean()),
        "ann_mean_fee": float(12 * ledger["cost"].mean()),
        "ann_cost_drag": float(12 * (ledger["gross_return"] - ledger["net_return"]).mean()),
        "avg_max_weight": float(ledger["max_weight"].mean()),
        "avg_effective_n": float(ledger["effective_n"].mean()),
        "avg_max_risk_fraction": float(ledger["max_risk_fraction_ex_ante"].mean()),
        "fallbacks": int((ledger["status"] != "ok").sum()),
    }


def bootstrap_difference(strategy: pd.DataFrame, benchmark: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, float]:
    diff = strategy["net_return"].to_numpy() - benchmark["net_return"].to_numpy()
    draws = moving_block_bootstrap_mean_draws(
        diff, block_length=cfg["block_length"], n_resamples=cfg["resamples"],
        rng=np.random.default_rng(cfg["seed"]))
    ci = bootstrap_mean_confidence_interval(draws, confidence_level=cfg["confidence"])
    return {"mean_monthly_difference": float(diff.mean()), "ci_lower": ci.lower, "ci_upper": ci.upper,
            "share_of_draws_above_zero": float((draws > 0).mean())}


def bootstrap_sharpe_difference(strategy: pd.DataFrame, benchmark: pd.DataFrame,
                                cfg: dict[str, Any]) -> dict[str, float]:
    """Paired circular block bootstrap of annualized net Sharpe difference.

    The same resampled month indices are applied to both return series so
    their cross-correlation is kept. Same block length and seed as the mean test.
    """
    if len(strategy) < 2 or len(strategy) != len(benchmark):
        raise ValueError("paired Sharpe bootstrap needs equal series lengths >= 2")
    if not np.array_equal(strategy["holding_month"].to_numpy(), benchmark["holding_month"].to_numpy()):
        raise ValueError("paired bootstrap months must match exactly")
    block, repetitions = cfg["block_length"], cfg["resamples"]
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) for v in (block, repetitions)) or not 1 <= block <= len(strategy) or repetitions < 2:
        raise ValueError("bootstrap needs integer block length in [1,n] and resamples >= 2")
    confidence = cfg["confidence"]
    raw_confidence = np.asarray(confidence)
    if raw_confidence.ndim != 0 or raw_confidence.dtype.kind not in "iuf" or not np.isfinite(raw_confidence) or not 0 < float(raw_confidence) < 1:
        raise ValueError("confidence must be a finite real scalar in (0,1)")
    a = strategy["net_return"].to_numpy() - strategy["risk_free"].to_numpy()
    b = benchmark["net_return"].to_numpy() - benchmark["risk_free"].to_numpy()
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("bootstrap excess returns must be finite")
    if np.std(a, ddof=1) == 0 or np.std(b, ddof=1) == 0:
        raise ValueError("Sharpe is undefined for constant excess returns")
    n, block = a.size, cfg["block_length"]
    rng = np.random.default_rng(cfg["seed"])
    starts = rng.integers(0, n, size=(cfg["resamples"], int(np.ceil(n / block))))
    index = ((starts[..., None] + np.arange(block)) % n).reshape(cfg["resamples"], -1)[:, :n]
    def sr(x: np.ndarray) -> np.ndarray:
        deviation = x.std(axis=-1, ddof=1)
        if (deviation <= 0).any():
            raise ValueError("a resample has zero excess-return variance; Sharpe interval is undefined")
        return np.sqrt(12) * x.mean(axis=-1) / deviation
    draws = sr(a[index]) - sr(b[index])
    tail = (1 - cfg["confidence"]) / 2
    lower, upper = np.quantile(draws, [tail, 1 - tail])
    return {"sharpe_difference": float(sr(a) - sr(b)), "ci_lower": float(lower), "ci_upper": float(upper),
            "share_of_draws_above_zero": float((draws > 0).mean())}


def hindsight_max_sharpe(returns: pd.DataFrame, rf: pd.Series, start: str, end: str, cap: float) -> dict[str, Any]:
    """Look-ahead benchmark: max-Sharpe weights fitted on the whole evaluation period.

    Not tradable. It shows how much in-sample optimization overstates what the
    rolling procedure could achieve with the same constraints.
    """
    sample = returns.loc[start:end]
    excess = sample.sub(rf.loc[start:end], axis=0)
    result = max_sharpe_long_only(excess.mean().to_numpy(), sample.cov().to_numpy(),
                                  risk_free_return=0.0, max_weight=cap)
    realized_gross = sample.to_numpy() @ result.weights
    rf_values = rf.loc[start:end].to_numpy()
    realized_sharpe = sharpe_ratio(realized_gross, rf_values, 12)
    return {"weights": dict(zip(returns.columns, np.round(result.weights, 6))),
            "moment_objective_monthly_sharpe": result.sharpe,
            "moment_objective_annualized_sharpe": result.sharpe * np.sqrt(12),
            "in_sample_monthly_sharpe": realized_sharpe / np.sqrt(12),
            "in_sample_annualized_sharpe": realized_sharpe,
            "cost_bps": 0,
            "interpretation": "fixed-weight gross sample fit; not tradable or an isolated estimate of look-ahead bias"}


def run_all(cfg: dict[str, Any]) -> dict[str, Any]:
    returns, rf, provenance = load_industries_and_rf()
    start, end = cfg["evaluation"]["start"], cfg["evaluation"]["end"]
    primary = cfg["primary"]
    base = Spec(primary["window_months"], primary["covariance"], primary["max_weight"],
                primary["implementation_lag_months"])
    specs = {base.label(): base}
    sens = cfg["sensitivity"]
    for w in sens["window_months"]:
        for cov in sens["covariance"]:
            for lag in sens["implementation_lag_months"]:
                s = Spec(w, cov, primary["max_weight"], lag)
                specs.setdefault(s.label(), s)
    ledgers: dict[str, dict[str, pd.DataFrame]] = {}
    weights: dict[str, dict[str, pd.DataFrame]] = {}
    for label, spec in specs.items():
        ledgers[label], weights[label] = {}, {}
        for strategy in STRATEGIES:
            ledgers[label][strategy], weights[label][strategy] = run_strategy(strategy, returns, rf, spec, start, end)
    table = []
    for label, by_strategy in ledgers.items():
        for strategy, ledger in by_strategy.items():
            for bps in sens["cost_bps_per_unit_traded"]:
                row = {"spec": label, "strategy": strategy, "cost_bps": bps,
                       **metrics(apply_costs(ledger, bps))}
                table.append(row)
    primary_label, primary_bps = base.label(), primary["cost_bps_per_unit_traded"]
    primary_ledgers = {s: apply_costs(l, primary_bps) for s, l in ledgers[primary_label].items()}
    subperiods = []
    for a, b in cfg["subperiods"]:
        for s, l in primary_ledgers.items():
            part = l[(l["holding_month"] >= a) & (l["holding_month"] <= b)]
            subperiods.append({"period": f"{a}..{b}", "strategy": s,
                               **metrics(part, includes_initial_purchase=(a == start))})
    boot = {s: {**bootstrap_difference(primary_ledgers[s], primary_ledgers["equal_weight"], cfg["bootstrap"]),
                "sharpe": bootstrap_sharpe_difference(primary_ledgers[s], primary_ledgers["equal_weight"], cfg["bootstrap"])}
            for s in STRATEGIES if s != "equal_weight"}
    return {
        "provenance": provenance, "config": cfg, "primary_spec": primary_label,
        "ledgers": ledgers, "weights": weights, "primary_ledgers": primary_ledgers,
        "sensitivity": pd.DataFrame(table), "subperiods": pd.DataFrame(subperiods),
        "bootstrap_vs_equal_weight": boot,
        "hindsight": hindsight_max_sharpe(returns, rf, start, end, primary["max_weight"]),
        "fallback_log": [
            {"spec": label, "strategy": s, "holding_month": r.holding_month, "status": r.status}
            for label, by in ledgers.items() for s, l in by.items()
            for r in l.itertuples() if r.status != "ok"
        ],
    }
