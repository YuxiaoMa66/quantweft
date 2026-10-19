"""Chapter 25 CLI: exact 12-1 windows, cross-sectional vs time-series momentum on the frozen French industries,
overlapping holdings and costs, the (J, K) grid with its multiple-testing hurdle, and a momentum-crash state check.

Run from the course root::

    .venv/bin/python code/ch25_momentum.py

Outputs ``qa/a5/claude/results/ch25/ch25_results.json`` and ``figures/a5/ch25_*.png`` (refuses to overwrite).
Real data: the hash-checked frozen French 10-industry monthly returns and FF3 market/RF (revised history, 10 value-weight
industry portfolios, not tradable fills, not individual stocks). Hand examples are constructed.
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
from matplotlib.patches import FancyBboxPatch
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.factor_research import newey_west_variance_of_mean  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.momentum import (  # noqa: E402
    cross_sectional_momentum_weights, ex_ante_volatility, net_of_costs, strategy_returns, time_series_sign,
    trailing_bear_state, tsmom_weights,
)

COST_PER_UNIT = 0.0010      # 10 bp per unit of weight traded; an assumption for illustration
FIGURES = ("ch25_windows.png", "ch25_cs_ts_cumulative.png", "ch25_grid_t.png", "ch25_crash_state.png")
FF3_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"


# ------------------------------------------------------------------ hand examples
def hand_examples() -> dict:
    # 8.1: 14 monthly simple returns of one asset, signal at the end of month 13
    r = np.array([0.03, -0.02, 0.05, 0.01, -0.04, 0.06, 0.02, -0.01, 0.04, 0.03, -0.02, 0.05, -0.06, 0.02])
    window = r[1:12]                       # months 2..12 (0-based 1..11): 11 months, skip month 13
    prod = float(np.prod(1 + window) - 1)
    out = {"asset_returns_months_1_to_14": r.tolist(), "window_months": [2, 12], "signal_month": 13,
           "product_12_1": prod, "sum_12_1": float(window.sum()),
           "shifted_earlier_months_1_to_11": float(np.prod(1 + r[0:11]) - 1),
           "shifted_later_months_3_to_13": float(np.prod(1 + r[2:13]) - 1),
           "including_month_13_months_2_to_13": float(np.prod(1 + r[1:13]) - 1)}
    # 8.2: six assets, cross-sectional 12-1 and tercile long-short
    names = list("ABCDEF")
    f = np.array([0.30, 0.12, 0.05, -0.02, -0.10, -0.25]); nxt = np.array([0.02, 0.03, 0.01, 0.00, 0.01, -0.02])
    top, bottom = np.argsort(-f)[:2], np.argsort(f)[:2]
    out["cross_section"] = {"formation": f.tolist(), "next_month": nxt.tolist(), "long": [names[i] for i in top], "short": [names[i] for i in bottom],
                            "ls_return": float(nxt[top].mean() - nxt[bottom].mean())}
    # 8.3: time-series momentum with volatility scaling
    sig = np.array([1.0, -1.0, 1.0]); vol = np.array([0.10, 0.20, 0.40]); nr = np.array([0.01, -0.02, 0.03])
    w = sig * 0.40 / vol / 3
    out["tsmom"] = {"weights": w.tolist(), "gross": float(np.abs(w).sum()), "net": float(w.sum()), "next_month": nr.tolist(),
                    "portfolio_return": float(w @ nr), "per_instrument_contribution": (w * nr).tolist()}
    # 8.4: split with dividend (Chapter 3 fixture): unadjusted price change vs total return
    pre, ratio, div, post = 100.0, 2.0, 1.0, 51.0
    out["split"] = {"unadjusted_price_return": post / pre - 1, "total_return": (ratio * post + ratio * div) / pre - 1}
    # 8.5: futures roll splice
    a_prices, b_prices = [100.0, 102.0], [106.0, 107.0]
    spliced = a_prices + b_prices
    out["roll"] = {"spliced_returns": [spliced[i + 1] / spliced[i] - 1 for i in range(3)],
                   "tradable_returns": [a_prices[1] / a_prices[0] - 1, b_prices[1] / b_prices[0] - 1],
                   "fake_return_at_roll": spliced[2] / spliced[1] - 1}
    # 8.6: overlapping vintages: one asset flips from long to short
    vintages = np.array([[0.5, -0.5], [0.5, -0.5], [-0.5, 0.5], [-0.5, 0.5], [-0.5, 0.5], [-0.5, 0.5]])
    k3 = np.array([vintages[i - 2:i + 1].mean(axis=0) for i in range(2, 6)])
    turn1 = np.abs(np.diff(vintages, axis=0)).sum(axis=1)
    turn3 = np.abs(np.diff(k3, axis=0)).sum(axis=1)
    out["overlap"] = {"k1_turnover": turn1.tolist(), "k3_weights": k3.tolist(), "k3_turnover": turn3.tolist()}
    return out


# ------------------------------------------------------------------- real study
def series_stats(x: pd.Series, *, nw_lags: int = 0) -> dict:
    s = x.dropna()
    t = len(s)
    mean = float(s.mean())
    se = float(np.sqrt(newey_west_variance_of_mean(s.to_numpy(), nw_lags)))
    return {"months": int(t), "mean_pct": 100 * mean, "t_nw": mean / se, "sd_pct": 100 * float(s.std(ddof=1)),
            "sharpe_annual": mean / float(s.std(ddof=1)) * np.sqrt(12), "nw_lags": nw_lags}


def industry_study() -> dict:
    returns, rf, prov = load_industries_and_rf()
    ff3 = json.loads(FF3_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff3"]
    table = pd.read_csv(ROOT / ff3["processed_path"], dtype={"month": str})
    table.index = pd.PeriodIndex(table.pop("month"), freq="M")
    market_total = table["Mkt-RF"] + table["RF"]
    excess = returns.sub(rf, axis=0)
    result: dict = {"provenance": {"french_hashes": prov["sha256"], "ff3_processed_sha256": ff3["processed_sha256"]}}
    # cross-sectional 12-1, K = 1, 3, 6 with costs
    cs = {}
    ls_series = {}
    for k in (1, 3, 6):
        w = cross_sectional_momentum_weights(returns, window=11, skip=1, n_buckets=5, hold_months=k)
        g = strategy_returns(w, returns)
        net = net_of_costs(g, w, cost_per_unit=COST_PER_UNIT)
        turn = w.diff().abs().sum(axis=1, min_count=1)
        cs[str(k)] = {"gross": series_stats(g, nw_lags=k - 1), "net": series_stats(net, nw_lags=k - 1), "mean_turnover": float(turn.mean())}
        ls_series[k] = g
    result["cs_12_1"] = cs
    # window definition comparison (K = 1)
    windows = {}
    for label, (window, skip) in {"12-1 (months s-11..s-1)": (11, 1), "12-0 (months s-11..s)": (12, 0), "1-0 (last month)": (1, 0),
                                  "1-1 (month s-1)": (1, 1), "6-1": (5, 1), "3-1": (2, 1)}.items():
        w = cross_sectional_momentum_weights(returns, window=window, skip=skip, n_buckets=5, hold_months=1)
        windows[label] = series_stats(strategy_returns(w, returns))
    result["cs_window_variants"] = windows
    # (J, K) grid
    grid = {}
    for J in (3, 6, 9, 12):
        for K in (1, 3, 6, 12):
            w = cross_sectional_momentum_weights(returns, window=J - 1, skip=1, n_buckets=5, hold_months=K)
            grid[f"J{J}_K{K}"] = series_stats(strategy_returns(w, returns), nw_lags=K - 1)
    result["grid_J_K"] = grid
    result["grid_bonferroni_hurdle_z_16"] = float(stats.norm.ppf(1 - 0.05 / 32))
    # time-series momentum on excess returns; volatility scaling known at the signal month
    vol = ex_ante_volatility(returns)
    ts = {}
    ts_series = {}
    for label, (window, skip) in {"TS 12-0": (12, 0), "TS 12-1": (11, 1)}.items():
        sig = time_series_sign(excess, window=window, skip=skip)
        w = tsmom_weights(sig, vol, target_vol=0.40)
        g = strategy_returns(w, excess)
        ts[label] = {**series_stats(g), "mean_gross_exposure": float(w.abs().sum(axis=1).mean()), "mean_net_exposure": float(w.sum(axis=1).mean()),
                     "mean_fraction_long": float(((sig > 0).sum(axis=1) / sig.notna().sum(axis=1).replace(0, np.nan)).mean())}
        ts_series[label] = g
    always = pd.DataFrame(1.0, index=returns.index, columns=returns.columns).where(vol.notna())
    wl = tsmom_weights(always, vol, target_vol=0.40)
    gl = strategy_returns(wl, excess)
    ts["always long (same scaling)"] = {**series_stats(gl), "mean_gross_exposure": float(wl.abs().sum(axis=1).mean())}
    result["ts_momentum"] = ts
    both = pd.DataFrame({"cs": ls_series[1], "ts": ts_series["TS 12-0"]}).dropna()
    result["corr_cs_ts"] = float(both.corr().iloc[0, 1])
    result["ts_minus_always_long"] = series_stats(ts_series["TS 12-0"] - gl)
    # crash state: market total return over the last 24 months
    state = trailing_bear_state(market_total, window=24)
    g1 = ls_series[1]
    d = pd.DataFrame({"ls": g1, "bear": state}).dropna()
    result["bear_state"] = {k: {"months": int(len(v)), "mean_pct": float(100 * v["ls"].mean()), "sd_pct": float(100 * v["ls"].std(ddof=1))}
                            for k, v in {"bear": d[d["bear"] == 1.0], "not_bear": d[d["bear"] == 0.0]}.items()}
    worst = g1.dropna().nsmallest(10)
    result["worst_10_months"] = [{"signal_month": str(p), "return_month": str(p + 1), "ls_pct": float(100 * v), "bear_at_signal": float(state.get(p, np.nan)),
                                  "market_return_in_return_month_pct": float(100 * market_total.get(p + 1, np.nan))} for p, v in worst.items()]
    result["worst_10_in_bear"] = int(sum(1 for p in worst.index if state.get(p) == 1.0))
    result["bear_months_share"] = float((d["bear"] == 1.0).mean())
    result["max_drawdown_cs_12_1_gross"] = float(((1 + g1.dropna()).cumprod() / (1 + g1.dropna()).cumprod().cummax() - 1).min())
    result["_series"] = {"cs1": ls_series[1], "cs3": ls_series[3], "ts": ts_series["TS 12-0"], "always": gl, "state": state, "market": market_total}
    return result


# ------------------------------------------------------------------------- figures
def _figures(real: dict, fig_dir: Path) -> None:
    # 1 timeline of windows
    fig, ax = plt.subplots(figsize=(12.5, 4.4))
    ax.set_xlim(0, 16.2); ax.set_ylim(-0.2, 4.0); ax.axis("off")

    def row(y, label, formation, skipped, hold, color):
        ax.text(0.5, y + 0.55, label, fontsize=9.5, va="center", ha="left")
        for m in range(1, 16):
            face, edge, hatch = "white", "0.7", None
            if m in formation:
                face, edge = color, "k"
            elif m in skipped:
                face, edge, hatch = "#DDDDDD", "k", "//"
            elif m in hold:
                face, edge = "#D05A36", "k"
            ax.add_patch(FancyBboxPatch((m - 0.45 + 0.5, y - 0.25), 0.9, 0.5, boxstyle="round,pad=0.02", fc=face, ec=edge, lw=0.8, hatch=hatch, alpha=0.9))
            ax.text(m + 0.05 + 0.5, y, str(m), ha="center", va="center", fontsize=8, color="w" if m in formation or m in hold else "k")
    row(3.0, "Cross-sectional 12-1, signal at the end of month 13: months 2-12 (11 months); month 13 skipped; held in month 14", range(2, 13), [13], [14], "#176B87")
    row(1.85, "Time-series 12-0 (Moskowitz-Ooi-Pedersen): months 2-13 (12 months, nothing skipped); held in month 14", range(2, 14), [], [14], "#654A8B")
    row(0.7, "Off by one month: months 1-11 (too early). Months 3-13 would include the skipped month", range(1, 12), [], [], "#7E8C95")
    ax.text(8.3, 3.85, "Blue/purple/grey = formation, hatched = skipped month, orange = holding month; boxes are calendar months", ha="center", fontsize=9)
    fig.savefig(fig_dir / FIGURES[0], dpi=150, bbox_inches="tight"); plt.close(fig)
    # 2 cumulative returns
    s = real["_series"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    for key, color, label in (("cs1", "#176B87", "CS 12-1, K=1 (gross, gross exposure 2)"), ("cs3", "#654A8B", "CS 12-1, K=3 (gross)"),
                              ("ts", "#D05A36", "TS 12-0, 40% vol scaling (excess returns)"), ("always", "0.5", "always long, same scaling")):
        x = s[key].dropna()
        ax.semilogy(x.index.to_timestamp(how="end"), (1 + x).cumprod().values, color=color, lw=1.2, label=label)
    ax.set_xlabel("Return month"); ax.set_ylabel("Compounded wealth, start = 1 (log scale)")
    ax.set_title("French 10 industries: compounded long-short and trend strategies"); ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    gs = s["cs1"].dropna()
    ax.plot(gs.index.to_timestamp(how="end"), 100 * gs.values, lw=0.6, color="#176B87")
    worst = real["worst_10_months"]
    for w in worst:
        p = pd.Period(w["return_month"], "M")
        ax.scatter([p.to_timestamp(how="end")], [w["ls_pct"]], color="#D05A36", s=22, zorder=3)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Return month"); ax.set_ylabel("CS 12-1 long-short return, month t+1 (% per month)")
    ax.set_title("Orange: ten worst months (7 of 10 after a 24-month market fall)")
    fig.savefig(fig_dir / FIGURES[1], dpi=150); plt.close(fig)
    # 3 grid heat map
    Js, Ks = (3, 6, 9, 12), (1, 3, 6, 12)
    mat = np.array([[real["grid_J_K"][f"J{J}_K{K}"]["t_nw"] for K in Ks] for J in Js])
    fig, ax = plt.subplots(figsize=(6.8, 4.6), constrained_layout=True)
    im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=max(5.0, mat.max()))
    for i, J in enumerate(Js):
        for j, K in enumerate(Ks):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", color="k" if mat[i, j] < 3.5 else "w", fontsize=10)
    ax.set_xticks(range(4)); ax.set_xticklabels(Ks); ax.set_yticks(range(4)); ax.set_yticklabels(Js)
    ax.set_xlabel("Holding period K (months; overlapping vintages)"); ax.set_ylabel("Formation span J (months)")
    ax.set_title(f"Newey-West t: quintile long-short\n16 strategies; Bonferroni z = {real['grid_bonferroni_hurdle_z_16']:.2f}")
    fig.colorbar(im, ax=ax, label="t (unitless)")
    fig.savefig(fig_dir / FIGURES[2], dpi=150); plt.close(fig)
    # 4 crash state
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    b = real["bear_state"]
    ax.bar([0, 1], [b["not_bear"]["mean_pct"], b["bear"]["mean_pct"]], yerr=[2 * b["not_bear"]["sd_pct"] / np.sqrt(b["not_bear"]["months"]), 2 * b["bear"]["sd_pct"] / np.sqrt(b["bear"]["months"])],
           color=["#176B87", "#D05A36"], capsize=4)
    ax.set_xticks([0, 1]); ax.set_xticklabels([f"not bear ({b['not_bear']['months']} months)", f"bear ({b['bear']['months']} months)"])
    ax.axhline(0, color="0.4", lw=0.8); ax.set_ylabel("Mean CS 12-1 long-short (% per month, ±2 se)")
    ax.set_title("State at signal time: market total return over the last 24 months < 0")
    ax = axes[1]
    d = pd.DataFrame({"ls": s["cs1"], "mkt": s["market"].shift(-1).reindex(s["cs1"].index), "bear": s["state"]}).dropna()
    for flag, color, name in ((0.0, "#176B87", "not bear"), (1.0, "#D05A36", "bear")):
        sub = d[d["bear"] == flag]
        ax.scatter(100 * sub["mkt"], 100 * sub["ls"], s=7, color=color, alpha=0.5, label=name)
    ax.axhline(0, color="0.4", lw=0.8); ax.axvline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Market total return in the return month (%)"); ax.set_ylabel("CS 12-1 long-short return (% per month)")
    ax.set_title("Largest losses coincide with large market rebounds"); ax.legend(frameon=False, fontsize=8.5)
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


def run(out_dir: Path, fig_dir: Path) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch25_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 25 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True); fig_dir.mkdir(parents=True, exist_ok=True)
    real = industry_study()
    _figures(real, fig_dir)
    result = {"hand_examples": hand_examples(), "french_industries": real, "cost_per_unit": COST_PER_UNIT}
    (out_dir / "ch25_results.json").write_text(json.dumps(_clean(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _clean(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "qa/a5/claude/results/ch25"))
    parser.add_argument("--figures", default=str(ROOT / "figures/a5"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))["french_industries"]
    c = r["cs_12_1"]["1"]
    print(f"CS 12-1 K=1 gross {c['gross']['mean_pct']:.3f}%/mo (t {c['gross']['t_nw']:.2f}), net {c['net']['mean_pct']:.3f}%; turnover {c['mean_turnover']:.3f}")
    print(f"TS 12-0 {r['ts_momentum']['TS 12-0']['mean_pct']:.3f}%/mo; bear-state CS mean {r['bear_state']['bear']['mean_pct']:.3f}% vs {r['bear_state']['not_bear']['mean_pct']:.3f}%")


if __name__ == "__main__":
    main()
