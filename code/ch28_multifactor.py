"""Chapter 28 CLI: same-date preprocessing (winsorize, z-score, neutralize), orthogonalization order, combining signals,
missing factors, tuning weights on the test, and factor correlations.

Run from the course root::

    .venv/bin/python code/ch28_multifactor.py

Outputs ``qa/a5/claude/results/ch28/ch28_results.json`` and ``figures/a5/ch28_*.png`` (refuses to overwrite).
Constructed: hand examples and the multi-factor panel (seed 20261121; known data-generating process) plus a 60-world repetition
(seeds 20261122 ...). Real: the frozen FF5 aggregate factor returns (published, revised history, not stock-level) and two strategies
built from the frozen French 10 industries (cross-sectional 12-1 momentum and BAB; Chapters 25 and 27), which are not the published
UMD or BAB factors.

Reader packaging note: paths above document historical source outputs only.
Current CLI defaults write to one unique runs/cli_<chapter>_<uuid>/results and figures.
French CLI branches require separate rights and execution authorization;
use the adapted Notebook for the default offline constructed teaching route.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.factor_preprocessing import (  # noqa: E402
    average_pairwise_correlation, combine_signals, composite_ic, diversified_sharpe, expanding_zscore, neutralize,
    normal_scores, optimal_composite_weights, orthogonalize, sequential_orthogonal_ic, winsorize_cross_section,
    zscore_cross_section,
)
from quant_course.factor_research import ic_series, lead_return, quantile_long_short_weights  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.portfolio_construction import project_to_constraints  # noqa: E402
from quant_course.low_risk import bab_returns, rolling_beta, vasicek_shrink  # noqa: E402
from quant_course.momentum import cross_sectional_momentum_weights, strategy_returns  # noqa: E402

SEED = 20261121
SWEEP_WORLDS = 60
FACTORS = ("value", "momentum", "quality")
R_TRUE = np.array([[1.0, -0.3, -0.3], [-0.3, 1.0, 0.2], [-0.3, 0.2, 1.0]])    # correlation of the true signals within a date
LOAD = np.array([0.0030, 0.0040, 0.0025])                                       # monthly return per unit sd of each true signal
SIZE_LOAD = np.array([-0.5, 0.0, 0.3])                                          # nuisance: raw signal also loads on log size
N_INDUSTRY, IND_SHOCK_SD, IDIO_SD = 10, 0.02, 0.07
FIGURES = ("ch28_preprocessing.png", "ch28_neutralization.png", "ch28_composites.png", "ch28_factor_correlation.png")
FF_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"


# ------------------------------------------------------------------ hand examples
def hand_examples() -> dict:
    out: dict = {}
    idx = pd.period_range("2026-06", periods=1, freq="M")
    x = pd.DataFrame([[1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]], index=idx, columns=[f"s{i}" for i in range(11)])
    w = winsorize_cross_section(x, lower=0.1, upper=0.9, min_names=10)
    out["winsor"] = {"raw": x.iloc[0].tolist(), "winsorized": w.iloc[0].tolist(), "z_raw_of_5": float(zscore_cross_section(x).iloc[0, 4]),
                     "z_winsorized_of_5": float(zscore_cross_section(w).iloc[0, 4]), "z_winsorized_of_10": float(zscore_cross_section(w).iloc[0, 9]),
                     "mean_raw": float(x.iloc[0].mean()), "sd_raw": float(x.iloc[0].std(ddof=1)), "mean_winsorized": float(w.iloc[0].mean()),
                     "sd_winsorized": float(w.iloc[0].std(ddof=1)),
                     "normal_score_of_100": float(normal_scores(x).iloc[0, 10]), "normal_score_of_10": float(normal_scores(x).iloc[0, 9])}
    cols = list("abcdef")
    sig = pd.DataFrame([[1.0, -1.0, 0.0, 11.0, 10.0, 9.0]], index=idx, columns=cols)
    ret = pd.DataFrame([[0.05, 0.03, 0.04, -0.03, -0.04, -0.05]], index=idx, columns=cols)
    groups = pd.Series(["A", "A", "A", "B", "B", "B"], index=cols)
    res = neutralize(sig, groups=groups)
    corr = lambda a, b: float(np.corrcoef(np.asarray(a, dtype=float), np.asarray(b, dtype=float))[0, 1])
    out["neutralize"] = {"residual": res.iloc[0].tolist(), "raw_pearson_ic": corr(sig.iloc[0], ret.iloc[0]), "neutral_pearson_ic": corr(res.iloc[0], ret.iloc[0])}
    A = np.array([[1.0, 1.0, 1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]])             # industry indicator rows (their sum is the dollar row)
    proj = project_to_constraints(sig.iloc[0].to_numpy(), A)
    out["projection"] = {"projected": proj.tolist(), "max_abs_diff_from_neutralized": float(np.abs(proj - res.iloc[0].to_numpy()).max()),
                         "dollar_net": float(proj.sum()), "industry_nets": (A @ proj).tolist()}
    rho, r12 = np.array([0.04, 0.02]), 0.5
    R2 = np.array([[1.0, r12], [r12, 1.0]])
    out["orthogonal"] = {"equal_weight": composite_ic(rho, R2), "order_1_then_2": sequential_orthogonal_ic(rho, R2, [0, 1]),
                         "order_2_then_1": sequential_orthogonal_ic(rho, R2, [1, 0]), "optimal_ic": optimal_composite_weights(rho, R2)[1],
                         "optimal_weights": optimal_composite_weights(rho, R2)[0].tolist()}
    z = pd.DataFrame([[2.0, 1.0]], index=idx, columns=["s1", "s2"])
    one = pd.DataFrame([[np.nan, 1.0]], index=idx, columns=["s1", "s2"])
    zs = {"f1": pd.DataFrame([[2.0, np.nan]], index=idx, columns=["s1", "s2"]), "f2": pd.DataFrame([[2.0, 1.0]], index=idx, columns=["s1", "s2"])}
    rw, nrw = combine_signals(zs, {"f1": 0.5, "f2": 0.5}, missing="reweight")
    zf, _ = combine_signals(zs, {"f1": 0.5, "f2": 0.5}, missing="zero")
    del z, one
    out["missing"] = {"complete_name": float(rw.iloc[0, 0]), "reweighted_single_factor_name": float(rw.iloc[0, 1]), "zero_filled_single_factor_name": float(zf.iloc[0, 1])}
    out["diversification"] = {"sharpe_k3_rho0p2": diversified_sharpe(0.3, 3, 0.2), "sharpe_k3_rho0p8": diversified_sharpe(0.3, 3, 0.8),
                              "sharpe_k3_rho0": diversified_sharpe(0.3, 3, 0.0), "avg_corr_example": average_pairwise_correlation(np.array([[1, .2, .4], [.2, 1, .0], [.4, .0, 1]]))}
    path = pd.DataFrame({"x": [1.0, 2.0, 3.0, 10.0]}, index=pd.period_range("2026-01", periods=4, freq="M"))
    exp = expanding_zscore(path, min_periods=3)
    full = (path["x"] - path["x"].mean()) / path["x"].std(ddof=1)
    out["time_series_scaling"] = {"expanding_z_at_third_obs": float(exp["x"].iloc[2]), "full_sample_z_at_third_obs": float(full.iloc[2]),
                                  "full_sample_mean": float(path["x"].mean()), "full_sample_sd": float(path["x"].std(ddof=1))}
    return out


# ------------------------------------------------------------------ constructed world
def multifactor_world(seed: int = SEED, n: int = 300, months: int = 120) -> dict:
    """Row t: raw signals known at the end of month t; ``returns`` row t holds the return of month t (first row NaN), so
    ``lead_return(returns, 1)`` row t is the label of the signals of row t. Raw signal k = true_k + industry offset (AR(1), nuisance)
    + size loading * log size + rare large outliers; the return depends on the true signals only (plus industry shock and noise)."""
    rng = np.random.default_rng(seed)
    index = pd.period_range("2010-01", periods=months, freq="M")
    cols = [f"S{i:03d}" for i in range(n)]
    ind = np.arange(n) % N_INDUSTRY
    size = np.zeros((months, n))
    size[0] = rng.normal(size=n)
    for t in range(1, months):
        size[t] = 0.95 * size[t - 1] + np.sqrt(1 - 0.95 ** 2) * rng.normal(size=n)
    true = rng.multivariate_normal(np.zeros(3), R_TRUE, size=(months, n))
    off = np.zeros((months, 3, N_INDUSTRY))
    off[0] = rng.normal(size=(3, N_INDUSTRY))
    for t in range(1, months):
        off[t] = 0.9 * off[t - 1] + np.sqrt(1 - 0.81) * rng.normal(size=(3, N_INDUSTRY))
    outlier = rng.random((months, n, 3)) < 0.02
    big = rng.normal(0.0, 8.0, (months, n, 3))
    raw = true + np.transpose(off[:, :, ind], (0, 2, 1)) + size[:, :, None] * SIZE_LOAD + outlier * big
    shock = rng.normal(0.0, IND_SHOCK_SD, (months, N_INDUSTRY))
    nxt = true @ LOAD + shock[:, ind] + rng.normal(0.0, IDIO_SD, (months, n))
    returns = np.vstack([np.full((1, n), np.nan), nxt[:-1]])
    frame = lambda a: pd.DataFrame(a, index=index, columns=cols)
    return {"raw": {f: frame(raw[:, :, k]) for k, f in enumerate(FACTORS)}, "true": {f: frame(true[:, :, k]) for k, f in enumerate(FACTORS)},
            "returns": frame(returns), "industry": pd.Series([f"I{i:02d}" for i in ind], index=cols), "size": frame(size)}


def process(world: dict, *, winsor: bool = True, neutral: bool = True) -> dict:
    """winsorize (same date) -> neutralize on industry and size (same date) -> z-score (same date)."""
    out = {}
    for f, panel in world["raw"].items():
        p = winsorize_cross_section(panel) if winsor else panel
        if neutral:
            p = neutralize(p, groups=world["industry"], controls={"size": world["size"]})
        out[f] = zscore_cross_section(p)
    return out


def ic_stats(signal: pd.DataFrame, label: pd.DataFrame, method: str) -> dict:
    ic = ic_series(signal, label, method=method)["ic"].dropna()
    return {"mean": float(ic.mean()), "t": float(ic.mean() / (ic.std(ddof=1) / np.sqrt(len(ic)))), "months": int(len(ic))}


def true_ic() -> dict:
    sd = np.sqrt(LOAD @ R_TRUE @ LOAD + IND_SHOCK_SD ** 2 + IDIO_SD ** 2)
    rho = R_TRUE @ LOAD / sd
    return {"rho": dict(zip(FACTORS, rho.tolist())), "sd_return": float(sd), "rho_vec": rho}


def tuning_sweep(n_worlds: int = SWEEP_WORLDS) -> dict:
    rows = []
    atten = {f: {"true": [], "raw": [], "winsor": [], "neutral_winsor": []} for f in FACTORS}
    for k in range(1, n_worlds + 1):
        w = multifactor_world(SEED + k)
        label = lead_return(w["returns"], 1)
        for f in FACTORS:
            wins = winsorize_cross_section(w["raw"][f])
            neu = neutralize(wins, groups=w["industry"], controls={"size": w["size"]})
            for key, panel in (("true", w["true"][f]), ("raw", w["raw"][f]), ("winsor", wins), ("neutral_winsor", neu)):
                atten[f][key].append(float(ic_series(panel, label, method="pearson")["ic"].mean()))
        z = process(w)
        half = len(label) // 2
        ics = {f: ic_series(z[f], label, method="spearman")["ic"] for f in FACTORS}
        ic_disc = {f: float(ics[f].iloc[:half].mean()) for f in FACTORS}
        tuned = {f: max(ic_disc[f], 0.0) for f in FACTORS}
        if sum(tuned.values()) == 0:
            tuned = {f: 1.0 for f in FACTORS}
        best = max(ic_disc, key=ic_disc.get)
        schemes = {"equal": {f: 1.0 for f in FACTORS}, "tuned_on_discovery": tuned, "best_single_on_discovery": {f: float(f == best) for f in FACTORS}}
        rec = {}
        for name, wts in schemes.items():
            comp, _ = combine_signals(z, wts)
            s = ic_series(comp, label, method="spearman")["ic"]
            rec[name] = (float(s.iloc[:half].mean()), float(s.iloc[half:].mean()))
        rows.append(rec)
    summary = {}
    for name in ("equal", "tuned_on_discovery", "best_single_on_discovery"):
        disc = np.array([r[name][0] for r in rows])
        hold = np.array([r[name][1] for r in rows])
        summary[name] = {"discovery_mean": float(disc.mean()), "holdout_mean": float(hold.mean()), "optimism_mean": float((disc - hold).mean())}
    hold_eq = np.array([r["equal"][1] for r in rows])
    hold_tuned = np.array([r["tuned_on_discovery"][1] for r in rows])
    summary["share_tuned_beats_equal_in_holdout"] = float((hold_tuned > hold_eq).mean())
    hold_best = np.array([r["best_single_on_discovery"][1] for r in rows])
    summary["share_best_single_beats_equal_in_holdout"] = float((hold_best > hold_eq).mean())
    summary["_diff"] = {"tuned_on_discovery": hold_tuned - hold_eq, "best_single_on_discovery": hold_best - hold_eq}
    summary["worlds"] = n_worlds
    summary["attenuation"] = {f: {key: float(np.mean(v)) for key, v in d.items()} for f, d in atten.items()}
    for f in FACTORS:
        a = summary["attenuation"][f]
        a["ratio_raw_to_true"], a["ratio_winsor_to_true"], a["ratio_neutral_winsor_to_true"] = (a["raw"] / a["true"], a["winsor"] / a["true"], a["neutral_winsor"] / a["true"])
    summary["_optimism"] = {n: np.array([r[n][0] - r[n][1] for r in rows]) for n in ("equal", "tuned_on_discovery", "best_single_on_discovery")}
    return summary


def constructed_study() -> dict:
    w = multifactor_world()
    label = lead_return(w["returns"], 1)
    t = true_ic()
    result: dict = {"true": {k: v for k, v in t.items() if k != "rho_vec"}}
    variants = {}
    for f in FACTORS:
        raw = w["raw"][f]
        wins = winsorize_cross_section(raw)
        neu = neutralize(wins, groups=w["industry"], controls={"size": w["size"]})
        variants[f] = {"raw_pearson": ic_stats(raw, label, "pearson"), "raw_spearman": ic_stats(raw, label, "spearman"),
                       "winsor_pearson": ic_stats(wins, label, "pearson"), "winsor_spearman": ic_stats(wins, label, "spearman"),
                       "neutral_winsor_pearson": ic_stats(neu, label, "pearson"), "neutral_winsor_spearman": ic_stats(neu, label, "spearman"),
                       "true_signal_pearson": ic_stats(w["true"][f], label, "pearson"), "true_ic_analytic": t["rho"][f]}
    result["factor_ic"] = variants
    z = process(w)
    result["z_cross_section_check"] = {f: {"mean_abs_row_mean": float(z[f].mean(axis=1).abs().mean()), "mean_row_sd": float(z[f].std(axis=1, ddof=1).mean())} for f in FACTORS}
    # residual diagnostics on one date
    date = z["value"].index[60]
    res = neutralize(winsorize_cross_section(w["raw"]["value"]), groups=w["industry"], controls={"size": w["size"]}).loc[date]
    ind_means = res.groupby(w["industry"]).mean().abs().max()
    size_corr = float(np.corrcoef(res.to_numpy(), w["size"].loc[date].to_numpy())[0, 1])
    result["residual_diagnostics"] = {"date": str(date), "max_abs_industry_mean": float(ind_means), "corr_with_size": size_corr}
    # composites
    equal, _ = combine_signals(z, {f: 1.0 for f in FACTORS})
    oracle, _ = combine_signals(z, {f: float(LOAD[i]) for i, f in enumerate(FACTORS)})
    comps = {"equal": equal, "oracle_true_loadings": oracle}
    orders = {"V>M>Q": (0, 1, 2), "Q>M>V": (2, 1, 0), "M>V>Q": (1, 0, 2), "M>Q>V": (1, 2, 0)}
    rhos, R = t["rho_vec"], R_TRUE
    seq = {}
    for name, order in orders.items():
        resid = {}
        done: list = []
        for j in order:
            f = FACTORS[j]
            if done:
                resid[f] = zscore_cross_section(orthogonalize(z[f], [z[g] for g in done]))
            else:
                resid[f] = z[f]
            done.append(f)
        comp, _ = combine_signals(resid, {f: 1.0 for f in FACTORS})
        comps["sequential " + name] = comp
        seq[name] = float(sequential_orthogonal_ic(rhos, R, order))
    result["composite_ic"] = {name: {"spearman": ic_stats(c, label, "spearman"), "pearson": ic_stats(c, label, "pearson")} for name, c in comps.items()}
    ow, oic = optimal_composite_weights(rhos, R)
    true_z = {f: zscore_cross_section(w["true"][f]) for f in FACTORS}
    true_eq, _ = combine_signals(true_z, {f: 1.0 for f in FACTORS})
    result["true_signal_equal_weight_pearson"] = ic_stats(true_eq, label, "pearson")
    result["composite_analytic"] = {"equal": composite_ic(rhos, R), "oracle_loading_weights": composite_ic(rhos, R, LOAD), "optimal": oic,
                                    "optimal_weights": dict(zip(FACTORS, ow.tolist())), "sequential": seq, "max_single": float(rhos.max())}
    # overlap of the top quintiles (share of one factor's top quintile that is also in the other's); independence would give 0.20
    top = {f: z[f].rank(axis=1, pct=True) > 0.8 for f in FACTORS}
    result["top_quintile_overlap"] = {f"{a}|{b}": float((top[a] & top[b]).to_numpy().sum() / top[a].to_numpy().sum()) for a, b in (("value", "momentum"), ("value", "quality"), ("momentum", "quality"))}
    # constraints: neutralize the signal first, or take raw quintile weights and project them onto industry neutrality
    raw_comp, _ = combine_signals({f: zscore_cross_section(winsorize_cross_section(w["raw"][f])) for f in FACTORS}, {f: 1.0 for f in FACTORS})
    ind_rows = np.array([(w["industry"].to_numpy() == name).astype(float) for name in sorted(w["industry"].unique())])
    size_arr = w["size"].to_numpy()
    def constrained(weights_df: pd.DataFrame) -> pd.DataFrame:
        out = weights_df.copy()
        for i in range(len(out)):
            if weights_df.iloc[i].abs().sum() > 0:
                out.iloc[i] = project_to_constraints(weights_df.iloc[i].to_numpy(), ind_rows)
        return out
    books = {"neutralized signal, quintile weights": quantile_long_short_weights(equal, 5),
             "raw composite, quintile weights": quantile_long_short_weights(raw_comp, 5)}
    books["raw composite, quintile weights, projected to industry neutrality"] = constrained(books["raw composite, quintile weights"])
    cons_res = {}
    for name, wts in books.items():
        g = strategy_returns(wts, w["returns"]).dropna()
        net = np.abs(np.stack([ind_rows @ wts.iloc[i].to_numpy() for i in range(len(wts))])).max(axis=1)
        cons_res[name] = {"mean_pct": float(100 * g.mean()), "t": float(g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))), "sd_pct": float(100 * g.std(ddof=1)),
                          "mean_gross": float(wts.abs().sum(axis=1).mean()), "mean_max_abs_industry_net": float(net.mean()),
                          "mean_abs_size_exposure": float(np.mean([abs(wts.iloc[i].to_numpy() @ size_arr[i]) for i in range(len(wts))]))}
    result["constraints"] = cons_res
    # missing factors: 15% of each processed signal removed at random (MCAR)
    rng = np.random.default_rng(SEED + 1000)
    holes = {f: z[f].mask(rng.random(z[f].shape) < 0.15) for f in FACTORS}
    miss = {}
    for name, kwargs in (("zero fill", {"missing": "zero", "min_factors": 1}), ("reweight (min 2)", {"missing": "reweight", "min_factors": 2}),
                         ("reweight (min 1)", {"missing": "reweight", "min_factors": 1}), ("drop (all 3 needed)", {"missing": "reweight", "min_factors": 3})):
        comp, cnt = combine_signals(holes, {f: 1.0 for f in FACTORS}, **kwargs)
        top = comp.rank(axis=1, pct=True) > 0.8
        single = cnt == 1
        entry = {**ic_stats(comp, label, "spearman"), "coverage": float(comp.notna().to_numpy().mean())}
        both = single & comp.notna()
        if both.to_numpy().any():
            entry["share_of_top_quintile_that_are_single_factor_names"] = float((top & single).to_numpy().sum() / max(top.to_numpy().sum(), 1))
            entry["share_of_valid_names_that_are_single_factor"] = float(both.to_numpy().sum() / max(comp.notna().to_numpy().sum(), 1))
        miss[name] = entry
    result["missing"] = miss
    result["tuning"] = tuning_sweep()
    result["_series"] = {"raw_value_row": w["raw"]["value"].loc[date], "winsor_value_row": winsorize_cross_section(w["raw"]["value"]).loc[date], "res_row": res,
                         "industry": w["industry"], "size_row": w["size"].loc[date], "date": date, "ic_variants": variants, "composites": result["composite_ic"],
                         "analytic": result["composite_analytic"], "tuning_diff": result["tuning"]["_diff"], "tuning_share": result["tuning"]["share_tuned_beats_equal_in_holdout"]}
    return result


# ------------------------------------------------------------------ real aggregate factors
def real_study() -> dict:
    ff = json.loads(FF_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff5"]
    path = ROOT / ff["processed_path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != ff["processed_sha256"]:
        raise RuntimeError("FF5 processed file differs from its manifest")
    table = pd.read_csv(path, dtype={"month": str})
    table.index = pd.PeriodIndex(table.pop("month"), freq="M")
    ff3 = json.loads(FF_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff3"]
    path3 = ROOT / ff3["processed_path"]
    if hashlib.sha256(path3.read_bytes()).hexdigest() != ff3["processed_sha256"]:
        raise RuntimeError("FF3 processed file differs from its manifest")
    table3 = pd.read_csv(path3, dtype={"month": str})
    table3.index = pd.PeriodIndex(table3.pop("month"), freq="M")
    returns, rf, prov = load_industries_and_rf()
    excess = returns.sub(rf, axis=0)
    # strategies built from the ten industries (not the published UMD / BAB): return month = signal month + 1
    mom_w = cross_sectional_momentum_weights(returns, window=11, skip=1, n_buckets=5, hold_months=1)
    mom = strategy_returns(mom_w, returns)
    mom.index = mom.index + 1
    mkt = table["Mkt-RF"]
    bab_rows = bab_returns(excess, vasicek_shrink(rolling_beta(excess, table3["Mkt-RF"].reindex(excess.index), window=60, min_periods=36)))
    bab = bab_rows["bab"].copy()
    bab.index = bab.index + 1
    styles = pd.DataFrame({"HML (value)": table["HML"], "RMW (quality)": table["RMW"], "CMA": table["CMA"], "SMB": table["SMB"], "Mkt-RF": table["Mkt-RF"],
                           "industry momentum 12-1": mom.reindex(table.index), "industry BAB": bab.reindex(table.index)}).dropna()
    corr = styles.corr()
    result: dict = {"ff5_sha256": digest, "common_months": int(len(styles)), "first_month": str(styles.index[0]), "last_month": str(styles.index[-1])}
    result["correlation"] = {a: {b: float(corr.loc[a, b]) for b in corr.columns} for a in corr.index}
    periods = {"1963-07..1999-12": ("1963-07", "1999-12"), "2000-01..2026-08": ("2000-01", "2026-08")}
    result["correlation_hml_rmw_by_period"] = {k: float(styles.loc[a:b, "HML (value)"].corr(styles.loc[a:b, "RMW (quality)"])) for k, (a, b) in periods.items()}
    ff_corr = table[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]].corr()
    result["ff5_correlation_full_758"] = {a: {b: float(ff_corr.loc[a, b]) for b in ff_corr.columns} for a in ff_corr.index}
    roll = table["HML"].rolling(60).corr(table["RMW"]).dropna()
    result["rolling_60m_hml_rmw"] = {"min": float(roll.min()), "max": float(roll.max()), "min_end": str(roll.idxmin()), "max_end": str(roll.idxmax()), "last": float(roll.iloc[-1])}
    # three styles: published HML and RMW, plus industry momentum. Equal-risk average with expanding volatility (known at t - 1)
    trio = styles[["HML (value)", "RMW (quality)", "industry momentum 12-1"]]
    vol = trio.expanding(min_periods=60).std().shift(1)
    scaled = (trio / vol).dropna()
    composite = scaled.mean(axis=1)
    sharpe = lambda x: float(x.mean() / x.std(ddof=1) * np.sqrt(12))
    comp_stats = {c: sharpe(scaled[c]) for c in scaled.columns}
    avg_s = float(np.mean(list(comp_stats.values())))
    avg_c = average_pairwise_correlation(scaled.corr().to_numpy())
    result["equal_risk_composite"] = {"months": int(len(scaled)), "first_month": str(scaled.index[0]), "component_sharpe": comp_stats, "composite_sharpe": sharpe(composite),
                                      "average_component_sharpe": avg_s, "average_pairwise_correlation": avg_c, "formula_sharpe": diversified_sharpe(avg_s, 3, avg_c)}
    # full-sample volatility scaling (look-ahead) versus expanding: same months
    full_vol = trio.loc[scaled.index].std(ddof=1)
    leaky = (trio.loc[scaled.index] / full_vol).mean(axis=1)
    result["full_sample_scaling_sharpe_same_months"] = sharpe(leaky)
    result["_series"] = {"styles": styles, "corr": corr, "roll": roll}
    return result


# ------------------------------------------------------------------ figures
def _figures(cons: dict, real: dict, fig_dir: Path) -> None:
    s = cons["_series"]
    # 1 preprocessing
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    raw, wins = s["raw_value_row"], s["winsor_value_row"]
    bins = np.linspace(raw.min(), raw.max(), 60)
    ax.hist(raw.to_numpy(), bins=bins, color="#D05A36", alpha=0.7, label="raw value signal (one date)")
    ax.hist(wins.to_numpy(), bins=bins, color="#176B87", alpha=0.7, label="after winsorizing at 1% / 99% (same date)")
    ax.set_yscale("log"); ax.set_xlabel("Signal value (unitless)"); ax.set_ylabel("Number of stocks (log scale)")
    ax.set_title("Same-date winsorizing pulls in the large outliers"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    labels = ["raw\nPearson", "winsorized\nPearson", "neutral+wins.\nPearson", "neutral+wins.\nSpearman", "true signal\nPearson"]
    keys = ["raw_pearson", "winsor_pearson", "neutral_winsor_pearson", "neutral_winsor_spearman", "true_signal_pearson"]
    x = np.arange(len(labels)); width = 0.26
    for j, (f, color) in enumerate(zip(FACTORS, ("#176B87", "#D05A36", "#654A8B"))):
        vals = [s["ic_variants"][f][k]["mean"] for k in keys]
        ax.bar(x + (j - 1) * width, vals, width, color=color, label=f)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8); ax.axhline(0, color="0.4", lw=0.8)
    ax.set_ylabel("Mean monthly IC (119 months)"); ax.set_title("Each step restores part of the true IC (constructed panel)"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[0], dpi=150); plt.close(fig)
    # 2 neutralization
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ind = s["industry"]
    order = sorted(ind.unique())
    for ax, series, title, ylabel in ((axes[0], s["winsor_value_row"], "Winsorized raw signal: industry offsets dominate", "Value signal, winsorized (unitless)"),
                                      (axes[1], s["res_row"], "After neutralizing on industry and size", "Residual (unitless)")):
        for j, name in enumerate(order):
            v = series[ind == name].to_numpy()
            ax.scatter(np.full(len(v), j) + np.random.default_rng(j).uniform(-0.25, 0.25, len(v)), v, s=7, color="#176B87", alpha=0.6)
            ax.hlines(np.nanmean(v), j - 0.35, j + 0.35, color="#D05A36", lw=2)
        ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=45, fontsize=8); ax.axhline(0, color="0.4", lw=0.6)
        ax.set_xlabel("Industry (orange bar = industry mean on this date)"); ax.set_ylabel(ylabel); ax.set_title(title)
    fig.savefig(fig_dir / FIGURES[1], dpi=150); plt.close(fig)
    # 3 composites
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    names = list(s["composites"])
    vals = [s["composites"][n]["pearson"]["mean"] for n in names]
    err = [2 * s["composites"][n]["pearson"]["mean"] / s["composites"][n]["pearson"]["t"] for n in names]
    ax.barh(range(len(names)), vals, xerr=err, color="#176B87", capsize=3)
    ax.axvline(s["analytic"]["optimal"], color="#D05A36", ls="--", label=f"best possible IC {s['analytic']['optimal']:.4f}")
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=8.5); ax.invert_yaxis()
    ax.set_xlabel("Mean monthly Pearson IC (bar = ±2 se)"); ax.set_title("Composites of the same three processed signals"); ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    ax = axes[1]
    for name, color, label in (("tuned_on_discovery", "#D05A36", "weights tuned on the discovery half"), ("best_single_on_discovery", "#654A8B", "best single factor on the discovery half")):
        ax.hist(s["tuning_diff"][name], bins=15, alpha=0.6, color=color, label=label)
    ax.axvline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Hold-out IC minus hold-out IC of equal weights (60 worlds)"); ax.set_ylabel("Number of worlds")
    ax.set_title(f"Tuned weights beat equal weights in only {100 * s['tuning_share']:.0f}% of worlds"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[2], dpi=150); plt.close(fig)
    # 4 factor correlation
    corr, roll = real["_series"]["corr"], real["_series"]["roll"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True, gridspec_kw={"width_ratios": [1.05, 1]})
    ax = axes[0]
    im = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8.5)
    ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.index, fontsize=8.5)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8, color="w" if abs(corr.iloc[i, j]) > 0.55 else "k")
    fig.colorbar(im, ax=ax, label="correlation (unitless)")
    ax.set_title(f"Monthly factor-return correlations, {real['first_month']} to {real['last_month']}")
    ax = axes[1]
    ax.plot(roll.index.to_timestamp(how="end"), roll.values, color="#654A8B", lw=1.1)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Window end month"); ax.set_ylabel("Rolling 60-month correlation, HML and RMW")
    ax.set_title("Published value and quality returns: the correlation moves")
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
    if isinstance(obj, np.ndarray):
        return [_clean(v) for v in obj.tolist()]
    return obj


def run(out_dir: Path, fig_dir: Path) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch28_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 28 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    cons = constructed_study()
    real = real_study()
    _figures(cons, real, fig_dir)
    result = {"hand_examples": hand_examples(), "constructed": cons, "real": real, "seed": SEED, "sweep_worlds": SWEEP_WORLDS}
    cleaned = _clean(result)
    (out_dir / "ch28_results.json").write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cleaned


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch28_multifactor_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(default_run / "results"))
    parser.add_argument("--figures", default=str(default_run / "figures"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    c = r["constructed"]
    print("Spearman IC of composites:", {k: round(v["spearman"]["mean"], 4) for k, v in c["composite_ic"].items()})
    print("tuning:", {k: (round(v["discovery_mean"], 4), round(v["holdout_mean"], 4)) for k, v in c["tuning"].items() if isinstance(v, dict) and "discovery_mean" in v})
    print("real HML-RMW corr:", round(r["real"]["correlation"]["HML (value)"]["RMW (quality)"], 3))


if __name__ == "__main__":
    main()
