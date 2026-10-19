"""Runnable reference answers for projects/project05/exercises.md (P5-01 .. P5-10).

    .venv/bin/python projects/project05/solutions_code.py

Hand-calculation items use the stated inputs only. Code items use the labelled constructed panel
(src/p05_constructed.py): their numbers demonstrate the method and are not market evidence.
"""
from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))
import p05_constructed as pc  # noqa: E402
import p05_pairs as pp  # noqa: E402


def p5_01():
    beta, py, px, gross = 1.2, 80.0, 50.0, 1_000_000.0
    wy, wx = 1 / (1 + beta), -beta / (1 + beta)
    ny, nx = math.trunc(wy * gross / py), math.trunc(wx * gross / px)
    print(f"P5-01 w_y={wy:.6f} w_x={wx:.6f} $y={wy*gross:,.2f} $x={wx*gross:,.2f} shares y={ny} x={nx} "
          f"share ratio |nx|/ny={abs(nx)/ny:.6f} beta*Py/Px={beta*py/px:.6f} net $={ny*py+nx*px:,.2f}")
    return ny, nx


def p5_02(ny, nx):
    print(f"P5-02 y shares after 2:1 split={ny*2} ; x dividend cash (short)={nx*0.30:,.2f} ; "
          f"TR step y={2.0*(40.6+0.0)/80.0:.6f} ; TR step x={(49.9+0.30)/50.0:.6f}")


def p5_03(ny, nx):
    cash = 1_000_000.0 - ny * 80.0 - nx * 50.0
    days = (2 * 24 + 17.5) / 24  # Fri 16:00 -> Mon 09:30
    rate = 0.0533 - 0.0025
    interest = cash * rate * days / 360
    borrow = abs(nx) * 50.0 * 0.0025 * days / 360
    print(f"P5-03 cash={cash:,.2f} days={days:.6f} interest={interest:.4f} borrow={borrow:.4f} "
          f"cash after={cash+interest-borrow:,.4f}")


def p5_04():
    q, dec, a1, a2 = -10_000, 41.00, 40.80, 40.50
    f1, f2 = -6_000, -4_000
    p1, p2 = a1 * (1 - 0.0002 - 0.0005), a2 * (1 - 0.0002 - 0.0004)
    fees = 0.005 * 10_000
    delay, execution = q * (a1 - dec), f1 * (p1 - a1) + f2 * (p2 - a1)
    direct = f1 * (p1 - dec) + f2 * (p2 - dec) + fees
    naive = q * (a1 - dec) + f1 * (p1 - a1) + f2 * (a2 - dec) + f2 * (p2 - a2) + fees
    print(f"P5-04 p1={p1:.5f} p2={p2:.5f} delay={delay:.2f} exec={execution:.2f} fees={fees:.2f} "
          f"IS={delay+execution+fees:.2f} direct={direct:.2f} naive_redelay={naive:.2f}")


def constructed():
    long, rates, truth = pc.constructed_panel()
    panel = pp.load_panel(long)
    log_tr = np.log(pp.total_return_index(panel))
    return long, rates, panel, log_tr


def p5_05(log_tr, windows):
    rows = []
    for w in windows:
        f = pp.fit_formation(log_tr, "TA_TB", "TA", "TB", w.formation_start, w.formation_end)
        rows.append((w.k, f.corr_level, f.corr_return, f.eg_pvalue))
    df = pd.DataFrame(rows, columns=["window", "corr_level", "corr_return", "eg_p"])
    print("P5-05 TA/TB\n" + df.round(3).to_string(index=False))
    print(f"      windows with EG p<0.05: {(df.eg_p < 0.05).sum()} of {len(df)}")


def p5_06(long, rates, windows):
    panel = pp.load_panel(long)
    w = windows[0]
    base = pp.fit_formation(np.log(pp.total_return_index(panel)), "CA_CB", "CA", "CB", w.formation_start,
                            w.formation_end)
    bumped = long.copy()
    after = pd.to_datetime(bumped["date"]) > w.formation_end
    bumped.loc[after, ["open", "close"]] *= 1.5
    p2 = pp.load_panel(bumped)
    again = pp.fit_formation(np.log(pp.total_return_index(p2)), "CA_CB", "CA", "CB", w.formation_start,
                             w.formation_end)
    lt = np.log(pp.total_return_index(panel))
    s_full = lt["CA"] - base.alpha - base.beta * lt["CB"]
    leaky_mean = s_full.mean()  # uses the whole sample, including the trading window
    print(f"P5-06 frozen beta before/after future bump: {base.beta:.6f} / {again.beta:.6f} "
          f"(identical={base == again}); frozen spread mean={base.spread_mean:.6f} vs full-sample mean="
          f"{leaky_mean:.6f}")
    leakage_checks(long, rates, windows)


def leakage_checks(long, rates_df, windows):
    """P5-06 / Loom L10 runnable entry. Three separate checks, each a necessary condition only:
    (a) formation parameters ignore prices after the formation end (above);
    (b) orders signalled at or before close t and NAV through t ignore all prices after close t;
    (c) the 09:30 fills of day d ignore day d's full-day volume (known only after the close).
    Passing them does not prove an implementation leak-free; it rules out these three channels."""
    w3 = windows[:3]

    def run(lg):
        panel = pp.load_panel(lg)
        lt = np.log(pp.total_return_index(panel))
        rates = pp.load_rates(rates_df, panel.dates)
        F = {w.k: pp.fit_formation(lt, "CA_CB", "CA", "CB", w.formation_start, w.formation_end) for w in w3}
        return pp.simulate_pair(panel, lt, rates, "CA_CB", "CA", "CB", w3, F, {k: True for k in F},
                                pp.SignalRule(), pp.CostScenario(max_participation=0.001), 1e8)
    base = run(long)
    o = base["orders"]
    t = pd.Timestamp(o["signal_date"].iloc[0])
    after_t = long.copy()
    after_t.loc[pd.to_datetime(after_t["date"]) > t, ["open", "close"]] *= 1.35
    b = run(after_t)
    keep = ["order_id", "kind", "signal_date", "ticker", "attempt_ordered", "decision_price"]
    ok_b = o[o["signal_date"] <= t][keep].reset_index(drop=True).equals(
        b["orders"][b["orders"]["signal_date"] <= t][keep].reset_index(drop=True)) and \
        base["nav"].loc[:t].equals(b["nav"].loc[:t])
    d = pd.Timestamp(o["fill_date"].iloc[0])
    vol_d = long.copy()
    vol_d.loc[pd.to_datetime(vol_d["date"]) == d, "volume"] *= 1e-6
    c = run(vol_d)
    cols = [k for k in o.columns if k not in ("day_volume_diag", "day_participation_diag")]
    ok_c = o[o["fill_date"] <= d][cols].reset_index(drop=True).equals(
        c["orders"][c["orders"]["fill_date"] <= d][cols].reset_index(drop=True))
    print(f"      leakage checks: (b) signals/NAV through {t.date()} unchanged={ok_b}; "
          f"(c) fills on {d.date()} unchanged by that day's volume={ok_c}")


def p5_07(long, rates, windows):
    panel = pp.load_panel(long)
    lt = np.log(pp.total_return_index(panel))
    f = pp.fit_formation(lt, "CA_CB", "CA", "CB", windows[0].formation_start, windows[0].formation_end)
    w = lt.loc[windows[0].formation_start:windows[0].formation_end]
    resid = w["CA"] - f.alpha - f.beta * w["CB"]
    adf_crit = adfuller(resid.to_numpy(), regression="c", autolag="AIC", result_object=True).critical_values["5%"]
    print(f"P5-07 EG stat={f.eg_stat:.4f} EG 5% crit={f.eg_crit_5:.4f} plain ADF 5% crit={adf_crit:.4f} "
          f"EG p={f.eg_pvalue:.4f}")


def p5_08(long, rates):
    import json
    prereg = json.loads((HERE / "configs/preregistration_v2.json").read_text())
    sys.path.insert(0, str(HERE))
    import run_project05 as rp
    res = rp.run_all(long, rates, rp.CONSTRUCTED_PAIRS, prereg)
    m = rp.metrics_table(res)
    print("P5-08\n" + m[["pair", "gate", "total_return", "sharpe_excess", "max_drawdown", "closed_trades",
                          "win_rate", "mean_holding_days", "turnover_one_sided_ann"]].round(4).to_string(index=False))
    sel = res["formations"]
    print(f"      tests={len(sel)} EG p<0.05={int(sel.eg_pass.sum())} selected (p<0.05 and beta>0)="
          f"{int(sel.selected.sum())}; excluded by beta<=0: "
          f"{sel[sel.eg_pass & ~sel.selected][['pair', 'window', 'beta']].round(3).values.tolist()}")
    r252 = rp.run_all(long, rates, rp.CONSTRUCTED_PAIRS, prereg, formation_days=252)
    m252 = rp.metrics_table(r252)
    print("      252-day formation portfolio excess Sharpe: " + ", ".join(
        f"{g}={v:.4f}" for g, v in m252[m252.pair == "PORTFOLIO"][["gate", "sharpe_excess"]].values))
    print(f"      expected false positives if all null="
          f"{0.05*len(sel):.2f}; BH q<0.10 within windows={int((sel.qvalue_bh_window < 0.10).sum())}")
    return prereg, rp


def p5_09(long, rates, prereg, rp):
    out = {}
    for pol in ("matched", "independent"):
        r = rp.run_all(long, rates, rp.CONSTRUCTED_PAIRS, prereg, gated_only=True, w0=1e9,
                       sc_over={"partial_fill_policy": pol, "max_participation": 0.01})
        o = r["orders"]
        o = o[o["kind"].isin(["entry", "exit"])]
        first = o.drop_duplicates(["pair", "order_id", "ticker"])  # first attempt of each parent order
        dev = []
        for (pair, oid), g in first.groupby(["pair", "order_id"]):
            if len(g) == 2 and (g["filled"] != 0).all():
                ordered = g["attempt_ordered"].abs().to_numpy()
                filled = g["filled"].abs().to_numpy()
                dev.append(abs(filled[1] / filled[0] / (ordered[1] / ordered[0]) - 1))
        partial = int((o["remainder"] != 0).sum())
        retries = int(o.duplicated(["pair", "order_id", "ticker"]).sum())
        out[pol] = (partial, retries, max(dev))
        print(f"P5-09 {pol}: partial-fill rows={partial} exit retry rows={retries} "
              f"max |filled share ratio / ordered share ratio - 1| on first attempt={max(dev):.4f}")
    return out


if __name__ == "__main__":
    ny, nx = p5_01()
    p5_02(ny, nx)
    p5_03(ny, nx)
    p5_04()
    long, rates, panel, log_tr = constructed()
    windows = pp.make_windows(panel.dates, 504, 126, 126)
    p5_05(log_tr, windows)
    p5_06(long, rates, windows)
    p5_07(long, rates, windows)
    prereg, rp = p5_08(long, rates)
    p5_09(long, rates, prereg, rp)
    print("P5-10 is a written research-judgment item; see solutions.md")
