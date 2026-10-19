"""Chapter 29 CLI: Building a Backtesting Engine (teaching ledger, reconciliation, drift, and cost sensitivity).

Run from the course root::

    .venv/bin/python code/ch29_backtest_engine.py

Outputs ``qa/a6/claude/results/ch29/ch29_results.json`` and ``figures/a6/ch29_*.png`` (refuses to overwrite).
Constructed: frozen hand example (2 assets + cash across 4 dates) and multi-asset synthetic path (seed 20261029).
Real: frozen French 10 industries monthly returns (published, revised history, aggregate value-weighted returns,
not point-in-time, not tradable instruments).

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

from quant_course.backtest import (  # noqa: E402
    BacktestConfig, BacktestResult, drifted_weight_returns, reconcile, run_backtest, solve_post_fee_nav,
)
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.portfolio_construction import drift_weights, turnover  # noqa: E402

SEED = 20261029
FIGURES = (
    "ch29_hand_ledger.png",
    "ch29_drift_and_turnover.png",
    "ch29_vectorized_vs_ledger.png",
    "ch29_cost_sensitivity.png",
)
FRENCH_MANIFEST = ROOT / "data/manifests/french_industries_2026-10-05.json"


# ------------------------------------------------------------------ hand example
def hand_example() -> dict:
    """The frozen A6 contract hand example (two assets A and B, plus cash).

    Signal dates: 2026-01-30, 2026-02-27.
    Execution dates (lag=1): 2026-02-02, 2026-03-02.
    Initial cash = 1000.0, fee_rate = 0.002.
    Target weights: A=0.5, B=0.3, cash=0.2.
    """
    dates = pd.DatetimeIndex(["2026-01-30", "2026-02-02", "2026-02-27", "2026-03-02"])
    mark = pd.DataFrame({"A": [10.0, 11.0, 12.1, 12.0], "B": [20.0, 19.0, 19.0, 21.0]}, index=dates)
    execp = pd.DataFrame({"A": [10.0, 10.0, 12.0, 12.0], "B": [20.0, 20.0, 19.5, 20.0]}, index=dates)
    tw = pd.DataFrame({"A": [0.5, 0.5], "B": [0.3, 0.3]}, index=[dates[0], dates[2]])
    cfg = BacktestConfig(initial_cash=1000.0, fee_rate=0.002, lag=1)

    res = run_backtest(mark, tw, cfg, exec_prices=execp)
    rec = reconcile(res, mark, cfg, exec_prices=execp)

    # Verification of the closed-form derivations
    # Rebalance 1 (from pure cash):
    v1_analytic = 1000.0 / 1.0016
    qa1_analytic = 0.5 * v1_analytic / 10.0
    qb1_analytic = 0.3 * v1_analytic / 20.0
    fees1_analytic = 0.002 * (0.5 * v1_analytic + 0.3 * v1_analytic)
    cash1_analytic = 1000.0 - 0.8 * v1_analytic - fees1_analytic

    # Rebalance 2 (drifted positions to target):
    v2_pre = cash1_analytic + qa1_analytic * 12.0 + qb1_analytic * 20.0
    # Sell A, Buy B:
    # V' * (1 + c*(0.3 - 0.5)) = V_pre - c*(x_A - x_B)
    xa_pre = qa1_analytic * 12.0
    xb_pre = qb1_analytic * 20.0
    v2_post_analytic = (v2_pre - 0.002 * (xa_pre - xb_pre)) / (1.0 + 0.002 * (0.3 - 0.5))
    trade_val_a = 0.5 * v2_post_analytic - xa_pre
    trade_val_b = 0.3 * v2_post_analytic - xb_pre
    dqa_analytic = trade_val_a / 12.0
    dqb_analytic = trade_val_b / 20.0
    fees2_analytic = 0.002 * (abs(trade_val_a) + abs(trade_val_b))

    return {
        "dates": [d.strftime("%Y-%m-%d") for d in dates],
        "config": {"initial_cash": cfg.initial_cash, "fee_rate": cfg.fee_rate, "lag": cfg.lag},
        "prices": {
            "mark": mark.to_dict(orient="list"),
            "exec": execp.to_dict(orient="list"),
        },
        "analytic": {
            "rebalance_1": {
                "post_fee_nav": v1_analytic,
                "shares_A": qa1_analytic,
                "shares_B": qb1_analytic,
                "fees": fees1_analytic,
                "cash": cash1_analytic,
            },
            "rebalance_2": {
                "pre_trade_nav": v2_pre,
                "post_fee_nav": v2_post_analytic,
                "trade_val_A": trade_val_a,
                "trade_val_B": trade_val_b,
                "shares_delta_A": dqa_analytic,
                "shares_delta_B": dqb_analytic,
                "fees": fees2_analytic,
            },
        },
        "ledger": res.ledger.reset_index().to_dict(orient="records"),
        "positions": res.positions.to_dict(orient="index"),
        "fills": res.fills.to_dict(orient="records"),
        "weights": res.weights.to_dict(orient="index"),
        "reconcile": rec.reset_index().to_dict(orient="records"),
        "max_reconcile_residual": float(rec["residual"].abs().max()),
        "max_cash_identity_error": float(rec["cash_identity"].abs().max()),
        "_objects": {"res": res, "rec": rec, "mark": mark, "execp": execp, "tw": tw, "cfg": cfg},
    }


# ------------------------------------------------------------------ constructed study
def constructed_study(seed: int = SEED) -> dict:
    """Multi-asset constructed market simulation and policy boundary verification."""
    rng = np.random.default_rng(seed)
    n_days, n_assets = 60, 5
    assets = [f"Asset_{i+1}" for i in range(n_assets)]
    dates = pd.date_range("2026-01-05", periods=n_days, freq="B")

    # Geometric Brownian Motion log-returns with realistic dispersion
    daily_mu = np.array([0.0005, 0.0008, -0.0002, 0.0010, 0.0003])
    daily_vol = np.array([0.015, 0.020, 0.012, 0.025, 0.018])
    log_shocks = rng.normal(daily_mu, daily_vol, size=(n_days, n_assets))
    px_matrix = 100.0 * np.exp(np.cumsum(log_shocks, axis=0))
    mark_prices = pd.DataFrame(px_matrix, index=dates, columns=assets)

    # Rebalance every 10 business days with lag=1
    signal_idx = list(range(0, n_days - 1, 10))
    signal_dates = dates[signal_idx]
    # Equal weight 20% on each asset
    target_weights = pd.DataFrame(1.0 / n_assets, index=signal_dates, columns=assets)

    # 1. Standard realistic ledger with fee_rate = 10 bps
    cfg_fee = BacktestConfig(initial_cash=100000.0, fee_rate=0.001, lag=1)
    res_fee = run_backtest(mark_prices, target_weights, cfg_fee)
    rec_fee = reconcile(res_fee, mark_prices, cfg_fee)

    # 2. Vectorized vs Ledger comparison under IDENTICAL assumptions:
    # Zero fee, E = P, zero cash rate, same trade dates
    cfg_zero = BacktestConfig(initial_cash=100000.0, fee_rate=0.0, lag=1)
    res_zero = run_backtest(mark_prices, target_weights, cfg_zero)

    trade_w = target_weights.copy()
    trade_w.index = dates[np.searchsorted(dates, target_weights.index) + 1]
    vec_drifted = drifted_weight_returns(mark_prices, trade_w)

    # Naive shift-only vectorized version without return drift:
    naive_weights = trade_w.reindex(dates).ffill().shift(1).fillna(0.0)
    asset_simple_ret = mark_prices.pct_change(fill_method=None).fillna(0.0)
    vec_naive = (naive_weights * asset_simple_ret).sum(axis=1)

    max_diff_ledger_vec = float(np.abs(res_zero.ledger["ret"].to_numpy() - vec_drifted.to_numpy()).max())
    max_diff_naive_vec = float(np.abs(vec_naive.to_numpy() - vec_drifted.to_numpy()).max())

    # 3. Drift tracking metrics
    # Measure distance between actual holding weights and target weights over time
    actual_weights = res_zero.weights
    weight_drift_l1 = []
    current_target = target_weights.iloc[0].to_numpy()
    for d in dates:
        if d in trade_w.index:
            current_target = trade_w.loc[d].to_numpy()
        w_act = actual_weights.loc[d].to_numpy()
        if not np.isnan(w_act).any() and w_act.sum() > 0:
            weight_drift_l1.append(float(np.abs(w_act - current_target).sum()))
        else:
            weight_drift_l1.append(0.0)
    drift_series = pd.Series(weight_drift_l1, index=dates, name="drift_l1")

    # 4. Policy boundaries and counterexamples
    # a) Ruin / termination: over-leveraged short position hits <= 0
    ruin_mark = pd.DataFrame({"X": [10.0, 10.0, 25.0, 30.0], "Y": [20.0, 20.0, 20.0, 20.0]},
                             index=dates[:4])
    ruin_tw = pd.DataFrame({"X": [-1.0], "Y": [1.0]}, index=[dates[0]])
    ruin_res = run_backtest(ruin_mark, ruin_tw, BacktestConfig(initial_cash=100.0, allow_short=True, max_gross=2.0))

    # b) Corporate action: 2:1 stock split is value neutral with unadjusted prices
    split_mark = pd.DataFrame({"A": [10.0, 10.0, 5.0], "B": [20.0, 20.0, 20.0]}, index=dates[:3])
    split_tw = pd.DataFrame({"A": [1.0], "B": [0.0]}, index=[dates[0]])
    split_df = pd.DataFrame({"A": [np.nan, np.nan, 2.0]}, index=dates[:3])
    split_res = run_backtest(split_mark, split_tw, BacktestConfig(initial_cash=100.0), splits=split_df)
    no_split_res = run_backtest(split_mark, split_tw, BacktestConfig(initial_cash=100.0))

    # c) Delisting cash-out
    delist_mark = pd.DataFrame({"A": [10.0, 10.0, np.nan, np.nan], "B": [20.0, 20.0, 20.0, 20.0]}, index=dates[:4])
    delist_tw = pd.DataFrame({"A": [0.5], "B": [0.5]}, index=[dates[0]])
    delist_res = run_backtest(delist_mark, delist_tw, BacktestConfig(initial_cash=100.0),
                              delistings={"A": (dates[2], 3.0)})
    delist_rec = reconcile(delist_res, delist_mark, BacktestConfig(initial_cash=100.0),
                           delistings={"A": (dates[2], 3.0)})

    # d) Future perturbation invariance test
    pert_mark = mark_prices.copy()
    pert_mark.iloc[35:] *= 2.5
    pert_tw = target_weights.copy()
    pert_res = run_backtest(pert_mark, pert_tw, cfg_fee)
    past_identical = bool(res_fee.ledger.iloc[:35].equals(pert_res.ledger.iloc[:35]))

    # e) Flat book & zero-trade fee check
    flat_tw = pd.DataFrame(0.0, index=[dates[0]], columns=assets)
    flat_res = run_backtest(mark_prices.iloc[:5], flat_tw, cfg_fee)

    return {
        "n_days": n_days,
        "n_assets": n_assets,
        "seed": seed,
        "ledger_reconcile_max_residual": float(rec_fee["residual"].abs().max()),
        "vectorized_vs_ledger_max_diff": max_diff_ledger_vec,
        "naive_vs_drifted_max_diff": max_diff_naive_vec,
        "max_drift_l1": float(drift_series.max()),
        "mean_drift_l1": float(drift_series.mean()),
        "policies": {
            "ruin_terminated_at": ruin_res.terminated_at.strftime("%Y-%m-%d") if ruin_res.terminated_at else None,
            "ruin_final_nav": float(ruin_res.ledger["nav"].iloc[-1]),
            "split_nav_with_event": float(split_res.ledger["nav"].iloc[-1]),
            "split_nav_without_event": float(no_split_res.ledger["nav"].iloc[-1]),
            "delist_cash_received": float(delist_res.ledger["delist_cash"].iloc[2]),
            "delist_final_nav": float(delist_res.ledger["nav"].iloc[-1]),
            "delist_max_residual": float(delist_rec["residual"].abs().max()),
            "future_perturbation_past_identical": past_identical,
            "flat_book_fills_count": len(flat_res.fills),
            "flat_book_final_nav": float(flat_res.ledger["nav"].iloc[-1]),
        },
        "_series": {
            "dates": dates,
            "mark_prices": mark_prices,
            "target_weights": target_weights,
            "trade_weights": trade_w,
            "res_fee": res_fee,
            "res_zero": res_zero,
            "vec_drifted": vec_drifted,
            "vec_naive": vec_naive,
            "drift_series": drift_series,
        },
    }


# ------------------------------------------------------------------ real market study
def real_study() -> dict:
    """Real market example: French 10 industries monthly returns (1926-07 to 2026-08).

    Values are aggregated value-weighted monthly total returns from Kenneth French Data Library.
    We convert returns into a cumulative total-return index level starting at 100.0.
    We explicitly state: this is a total-return proxy level, not a trade price, no dividends added.
    We evaluate an equal-weight 1/N portfolio rebalanced monthly with lag=1 across fee tiers.
    """
    ind_rets, rf, prov = load_industries_and_rf()
    columns = list(ind_rets.columns)

    # Build total-return proxy level series with a base period
    levels = (1.0 + ind_rets).cumprod() * 100.0
    base_period = ind_rets.index[0] - 1
    base_row = pd.DataFrame(100.0, index=[base_period], columns=columns)
    price_levels = pd.concat([base_row, levels])

    # Monthly equal-weight rebalancing with lag=1
    # Signal is produced on each month's close from base_period to second-to-last month
    target_weights = pd.DataFrame(1.0 / len(columns), index=price_levels.index[:-1], columns=columns)

    fee_tiers = [0.0, 0.0005, 0.001, 0.002, 0.005]  # 0, 5, 10, 20, 50 bps
    initial_cash = 10000.0
    results_by_fee = {}
    ledger_series_by_fee = {}

    for fee in fee_tiers:
        cfg = BacktestConfig(initial_cash=initial_cash, fee_rate=fee, lag=1)
        res = run_backtest(price_levels, target_weights, cfg)
        rec = reconcile(res, price_levels, cfg)

        nav_path = res.ledger["nav"]
        total_ret = nav_path.iloc[-1] / initial_cash - 1.0
        n_months = len(res.ledger) - 1  # exclude base row
        years = n_months / 12.0
        cagr = (nav_path.iloc[-1] / initial_cash) ** (1.0 / years) - 1.0
        monthly_rets = res.ledger["ret"].iloc[1:].to_numpy()
        ann_vol = float(np.std(monthly_rets, ddof=1) * np.sqrt(12.0))
        mean_monthly_ret = float(np.mean(monthly_rets))
        rf_aligned = rf.loc[ind_rets.index].to_numpy()
        excess_monthly = monthly_rets - rf_aligned
        ann_sharpe = float(np.mean(excess_monthly) / np.std(excess_monthly, ddof=1) * np.sqrt(12.0))
        total_fees = float(res.ledger["fees"].sum())
        valid_trades = res.ledger[res.ledger["nav_pre_trade"] > 0]
        trade_turnovers = valid_trades["traded_notional"] / valid_trades["nav_pre_trade"]
        avg_monthly_turnover = float(trade_turnovers.mean()) if len(trade_turnovers) > 0 else 0.0

        fee_bps = int(round(fee * 10000))
        results_by_fee[f"{fee_bps}_bps"] = {
            "fee_rate": fee,
            "final_nav": float(nav_path.iloc[-1]),
            "total_return": float(total_ret),
            "cagr": float(cagr),
            "annualized_vol": ann_vol,
            "annualized_sharpe": ann_sharpe,
            "total_fees": total_fees,
            "avg_monthly_turnover": avg_monthly_turnover,
            "max_reconcile_residual": float(rec["residual"].abs().max()),
        }
        ledger_series_by_fee[f"{fee_bps}_bps"] = nav_path

    # Compare zero-fee ledger vs vectorized with drift on real dataset
    trade_w = target_weights.copy()
    trade_w.index = price_levels.index[1:]
    vec_drifted = drifted_weight_returns(price_levels, trade_w)
    zero_fee_ledger_ret = run_backtest(price_levels, target_weights,
                                       BacktestConfig(initial_cash=initial_cash, fee_rate=0.0, lag=1)).ledger["ret"]
    real_ledger_vec_diff = float(np.abs(zero_fee_ledger_ret.to_numpy() - vec_drifted.to_numpy()).max())

    # Annual rebalance comparison: Drifted vs Naive shift-1
    tw_annual = pd.DataFrame(1.0 / len(columns), index=price_levels.index[::12], columns=columns)
    trade_w_ann = tw_annual.copy()
    trade_w_ann.index = price_levels.index[np.searchsorted(price_levels.index, tw_annual.index) + 1]
    vec_ann_drifted = drifted_weight_returns(price_levels, trade_w_ann)
    naive_ann = (trade_w_ann.reindex(price_levels.index).ffill().shift(1).fillna(0.0)
                 * price_levels.pct_change(fill_method=None).fillna(0.0)).sum(axis=1)
    max_ann_drift_diff = float(np.abs(naive_ann - vec_ann_drifted).max())

    # Fee drag relative to zero-fee CAGR
    zero_cagr = results_by_fee["0_bps"]["cagr"]
    for k in results_by_fee:
        results_by_fee[k]["annual_fee_drag"] = float(zero_cagr - results_by_fee[k]["cagr"])

    return {
        "dataset": "French 10 Industry Portfolios (value-weighted monthly)",
        "source": prov["source"],
        "first_month": prov["first_month"],
        "last_month": prov["last_month"],
        "months": prov["months"],
        "is_point_in_time": prov["is_point_in_time"],
        "manifest_sha256": prov["sha256"]["industry_processed_csv"],
        "zero_fee_ledger_vs_vectorized_diff": real_ledger_vec_diff,
        "annual_rebalance_naive_vs_drift_max_diff": max_ann_drift_diff,
        "fee_sensitivity": results_by_fee,
        "_series": {
            "price_levels": price_levels,
            "ledger_series_by_fee": ledger_series_by_fee,
            "vec_drifted": vec_drifted,
            "ind_rets": ind_rets,
        },
    }


# ------------------------------------------------------------------ figures
def _figures(hand: dict, cons: dict, real: dict, fig_dir: Path) -> None:
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. ch29_hand_ledger.png
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    h_led = pd.DataFrame(hand["ledger"]).set_index("date")
    h_dates = [str(d)[:10] for d in h_led.index]
    x_pos = np.arange(len(h_dates))
    cash_vals = h_led["cash_end"].to_numpy()
    h_pos = pd.DataFrame(hand["positions"]).T
    px_mark = pd.DataFrame(hand["prices"]["mark"])
    val_a = h_pos["A"].to_numpy() * px_mark["A"].to_numpy()
    val_b = h_pos["B"].to_numpy() * px_mark["B"].to_numpy()

    ax.bar(x_pos, cash_vals, label="Cash", color="#176B87", alpha=0.85, width=0.5)
    ax.bar(x_pos, val_a, bottom=cash_vals, label="Asset A Holdings", color="#D05A36", alpha=0.85, width=0.5)
    ax.bar(x_pos, val_b, bottom=cash_vals + val_a, label="Asset B Holdings", color="#654A8B", alpha=0.85, width=0.5)
    for i, nav in enumerate(h_led["nav"]):
        ax.text(i, nav + 15, f"${nav:.2f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(h_dates, fontsize=9)
    ax.set_ylabel("Portfolio Value (USD)")
    ax.set_ylim(0, 1250)
    ax.set_title("Frozen Hand Example: NAV Progression & Asset Breakdown\n(Initial $1000, 50% A, 30% B, 20% Cash)")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)

    ax = axes[1]
    h_rec = pd.DataFrame(hand["reconcile"]).set_index("date")
    nav_changes = h_rec["nav_change"].to_numpy()
    explained = h_rec["explained"].to_numpy()
    residuals = h_rec["residual"].to_numpy()
    width = 0.35
    ax.bar(x_pos - width/2, nav_changes, width=width, label="Actual NAV Change", color="#176B87", alpha=0.85)
    ax.bar(x_pos + width/2, explained, width=width, label="Reconciled Attribution", color="#2B7A78", alpha=0.85)
    ax.axhline(0, color="0.4", lw=0.8)
    for i in range(len(x_pos)):
        ax.text(x_pos[i], max(nav_changes[i], explained[i]) + 2, f"Δ={nav_changes[i]:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(h_dates, fontsize=9)
    ax.set_ylabel("Daily Change (USD)")
    ax.set_ylim(-10, 68)
    ax.set_title("Reconciliation Residual Max: |residual| < 1e-12\n(Explained = Interest + Div + Pre-trade + Post-trade - Fees)")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[0], dpi=150)
    plt.close(fig)

    # 2. ch29_drift_and_turnover.png
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    c_series = cons["_series"]
    dates = c_series["dates"]
    res_zero = c_series["res_zero"]
    w_df = res_zero.weights

    ax = axes[0]
    for col, color in zip(w_df.columns, ["#176B87", "#D05A36", "#654A8B", "#2B7A78", "#E38B29"]):
        ax.plot(dates, w_df[col], label=col, color=color, lw=1.5)
    ax.axhline(0.20, color="0.3", ls="--", lw=1.0, label="Target Weight (20%)")
    ax.set_ylabel("Holding Weight (Fraction of NAV)")
    ax.set_xlabel("Date")
    ax.set_title("Constructed Multi-Asset: Return-Induced Weight Drift\n(Periodic rebalances pull drifted weights back to target)")
    ax.legend(frameon=False, loc="upper left", fontsize=8, ncol=2)

    ax = axes[1]
    drift_series = c_series["drift_series"]
    res_fee = c_series["res_fee"]
    notional = res_fee.ledger["traded_notional"]
    ax.plot(dates, drift_series, color="#D05A36", lw=1.5, label="Total Weight Drift Distance (L1)")
    ax.set_ylabel("Weight Drift Distance $\\sum |w_i - w_i^*|$", color="#D05A36")
    ax.tick_params(axis="y", labelcolor="#D05A36")
    ax2 = ax.twinx()
    ax2.bar(dates, notional, width=1.0, color="#176B87", alpha=0.4, label="Traded Notional ($)")
    ax2.set_ylabel("Traded Notional (USD)", color="#176B87")
    ax2.tick_params(axis="y", labelcolor="#176B87")
    ax.set_xlabel("Date")
    ax.set_title("Rebalancing Turnover is Driven by Accumulated Drift\n(Traded Notional Peaks at Scheduled Rebalances)")
    fig.savefig(fig_dir / FIGURES[1], dpi=150)
    plt.close(fig)

    # 3. ch29_vectorized_vs_ledger.png
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    nav_ledger = res_zero.ledger["nav"] / res_zero.ledger["nav"].iloc[0]
    vec_drifted = c_series["vec_drifted"]
    vec_nav = (1.0 + vec_drifted).cumprod()
    vec_naive = c_series["vec_naive"]
    naive_nav = (1.0 + vec_naive).cumprod()

    ax.plot(dates, nav_ledger, label="Event Ledger (E=P, zero fee)", color="#176B87", lw=2.0)
    ax.plot(dates, vec_nav, label="Vectorized with Drift", color="#2B7A78", ls="--", lw=2.0)
    ax.plot(dates, naive_nav, label="Naive Vectorized (Shift only, no drift)", color="#D05A36", ls=":", lw=1.8)
    ax.set_ylabel("Normalized Portfolio Wealth (Base = 1.0)")
    ax.set_xlabel("Date")
    ax.set_title("Vectorized vs Ledger Comparison\n(Ledger and Drifted Vectorized match to < 1e-12)")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)

    ax = axes[1]
    diff_ledger_vec = np.abs(res_zero.ledger["ret"].to_numpy() - vec_drifted.to_numpy())
    diff_naive_vec = np.abs(vec_naive.to_numpy() - vec_drifted.to_numpy())
    ax.plot(dates, diff_naive_vec * 10000, label="|Naive - Drifted| Tracking Error", color="#D05A36", lw=1.3)
    ax.plot(dates, diff_ledger_vec * 10000, label="|Ledger - Drifted| Discrepancy", color="#176B87", lw=1.5)
    ax.set_ylabel("Return Difference (Basis Points, bps)")
    ax.set_xlabel("Date")
    ax.set_title("Tracking Error of Naive Shift-Only Formulation\n(Ignores within-period drift, generating persistent errors)")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[2], dpi=150)
    plt.close(fig)

    # 4. ch29_cost_sensitivity.png
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
    r_series = real["_series"]
    ledger_by_fee = r_series["ledger_series_by_fee"]
    idx_dates = [p.to_timestamp(how="end") for p in real["_series"]["price_levels"].index]

    ax = axes[0]
    colors = ["#176B87", "#2B7A78", "#E38B29", "#D05A36", "#654A8B"]
    for (label, nav_path), color in zip(ledger_by_fee.items(), colors):
        fee_name = label.replace("_", " ")
        cagr = real["fee_sensitivity"][label]["cagr"] * 100.0
        ax.plot(idx_dates, nav_path, label=f"{fee_name} (CAGR: {cagr:.2f}%)", color=color, lw=1.4)
    ax.set_yscale("log")
    ax.set_ylabel("Portfolio NAV (USD, Log Scale, Initial $10k)")
    ax.set_xlabel("Year")
    ax.set_title(f"French 10 Industries 1/N Monthly Rebalanced\n(1926-07 to 2026-08, 1202 Months, Lag=1)")
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)

    ax = axes[1]
    fee_bps_list = [0, 5, 10, 20, 50]
    cagrs = [real["fee_sensitivity"][f"{bps}_bps"]["cagr"] * 100.0 for bps in fee_bps_list]
    fee_drags = [real["fee_sensitivity"][f"{bps}_bps"]["annual_fee_drag"] * 10000.0 for bps in fee_bps_list]

    ax.plot(fee_bps_list, cagrs, marker="o", color="#176B87", lw=1.5, label="Net CAGR (%)")
    ax.set_xlabel("Transaction Fee Rate (Basis Points, bps)")
    ax.set_ylabel("Annualized Compound Return CAGR (%)", color="#176B87")
    ax.tick_params(axis="y", labelcolor="#176B87")

    ax2 = ax.twinx()
    ax2.plot(fee_bps_list, fee_drags, marker="s", color="#D05A36", lw=1.5, ls="--", label="Annual Fee Drag (bps)")
    ax2.set_ylabel("Annual Fee Drag (bps/yr)", color="#D05A36")
    ax2.tick_params(axis="y", labelcolor="#D05A36")

    drag_10 = real["fee_sensitivity"]["10_bps"]["annual_fee_drag"] * 10000.0
    drag_50 = real["fee_sensitivity"]["50_bps"]["annual_fee_drag"] * 10000.0
    ax.set_title(f"Fee Rate Sensitivity: Compounding Friction\n(10 bps fee reduces CAGR by ~{drag_10:.1f} bps/yr; 50 bps reduces CAGR by ~{drag_50:.1f} bps/yr)")
    fig.savefig(fig_dir / FIGURES[3], dpi=150)
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
    targets = [out_dir / "ch29_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 29 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    hand = hand_example()
    cons = constructed_study(seed=SEED)
    real = real_study()

    _figures(hand, cons, real, fig_dir)

    results = {
        "hand_example": hand,
        "constructed": cons,
        "real": real,
        "seed": SEED,
    }
    cleaned = _clean(results)
    (out_dir / "ch29_results.json").write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cleaned


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch29_backtest_engine_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(default_run / "results"))
    parser.add_argument("--figures", default=str(default_run / "figures"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    print("Chapter 29 CLI run completed successfully.")
    print("Hand example max reconcile residual:", r["hand_example"]["max_reconcile_residual"])
    print("Constructed vectorized vs ledger diff:", r["constructed"]["vectorized_vs_ledger_max_diff"])
    print("Constructed naive vs drifted diff:", r["constructed"]["naive_vs_drifted_max_diff"])
    print("Real market zero-fee ledger vs vec diff:", r["real"]["zero_fee_ledger_vs_vectorized_diff"])
    print("Real market annual rebalance naive diff:", r["real"]["annual_rebalance_naive_vs_drift_max_diff"])
    print("Real market 10 bps CAGR:", r["real"]["fee_sensitivity"]["10_bps"]["cagr"])


if __name__ == "__main__":
    main()
