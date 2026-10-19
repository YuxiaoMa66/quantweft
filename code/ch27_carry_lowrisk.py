"""Chapter 27 CLI: carry arithmetic (FX forward, bond roll-down, commodity curve), tradable vs spliced futures returns,
a constructed carry-crash world, and betting-against-beta on the frozen French 10 industries.

Run from the course root::

    .venv/bin/python code/ch27_carry_lowrisk.py

Outputs ``qa/a5/claude/results/ch27/ch27_results.json`` and ``figures/a5/ch27_*.png`` (refuses to overwrite).
Real data: the hash-checked frozen French 10-industry monthly returns and FF3 market/RF (revised history, ten value-weight
industry portfolios, not tradable fills, not individual stocks). Hand examples, the FX carry world (seed 20261114) and
the commodity curve world (seed 20261115) are constructed teaching examples with a known data-generating process.

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

from quant_course.carry import (  # noqa: E402
    commodity_curve_carry, forward_premium, fx_carry_from_rates, futures_carry, held_contract_returns,
    naive_splice_returns, portfolio_carry, roll_down_approximation, zero_coupon_carry,
)
from quant_course.factor_research import newey_west_variance_of_mean, quantile_long_short_weights  # noqa: E402
from quant_course.french_frozen import load_industries_and_rf  # noqa: E402
from quant_course.low_risk import bab_returns, bab_weights, rolling_beta, state_beta, vasicek_shrink  # noqa: E402
from quant_course.momentum import strategy_returns  # noqa: E402

SEED_FX = 20261114
SEED_COMMODITY = 20261115
JUMP_BASE, JUMP_SD = 0.05, 0.02       # squeeze size m = 0.05 + |N(0, 0.02^2)|, so E[m] = 0.05 + 0.02 sqrt(2/pi)
FIGURES = ("ch27_fx_carry_crash.png", "ch27_roll_splice.png", "ch27_industry_sml.png", "ch27_bab_months.png")
FF3_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"
SPLITS = (("1926-07..1963-06", "1926-07", "1963-06"), ("1963-07..1999-12", "1963-07", "1999-12"), ("2000-01..end", "2000-01", "2100-12"))


# ------------------------------------------------------------------ hand examples
def hand_examples() -> dict:
    out: dict = {}
    # 8.1 FX: quote = local currency per unit of foreign currency; one-year simple rates
    s0, r_loc, r_for = 100.0, 0.02, 0.06
    f = s0 * (1 + r_loc) / (1 + r_for)
    carry = futures_carry(s0, f)
    s_t = 96.0
    out["fx"] = {"forward": f, "carry_from_prices": carry, "carry_from_rates": fx_carry_from_rates(r_loc, r_for),
                 "forward_premium": forward_premium(s0, f), "breakeven_spot": f, "breakeven_move": f / s0 - 1,
                 "forward_return_if_spot_96": (s_t - f) / f,
                 "deposit_excess_if_spot_96": (s_t / s0 * (1 + r_for) - (1 + r_loc)) / (1 + r_loc),
                 "wrong_quote_sign": futures_carry(1 / s0, 1 / f)}
    # 8.2 zero-coupon roll-down
    m, y = [1.0, 2.0, 3.0, 5.0], [0.02, 0.03, 0.035, 0.04]
    z = zero_coupon_carry(m, y, 3.0, 1.0, financing_rate=0.02)
    z["duration_approximation"] = roll_down_approximation(2 / 1.03, 0.035, 0.03)
    z["flat_curve_total"] = zero_coupon_carry([1.0, 5.0], [0.035, 0.035], 3.0, 1.0)["total"]
    out["bond"] = z
    # 8.3 commodity curve
    out["commodity"] = {"contango_carry_per_month": commodity_curve_carry(100.0, 101.0, 1.0, 2.0),
                        "backwardation_carry_per_month": commodity_curve_carry(100.0, 98.0, 1.0, 2.0)}
    # 8.4 roll splice, spot flat at 100, contango of 1 per month
    dates = pd.period_range("2026-01", periods=4, freq="M")
    prices = pd.DataFrame({"A": [102.0, 101.0, 100.0, np.nan], "B": [np.nan, np.nan, 103.0, 102.0]}, index=dates)
    front = pd.Series(["A", "A", "B", "B"], index=dates)
    held = pd.Series(["A", "A", "B", "B"], index=dates)
    trad = held_contract_returns(prices, held)
    naive = naive_splice_returns(prices, front)
    out["splice"] = {"tradable": trad.dropna().tolist(), "naive": naive.dropna().tolist(),
                     "tradable_cumulative": float((1 + trad.dropna()).prod() - 1), "naive_cumulative": float((1 + naive.dropna()).prod() - 1)}
    # 8.5 BAB with four assets
    beta = pd.Series([0.6, 0.9, 1.1, 1.4], index=list("ABCD"))
    wl, wh = bab_weights(beta)
    r = pd.Series([0.012, 0.015, 0.010, 0.020], index=beta.index)
    bl, bh = float(wl @ beta), float(wh @ beta)
    rl, rh = float(wl @ r), float(wh @ r)
    idx = pd.period_range("2026-01", periods=2, freq="M")
    two = bab_returns(pd.DataFrame([r.to_numpy(), r.to_numpy()], index=idx, columns=beta.index),
                      pd.DataFrame([beta.to_numpy(), beta.to_numpy()], index=idx, columns=beta.index), borrow_spread=0.002)
    pure = bab_returns(pd.DataFrame([r.to_numpy(), r.to_numpy()], index=idx, columns=beta.index),
                       pd.DataFrame([beta.to_numpy(), beta.to_numpy()], index=idx, columns=beta.index))
    mkt = 0.01
    neutral = bab_returns(pd.DataFrame([beta.to_numpy() * mkt] * 2, index=idx, columns=beta.index),
                          pd.DataFrame([beta.to_numpy(), beta.to_numpy()], index=idx, columns=beta.index))
    out["bab"] = {"w_low": wl.tolist(), "w_high": wh.tolist(), "beta_low": bl, "beta_high": bh, "leverage_long": 1 / bl, "leverage_short": 1 / bh,
                  "r_low": rl, "r_high": rh, "bab": rl / bl - rh / bh, "bab_function": float(pure["bab"].iloc[0]),
                  "bab_with_spread_0p2pct": float(two["bab"].iloc[0]), "beta_neutral_check": float(neutral["bab"].iloc[0]),
                  "shrunk_0p5": float(vasicek_shrink(0.5)), "shrunk_1p8": float(vasicek_shrink(1.8))}
    # 8.6 portfolio carry (eq. 24-25)
    c = pd.Series([0.004, 0.002, -0.001, -0.003], index=list("ABCD"))
    w = pd.Series([0.5, 0.5, -0.5, -0.5], index=c.index)
    out["portfolio_carry"] = {"long_short": portfolio_carry(w, c), "mean_top_minus_bottom": (0.004 + 0.002) / 2 - (-0.001 - 0.003) / 2}
    return out


# ------------------------------------------------------------------ constructed worlds
def fx_world(seed: int = SEED_FX, n: int = 10, months: int = 360, gamma: float = 0.5, crash_prob: float = 0.012) -> dict:
    """Ten currencies, monthly. Row t: carry c_t known at the end of month t; the forward return of month t+1 is
    r = (1 - gamma) c_t + common + idio - loading_t * size * jump, where loading = 2 * percentile(c_t) - 1 (high-carry
    currencies fall, funding currencies rise when a global squeeze hits)."""
    rng = np.random.default_rng(seed)
    level = rng.normal(0.0, 0.0020, n)
    x = np.zeros((months, n))
    x[0] = rng.normal(0.0, 0.0004 / np.sqrt(1 - 0.95 ** 2), n)
    for t in range(1, months):
        x[t] = 0.95 * x[t - 1] + rng.normal(0.0, 0.0004, n)
    carry = level + x
    common = rng.normal(0.0, 0.012, months)
    idio = rng.normal(0.0, 0.02, (months, n))
    jump = rng.random(months) < crash_prob
    size = JUMP_BASE + np.abs(rng.normal(0.0, JUMP_SD, months))
    pct = (stats.rankdata(carry, axis=1) - 1) / (n - 1)
    loading = 2 * pct - 1
    nxt = (1 - gamma) * carry + common[:, None] + idio - loading * (size * jump)[:, None]
    index = pd.period_range("1996-01", periods=months, freq="M")
    cols = [f"C{i + 1:02d}" for i in range(n)]
    carry_df = pd.DataFrame(carry, index=index, columns=cols)
    ret = pd.DataFrame(np.vstack([np.full((1, n), np.nan), nxt[:-1]]), index=index, columns=cols)   # row m = return during month m
    return {"carry": carry_df, "returns": ret, "jump_rows": pd.Series(jump, index=index), "gamma": gamma, "crash_prob": crash_prob, "size": pd.Series(size, index=index)}


def fx_study(world: dict, *, detail: bool = True) -> dict:
    carry, ret = world["carry"], world["returns"]
    w = quantile_long_short_weights(carry, 5)
    g = strategy_returns(w, ret).dropna()
    pc = pd.Series({s: portfolio_carry(w.loc[s], carry.loc[s]) for s in g.index})
    acc = pc.cumsum()
    wealth = (1 + g).cumprod()
    peak = wealth.cummax()
    dd = (wealth / peak - 1.0)
    jump_next = world["jump_rows"].reindex(g.index)            # a jump at row s hits the return of month s + 1
    c_mat = carry.loc[g.index].to_numpy()
    r_mat = ret.reindex(g.index + 1).to_numpy()
    c_dev, r_dev = c_mat - c_mat.mean(axis=1, keepdims=True), r_mat - r_mat.mean(axis=1, keepdims=True)
    slopes = (c_dev * r_dev).sum(axis=1) / (c_dev ** 2).sum(axis=1)               # cross-sectional OLS slope of next-month return on carry, each month
    load = 2 * (np.apply_along_axis(stats.rankdata, 1, c_mat) - 1) / (c_mat.shape[1] - 1) - 1
    load_slope = ((c_dev * (load - load.mean(axis=1, keepdims=True))).sum(axis=1) / (c_dev ** 2).sum(axis=1)).mean()      # mean of Cov(loading, carry) / Var(carry)
    expected_m = JUMP_BASE + JUMP_SD * np.sqrt(2 / np.pi)
    slope_theory = (1 - world["gamma"]) - world["crash_prob"] * expected_m * load_slope
    top_mean = float(np.mean([carry.loc[s][w.loc[s] > 0].mean() for s in g.index]))
    bot_mean = float(np.mean([carry.loc[s][w.loc[s] < 0].mean() for s in g.index]))
    return {"months": int(len(g)), "mean_portfolio_carry_pct": 100 * float(pc.mean()), "mean_return_pct": 100 * float(g.mean()),
            "take_back_ratio": float(g.mean() / pc.mean()), "sd_pct": 100 * float(g.std(ddof=1)), "skew": float(stats.skew(g, bias=False)),
            "excess_kurtosis": float(stats.kurtosis(g, bias=False)), "sharpe_annual": float(g.mean() / g.std(ddof=1) * np.sqrt(12)),
            "worst_month_pct": 100 * float(g.min()), "max_drawdown": float(dd.min()), "months_negative_share": float((g < 0).mean()),
            "jump_months": int(jump_next.sum()), "mean_in_jump_pct": 100 * float(g[jump_next].mean()), "mean_not_jump_pct": 100 * float(g[~jump_next].mean()),
            "fm_slope_mean": float(slopes.mean()), "fm_slope_true": 1 - world["gamma"], "fm_slope_theory_with_crash": float(slope_theory),
            "fm_slope_mean_no_jump_months": float(slopes[~jump_next.to_numpy()].mean()) if (~jump_next).any() else float("nan"),
            "fm_slope_mean_jump_months": float(slopes[jump_next.to_numpy()].mean()) if jump_next.any() else float("nan"),
            "top_quintile_mean_carry_pct": 100 * top_mean, "bottom_quintile_mean_carry_pct": 100 * bot_mean,
            "_g": g, "_acc": acc, "_dd": dd, "_jump": jump_next}


def fx_sweep(n_worlds: int = 200) -> dict:
    """The same data-generating process with 200 fresh seeds (SEED_FX + 1 ...): what one path can and cannot show."""
    rows = [fx_study(fx_world(SEED_FX + k), detail=False) for k in range(1, n_worlds + 1)]
    f = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    q = lambda col: {str(p): float(np.quantile(f[col], p)) for p in (0.05, 0.5, 0.95)}
    return {"worlds": n_worlds, "mean_return_pct": q("mean_return_pct"), "skew": q("skew"), "max_drawdown": q("max_drawdown"), "worst_month_pct": q("worst_month_pct"),
            "share_mean_return_negative": float((f["mean_return_pct"] < 0).mean()), "share_skew_negative": float((f["skew"] < 0).mean()),
            "share_max_drawdown_below_25pct": float((f["max_drawdown"] < -0.25).mean()),
            "mean_portfolio_carry_pct_range": [float(f["mean_portfolio_carry_pct"].min()), float(f["mean_portfolio_carry_pct"].max())],
            "share_realised_below_accrued_carry": float((f["mean_return_pct"] < f["mean_portfolio_carry_pct"]).mean()),
            "fm_slope_mean": q("fm_slope_mean"), "fm_slope_theory_with_crash_median": float(np.median(f["fm_slope_theory_with_crash"]))}


def commodity_world(seed: int = SEED_COMMODITY, months: int = 240) -> dict:
    """Spot S_t, a persistent curve slope g_t = delta_t - r_t (positive = backwardation). The contract expiring one month
    ahead trades at F_t = S_t (1 - g_t) and settles at S_(t+1)."""
    rng = np.random.default_rng(seed)
    log_s = np.cumsum(np.r_[0.0, rng.normal(0.0, 0.05, months)])
    s = 100.0 * np.exp(log_s)
    g = np.zeros(months + 1)
    g[0] = rng.normal(0.0, 0.003 / np.sqrt(1 - 0.97 ** 2))
    for t in range(1, months + 1):
        g[t] = 0.97 * g[t - 1] + rng.normal(0.0, 0.003)
    index = pd.period_range("2006-01", periods=months + 1, freq="M")
    cols = [f"E{e:03d}" for e in range(1, months + 2)]
    prices = pd.DataFrame(np.nan, index=index, columns=cols)
    for t in range(months + 1):                              # contract E(t+1): quoted at t, settles at t + 1 (if observed)
        prices.iloc[t, t] = s[t] * (1 - g[t])
        if t + 1 <= months:
            prices.iloc[t + 1, t] = s[t + 1]
    return {"prices": prices, "spot": pd.Series(s, index=index), "slope": pd.Series(g, index=index)}


def commodity_study(world: dict) -> dict:
    prices, spot, slope = world["prices"], world["spot"], world["slope"]
    idx = prices.index
    held = pd.Series(list(prices.columns), index=idx)        # the contract quoted at row t is held from t to t + 1
    trad = held_contract_returns(prices, held).iloc[:-1]
    naive = naive_splice_returns(prices, held).iloc[:-1]
    spot_ret = (spot.shift(-1) / spot - 1).iloc[:-1]
    carry_t = pd.Series([futures_carry(spot.iloc[t], prices.iloc[t, t]) for t in range(len(idx) - 1)], index=idx[:-1])
    price_part = (spot.shift(-1) - spot).iloc[:-1] / pd.Series([prices.iloc[t, t] for t in range(len(idx) - 1)], index=idx[:-1])
    gap = naive - trad
    return {"months": int(len(trad)), "mean_tradable_pct": 100 * float(trad.mean()), "mean_naive_pct": 100 * float(naive.mean()),
            "mean_spot_pct": 100 * float(spot_ret.mean()), "mean_slope_pct": 100 * float(slope.iloc[:-1].mean()),
            "cum_tradable": float((1 + trad).prod() - 1), "cum_naive": float((1 + naive).prod() - 1), "cum_spot": float(spot.iloc[-1] / spot.iloc[0] - 1),
            "decomposition_max_abs_error": float((trad - carry_t - price_part).abs().max()),
            "mean_gap_pct": 100 * float(gap.mean()), "mean_neg_next_slope_pct": -100 * float(slope.shift(-1).iloc[:-1].mean()),
            "corr_gap_next_slope": float(np.corrcoef(gap.to_numpy(), -slope.shift(-1).iloc[:-1].to_numpy())[0, 1]),
            "share_backwardation_months": float((slope.iloc[:-1] > 0).mean()),
            "_trad": trad, "_naive": naive, "_spot": spot, "_slope": slope}


# ------------------------------------------------------------------ real industries
def _ols(y: pd.Series, x: pd.Series) -> dict:
    d = pd.DataFrame({"y": y, "x": x}).dropna()
    n = len(d)
    xv, yv = d["x"].to_numpy(), d["y"].to_numpy()
    sxx = float(((xv - xv.mean()) ** 2).sum())
    b = float(((xv - xv.mean()) * (yv - yv.mean())).sum() / sxx)
    a = float(yv.mean() - b * xv.mean())
    res = yv - a - b * xv
    s2 = float((res ** 2).sum() / (n - 2))
    se_b = float(np.sqrt(s2 / sxx))
    se_a = float(np.sqrt(s2 * (1 / n + xv.mean() ** 2 / sxx)))
    return {"months": int(n), "alpha_pct": 100 * a, "alpha_t": a / se_a, "beta": b, "beta_t": b / se_b, "r2": float(1 - (res ** 2).sum() / ((yv - yv.mean()) ** 2).sum())}


def series_stats(x: pd.Series) -> dict:
    s = x.dropna()
    mean = float(s.mean())
    return {"months": int(len(s)), "mean_pct": 100 * mean, "t_iid": mean / float(s.std(ddof=1) / np.sqrt(len(s))),
            "t_nw6": mean / float(np.sqrt(newey_west_variance_of_mean(s.to_numpy(), 6))), "sd_pct": 100 * float(s.std(ddof=1)),
            "sharpe_annual": mean / float(s.std(ddof=1)) * np.sqrt(12)}


def industry_study() -> dict:
    returns, rf, prov = load_industries_and_rf()
    ff3 = json.loads(FF3_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff3"]
    table = pd.read_csv(ROOT / ff3["processed_path"], dtype={"month": str})
    table.index = pd.PeriodIndex(table.pop("month"), freq="M")
    mkt = table["Mkt-RF"]
    excess = returns.sub(rf, axis=0)
    raw = rolling_beta(excess, mkt, window=60, min_periods=36)
    beta = vasicek_shrink(raw)
    bab = bab_returns(excess, beta)
    nxt_mkt = mkt.shift(-1)
    g = bab["bab"].dropna()
    result: dict = {"provenance": {"french_hashes": prov["sha256"], "ff3_processed_sha256": ff3["processed_sha256"]}}
    mk = nxt_mkt.reindex(g.index)
    result["bab"] = {**series_stats(g), "regression_on_market": _ols(g, mk), "mean_long_leverage": float(bab["long_leverage"].dropna().mean()),
                     "mean_short_leverage": float(bab["short_leverage"].dropna().mean()), "mean_beta_low": float(bab["beta_low"].dropna().mean()),
                     "mean_beta_high": float(bab["beta_high"].dropna().mean()), "first_signal_month": str(g.index[0]), "last_signal_month": str(g.index[-1]),
                     "mean_leg_excess_low_pct": 100 * float(bab["long_leg"].dropna().mean()), "mean_leg_excess_high_pct": 100 * float(bab["short_leg"].dropna().mean())}
    result["bab_by_period"] = {}
    for name, a, b in SPLITS:
        sub = g[(g.index + 1 >= pd.Period(a, "M")) & (g.index + 1 <= pd.Period(b, "M"))]
        result["bab_by_period"][name] = {**series_stats(sub), "regression_on_market": _ols(sub, nxt_mkt.reindex(sub.index))}
    result["bab_shrink_variants"] = {}
    for weight in (1.0, 0.8, 0.6):
        series = bab_returns(excess, vasicek_shrink(raw, weight))["bab"].dropna()
        result["bab_shrink_variants"][f"{weight:.1f}"] = {**series_stats(series), "regression_on_market": _ols(series, nxt_mkt.reindex(series.index))}
    result["bab_cost_sensitivity"] = {}
    for annual in (0.0, 0.005, 0.01, 0.02, 0.04):
        cost = bab_returns(excess, beta, borrow_spread=annual / 12)["bab"].dropna()
        result["bab_cost_sensitivity"][f"{annual:.3f}"] = series_stats(cost)
    # halves by beta and by volatility (equal-weighted, 5 vs 5)
    vol = excess.rolling(12, min_periods=12).std()
    next_ex = excess.shift(-1)
    rows = beta.dropna(how="all").index.intersection(vol.dropna(how="all").index)
    low_b, high_b, low_v, high_v, overlap = {}, {}, {}, {}, []
    for s in rows:
        if s not in next_ex.index or next_ex.loc[s].isna().any() or beta.loc[s].isna().any() or vol.loc[s].isna().any():
            continue
        bi = beta.loc[s].rank(method="first")
        vi = vol.loc[s].rank(method="first")
        lb, hb = bi[bi <= 5].index, bi[bi > 5].index
        lv, hv = vi[vi <= 5].index, vi[vi > 5].index
        low_b[s], high_b[s] = next_ex.loc[s, lb].mean(), next_ex.loc[s, hb].mean()
        low_v[s], high_v[s] = next_ex.loc[s, lv].mean(), next_ex.loc[s, hv].mean()
        overlap.append(len(set(lb) & set(lv)))
    halves = {k: pd.Series(v) for k, v in {"low_beta": low_b, "high_beta": high_b, "low_vol": low_v, "high_vol": high_v}.items()}
    mk_h = nxt_mkt.reindex(halves["low_beta"].index)
    result["halves"] = {k: {**series_stats(v), "regression_on_market": _ols(v, mk_h)} for k, v in halves.items()}
    result["halves_mean_overlap_low_beta_low_vol"] = float(np.mean(overlap))
    result["halves_months"] = int(len(halves["low_beta"]))
    # conditional beta: months the market falls versus rises (ex-post diagnostic, not a tradable signal)
    down = (mk_h < 0)
    result["state_beta_low_beta_half"] = {"down_market": state_beta(halves["low_beta"], mk_h, down), "up_market": state_beta(halves["low_beta"], mk_h, ~down)}
    result["state_beta_high_beta_half"] = {"down_market": state_beta(halves["high_beta"], mk_h, down), "up_market": state_beta(halves["high_beta"], mk_h, ~down)}
    result["mean_by_market_state_pct"] = {"down": {k: 100 * float(v[down].mean()) for k, v in halves.items()}, "up": {k: 100 * float(v[~down].mean()) for k, v in halves.items()},
                                         "months_down": int(down.sum()), "months_up": int((~down).sum())}
    # security market line over the whole sample (ten points, full-sample betas: descriptive only)
    full = {c: _ols(excess[c], mkt) for c in excess.columns}
    sml = pd.DataFrame({"beta": {c: full[c]["beta"] for c in full}, "mean_excess_pct": {c: 100 * float(excess[c].mean()) for c in excess.columns}})
    line = np.polyfit(sml["beta"], sml["mean_excess_pct"], 1)
    result["sml"] = {"table": {c: {"beta": float(sml.loc[c, "beta"]), "mean_excess_pct": float(sml.loc[c, "mean_excess_pct"])} for c in sml.index},
                     "cross_section_slope_pct": float(line[0]), "cross_section_intercept_pct": float(line[1]), "market_mean_excess_pct": 100 * float(mkt.mean())}
    # worst months and correlations
    both = pd.DataFrame({"bab": g, "mkt": mk, "smb": table["SMB"].shift(-1).reindex(g.index), "hml": table["HML"].shift(-1).reindex(g.index)}).dropna()
    result["bab_corr"] = {k: float(both["bab"].corr(both[k])) for k in ("mkt", "smb", "hml")}
    worst = g.nsmallest(10)
    result["bab_worst_10"] = [{"signal_month": str(p), "return_month": str(p + 1), "bab_pct": 100 * float(v), "market_excess_pct": 100 * float(nxt_mkt.get(p, np.nan))} for p, v in worst.items()]
    wealth = (1 + g).cumprod()
    dd = wealth / wealth.cummax() - 1
    trough = dd.idxmin()
    result["bab_max_drawdown"] = {"value": float(dd.min()), "trough_return_month": str(trough + 1)}
    result["_series"] = {"bab": g, "market_next": mk, "dd": dd, "excess_means": sml, "bab_frame": bab, "halves": halves}
    return result


# ------------------------------------------------------------------ figures
def _figures(fx: dict, com: dict, real: dict, fig_dir: Path) -> None:
    # 1 FX carry crash world
    g, acc, jump = fx["_g"], fx["_acc"], fx["_jump"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    t = (g.index + 1).to_timestamp(how="end")          # g is indexed by signal month s; its return is earned in month s + 1
    ax.plot(t, (1 + g).cumprod().values, color="#176B87", lw=1.3, label="realised long-short return, compounded")
    ax.plot(t, (1 + acc).values, color="#D05A36", lw=1.3, ls="--", label="accrued portfolio carry (never realised alone), start = 1")
    for p in g.index[jump.to_numpy()]:
        ax.axvline((p + 1).to_timestamp(how="end"), color="0.6", lw=0.5, alpha=0.7)
    ax.set_xlabel("Return month (constructed world, grey lines = global squeeze months)"); ax.set_ylabel("Wealth, start = 1")
    ax.set_title("Carry portfolio: smooth accrual versus realised wealth"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    ax.hist(100 * g[~jump].values, bins=40, color="#176B87", alpha=0.8, label="ordinary months")
    ax.hist(100 * g[jump].values, bins=12, color="#D05A36", alpha=0.9, label="squeeze months")
    ax.axvline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Monthly long-short return (%)"); ax.set_ylabel("Number of months")
    ax.set_title(f"Return distribution (skew {fx['skew']:.2f}, worst month {fx['worst_month_pct']:.1f}%)"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[0], dpi=150); plt.close(fig)
    # 2 commodity splice
    trad, naive, spot, slope = com["_trad"], com["_naive"], com["_spot"], com["_slope"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    tt = trad.index.to_timestamp(how="end")
    ax.plot(tt, (1 + trad).cumprod().values, color="#176B87", lw=1.3, label="tradable: hold one contract per month, fully collateralised excess")
    ax.plot(tt, (1 + naive).cumprod().values, color="#D05A36", lw=1.3, label="naive stitched 'continuous' price")
    ax.plot(tt, (spot.iloc[:-1] / spot.iloc[0]).values, color="0.5", lw=1.0, ls=":", label="spot price")
    ax.set_yscale("log"); ax.set_xlabel("Month"); ax.set_ylabel("Wealth or price index, start = 1 (log scale)")
    ax.set_title("Same contracts, different series (constructed world)"); ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    ax.plot(slope.index.to_timestamp(how="end"), 100 * slope.values, color="#654A8B", lw=1.0)
    ax.axhline(0, color="0.4", lw=0.8)
    ax.fill_between(slope.index.to_timestamp(how="end"), 0, 100 * slope.values, where=slope.values > 0, color="#176B87", alpha=0.25, label="backwardation: long earns the slope")
    ax.fill_between(slope.index.to_timestamp(how="end"), 0, 100 * slope.values, where=slope.values < 0, color="#D05A36", alpha=0.25, label="contango: long pays the slope")
    ax.set_xlabel("Month"); ax.set_ylabel("Curve slope g = (S - F)/S per month (%)")
    ax.set_title("The roll yield is the curve slope, not a price change"); ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(fig_dir / FIGURES[1], dpi=150); plt.close(fig)
    # 3 industries SML
    sml = real["_series"]["excess_means"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    ax.scatter(sml["beta"], sml["mean_excess_pct"], color="#176B87", s=36)
    for c in sml.index:
        ax.annotate(c, (sml.loc[c, "beta"], sml.loc[c, "mean_excess_pct"]), fontsize=8, xytext=(4, 3), textcoords="offset points")
    xs = np.linspace(0.6, 1.4, 20)
    ax.plot(xs, xs * real["sml"]["market_mean_excess_pct"], color="0.5", ls="--", label="CAPM line through the market's mean excess return")
    ax.plot(xs, real["sml"]["cross_section_intercept_pct"] + real["sml"]["cross_section_slope_pct"] * xs, color="#D05A36", label="fitted line across the ten industries")
    ax.set_xlabel("Full-sample market beta of the industry (unitless)"); ax.set_ylabel("Mean monthly excess return (%)")
    ax.set_title("French 10 industries, 1926-07 to 2026-08 (ten points, descriptive)"); ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    h = real["_series"]["halves"]
    for key, color, label in (("low_beta", "#176B87", "low-beta half"), ("high_beta", "#D05A36", "high-beta half")):
        x = h[key]
        ax.semilogy(x.index.to_timestamp(how="end"), (1 + x).cumprod().values, color=color, lw=1.2, label=label + " (equal weight, excess return)")
    ax.set_xlabel("Signal month"); ax.set_ylabel("Compounded excess wealth, start = 1 (log scale)")
    ax.set_title("Beta-sorted halves of the ten industries (shrunk 60-month beta)"); ax.legend(frameon=False, fontsize=8)
    fig.savefig(fig_dir / FIGURES[2], dpi=150); plt.close(fig)
    # 4 BAB months
    s = real["_series"]
    bab, mk = s["bab"], s["market_next"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    ax.scatter(100 * mk.values, 100 * bab.values, s=6, color="#176B87", alpha=0.45)
    w10 = bab.nsmallest(10)
    ax.scatter(100 * mk.reindex(w10.index).values, 100 * w10.values, s=22, color="#D05A36", zorder=3, label="ten worst BAB months")
    ax.axhline(0, color="0.4", lw=0.8); ax.axvline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Market excess return in the return month (%)"); ax.set_ylabel("BAB return of the ten industries (% per month)")
    ax.set_title(f"Realised beta {real['bab']['regression_on_market']['beta']:.2f}: not zero, and bad months follow rebounds"); ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    ax.plot((s["dd"].index + 1).to_timestamp(how="end"), 100 * s["dd"].values, color="#654A8B", lw=1.0)
    ax.set_xlabel("Return month"); ax.set_ylabel("Drawdown of compounded BAB wealth (%)")
    ax.set_title(f"BAB drawdown (maximum {100 * real['bab_max_drawdown']['value']:.0f}%)")
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
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def run(out_dir: Path, fig_dir: Path) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch27_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 27 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    fx = fx_study(fx_world())
    com = commodity_study(commodity_world())
    real = industry_study()
    _figures(fx, com, real, fig_dir)
    result = {"hand_examples": hand_examples(), "fx_world": fx, "fx_sweep_200_worlds": fx_sweep(), "commodity_world": com, "french_industries": real,
              "seeds": {"fx": SEED_FX, "commodity": SEED_COMMODITY}}
    cleaned = _clean(result)
    (out_dir / "ch27_results.json").write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cleaned


def main() -> None:
    import uuid
    default_run = ROOT / "runs" / ("cli_ch27_carry_lowrisk_" + uuid.uuid4().hex)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(default_run / "results"))
    parser.add_argument("--figures", default=str(default_run / "figures"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    f, c, b = r["fx_world"], r["commodity_world"], r["french_industries"]["bab"]
    print(f"FX world: portfolio carry {f['mean_portfolio_carry_pct']:.3f}%/mo, realised {f['mean_return_pct']:.3f}%/mo, skew {f['skew']:.2f}, max drawdown {f['max_drawdown']:.2f}")
    print(f"Commodity world: tradable {c['mean_tradable_pct']:.3f}%/mo vs naive {c['mean_naive_pct']:.3f}%/mo vs spot {c['mean_spot_pct']:.3f}%/mo")
    print(f"BAB (10 industries): {b['mean_pct']:.3f}%/mo, t {b['t_iid']:.2f}, realised beta {b['regression_on_market']['beta']:.2f}")


if __name__ == "__main__":
    main()
