"""Chapter 30 CLI: Backtesting Biases (Look-ahead, Survivorship, Selection, Data Snooping,
Overfitting, Corporate Actions, Parameter Mining, and Cost Modeling).

Run from the course root:

    .venv/bin/python code/ch30_backtest_biases.py

Outputs ``qa/a6/codex_resume/ch30/results_v2/ch30_results.json`` and a companion
figure directory by default (refuses to overwrite).
Constructed: 36 synthetic assets over 522 synthetic weekday observations (2024-01-02 to 2025-12-31, seed 20261030)
with announcements, corporate actions (2:1 split on S05, dividends on S08 and S12, delistings on S35 and S36).
Real: Kenneth French 10 industry portfolios monthly returns (1926-07 to 2026-08, revised history,
aggregate value-weighted returns, not point-in-time, not tradable instruments).

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
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.backtest import (  # noqa: E402
    BacktestConfig, BacktestResult, reconcile, run_backtest,
)
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.performance import (  # noqa: E402
    annualized_volatility, cagr, drawdown_path, sharpe_ratio,
)
from quant_course.research_protocol import (  # noqa: E402
    TrialLedger, bonferroni_adjust, expected_max_standard_normal,
    expected_max_standard_normal_exact,
)

SEED = 20261030
FIGURES = (
    "ch30_lookahead_and_survivorship.png",
    "ch30_data_snooping_trials.png",
    "ch30_overfitting_and_parameter_mining.png",
    "ch30_corporate_actions_and_costs.png",
)


def split_dividend_reference_price(previous_close, split_ratio, dividend_per_post_split_share):
    """Ex-action raw-price reference under split-then-dividend ledger ordering."""
    ratio = np.asarray(split_ratio, dtype=float)
    if (ratio <= 0).any():
        raise ValueError("split ratios must be positive")
    return np.asarray(previous_close, dtype=float) / ratio - np.asarray(
        dividend_per_post_split_share, dtype=float
    )


# ------------------------------------------------------------------ dataset generation
def build_constructed_market(seed: int = SEED) -> dict:
    """Generate 36 assets over 522 synthetic Monday-Friday observations.

    This weekday grid is not an exchange calendar and includes exchange holidays
    (for example 2025-01-01); 252 observations/year is only a conventional
    annualization factor here.

    Features:
    - S01 to S36 with cross-sectional and market components.
    - S05: 2-for-1 split on day 125 (2024-06-25).
    - S08: 1.00 USD cash dividend on days 60, 180, 300, 420.
    - S12: 1.50 USD cash dividend on days 100, 220, 340, 460.
    - S35: distress drop and delisting on day 180 (2024-09-10, cash 2.00 USD).
    - S36: distress drop and delisting on day 350 (2025-05-06, cash 1.00 USD).
    - Announcements: every 21 weekday observations after close, 12 stocks announce earnings
      surprises; the jump occurs at the next observation's open.
    - Ex-dividend reference price convention: D is cash per post-split share, so on an
      ex-date t the reference price is P[t-1] / S[t] - D[t].
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-02", "2025-12-31")
    T = len(dates)
    assets = [f"S{i:02d}" for i in range(1, 37)]
    N = len(assets)

    market_innov = rng.normal(0.0004, 0.012, T)
    idio_innov = rng.normal(0.0, 0.018, (T, N))
    daily_rets = market_innov[:, None] * 0.8 + idio_innov

    # Corporate action setup
    split_day = 125  # 2024-06-25
    splits_df = pd.DataFrame(1.0, index=dates, columns=assets)
    splits_df.iloc[split_day, assets.index("S05")] = 2.0

    divs_df = pd.DataFrame(0.0, index=dates, columns=assets)
    for d in [60, 180, 300, 420]:
        divs_df.iloc[d, assets.index("S08")] = 1.00
    for d in [100, 220, 340, 460]:
        divs_df.iloc[d, assets.index("S12")] = 1.50

    delist_day_1 = 180  # 2024-09-10
    delist_day_2 = 350  # 2025-05-06
    delistings = {
        "S35": (dates[delist_day_1], 2.0),
        "S36": (dates[delist_day_2], 1.0),
    }

    # Severe distress drops prior to delisting
    daily_rets[delist_day_1 - 40:delist_day_1, assets.index("S35")] = -0.04 + rng.normal(0, 0.01, 40)
    daily_rets[delist_day_2 - 40:delist_day_2, assets.index("S36")] = -0.04 + rng.normal(0, 0.01, 40)

    # Earnings announcements (every 21 days after close)
    announcement_dates = [dates[k] for k in range(21, T - 2, 21)]
    earnings_surprises = pd.DataFrame(0.0, index=dates, columns=assets)
    for ad in announcement_dates:
        chosen = rng.choice(assets, size=12, replace=False)
        surp = rng.normal(0.0, 1.0, size=12)
        for a, s in zip(chosen, surp):
            earnings_surprises.loc[ad, a] = s

    # Generate unadjusted mark and execution prices
    P = np.zeros((T, N))
    E = np.zeros((T, N))
    P[0] = 100.0
    E[0] = 100.0

    for t in range(1, T):
        prev_P = P[t - 1].copy()
        split_ratio = splits_df.iloc[t].to_numpy()
        div_cash = divs_df.iloc[t].to_numpy()
        # Item 1 / C30-01: D is quoted per post-split share and paid after shares split.
        prev_P_adj = split_dividend_reference_price(prev_P, split_ratio, div_cash)

        overnight_gap = rng.normal(0.0, 0.003, N)
        # Pre-open surprise jump based on announcement at close of t-1
        surprise_jump = 0.025 * earnings_surprises.iloc[t - 1].to_numpy()
        E[t] = prev_P_adj * (1.0 + overnight_gap + surprise_jump)

        day_ret = daily_rets[t]
        P[t] = E[t] * (1.0 + day_ret)

    P_df = pd.DataFrame(P, index=dates, columns=assets)
    E_df = pd.DataFrame(E, index=dates, columns=assets)

    # Delisted assets become NaN after delisting date
    P_df.loc[dates[delist_day_1]:, "S35"] = np.nan
    E_df.loc[dates[delist_day_1]:, "S35"] = np.nan
    P_df.loc[dates[delist_day_2]:, "S36"] = np.nan
    E_df.loc[dates[delist_day_2]:, "S36"] = np.nan

    return {
        "dates": dates,
        "assets": assets,
        "mark_prices": P_df,
        "exec_prices": E_df,
        "splits": splits_df,
        "dividends": divs_df,
        "delistings": delistings,
        "earnings_surprises": earnings_surprises,
        "announcement_dates": announcement_dates,
    }


def _calc_stats(res: BacktestResult) -> dict:
    led = res.ledger
    final_nav = float(led["nav"].iloc[-1])
    tot_ret = float(final_nav / led["nav"].iloc[0] - 1.0)
    n_intervals = len(led) - 1  # N returns span N+1 NAV observations.
    initial_nav = float(led["nav"].iloc[0])
    cg = float(cagr(initial_nav, final_nav, n_intervals / 252.0))
    rets = led["ret"].iloc[1:].to_numpy(dtype=float)
    sh = float(sharpe_ratio(rets, np.zeros_like(rets), 252.0))
    vol = float(annualized_volatility(rets, 252.0))
    dd = float(drawdown_path(led["nav"].to_numpy()).min())
    return {
        "final_nav": final_nav,
        "total_return": tot_ret,
        "cagr": cg,
        "sharpe": sh,
        "volatility": vol,
        "max_drawdown": dd,
    }


def economic_daily_returns(data: dict, mark_prices: pd.DataFrame | None = None,
                           splits: pd.DataFrame | None = None,
                           dividends: pd.DataFrame | None = None,
                           delistings: dict | None = None) -> pd.DataFrame:
    """Return point-in-time close-to-close economic returns from raw ledger prices.

    The backtest itself continues to trade and mark the supplied unadjusted prices.
    For research features, this converts each day's price and cash-flow events into
    the return earned by a position held from the previous close through today's
    close. Split ratios and per-post-split-share dividends follow the ledger's
    event order. A delisting row uses its cash-out price; later rows stay missing.
    """
    prices = data["mark_prices"] if mark_prices is None else mark_prices
    split_table = (data["splits"] if splits is None else splits).reindex_like(prices)
    dividend_table = (data["dividends"] if dividends is None else dividends).reindex_like(prices)
    delisting_table = data["delistings"] if delistings is None else delistings
    close_or_cash = prices.copy()
    for asset, (date, cash_out_per_share) in delisting_table.items():
        if date in close_or_cash.index and asset in close_or_cash.columns:
            close_or_cash.loc[date, asset] = cash_out_per_share
    gross = (close_or_cash + dividend_table) * split_table / prices.shift(1)
    return gross - 1.0


def open_to_close_returns(data: dict, mark_prices: pd.DataFrame | None = None,
                          exec_prices: pd.DataFrame | None = None) -> pd.DataFrame:
    """Gross holding-period returns for a signal at close d filled at open d+1.

    A new position buys after that session's split/dividend processing, so the
    label is close / execution-open - 1. The overnight gap from close d to open
    d+1 occurs before the fill and is excluded.
    """
    prices = data["mark_prices"] if mark_prices is None else mark_prices
    execution = data["exec_prices"] if exec_prices is None else exec_prices
    return prices.reindex_like(execution) / execution - 1.0


def trailing_compounded_return(returns: pd.DataFrame, signal_date, lookback: int) -> pd.Series:
    """Compound exactly ``lookback`` economic returns through the signal close."""
    if lookback <= 0:
        raise ValueError("lookback must be positive")
    loc = returns.index.get_loc(signal_date)
    start = loc - lookback + 1
    if start < 0:
        return pd.Series(np.nan, index=returns.columns, dtype=float)
    window = returns.iloc[start:loc + 1]
    return (1.0 + window).prod(axis=0, min_count=lookback) - 1.0


# ------------------------------------------------------------------ 8 bias studies
def study_lookahead(data: dict) -> dict:
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs, delistings = data["splits"], data["dividends"], data["delistings"]
    surprises = data["earnings_surprises"]
    ann_dates = data["announcement_dates"]

    surp_stocks = [a for a in assets if a not in ["S35", "S36"]]
    tw_fixed_rows, tw_wrong_rows = [], []
    sig_dates_fixed, sig_dates_wrong = [], []

    for ad in ann_dates:
        t_idx = dates.get_loc(ad)
        s_row = surprises.loc[ad, surp_stocks]
        top_long = s_row.nlargest(5).index
        w = pd.Series(0.0, index=assets)
        w[top_long] = 0.2

        tw_fixed_rows.append(w)
        # The announcement is at 16:30 after close(ad). Under the chapter's
        # close-time decision contract it first enters the next observation's
        # close signal; lag=1 then fills at the following observation's open.
        sig_dates_fixed.append(dates[t_idx + 1])

        tw_wrong_rows.append(w)
        sig_dates_wrong.append(dates[t_idx - 1])

    tw_fixed = pd.DataFrame(tw_fixed_rows, index=sig_dates_fixed)
    tw_wrong = pd.DataFrame(tw_wrong_rows, index=sig_dates_wrong)

    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_fixed = run_backtest(P, tw_fixed, cfg, exec_prices=E, splits=splits, dividends=divs, delistings=delistings)
    res_wrong = run_backtest(P, tw_wrong, cfg, exec_prices=E, splits=splits, dividends=divs, delistings=delistings)

    st_fixed = _calc_stats(res_fixed)
    st_wrong = _calc_stats(res_wrong)

    return {
        "fixed": st_fixed,
        "wrong": st_wrong,
        "diff_final_nav": st_wrong["final_nav"] - st_fixed["final_nav"],
        "diff_sharpe": st_wrong["sharpe"] - st_fixed["sharpe"],
        "sign": "wrong > fixed" if st_wrong["sharpe"] > st_fixed["sharpe"] else "wrong <= fixed",
        "causal_signal_contract": "announcement after close on d; signal at close d+1; lag=1 fill at open d+2",
        "what_fix_leaves_unsolved": (
            "The close-after-announcement signal schedule plus lag=1 prevents this synthetic timing leak, but does not solve "
            "data revisions (subsequent restatements), vendor delivery latencies, or intraday "
            "execution feasibility (limit-up trading halts preventing fill at open)."
        ),
        "_res_fixed": res_fixed,
        "_res_wrong": res_wrong,
    }


def study_survivorship(data: dict) -> dict:
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs, delistings = data["splits"], data["dividends"], data["delistings"]

    rebal_dates = [dates[k] for k in range(0, len(dates) - 1, 21)]
    survivors = [a for a in assets if a not in ["S35", "S36"]]

    tw_wrong_rows, tw_fixed_rows = [], []
    for rd in rebal_dates:
        w_w = pd.Series(0.0, index=assets)
        w_w[survivors] = 1.0 / len(survivors)
        tw_wrong_rows.append(w_w)

        w_f = pd.Series(0.0, index=assets)
        alive_at_rd = [a for a in assets if not (a in delistings and rd >= delistings[a][0])]
        w_f[alive_at_rd] = 1.0 / len(alive_at_rd)
        tw_fixed_rows.append(w_f)

    tw_wrong = pd.DataFrame(tw_wrong_rows, index=rebal_dates)[survivors]
    tw_fixed = pd.DataFrame(tw_fixed_rows, index=rebal_dates)

    P_surv = P[survivors].copy()
    E_surv = E[survivors].copy()
    splits_surv = splits[survivors].copy()
    divs_surv = divs[survivors].copy()

    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_wrong = run_backtest(P_surv, tw_wrong, cfg, exec_prices=E_surv, splits=splits_surv, dividends=divs_surv)
    res_fixed = run_backtest(P, tw_fixed, cfg, exec_prices=E, splits=splits, dividends=divs, delistings=delistings)

    st_wrong = _calc_stats(res_wrong)
    st_fixed = _calc_stats(res_fixed)

    # Item 4 / C30-04: Truncated normal check: mu=0, sigma=0.3, d=-0.3
    mu_X, sigma_X, d_val = 0.0, 0.3, -0.3
    alpha_val = (d_val - mu_X) / sigma_X
    phi_alpha = float(stats.norm.pdf(alpha_val))
    Phi_alpha = float(stats.norm.cdf(alpha_val))
    lambda_alpha = phi_alpha / (1.0 - Phi_alpha)
    trunc_mean = mu_X + sigma_X * lambda_alpha
    trunc_bias = trunc_mean - mu_X

    # Item 5 / C30-05: S35 delisting hand check on day 180 (2024-09-10)
    delist_date_s35 = dates[180]
    date_before_s35 = dates[179]
    s35_shares_held = float(res_fixed.positions.loc[date_before_s35, "S35"])
    s35_price_before = float(P.loc[date_before_s35, "S35"])
    s35_delist_cash_rate = 2.0
    s35_delist_cash_total = s35_shares_held * s35_delist_cash_rate
    s35_pre_delist_market_val = s35_shares_held * s35_price_before
    s35_delist_loss = s35_pre_delist_market_val - s35_delist_cash_total

    return {
        "fixed": st_fixed,
        "wrong": st_wrong,
        "diff_final_nav": st_wrong["final_nav"] - st_fixed["final_nav"],
        "diff_sharpe": st_wrong["sharpe"] - st_fixed["sharpe"],
        "sign": "wrong > fixed" if st_wrong["sharpe"] > st_fixed["sharpe"] else "wrong <= fixed",
        "truncated_normal_check": {
            "mu_X": mu_X,
            "sigma_X": sigma_X,
            "d": d_val,
            "alpha": alpha_val,
            "default_prob": Phi_alpha,
            "inverse_mills_ratio": lambda_alpha,
            "truncated_mean": trunc_mean,
            "bias": trunc_bias,
        },
        "s35_delisting_hand_check": {
            "delist_date": str(delist_date_s35.date()),
            "date_before": str(date_before_s35.date()),
            "shares_held": s35_shares_held,
            "price_before": s35_price_before,
            "delist_price": s35_delist_cash_rate,
            "delist_cash_received": s35_delist_cash_total,
            "pre_delist_market_value": s35_pre_delist_market_val,
            "delist_loss": s35_delist_loss,
        },
        "what_fix_leaves_unsolved": (
            "Point-in-time universe tracking accounts for observed delistings, but does not solve "
            "uncertainty in delisting cash-out values (OTC market haircut risk), pre-delisting "
            "trading suspensions, or survivor bias in raw database vendor coverage where bankrupt "
            "firms were never recorded."
        ),
        "_res_fixed": res_fixed,
        "_res_wrong": res_wrong,
    }


def study_selection(data: dict) -> dict:
    """Item 10 / C30-10: Run selection bias on full PIT universe including S35/S36 with delistings."""
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs, delistings = data["splits"], data["dividends"], data["delistings"]
    econ_rets = economic_daily_returns(data)

    # Wrong version: ex-post full-sample (2024-2025) Sharpe to pick top 10 assets
    asset_sharpes = pd.Series(dtype=float)
    for a in assets:
        rets_a = econ_rets[a].dropna()
        asset_sharpes[a] = float(rets_a.mean() / rets_a.std() * np.sqrt(252.0)) if len(rets_a) > 20 else -999.0
    top10_expost = asset_sharpes.nlargest(10).index.tolist()

    rebal_dates = [dates[k] for k in range(0, len(dates) - 1, 21)]
    tw_wrong_rows, tw_fixed_rows = [], []
    for rd in rebal_dates:
        # Wrong: holds ex-post top 10 unconditionally
        w_w = pd.Series(0.0, index=assets)
        w_w[top10_expost] = 0.10
        tw_wrong_rows.append(w_w)

        # Fixed: dynamically selects top 10 assets among ALIVE assets at rd using trailing 60-day returns
        alive_at_rd = [a for a in assets if not (a in delistings and rd >= delistings[a][0])]
        t_loc = dates.get_loc(rd)
        if t_loc >= 60:
            hist_rets = econ_rets[alive_at_rd].iloc[t_loc - 59:t_loc + 1]
            hist_sh = hist_rets.mean() / hist_rets.std()
            top10_dyn = hist_sh.nlargest(10).index.tolist()
        else:
            top10_dyn = alive_at_rd[:10]
        w_f = pd.Series(0.0, index=assets)
        w_f[top10_dyn] = 1.0 / len(top10_dyn)
        tw_fixed_rows.append(w_f)

    tw_wrong = pd.DataFrame(tw_wrong_rows, index=rebal_dates)
    tw_fixed = pd.DataFrame(tw_fixed_rows, index=rebal_dates)

    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_wrong = run_backtest(P, tw_wrong, cfg, exec_prices=E, splits=splits, dividends=divs, delistings=delistings)
    res_fixed = run_backtest(P, tw_fixed, cfg, exec_prices=E, splits=splits, dividends=divs, delistings=delistings)

    st_wrong = _calc_stats(res_wrong)
    st_fixed = _calc_stats(res_fixed)

    return {
        "fixed": st_fixed,
        "wrong": st_wrong,
        "top10_expost": top10_expost,
        "diff_final_nav": st_wrong["final_nav"] - st_fixed["final_nav"],
        "diff_sharpe": st_wrong["sharpe"] - st_fixed["sharpe"],
        "sign": "wrong > fixed" if st_wrong["sharpe"] > st_fixed["sharpe"] else "wrong <= fixed",
        "what_fix_leaves_unsolved": (
            "Dynamic trailing selection eliminates ex-post cherry picking, but broad benchmark "
            "universes (such as S&P 500 or CSI 300) still carry subtle committee-selection bias "
            "inherent to index inclusion rules."
        ),
        "_res_fixed": res_fixed,
        "_res_wrong": res_wrong,
    }


def study_data_snooping(data: dict) -> dict:
    """Item 3 & Item 13: 50 trials, exact/BLdP/Gumbel expected max, full bonferroni_adjust vector."""
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs = data["splits"], data["dividends"]
    econ_rets = economic_daily_returns(data)

    survivors = [a for a in assets if a not in ["S35", "S36"]]
    P_surv = P[survivors].copy()
    E_surv = E[survivors].copy()
    splits_surv = splits[survivors].copy()
    divs_surv = divs[survivors].copy()

    rebal_dates = [dates[k] for k in range(0, len(dates) - 1, 21)]
    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)

    ledger = TrialLedger()
    cand_sharpes = []
    cand_specs = []

    for m in range(1, 51):
        k = 3 + m
        tw_cand_rows = []
        for rd in rebal_dates:
            t_loc = dates.get_loc(rd)
            if t_loc >= k:
                vals = trailing_compounded_return(econ_rets[survivors], rd, k)
                top5 = vals.nlargest(5).index
                w = pd.Series(0.0, index=survivors)
                w[top5] = 0.20
            else:
                w = pd.Series(0.0, index=survivors)
            tw_cand_rows.append(w)
        tw_cand = pd.DataFrame(tw_cand_rows, index=rebal_dates)
        res_cand = run_backtest(P_surv, tw_cand, cfg, exec_prices=E_surv, splits=splits_surv, dividends=divs_surv)
        st_cand = _calc_stats(res_cand)
        cand_sharpes.append(st_cand["sharpe"])
        cand_specs.append({"trial": m, "lookback": k, "sharpe": st_cand["sharpe"], "cagr": st_cand["cagr"]})
        ledger.record({"lookback": k}, metric=st_cand["sharpe"], n_obs=len(dates), status="run")

    best_idx = int(np.argmax(cand_sharpes))
    best_spec = cand_specs[best_idx]
    median_sh = float(np.median(cand_sharpes))
    mean_sh = float(np.mean(cand_sharpes))
    max_sh = float(np.max(cand_sharpes))
    min_sh = float(np.min(cand_sharpes))

    # Item 3 / C30-03: Three expected max values for M=50
    M = 50
    exact_exp_max = float(expected_max_standard_normal_exact(M))
    bldp_exp_max = float(expected_max_standard_normal(M))
    gamma_euler = 0.5772156649015329
    log_M = np.log(float(M))
    denom = np.sqrt(2.0 * log_M)
    gumbel_exp_max = float(denom + gamma_euler / denom - (np.log(4.0 * np.pi) + np.log(log_M)) / (2.0 * denom))

    # Item 13 / L-01: Full vector of 50 p-values into bonferroni_adjust
    t_stats = np.array([sh * np.sqrt(2.0) for sh in cand_sharpes])
    p_nominals = 2.0 * (1.0 - stats.norm.cdf(np.abs(t_stats)))
    p_bonferronis = bonferroni_adjust(p_nominals)

    p_nominal_best = float(p_nominals[best_idx])
    p_bonf_best = float(p_bonferronis[best_idx])

    return {
        "n_trials": 50,
        "best_trial": best_spec,
        "max_sharpe": max_sh,
        "median_sharpe": median_sh,
        "mean_sharpe": mean_sh,
        "min_sharpe": min_sh,
        "expected_max_exact": exact_exp_max,
        "expected_max_bldp": bldp_exp_max,
        "expected_max_gumbel": gumbel_exp_max,
        "t_stat": float(t_stats[best_idx]),
        "p_nominal": p_nominal_best,
        "p_bonferroni": p_bonf_best,
        "trial_ledger_trials_count": ledger.n_trials,
        "cand_sharpes": cand_sharpes,
        "p_nominals": p_nominals.tolist(),
        "p_bonferronis": p_bonferronis.tolist(),
        "what_fix_leaves_unsolved": (
            "TrialLedger documents all explicit machine trials, but cannot capture informal "
            "mental trials abandoned before logging, or collective data snooping across researchers "
            "sharing the same public historical financial data."
        ),
    }


def study_overfitting(data: dict) -> dict:
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs = data["splits"], data["dividends"]

    survivors = [a for a in assets if a not in ["S35", "S36"]]
    P_surv = P[survivors].copy()
    E_surv = E[survivors].copy()
    econ_rets = economic_daily_returns(data)[survivors]
    next_open_close = open_to_close_returns(data)[survivors]

    is_mask = dates.year == 2024
    oos_mask = dates.year == 2025
    is_dates = dates[is_mask]
    oos_dates = dates[oos_mask]

    P_is, E_is = P_surv.loc[is_dates], E_surv.loc[is_dates]
    P_oos, E_oos = P_surv.loc[oos_dates], E_surv.loc[oos_dates]

    # Each row is one asset at a signal close in 2024. Features use the last eight
    # close-to-close economic returns through that close; the target is the next
    # session's open-to-close return, exactly the interval earned after lag=1 fill.
    X_rows, y_rows = [], []
    for loc in range(8, len(is_dates) - 1):
        signal_date, trade_date = is_dates[loc], is_dates[loc + 1]
        feature_window = econ_rets.loc[is_dates[loc - 7]:signal_date, survivors]
        features = feature_window.iloc[::-1].to_numpy().T
        labels = next_open_close.loc[trade_date, survivors].to_numpy(float)
        valid = np.isfinite(labels) & np.isfinite(features).all(axis=1)
        X_rows.append(features[valid])
        y_rows.append(labels[valid])
    X_is_mat = np.vstack(X_rows)
    y_is_vec = np.concatenate(y_rows)
    beta_overfit = np.linalg.lstsq(X_is_mat, y_is_vec, rcond=None)[0]

    is_rebal_dates = list(is_dates[8:-1:10])
    oos_rebal_dates = list(oos_dates[:-1:10])

    def predict_weights(signal_dates, beta):
        rows = []
        for d in signal_dates:
            loc = econ_rets.index.get_loc(d)
            features = econ_rets.iloc[loc - 7:loc + 1][survivors].iloc[::-1].to_numpy().T
            prediction = features @ beta
            top5 = np.argsort(prediction)[-5:]
            weights = pd.Series(0.0, index=survivors)
            weights.iloc[top5] = 0.20
            rows.append(weights)
        return pd.DataFrame(rows, index=signal_dates)

    def momentum_weights(signal_dates):
        rows = []
        for d in signal_dates:
            momentum = trailing_compounded_return(econ_rets[survivors], d, 20)
            weights = pd.Series(0.0, index=survivors)
            weights[momentum.nlargest(5).index] = 0.20
            rows.append(weights)
        return pd.DataFrame(rows, index=signal_dates)

    tw_overfit_is = predict_weights(is_rebal_dates, beta_overfit)
    tw_overfit_oos = predict_weights(oos_rebal_dates, beta_overfit)
    tw_simple_is = momentum_weights(is_rebal_dates)
    tw_simple_oos = momentum_weights(oos_rebal_dates)

    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_overfit_is = run_backtest(P_is, tw_overfit_is, cfg, exec_prices=E_is, splits=splits[survivors].loc[is_dates], dividends=divs[survivors].loc[is_dates])
    res_overfit_oos = run_backtest(P_oos, tw_overfit_oos, cfg, exec_prices=E_oos, splits=splits[survivors].loc[oos_dates], dividends=divs[survivors].loc[oos_dates])
    res_simple_is = run_backtest(P_is, tw_simple_is, cfg, exec_prices=E_is, splits=splits[survivors].loc[is_dates], dividends=divs[survivors].loc[is_dates])
    res_simple_oos = run_backtest(P_oos, tw_simple_oos, cfg, exec_prices=E_oos, splits=splits[survivors].loc[oos_dates], dividends=divs[survivors].loc[oos_dates])

    st_overfit_is = _calc_stats(res_overfit_is)
    st_overfit_oos = _calc_stats(res_overfit_oos)
    st_simple_is = _calc_stats(res_simple_is)
    st_simple_oos = _calc_stats(res_simple_oos)

    return {
        "overfitted_model": {
            "is": st_overfit_is,
            "oos": st_overfit_oos,
            "sharpe_decay": st_overfit_oos["sharpe"] - st_overfit_is["sharpe"],
        },
        "simple_model": {
            "is": st_simple_is,
            "oos": st_simple_oos,
            "sharpe_decay": st_simple_oos["sharpe"] - st_simple_is["sharpe"],
        },
        "label_interval": "next-session open-to-close gross return; excludes the pre-fill overnight gap",
        "feature_interval": "eight trailing close-to-close economic returns through signal close",
        "training_rows": int(len(y_is_vec)),
        "is_rebalance_count": len(is_rebal_dates),
        "oos_rebalance_count": len(oos_rebal_dates),
        "what_fix_leaves_unsolved": (
            "A single train/test split isolates in-sample fitting, but does not prevent iterative "
            "leakage from repeated trial-and-error evaluations against the test set, nor does it "
            "address serial correlation leakage across overlapping label horizons (formalized in "
            "Chapter 31 via Purged CV and Embargo)."
        ),
        "_res_overfit_is": res_overfit_is,
        "_res_overfit_oos": res_overfit_oos,
        "_res_simple_is": res_simple_is,
        "_res_simple_oos": res_simple_oos,
    }


def study_corporate_actions(data: dict) -> dict:
    """Item 1 & Item 5: Unadjusted prices with splits/dividends; exact day 124/125 hand checks."""
    dates = data["dates"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs = data["splits"], data["dividends"]

    tw_ca = pd.DataFrame({"S05": [0.5], "S08": [0.5]}, index=[dates[0]])
    P_ca = P[["S05", "S08"]].copy()
    E_ca = E[["S05", "S08"]].copy()
    splits_ca = splits[["S05", "S08"]].copy()
    divs_ca = divs[["S05", "S08"]].copy()

    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_fixed = run_backtest(P_ca, tw_ca, cfg, exec_prices=E_ca, splits=splits_ca, dividends=divs_ca)
    rec_ca = reconcile(res_fixed, P_ca, cfg, exec_prices=E_ca, splits=splits_ca)
    max_rec_residual = float(rec_ca["residual"].abs().max())

    res_no_split = run_backtest(P_ca, tw_ca, cfg, exec_prices=E_ca, dividends=divs_ca)

    # Error B: total-return adjusted prices + dividends double counted
    div_cum = (1.0 + divs_ca["S08"] / P_ca["S08"]).cumprod()
    P_adj = P_ca.copy()
    E_adj = E_ca.copy()
    P_adj["S08"] = P_ca["S08"] * div_cum
    E_adj["S08"] = E_ca["S08"] * div_cum
    res_double_div = run_backtest(P_adj, tw_ca, cfg, exec_prices=E_adj, splits=splits_ca, dividends=divs_ca)

    st_fixed = _calc_stats(res_fixed)
    st_no_split = _calc_stats(res_no_split)
    st_double_div = _calc_stats(res_double_div)

    # Item 5 / C30-05: Real hand-check numbers from actual run
    d124 = dates[124]
    d125 = dates[125]
    s05_shares_124 = float(res_fixed.positions.loc[d124, "S05"])
    s05_close_124 = float(P_ca.loc[d124, "S05"])
    s05_exec_125 = float(E_ca.loc[d125, "S05"])
    s05_close_125 = float(P_ca.loc[d125, "S05"])
    s05_shares_fixed_125 = float(res_fixed.positions.loc[d125, "S05"])
    s05_shares_no_split_125 = float(res_no_split.positions.loc[d125, "S05"])
    nav_fixed_124 = float(res_fixed.ledger.loc[d124, "nav"])
    nav_fixed_125 = float(res_fixed.ledger.loc[d125, "nav"])
    nav_no_split_125 = float(res_no_split.ledger.loc[d125, "nav"])
    cash_fixed_124 = float(res_fixed.ledger.loc[d124, "cash_end"])
    cash_fixed_125 = float(res_fixed.ledger.loc[d125, "cash_end"])

    return {
        "fixed": st_fixed,
        "split_ignored": st_no_split,
        "dividend_double_counted": st_double_div,
        "max_reconcile_residual": max_rec_residual,
        "split_day_nav_drop_no_split": float(res_no_split.ledger["ret"].iloc[125]),
        "split_day_nav_ret_fixed": float(res_fixed.ledger["ret"].iloc[125]),
        "day_125_split_hand_check": {
            "date_124": str(d124.date()),
            "date_125": str(d125.date()),
            "s05_shares_day_124": s05_shares_124,
            "s05_close_day_124": s05_close_124,
            "s05_exec_day_125": s05_exec_125,
            "s05_close_day_125": s05_close_125,
            "s05_shares_fixed_125": s05_shares_fixed_125,
            "s05_shares_no_split_125": s05_shares_no_split_125,
            "cash_fixed_124": cash_fixed_124,
            "cash_fixed_125": cash_fixed_125,
            "nav_fixed_124": nav_fixed_124,
            "nav_fixed_125": nav_fixed_125,
            "nav_no_split_125": nav_no_split_125,
            "ret_fixed_125": float(res_fixed.ledger["ret"].iloc[125]),
            "ret_no_split_125": float(res_no_split.ledger["ret"].iloc[125]),
            "s08_shares_125": float(res_fixed.positions.loc[d125, "S08"]),
            "s08_close_day_124": float(P_ca.loc[d124, "S08"]),
            "s08_exec_day_125": float(E_ca.loc[d125, "S08"]),
            "s08_close_day_125": float(P_ca.loc[d125, "S08"]),
            "s05_value_fixed_125": s05_shares_fixed_125 * s05_close_125,
            "s05_value_no_split_125": s05_shares_no_split_125 * s05_close_125,
            "s08_value_125": float(res_fixed.positions.loc[d125, "S08"]) * float(P_ca.loc[d125, "S08"]),
        },
        "what_fix_leaves_unsolved": (
            "Feeding unadjusted prices with explicit split and dividend tables ensures mathematical "
            "conservation, but does not resolve complex corporate reorganizations (e.g. spinoff "
            "distributions of untraded subsidiaries), scrip dividends, rights offerings dilution, "
            "or dividend withholding tax variations."
        ),
        "_res_fixed": res_fixed,
        "_res_no_split": res_no_split,
        "_res_double_div": res_double_div,
    }


def study_parameter_mining(data: dict) -> dict:
    """Item 14 / L-02: Warm-up window from 2024 so all L evaluate on identical 2025 window."""
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs = data["splits"], data["dividends"]

    survivors = [a for a in assets if a not in ["S35", "S36"]]
    P_surv = P[survivors].copy()
    E_surv = E[survivors].copy()

    is_mask = dates.year == 2024
    oos_mask = dates.year == 2025
    is_dates = dates[is_mask]
    oos_dates = dates[oos_mask]

    P_is, E_is = P_surv.loc[is_dates], E_surv.loc[is_dates]
    P_oos, E_oos = P_surv.loc[oos_dates], E_surv.loc[oos_dates]

    econ_rets = economic_daily_returns(data)[survivors]

    param_grid = list(range(5, 65, 5))
    grid_records = []
    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)

    # The same IS and OOS signal dates are used for every lookback. Signals include
    # the close on d; the lag=1 order fills at d+1 open.
    is_rebal_dates = list(is_dates[60:-1:10])
    oos_rebal_dates = list(oos_dates[:-1:10])

    for L in param_grid:
        tw_is_rows = []
        for d in is_rebal_dates:
            mom = trailing_compounded_return(econ_rets, d, L)
            w = pd.Series(0.0, index=survivors)
            w[mom.nlargest(5).index] = 0.20
            tw_is_rows.append(w)
        tw_is_df = pd.DataFrame(tw_is_rows, index=is_rebal_dates)

        # OOS features may use earlier history, but not future observations.
        tw_oos_rows = []
        for d in oos_rebal_dates:
            mom = trailing_compounded_return(econ_rets, d, L)
            w = pd.Series(0.0, index=survivors)
            w[mom.nlargest(5).index] = 0.20
            tw_oos_rows.append(w)
        tw_oos_df = pd.DataFrame(tw_oos_rows, index=oos_rebal_dates)

        r_is = run_backtest(P_is, tw_is_df, cfg, exec_prices=E_is, splits=splits[survivors].loc[is_dates], dividends=divs[survivors].loc[is_dates])
        r_oos = run_backtest(P_oos, tw_oos_df, cfg, exec_prices=E_oos, splits=splits[survivors].loc[oos_dates], dividends=divs[survivors].loc[oos_dates])

        st_i = _calc_stats(r_is)
        st_o = _calc_stats(r_oos)
        grid_records.append({
            "lookback": L,
            "is_sharpe": st_i["sharpe"],
            "oos_sharpe": st_o["sharpe"],
            "is_cagr": st_i["cagr"],
            "oos_cagr": st_o["cagr"],
        })

    grid_df = pd.DataFrame(grid_records)
    best_is_row = grid_df.loc[grid_df["is_sharpe"].idxmax()]
    median_oos_sh = float(grid_df["oos_sharpe"].median())

    return {
        "grid": grid_records,
        "best_is_lookback": int(best_is_row["lookback"]),
        "best_is_sharpe": float(best_is_row["is_sharpe"]),
        "best_param_oos_sharpe": float(best_is_row["oos_sharpe"]),
        "median_oos_sharpe": median_oos_sh,
        "oos_shrinkage": float(best_is_row["is_sharpe"] - best_is_row["oos_sharpe"]),
        "what_fix_leaves_unsolved": (
            "Reporting the entire parameter surface reveals sensitivity and shrinkage, but "
            "does not resolve regime shifts where structural market dynamics drift over time, "
            "causing the true underlying parameter to evolve continuously."
        ),
    }


def study_cost_modeling(data: dict) -> dict:
    dates, assets = data["dates"], data["assets"]
    P, E = data["mark_prices"], data["exec_prices"]
    splits, divs = data["splits"], data["dividends"]

    survivors = [a for a in assets if a not in ["S35", "S36"]]
    P_surv = P[survivors].copy()
    E_surv = E[survivors].copy()

    rebal_dates = [dates[k] for k in range(0, len(dates) - 1, 5)]
    econ_rets = economic_daily_returns(data)[survivors]
    tw_rows = []
    for rd in rebal_dates:
        t_loc = dates.get_loc(rd)
        if t_loc >= 5:
            vals = trailing_compounded_return(econ_rets, rd, 5)
            top5 = vals.nlargest(5).index
            w = pd.Series(0.0, index=survivors)
            w[top5] = 0.20
        else:
            w = pd.Series(0.0, index=survivors)
        tw_rows.append(w)
    tw_df = pd.DataFrame(tw_rows, index=rebal_dates)

    fee_tiers = [0.0, 0.0005, 0.0010, 0.0020, 0.0050]
    tier_names = ["0_bps", "5_bps", "10_bps", "20_bps", "50_bps"]
    tier_stats = {}
    tier_runs = {}

    for fr, tn in zip(fee_tiers, tier_names):
        cfg = BacktestConfig(initial_cash=100000.0, fee_rate=fr, lag=1)
        r = run_backtest(P_surv, tw_df, cfg, exec_prices=E_surv, splits=splits[survivors], dividends=divs[survivors])
        st = _calc_stats(r)
        tot_notional = float(r.ledger["traded_notional"].sum())
        n_intervals = len(r.ledger) - 1
        ann_turnover = float(tot_notional / (n_intervals / 252.0) / 100000.0 * 100.0)
        tot_fees = float(r.ledger["fees"].sum())
        st.update(total_fees=tot_fees, annualized_turnover=ann_turnover)
        tier_stats[tn] = st
        tier_runs[tn] = r

    ann_turn = tier_stats["10_bps"]["annualized_turnover"]

    return {
        "fee_sensitivity": tier_stats,
        "annualized_turnover": ann_turn,
        "what_fix_leaves_unsolved": (
            "Proportional fee modeling captures linear trading commissions and stamp duties, "
            "but does not model nonlinear market impact (Kyle's lambda / square-root law), "
            "size-dependent liquidity limits, short-borrow financing fees, or forced liquidation "
            "margin haircuts."
        ),
        "_tier_runs": tier_runs,
    }


def study_future_perturbation(data: dict) -> dict:
    """Item 11 / M-02: Perturb every future market/action input and compare prior outputs."""
    dates = data["dates"]
    cutoff_date = dates[261]  # 2025-01-01
    cutoff_loc = dates.get_loc(cutoff_date)
    pert_data = {k: (v.copy(deep=True) if isinstance(v, pd.DataFrame) else v)
                 for k, v in data.items()}
    rng_p = np.random.default_rng(9999)
    after_mask = dates > cutoff_date

    # Stress future close marks, execution prices, disclosures, splits, dividends,
    # and future delisting cash-out metadata. None of these edits touches <= cutoff.
    for key, scale in (("mark_prices", 0.10), ("exec_prices", 0.08)):
        table = pert_data[key]
        shocks = np.exp(rng_p.normal(0.0, scale, size=table.loc[after_mask].shape))
        table.loc[after_mask] = table.loc[after_mask] * shocks

    pert_splits = pert_data["splits"]
    future_event = dates[cutoff_loc + 20]
    pert_splits.loc[future_event, "S04"] = 1.5
    pert_dividends = pert_data["dividends"]
    pert_dividends.loc[after_mask] *= 1.5
    pert_dividends.loc[dates[cutoff_loc + 25], "S01"] += 0.25

    pert_surprises = pert_data["earnings_surprises"]
    pert_surprises.loc[after_mask] = rng_p.normal(0, 1.0, size=pert_surprises.loc[after_mask].shape)
    pert_delistings = dict(data["delistings"])
    for asset, (date, cash_out) in list(pert_delistings.items()):
        if date > cutoff_date:
            pert_delistings[asset] = (date, float(cash_out) * 1.75)
    pert_data["delistings"] = pert_delistings

    def max_frame_diff(left: pd.DataFrame, right: pd.DataFrame) -> float:
        if not left.index.equals(right.index) or list(left.columns) != list(right.columns):
            return float("inf")
        if left.empty:
            return 0.0
        a = left.to_numpy(dtype=float)
        b = right.to_numpy(dtype=float)
        return float(np.nanmax(np.abs(np.nan_to_num(a, nan=0.0) - np.nan_to_num(b, nan=0.0))))

    def fill_diff(left: BacktestResult, right: BacktestResult) -> float:
        cols_key = ["signal_time", "trade_time", "asset"]
        cols_value = ["quantity", "price", "notional", "fee"]
        lf = left.fills.loc[left.fills["trade_time"] <= cutoff_date].sort_values(cols_key).reset_index(drop=True)
        rf = right.fills.loc[right.fills["trade_time"] <= cutoff_date].sort_values(cols_key).reset_index(drop=True)
        if not lf[cols_key].equals(rf[cols_key]):
            # Finite 0/1 identity flag keeps the JSON report standards-compliant.
            return 1.0
        return max_frame_diff(lf[cols_value], rf[cols_value])

    def prior_output_diffs(tw_a: pd.DataFrame, res_a: BacktestResult,
                           tw_b: pd.DataFrame, res_b: BacktestResult) -> dict:
        tw_a = tw_a.loc[tw_a.index <= cutoff_date]
        tw_b = tw_b.loc[tw_b.index <= cutoff_date]
        return {
            "target_weights": max_frame_diff(tw_a, tw_b),
            "filled_orders": fill_diff(res_a, res_b),
            "positions": max_frame_diff(res_a.positions.loc[:cutoff_date], res_b.positions.loc[:cutoff_date]),
            "close_weights": max_frame_diff(res_a.weights.loc[:cutoff_date], res_b.weights.loc[:cutoff_date]),
            "nav": max_frame_diff(res_a.ledger.loc[:cutoff_date, ["nav"]],
                                   res_b.ledger.loc[:cutoff_date, ["nav"]]),
        }

    # 1. Pipeline A: close-time causal signal after the 16:30 announcement.
    def gen_causal_announcement_weights(surp_df):
        surp_stocks = [a for a in data["assets"] if a not in ["S35", "S36"]]
        rows, sig_dates = [], []
        for ad in data["announcement_dates"]:
            t_idx = dates.get_loc(ad)
            s_row = surp_df.loc[ad, surp_stocks]
            top_long = s_row.nlargest(5).index
            w = pd.Series(0.0, index=data["assets"])
            w[top_long] = 0.2
            rows.append(w)
            sig_dates.append(dates[t_idx + 1])
        return pd.DataFrame(rows, index=sig_dates)

    tw_la_orig = gen_causal_announcement_weights(data["earnings_surprises"])
    tw_la_pert = gen_causal_announcement_weights(pert_data["earnings_surprises"])

    cfg = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_la_orig = run_backtest(data["mark_prices"], tw_la_orig, cfg, exec_prices=data["exec_prices"],
                               splits=data["splits"], dividends=data["dividends"], delistings=data["delistings"])
    res_la_pert = run_backtest(pert_data["mark_prices"], tw_la_pert, cfg, exec_prices=pert_data["exec_prices"],
                               splits=pert_data["splits"], dividends=pert_data["dividends"],
                               delistings=pert_data["delistings"])
    la_diffs = prior_output_diffs(tw_la_orig, res_la_orig, tw_la_pert, res_la_pert)

    # 2. Pipeline B: Fixed Selection (dynamic trailing 60-day)
    rebal_dates = [dates[k] for k in range(0, len(dates) - 1, 21)]
    def gen_fixed_selection_weights(p_df, split_df, dividend_df, delist_map):
        econ_rets = economic_daily_returns(data, mark_prices=p_df, splits=split_df,
                                           dividends=dividend_df, delistings=delist_map)
        rows = []
        for rd in rebal_dates:
            alive_at_rd = [a for a in data["assets"] if not (a in delist_map and rd >= delist_map[a][0])]
            t_loc = dates.get_loc(rd)
            if t_loc >= 60:
                hist_rets = econ_rets[alive_at_rd].iloc[t_loc - 59:t_loc + 1]
                hist_sh = hist_rets.mean() / hist_rets.std()
                top10_dyn = hist_sh.nlargest(10).index.tolist()
            else:
                top10_dyn = alive_at_rd[:10]
            w = pd.Series(0.0, index=data["assets"])
            w[top10_dyn] = 1.0 / len(top10_dyn)
            rows.append(w)
        return pd.DataFrame(rows, index=rebal_dates)

    tw_sel_fixed_orig = gen_fixed_selection_weights(data["mark_prices"], data["splits"],
                                                    data["dividends"], data["delistings"])
    tw_sel_fixed_pert = gen_fixed_selection_weights(pert_data["mark_prices"], pert_data["splits"],
                                                    pert_data["dividends"], pert_data["delistings"])

    res_sel_orig = run_backtest(data["mark_prices"], tw_sel_fixed_orig, cfg, exec_prices=data["exec_prices"],
                                splits=data["splits"], dividends=data["dividends"], delistings=data["delistings"])
    res_sel_pert = run_backtest(pert_data["mark_prices"], tw_sel_fixed_pert, cfg,
                                exec_prices=pert_data["exec_prices"], splits=pert_data["splits"],
                                dividends=pert_data["dividends"], delistings=pert_data["delistings"])
    sel_diffs = prior_output_diffs(tw_sel_fixed_orig, res_sel_orig, tw_sel_fixed_pert, res_sel_pert)

    # 3. Pipeline C: WRONG Selection (ex-post full sample across 2024-2025)
    def gen_wrong_selection_weights(p_df, split_df, dividend_df, delist_map):
        econ_rets = economic_daily_returns(data, mark_prices=p_df, splits=split_df,
                                           dividends=dividend_df, delistings=delist_map)
        sh = pd.Series(dtype=float)
        for a in data["assets"]:
            rets_a = econ_rets[a].dropna()
            sh[a] = float(rets_a.mean() / rets_a.std() * np.sqrt(252.0)) if len(rets_a) > 20 else -999.0
        top10 = sh.nlargest(10).index.tolist()
        rows = []
        for rd in rebal_dates:
            w = pd.Series(0.0, index=data["assets"])
            w[top10] = 0.10
            rows.append(w)
        return pd.DataFrame(rows, index=rebal_dates)

    tw_sel_wrong_orig = gen_wrong_selection_weights(data["mark_prices"], data["splits"],
                                                    data["dividends"], data["delistings"])
    tw_sel_wrong_pert = gen_wrong_selection_weights(pert_data["mark_prices"], pert_data["splits"],
                                                    pert_data["dividends"], pert_data["delistings"])
    res_sel_wrong_orig = run_backtest(data["mark_prices"], tw_sel_wrong_orig, cfg,
                                      exec_prices=data["exec_prices"], splits=data["splits"],
                                      dividends=data["dividends"], delistings=data["delistings"])
    res_sel_wrong_pert = run_backtest(pert_data["mark_prices"], tw_sel_wrong_pert, cfg,
                                      exec_prices=pert_data["exec_prices"], splits=pert_data["splits"],
                                      dividends=pert_data["dividends"], delistings=pert_data["delistings"])
    wrong_diffs = prior_output_diffs(tw_sel_wrong_orig, res_sel_wrong_orig,
                                     tw_sel_wrong_pert, res_sel_wrong_pert)

    return {
        "cutoff_date": str(cutoff_date.date()),
        "perturbed_future_inputs": ["mark_prices", "exec_prices", "earnings_surprises",
                                    "splits", "dividends", "future_delisting_cash_out_values"],
        "fixed_lookahead_max_nav_diff_up_to_cutoff": la_diffs["nav"],
        "fixed_lookahead_diffs_up_to_cutoff": la_diffs,
        "fixed_selection_max_weight_diff_up_to_cutoff": sel_diffs["target_weights"],
        "fixed_selection_max_nav_diff_up_to_cutoff": sel_diffs["nav"],
        "fixed_selection_diffs_up_to_cutoff": sel_diffs,
        "is_fixed_invariant": int(all(v < 1e-10 for group in (la_diffs, sel_diffs)
                                      for v in group.values())),
        "wrong_selection_max_weight_diff_up_to_cutoff": wrong_diffs["target_weights"],
        "wrong_selection_max_nav_diff_up_to_cutoff": wrong_diffs["nav"],
        "wrong_selection_diffs_up_to_cutoff": wrong_diffs,
        "is_wrong_causality_violated": int(any(v > 0.0 for v in wrong_diffs.values())),
    }


def study_real_french() -> dict:
    """Item 2 & Item 17: French 10 industries: Full-sample ex-post (wrong) vs Period-1 ex-ante (fixed)."""
    ind, rf, prov = load_industries_and_rf()
    ind_manifest_path = ROOT / "data/manifests/french_industries_2026-10-05.json"
    ind_manifest = json.loads(ind_manifest_path.read_text(encoding="utf-8"))

    rf_manifest_path = ROOT / "data/manifests/french_factors_2026-10-05.json"
    rf_manifest = json.loads(rf_manifest_path.read_text(encoding="utf-8"))

    p1 = ind.loc["1926-07":"1975-12"]
    rf1 = rf.loc["1926-07":"1975-12"]
    p2 = ind.loc["1976-01":"2026-08"]
    rf2 = rf.loc["1976-01":"2026-08"]

    # Full-sample Sharpe (1926-07 to 2026-08)
    sh_full = {col: float(sharpe_ratio(ind[col], rf, 12.0)) for col in ind.columns}
    sorted_sh_full = sorted(sh_full.items(), key=lambda x: x[1], reverse=True)
    top3_full = [k for k, _ in sorted_sh_full[:3]]

    # Period 1 Sharpe (1926-07 to 1975-12)
    sh1 = {col: float(sharpe_ratio(p1[col], rf1, 12.0)) for col in ind.columns}
    sorted_sh1 = sorted(sh1.items(), key=lambda x: x[1], reverse=True)
    top3_p1 = [k for k, _ in sorted_sh1[:3]]

    # Evaluations on Period 2 (1976-01 to 2026-08)
    # Wrong: hold full-sample top 3 in Period 2 (look-ahead selection)
    wrong_p2_ret = p2[top3_full].mean(axis=1)
    wrong_p2_sharpe = float(sharpe_ratio(wrong_p2_ret, rf2, 12.0))
    wrong_p2_cagr = float(cagr(1.0, float(np.prod(1.0 + wrong_p2_ret)), len(wrong_p2_ret) / 12.0))

    # Fixed: hold Period 1 top 3 in Period 2 (ex-ante selection)
    fixed_p2_ret = p2[top3_p1].mean(axis=1)
    fixed_p2_sharpe = float(sharpe_ratio(fixed_p2_ret, rf2, 12.0))
    fixed_p2_cagr = float(cagr(1.0, float(np.prod(1.0 + fixed_p2_ret)), len(fixed_p2_ret) / 12.0))

    # Benchmark: Equal-weight 10 industries in Period 2
    ew10_p2_ret = p2.mean(axis=1)
    ew10_p2_sharpe = float(sharpe_ratio(ew10_p2_ret, rf2, 12.0))
    ew10_p2_cagr = float(cagr(1.0, float(np.prod(1.0 + ew10_p2_ret)), len(ew10_p2_ret) / 12.0))

    # Period 1 equal weight
    ew10_p1_ret = p1.mean(axis=1)
    ew10_p1_sharpe = float(sharpe_ratio(ew10_p1_ret, rf1, 12.0))
    top3_p1_in_p1 = p1[top3_p1].mean(axis=1)
    top3_p1_sharpe_in_p1 = float(sharpe_ratio(top3_p1_in_p1, rf1, 12.0))

    diff_period2_sharpe = wrong_p2_sharpe - fixed_p2_sharpe
    wrong_excess_over_ew10 = wrong_p2_sharpe - ew10_p2_sharpe
    fixed_excess_over_ew10 = fixed_p2_sharpe - ew10_p2_sharpe
    period1_excess_over_ew10 = top3_p1_sharpe_in_p1 - ew10_p1_sharpe
    excess_decay = fixed_excess_over_ew10 - period1_excess_over_ew10

    return {
        "industry_manifest_sha256": hashlib.sha256(ind_manifest_path.read_bytes()).hexdigest(),
        "industry_raw_zip_sha256": ind_manifest["sha256"],
        "processed_sha256": ind_manifest["processed_sha256"],
        "rf_manifest_snapshot_date": rf_manifest["snapshot_date"],
        "rf_processed_sha256": rf_manifest["datasets"]["ff3"]["processed_sha256"],
        "sample_months": len(ind),
        "first_month": str(ind.index[0]),
        "last_month": str(ind.index[-1]),
        "period_1": {
            "range": "1926-07 to 1975-12",
            "months": len(p1),
            "top_3_industries": sorted_sh1[:3],
            "top_3_sharpe": top3_p1_sharpe_in_p1,
            "equal_weight_10_sharpe": ew10_p1_sharpe,
            "top_3_excess_sharpe": period1_excess_over_ew10,
        },
        "full_sample": {
            "top_3_industries": sorted_sh_full[:3],
        },
        "period_2": {
            "range": "1976-01 to 2026-08",
            "months": len(p2),
            "wrong_full_sample_top3_sharpe": wrong_p2_sharpe,
            "wrong_full_sample_top3_cagr": wrong_p2_cagr,
            "fixed_period1_top3_sharpe": fixed_p2_sharpe,
            "fixed_period1_top3_cagr": fixed_p2_cagr,
            "equal_weight_10_sharpe": ew10_p2_sharpe,
            "equal_weight_10_cagr": ew10_p2_cagr,
            "diff_wrong_minus_fixed_sharpe": diff_period2_sharpe,
            "wrong_excess_over_ew10": wrong_excess_over_ew10,
            "fixed_excess_over_ew10": fixed_excess_over_ew10,
            "excess_decay": excess_decay,
        },
        "pit_disclaimer": (
            "Kenneth French 10 industries are value-weighted aggregate sector indices, "
            "published as revised historical series, not point-in-time, not tradable."
        ),
    }


def study_multi_seed_distribution() -> dict:
    """Item 9 / C30-09: Run 20 additional seeds to report distribution of differences."""
    seeds = [20261031 + i for i in range(20)]
    la_diffs = []
    surv_diffs = []
    sel_diffs = []
    pm_shrinkages = []

    for s in seeds:
        d = build_constructed_market(seed=s)
        # Lookahead
        la = study_lookahead(d)
        la_diffs.append(la["diff_sharpe"])
        # Survivorship
        su = study_survivorship(d)
        surv_diffs.append(su["diff_sharpe"])
        # Selection
        se = study_selection(d)
        sel_diffs.append(se["diff_sharpe"])
        # Parameter mining
        pm = study_parameter_mining(d)
        pm_shrinkages.append(pm["oos_shrinkage"])

    def summarize(vals):
        arr = np.array(vals)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "fraction_positive": float(np.mean(arr > 0)),
            "values": [float(x) for x in arr],
        }

    return {
        "seeds_tested": seeds,
        "n_seeds": len(seeds),
        "lookahead_diff_sharpe": summarize(la_diffs),
        "survivorship_diff_sharpe": summarize(surv_diffs),
        "selection_diff_sharpe": summarize(sel_diffs),
        "parameter_mining_oos_shrinkage": summarize(pm_shrinkages),
    }


# ------------------------------------------------------------------ figures
def generate_figures(results: dict, fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False

    # Fig 1: Lookahead & Survivorship
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    r_la_f = results["bias_1_lookahead"]["_res_fixed"].ledger
    r_la_w = results["bias_1_lookahead"]["_res_wrong"].ledger
    axes[0].plot(r_la_w.index, r_la_w["nav"] / 1000.0, label="Look-ahead (wrong, retroactive)", color="#d95f02", lw=1.8)
    axes[0].plot(r_la_f.index, r_la_f["nav"] / 1000.0, label="Causal lag=1 (fixed)", color="#1b9e77", lw=1.8)
    axes[0].set_title("Bias 1: Look-ahead vs Fixed Causal Execution", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Date (2024–2025)", fontsize=10)
    axes[0].set_ylabel("NAV (k USD, initial=100)", fontsize=10)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="upper left")

    r_su_f = results["bias_2_survivorship"]["_res_fixed"].ledger
    r_su_w = results["bias_2_survivorship"]["_res_wrong"].ledger
    axes[1].plot(r_su_w.index, r_su_w["nav"] / 1000.0, label="Survivors-only (wrong, drop S35/S36)", color="#d95f02", lw=1.8)
    axes[1].plot(r_su_f.index, r_su_f["nav"] / 1000.0, label="PIT universe (fixed, with delistings)", color="#1b9e77", lw=1.8)
    axes[1].set_title("Bias 2: Survivorship vs PIT Universe with Delisting", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Date (2024–2025)", fontsize=10)
    axes[1].set_ylabel("NAV (k USD, initial=100)", fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="upper left")

    fig.text(0.5, 0.01, "Sample: 36 synthetic assets (522 weekday observations, seed 20261030) | Engine: quant_course.backtest.run_backtest", ha="center", fontsize=9, color="#555555")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(fig_dir / "ch30_lookahead_and_survivorship.png", dpi=200)
    plt.close(fig)

    # Fig 2: Data Snooping & Selection Bias
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    cand_sh = results["bias_4_data_snooping"]["cand_sharpes"]
    axes[0].hist(cand_sh, bins=12, color="#7570b3", edgecolor="black", alpha=0.7, label="50 Candidate Trials")
    axes[0].axvline(results["bias_4_data_snooping"]["max_sharpe"], color="#d95f02", lw=2, linestyle="--", label="Max Candidate")
    axes[0].axvline(results["bias_4_data_snooping"]["median_sharpe"], color="#1b9e77", lw=2, linestyle=":", label="Median Candidate")
    axes[0].set_title("Bias 4: Data Snooping Distribution over 50 Trials", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Annualized Sharpe Ratio", fontsize=10)
    axes[0].set_ylabel("Count of Trials", fontsize=10)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="upper right")

    r_se_f = results["bias_3_selection"]["_res_fixed"].ledger
    r_se_w = results["bias_3_selection"]["_res_wrong"].ledger
    axes[1].plot(r_se_w.index, r_se_w["nav"] / 1000.0, label="Ex-post Top 10 Selected (wrong)", color="#d95f02", lw=1.8)
    axes[1].plot(r_se_f.index, r_se_f["nav"] / 1000.0, label="Dynamic Trailing Selection (fixed)", color="#1b9e77", lw=1.8)
    axes[1].set_title("Bias 3: Ex-post Selection vs Dynamic Trailing Selection", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Date (2024–2025)", fontsize=10)
    axes[1].set_ylabel("NAV (k USD, initial=100)", fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="upper left")

    fig.text(0.5, 0.01, "Sample: 36 synthetic assets (522 weekday observations, seed 20261030) | Engine: quant_course.backtest.run_backtest", ha="center", fontsize=9, color="#555555")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(fig_dir / "ch30_data_snooping_trials.png", dpi=200)
    plt.close(fig)

    # Fig 3: Overfitting & Parameter Mining
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    r_ov_is = results["bias_5_overfitting"]["_res_overfit_is"].ledger
    r_ov_oos = results["bias_5_overfitting"]["_res_overfit_oos"].ledger
    r_sm_is = results["bias_5_overfitting"]["_res_simple_is"].ledger
    r_sm_oos = results["bias_5_overfitting"]["_res_simple_oos"].ledger

    nav_ov = pd.concat([r_ov_is["nav"], r_ov_oos["nav"] * (r_ov_is["nav"].iloc[-1] / 100000.0)])
    nav_sm = pd.concat([r_sm_is["nav"], r_sm_oos["nav"] * (r_sm_is["nav"].iloc[-1] / 100000.0)])
    axes[0].plot(nav_ov.index, nav_ov / 1000.0, label="Overfitted 8-Lag Model", color="#e7298a", lw=1.8)
    axes[0].plot(nav_sm.index, nav_sm / 1000.0, label="Simple 20-Day Momentum", color="#1b9e77", lw=1.8)
    axes[0].axvline(pd.Timestamp("2024-12-31"), color="#666666", linestyle="--", label="IS / OOS Split Date")
    axes[0].set_title("Bias 5: In-Sample Fit vs Out-of-Sample Generalization", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Date (2024 IS | 2025 OOS)", fontsize=10)
    axes[0].set_ylabel("NAV (k USD)", fontsize=10)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="upper left")

    grid_recs = results["bias_7_parameter_mining"]["grid"]
    lbs = [r["lookback"] for r in grid_recs]
    is_shs = [r["is_sharpe"] for r in grid_recs]
    oos_shs = [r["oos_sharpe"] for r in grid_recs]
    axes[1].plot(lbs, is_shs, marker="o", color="#d95f02", lw=1.8, label="In-Sample Sharpe (2024)")
    axes[1].plot(lbs, oos_shs, marker="s", color="#1b9e77", lw=1.8, label="Out-of-Sample Sharpe (2025)")
    axes[1].axhline(results["bias_7_parameter_mining"]["median_oos_sharpe"], color="#7570b3", linestyle=":", label="Median OOS Sharpe")
    axes[1].set_title("Bias 7: Parameter Grid Search (IS Peak vs OOS Shrinkage)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Lookback Parameter L (Trading Days)", fontsize=10)
    axes[1].set_ylabel("Annualized Sharpe Ratio", fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="upper right")

    fig.text(0.5, 0.01, "Sample: 36 synthetic assets (522 weekday observations, seed 20261030) | Engine: quant_course.backtest.run_backtest", ha="center", fontsize=9, color="#555555")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(fig_dir / "ch30_overfitting_and_parameter_mining.png", dpi=200)
    plt.close(fig)

    # Fig 4: Corporate Actions & Cost Sensitivity
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    r_ca_f = results["bias_6_corporate_actions"]["_res_fixed"].ledger
    r_ca_ns = results["bias_6_corporate_actions"]["_res_no_split"].ledger
    r_ca_dd = results["bias_6_corporate_actions"]["_res_double_div"].ledger
    axes[0].plot(r_ca_f.index, r_ca_f["nav"] / 1000.0, label="Proper Ledger (Split & Divs)", color="#1b9e77", lw=1.8)
    axes[0].plot(r_ca_ns.index, r_ca_ns["nav"] / 1000.0, label="Split Ignored (Fake -50% Cliff)", color="#e41a1c", lw=1.8)
    axes[0].plot(r_ca_dd.index, r_ca_dd["nav"] / 1000.0, label="Dividends Double-Counted", color="#377eb8", lw=1.8, linestyle="--")
    axes[0].set_title("Bias 6: Corporate Actions (Splits & Dividends Accounting)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Date (2024–2025)", fontsize=10)
    axes[0].set_ylabel("NAV (k USD, initial=100)", fontsize=10)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="upper left")

    tier_runs = results["bias_8_cost_modeling"]["_tier_runs"]
    colors = ["#1b9e77", "#377eb8", "#7570b3", "#d95f02", "#e41a1c"]
    for (t_name, r_t), col in zip(tier_runs.items(), colors):
        axes[1].plot(r_t.ledger.index, r_t.ledger["nav"] / 1000.0, label=f"Fee: {t_name}", color=col, lw=1.6)
    axes[1].set_title("Bias 8: Transaction Cost Sensitivity (High Turnover)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Date (2024–2025)", fontsize=10)
    axes[1].set_ylabel("NAV (k USD, initial=100)", fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="lower left")

    fig.text(0.5, 0.01, "Sample: 36 synthetic assets (522 weekday observations, seed 20261030) | Engine: quant_course.backtest.run_backtest", ha="center", fontsize=9, color="#555555")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(fig_dir / "ch30_corporate_actions_and_costs.png", dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------ clean & run
def _clean(obj):
    if obj is pd.NaT:
        return None
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return [_clean(v) for v in obj.tolist()]
    if isinstance(obj, (pd.Timestamp, pd.Period)):
        return str(obj)
    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass
    return obj


def run(out_dir: Path, fig_dir: Path) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch30_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 30 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    data = build_constructed_market(seed=SEED)

    s1 = study_lookahead(data)
    s2 = study_survivorship(data)
    s3 = study_selection(data)
    s4 = study_data_snooping(data)
    s5 = study_overfitting(data)
    s6 = study_corporate_actions(data)
    s7 = study_parameter_mining(data)
    s8 = study_cost_modeling(data)
    s_pert = study_future_perturbation(data)
    s_real = study_real_french()
    s_multi_seed = study_multi_seed_distribution()

    all_results = {
        "bias_1_lookahead": s1,
        "bias_2_survivorship": s2,
        "bias_3_selection": s3,
        "bias_4_data_snooping": s4,
        "bias_5_overfitting": s5,
        "bias_6_corporate_actions": s6,
        "bias_7_parameter_mining": s7,
        "bias_8_cost_modeling": s8,
        "future_perturbation_test": s_pert,
        "real_market_french": s_real,
        "multi_seed_distribution": s_multi_seed,
        "seed": SEED,
    }

    # Generate figures
    generate_figures(all_results, fig_dir)

    # Save cleaned JSON
    cleaned = _clean(all_results)
    json_path = out_dir / "ch30_results.json"
    json_path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")

    return cleaned


def main():
    import uuid
    default_run = ROOT / "runs" / ("cli_ch30_backtest_biases_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description="Chapter 30 Backtest Biases CLI")
    parser.add_argument("--out", type=Path, default=default_run / "results",
                        help="Output directory for results JSON")
    parser.add_argument("--figures", type=Path, default=default_run / "figures",
                        help="Output directory for figures")
    parser.add_argument("--overwrite", action="store_true",
                        help="Allow overwriting existing result files")
    args = parser.parse_args()

    targets = [args.out / "ch30_results.json", *[args.figures / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        if not args.overwrite:
            raise FileExistsError(
                f"Targets exist in {args.out} or {args.figures}; rerun with --overwrite or specify new dirs."
            )
        for t in targets:
            if t.exists():
                t.unlink()

    print(f"[ch30] Building constructed market and running studies (seed={SEED})...")
    res = run(args.out, args.figures)
    print(f"[ch30] Done! Results saved to {args.out / 'ch30_results.json'}")
    print(f"[ch30] Generated {len(FIGURES)} figures in {args.figures}")


if __name__ == "__main__":
    main()
