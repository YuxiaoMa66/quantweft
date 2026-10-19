"""Project 4 preparation: the signal layer (Value, Momentum, Quality) on a CONSTRUCTED company universe.

This file is the signal-preparation layer only: point-in-time fundamentals, as-of universe, field definitions, same-date preprocessing,
fixed combination and portfolio rules, and counterexamples that show what breaks when a rule is violated. It does NOT contain
transaction costs, borrow or financing, capacity, a walk-forward backtest, or any result about real companies.

Every number it produces comes from a teaching construction (``build_universe``, seed 20261210) with a known data-generating process; the
repository has no company-level point-in-time statements, no price history and no historical universe (see ``gap_table.md``).
Run from the course root: ``.venv/bin/python projects/project04/preparation/signal_layer.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from quant_course.factor_preprocessing import (  # noqa: E402
    combine_signals, expanding_zscore, neutralize, winsorize_cross_section, zscore_cross_section,
)
from quant_course.factor_research import ic_series, lead_return, quantile_long_short_weights  # noqa: E402
from quant_course.factor_signals import (  # noqa: E402
    book_to_market, cheapness_percentile, ev_to_ebitda, formation_return, latest_available_values, yield_ratio,
)
from quant_course.portfolio_construction import project_to_constraints  # noqa: E402
from quant_course.quality import accrual_ratio, average_balance, gross_profit_to_assets, guarded_ratio  # noqa: E402

SEED = 20261210
FRAME = {"constructed": True, "has_real_company_data": False,
         "purpose": "demonstrate the point-in-time signal layer, its field contract and its counterexamples; not evidence about any real company or factor"}
RULES_PATH = Path(__file__).resolve().parent / "configs/frozen_rules.json"
CONTRACT_PATH = Path(__file__).resolve().parent / "configs/signal_contract.json"
KAPPA_NEWS = 0.04                  # return in the filing month per standard deviation of the fiscal-year news (a filing-news jump)
FIGURE = "p04_signal_layer.png"
VALUE_COLUMNS = ["revenue", "cogs", "sga", "interest", "net_income", "cfo", "assets", "assets_prev", "equity", "equity_prev", "debt", "cash", "ebitda"]


def load_rules() -> dict:
    raw = RULES_PATH.read_bytes()
    rules = json.loads(raw)
    rules["_sha256"] = hashlib.sha256(raw).hexdigest()
    return rules


def load_contract() -> dict:
    raw = CONTRACT_PATH.read_bytes()
    contract = json.loads(raw)
    contract["_sha256"] = hashlib.sha256(raw).hexdigest()
    return contract


# ------------------------------------------------------------------ constructed universe
def _tail(rng: np.random.Generator, df: int, size) -> np.ndarray:
    return rng.standard_t(df, size) / np.sqrt(df / (df - 2))


def build_universe(seed: int = SEED, *, n_firms: int = 240, n_bank: int = 40, months: int = 96, start: str = "2014-01") -> dict:
    """Annual statements with filing delays and amendments, monthly total returns with a filing-news jump, IPOs and delistings.

    No effect of Value, Momentum or Quality on returns is built in; the only built-in link between filings and returns is the filing-month news
    jump (KAPPA_NEWS), which is what makes look-ahead visible. Banks have no cost of goods sold. About 3% of firm-years have near-zero or negative equity,
    about 4% of filings are amended later (amended net income and equity differ), 15% of firms list after the start and 10% delist (return -25% in the
    last month, NaN afterwards).
    """
    rng = np.random.default_rng(seed)
    idx = pd.period_range(start, periods=months, freq="M")
    names = [f"P{i:03d}" for i in range(n_firms)]
    bank = np.arange(n_firms) >= n_firms - n_bank
    industry = pd.Series(np.where(bank, "Bank", [f"Ind{i % 6}" for i in range(n_firms)]), index=names)
    years = list(range(idx[0].year - 2, idx[-1].year + 1))
    ny = len(years)
    news = rng.standard_normal((ny, n_firms))
    assets = np.empty((ny, n_firms)); assets[0] = np.exp(5.0 + 0.7 * rng.standard_normal(n_firms))
    for k in range(1, ny):
        assets[k] = assets[k - 1] * np.exp(0.05 + 0.10 * news[k])
    debt_ratio = np.clip(np.where(bank, 0.91, rng.uniform(0.05, 0.60, n_firms))[None, :] + 0.02 * rng.standard_normal((ny, n_firms)), 0.0, 0.97)
    shock = rng.random((ny, n_firms)) < 0.03
    equity_ratio = np.where(shock, rng.choice([-0.05, 0.003, 0.008], size=(ny, n_firms)), 1 - debt_ratio)
    equity = equity_ratio * assets
    debt = np.maximum(assets - equity, 0.0)
    turnover = np.where(bank, 0.06, np.exp(0.25 * rng.standard_normal(n_firms)))[None, :] * np.ones((ny, 1))
    revenue = turnover * assets
    gross_margin = np.where(bank, 0.5, 0.25 + 0.06 * rng.standard_normal(n_firms)[None, :] + 0.03 * rng.standard_normal((ny, n_firms)))
    cogs = np.where(bank[None, :], np.nan, (1 - gross_margin) * revenue)
    sga = np.where(bank[None, :], 0.30 * revenue, 0.12 * revenue * (1 + 0.1 * rng.standard_normal((ny, n_firms))))
    interest = np.where(bank[None, :], 0.025 * debt, 0.05 * debt)
    operating_income = np.where(bank[None, :], 0.012 * assets, gross_margin * revenue - sga)
    true_ni = (operating_income - np.where(bank[None, :], 0.0, interest)) * 0.75
    net_income = true_ni + (0.02 * rng.standard_normal(n_firms)[None, :] + 0.01 * rng.standard_normal((ny, n_firms))) * assets
    cfo = true_ni + 0.04 * assets + 0.005 * rng.standard_normal((ny, n_firms)) * assets
    cash = 0.05 * assets
    ebitda = np.where(bank[None, :], np.nan, operating_income + 0.03 * assets)
    delay = rng.integers(60, 111, size=(ny, n_firms))
    amend = rng.random((ny, n_firms)) < 0.04
    amend_delay = rng.integers(130, 261, size=(ny, n_firms))
    rows = []
    for k in range(1, ny):
        fye = pd.Timestamp(f"{years[k]}-12-31 16:05", tz="UTC")
        for j in range(n_firms):
            av = fye + pd.Timedelta(days=int(delay[k, j]))
            base = [revenue[k, j], cogs[k, j], sga[k, j], interest[k, j], net_income[k, j], cfo[k, j], assets[k, j], assets[k - 1, j], equity[k, j], equity[k - 1, j], debt[k, j], cash[k, j], ebitda[k, j]]
            rows.append((names[j], pd.Timestamp(f"{years[k]}-12-31"), av, av + pd.Timedelta(days=1), "10-K", *base))
            if amend[k, j]:
                f = 1.0 + 0.10 * rng.standard_normal()
                changed = list(base); changed[4] = net_income[k, j] * f; changed[8] = equity[k, j] * (1.0 + 0.5 * (f - 1.0))
                av2 = fye + pd.Timedelta(days=int(amend_delay[k, j]))
                rows.append((names[j], pd.Timestamp(f"{years[k]}-12-31"), av2, av2 + pd.Timedelta(days=1), "10-K/A", *changed))
    versions = pd.DataFrame(rows, columns=["security_id", "period_end", "available_at", "ingested_at", "form", *VALUE_COLUMNS])
    listed_from = np.where(rng.random(n_firms) < 0.15, rng.integers(6, 61, n_firms), 0)
    delist_at = np.where(rng.random(n_firms) < 0.10, rng.integers(30, months - 1, n_firms), months + 1)
    delist_at = np.maximum(delist_at, listed_from + 12)
    draw = rng.standard_normal(months)
    market = 0.008 + 0.045 * (draw - draw.mean()) / draw.std()
    ind_codes = {name: (industry.to_numpy() == name) for name in sorted(industry.unique())}
    ind_shock = {name: rng.normal(0.0, 0.02, months) for name in ind_codes}
    filing_month = np.empty((ny, n_firms), dtype=object)
    for k in range(1, ny):
        for j in range(n_firms):
            av = pd.Timestamp(f"{years[k]}-12-31 16:05", tz="UTC") + pd.Timedelta(days=int(delay[k, j]))
            filing_month[k, j] = pd.Period(av.tz_localize(None), "M")
    ret = np.full((months, n_firms), np.nan)
    for i in range(months):
        jump = np.zeros(n_firms)
        for k in range(1, ny):
            for j in range(n_firms):
                if filing_month[k, j] == idx[i]:
                    jump[j] += KAPPA_NEWS * news[k, j]
        shock_i = np.zeros(n_firms)
        for name, mask in ind_codes.items():
            shock_i[mask] = ind_shock[name][i]
        ret[i] = market[i] + shock_i + jump + 0.07 * _tail(rng, 5, n_firms)
    listed = np.zeros((months, n_firms), dtype=bool)
    for j in range(n_firms):
        listed[listed_from[j]:min(delist_at[j] + 1, months), j] = True
        if delist_at[j] < months:
            ret[delist_at[j], j] = -0.25
    ret = np.where(listed, ret, np.nan)
    bm0 = np.exp(np.where(bank, -0.1, -0.7) + 0.5 * rng.standard_normal(n_firms))
    cap = np.full((months, n_firms), np.nan)
    first = (assets[1] * (1 - np.where(bank, 0.91, 0.30))) / bm0
    for j in range(n_firms):
        level = first[j]
        for i in range(months):
            if listed[i, j]:
                level = level * (1 + max(ret[i, j], -0.95)) if not np.isnan(ret[i, j]) else level
                cap[i, j] = level
    frame = lambda a: pd.DataFrame(a, index=idx, columns=names)
    return {"frame": dict(FRAME), "index": idx, "names": names, "industry": industry, "versions": versions, "returns": frame(ret), "market_cap": frame(cap),
            "listed": frame(listed), "years": years, "seed": seed}


# ------------------------------------------------------------------ signals
def compute_signals(universe: dict, *, available_override: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """The seven raw fields of the contract at every month-end, from one filing version per name and the as-of universe.

    ``available_override`` replaces the versions table (used by the counterexamples); fundamentals are always selected through
    ``latest_available_values``. Names that are not listed at ``signal_time`` are NaN in every field.
    """
    idx, names = universe["index"], universe["names"]
    versions = universe["versions"] if available_override is None else available_override
    pit = latest_available_values(versions, idx, VALUE_COLUMNS, securities=names)
    cap, ret, listed = universe["market_cap"], universe["returns"], universe["listed"]
    assets_avg = average_balance(pit["assets"], pit["assets_prev"])
    equity_avg = average_balance(pit["equity"], pit["equity_prev"], floor=0.0)
    ev = cap + pit["debt"] - pit["cash"]
    raw = {
        "book_to_market": book_to_market(pit["equity"], cap),
        "earnings_yield": yield_ratio(pit["net_income"], cap),
        "ev_to_ebitda_cheapness": cheapness_percentile(ev_to_ebitda(ev, pit["ebitda"]), kind="multiple"),
        "mom_12_1": formation_return(ret.where(listed), 11, 1),
        "gp_a": gross_profit_to_assets(pit["revenue"], pit["cogs"], assets_avg),
        "neg_accrual": -accrual_ratio(pit["net_income"], pit["cfo"], assets_avg),
        "roe_avg": guarded_ratio(pit["net_income"], equity_avg, floor=0.05 * assets_avg),
    }
    return {k: v.where(listed) for k, v in raw.items()}


def _portfolio_inputs(panel: pd.DataFrame, universe: dict) -> tuple[pd.DataFrame, pd.Series]:
    """Validate the signal-date support and its industry labels before portfolio math."""
    listed = universe.get("listed")
    industry = universe.get("industry")
    if not isinstance(panel, pd.DataFrame) or not isinstance(listed, pd.DataFrame):
        raise TypeError("panel and universe['listed'] must be DataFrames")
    if not panel.index.is_unique or not panel.columns.is_unique:
        raise ValueError("signal index and columns must be unique")
    if not listed.index.equals(panel.index) or not listed.columns.equals(panel.columns):
        raise ValueError("listed support must have the same index and columns as the signal")
    if not listed.dtypes.map(pd.api.types.is_bool_dtype).all() or listed.isna().to_numpy().any():
        raise ValueError("listed support must contain only non-missing booleans")
    if np.isinf(panel.to_numpy(dtype=float)).any():
        raise ValueError("signals must contain only finite values or NaN")
    if not isinstance(industry, pd.Series) or not industry.index.is_unique or not industry.index.equals(panel.columns):
        raise ValueError("industry labels must be a Series aligned exactly to signal columns")
    return listed, industry


def preprocess(raw: dict[str, pd.DataFrame], universe: dict, rules: dict) -> dict[str, pd.DataFrame]:
    """Apply the frozen same-date transforms only on signal dates meeting the listed-name gate."""
    p = rules["preprocessing"]
    if not raw:
        raise ValueError("raw signals must not be empty")
    first_panel = next(iter(raw.values()))
    listed, industry = _portfolio_inputs(first_panel, universe)
    min_names = int(rules["universe"]["min_names_per_date"])
    eligible_date = listed.sum(axis=1) >= min_names
    listed_values = listed.to_numpy(dtype=bool)
    missing_industry = pd.isna(industry.to_numpy(dtype=object))
    invalid_class_dates = np.flatnonzero((eligible_date.to_numpy()[:, None] & listed_values & missing_industry[None, :]).any(axis=1))
    if len(invalid_class_dates):
        bad_date = listed.index[int(invalid_class_dates[0])]
        raise ValueError(f"listed names require non-missing industry labels at {bad_date}")
    market_cap = universe.get("market_cap")
    if not isinstance(market_cap, pd.DataFrame) or not market_cap.index.equals(listed.index) or not market_cap.columns.equals(listed.columns):
        raise ValueError("market_cap must have the same index and columns as listed support")
    log_cap = np.log(market_cap.where(market_cap > 0))
    out = {}
    for name, panel in raw.items():
        _portfolio_inputs(panel, universe)
        x = panel.where(listed).where(eligible_date, axis=0)
        x = winsorize_cross_section(x, lower=p["winsorize"]["lower"], upper=p["winsorize"]["upper"], min_names=p["winsorize"]["min_names"])
        x = neutralize(x, groups=industry, controls={"log_market_cap": log_cap})
        out[name] = zscore_cross_section(x, ddof=p["zscore"]["ddof"], min_names=p["zscore"]["min_names"])
    return out


def style_scores(z: dict[str, pd.DataFrame], rules: dict) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Equal-weight style scores (reweight, at least one field), then the equal-weight composite of the styles (reweight, at least two styles)."""
    within, across = rules["combination"]["within_style"], rules["combination"]["across_styles"]
    styles = {}
    for style, fields in rules["fields"].items():
        styles[style], _ = combine_signals({f: z[f] for f in fields}, {f: 1.0 for f in fields}, min_factors=within["min_factors"], missing=within["missing"])
    composite, count = combine_signals(styles, across["weights"], min_factors=across["min_factors"], missing=across["missing"])
    return styles, composite, count


def long_short_weights(composite: pd.DataFrame, universe: dict, rules: dict, *, industry_neutral: bool) -> pd.DataFrame:
    """Construct listed-only quintile weights and optionally neutralize over the full listed support."""
    listed, labels = _portfolio_inputs(composite, universe)
    min_names = int(rules["universe"]["min_names_per_date"])
    target_gross = float(rules["portfolio"]["gross"])
    if not np.isfinite(target_gross) or target_gross <= 0:
        raise ValueError("portfolio gross must be finite and positive")
    eligible = listed.to_numpy(dtype=bool)
    scores = composite.where(listed)
    base = quantile_long_short_weights(scores, rules["portfolio"]["n_buckets"]).to_numpy(dtype=float)
    out = np.zeros(composite.shape, dtype=float)
    cash_reasons: dict[str, str] = {}
    support_sizes: dict[str, int] = {}
    label_values = labels.to_numpy(dtype=object)
    missing_label = pd.isna(label_values)
    for i, date in enumerate(composite.index):
        date_key = str(date)
        support = eligible[i]
        support_sizes[date_key] = int(support.sum())
        if support.sum() < min_names:
            cash_reasons[date_key] = "below_min_listed_names"
            continue
        if np.any(support & missing_label):
            raise ValueError(f"listed names require non-missing industry labels at {date_key}")
        if not np.any(base[i]):
            cash_reasons[date_key] = "no_valid_quintile_directions"
            continue
        row = base[i].copy()
        row[~support] = 0.0
        if industry_neutral:
            support_labels = label_values[support]
            industries = pd.unique(support_labels)
            constraints = np.vstack([support_labels == name for name in industries]).astype(float)
            if np.linalg.matrix_rank(constraints) != len(constraints):
                raise ValueError(f"listed industry constraints are rank deficient at {date_key}")
            projected = project_to_constraints(row[support], constraints)
            projected_gross = float(np.abs(projected).sum())
            if not np.isfinite(projected_gross):
                raise ValueError(f"industry projection produced non-finite weights at {date_key}")
            if projected_gross <= 1e-12 * max(1.0, float(np.abs(row).sum())):
                cash_reasons[date_key] = "industry_projection_degenerate"
                continue
            row[support] = projected * (target_gross / projected_gross)
        else:
            row *= target_gross / float(np.abs(row).sum())
        out[i] = row
    result = pd.DataFrame(out, index=composite.index, columns=composite.columns)
    result.attrs["cash_reasons"] = cash_reasons
    result.attrs["listed_support_sizes"] = support_sizes
    result.attrs["industry_neutral"] = industry_neutral
    result.attrs["target_gross"] = target_gross
    return result


def exposure_summary(weights: pd.DataFrame, universe: dict) -> dict:
    listed, labels = _portfolio_inputs(weights, universe)
    inds = sorted(labels.unique())
    nets = np.stack([[weights.iloc[i][labels == n].sum() for n in inds] for i in range(len(weights))])
    log_cap = np.log(universe["market_cap"].where(universe["market_cap"] > 0))
    size = np.array([np.nansum(weights.iloc[i].to_numpy() * log_cap.iloc[i].to_numpy()) for i in range(len(weights))])
    active = weights.abs().sum(axis=1) > 0
    active_array = active.to_numpy()
    return {"months_with_positions": int(active.sum()), "cash_months": int((~active).sum()),
            "mean_gross": float(weights.abs().sum(axis=1)[active].mean()) if active.any() else 0.0,
            "max_abs_net": float(abs(weights.sum(axis=1)).max()),
            "mean_max_abs_industry_net": float(np.abs(nets[active_array]).max(axis=1).mean()) if active.any() else 0.0,
            "mean_abs_log_cap_exposure": float(np.abs(size[active_array]).mean()) if active.any() else 0.0,
            "max_abs_off_support_weight": float(weights.where(~listed, 0.0).abs().to_numpy().max(initial=0.0))}


def _portfolio_diagnostics(weights: pd.DataFrame, universe: dict, target_gross: float) -> dict:
    listed, labels = _portfolio_inputs(weights, universe)
    gross = weights.abs().sum(axis=1)
    active = gross > 1e-12
    nets = []
    for i in range(len(weights)):
        support_labels = labels.iloc[np.flatnonzero(listed.iloc[i].to_numpy(dtype=bool))]
        nets.append([float(weights.iloc[i, labels.to_numpy(dtype=object) == industry].sum())
                     for industry in pd.unique(support_labels)])
    active_nets = [value for row, is_active in zip(nets, active.to_numpy()) if is_active for value in row]
    return {
        "rows": int(len(weights)),
        "active_rows": int(active.sum()),
        "cash_rows": int((~active).sum()),
        "cash_reasons": dict(weights.attrs.get("cash_reasons", {})),
        "max_abs_net_active": float(weights.sum(axis=1)[active].abs().max()) if active.any() else 0.0,
        "max_abs_industry_net_active": float(max(map(abs, active_nets), default=0.0)),
        "max_abs_gross_error_active": float((gross[active] - target_gross).abs().max()) if active.any() else 0.0,
        "max_abs_off_support_weight": float(weights.where(~listed, 0.0).abs().to_numpy().max(initial=0.0)),
        "min_listed_support": int(listed.sum(axis=1).min()),
        "max_listed_support": int(listed.sum(axis=1).max()),
    }


def coverage(raw: dict[str, pd.DataFrame], universe: dict) -> pd.DataFrame:
    """Share of listed names with a non-missing value, per field, averaged over months with at least 60 listed names."""
    listed = universe["listed"]
    n_listed = listed.sum(axis=1)
    ok = n_listed >= 60
    return pd.DataFrame({name: (panel.notna() & listed).sum(axis=1)[ok] / n_listed[ok] for name, panel in raw.items()}).mean().to_frame("mean_coverage")


# ------------------------------------------------------------------ counterexamples
def naive_period_end_versions(versions: pd.DataFrame) -> pd.DataFrame:
    """The mistake: pretend every statement is available at the end of its fiscal year (period_end used as available_at)."""
    naive = versions.copy()
    naive["available_at"] = pd.to_datetime(naive["period_end"]).dt.tz_localize("UTC")
    naive["ingested_at"] = naive["available_at"] + pd.Timedelta(days=1)
    return naive[naive["form"] == "10-K"]


def _ic_stats(series: pd.Series) -> dict:
    s = series.dropna()
    return {"mean": float(s.mean()), "t": float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), "months": int(len(s))}


def counterexample_period_end(universe: dict) -> dict:
    """period_end used as available_at: how many cells change, what the signal then contains, and the IC with and without the leak.

    The leak channel is the difference ``naive - pit``: it is the content of a statement that has not been filed yet. Its cross-sectional
    correlation with the next month's return is measured separately in the signal months February and March (the filings land in March and April)
    and in the other months. The IC of the naive signal itself is reported for all months and for February-March.
    """
    pit = compute_signals(universe)
    naive = compute_signals(universe, available_override=naive_period_end_versions(universe["versions"]))
    label = lead_return(universe["returns"], 1)
    out = {}
    for name in ("book_to_market", "earnings_yield", "roe_avg", "gp_a"):
        both = pit[name].notna() & naive[name].notna()
        changed = ((pit[name] - naive[name]).abs() > 1e-12) & both
        ic_pit = ic_series(pit[name], label)["ic"]
        ic_naive = ic_series(naive[name], label)["ic"]
        leak = ic_series((naive[name] - pit[name]).where(both), label, method="pearson")["ic"]
        month = pd.Series([p.month for p in ic_pit.index], index=ic_pit.index)
        spring = month.isin([2, 3])
        out[name] = {"share_of_cells_that_differ": float(changed.to_numpy().sum() / max(both.to_numpy().sum(), 1)),
                     "ic_pit_all_months": _ic_stats(ic_pit), "ic_pit_feb_mar": _ic_stats(ic_pit[spring]),
                     "ic_period_end_as_available_all_months": _ic_stats(ic_naive), "ic_period_end_as_available_feb_mar": _ic_stats(ic_naive[spring]),
                     "leak_channel_corr_feb_mar": _ic_stats(leak[spring]), "leak_channel_corr_other_months": _ic_stats(leak[~spring])}
    return out


def counterexample_restatement(universe: dict) -> dict:
    """One amended firm-year: which equity and net income does the PIT join use before and after the amendment, and what a mixed-version ratio would do."""
    v = universe["versions"]
    amended = v[v["form"] == "10-K/A"].sort_values("available_at").iloc[0]
    orig = v[(v["security_id"] == amended.security_id) & (v["period_end"] == amended.period_end) & (v["form"] == "10-K")].iloc[0]
    idx = universe["index"]
    pit = latest_available_values(v, idx, ["net_income", "equity"], securities=universe["names"])
    before = pd.Period(orig.available_at.tz_convert("UTC").tz_localize(None), "M")
    after = pd.Period(amended.available_at.tz_convert("UTC").tz_localize(None), "M")
    sec = amended.security_id
    # first month in which the amendment is known, and the last month before it
    pre_month = after - 1
    post_month = after
    res = {"security": sec, "period_end": str(pd.Timestamp(amended.period_end).date()), "original_available_at": str(orig.available_at), "amendment_available_at": str(amended.available_at),
           "original_net_income": float(orig.net_income), "amended_net_income": float(amended.net_income), "original_equity": float(orig.equity), "amended_equity": float(amended.equity)}
    for tag, month in (("month_before_amendment", pre_month), ("month_of_amendment", post_month)):
        if month in idx:
            res[tag] = {"month": str(month), "pit_net_income": float(pit["net_income"].loc[month, sec]), "pit_equity": float(pit["equity"].loc[month, sec])}
    res["same_version_roe_before"] = float(orig.net_income / orig.equity)
    res["same_version_roe_after"] = float(amended.net_income / amended.equity)
    res["mixed_version_roe_new_numerator_old_denominator"] = float(amended.net_income / orig.equity)
    res["original_filing_month"] = str(before)
    return res


def counterexample_future_perturbation(universe: dict, rules: dict, cutoff: str = "2018-06") -> dict:
    """Change everything after ``cutoff`` (returns, new filings, amended values becoming available later) and recompute: signals up to the cutoff must not move."""
    cut = pd.Period(cutoff, "M")
    rng = np.random.default_rng(1)
    pert = {k: (v.copy() if isinstance(v, pd.DataFrame) else v) for k, v in universe.items()}
    later = pert["returns"].index > cut
    pert["returns"].loc[later] = pert["returns"].loc[later].to_numpy() + rng.normal(0, 0.2, size=pert["returns"].loc[later].shape)
    cap = pert["market_cap"].copy()
    cap.loc[later] = cap.loc[later].to_numpy() * np.exp(rng.normal(0, 0.5, size=cap.loc[later].shape))
    pert["market_cap"] = cap
    cutoff_ts = pd.Timestamp((cut + 1).start_time).tz_localize("UTC")
    v = pert["versions"].copy()
    future = v["available_at"] >= cutoff_ts
    v.loc[future, ["net_income", "equity", "assets"]] *= 3.0
    pert["versions"] = v
    a = compute_signals(universe)
    b = compute_signals(pert)
    za, zb = preprocess(a, universe, rules), preprocess(b, pert, rules)
    ca, cb = style_scores(za, rules)[1], style_scores(zb, rules)[1]
    upto = universe["index"][universe["index"] <= cut]
    diff = {k: float(np.nanmax(np.abs(a[k].loc[upto].to_numpy() - b[k].loc[upto].to_numpy()))) for k in a}
    diff["composite"] = float(np.nanmax(np.abs(ca.loc[upto].to_numpy() - cb.loc[upto].to_numpy())))
    after = universe["index"][universe["index"] > cut]
    moved = float(np.nanmax(np.abs(ca.loc[after].to_numpy() - cb.loc[after].to_numpy())))
    return {"cutoff": cutoff, "max_abs_difference_up_to_cutoff": diff, "max_abs_difference_of_composite_after_cutoff": moved, "months_compared": int(len(upto))}


def counterexample_survivorship(universe: dict, rules: dict, date: str = "2019-06") -> dict:
    """Build the universe from today's survivors only: which names disappear, and how the next-month return of the equal-weight universe moves."""
    t = pd.Period(date, "M")
    listed = universe["listed"]
    ever_delisted = (~listed.iloc[-1]) & listed.any(axis=0)
    survivors_only = listed.copy()
    survivors_only.loc[:, ever_delisted] = False
    nxt = lead_return(universe["returns"], 1)
    rows = {}
    for tag, mask in (("as_of_membership", listed), ("survivors_only", survivors_only)):
        r = nxt.where(mask).loc[t]
        rows[tag] = {"names": int(mask.loc[t].sum()), "mean_next_month_return_pct": float(100 * r.mean())}
    all_months = {tag: float(100 * nxt.where(mask).mean(axis=1).mean()) for tag, mask in (("as_of_membership", listed), ("survivors_only", survivors_only))}
    return {"date": date, "names_removed_at_date": int(listed.loc[t].sum() - survivors_only.loc[t].sum()), "at_date": rows, "mean_monthly_equal_weight_return_pct_all_months": all_months,
            "names_that_delist_by_the_end": int(ever_delisted.sum())}


def counterexample_full_sample_standardization(universe: dict, rules: dict) -> dict:
    """Time-series standardization of a style score with the full sample versus an expanding window."""
    raw = compute_signals(universe)
    z = preprocess(raw, universe, rules)
    composite = style_scores(z, rules)[1]
    series = composite.dropna(axis=1, thresh=40)
    full = (series - series.mean()) / series.std(ddof=1)
    past = expanding_zscore(series, min_periods=12)
    both = full.notna() & past.notna()
    flips = (np.sign(full) != np.sign(past)) & both
    return {"columns": int(series.shape[1]), "cells_compared": int(both.to_numpy().sum()), "share_with_opposite_sign": float(flips.to_numpy().sum() / both.to_numpy().sum()),
            "mean_abs_difference": float(np.nanmean(np.abs(full.to_numpy() - past.to_numpy())))}


def counterexample_denominators(universe: dict) -> dict:
    pit = latest_available_values(universe["versions"], universe["index"], ["equity", "ebitda", "debt", "cash"], securities=universe["names"])
    cap = universe["market_cap"]
    listed = universe["listed"]
    naive_bm = (pit["equity"] / cap).where(listed)
    safe_bm = book_to_market(pit["equity"], cap).where(listed)
    ev = cap + pit["debt"] - pit["cash"]
    naive_mult = (ev / pit["ebitda"]).where(listed)
    safe_mult = ev_to_ebitda(ev, pit["ebitda"]).where(listed)
    n_listed = int(listed.to_numpy().sum())
    return {"listed_cells": n_listed, "non_positive_book_equity_cells": int(((pit["equity"] <= 0) & listed).to_numpy().sum()), "naive_negative_bm_cells": int((naive_bm < 0).to_numpy().sum()),
            "safe_bm_negative_cells": int((safe_bm < 0).to_numpy().sum()), "naive_negative_ev_ebitda_cells": int((naive_mult < 0).to_numpy().sum()), "safe_ev_ebitda_negative_cells": int((safe_mult < 0).to_numpy().sum()),
            "naive_bm_min": float(np.nanmin(naive_bm.to_numpy())), "safe_bm_min": float(np.nanmin(safe_bm.to_numpy())),
            "financial_firms_ev_ebitda_missing_share": float(safe_mult.loc[:, universe["industry"] == "Bank"].isna().to_numpy().mean())}


def diagnostics(universe: dict, rules: dict) -> dict:
    """Coverage and Rank IC of the style scores and the composite against the next month's return; constructed world with no built-in effect."""
    raw = compute_signals(universe)
    z = preprocess(raw, universe, rules)
    styles, composite, count = style_scores(z, rules)
    label = lead_return(universe["returns"], 1)
    ics = {}
    for name, panel in {**styles, "composite": composite}.items():
        s = ic_series(panel, label)["ic"].dropna()
        ics[name] = {"mean_rank_ic": float(s.mean()), "t_iid": float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), "months": int(len(s))}
    cov = coverage(raw, universe)
    w_plain = long_short_weights(composite, universe, rules, industry_neutral=False)
    w_neutral = long_short_weights(composite, universe, rules, industry_neutral=True)
    z_checks = {k: {"mean_abs_row_mean": float(v.mean(axis=1).abs().mean()), "mean_row_sd": float(v.std(axis=1, ddof=1).mean())} for k, v in z.items()}
    return {"coverage": {k: float(v) for k, v in cov["mean_coverage"].items()}, "ic": ics, "z_checks": z_checks,
            "composite_names_per_month": {"min": int(composite.notna().sum(axis=1).min()), "median": float(composite.notna().sum(axis=1).median())},
            "share_of_composite_names_with_two_styles": float((count == 2).to_numpy().sum() / max((count >= 2).to_numpy().sum(), 1)),
            "exposures_quintile_plain": exposure_summary(w_plain, universe), "exposures_quintile_industry_neutral": exposure_summary(w_neutral, universe),
            "portfolio_support": {"min_names_per_date": int(rules["universe"]["min_names_per_date"]),
                                  "plain": _portfolio_diagnostics(w_plain, universe, float(rules["portfolio"]["gross"])),
                                  "industry_neutral": _portfolio_diagnostics(w_neutral, universe, float(rules["portfolio"]["gross"]))},
            "_composite": composite, "_raw": raw}


def make_figure(universe: dict, res: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    names = list(res["diagnostics"]["coverage"])
    vals = [100 * res["diagnostics"]["coverage"][n] for n in names]
    ax.barh(range(len(names)), vals, color="#176B87")
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=9); ax.invert_yaxis()
    ax.set_xlabel("Share of listed names with a value (%, average over months)"); ax.set_title("Field coverage of the constructed universe (banks have no COGS)")
    ax = axes[1]
    pe = res["counterexample_period_end"]
    keys = list(pe)
    x = np.arange(len(keys)); width = 0.38
    ax.bar(x - width / 2, [pe[k]["leak_channel_corr_feb_mar"]["mean"] for k in keys], width, color="#D05A36", label="signal months Feb-Mar (filings land in Mar-Apr)")
    ax.bar(x + width / 2, [pe[k]["leak_channel_corr_other_months"]["mean"] for k in keys], width, color="#176B87", label="other signal months")
    ax.axhline(0, color="0.4", lw=0.8); ax.set_xticks(x); ax.set_xticklabels(keys, fontsize=9)
    ax.set_ylabel("Mean cross-sectional correlation of (naive - point-in-time) with next month's return")
    ax.set_title("Leak counterexample: unfiled content (CONSTRUCTED)")
    ax.legend(frameon=False, fontsize=8.5)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run(out_dir: Path, fig_dir: Path | None = None) -> dict:
    out_dir = Path(out_dir)
    target = out_dir / "p04_signal_layer_results.json"
    fig_dir = Path(fig_dir) if fig_dir else ROOT / "figures/a5"
    if target.exists() or (fig_dir / FIGURE).exists():
        raise FileExistsError("Project 4 preparation outputs already exist; remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    rules, contract = load_rules(), load_contract()
    universe = build_universe()
    diag = diagnostics(universe, rules)
    result = {"frame": FRAME, "seed": SEED, "rules_sha256": rules["_sha256"], "contract_sha256": contract["_sha256"],
              "universe": {"names": len(universe["names"]), "months": len(universe["index"]), "filings": int(len(universe["versions"])), "amendments": int((universe["versions"]["form"] == "10-K/A").sum()),
                           "delisted_names": int((~universe["listed"].iloc[-1] & universe["listed"].any(axis=0)).sum()), "min_listed": int(universe["listed"].sum(axis=1).min()), "max_listed": int(universe["listed"].sum(axis=1).max())},
              "diagnostics": {k: v for k, v in diag.items() if not k.startswith("_")},
              "counterexample_period_end": counterexample_period_end(universe), "counterexample_restatement": counterexample_restatement(universe),
              "counterexample_future_perturbation": counterexample_future_perturbation(universe, rules), "counterexample_survivorship": counterexample_survivorship(universe, rules),
              "counterexample_full_sample_standardization": counterexample_full_sample_standardization(universe, rules), "counterexample_denominators": counterexample_denominators(universe),
              "variants_evaluated": {"signal_fields": 7, "styles": 3, "composite": 1, "portfolio_constructions": 2, "counterexamples": 6,
                                     "note": "the counterexamples are checks of rules, not alternative strategies; the IC diagnostics are one pre-specified set"}}
    make_figure(universe, result, fig_dir / FIGURE)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=float) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "qa/a5/claude/results/p04"))
    parser.add_argument("--figures", default=str(ROOT / "figures/a5"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    d = r["diagnostics"]
    print("coverage:", {k: round(v, 3) for k, v in d["coverage"].items()})
    print("Rank IC (constructed null world):", {k: (round(v["mean_rank_ic"], 4), round(v["t_iid"], 2)) for k, v in d["ic"].items()})
    print("leak channel corr, Feb-Mar vs other:", {k: (round(v["leak_channel_corr_feb_mar"]["mean"], 3), round(v["leak_channel_corr_other_months"]["mean"], 3)) for k, v in r["counterexample_period_end"].items()})
    print("future perturbation, max abs composite difference up to cutoff:", r["counterexample_future_perturbation"]["max_abs_difference_up_to_cutoff"]["composite"])


if __name__ == "__main__":
    main()
