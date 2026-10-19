"""Chapter 23 CLI: cross-sectional ranking, IC / RankIC, decay, quantile portfolios, turnover, Fama-MacBeth.

Run from the course root::

    .venv/bin/python code/ch23_cross_sectional_research.py

Outputs ``qa/a5/claude/results/ch23/ch23_results.json`` and ``figures/a5/ch23_*.png``; refuses to overwrite.
Constructed panels have a known data-generating process (teaching construction, not market evidence). The real
example uses the frozen French 10-industry monthly snapshot (revised history, N = 10 portfolios).

Reader packaging note: paths above document historical source outputs only.
Current CLI defaults write to one unique runs/cli_<chapter>_<uuid>/results and figures.
French CLI branches require separate rights and execution authorization;
use the adapted Notebook for the default offline constructed teaching route.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.factor_research import (  # noqa: E402
    bucket_membership_turnover, bucket_returns, fama_macbeth, forward_label, ic_decay, ic_series, ic_summary,
    lead_return, newey_west_variance_of_mean, percentile_cross_section, quantile_bucket, quantile_long_short_weights,
    rank_cross_section, signal_proportional_weights, target_turnover,
)
from quant_course.factor_signals import formation_return  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402

SEED = 20261023
N_NAMES, MONTHS = 300, 180
RHO = 0.85                # month-to-month persistence of the constructed signal
BETA = 0.004              # return per unit of unit-variance signal, one month ahead
NOISE_SD, MARKET_SD, MARKET_MEAN = 0.08, 0.045, 0.008
FIGURES = ("ch23_constructed_ic_decay.png", "ch23_pooled_vs_per_date.png", "ch23_overlap_t.png", "ch23_industry_ic.png")


# ------------------------------------------------------------------ hand examples
def _corr_pearson(x, y) -> float:
    return float(np.corrcoef(x, y)[0, 1])


def hand_examples() -> dict:
    """All numbers of chapter section 8; each is also recomputed in qa/a5/claude/recompute/ch23_recompute.py."""
    # 8.1 ranks, ties, NaN
    x = np.array([3, 1, np.nan, 3, 2, 7, 5, 5])
    # 8.2 buckets
    ten = np.arange(1.0, 11.0)
    tie = np.array([1, 2, 2, 2, 5, 6, 7, 8.0])
    # 8.3 Pearson vs Spearman with one outlier
    s3 = np.array([1, 2, 3, 4, 5, 20.0])
    y3 = np.array([0.02, 0.01, 0.04, 0.03, 0.06, -0.05])
    r_s, r_y = rank_cross_section(s3), rank_cross_section(y3)
    d2 = float(((r_s - r_y) ** 2).sum())
    # 8.4 pooled correlation vs per-date IC
    sa, ra = np.array([1, 2, 3, 4.0]), np.array([0.10, 0.12, 0.14, 0.16])
    sb, rb = np.array([11, 12, 13, 14.0]), np.array([0.26, 0.24, 0.22, 0.20])
    pooled = _corr_pearson(np.r_[sa, sb], np.r_[ra, rb])
    # 8.5 quintile long-short, two dates, N = 10
    sig1 = np.array([5, 3, 9, 1, 7, 2, 10, 4, 8, 6.0]); ret1 = np.array([.02, .01, .05, -.01, .03, .00, .06, .01, .04, .02])
    sig2 = np.array([5, 4, 9, 1, 6, 3, 10, 2, 7, 8.0]); ret2 = np.array([.01, .02, .03, -.02, .02, .01, .03, .00, .04, .05])
    bucket1, bucket2 = quantile_bucket(sig1, 5), quantile_bucket(sig2, 5)
    ls1 = ret1[bucket1 == 5].mean() - ret1[bucket1 == 1].mean()
    ls2 = ret2[bucket2 == 5].mean() - ret2[bucket2 == 1].mean()
    w1 = np.where(bucket1 == 5, 0.5, 0.0) - np.where(bucket1 == 1, 0.5, 0.0)
    w2 = np.where(bucket2 == 5, 0.5, 0.0) - np.where(bucket2 == 1, 0.5, 0.0)
    # 8.6 IC = return of z-weights
    s6 = np.array([2, 4, 6, 8, 10.0]); r6 = np.array([0.01, 0.00, 0.03, 0.02, 0.04])
    z6 = (s6 - s6.mean()) / s6.std(ddof=0)
    port6 = float((z6 * r6).sum() / 5)
    # 8.7 Fama-MacBeth, three dates, N = 4
    fm_s = np.array([[1, 2, 3, 4.0], [4, 3, 2, 1.0], [1, 3, 2, 4.0]])
    fm_r = np.array([[0.01, 0.02, 0.04, 0.05], [0.02, 0.02, 0.01, 0.00], [0.00, 0.03, 0.02, 0.04]])
    slopes = []
    for srow, rrow in zip(fm_s, fm_r):
        dev = srow - srow.mean()
        slopes.append(float((dev * (rrow - rrow.mean())).sum() / (dev ** 2).sum()))
    slopes_arr = np.array(slopes)
    return {
        "ranks": {"x": x.tolist(), "rank": rank_cross_section(x).tolist(), "percentile": percentile_cross_section(x).tolist()},
        "buckets": {"ten_q5": quantile_bucket(ten, 5).tolist(), "ties_q4": quantile_bucket(tie, 4).tolist()},
        "pearson_vs_spearman": {"pearson": _corr_pearson(s3, y3), "spearman": 1 - 6 * d2 / (6 * 35), "sum_d2": d2,
                                 "spearman_via_scipy": float(stats.spearmanr(s3, y3).statistic)},
        "pooled_vs_per_date": {"ic_a": _corr_pearson(sa, ra), "ic_b": _corr_pearson(sb, rb), "mean_ic": 0.0, "pooled": pooled},
        "quintile_ls": {"bucket_date1": bucket1.tolist(), "ls_date1": float(ls1), "ls_date2": float(ls2),
                        "turnover_between_targets": float(np.abs(w2 - w1).sum()),
                        "top_bucket_members_date1": np.flatnonzero(bucket1 == 5).tolist(),
                        "top_bucket_members_date2": np.flatnonzero(bucket2 == 5).tolist()},
        "z_weighted_return": {"z": z6.tolist(), "portfolio_return": port6, "pearson_ic": _corr_pearson(s6, r6),
                              "sd0_return": float(r6.std(ddof=0)), "ic_times_sd0": _corr_pearson(s6, r6) * float(r6.std(ddof=0))},
        "fama_macbeth_hand": {"slopes": slopes_arr.tolist(), "mean": float(slopes_arr.mean()),
                              "se_naive": float(slopes_arr.std(ddof=1) / np.sqrt(3)),
                              "t_naive": float(slopes_arr.mean() / (slopes_arr.std(ddof=1) / np.sqrt(3)))},
        "overlap_effective_dates": {"months": 120, "horizon": 3, "n_eff": 120 / 3},
    }


# --------------------------------------------------------------- constructed panel
def _tail(rng: np.random.Generator, df: int, size) -> np.ndarray:
    return rng.standard_t(df, size) / np.sqrt(df / (df - 2))


def constructed_panel(seed: int = SEED, *, n_names: int = N_NAMES, months: int = MONTHS, beta: float = BETA,
                      rho: float = RHO) -> dict:
    """Signal ``z`` (AR(1), unit variance, heavy tails) and one-month returns ``r[t+1] = m[t+1] + beta z[t] + noise``."""
    rng = np.random.default_rng(seed)
    idx = pd.period_range("2005-01", periods=months, freq="M")
    cols = [f"S{i:03d}" for i in range(n_names)]
    z = np.empty((months, n_names)); z[0] = _tail(rng, 4, n_names)
    for t in range(1, months):
        z[t] = rho * z[t - 1] + np.sqrt(1 - rho ** 2) * _tail(rng, 4, n_names)
    market = MARKET_MEAN + MARKET_SD * rng.standard_normal(months)
    r = market[:, None] + NOISE_SD * _tail(rng, 5, (months, n_names))
    r[1:] += beta * z[:-1]
    log_cap = rng.standard_normal(n_names)[None, :] + 0.05 * rng.standard_normal((months, n_names)).cumsum(axis=0) / np.sqrt(months)
    return {"index": idx, "z": pd.DataFrame(z, index=idx, columns=cols), "returns": pd.DataFrame(r, index=idx, columns=cols),
            "cap": pd.DataFrame(np.exp(log_cap), index=idx, columns=cols), "market": pd.Series(market, index=idx)}


def _summary_row(summary) -> dict:
    return {"mean": summary.mean, "std": summary.std, "t_naive": summary.t_naive, "t_nw": summary.t_nw,
            "nw_lags": summary.nw_lags, "n_eff": summary.n_eff, "n_dates": summary.n_dates, "hit_rate": summary.hit_rate}


def constructed_study(panel: dict) -> dict:
    z, ret, cap = panel["z"], panel["returns"], panel["cap"]
    label1 = lead_return(ret, 1)
    ic_p = ic_series(z, label1, method="pearson")["ic"]
    ic_s = ic_series(z, label1, method="spearman")["ic"]
    decay = ic_decay(z, ret, leads=range(1, 13), method="spearman", nw_lags=0)
    ic1 = float(decay.loc[1, "mean_ic"])
    theory = {int(k): ic1 * RHO ** (k - 1) for k in range(1, 13)}
    # overlapping 3-month labels on the same panel
    label3 = forward_label(ret, horizon=3)
    ic3 = ic_series(z, label3, method="spearman")["ic"]
    # deciles, weighting schemes, turnover
    deciles = bucket_returns(z, label1, 10).dropna()
    ls_ew = bucket_returns(z, label1, 5)["LS"].dropna()
    ls_vw = bucket_returns(z, label1, 5, weights=cap)["LS"].dropna()
    w_prop = signal_proportional_weights(z, gross=2.0)
    ls_prop = (w_prop * label1).sum(axis=1, min_count=1).dropna()
    zs = z.sub(z.mean(axis=1), axis=0).div(z.std(axis=1, ddof=0), axis=0)
    ls_z = ((zs * label1).sum(axis=1, min_count=1) / z.shape[1]).dropna()                     # w = z / N
    identity_gap = float((ls_z - ic_series(z, label1, method="pearson")["ic"].reindex(ls_z.index) * label1.std(axis=1, ddof=0).reindex(ls_z.index)).abs().max())
    w_q = quantile_long_short_weights(z, 10)
    turn_target = target_turnover(w_q)
    turn_member = bucket_membership_turnover(z, 10)
    fm = fama_macbeth(label1, {"signal": zs}, nw_lags=0)
    noise = pd.DataFrame(np.random.default_rng(SEED + 5).standard_normal(z.shape), index=z.index, columns=z.columns)
    fm2 = fama_macbeth(label1, {"signal": zs, "noise_signal": noise}, nw_lags=0)

    def stat(series: pd.Series) -> dict:
        s = series.dropna()
        return {"mean_pct": float(100 * s.mean()), "t_naive": float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), "months": int(len(s))}

    return {
        "n_names": z.shape[1], "months": z.shape[0], "population_ic_1m_approx": BETA / np.sqrt(BETA ** 2 + NOISE_SD ** 2),
        "ic_pearson": _summary_row(ic_summary(ic_p)), "ic_spearman": _summary_row(ic_summary(ic_s)),
        "ic_decay_spearman": {int(k): {"mean_ic": float(v["mean_ic"]), "t": float(v["t_nw"]), "theory": theory[int(k)]} for k, v in decay.iterrows()},
        "overlap_3m_label": {"nw0": _summary_row(ic_summary(ic3, nw_lags=0)), "nw2": _summary_row(ic_summary(ic3, nw_lags=2))},
        "decile_mean_return_pct": {int(c): float(100 * deciles[c].mean()) for c in deciles.columns if c != "LS"},
        "decile_ls_top_minus_bottom": stat(deciles["LS"]),
        "quintile_ls_equal_weight": stat(ls_ew), "quintile_ls_value_weight": stat(ls_vw),
        "proportional_gross2_ls": stat(ls_prop), "z_over_n_ls": stat(ls_z), "identity_z_over_n_vs_ic_times_sd0_max_gap": identity_gap,
        "turnover_decile_ls_target_mean": float(turn_target.mean()), "turnover_top_decile_membership_mean": float(turn_member.mean()),
        "fama_macbeth_one_signal": fm.summary.round(8).to_dict(orient="index"),
        "fama_macbeth_two_signals": fm2.summary.round(8).to_dict(orient="index"),
        "_ic_p": ic_p, "_ic_s": ic_s, "_decay": decay, "_theory": theory, "_deciles": deciles,
    }


def pooled_vs_per_date(seed: int = SEED + 1, *, months: int = 120, n_names: int = 200, shift: float = 2.0, rho_u: float = 0.5) -> dict:
    """Signal whose date-level mean carries timing information about the market but none about the ordering of names."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((months, n_names))
    market_next = MARKET_MEAN + MARKET_SD * rng.standard_normal(months)
    u = rho_u * (market_next - MARKET_MEAN) / MARKET_SD + np.sqrt(1 - rho_u ** 2) * rng.standard_normal(months)
    signal = z + shift * u[:, None]
    ret = market_next[:, None] + NOISE_SD * rng.standard_normal((months, n_names))   # no cross-sectional dependence on z
    pooled = float(np.corrcoef(signal.ravel(), ret.ravel())[0, 1])
    per_date = np.array([np.corrcoef(signal[t], ret[t])[0, 1] for t in range(months)])
    s = ic_summary(per_date)
    return {"pooled_corr": pooled, "mean_ic": s.mean, "t_ic": s.t_naive, "months": months, "n_names": n_names,
            "_signal_level": signal.mean(axis=1), "_market_next": market_next, "_per_date": per_date}


# ------------------------------------------------------ overlapping labels null study
def _row_corr(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a - a.mean(axis=1, keepdims=True); b = b - b.mean(axis=1, keepdims=True)
    return (a * b).sum(axis=1) / np.sqrt((a * a).sum(axis=1) * (b * b).sum(axis=1))


def overlap_vif(rho: float, h: int) -> dict:
    """Population variance-inflation factors for the mean IC when the signal is AR(1) with coefficient rho and labels span h months.

    corr(IC_t, IC_{t+j}) = rho^j (1 - j/h) for 0 < j < h (derived in the chapter, section 6.4, under a null of independent
    returns). The naive t is too large by sqrt(VIF); a Bartlett-kernel Newey-West estimator with lags h-1 multiplies the
    j-th autocorrelation by (1 - j/h) once more, so it recovers only VIF_nw.
    """
    true = 1 + 2 * sum(rho ** j * (1 - j / h) for j in range(1, h))
    nw = 1 + 2 * sum(rho ** j * (1 - j / h) ** 2 for j in range(1, h))
    return {"vif_true": true, "vif_nw_population": nw, "predicted_sd_naive_t": float(np.sqrt(true)),
            "predicted_sd_nw_t": float(np.sqrt(true / nw)), "n_eff_for_120_months": 120 / true}


def overlap_null_study(seed: int = SEED + 2, *, worlds: int = 600, months: int = 120, n_names: int = 100,
                       horizons: tuple[int, ...] = (1, 3, 6, 12), signal_rho: float = RHO) -> dict:
    """Null world (returns independent of the signal): size of three t statistics for overlapping labels.

    ``naive``: iid-across-dates t on all months; ``nw``: Newey-West with lags h-1 on all months;
    ``non_overlap``: keep every h-th month (T/h non-overlapping labels), t with T/h - 1 degrees of freedom.
    The label is the *sum* of h one-month returns so that only the overlap structure matters. Overlap alone does not
    inflate the naive t: the IC series is autocorrelated only if the signal is also persistent (compare ``signal_rho`` 0 and 0.85).
    """
    rng = np.random.default_rng(seed)
    hmax = max(horizons)
    total = months + hmax
    out = {h: {"naive": [], "nw": [], "non_overlap": [], "crit": float(stats.t.ppf(0.975, max(months // h - 1, 1)))} for h in horizons}
    for _ in range(worlds):
        z = np.empty((total, n_names)); z[0] = rng.standard_normal(n_names)
        for t in range(1, total):
            z[t] = signal_rho * z[t - 1] + np.sqrt(1 - signal_rho ** 2) * rng.standard_normal(n_names)
        r = 0.08 * rng.standard_normal((total, n_names))
        for h in horizons:
            label = np.sum([r[k: k + months] for k in range(1, h + 1)], axis=0)
            ic = _row_corr(z[:months], label)
            out[h]["naive"].append(ic.mean() / (ic.std(ddof=1) / np.sqrt(months)))
            out[h]["nw"].append(ic.mean() / np.sqrt(newey_west_variance_of_mean(ic, h - 1)))
            sub = ic[::h]
            out[h]["non_overlap"].append(sub.mean() / (sub.std(ddof=1) / np.sqrt(len(sub))))
    table = {}
    for h in horizons:
        naive, nw, non = (np.array(out[h][k]) for k in ("naive", "nw", "non_overlap"))
        table[h] = {"sd_naive_t": float(naive.std()), "sd_nw_t": float(nw.std()), "sd_non_overlap_t": float(non.std()),
                    "reject_naive": float((np.abs(naive) > 1.96).mean()), "reject_nw": float((np.abs(nw) > 1.96).mean()),
                    "reject_non_overlap": float((np.abs(non) > out[h]["crit"]).mean()), "sqrt_h": float(np.sqrt(h)),
                    "non_overlap_months": int(len(range(0, months, h))), "theory": overlap_vif(signal_rho, h)}
    return {"worlds": worlds, "months": months, "n_names": n_names, "signal_rho": signal_rho, "by_horizon": table}


# ------------------------------------------------------------------- real industries
def industry_study(returns: pd.DataFrame) -> dict:
    signal = formation_return(returns, 11, 1)
    label1 = lead_return(returns, 1)
    ic = ic_series(signal, label1, method="spearman")["ic"]
    ic_pear = ic_series(signal, label1, method="pearson")["ic"]
    periods = {"1927-06..1963-12": ("1927-06", "1963-12"), "1964-01..1999-12": ("1964-01", "1999-12"), "2000-01..2026-07": ("2000-01", "2026-07"),
               "all": ("1927-06", "2026-07")}
    sub = {name: _summary_row(ic_summary(ic.loc[pd.Period(a, "M"):pd.Period(b, "M")], nw_lags=0)) for name, (a, b) in periods.items()}
    decay = ic_decay(signal, returns, leads=range(1, 13), method="spearman", nw_lags=0)
    buckets = bucket_returns(signal.dropna(how="all"), label1, 5).dropna()
    zs = signal.sub(signal.mean(axis=1), axis=0).div(signal.std(axis=1, ddof=0), axis=0)
    fm = fama_macbeth(label1, {"signal_z": zs}, nw_lags=0)
    ls = buckets["LS"]
    w = quantile_long_short_weights(signal.dropna(how="all"), 5)
    # slope identity: b_t = IC_pearson_t * sd0(r_t) because z has unit population sd on every date
    common = fm.slopes.index
    gap = float((fm.slopes["signal_z"] - ic_pear.reindex(common) * label1.std(axis=1, ddof=0).reindex(common)).abs().max())
    return {
        "months_with_ic": int(ic.notna().sum()), "rank_ic_by_period": sub,
        "ic_decay_spearman": {int(k): {"mean_ic": float(v["mean_ic"]), "t": float(v["t_nw"])} for k, v in decay.iterrows()},
        "quintile_mean_return_pct": {int(c): float(100 * buckets[c].mean()) for c in buckets.columns if c != "LS"},
        "quintile_ls_mean_pct": float(100 * ls.mean()), "quintile_ls_t_naive": float(ls.mean() / (ls.std(ddof=1) / np.sqrt(len(ls)))),
        "target_turnover_mean": float(target_turnover(w).mean()),
        "top_bucket_membership_turnover_mean": float(bucket_membership_turnover(signal.dropna(how="all"), 5).mean()),
        "fama_macbeth_signal_z": fm.summary.round(8).to_dict(orient="index"), "fm_months": int(len(fm.slopes)),
        "fm_slope_vs_ic_times_sd0_gap": gap,
        "_ic": ic, "_decay": decay, "_buckets": buckets,
    }


# ------------------------------------------------------------------------- figures
def _figures(const: dict, pooled: dict, overlap: dict, real: dict, fig_dir: Path) -> None:
    # 1: constructed IC decay + deciles
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    d = const["_decay"]; ks = d.index.to_numpy()
    se = np.abs(d["mean_ic"].to_numpy() / d["t_nw"].to_numpy())
    ax.errorbar(ks, d["mean_ic"], yerr=2 * se, fmt="o", color="#176B87", capsize=3, label="mean RankIC at lead k (±2 se)")
    ax.plot(ks, [const["_theory"][int(k)] for k in ks], "--", color="#D05A36", label=f"IC1 x {RHO}^(k-1) (signal persistence)")
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Lead k: months between signal_time and the return month (months)"); ax.set_ylabel("Mean Spearman IC (unitless)")
    ax.set_title("Constructed panel: IC decays like the signal's own persistence"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    dec = const["_deciles"].drop(columns="LS").mean() * 100
    ax.bar(dec.index, dec.values, color="#176B87"); ax.set_xticks(list(dec.index))
    ax.set_xlabel("Signal decile at signal_time (1 = lowest signal, 10 = highest)"); ax.set_ylabel("Mean next-month return (% per month)")
    ax.set_title(f"Equal-weight decile returns; N={const['n_names']}, {const['months']} months (constructed)")
    fig.savefig(fig_dir / FIGURES[0], dpi=150); plt.close(fig)
    # 2: pooled vs per date
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    ax.scatter(pooled["_market_next"] * 100, pooled["_signal_level"], s=14, color="#654A8B", alpha=0.7)
    ax.set_xlabel("Next-month market return (%)"); ax.set_ylabel("Cross-sectional mean of signal (signal units)")
    ax.set_title("The signal's date level co-moves with the market; no ordering information")
    ax = axes[1]
    ax.hist(pooled["_per_date"], bins=24, color="#176B87", alpha=0.85)
    ax.axvline(pooled["mean_ic"], color="k", lw=1.3, label=f"mean per-date IC = {pooled['mean_ic']:.3f}")
    ax.axvline(pooled["pooled_corr"], color="#D05A36", lw=1.8, ls="--", label=f"pooled correlation = {pooled['pooled_corr']:.3f}")
    ax.set_xlabel("Per-date Pearson IC (unitless)"); ax.set_ylabel("Number of months")
    ax.set_title("Pooling mixes date-level co-movement into the correlation"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[1], dpi=150); plt.close(fig)
    # 3: overlap
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    hs = sorted(overlap["by_horizon"]); tab = overlap["by_horizon"]
    ax = axes[0]; x = np.arange(len(hs)); wd = 0.26
    ax.bar(x - wd, [tab[h]["sd_naive_t"] for h in hs], wd, color="#D05A36", label="naive t (iid across dates)")
    ax.bar(x, [tab[h]["sd_nw_t"] for h in hs], wd, color="#176B87", label="Newey-West t, lags = h - 1")
    ax.bar(x + wd, [tab[h]["sd_non_overlap_t"] for h in hs], wd, color="#654A8B", label="every h-th month (non-overlapping)")
    ax.axhline(1, color="k", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([str(h) for h in hs])
    ax.set_xlabel("Label horizon h (months, overlapping labels)"); ax.set_ylabel("SD of t across null worlds (1 = correct)")
    ax.set_title("Null world: overlap inflates the naive t"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    ax.bar(x - wd, [100 * tab[h]["reject_naive"] for h in hs], wd, color="#D05A36", label="naive")
    ax.bar(x, [100 * tab[h]["reject_nw"] for h in hs], wd, color="#176B87", label="Newey-West")
    ax.bar(x + wd, [100 * tab[h]["reject_non_overlap"] for h in hs], wd, color="#654A8B", label="non-overlapping (t critical value)")
    ax.axhline(5, color="k", ls="--", lw=1); ax.set_xticks(x); ax.set_xticklabels([str(h) for h in hs])
    ax.set_xlabel("Label horizon h (months)"); ax.set_ylabel("Share of null worlds rejected at nominal 5% (%)")
    ax.set_title(f"Size: {overlap['worlds']} worlds, {overlap['months']} months, {overlap['n_names']} names, signal rho {overlap['signal_rho']}"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[2], dpi=150); plt.close(fig)
    # 4: industries
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    ic = real["_ic"].dropna(); roll = ic.rolling(120).mean()
    x = ic.index.to_timestamp(how="end")
    ax.plot(x, roll.values, color="#176B87", lw=1.4)
    ax.axhline(0, color="0.4", lw=0.8); ax.axhline(float(ic.mean()), color="#D05A36", ls="--", lw=1, label=f"full-sample mean {ic.mean():.3f}")
    ax.set_xlabel("Signal month (end of month)"); ax.set_ylabel("Rolling 120-month mean Spearman IC (unitless)")
    ax.set_title("French 10 industries, 12-1 signal vs next-month return"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    d = real["_decay"]; ks = d.index.to_numpy(); se = np.abs(d["mean_ic"].to_numpy() / d["t_nw"].to_numpy())
    ax.errorbar(ks, d["mean_ic"], yerr=2 * se, fmt="o", color="#176B87", capsize=3)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Lead k (months after signal_time)"); ax.set_ylabel("Mean Spearman IC at lead k (unitless)")
    ax.set_title("IC decay of the 12-1 industry signal, 1927-06 to 2026-07 signals")
    fig.savefig(fig_dir / FIGURES[3], dpi=150); plt.close(fig)


# --------------------------------------------------------------------------- driver
def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def run(out_dir: Path, fig_dir: Path, *, worlds: int = 600) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch23_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 23 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True); fig_dir.mkdir(parents=True, exist_ok=True)
    const = constructed_study(constructed_panel())
    pooled = pooled_vs_per_date()
    overlap = overlap_null_study(worlds=worlds)
    overlap_iid = overlap_null_study(seed=SEED + 3, worlds=worlds, signal_rho=0.0)
    returns, _, provenance = load_industries_and_rf()
    real = industry_study(returns)
    _figures(const, pooled, overlap, real, fig_dir)
    result = {"seed": SEED, "hand_examples": hand_examples(), "constructed": const, "pooled_vs_per_date": pooled,
              "overlap_null": overlap, "overlap_null_iid_signal": overlap_iid, "french_industries": real,
              "provenance": {"french_hashes": provenance["sha256"], "is_point_in_time": provenance["is_point_in_time"]}}
    (out_dir / "ch23_results.json").write_text(json.dumps(_clean(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _clean(result)


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch23_cross_sectional_research_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(default_run / "results"))
    parser.add_argument("--figures", default=str(default_run / "figures"))
    parser.add_argument("--worlds", type=int, default=600)
    args = parser.parse_args()
    result = run(Path(args.out), Path(args.figures), worlds=args.worlds)
    c, p, r = result["constructed"], result["pooled_vs_per_date"], result["french_industries"]
    print(f"constructed: Spearman IC mean {c['ic_spearman']['mean']:.4f} (t {c['ic_spearman']['t_naive']:.1f}); decile LS {c['decile_ls_top_minus_bottom']['mean_pct']:.3f}%/mo")
    print(f"pooled corr {p['pooled_corr']:.3f} vs mean per-date IC {p['mean_ic']:.3f}")
    print(f"French 12-1 RankIC all {r['rank_ic_by_period']['all']['mean']:.4f} (t {r['rank_ic_by_period']['all']['t_nw']:.2f})")


if __name__ == "__main__":
    main()
