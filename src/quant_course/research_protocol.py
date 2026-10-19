"""Research-protocol tools for Chapter 22: frozen plans, trial ledgers, multiple-testing adjustments.

None of this proves that a plan was written *before* the data were looked at. A SHA-256
of a plan file plus the local clock is tamper evidence inside one working directory; only
an external, independently timestamped registry (or a collaborator's record) gives
evidence about timing.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy import integrate, stats

__all__ = [
    "ResearchPlan", "FrozenPlan", "freeze_plan", "TrialLedger", "bonferroni_adjust", "holm_adjust",
    "benjamini_hochberg_adjust", "expected_max_standard_normal", "expected_max_standard_normal_exact",
    "split_discovery_holdout", "pad_untested_attempts",
]

_EULER_GAMMA = 0.5772156649015329


@dataclass(frozen=True)
class ResearchPlan:
    """Everything that must be fixed before the test sample is evaluated."""
    hypothesis: str                      # economic claim, with sign of the expected effect
    universe: str
    data_sources: tuple[str, ...]
    discovery_start: str                 # ISO month/date; inclusive
    discovery_end: str
    holdout_start: str                   # strictly after discovery_end; untouched until the plan is frozen
    holdout_end: str
    signal_definition: str
    label_definition: str
    portfolio_rule: str
    benchmark: str
    primary_metric: str                  # ONE metric that decides the primary conclusion
    decision_rule: str                   # numerical threshold and what happens on failure
    cost_assumption: str
    trial_budget: int                    # maximum number of variants the team will look at
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("hypothesis", "universe", "signal_definition", "label_definition", "portfolio_rule",
                     "benchmark", "primary_metric", "decision_rule", "cost_assumption"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be filled before freezing")
        if (not self.data_sources or isinstance(self.data_sources, str)
                or not all(isinstance(item, str) and item.strip() for item in self.data_sources)):
            raise ValueError("data_sources must be a tuple of non-empty strings")
        if isinstance(self.trial_budget, bool) or not isinstance(self.trial_budget, int) or self.trial_budget < 1:
            raise ValueError("trial_budget must be a positive integer")
        starts = [pd.Period(self.discovery_start, "M"), pd.Period(self.discovery_end, "M"),
                  pd.Period(self.holdout_start, "M"), pd.Period(self.holdout_end, "M")]
        if not (starts[0] <= starts[1] < starts[2] <= starts[3]):
            raise ValueError("require discovery_start <= discovery_end < holdout_start <= holdout_end")


@dataclass(frozen=True)
class FrozenPlan:
    plan: ResearchPlan
    sha256: str
    frozen_at_local: str                 # local clock; NOT an external timestamp


def _canonical_json(plan: ResearchPlan) -> str:
    data = asdict(plan)
    data["data_sources"] = list(data["data_sources"])
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def freeze_plan(plan: ResearchPlan, *, now: datetime | None = None) -> FrozenPlan:
    """Hash the canonical JSON of the plan. Any later edit changes the hash."""
    stamp = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    return FrozenPlan(plan, hashlib.sha256(_canonical_json(plan).encode("utf-8")).hexdigest(), stamp)


@dataclass
class TrialLedger:
    """Append-only record of every specification evaluated, including the ones later abandoned."""
    rows: list[dict[str, Any]] = field(default_factory=list)

    def record(self, spec: Mapping[str, Any], *, metric: float, n_obs: int, status: str = "run",
               note: str = "") -> int:
        if status not in ("primary", "run", "abandoned"):
            raise ValueError("status must be primary, run or abandoned")
        if isinstance(n_obs, bool) or not isinstance(n_obs, (int, np.integer)) or int(n_obs) < 0:
            raise ValueError("n_obs must be a non-negative integer")
        if isinstance(metric, bool) or not isinstance(metric, (int, float, np.floating, np.integer)) or math.isinf(metric):
            raise ValueError("metric must be a finite real number or NaN (an undefined result is still a trial)")
        spec_key = json.dumps(dict(spec), sort_keys=True, default=str)
        trial_id = len(self.rows) + 1
        self.rows.append({"trial_id": trial_id, "spec": spec_key, "metric": float(metric), "n_obs": int(n_obs),
                          "status": status, "note": note})
        return trial_id

    @property
    def n_trials(self) -> int:
        """Every record counts: duplicates and abandoned runs are still looks at the data."""
        return len(self.rows)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


# ------------------------------------------------------ multiple testing
def _pvalues(values: object) -> np.ndarray:
    if isinstance(values, (list, tuple)) and any(isinstance(v, (bool, np.bool_)) for v in values):
        raise ValueError("p-values must not contain booleans")      # asarray([0.05, True]) would coerce silently
    p = np.asarray(values)
    if p.ndim != 1 or p.size == 0 or p.dtype.kind not in "iuf":
        raise ValueError("p-values must be a nonempty real 1-D array")
    p = p.astype(float)
    if np.isnan(p).any() or ((p < 0) | (p > 1)).any():
        raise ValueError("p-values must lie in [0, 1]")
    return p


def pad_untested_attempts(p_values: object, n_trials: int) -> np.ndarray:
    """Append ``p = 1`` for every ledger attempt that produced no p-value, so that the family size equals ``TrialLedger.n_trials``.

    An attempt with an undefined result still looked at the data; it can never be rejected, but it counts in the multiplier.
    """
    p = _pvalues(p_values)
    if isinstance(n_trials, bool) or not isinstance(n_trials, (int, np.integer)) or int(n_trials) < p.size:
        raise ValueError("n_trials must be an integer not smaller than the number of p-values")
    return np.concatenate([p, np.ones(int(n_trials) - p.size)])


def bonferroni_adjust(p_values: object) -> np.ndarray:
    """min(M p_i, 1): controls the family-wise error rate for any dependence among tests."""
    p = _pvalues(p_values)
    return np.minimum(p.size * p, 1.0)


def holm_adjust(p_values: object) -> np.ndarray:
    """Holm step-down adjusted p-values: p_(i)^adj = min(max_{j<=i} (M-j+1) p_(j), 1), returned in input order."""
    p = _pvalues(p_values)
    m = p.size
    order = np.argsort(p, kind="stable")
    stepped = np.maximum.accumulate((m - np.arange(m)) * p[order])
    adjusted = np.empty(m)
    adjusted[order] = np.minimum(stepped, 1.0)
    return adjusted


def benjamini_hochberg_adjust(p_values: object) -> np.ndarray:
    """Benjamini-Hochberg step-up adjusted p-values (valid for independent or positively dependent tests)."""
    p = _pvalues(p_values)
    m = p.size
    order = np.argsort(p, kind="stable")
    scaled = p[order] * m / (np.arange(m) + 1.0)
    stepped = np.minimum.accumulate(scaled[::-1])[::-1]
    adjusted = np.empty(m)
    adjusted[order] = np.minimum(stepped, 1.0)
    return adjusted


def expected_max_standard_normal(n_trials: int) -> float:
    """Bailey-Lopez de Prado (2014) approximation of E[max of N iid N(0,1)]:

    (1 - gamma) Phi^{-1}(1 - 1/N) + gamma Phi^{-1}(1 - 1/(N e)), gamma = Euler-Mascheroni.
    Requires N >= 2 (the approximation uses Phi^{-1}(1 - 1/N)).
    """
    if isinstance(n_trials, bool) or not isinstance(n_trials, (int, np.integer)) or n_trials < 2:
        raise ValueError("n_trials must be an integer >= 2")
    n = float(n_trials)
    return float((1 - _EULER_GAMMA) * stats.norm.ppf(1 - 1 / n) + _EULER_GAMMA * stats.norm.ppf(1 - 1 / (n * math.e)))


def expected_max_standard_normal_exact(n_trials: int) -> float:
    """E[max of N iid N(0,1)] = integral of x N phi(x) Phi(x)^{N-1} dx, by numerical quadrature."""
    if isinstance(n_trials, bool) or not isinstance(n_trials, (int, np.integer)) or n_trials < 1:
        raise ValueError("n_trials must be an integer >= 1")
    n = int(n_trials)
    value, _ = integrate.quad(lambda x: x * n * stats.norm.pdf(x) * stats.norm.cdf(x) ** (n - 1), -12, 12,
                              limit=200)
    return float(value)


def split_discovery_holdout(index: pd.PeriodIndex, plan: ResearchPlan) -> tuple[pd.PeriodIndex, pd.PeriodIndex]:
    """Return the discovery and holdout month labels of a monthly index; they never overlap."""
    if not isinstance(index, pd.PeriodIndex) or index.freqstr != "M":
        raise TypeError("index must be a monthly PeriodIndex")
    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError("index must be unique and increasing")
    d0, d1 = pd.Period(plan.discovery_start, "M"), pd.Period(plan.discovery_end, "M")
    h0, h1 = pd.Period(plan.holdout_start, "M"), pd.Period(plan.holdout_end, "M")
    discovery = index[(index >= d0) & (index <= d1)]
    holdout = index[(index >= h0) & (index <= h1)]
    if len(discovery) == 0 or len(holdout) == 0:
        raise ValueError("plan windows leave an empty discovery or holdout sample")
    return discovery, holdout
