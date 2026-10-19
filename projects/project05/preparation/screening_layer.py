"""Project 5 preparation: training-window pair screening (no trading simulation).

What this file does: correlation and Engle-Granger cointegration screening of every unordered pair of series using only a fixed
training window, hedge ratios fitted on that window, a count of all tests with their critical values, and checks that show what
screening can and cannot say. What it does not do: entry/exit rules, two-leg costs, borrow or financing, a backtest.

Real series: total-return index proxies compounded from the frozen French 10 value-weight industry portfolios (published, revised,
monthly, NOT tradable instruments, NOT point-in-time). Constructed series: the Chapter 17 simulators and the null simulation below.
Run from the course root: ``.venv/bin/python projects/project05/preparation/screening_layer.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.cointegration import (  # noqa: E402
    engle_granger_test, screen_cointegration_pairs, simulate_cointegrated_pair, simulate_noncointegrated_common_trend,
    total_return_index_proxy, validate_monthly_frame,
)
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402

CONFIG_PATH = Path(__file__).resolve().parent / "configs/screening_rules.json"
RESULT_NAME = "p05_screening_results.json"


def load_rules() -> dict:
    """The frozen screening rules and their SHA-256 (a local file hash is not a pre-registration)."""
    raw = CONFIG_PATH.read_bytes()
    rules = json.loads(raw)
    rules["_sha256"] = hashlib.sha256(raw).hexdigest()
    return rules


def real_levels() -> tuple[pd.DataFrame, dict]:
    """log of the total-return index proxies of the ten industries (levels, so that cointegration is a statement about levels)."""
    returns, _, prov = load_industries_and_rf()
    index = total_return_index_proxy(returns)
    levels = np.log(index)
    levels.columns = [c.replace("_TR_proxy", "") for c in levels.columns]
    return levels, prov


def hedge_ratio(y: pd.Series, x: pd.Series) -> dict:
    """OLS of y on [1, x] over the given (training) window: y = alpha + beta x + e. beta is a ratio of *log-index units*, not a capital weight."""
    X = np.column_stack([np.ones(len(x)), x.to_numpy()])
    coef, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
    resid = y.to_numpy() - X @ coef
    return {"alpha": float(coef[0]), "beta": float(coef[1]), "resid_sd": float(resid.std(ddof=2))}


def half_life(spread: np.ndarray) -> float:
    """-ln 2 / ln(phi) from the AR(1) slope of the demeaned spread; inf if phi >= 1 or <= 0 (no mean reversion to measure)."""
    s = spread - spread.mean()
    phi = float(np.dot(s[1:], s[:-1]) / np.dot(s[:-1], s[:-1]))
    return float(-np.log(2) / np.log(phi)) if 0 < phi < 1 else float("inf")


def screen_window(levels: pd.DataFrame, train_end: str, test_end: str, rules: dict) -> dict:
    """Screen on [start, train_end] only; then look at the *later* window [train_end+1, test_end] with the frozen hedge ratios."""
    end = pd.Period(train_end, "M")
    train = levels.loc[:end]
    # slice before screening: the shared helper validates every row it is given, so a missing *later* value must not stop a training-only screen
    table = screen_cointegration_pairs(train, training_end=end, trend=rules["engle_granger"]["trend"])
    stop = pd.Period(test_end, "M")
    if stop <= end:
        raise ValueError("test_end must be after train_end")
    test = levels.loc[end + 1:stop]
    expected_months = pd.period_range(end + 1, stop, freq="M")
    if not test.index.equals(expected_months):
        raise ValueError("later diagnostic window must contain every month from train_end + 1 through test_end exactly once")
    try:
        test = validate_monthly_frame(test)
    except ValueError as exc:
        raise ValueError(f"later diagnostic window is invalid: {exc}") from exc
    n_pairs = len(table)
    returns = levels.diff()
    rows = []
    for rec in table.itertuples():
        a, b = rec.series_1, rec.series_2
        h = hedge_ratio(train[a], train[b])
        spread_train = train[a] - h["alpha"] - h["beta"] * train[b]
        spread_test = test[a] - h["alpha"] - h["beta"] * test[b]
        corr_ret = float(returns.loc[:end, [a, b]].dropna().corr().iloc[0, 1])
        corr_lvl = float(train[[a, b]].corr().iloc[0, 1])
        adf_test = adfuller(spread_test.to_numpy(), regression="c", autolag="AIC", result_object=True)
        rows.append({"series_1": a, "series_2": b, "statistic": rec.statistic, "pvalue": rec.pvalue, "qvalue_bh": rec.qvalue_bh, "alpha": h["alpha"], "beta": h["beta"],
                     "corr_log_levels_train": corr_lvl, "corr_monthly_log_returns_train": corr_ret,
                     "half_life_train_months": half_life(spread_train.to_numpy()), "half_life_test_months": half_life(spread_test.to_numpy()),
                     "spread_sd_train": float(spread_train.std(ddof=1)), "spread_sd_test": float(spread_test.std(ddof=1)),
                     "test_mean_spread_in_train_sd": float((spread_test.mean() - spread_train.mean()) / spread_train.std(ddof=1)),
                     "adf_pvalue_test_frozen_spread": float(adf_test.pvalue)})
    out = pd.DataFrame(rows)
    crit = engle_granger_test(train[table.iloc[0].series_1], train[table.iloc[0].series_2], trend=rules["engle_granger"]["trend"]).critical_values
    alpha = rules["alpha"]
    return {"train_end": train_end, "test_end": test_end, "n_train_months": int(len(train)), "n_test_months": int(len(test)), "n_pairs_tested": int(n_pairs),
            "engle_granger_critical_values_for_first_pair_5pct": crit["5%"], "critical_values_first_pair": crit,
            "n_pvalue_below_alpha": int((out["pvalue"] < alpha).sum()), "expected_false_positives_if_all_null": float(n_pairs * alpha),
            "n_qvalue_below_q": int((out["qvalue_bh"] < rules["bh_q"]).sum()), "bonferroni_pvalue_threshold": float(alpha / n_pairs),
            "n_pvalue_below_bonferroni": int((out["pvalue"] < alpha / n_pairs).sum()),
            "n_selected_for_followup": int(((out["qvalue_bh"] < rules["bh_q"])).sum()),
            "pairs": out.to_dict(orient="records"), "_frame": out}


def null_calibration(rules: dict) -> dict:
    """Independent random walks: how many of the 45 pair tests reject at alpha by chance, and what Benjamini-Hochberg does."""
    cal = rules["null_calibration"]
    rng = np.random.default_rng(cal["seed"])
    idx = pd.period_range("1960-01", periods=cal["months"], freq="M")
    rejected, bh_rejected, min_p = [], [], []
    for _ in range(cal["reps"]):
        levels = pd.DataFrame(np.cumsum(rng.normal(size=(cal["months"], cal["n_series"])), axis=0), index=idx, columns=[f"s{i}" for i in range(cal["n_series"])])
        table = screen_cointegration_pairs(levels, training_end=idx[-1], trend=rules["engle_granger"]["trend"])
        rejected.append(int((table["pvalue"] < rules["alpha"]).sum()))
        bh_rejected.append(int((table["qvalue_bh"] < rules["bh_q"]).sum()))
        min_p.append(float(table["pvalue"].min()))
    n_pairs = cal["n_series"] * (cal["n_series"] - 1) // 2
    return {"reps": cal["reps"], "n_pairs": n_pairs, "months": cal["months"], "mean_rejections_at_alpha": float(np.mean(rejected)),
            "share_replications_with_at_least_one_rejection": float(np.mean(np.array(rejected) > 0)),
            "mean_bh_rejections": float(np.mean(bh_rejected)), "share_replications_with_a_bh_rejection": float(np.mean(np.array(bh_rejected) > 0)),
            "mean_min_pvalue": float(np.mean(min_p)), "expected_rejections_if_independent_tests": float(n_pairs * rules["alpha"])}


def selection_effect(rules: dict) -> dict:
    """Pick the pair with the smallest training p-value among all pairs of independent random walks; then test its frozen spread on the next window."""
    cal = rules["selection_effect"]
    rng = np.random.default_rng(cal["seed"])
    total = cal["train_months"] + cal["test_months"]
    idx = pd.period_range("1960-01", periods=total, freq="M")
    in_sample, out_sample = [], []
    for _ in range(cal["reps"]):
        levels = pd.DataFrame(np.cumsum(rng.normal(size=(total, cal["n_series"])), axis=0), index=idx, columns=[f"s{i}" for i in range(cal["n_series"])])
        train_end = idx[cal["train_months"] - 1]
        table = screen_cointegration_pairs(levels, training_end=train_end, trend=rules["engle_granger"]["trend"])
        best = table.iloc[0]
        a, b = best.series_1, best.series_2
        h = hedge_ratio(levels.loc[:train_end, a], levels.loc[:train_end, b])
        test = levels.loc[train_end + 1:]
        spread = test[a] - h["alpha"] - h["beta"] * test[b]
        in_sample.append(float(best.pvalue))
        out_sample.append(float(adfuller(spread.to_numpy(), regression="c", autolag="AIC", result_object=True).pvalue))
    return {"reps": cal["reps"], "mean_smallest_training_pvalue": float(np.mean(in_sample)), "share_training_best_below_alpha": float(np.mean(np.array(in_sample) < rules["alpha"])),
            "mean_test_pvalue_of_selected_pair": float(np.mean(out_sample)), "share_selected_pairs_with_test_pvalue_below_alpha": float(np.mean(np.array(out_sample) < rules["alpha"])),
            "note": "all series are independent random walks, so every selected pair is a false discovery"}


def correlation_is_not_cointegration() -> dict:
    """Chapter 17 simulators: highly correlated non-cointegrated levels versus a cointegrated pair with a smaller level correlation."""
    non = simulate_noncointegrated_common_trend(n=360, seed=20261017)
    coi = simulate_cointegrated_pair(n=360, seed=20261018)
    res = {}
    for name, frame, pair in (("common_trend_not_cointegrated", non, ("y", "x")), ("cointegrated", coi, ("y", "x"))):
        eg = engle_granger_test(frame[pair[0]], frame[pair[1]])
        res[name] = {"correlation_of_levels": float(frame[list(pair)].corr().iloc[0, 1]), "correlation_of_changes": float(frame[list(pair)].diff().dropna().corr().iloc[0, 1]),
                     "engle_granger_statistic": eg.statistic, "engle_granger_pvalue": eg.pvalue, "critical_value_5pct": eg.critical_values["5%"]}
    return res


def hedge_ratio_is_not_a_capital_weight(beta: float = 1.5, price_y: float = 120.0, price_x: float = 40.0) -> dict:
    """y = alpha + beta x in price (level) units: long 1 unit of y against beta units of x. Capital weights follow from prices."""
    value_y, value_x = price_y, beta * price_x
    return {"beta": beta, "price_y": price_y, "price_x": price_x, "value_long_y": value_y, "value_short_x": value_x, "gross": value_y + value_x,
            "capital_weight_y": value_y / (value_y + value_x), "capital_weight_x": value_x / (value_y + value_x), "net_dollar_exposure": value_y - value_x}


def make_figure(windows: dict, selection: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    colors = ("#176B87", "#D05A36")
    for (name, w), color in zip(windows.items(), colors):
        p = np.sort([q["pvalue"] for q in w["pairs"]])
        ax.plot(np.arange(1, len(p) + 1), p, marker="o", ms=3.5, lw=1.0, color=color, label=f"train end {w['train_end']} ({w['n_train_months']} months)")
    n = len(next(iter(windows.values()))["pairs"])
    ax.axhline(0.05, color="0.5", ls=":", lw=1.0, label="0.05 (unadjusted)")
    ax.plot(np.arange(1, n + 1), 0.10 * np.arange(1, n + 1) / n, color="0.2", ls="--", lw=1.0, label="Benjamini-Hochberg line, q = 0.10")
    ax.set_yscale("log"); ax.set_xlabel("Rank of the pair by Engle-Granger p-value (45 pairs of the ten industries)"); ax.set_ylabel("Engle-Granger p-value (log scale)")
    ax.set_title("Training-window screening: few p-values sit below the BH line"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    ax.bar(["training p-value\nof the best pair", "later-window ADF p-value\nof its frozen spread"], [selection["mean_smallest_training_pvalue"], selection["mean_test_pvalue_of_selected_pair"]], color=colors)
    ax.axhline(0.05, color="0.5", ls=":", lw=1.0)
    ax.set_ylabel("Mean p-value, 200 replications")
    ax.set_title("Ten independent random walks: the best of 45 pairs")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run(out_dir: Path, fig_dir: Path | None = None) -> dict:
    out_dir = Path(out_dir)
    target = out_dir / RESULT_NAME
    if target.exists():
        raise FileExistsError("Project 5 preparation results already exist; remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = load_rules()
    levels, prov = real_levels()
    windows = {}
    for w in rules["windows"]:
        res = screen_window(levels, w["train_end"], w["test_end"], rules)
        res.pop("_frame")
        windows[w["name"]] = res
    result = {"rules_sha256": rules["_sha256"], "data": {"source": prov["source"], "first_month": prov["first_month"], "last_month": prov["last_month"], "sha256": prov["sha256"],
                                                          "is_point_in_time": False, "tradable": False, "note": "ten value-weight industry portfolios; not individual securities, not tradable pairs"},
              "total_pair_tests": int(sum(w["n_pairs_tested"] for w in windows.values())),
              "windows": windows, "null_calibration": null_calibration(rules), "selection_effect": selection_effect(rules),
              "correlation_is_not_cointegration": correlation_is_not_cointegration(), "hedge_ratio_is_not_a_capital_weight": hedge_ratio_is_not_a_capital_weight()}
    fig_dir = Path(fig_dir) if fig_dir else ROOT / "figures/a5"
    fig_path = fig_dir / "p05_screening.png"
    if fig_path.exists():
        raise FileExistsError("Project 5 preparation figure already exists; remove it deliberately")
    fig_dir.mkdir(parents=True, exist_ok=True)
    make_figure(windows, result["selection_effect"], fig_path)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=float) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "qa/a5/claude/results/p05"))
    parser.add_argument("--figures", default=str(ROOT / "figures/a5"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    for name, w in r["windows"].items():
        print(f"{name}: {w['n_pairs_tested']} pairs, p<alpha {w['n_pvalue_below_alpha']} (expected by chance {w['expected_false_positives_if_all_null']:.2f}), BH q<{0.10}: {w['n_qvalue_below_q']}")
    nc = r["null_calibration"]
    print(f"null: mean rejections {nc['mean_rejections_at_alpha']:.2f} of {nc['n_pairs']} pairs; at least one in {100 * nc['share_replications_with_at_least_one_rejection']:.0f}% of replications")


if __name__ == "__main__":
    main()
