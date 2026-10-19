"""Chapter 24 CLI: value ratios, industry-relative ranking, point-in-time fundamentals, value traps, HML description.

Run from the course root::

    .venv/bin/python code/ch24_value_factors.py

Outputs ``qa/a5/claude/results/ch24/ch24_results.json`` and ``figures/a5/ch24_*.png`` (refuses to overwrite).
The firm-level panel is a **teaching construction** with a known data-generating process; it is not market data.
The only real data are the published Fama-French HML monthly returns from the frozen 2026-10-05 FF3 snapshot
(aggregate factor returns, revised history, not point-in-time, not tradable fills): they describe the premium, they do
not test stock-level value signals.
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
    bucket_returns, group_percentile, ic_series, ic_summary, lead_return, quantile_bucket, rank_cross_section, factor_rank,
)
from quant_course.factor_signals import (  # noqa: E402
    book_to_market, cheapness_percentile, ev_to_ebitda, latest_available_values, yield_ratio,
)
from quant_course.valuation import Amount, constructed_company_cases, enterprise_value  # noqa: E402

SEED = 20261031
N_FIRMS, MONTHS = 300, 108
START = pd.Period("2010-01", "M")
BETA_VALUE = 0.004        # monthly return per unit of the standardized within-industry cheapness known at signal_time
KAPPA_NEWS = 0.02         # price reaction (return) per standard deviation of book-value news in the filing month
TRAP_SHARE, TRAP_DRIFT = 0.10, -0.010
FIGURES = ("ch24_industry_and_lookahead.png", "ch24_calendar_ic.png", "ch24_deciles_and_traps.png", "ch24_hml.png")
FRENCH_FF3_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"


# ------------------------------------------------------------------ hand examples
def hand_examples() -> dict:
    cases = constructed_company_cases()
    unit = "USD millions"
    out: dict = {"orion_lyra": {}}
    for name, c in cases.items():
        mc = c["market_cap"]
        ev = enterprise_value(mc, c["debt"], c["cash"], noncontrolling_interest=c["nci"], preferred_equity=c["preferred"],
                              nonoperating_assets=c["nonoperating_assets"])
        out["orion_lyra"][name] = {
            "market_cap": mc.value, "enterprise_value": ev.value, "b_over_m": c["book_equity"].value / mc.value,
            "e_over_p": c["net_income"].value / mc.value, "fcfe_yield": c["fcfe"].value / mc.value,
            "fcff_over_ev": c["fcff"].value / ev.value, "ev_over_ebitda": ev.value / c["ebitda"].value,
        }
    # six firms, two industries: B/M levels differ by industry
    firms = ["Orion", "Lyra", "Forge", "Gear", "Harbor", "Summit", "Delta"]
    price = np.array([60.0, 24.0, 20.0, 50.0, 30.0, 45.0, 12.0]); shares = np.array([10.0, 20.0, 30.0, 8.0, 20.0, 10.0, 40.0])
    book = np.array([180.0, 120.0, 480.0, 200.0, 540.0, 360.0, 336.0])
    industry = ["Mfg", "Mfg", "Mfg", "Mfg", "Bank", "Bank", "Bank"]
    cap = price * shares; bm = book / cap
    idx = pd.period_range("2026-06", periods=1, freq="M")
    sig = pd.DataFrame([bm], index=idx, columns=firms)
    raw = factor_rank(sig).iloc[0]
    inside = group_percentile(sig, pd.Series(industry, index=firms)).iloc[0]
    out["seven_firms"] = {"market_cap": cap.tolist(), "b_over_m": bm.tolist(), "raw_rank": rank_cross_section(bm).tolist(),
                          "raw_percentile": raw.tolist(), "industry_percentile": inside.tolist(), "firms": firms}
    # denominator policy table
    cols = ["pos", "neg_earn", "neg_book", "zero_cap", "neg_ebitda"]
    e = pd.DataFrame([[30.0, -10.0, 8.0, 5.0, 12.0]], index=idx, columns=cols)
    b = pd.DataFrame([[180.0, 40.0, -25.0, 50.0, 70.0]], index=idx, columns=cols)
    m = pd.DataFrame([[600.0, 100.0, 200.0, 0.0, 300.0]], index=idx, columns=cols)
    ev = pd.DataFrame([[650.0, 150.0, 260.0, 10.0, 320.0]], index=idx, columns=cols)
    eb = pd.DataFrame([[75.0, 20.0, 30.0, 5.0, -4.0]], index=idx, columns=cols)
    out["policy_table"] = {"e_over_p": yield_ratio(e, m).iloc[0].tolist(), "b_over_m": book_to_market(b, m).iloc[0].tolist(),
                           "ev_over_ebitda": ev_to_ebitda(ev, eb).iloc[0].tolist(), "columns": cols}
    # point-in-time versions of one firm
    v = pd.DataFrame({
        "security_id": ["S1"] * 4, "period_end": pd.to_datetime(["2021-12-31", "2022-12-31", "2022-12-31", "2023-12-31"]),
        "available_at": pd.to_datetime(["2022-03-15 16:05", "2023-03-15 16:05", "2023-11-20 16:05", "2024-03-12 16:05"], utc=True),
        "ingested_at": pd.to_datetime(["2022-03-15 16:12", "2023-03-15 16:12", "2023-11-20 16:12", "2024-03-12 16:12"], utc=True),
        "book_equity": [80.0, 100.0, 90.0, 120.0]})
    months = pd.period_range("2023-02", "2024-03", freq="M")
    pit = latest_available_values(v, months, ["book_equity"])["book_equity"]["S1"]
    out["pit_example"] = {str(k): (None if np.isnan(x) else float(x)) for k, x in pit.items() if str(k) in
                          ("2023-02", "2023-03", "2023-10", "2023-11", "2024-02", "2024-03")}
    return out


# ----------------------------------------------------------------- constructed world
def _tail(rng: np.random.Generator, df: int, size) -> np.ndarray:
    return rng.standard_t(df, size) / np.sqrt(df / (df - 2))


def value_world(seed: int = SEED, *, n_firms: int = N_FIRMS, months: int = MONTHS) -> dict:
    """Firm-level fundamentals with annual filings, monthly prices and returns, a known value effect and a filing-news jump.

    Fiscal year = calendar year; the filing for FY y becomes available FYE + 60..110 days (``available_at``) and is
    ingested a day later. Month-t return = market + BETA_VALUE * z[t-1] (z = within-industry standardized log B/M from
    the *point-in-time* book value known at the end of month t-1) + KAPPA_NEWS * book news in the filing month +
    trap drift + noise. 10% of firms are "traps": priced cheaply on B/M but with a negative drift.
    """
    rng = np.random.default_rng(seed)
    idx = pd.period_range(START, periods=months, freq="M")
    names = [f"F{i:03d}" for i in range(n_firms)]
    industry = np.array(["Mfg"] * (n_firms // 2) + ["Bank"] * (n_firms - n_firms // 2))
    trap = rng.random(n_firms) < TRAP_SHARE
    first_year, last_year = idx[0].year - 2, idx[-1].year
    years = list(range(first_year, last_year + 1))
    news = rng.standard_normal((len(years), n_firms))                      # standardized book-value news per fiscal year
    g = 0.05 + 0.12 * news
    log_book = np.empty((len(years), n_firms)); log_book[0] = 5.0 + 0.7 * rng.standard_normal(n_firms) + 0.2 * (industry == "Bank")
    for k in range(1, len(years)):
        log_book[k] = log_book[k - 1] + g[k]
    delay_days = rng.integers(60, 111, size=(len(years), n_firms))
    available = pd.DataFrame({y: pd.Timestamp(f"{y}-12-31 16:05", tz="UTC") + pd.to_timedelta(delay_days[k], unit="D")
                              for k, y in enumerate(years)})
    # initial market cap: B/M level depends on industry and trap status
    log_bm0 = np.where(industry == "Bank", -0.1, -1.0) + 0.5 * rng.standard_normal(n_firms) + 0.8 * trap
    log_cap = np.empty((months, n_firms)); log_cap[0] = log_book[0] - log_bm0
    draw = rng.standard_normal(months)
    market = 0.008 + 0.045 * (draw - draw.mean()) / draw.std()      # sample mean and sd fixed: no seed luck in the level
    ret = np.full((months, n_firms), np.nan)
    versions = []
    for k, y in enumerate(years):
        for j in range(n_firms):
            av = available.iloc[j, k]
            versions.append((names[j], pd.Timestamp(f"{y}-12-31"), av, av + pd.Timedelta(days=1), float(np.exp(log_book[k, j]))))
    versions = pd.DataFrame(versions, columns=["security_id", "period_end", "available_at", "ingested_at", "book_equity"])
    pit_book = latest_available_values(versions, idx, ["book_equity"])["book_equity"].to_numpy()
    # naive look-ahead: the book value of the fiscal year that has *ended*, as if filed on fiscal year end
    naive_book = np.empty((months, n_firms))
    for i, p in enumerate(idx):
        k = years.index(p.year - 1)                                          # FY (calendar year - 1) ended on Dec 31 of last year
        naive_book[i] = np.exp(log_book[k])
    filing_month = {(k, j): pd.Period(available.iloc[j, k].tz_convert("UTC").tz_localize(None), "M") for k in range(len(years)) for j in range(n_firms)}
    industry_codes = {"Mfg": industry == "Mfg", "Bank": industry == "Bank"}
    z_prev = None
    for i in range(months):
        if i == 0:
            ret[0] = market[0] + 0.07 * _tail(rng, 5, n_firms)
        else:
            jump = np.zeros(n_firms)
            for j in range(n_firms):
                for k, y in enumerate(years):
                    if filing_month[(k, j)] == idx[i]:
                        jump[j] += KAPPA_NEWS * news[k, j]
            ret[i] = (market[i] + BETA_VALUE * z_prev + jump + TRAP_DRIFT * trap + 0.07 * _tail(rng, 5, n_firms))
            log_cap[i] = log_cap[i - 1] + np.log1p(np.maximum(ret[i], -0.95))
        lbm = np.log(pit_book[i]) - log_cap[i]
        z = np.empty(n_firms)
        for mask in industry_codes.values():
            part = lbm[mask]; z[mask] = (part - part.mean()) / part.std()
        z_prev = z
    cap = pd.DataFrame(np.exp(log_cap), index=idx, columns=names)
    return {"index": idx, "names": names, "industry": pd.Series(industry, index=names), "trap": pd.Series(trap, index=names),
            "returns": pd.DataFrame(ret, index=idx, columns=names), "cap": cap, "versions": versions,
            "pit_book": pd.DataFrame(pit_book, index=idx, columns=names), "naive_book": pd.DataFrame(naive_book, index=idx, columns=names)}


def _ic(signal: pd.DataFrame, label: pd.DataFrame) -> pd.Series:
    return ic_series(signal, label, method="spearman")["ic"]


def constructed_study(world: dict) -> dict:
    cap, ret = world["cap"], world["returns"]
    label = lead_return(ret, 1)
    bm_pit = book_to_market(world["pit_book"], cap)
    bm_naive = book_to_market(world["naive_book"], cap)
    raw_pit = cheapness_percentile(bm_pit, kind="yield")
    ind_pit = group_percentile(bm_pit, world["industry"])
    ind_naive = group_percentile(bm_naive, world["industry"])
    variants = {"raw_pit": raw_pit, "industry_pit": ind_pit, "industry_lookahead": ind_naive}
    ics = {k: _ic(v, label) for k, v in variants.items()}
    summaries = {k: ic_summary(v, nw_lags=0) for k, v in ics.items()}
    calendar = {}
    for k in ("industry_pit", "industry_lookahead"):
        s = ics[k].dropna()
        calendar[k] = {int(m): float(s[[p.month == m for p in s.index]].mean()) for m in range(1, 13)}
    # deciles and long-short (top decile = cheapest)
    dec = bucket_returns(ind_pit, label, 10).dropna()
    dec_raw = bucket_returns(raw_pit, label, 10).dropna()
    # traps among the cheapest decile
    trap = world["trap"].to_numpy()
    lab = label.to_numpy()
    top_share, top_all, top_clean = [], [], []
    by_decile = {d: [] for d in range(1, 11)}
    for i in range(len(ind_pit) - 1):
        b = quantile_bucket(ind_pit.iloc[i].to_numpy(), 10)
        for d in range(1, 11):
            sel = b == d
            if sel.any():
                by_decile[d].append(trap[sel].mean())
        top = (b == 10) & ~np.isnan(lab[i])
        if top.sum() >= 5:
            top_share.append(trap[top].mean()); top_all.append(lab[i][top].mean())
            clean = top & ~trap
            top_clean.append(lab[i][clean].mean())
    by_decile_trap = [float(np.mean(by_decile[d])) for d in range(1, 11)]
    top_trap_share, top_ret_all, top_ret_clean = top_share, top_all, top_clean
    def row(s):
        return {"mean": s.mean, "t": s.t_naive, "std": s.std, "n_dates": s.n_dates, "hit_rate": s.hit_rate}
    ls = dec["LS"]
    return {
        "n_firms": cap.shape[1], "months": cap.shape[0], "signals_with_label": int(ics["industry_pit"].notna().sum()),
        "ic_raw_pit": row(summaries["raw_pit"]), "ic_industry_pit": row(summaries["industry_pit"]),
        "ic_industry_lookahead": row(summaries["industry_lookahead"]),
        "calendar_month_mean_ic": calendar,
        "decile_mean_return_pct_industry_pit": {int(c): float(100 * dec[c].mean()) for c in dec.columns if c != "LS"},
        "decile_ls_pct_industry_pit": {"mean": float(100 * ls.mean()), "t": float(ls.mean() / (ls.std(ddof=1) / np.sqrt(len(ls)))), "months": int(len(ls))},
        "decile_ls_pct_raw_pit_mean": float(100 * dec_raw["LS"].mean()),
        "trap_share_in_cheapest_decile": float(np.mean(top_trap_share)), "trap_share_overall": float(trap.mean()),
        "trap_share_by_decile": by_decile_trap,
        "cheapest_decile_return_pct_with_traps": float(100 * np.mean(top_ret_all)),
        "cheapest_decile_return_pct_without_traps": float(100 * np.mean(top_ret_clean)),
        "population_note": "value effect = BETA_VALUE per unit of z; population Pearson IC about BETA_VALUE/sd(r)",
        "_ics": ics, "_deciles": dec, "_bm_pit": bm_pit, "_trap_by_decile": by_decile_trap,
        "_industry": world["industry"], "_world": world,
    }


# ------------------------------------------------------------------------ real HML
def hml_study() -> dict:
    manifest = json.loads(FRENCH_FF3_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff3"]
    path = ROOT / manifest["processed_path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest["processed_sha256"]:
        raise RuntimeError("FF3 processed file differs from its manifest")
    table = pd.read_csv(path, dtype={"month": str})
    table.index = pd.PeriodIndex(table.pop("month"), freq="M")
    hml, mkt, smb = table["HML"], table["Mkt-RF"], table["SMB"]

    def stats(x: pd.Series) -> dict:
        return {"months": int(len(x)), "mean_pct": float(100 * x.mean()), "t": float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))),
                "sd_pct": float(100 * x.std(ddof=1))}
    wealth = (1 + hml).cumprod()
    dd = wealth / wealth.cummax() - 1
    periods = {"1926-07..1963-06": ("1926-07", "1963-06"), "1963-07..1999-12": ("1963-07", "1999-12"),
               "2000-01..2026-08": ("2000-01", "2026-08"), "2007-01..2020-12": ("2007-01", "2020-12"), "all": ("1926-07", "2026-08")}
    return {"processed_sha256": digest, "first_month": str(hml.index[0]), "last_month": str(hml.index[-1]),
            "by_period": {k: stats(hml[a:b]) for k, (a, b) in periods.items()},
            "max_drawdown": float(dd.min()), "max_drawdown_month": str(dd.idxmin()),
            "corr_with_mkt": float(np.corrcoef(hml, mkt)[0, 1]), "corr_with_smb": float(np.corrcoef(hml, smb)[0, 1]),
            "_hml": hml, "_wealth": wealth}


# ------------------------------------------------------------------------- figures
def _figures(study: dict, hml: dict, fig_dir: Path) -> None:
    world = study["_world"]
    # 1: industry offsets and IC bars
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    date = world["cap"].index[60]
    bm = (world["pit_book"].loc[date] / world["cap"].loc[date])
    for k, (name, color) in enumerate((("Mfg", "#176B87"), ("Bank", "#D05A36"))):
        vals = np.log(bm[world["industry"] == name]).dropna()
        ax.scatter(np.full(len(vals), k) + 0.15 * np.random.default_rng(k).standard_normal(len(vals)), vals, s=10, color=color, alpha=0.6)
        ax.hlines(vals.mean(), k - 0.3, k + 0.3, color="k", lw=2)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Manufacturing", "Banks"])
    ax.set_ylabel(f"log(B/M) at {date} (log ratio)"); ax.set_title("Constructed: industry level shifts B/M for every firm in the industry")
    ax = axes[1]
    labels = ["raw B/M rank", "within-industry rank", "within-industry rank,\nlook-ahead book"]
    keys = ["ic_raw_pit", "ic_industry_pit", "ic_industry_lookahead"]
    means = [study[k]["mean"] for k in keys]; se = [study[k]["std"] / np.sqrt(study[k]["n_dates"]) for k in keys]
    ax.bar(range(3), means, yerr=[2 * s for s in se], color=["#9AA7B0", "#176B87", "#D05A36"], capsize=4)
    ax.set_xticks(range(3)); ax.set_xticklabels(labels, fontsize=9); ax.axhline(0, color="0.4", lw=0.8)
    ax.set_ylabel("Mean Spearman IC with next-month return (unitless; ±2 se)")
    ax.set_title(f"Constructed: {study['n_firms']} firms, {study['months']} months")
    fig.savefig(fig_dir / FIGURES[0], dpi=150); plt.close(fig)
    # 2: calendar-month IC
    fig, ax = plt.subplots(figsize=(10.5, 4.4), constrained_layout=True)
    months = np.arange(1, 13); w = 0.38
    ax.bar(months - w / 2, [study["calendar_month_mean_ic"]["industry_pit"][m] for m in months], w, color="#176B87", label="point-in-time book value")
    ax.bar(months + w / 2, [study["calendar_month_mean_ic"]["industry_lookahead"][m] for m in months], w, color="#D05A36", label="look-ahead: fiscal-year-end book value")
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xticks(months); ax.set_xlabel("Calendar month of signal_time (1 = January)"); ax.set_ylabel("Mean Spearman IC with next-month return (unitless)")
    ax.set_title("Constructed: FY ends Dec 31; book values become available 60-110 days later\n(late Feb/Mar-Apr); IC uses next-month returns")
    ax.legend(frameon=False)
    fig.savefig(fig_dir / FIGURES[1], dpi=150); plt.close(fig)
    # 3: deciles and traps
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    dec = study["decile_mean_return_pct_industry_pit"]
    axes[0].bar(list(dec), list(dec.values()), color="#176B87")
    axes[0].set_xticks(list(dec)); axes[0].set_xlabel("Within-industry cheapness decile (10 = cheapest)"); axes[0].set_ylabel("Mean next-month return (% per month)")
    axes[0].set_title("Constructed: equal-weight decile returns")
    axes[1].bar(range(1, 11), [100 * x for x in study["trap_share_by_decile"]], color="#D05A36")
    axes[1].axhline(100 * study["trap_share_overall"], color="k", ls="--", lw=1)
    axes[1].set_xticks(range(1, 11)); axes[1].set_xlabel("Within-industry cheapness decile (10 = cheapest)"); axes[1].set_ylabel("Share of value traps in the decile (%)")
    axes[1].set_title("Traps crowd into the cheapest decile (dashed = 10% overall)")
    fig.savefig(fig_dir / FIGURES[2], dpi=150); plt.close(fig)
    # 4: HML
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), constrained_layout=True)
    ax = axes[0]
    w = hml["_wealth"]; x = w.index.to_timestamp(how="end")
    ax.semilogy(x, w.values, color="#176B87"); ax.axvspan(pd.Timestamp("2007-01-01"), pd.Timestamp("2020-12-31"), color="#D05A36", alpha=0.15)
    ax.set_xlabel("Month (shaded: 2007-2020)"); ax.set_ylabel("Compounded HML spread, start = 1 (log scale)")
    ax.set_title("Published Fama-French HML, 1926-07 to 2026-08 (revised history)")
    ax = axes[1]
    roll = hml["_hml"].rolling(120).mean() * 100
    ax.plot(roll.index.to_timestamp(how="end"), roll.values, color="#654A8B"); ax.axhline(0, color="0.4", lw=0.8)
    ax.set_xlabel("Month (end of the 120-month window)"); ax.set_ylabel("Rolling 120-month mean of HML (% per month)")
    ax.set_title("The premium is not constant: long stretches near or below zero")
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
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


def run(out_dir: Path, fig_dir: Path) -> dict:
    out_dir, fig_dir = Path(out_dir), Path(fig_dir)
    targets = [out_dir / "ch24_results.json", *[fig_dir / n for n in FIGURES]]
    if any(t.exists() for t in targets):
        raise FileExistsError("Chapter 24 outputs already exist; choose new directories or remove them deliberately")
    out_dir.mkdir(parents=True, exist_ok=True); fig_dir.mkdir(parents=True, exist_ok=True)
    study = constructed_study(value_world())
    hml = hml_study()
    _figures(study, hml, fig_dir)
    result = {"seed": SEED, "hand_examples": hand_examples(), "constructed": study, "hml": hml}
    (out_dir / "ch24_results.json").write_text(json.dumps(_clean(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _clean(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "qa/a5/claude/results/ch24"))
    parser.add_argument("--figures", default=str(ROOT / "figures/a5"))
    args = parser.parse_args()
    r = run(Path(args.out), Path(args.figures))
    c = r["constructed"]
    print(f"IC raw {c['ic_raw_pit']['mean']:.4f} | industry PIT {c['ic_industry_pit']['mean']:.4f} (t {c['ic_industry_pit']['t']:.1f}) | look-ahead {c['ic_industry_lookahead']['mean']:.4f}")
    print(f"HML all {r['hml']['by_period']['all']['mean_pct']:.3f}%/mo (t {r['hml']['by_period']['all']['t']:.2f}); 2007-2020 {r['hml']['by_period']['2007-01..2020-12']['mean_pct']:.3f}%/mo")


if __name__ == "__main__":
    main()
