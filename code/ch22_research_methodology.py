"""Chapter 22 CLI: hand examples, the constructed pre-registered-vs-mined experiment, and a real
French industry look-back search recorded in a trial ledger.

Run from the course root::

    .venv/bin/python code/ch22_research_methodology.py

Outputs: ``qa/a5/claude/results/ch22/*.json`` and ``figures/a5/ch22_*.png``. The CLI refuses to
overwrite an existing result. Nothing is downloaded; real inputs are the hash-checked frozen French
snapshot read through ``quant_course.french_frozen``. Constructed worlds are teaching constructions
with a known data-generating process, not market evidence.

Reader packaging note: paths above document historical source outputs only.
Current CLI defaults write to one unique runs/cli_<chapter>_<uuid>/results and figures.
French CLI branches require separate rights and execution authorization;
use the adapted Notebook for the default offline constructed teaching route.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy import integrate, optimize, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.factor_research import (  # noqa: E402
    bucket_returns, ic_series, ic_summary, lead_return, newey_west_variance_of_mean,
    quantile_long_short_weights, target_turnover,
)
from quant_course.factor_signals import formation_return  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.research_protocol import (  # noqa: E402
    ResearchPlan, TrialLedger, benjamini_hochberg_adjust, bonferroni_adjust, expected_max_standard_normal,
    expected_max_standard_normal_exact, freeze_plan, holm_adjust, split_discovery_holdout,
)

SEED = 20261006
N_NAMES, D_MONTHS, H_MONTHS = 200, 120, 60
EMBARGO = 3               # months dropped between discovery and holdout signals = longest label horizon
RETURN_SD = 0.08          # monthly idiosyncratic return sd in the constructed worlds
ALT_SLOPE = 0.0016        # return per unit of unit-variance characteristic -> population IC about 0.02
RHO = 0.9                 # month-to-month persistence of the constructed characteristic
WORLDS = 500
TRANSFORMS = ("rank", "raw", "winsor1", "winsor5")
LAGS = (0, 1, 2, 3)
HORIZONS = (1, 3)
VARIANTS = list(product(TRANSFORMS, LAGS, HORIZONS))      # 32; variants[0] is the registered primary
FIGURES = ("ch22_pipeline.png", "ch22_mining_inflation.png", "ch22_industry_trials.png")
COST_BP_PER_UNIT = 10.0   # assumed one-way cost per unit of weight traded; an illustration, not an estimate


# ----------------------------------------------------------------- hand examples
def hand_examples() -> dict:
    """Numbers used in the chapter's worked examples (all recomputable by hand)."""
    p = [0.01, 0.04, 0.03, 0.005]
    fwer = {m: 1 - 0.95 ** m for m in (1, 5, 10, 32, 100)}
    z_bonf = {m: float(stats.norm.ppf(1 - 0.05 / (2 * m))) for m in (1, 10, 32, 100, 316)}
    expmax = {n: {"approx": expected_max_standard_normal(n), "exact": expected_max_standard_normal_exact(n)}
              for n in (5, 10, 32, 100, 1000)}
    return {
        "p_values": p, "bonferroni": bonferroni_adjust(p).tolist(), "holm": holm_adjust(p).tolist(),
        "benjamini_hochberg": benjamini_hochberg_adjust(p).tolist(),
        "fwer_independent_tests_at_5pct": fwer, "bonferroni_two_sided_z_hurdle_at_5pct": z_bonf,
        "expected_max_standard_normal": expmax,
        "t_from_monthly_sharpe": {"monthly_sharpe": 0.15, "months": 120, "t_iid": 0.15 * np.sqrt(120)},
    }


# ------------------------------------------------------- constructed worlds
def _row_corr(signal: np.ndarray, label: np.ndarray) -> np.ndarray:
    s = signal - signal.mean(axis=1, keepdims=True)
    y = label - label.mean(axis=1, keepdims=True)
    return (s * y).sum(axis=1) / np.sqrt((s * s).sum(axis=1) * (y * y).sum(axis=1))


def _transform(x: np.ndarray, kind: str) -> np.ndarray:
    if kind == "raw":
        return x
    if kind == "rank":
        return x.argsort(axis=1).argsort(axis=1).astype(float)
    pct = {"winsor1": 0.01, "winsor5": 0.05}[kind]
    lo = np.quantile(x, pct, axis=1, keepdims=True)
    hi = np.quantile(x, 1 - pct, axis=1, keepdims=True)
    return np.clip(x, lo, hi)


def simulate_world(rng: np.random.Generator, slope: float) -> tuple[np.ndarray, np.ndarray]:
    """Characteristic panel ``x[m]`` and one-month returns ``r[m] = slope * x[m-1] + noise`` (month m).

    Both have heavy tails (scaled Student-t). ``slope = 0`` is the null world: no characteristic
    predicts returns, so every variant has population IC exactly zero.
    """
    months = 3 + D_MONTHS + EMBARGO + H_MONTHS + 3
    tail = lambda df, size: rng.standard_t(df, size) / np.sqrt(df / (df - 2))  # unit variance
    x = np.empty((months, N_NAMES))
    x[0] = tail(4, N_NAMES)
    for m in range(1, months):
        x[m] = RHO * x[m - 1] + np.sqrt(1 - RHO ** 2) * tail(4, N_NAMES)
    r = np.full((months, N_NAMES), np.nan)
    r[1:] = slope * x[:-1] + RETURN_SD * tail(5, (months - 1, N_NAMES))
    return x, r


def variant_t_stats(x: np.ndarray, r: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """NW t of mean IC in discovery and holdout for each of the 32 variants, plus mean ICs.

    Holdout signals start ``EMBARGO`` months after the last discovery signal so that no 3-month label
    overlaps a return month used by a discovery label (the purge idea of Chapter 30).
    """
    disc_months = np.arange(3, 3 + D_MONTHS)
    hold_months = np.arange(3 + D_MONTHS + EMBARGO, 3 + D_MONTHS + EMBARGO + H_MONTHS)
    t_disc, t_hold, ic_disc, ic_hold = (np.empty(len(VARIANTS)) for _ in range(4))
    for v, (kind, lag, h) in enumerate(VARIANTS):
        for months, t_out, ic_out in ((disc_months, t_disc, ic_disc), (hold_months, t_hold, ic_hold)):
            label = np.prod([1 + r[months + k] for k in range(1, h + 1)], axis=0) - 1
            ic = _row_corr(_transform(x[months - lag], kind), label)
            t_out[v] = ic.mean() / np.sqrt(newey_west_variance_of_mean(ic, h - 1))
            ic_out[v] = ic.mean()
    return t_disc, t_hold, ic_disc, ic_hold


def mining_experiment(slope: float, worlds: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    t_disc = np.empty((worlds, len(VARIANTS)))
    t_hold = np.empty_like(t_disc)
    ic_hold = np.empty_like(t_disc)
    for w in range(worlds):
        x, r = simulate_world(rng, slope)
        t_disc[w], t_hold[w], _, ic_hold[w] = variant_t_stats(x, r)
    best = np.abs(t_disc).argmax(axis=1)
    rows = np.arange(worlds)
    sign = np.sign(t_disc[rows, best])
    bonf_hurdle = float(stats.norm.ppf(1 - 0.05 / (2 * len(VARIANTS))))
    max_abs = np.abs(t_disc).max(axis=1)
    return {
        "slope": slope, "worlds": worlds, "variants": len(VARIANTS),
        "population_ic_approx": slope / np.sqrt(slope ** 2 + RETURN_SD ** 2),
        "primary_reject_rate_abs_t_gt_1.96": float((np.abs(t_disc[:, 0]) > 1.96).mean()),
        "best_of_32_reject_rate_abs_t_gt_1.96": float((max_abs > 1.96).mean()),
        "best_of_32_reject_rate_bonferroni_hurdle": float((max_abs > bonf_hurdle).mean()),
        "bonferroni_hurdle_z": bonf_hurdle,
        "mean_max_abs_t_discovery": float(max_abs.mean()),
        "t_sd_horizon_1_variants": float(t_disc[:, [i for i, v in enumerate(VARIANTS) if v[2] == 1]].std()),
        "t_sd_horizon_3_variants": float(t_disc[:, [i for i, v in enumerate(VARIANTS) if v[2] == 3]].std()),
        "reject_rate_horizon_3_primary_like": float((np.abs(t_disc[:, 1]) > 1.96).mean()),
        "mean_t_discovery_by_transform_h1": {k: float(t_disc[:, [i for i, v in enumerate(VARIANTS) if v[0] == k and v[2] == 1]].mean()) for k in TRANSFORMS},
        "mean_t_discovery_by_signal_lag_h1": {str(k): float(t_disc[:, [i for i, v in enumerate(VARIANTS) if v[1] == k and v[2] == 1]].mean()) for k in LAGS},
        "selected_horizon_3_share": float(np.mean([VARIANTS[b][2] == 3 for b in best])),
        "selected_is_primary_share": float((best == 0).mean()),
        "selected_holdout_signed_t_mean": float((sign * t_hold[rows, best]).mean()),
        "selected_holdout_signed_t_gt_1.96_rate": float((sign * t_hold[rows, best] > 1.96).mean()),
        "primary_holdout_t_gt_1.96_rate": float((t_hold[:, 0] > 1.96).mean()),
        "_t_disc_primary": t_disc[:, 0], "_t_disc_max": max_abs,
        "_holdout_signed_selected": sign * t_hold[rows, best],
    }


def implied_independent_trials(mean_max_abs_t: float) -> float:
    """N such that E[max of N iid |N(0,1)|] equals the observed mean maximum |t| (real-valued N)."""
    def expectation(n: float) -> float:
        cdf = lambda x: 2 * stats.norm.cdf(x) - 1
        pdf = lambda x: 2 * stats.norm.pdf(x)
        return integrate.quad(lambda x: x * n * pdf(x) * cdf(x) ** (n - 1), 0, 12, limit=200)[0]
    return float(optimize.brentq(lambda n: expectation(n) - mean_max_abs_t, 1.0, 5000.0))


# --------------------------------------------------- real French industry search
def real_plan() -> ResearchPlan:
    return ResearchPlan(
        hypothesis="Industries with higher past 12-1 return have higher next-month return (cross-sectional momentum, sign +)",
        universe="10 French value-weighted industry portfolios (monthly, revised history, not tradable fills)",
        data_sources=("data/processed/french_10_industries_monthly.csv sha256 3b097d81...",),
        discovery_start="1926-07", discovery_end="1999-12", holdout_start="2000-01", holdout_end="2026-07",
        signal_definition="12-1: compounded return of months s-11..s-1, signal at end of month s",
        label_definition="simple return of month s+1",
        portfolio_rule="equal-weight top 2 minus bottom 2 of 10 industries (quintile buckets), monthly rebalance",
        benchmark="zero signal / equal-weight 10 industries",
        primary_metric="t of mean Spearman RankIC (Newey-West lag 0) in the holdout",
        decision_rule="holdout t >= 2.0 with positive sign; otherwise report the hypothesis as not supported",
        cost_assumption=f"{COST_BP_PER_UNIT:g} bp per unit of weight traded (illustrative)", trial_budget=24,
        notes="Written after the literature and after earlier chapters used the same data: not blind, not externally registered.")


def placebo_holdout(signal: pd.DataFrame, label: pd.DataFrame, months: pd.PeriodIndex, *, n_perm: int, seed: int) -> dict:
    """Permutation benchmark: shuffle the label across industries within each month and recompute the mean-RankIC t.

    Destroys any signal-label link while keeping each month's cross-sectional set of labels, the number
    of names and the time-series ordering; it does not model dependence across months.
    """
    s, y = signal.loc[months], label.loc[months]
    ok = ~(s.isna().any(axis=1) | y.isna().any(axis=1))
    s_rank = stats.rankdata(s[ok].to_numpy(), axis=1)      # average ranks: published returns are rounded, so ties occur
    y_rank = stats.rankdata(y[ok].to_numpy(), axis=1)

    def t_stat(sr: np.ndarray, yr: np.ndarray) -> float:
        ic = _row_corr(sr, yr)
        return float(ic.mean() / (ic.std(ddof=0) / np.sqrt(ic.size)))

    observed = t_stat(s_rank, y_rank)
    rng = np.random.default_rng(seed)
    draws = np.array([t_stat(s_rank, rng.permuted(y_rank, axis=1)) for _ in range(n_perm)])
    return {"months": int(ok.sum()), "n_perm": n_perm, "t_observed": observed, "placebo_t_sd": float(draws.std()),
            "p_one_sided": float((1 + (draws >= observed).sum()) / (n_perm + 1))}


def industry_search(returns: pd.DataFrame, plan: ResearchPlan) -> dict:
    disc_idx, hold_idx = split_discovery_holdout(returns.index, plan)
    label = lead_return(returns, 1)
    ledger = TrialLedger()
    table = []
    for window, skip in product(range(1, 13), (0, 1)):
        signal = formation_return(returns, window, skip)
        ic = ic_series(signal, label, method="spearman")["ic"]
        d = ic_summary(ic.loc[ic.index.isin(disc_idx)], nw_lags=0)
        h = ic_summary(ic.loc[ic.index.isin(hold_idx)], nw_lags=0)
        primary = (window, skip) == (11, 1)
        ledger.record({"window": window, "skip": skip}, metric=d.t_nw, n_obs=d.n_dates,
                      status="primary" if primary else "run")
        table.append({"window": window, "skip": skip, "primary": primary, "t_disc": d.t_nw, "ic_disc": d.mean,
                      "t_hold": h.t_nw, "ic_hold": h.mean, "n_disc": d.n_dates, "n_hold": h.n_dates})
    frame = pd.DataFrame(table)
    pvals_disc = 2 * stats.norm.sf(np.abs(frame["t_disc"]))
    best = frame.loc[frame["t_disc"].idxmax()]
    primary_row = frame.loc[frame["primary"]].iloc[0]
    # gross/net quintile long-short for the registered primary and for the discovery-selected variant
    cost = COST_BP_PER_UNIT / 1e4

    def long_short(window: int, skip: int) -> dict:
        signal = formation_return(returns, window, skip)
        gross = bucket_returns(signal.dropna(how="all"), label, 5)["LS"].dropna()
        w = quantile_long_short_weights(signal.dropna(how="all"), 5)
        turn = target_turnover(w).reindex(gross.index)
        net = gross - cost * turn.fillna(0.0)
        out = {}
        for name, idx in (("discovery", disc_idx), ("holdout", hold_idx)):
            g, n = gross[gross.index.isin(idx)], net[net.index.isin(idx)]
            out[name] = {"months": int(len(g)), "gross_mean_pct": float(100 * g.mean()),
                         "gross_t": float(g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))),
                         "net_mean_pct": float(100 * n.mean()), "mean_turnover": float(turn[turn.index.isin(idx)].mean())}
        return out

    return {
        "plan_hash_note": "see ch22_plan_frozen.json", "ledger_trials": ledger.n_trials,
        "primary": primary_row.to_dict(), "selected_by_discovery": best.to_dict(),
        "discovery_p_two_sided_best": float(pvals_disc[frame["t_disc"].idxmax()]),
        "bonferroni_p_best": float(bonferroni_adjust(pvals_disc).min()),
        "holm_p_best": float(holm_adjust(pvals_disc).min()),
        "bh_p_best": float(benjamini_hochberg_adjust(pvals_disc).min()),
        "n_variants_discovery_t_gt_2": int((frame["t_disc"] > 2).sum()),
        "n_variants_holdout_t_gt_2": int((frame["t_hold"] > 2).sum()),
        "placebo_primary_holdout": placebo_holdout(formation_return(returns, 11, 1), label, hold_idx, n_perm=2000, seed=SEED + 2),
        "long_short_primary": long_short(11, 1),
        "long_short_selected": long_short(int(best["window"]), int(best["skip"])),
        "table": frame.to_dict(orient="records"), "ledger": ledger.to_frame().to_dict(orient="records"),
    }


# --------------------------------------------------------------------- figures
def _pipeline_figure(path: Path) -> None:
    stages = [("Economic hypothesis", "plan.md + SHA-256\n(sign, universe)"), ("Data", "source, hash, available_at"),
              ("Cleaning", "rules written before looking\nat returns"), ("Feature", "definition, window, units"),
              ("Signal", "signal_time <= trade_time"), ("Portfolio", "weights rule, constraints"),
              ("Backtest", "label interval, lag, ledger"), ("Validation", "holdout, ablation, benchmark"),
              ("Cost model", "gross vs net, turnover"), ("Out-of-sample", "untouched until plan frozen")]
    fig, ax = plt.subplots(figsize=(12.5, 4.6))
    ax.set_xlim(0, 5.3); ax.set_ylim(0, 2.2); ax.axis("off")
    for i, (name, note) in enumerate(stages):
        row, col = divmod(i, 5)
        x, y = 0.12 + col * 1.04, 1.25 - row * 1.1
        ax.add_patch(FancyBboxPatch((x, y), 0.9, 0.7, boxstyle="round,pad=0.02", fc="#E8F1F5", ec="#176B87", lw=1.3))
        ax.text(x + 0.45, y + 0.50, f"{i + 1}. {name}", ha="center", va="center", fontsize=8.8, weight="bold")
        ax.text(x + 0.45, y + 0.20, note, ha="center", va="center", fontsize=7.6)
        if col < 4:
            ax.add_patch(FancyArrowPatch((x + 0.91, y + 0.35), (x + 1.03, y + 0.35), arrowstyle="-|>", mutation_scale=10, color="#444"))
    ax.text(2.65, 2.12, "Research pipeline: every stage leaves an artifact and a timestamp field; the trial ledger spans stages 3-10",
            ha="center", fontsize=10)
    ax.text(2.65, 0.05, "No arrow leads from stage 10 back to stage 1: a holdout result may not rewrite the hypothesis it was meant to test",
            ha="center", fontsize=8.2, color="#D05A36")
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def _mining_figure(null: dict, alt: dict, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    bins = np.linspace(0, 6, 49)
    ax = axes[0]
    ax.hist(np.abs(null["_t_disc_primary"]), bins=bins, alpha=0.7, color="#176B87", label="registered primary (1 look)")
    ax.hist(null["_t_disc_max"], bins=bins, alpha=0.6, color="#D05A36", label="best of 32 variants")
    ax.axvline(1.96, color="k", ls="--", lw=1); ax.axvline(null["bonferroni_hurdle_z"], color="#654A8B", ls=":", lw=1.4)
    ax.text(1.99, ax.get_ylim()[1] * 0.92, "1.96", fontsize=8); ax.text(null["bonferroni_hurdle_z"] + 0.03, ax.get_ylim()[1] * 0.8, "Bonferroni\n(32 trials)", fontsize=8, color="#654A8B")
    ax.set_xlabel("|Newey-West t| of mean IC in the discovery sample (unitless)"); ax.set_ylabel("Number of simulated null worlds")
    ax.set_title("Null world (true IC = 0): searching manufactures significance"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    b2 = np.linspace(-5, 8, 53)
    ax.hist(null["_holdout_signed_selected"], bins=b2, alpha=0.7, color="#D05A36", label="selected variant, null world")
    ax.hist(alt["_holdout_signed_selected"], bins=b2, alpha=0.6, color="#176B87", label="selected variant, true IC 0.02")
    ax.axvline(0, color="k", lw=0.8); ax.axvline(1.96, color="k", ls="--", lw=1)
    ax.set_xlabel("Holdout t of the selected variant, sign-aligned (unitless)")
    ax.set_ylabel("Number of simulated worlds"); ax.set_title("The untouched holdout separates the two worlds"); ax.legend(frameon=False, fontsize=8.5)
    fig.suptitle(f"Constructed worlds: {null['worlds']} per panel, N={N_NAMES} names, {D_MONTHS}+{H_MONTHS} months, seed {SEED}", fontsize=9)
    fig.savefig(path, dpi=150); plt.close(fig)


def _industry_figure(search: dict, path: Path) -> None:
    frame = pd.DataFrame(search["table"])
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    for skip, marker, color in ((0, "o", "#176B87"), (1, "s", "#D05A36")):
        sub = frame[frame["skip"] == skip]
        ax.scatter(sub["t_disc"], sub["t_hold"], marker=marker, color=color, s=34, label=f"skip = {skip} month")
    p = frame[frame["primary"]]
    ax.scatter(p["t_disc"], p["t_hold"], s=180, facecolors="none", edgecolors="k", lw=1.6, label="registered primary (11, 1)")
    ax.axhline(0, color="0.5", lw=0.8); ax.axvline(0, color="0.5", lw=0.8)
    ax.set_xlabel("Discovery t, mean RankIC, 1926-07 to 1999-12 (unitless)"); ax.set_ylabel("Holdout t, 2000-01 to 2026-07 (unitless)")
    ax.set_title("24 look-back variants on 10 industries"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    order = frame.sort_values("t_disc", ascending=False).reset_index(drop=True)
    ax.bar(np.arange(len(order)), order["t_disc"], color="#176B87", alpha=0.8, label="discovery t")
    ax.plot(np.arange(len(order)), order["t_hold"], "o-", color="#D05A36", ms=4, lw=1, label="same variant, holdout t")
    ax.axhline(1.96, color="k", ls="--", lw=1)
    ax.set_xlabel("Variants ranked by discovery t (rank 0 = best)"); ax.set_ylabel("t (unitless)")
    ax.set_title("Ranking on discovery is not a ranking on the holdout"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(path, dpi=150); plt.close(fig)


# ------------------------------------------------------------------------ driver
def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def run(out_dir: Path, fig_dir: Path, *, worlds: int = WORLDS) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch22_results.json", out_dir / "ch22_plan_frozen.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 22 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True); fig_dir.mkdir(parents=True, exist_ok=True)

    plan = real_plan()
    frozen = freeze_plan(plan)                       # real wall-clock; written BEFORE any holdout number is computed
    (out_dir / "ch22_plan_frozen.json").write_text(json.dumps(
        {"sha256": frozen.sha256, "frozen_at_local": frozen.frozen_at_local, "plan": json.loads(json.dumps(plan.__dict__, default=list))},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    returns, _, provenance = load_industries_and_rf()
    search = industry_search(returns, plan)
    null = mining_experiment(0.0, worlds, SEED)
    alt = mining_experiment(ALT_SLOPE, worlds, SEED + 1)
    null["implied_independent_trials"] = implied_independent_trials(null["mean_max_abs_t_discovery"])
    result = {"seed": SEED, "plan_sha256": frozen.sha256, "hand_examples": hand_examples(), "null_world": null,
              "alternative_world": alt, "french_industry_search": search,
              "provenance": {"french_hashes": provenance["sha256"], "is_point_in_time": provenance["is_point_in_time"]}}
    _pipeline_figure(fig_dir / FIGURES[0])
    _mining_figure(null, alt, fig_dir / FIGURES[1])
    _industry_figure(search, fig_dir / FIGURES[2])
    (out_dir / "ch22_results.json").write_text(json.dumps(_clean(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _clean(result)


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch22_research_methodology_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(default_run / "results"))
    parser.add_argument("--figures", default=str(default_run / "figures"))
    parser.add_argument("--worlds", type=int, default=WORLDS)
    args = parser.parse_args()
    result = run(Path(args.out), Path(args.figures), worlds=args.worlds)
    null, alt, real = result["null_world"], result["alternative_world"], result["french_industry_search"]
    print(f"plan sha256 {result['plan_sha256']}")
    print(f"null world: primary reject {null['primary_reject_rate_abs_t_gt_1.96']:.3f}; best-of-32 reject "
          f"{null['best_of_32_reject_rate_abs_t_gt_1.96']:.3f}; Bonferroni hurdle reject {null['best_of_32_reject_rate_bonferroni_hurdle']:.3f}")
    print(f"alt world: primary reject {alt['primary_reject_rate_abs_t_gt_1.96']:.3f}; selected holdout t>1.96 {alt['selected_holdout_signed_t_gt_1.96_rate']:.3f}")
    print(f"French: ledger {real['ledger_trials']} trials; primary t_disc {real['primary']['t_disc']:.2f}, t_hold {real['primary']['t_hold']:.2f}")


if __name__ == "__main__":
    main()
