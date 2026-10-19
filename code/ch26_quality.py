"""Chapter 26 CLI: quality measures from one filing version, leverage vs operations (DuPont), near-zero equity, composite,
and the published RMW profitability factor.

Run from the course root::

    .venv/bin/python code/ch26_quality.py

Outputs ``qa/a5/claude/results/ch26/ch26_results.json`` and ``figures/a5/ch26_*.png`` (refuses to overwrite).
The firm-level fundamentals panel is a **teaching construction** with a known data-generating process (not market data).
The only real data are the published monthly RMW and related factor returns from the frozen 2026-10-05 FF5 snapshot:
aggregate factor returns, revised history, not stock-level, not point-in-time, not tradable fills.

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

from quant_course.factor_research import (  # noqa: E402
    factor_rank, group_percentile, ic_series, ic_summary, lead_return, quantile_bucket,
)
from quant_course.factor_signals import latest_available_values  # noqa: E402
from quant_course.quality import (  # noqa: E402
    accrual_ratio, average_balance, dupont, gross_profit_to_assets, guarded_ratio, leverage_ratio, operating_profitability,
    roe_from_leverage,
)

SEED = 20261107
N_IND, N_BANK = 300, 100
START = pd.Period("2012-01", "M")
MONTHS = 132
BETA_Q, BETA_ACCRUAL = 0.003, 0.003      # monthly return per standard deviation of latent quality / accrual propensity
FIGURES = ("ch26_dupont_and_outliers.png", "ch26_ic_measures.png", "ch26_rmw.png")
FF5_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"


# ------------------------------------------------------------------ hand examples
def hand_examples() -> dict:
    out: dict = {}
    # 8.1 same ROE, different engines: firm X improves operations, firm Y adds debt
    yearly = {"X_before": (60.0, 1000.0, 600.0, 400.0), "X_after": (90.0, 1000.0, 600.0, 400.0),
              "Y_before": (60.0, 1000.0, 600.0, 400.0), "Y_after": (56.25, 1000.0, 600.0, 300.0)}
    idx = pd.period_range("2026-06", periods=1, freq="M")
    out["dupont"] = {}
    for k, (ni, sales, assets, equity) in yearly.items():
        d = dupont(*[pd.DataFrame([[v]], index=idx, columns=["f"]) for v in (ni, sales, assets, equity)])
        out["dupont"][k] = {name: float(frame.iloc[0, 0]) for name, frame in d.items()}
    # 8.2 leverage effect on ROE: rho + (rho - i) D/E
    out["leverage_roe"] = {de: roe_from_leverage(0.08, 0.03, de) for de in (0.0, 0.5, 1.0, 2.0)}
    # 8.3 average vs ending denominators and the near-zero guard
    ni = pd.DataFrame([[40.0, 40.0, 40.0, 40.0]], index=idx, columns=["steady", "shrinking_equity", "tiny_equity", "negative_equity"])
    eq_end = pd.DataFrame([[400.0, 100.0, 2.0, -30.0]], index=idx, columns=ni.columns)
    eq_prev = pd.DataFrame([[400.0, 500.0, 300.0, 100.0]], index=idx, columns=ni.columns)
    assets = pd.DataFrame([[1000.0, 1000.0, 1000.0, 1000.0]], index=idx, columns=ni.columns)
    avg_unguarded = average_balance(eq_end, eq_prev)
    avg = average_balance(eq_end, eq_prev, floor=0.0)
    out["roe_denominators"] = {"columns": list(ni.columns), "roe_ending": guarded_ratio(ni, eq_end).iloc[0].tolist(),
                               "roe_average_unguarded": guarded_ratio(ni, avg_unguarded).iloc[0].tolist(),
                               "roe_average_both_balances_positive": guarded_ratio(ni, avg).iloc[0].tolist(),
                               "roe_ending_with_floor_2pct_assets": guarded_ratio(ni, eq_end, floor=0.02 * assets).iloc[0].tolist()}
    # 8.4 gross profitability, operating profitability, accruals
    rev, cogs, sga, interest = 1000.0, 600.0, 200.0, 20.0
    a_, e_ = 800.0, 400.0
    out["profitability"] = {"gp_over_assets": (rev - cogs) / a_, "op_over_equity": (rev - cogs - sga - interest) / e_,
                            "accrual_ratio_low_quality": (50.0 - 20.0) / 500.0, "accrual_ratio_high_quality": (50.0 - 80.0) / 500.0}
    # 8.5 vintage mismatch: restated net income over the original equity
    out["vintage_mismatch"] = {"original_roe": 40.0 / 400.0, "restated_ni_over_original_equity": 28.0 / 400.0, "restated_roe_same_version": 28.0 / 350.0}
    return out


# ----------------------------------------------------------------- constructed world
def _tail(rng: np.random.Generator, df: int, size) -> np.ndarray:
    return rng.standard_t(df, size) / np.sqrt(df / (df - 2))


def quality_world(seed: int = SEED, *, n_ind: int = N_IND, n_bank: int = N_BANK, months: int = MONTHS) -> dict:
    """Annual fundamentals with filing delays, monthly returns driven by latent quality and accrual propensity.

    Non-financial firms: gross margin rises with latent quality q; asset turnover and leverage are independent of q;
    interest = 5% of debt; reported net income includes an accrual component that later cash does not back. Banks have
    no cost of goods sold (gross profitability undefined) and ~9% equity/assets. 3% of firm-years suffer an equity shock
    that leaves equity near zero or negative.
    """
    rng = np.random.default_rng(seed)
    n = n_ind + n_bank
    names = [f"Q{i:03d}" for i in range(n)]
    industry = np.array(["Ind"] * n_ind + ["Bank"] * n_bank)
    bank = industry == "Bank"
    q = rng.standard_normal(n)
    acc_prop = rng.standard_normal(n)
    idx = pd.period_range(START, periods=months, freq="M")
    years = list(range(START.year - 3, idx[-1].year + 1))                    # FY2009.. so that FY2010 has a previous balance sheet
    ny = len(years)
    assets = np.empty((ny, n)); assets[0] = np.exp(5.0 + 0.7 * rng.standard_normal(n))
    for k in range(1, ny):
        assets[k] = assets[k - 1] * np.exp(0.05 + 0.08 * rng.standard_normal(n))
    debt_ratio = np.where(bank, 0.91, rng.uniform(0.05, 0.60, n))[None, :] + 0.02 * rng.standard_normal((ny, n))
    debt_ratio = np.clip(debt_ratio, 0.0, 0.97)
    shock = rng.random((ny, n)) < 0.03
    equity_ratio = 1 - debt_ratio
    equity_ratio = np.where(shock, rng.choice([-0.05, 0.003, 0.008], size=(ny, n)), equity_ratio)
    equity = equity_ratio * assets
    debt = np.maximum(assets - equity, 0.0)
    turnover = np.where(bank, 0.06, np.exp(0.0 + 0.25 * rng.standard_normal(n)))[None, :] * np.ones((ny, 1))
    sales = turnover * assets
    gross_margin = np.where(bank, 0.5, 0.25 + 0.06 * q[None, :] + 0.03 * rng.standard_normal((ny, n)))
    cogs = np.where(bank[None, :], np.nan, (1 - gross_margin) * sales)
    sga = np.where(bank[None, :], 0.30 * sales, 0.12 * sales * (1 + 0.1 * rng.standard_normal((ny, n))))
    interest = np.where(bank[None, :], 0.025 * debt, 0.05 * debt)
    operating_income = np.where(bank[None, :], 0.55 * sales * 0.0 + 0.012 * assets + 0.004 * q[None, :] * assets, gross_margin * sales - sga)
    true_ni = (operating_income - np.where(bank[None, :], 0.0, interest)) * 0.75
    accrual = (0.02 * acc_prop[None, :] + 0.01 * rng.standard_normal((ny, n))) * assets
    net_income = true_ni + accrual
    cfo = true_ni + 0.04 * assets + 0.005 * rng.standard_normal((ny, n)) * assets      # cash flow does not contain the accrual
    delay = rng.integers(60, 111, size=(ny, n))
    rows = []
    for k in range(1, ny):
        for j in range(n):
            av = pd.Timestamp(f"{years[k]}-12-31 16:05", tz="UTC") + pd.Timedelta(days=int(delay[k, j]))
            rows.append((names[j], pd.Timestamp(f"{years[k]}-12-31"), av, av + pd.Timedelta(days=1), sales[k, j], cogs[k, j], sga[k, j], interest[k, j],
                         net_income[k, j], cfo[k, j], assets[k, j], assets[k - 1, j], equity[k, j], equity[k - 1, j], debt[k, j]))
    cols = ["security_id", "period_end", "available_at", "ingested_at", "revenue", "cogs", "sga", "interest", "net_income", "cfo",
            "assets", "assets_prev", "equity", "equity_prev", "debt"]
    versions = pd.DataFrame(rows, columns=cols)
    values = ["revenue", "cogs", "sga", "interest", "net_income", "cfo", "assets", "assets_prev", "equity", "equity_prev", "debt"]
    pit = latest_available_values(versions, idx, values)
    market = 0.008 + 0.045 * (lambda d: (d - d.mean()) / d.std())(rng.standard_normal(months))
    premium = BETA_Q * q - BETA_ACCRUAL * acc_prop
    returns = market[:, None] + premium[None, :] + 0.07 * _tail(rng, 5, (months, n))
    return {"index": idx, "names": names, "industry": pd.Series(industry, index=names), "q": q, "acc_prop": acc_prop, "pit": pit,
            "returns": pd.DataFrame(returns, index=idx, columns=names), "versions": versions}


def measures(world: dict) -> dict[str, pd.DataFrame]:
    p = world["pit"]
    assets_avg = average_balance(p["assets"], p["assets_prev"])
    equity_avg = average_balance(p["equity"], p["equity_prev"], floor=0.0)
    return {
        "ROE (ending equity)": guarded_ratio(p["net_income"], p["equity"]),
        "ROE (average equity)": guarded_ratio(p["net_income"], equity_avg),
        "ROE (average equity, floor 5% of assets)": guarded_ratio(p["net_income"], equity_avg, floor=0.05 * assets_avg),
        "ROA (average assets)": guarded_ratio(p["net_income"], assets_avg),
        "GP/A (average assets)": gross_profit_to_assets(p["revenue"], p["cogs"], assets_avg),
        "OP (ending equity)": operating_profitability(p["revenue"], p["cogs"], p["sga"], p["interest"], p["equity"]),
        "accrual ratio": accrual_ratio(p["net_income"], p["cfo"], assets_avg),
        "leverage D/A": leverage_ratio(p["debt"], p["assets"]),
    }


def quality_study(world: dict) -> dict:
    ret, industry = world["returns"], world["industry"]
    label = lead_return(ret, 1)
    m = measures(world)
    nonbank = (industry == "Ind").to_numpy()
    cols_ind = [c for c, flag in zip(world["names"], nonbank) if flag]

    def ic_for(frame: pd.DataFrame, sign: float = 1.0, columns=None, method="spearman") -> dict:
        f = frame if columns is None else frame[columns]
        lab = label if columns is None else label[columns]
        s = ic_summary(ic_series(sign * f, lab, method=method)["ic"], nw_lags=0)
        return {"mean": s.mean, "t": s.t_naive, "n_dates": s.n_dates, "hit_rate": s.hit_rate}

    table = {
        "ROE (ending equity)": ic_for(m["ROE (ending equity)"], columns=cols_ind), "ROE (average equity)": ic_for(m["ROE (average equity)"], columns=cols_ind),
        "ROE (average equity, floor 5% of assets)": ic_for(m["ROE (average equity, floor 5% of assets)"], columns=cols_ind),
        "ROA (average assets)": ic_for(m["ROA (average assets)"], columns=cols_ind), "GP/A (average assets)": ic_for(m["GP/A (average assets)"], columns=cols_ind),
        "OP (ending equity)": ic_for(m["OP (ending equity)"], columns=cols_ind), "minus accrual ratio": ic_for(m["accrual ratio"], sign=-1.0, columns=cols_ind),
        "minus leverage D/A": ic_for(m["leverage D/A"], sign=-1.0, columns=cols_ind),
    }
    # Pearson IC of raw ROE vs rank IC: outliers from near-zero equity
    pearson_roe = ic_for(m["ROE (ending equity)"], columns=cols_ind, method="pearson")
    pearson_guard = ic_for(m["ROE (average equity, floor 5% of assets)"], columns=cols_ind, method="pearson")
    # composite: equal-weight average of same-date percentile ranks of GP/A and minus accrual ratio (weights fixed ex ante)
    gpa_rank = factor_rank(m["GP/A (average assets)"][cols_ind])
    acc_rank = factor_rank(-m["accrual ratio"][cols_ind])
    composite = (gpa_rank + acc_rank) / 2.0
    comp = ic_summary(ic_series(composite, label[cols_ind], method="spearman")["ic"], nw_lags=0)
    # how often equity is unusable
    eq = world["pit"]["equity"][cols_ind]; assets_ = world["pit"]["assets"][cols_ind]
    share_nonpos = float((eq <= 0).sum().sum() / eq.notna().sum().sum())
    share_tiny = float(((eq > 0) & (eq < 0.05 * assets_)).sum().sum() / eq.notna().sum().sum())
    # ROE dispersion: how much of the ROE variance is leverage (log multiplier) vs ROA
    p = world["pit"]
    roa = m["ROA (average assets)"][cols_ind]; mult = (average_balance(p["assets"], p["assets_prev"]) / average_balance(p["equity"], p["equity_prev"], floor=0.0))[cols_ind]
    ok = (mult > 0) & roa.notna()
    roe_ok = (roa * mult).where(ok)
    cs_var_roe = float(roe_ok.stack().var()); cs_var_roa = float(roa.where(ok).stack().var())
    # by-industry level of equity multiplier (banks vs non-banks)
    mult_all = average_balance(p["assets"], p["assets_prev"]) / average_balance(p["equity"], p["equity_prev"], floor=0.0)
    mult_by = {name: float(np.nanmedian(mult_all[industry.index[industry == name]].where(lambda x: x > 0).to_numpy())) for name in ("Ind", "Bank")}
    # leverage confounding: mean D/A of the top and bottom quintile by each measure
    lev = m["leverage D/A"][cols_ind]
    def bucket_leverage(measure: pd.DataFrame) -> dict:
        top, bot = [], []
        for date in measure.index:
            b = quantile_bucket(measure.loc[date, cols_ind].to_numpy(), 5)
            if np.isnan(b).all():
                continue
            top.append(np.nanmean(lev.loc[date].to_numpy()[b == 5])); bot.append(np.nanmean(lev.loc[date].to_numpy()[b == 1]))
        return {"top_quintile_mean_leverage": float(np.mean(top)), "bottom_quintile_mean_leverage": float(np.mean(bot))}
    leverage_by_measure = {k: bucket_leverage(m[k]) for k in ("ROE (average equity)", "ROA (average assets)", "GP/A (average assets)")}
    leverage_all = float(np.nanmean(lev.to_numpy()))
    # quintile spread of GP/A (non-banks), equal weight
    from quant_course.factor_research import bucket_returns
    bk = bucket_returns(m["GP/A (average assets)"][cols_ind], label[cols_ind], 5).dropna()
    return {
        "n_nonfinancial": len(cols_ind), "months": len(world["index"]), "ic_spearman": table,
        "ic_pearson_roe_ending": pearson_roe, "ic_pearson_roe_guarded": pearson_guard,
        "ic_composite_gpa_and_minus_accrual": {"mean": comp.mean, "t": comp.t_naive, "hit_rate": comp.hit_rate},
        "share_nonpositive_equity_firm_months": share_nonpos, "share_equity_below_5pct_of_assets_firm_months": share_tiny,
        "cross_sectional_variance_roa": cs_var_roa, "cross_sectional_variance_roe": cs_var_roe,
        "median_equity_multiplier_by_industry": mult_by, "leverage_of_top_and_bottom_quintiles": leverage_by_measure, "mean_leverage_all": leverage_all,
        "gpa_quintile_mean_return_pct": {int(c): float(100 * bk[c].mean()) for c in bk.columns if c != "LS"},
        "gpa_quintile_ls_pct": {"mean": float(100 * bk["LS"].mean()), "t": float(bk["LS"].mean() / (bk["LS"].std(ddof=1) / np.sqrt(len(bk))))},
        "banks_gpa_all_nan": bool(m["GP/A (average assets)"][[c for c in world["names"] if c not in cols_ind]].isna().all().all()),
        "_measures": m, "_world": world,
    }


# --------------------------------------------------------------------- real RMW
def rmw_study() -> dict:
    ff5 = json.loads(FF5_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff5"]
    path = ROOT / ff5["processed_path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != ff5["processed_sha256"]:
        raise RuntimeError("FF5 processed file differs from its manifest")
    table = pd.read_csv(path, dtype={"month": str})
    table.index = pd.PeriodIndex(table.pop("month"), freq="M")
    rmw = table["RMW"]

    def stats(x: pd.Series) -> dict:
        return {"months": int(len(x)), "mean_pct": float(100 * x.mean()), "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))), "sd_pct": float(100 * x.std(ddof=1))}
    wealth = (1 + rmw).cumprod(); dd = wealth / wealth.cummax() - 1
    periods = {"1963-07..1999-12": ("1963-07", "1999-12"), "2000-01..2026-08": ("2000-01", "2026-08"), "2007-01..2020-12": ("2007-01", "2020-12"), "all": ("1963-07", "2026-08")}
    corr = table[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]].corr()
    return {"processed_sha256": digest, "first_month": str(rmw.index[0]), "last_month": str(rmw.index[-1]),
            "by_period": {k: stats(rmw[a:b]) for k, (a, b) in periods.items()},
            "max_drawdown": float(dd.min()), "max_drawdown_month": str(dd.idxmin()),
            "correlation": {c: float(corr.loc["RMW", c]) for c in corr.columns if c != "RMW"}, "_rmw": rmw, "_wealth": wealth}


# ------------------------------------------------------------------------- figures
def _figures(study: dict, rmw: dict, fig_dir: Path) -> None:
    world, m = study["_world"], study["_measures"]
    industry = world["industry"]
    # 1: DuPont/leverage and ROE outliers
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    de = np.linspace(0, 3, 61)
    for rho, color in ((0.04, "#9AA7B0"), (0.08, "#176B87"), (0.12, "#654A8B")):
        ax.plot(de, [roe_from_leverage(rho, 0.03, d) * 100 for d in de], color=color, lw=1.8, label=f"operating return on assets {rho:.0%}")
    ax.axhline(3, color="k", ls=":", lw=1)
    ax.set_xlabel("Debt-to-equity D/E (ratio)"); ax.set_ylabel("ROE (%)")
    ax.set_title("ROE = rho + (rho - i) D/E, after-tax cost of debt i = 3% (dotted)"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    ind = [c for c in world["names"] if industry[c] == "Ind"]
    date = world["index"][60]
    raw = m["ROE (ending equity)"].loc[date, ind].dropna(); guarded = m["ROE (average equity, floor 5% of assets)"].loc[date, ind].dropna()
    ax.scatter(np.full(len(raw), 0) + 0.12 * np.random.default_rng(1).standard_normal(len(raw)), 100 * raw, s=9, color="#D05A36", alpha=0.6)
    ax.scatter(np.full(len(guarded), 1) + 0.12 * np.random.default_rng(2).standard_normal(len(guarded)), 100 * guarded, s=9, color="#176B87", alpha=0.6)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["ROE, ending equity,\nno guard", "ROE, average equity,\nfloor 5% of assets"])
    ax.set_ylabel(f"ROE at {date} (%)"); ax.set_title("Constructed: near-zero equity creates extreme ROE values")
    fig.savefig(fig_dir / FIGURES[0], dpi=150); plt.close(fig)
    # 2: IC by measure
    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    keys = list(study["ic_spearman"])
    means = [study["ic_spearman"][k]["mean"] for k in keys]
    se = [2 * 0.058 / np.sqrt(study["ic_spearman"][k]["n_dates"]) for k in keys]
    short = ["ROE\nending equity", "ROE\naverage equity", "ROE avg,\nfloor 5%", "ROA", "GP/A", "OP", "minus\naccruals", "minus\nleverage", "composite\nGP/A, -accr."]
    keys2 = keys + ["composite"]
    means.append(study["ic_composite_gpa_and_minus_accrual"]["mean"]); se.append(2 * 0.058 / np.sqrt(study["months"] - 1))
    colors = ["#D05A36", "#D05A36", "#176B87", "#176B87", "#176B87", "#176B87", "#654A8B", "#9AA7B0", "#2E8B57"]
    ax.bar(range(len(keys2)), means, color=colors[: len(keys2)])
    ax.errorbar(range(len(keys2)), means, yerr=se, fmt="none", ecolor="k", capsize=3)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xticks(range(len(keys2))); ax.set_xticklabels(short, fontsize=8.5, rotation=0)
    ax.set_ylabel("Mean Spearman IC (unitless; bar ±2 se)")
    ax.set_title(f"Constructed: {study['n_nonfinancial']} non-financial firms, {study['months']} months; leverage and accruals are separate dimensions")
    fig.savefig(fig_dir / FIGURES[1], dpi=150); plt.close(fig)
    # 3: RMW
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    w = rmw["_wealth"]
    axes[0].semilogy(w.index.to_timestamp(how="end"), w.values, color="#176B87")
    axes[0].set_xlabel("Month"); axes[0].set_ylabel("Compounded RMW spread, start = 1 (log scale)"); axes[0].set_title("Published Fama-French RMW, 1963-07 to 2026-08 (revised history)")
    roll = rmw["_rmw"].rolling(120).mean() * 100
    axes[1].plot(roll.index.to_timestamp(how="end"), roll.values, color="#654A8B"); axes[1].axhline(0, color="0.4", lw=0.8)
    axes[1].set_xlabel("Month (end of the 120-month window)"); axes[1].set_ylabel("Rolling 120-month mean of RMW (% per month)"); axes[1].set_title("RMW premium over time")
    fig.savefig(fig_dir / FIGURES[2], dpi=150); plt.close(fig)


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
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


def run(out_dir: Path, fig_dir: Path) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch26_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 26 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True); fig_dir.mkdir(parents=True, exist_ok=True)
    study = quality_study(quality_world())
    rmw = rmw_study()
    _figures(study, rmw, fig_dir)
    result = {"seed": SEED, "hand_examples": hand_examples(), "constructed": study, "rmw": rmw}
    (out_dir / "ch26_results.json").write_text(json.dumps(_clean(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _clean(result)


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch26_quality_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(default_run / "results"))
    parser.add_argument("--figures", default=str(default_run / "figures"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    c = r["constructed"]["ic_spearman"]
    print("IC:", {k: round(v["mean"], 4) for k, v in c.items()}, "| composite", round(r["constructed"]["ic_composite_gpa_and_minus_accrual"]["mean"], 4))
    print(f"RMW all {r['rmw']['by_period']['all']['mean_pct']:.3f}%/mo (t {r['rmw']['by_period']['all']['t']:.2f})")


if __name__ == "__main__":
    main()
