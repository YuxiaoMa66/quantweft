"""Chapter 41 (Unsupervised Learning): PCA hand checks, train-only PCA vs full-sample PCA, explained variance vs
prediction, k-means and HMM state labels, and the regime-timing comparison with lagged execution and costs.

    .venv/bin/python code/ch41_unsupervised.py --out <new dir> [--figures-dir course/zh/chapters/ch41/figures]

Every number is CONSTRUCTED teaching data. Registered before the first run (A8-B DECISION_LOG D10):
factor panel = simulate_factor_panel(1000 days, 50 assets, factor_vols=(0.010, 0.005, 0.003), idio_vol=0.015,
seed=4101); noise panel = iid N(0, 0.015^2), same size, seed 4103; PCA k=3, training windows 60 and 250 days, test the
next 21 days, step 21. Regime market = simulate_markov_regimes(3000 days, p_stay=(0.98, 0.95), mus=(0.0005, -0.001),
sigmas=(0.007, 0.02), seed=4102); training = first 1000 days, test = the remaining 2000. Clock: ret[t] is the close
t-1 -> close t return; a rule's signal at the close of t uses data <= t (except the leaking variants, which say so),
the position is traded at the close of t+1 and earns ret[t+2]; cost 10 bp one way on |change in weight|.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.mixture import GaussianMixture

from quant_course import unsupervised_tools as ut

ROOT = Path(__file__).resolve().parents[1]
K = 3
FEE = 0.001
P_TRUE = np.array([[0.98, 0.02], [0.05, 0.95]])
MUS, SIGMAS = (0.0005, -0.001), (0.007, 0.02)


# ---------------------------------------------------------------------------------------------------------------------
# Hand checks (Sections 3, 6, 8.1, 8.3)
# ---------------------------------------------------------------------------------------------------------------------

def exact_cov_sample(cov: np.ndarray, n: int = 400, seed: int = 0) -> pd.DataFrame:
    """A sample whose ddof=1 covariance equals ``cov`` exactly (whitened draws times a Cholesky factor)."""
    z = np.random.default_rng(seed).normal(size=(n, cov.shape[0]))
    z -= z.mean(axis=0)
    w = np.linalg.cholesky(np.cov(z, rowvar=False))
    z = z @ np.linalg.inv(w).T
    return pd.DataFrame(z @ np.linalg.cholesky(cov).T, columns=[f"x{j + 1}" for j in range(cov.shape[0])])


def hand_pca() -> dict:
    out = {}
    for name, cov, std in (("cov_2_1_1_2", [[2, 1], [1, 2]], False), ("cov_4_1_1_1", [[4, 1], [1, 1]], False),
                           ("corr_of_4_1_1_1", [[4, 1], [1, 1]], True)):
        fit = ut.pca_fit(exact_cov_sample(np.array(cov, float)), 2, standardize=std)
        out[name] = {"eigenvalues": fit.eigenvalues.round(6).tolist(), "loadings": fit.loadings.round(6).tolist(),
                     "explained_ratio": fit.explained_ratio.round(6).tolist()}
    return out


def hand_hmm() -> dict:
    prev = np.array([0.9, 0.1])
    pred = prev @ P_TRUE
    rows = {}
    for x in (-0.025, -0.010, 0.003):
        filt, _ = ut.hmm_filter_smooth(np.array([x]), means=np.array(MUS), sds=np.array(SIGMAS), transition=P_TRUE, init=pred)
        rows[f"{x:+.3f}"] = filt[0].round(6).tolist()
    w, v = np.linalg.eig(P_TRUE.T)
    stat = np.real(v[:, np.argmax(np.real(w))])
    return {"prior_filtered": prev.tolist(), "predicted": pred.round(6).tolist(), "posterior": rows,
            "stationary": (stat / stat.sum()).round(6).tolist(), "expected_durations": (1 / (1 - np.diag(P_TRUE))).tolist()}


def mp_edges(n_assets: int, n_days: int) -> list[float]:
    q = n_assets / n_days
    return [(1 - np.sqrt(q)) ** 2, (1 + np.sqrt(q)) ** 2]


# ---------------------------------------------------------------------------------------------------------------------
# PCA: in-sample vs out-of-sample, train-only vs full sample, stability
# ---------------------------------------------------------------------------------------------------------------------

def rolling_pca(R: pd.DataFrame, window: int, *, k: int = K, test: int = 21, standardize: bool = True) -> dict:
    ins, oos, full_on_test, cos = [], [], [], []
    full = ut.pca_fit(R, k, standardize=standardize)  # the leaking variant: sees every date, including test windows
    prev = None
    for s in range(window, len(R) - test + 1, test):
        fit = ut.pca_fit(R.iloc[s - window:s], k, standardize=standardize)
        ins.append(float(fit.explained_ratio.sum()))
        oos.append(ut.pca_reconstruction_r2(R.iloc[s:s + test], fit))
        full_on_test.append(ut.pca_reconstruction_r2(R.iloc[s:s + test], full))
        if prev is not None:
            cos.append(ut.subspace_cosines(prev.loadings, fit.loadings).tolist())
        prev = fit
    cos = np.array(cos)
    return {"n_windows": len(ins), "in_sample_explained_mean": float(np.mean(ins)), "oos_r2_mean": float(np.mean(oos)),
            "full_sample_fit_on_test_r2_mean": float(np.mean(full_on_test)),
            "consecutive_cosines_mean": cos.mean(axis=0).round(4).tolist(), "consecutive_min_cosine_min": float(cos[:, -1].min())}


def eigen_spectrum(R: pd.DataFrame) -> np.ndarray:
    return np.sort(np.linalg.eigvalsh(np.corrcoef(R.to_numpy(), rowvar=False)))[::-1]


def variance_vs_prediction(seed: int = 4104, n: int = 2000) -> dict:
    """Section 6.4: Var(x1)=10 carries no signal, Var(x2)=0.1 carries it. PCR on the first half, test on the second."""
    rng = np.random.default_rng(seed)
    x1 = rng.normal(0, np.sqrt(10.0), n)
    x2 = rng.normal(0, np.sqrt(0.1), n)
    y = 0.5 * x2 + rng.normal(0, 0.1, n)
    X = pd.DataFrame({"x1": x1, "x2": x2})
    tr, te = slice(0, n // 2), slice(n // 2, n)
    out = {}
    for std in (False, True):
        for k in (1, 2):
            fit = ut.pca_fit(X.iloc[tr], k, standardize=std)
            ztr, zte = ut.pca_project(X.iloc[tr], fit), ut.pca_project(X.iloc[te], fit)
            reg = LinearRegression().fit(ztr, y[tr])
            resid = y[te] - reg.predict(zte)
            out[f"{'corr' if std else 'cov'}_k{k}"] = {
                "explained_ratio": fit.explained_ratio.round(4).tolist(), "pc1_loading": fit.loadings[:, 0].round(4).tolist(),
                "oos_r2": float(1 - (resid ** 2).sum() / ((y[te] - y[tr].mean()) ** 2).sum())}
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Regimes
# ---------------------------------------------------------------------------------------------------------------------

def gmm_hmm_params(train_ret: pd.Series, seed: int) -> dict:
    """HMM parameters from the training window only: 2-component Gaussian mixture (means/sds), transition from the
    hard-labelled training sequence; state 0 = lower-volatility component."""
    gm = GaussianMixture(2, random_state=seed, n_init=5).fit(train_ret.to_numpy()[:, None])
    order = np.argsort(np.sqrt(gm.covariances_.ravel()))
    means, sds = gm.means_.ravel()[order], np.sqrt(gm.covariances_.ravel())[order]
    lab = np.argsort(order)[gm.predict(train_ret.to_numpy()[:, None])]
    P = np.ones((2, 2))  # add-one smoothing
    for a, b in zip(lab[:-1], lab[1:]):
        P[a, b] += 1
    P /= P.sum(axis=1, keepdims=True)
    init = np.bincount(lab, minlength=2) / lab.size
    return {"means": means, "sds": sds, "transition": P, "init": init}


def book(ret: pd.Series, signal: pd.Series, *, lag_days: int = 2, fee: float = FEE) -> dict:
    """Weight decided at the close of t (signal[t]) earns ret[t + lag_days]; fee on |dw| at the trade."""
    w = signal.shift(lag_days).fillna(0.0)
    turnover = w.diff().abs().fillna(w.abs())
    net = w * ret - fee * turnover
    wealth = np.concatenate([[1.0], np.cumprod(1 + net.to_numpy())])
    dd = wealth / np.maximum.accumulate(wealth) - 1
    years = len(net) / 252
    return {"ann_return": float(wealth[-1] ** (1 / years) - 1), "ann_vol": float(net.std(ddof=1) * np.sqrt(252)),
            "sharpe": float(net.mean() / net.std(ddof=1) * np.sqrt(252)) if net.std(ddof=1) > 0 else float("nan"),
            "max_drawdown": float(dd.min()), "turnover_ann": float(turnover.sum() / years),
            "time_in_market": float(w.mean()), "wealth_end": float(wealth[-1]), "net": net}


def regime_monte_carlo(seeds: range = range(4200, 4250)) -> dict:
    """Post-hoc robustness diagnostic (D11): the registered regime case repeated on 50 other seeds."""
    rows = {}
    for s in seeds:
        r = regime_case(s, light=True)
        for name, m in r["rules"].items():
            rows.setdefault(name, []).append((m["sharpe"], m["ann_return"], m["turnover_ann"]))
    bh = np.array([v[0] for v in rows["buy_and_hold"]])
    return {name: {"median_sharpe": float(np.median([v[0] for v in vals])),
                   "median_ann_return": float(np.median([v[1] for v in vals])),
                   "median_turnover": float(np.median([v[2] for v in vals])),
                   "share_sharpe_above_buy_and_hold": float(np.mean(np.array([v[0] for v in vals]) > bh))}
            for name, vals in rows.items()} | {"n_seeds": len(seeds)}


def regime_case(seed: int = 4102, light: bool = False) -> dict:
    mk = ut.simulate_markov_regimes(3000, p_stay=(0.98, 0.95), mus=MUS, sigmas=SIGMAS, seed=seed)
    ret, state = mk["ret"], mk["state"]
    train, test = slice(0, 1000), slice(1000, 3000)
    par = gmm_hmm_params(ret.iloc[train], seed)
    filt, smooth = ut.hmm_filter_smooth(ret.to_numpy(), means=par["means"], sds=par["sds"],
                                        transition=par["transition"], init=par["init"])
    # post-hoc diagnostic (D11): the same filter with the simulator's true parameters, unknowable in practice
    filt_true, _ = ut.hmm_filter_smooth(ret.to_numpy(), means=np.array(MUS), sds=np.array(SIGMAS),
                                        transition=P_TRUE, init=np.array([1.0, 0.0]))
    p_calm_filt = pd.Series(filt[:, 0], index=ret.index)
    p_calm_smooth = pd.Series(smooth[:, 0], index=ret.index)
    feats = ut.trailing_state_features(ret, vol_window=21, ret_window=63)
    km = ut.fit_kmeans_states(feats.iloc[train], 2, seed=seed)
    km_state = ut.assign_states(feats, km)
    centred_vol = ret.rolling(21, center=True, min_periods=21).std(ddof=1) * np.sqrt(252)
    vol_cut = float(feats["vol"].iloc[train].median())  # threshold fixed on training data
    signals = {
        "buy_and_hold": pd.Series(1.0, index=ret.index),
        "true_state_same_day [impossible]": (state == 0).astype(float),
        "smoothed_prob_same_day [leaks]": (p_calm_smooth > 0.5).astype(float),
        "smoothed_prob_lagged [leaks]": (p_calm_smooth > 0.5).astype(float),
        "centred_vol_lagged [leaks]": (centred_vol < vol_cut).astype(float),
        "filtered_prob_lagged": (p_calm_filt > 0.5).astype(float),
        "filtered_true_params_lagged [oracle params]": pd.Series((filt_true[:, 0] > 0.5).astype(float), index=ret.index),
        "kmeans_trailing_lagged": (km_state == 0).astype(float),
        "trailing_vol_lagged": (feats["vol"] < vol_cut).astype(float),
    }
    lags = {k: (0 if "same_day" in k else 2) for k in signals}
    test_idx = ret.index[test]
    results, curves = {}, {}
    for name, sig in signals.items():
        b = book(ret.loc[test_idx], sig.reindex(ret.index).fillna(0.0).shift(lags[name]).loc[test_idx], lag_days=0)
        curves[name] = np.cumprod(1 + b.pop("net").to_numpy())
        lab = sig.loc[test_idx]
        b["state_hit_rate"] = float(((lab == 1) == (state.loc[test_idx] == 0)).mean())
        results[name] = b
    if light:
        return {"rules": results}
    stab = {}
    for k in (2, 3, 4):
        s = ut.cluster_stability(feats.iloc[train].dropna(), k, n_boot=20, seed=seed)
        stab[f"k{k}"] = {"ari_mean": s["ari_mean"], "ari_min": s["ari_min"]}
    detect = []  # days from a true calm->turbulent switch until the filtered prob first drops below 0.5
    s = state.loc[test_idx].to_numpy()
    pf = p_calm_filt.loc[test_idx].to_numpy()
    for t in range(1, len(s)):
        if s[t - 1] == 0 and s[t] == 1:
            d = next((j for j in range(t, min(t + 60, len(s))) if pf[j] < 0.5), None)
            if d is not None and (s[t:d + 1] == 1).all():
                detect.append(d - t)
    return {"params_train": {k: np.asarray(v).round(6).tolist() for k, v in par.items()},
            "true_state_share_test": float((state.loc[test_idx] == 0).mean()), "vol_cut_train_median": vol_cut,
            "rules": results, "cluster_stability": stab,
            "filtered_detection_delay_days": {"n": len(detect), "median": float(np.median(detect)) if detect else None,
                                              "mean": float(np.mean(detect)) if detect else None},
            "_curves": curves, "_series": {"state": state, "p_filt": p_calm_filt, "p_smooth": p_calm_smooth,
                                            "test_idx": test_idx}}


# ---------------------------------------------------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------------------------------------------------

def make_figures(res: dict, spectra: dict, reg: dict, figdir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figdir.mkdir(parents=True, exist_ok=True)
    note = "CONSTRUCTED teaching data, not market evidence."
    paths = []

    fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.8))
    for j, (name, ev) in enumerate(spectra.items()):
        ax[0].plot(np.arange(1, len(ev) + 1), ev, marker="o", ms=2.5, lw=1, label=name, color=("#247F82", "#CF8951")[j])
    lo, hi = res["pca"]["mp_edges_N50_T250"]
    ax[0].axhspan(lo, hi, color="#BBBBBB", alpha=0.35, label="Marchenko-Pastur band (N=50, T=250)")
    ax[0].set_yscale("log")
    ax[0].set_xlabel("Eigenvalue rank (correlation matrix, last 250 days)")
    ax[0].set_ylabel("Eigenvalue (log scale)")
    ax[0].legend(frameon=False, fontsize=7)
    rows = [("factor", 60), ("factor", 250), ("noise", 60), ("noise", 250)]
    xs = np.arange(len(rows))
    vals = [(res["pca"][p][f"T{w}"]["in_sample_explained_mean"], res["pca"][p][f"T{w}"]["oos_r2_mean"]) for p, w in rows]
    ax[1].bar(xs - 0.2, [v[0] for v in vals], 0.4, color="#7F7F7F", label="in-sample explained (k=3)")
    ax[1].bar(xs + 0.2, [v[1] for v in vals], 0.4, color="#247F82", label="out-of-sample reconstruction R2")
    ax[1].set_xticks(xs, [f"{p}\nT={w}" for p, w in rows])
    ax[1].set_ylabel("Share of variance (standardized)")
    ax[1].legend(frameon=False, fontsize=7)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, note + " 50 assets; 3-factor panel vs pure noise; next 21 days as test.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig41_1_pca_in_vs_out.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)

    s = reg["_series"]
    idx = s["test_idx"][:400]
    fig, ax = plt.subplots(figsize=(9.0, 3.6))
    turb = (s["state"].loc[idx] == 1).to_numpy()
    ax.fill_between(idx, 0, 1, where=turb, color="#E8C9A8", step="mid", label="true turbulent state")
    ax.plot(idx, 1 - s["p_filt"].loc[idx], color="#247F82", lw=1.1, label="filtered P(turbulent | data to t)")
    ax.plot(idx, 1 - s["p_smooth"].loc[idx], color="#142D36", lw=1.0, ls="--", label="smoothed P(turbulent | all data)")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Date (first 400 test days)")
    ax.set_ylabel("Probability")
    ax.legend(frameon=False, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, note + " HMM parameters estimated on the 1000 training days only.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig41_2_filtered_vs_smoothed.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9.0, 4.0))
    style = {"buy_and_hold": ("#444444", "-"), "true_state_same_day [impossible]": ("#BBBBBB", ":"),
             "smoothed_prob_same_day [leaks]": ("#C0504D", ":"), "smoothed_prob_lagged [leaks]": ("#C0504D", "--"),
             "centred_vol_lagged [leaks]": ("#E0A458", "--"), "filtered_prob_lagged": ("#247F82", "-"),
             "filtered_true_params_lagged [oracle params]": ("#247F82", ":"),
             "kmeans_trailing_lagged": ("#4F81BD", "-"), "trailing_vol_lagged": ("#8064A2", "-")}
    for name, curve in reg["_curves"].items():
        c, ls = style[name]
        ax.plot(reg["_series"]["test_idx"], curve, color=c, ls=ls, lw=1.2, label=name)
    ax.set_yscale("log")
    ax.set_xlabel("Date (2000 test days)")
    ax.set_ylabel("Wealth after 10 bp cost (log scale, start 1)")
    ax.legend(frameon=False, fontsize=7, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, note + " Dotted/dashed = uses information not available at the trade.", fontsize=7.5, color="#444444")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    paths.append(figdir / "fig41_3_regime_rules.png")
    fig.savefig(paths[-1], dpi=200)
    plt.close(fig)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--figures-dir", type=Path, default=None)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    t0 = time.time()
    R, B = ut.simulate_factor_panel(1000, 50, factor_vols=(0.010, 0.005, 0.003), idio_vol=0.015, seed=4101)
    noise = pd.DataFrame(np.random.default_rng(4103).normal(0, 0.015, (1000, 50)), index=R.index, columns=R.columns)
    res = {"data_class": "CONSTRUCTED", "hand": {"pca": hand_pca(), "hmm": hand_hmm()},
           "pca": {"mp_edges_N50_T60": mp_edges(50, 60), "mp_edges_N50_T250": mp_edges(50, 250)}}
    for name, panel in (("factor", R), ("noise", noise)):
        res["pca"][name] = {f"T{w}": rolling_pca(panel, w) for w in (60, 250)}
        res["pca"][name]["top_eigen_last250"] = eigen_spectrum(panel.iloc[-250:])[:5].round(4).tolist()
    res["variance_vs_prediction"] = variance_vs_prediction()
    reg = regime_case()
    res["regime"] = {k: v for k, v in reg.items() if not k.startswith("_")}
    res["regime_monte_carlo_posthoc"] = regime_monte_carlo()
    a.out.mkdir(parents=True)
    spectra = {"3-factor panel": eigen_spectrum(R.iloc[-250:]), "pure noise": eigen_spectrum(noise.iloc[-250:])}
    figs = make_figures(res, spectra, reg, a.out)
    if a.figures_dir is not None:
        a.figures_dir.mkdir(parents=True, exist_ok=True)
        for p in figs:
            (a.figures_dir / p.name).write_bytes(p.read_bytes())
    res["seconds"] = round(time.time() - t0, 1)
    (a.out / "results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    for p in ("factor", "noise"):
        for w in (60, 250):
            r = res["pca"][p][f"T{w}"]
            print(f"PCA {p:6s} T={w:3d}: in-sample {r['in_sample_explained_mean']:.3f} OOS {r['oos_r2_mean']:.3f} "
                  f"full-sample-on-test {r['full_sample_fit_on_test_r2_mean']:.3f} cos {r['consecutive_cosines_mean']}")
    for name, r in res["regime"]["rules"].items():
        print(f"{name:36s} ann {100 * r['ann_return']:+6.2f}% SR {r['sharpe']:+.2f} MDD {100 * r['max_drawdown']:6.1f}% "
              f"TO {r['turnover_ann']:5.1f} hit {r['state_hit_rate']:.3f}")
    for name, r in res["regime_monte_carlo_posthoc"].items():
        if name != "n_seeds":
            print(f"MC50 {name:44s} median SR {r['median_sharpe']:+.2f} share>B&H {r['share_sharpe_above_buy_and_hold']:.2f} "
                  f"TO {r['median_turnover']:.1f}")
    print(f"done in {res['seconds']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
