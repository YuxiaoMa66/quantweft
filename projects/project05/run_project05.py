"""Project 5 CLI: walk-forward pairs research on a frozen daily panel.

    .venv/bin/python projects/project05/run_project05.py --data constructed --out <new dir>
    .venv/bin/python projects/project05/run_project05.py --data real --out <new dir>

``--data real`` needs the licensed panel listed in ``projects/project05/data_manifest.json`` (status ``frozen``); until
then it exits with code 3 (BLOCKED) and writes nothing. ``--data constructed`` runs the same pipeline on the labelled
teaching panel from ``src/p05_constructed.py``; every output carries ``data_class=constructed`` and is not evidence.
The output directory must not exist (no overwrite).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "src"))
import p05_constructed  # noqa: E402
import p05_pairs as pp  # noqa: E402

PREREG = HERE / "configs" / "preregistration_v2.json"
SUPPORTED_SCHEMA = "p05-preregistration.v2"  # v1 results live in the frozen c1-c4 evidence; v1 is not re-runnable here
MANIFEST = HERE / "data_manifest.json"
CONSTRUCTED_PAIRS = [{"id": "CA_CB", "y": "CA", "x": "CB"}, {"id": "TA_TB", "y": "TA", "x": "TB"},
                     {"id": "IA_IB", "y": "IA", "x": "IB"}]
ETFS = {"EWA", "EWC", "GDX", "GLD", "XOP", "XLE", "IVV", "SPY"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(kind: str, prereg: dict, *, prereg_sha256: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], dict]:
    if kind == "constructed":
        panel, rates, truth = p05_constructed.constructed_panel()
        return panel, rates, CONSTRUCTED_PAIRS, {"data_class": "constructed", "truth": truth}
    if not MANIFEST.exists():
        raise SystemExit(3)
    man = json.loads(MANIFEST.read_text())
    if prereg_sha256 != man["preregistration"]["sha256"]:
        raise SystemExit("preregistration hash mismatch: real main specification requires manifest-bound bytes")
    if man.get("status") != "frozen":
        print(f"BLOCKED: data_manifest status is {man.get('status')!r}, not 'frozen'", file=sys.stderr)
        raise SystemExit(3)
    files = {f["role"]: f for f in man["files"]}
    for f in man["files"]:
        if sha256(ROOT / f["path"]) != f["sha256"]:
            raise SystemExit(f"hash mismatch: {f['path']}")
    panel = pd.read_csv(ROOT / files["panel"]["path"])
    rates = pd.read_csv(ROOT / files["rates"]["path"])
    first, last = prereg["sample"]["first_date"], prereg["sample"]["last_date"]
    panel = panel[(pd.to_datetime(panel["date"]) >= first) & (pd.to_datetime(panel["date"]) <= last)]
    return panel, rates, prereg["universe"]["pairs"], {"data_class": "real", "manifest_sha256": sha256(MANIFEST)}


def scenario(prereg: dict, tickers: list[str], **over) -> pp.CostScenario:
    c = prereg["costs_scenarios_not_calibrated"]
    hs = {t: c["half_spread_bps"]["ETF" if t in ETFS else "stock"] for t in tickers}
    base = pp.CostScenario(commission_per_share=c["commission_usd_per_share"], half_spread_bps=hs,
                           default_half_spread_bps=c["half_spread_bps"]["stock"], eta=0.1,
                           max_participation=c["opening_fill_budget"]["max_fraction_of_adv20"],
                           borrow_fee_annual=c["borrow_fee_annual"],
                           credit_spread=c["cash_credit_spread_below_policy_rate"],
                           debit_spread=c["cash_debit_spread_above_policy_rate"])
    mult = over.pop("half_spread_multiplier", 1.0)
    base = replace(base, half_spread_bps={t: v * mult for t, v in hs.items()})
    return replace(base, **over)


def selected(f: pp.Formation, prereg: dict) -> bool:
    """Selection rule read from the preregistration (v2: EG p < 0.05 AND beta > 0)."""
    r = prereg["screening"]["select_rule"]
    return bool(f.eg_pvalue < r["pvalue_lt"] and f.beta > r["beta_gt"])


def check_prereg(prereg: dict) -> None:
    if prereg.get("schema") != SUPPORTED_SCHEMA:
        raise SystemExit(f"preregistration schema {prereg.get('schema')!r} is not {SUPPORTED_SCHEMA!r}; "
                         "v1 is superseded and its results are kept in the c1-c4 evidence")


def run_all(panel_long, rates_df, pairs, prereg, *, formation_days=None, rule=None, sc_over=None, w0=None,
            gated_only=False):
    check_prereg(prereg)
    P = pp.load_panel(panel_long, sorted({p[k] for p in pairs for k in ("y", "x")}))
    log_tr = np.log(pp.total_return_index(P))
    rates = pp.load_rates(rates_df, P.dates)
    wf = prereg["walk_forward"]
    windows = pp.make_windows(P.dates, formation_days or wf["formation_days"], wf["trading_days"], wf["step_days"])
    sig = prereg["signal"]
    rule = rule or pp.SignalRule(sig["entry_abs_z"], sig["exit_abs_z"], sig["stop_abs_z"])
    sc = scenario(prereg, P.tickers, **(sc_over or {}))
    w0 = w0 or prereg["sizing"]["initial_wealth_per_pair_usd"]
    form_rows, navs, orders, trades, ledgers = [], {}, [], [], {}
    formations = {p["id"]: {w.k: pp.fit_formation(log_tr, p["id"], p["y"], p["x"], w.formation_start,
                                                  w.formation_end) for w in windows} for p in pairs}
    for w in windows:
        ps = np.array([formations[p["id"]][w.k].eg_pvalue for p in pairs])
        qs = pp.bh_qvalues(ps)
        for p, q in zip(pairs, qs):
            f = formations[p["id"]][w.k]
            row = {k: v for k, v in asdict(f).items()}
            row.update(window=w.k, qvalue_bh_window=float(q), selected=selected(f, prereg),
                       eg_pass=bool(f.eg_pvalue < prereg["screening"]["select_rule"]["pvalue_lt"]),
                       trade_start=str(w.signal_dates[0].date()), trade_last_signal=str(w.signal_dates[-1].date()))
            form_rows.append(row)
    for p in pairs:
        F = formations[p["id"]]
        gates = {"screened": {k: selected(f, prereg) for k, f in F.items()}}
        if not gated_only:
            gates["ungated"] = {k: True for k in F}
        for g, active in gates.items():
            res = pp.simulate_pair(P, log_tr, rates, p["id"], p["y"], p["x"], windows, F, active, rule, sc, w0)
            navs[(p["id"], g)] = res["nav"]
            ledgers[(p["id"], g)] = res
            for frame, sink in ((res["orders"], orders), (res["trades"], trades)):
                if len(frame):
                    sink.append(frame.assign(pair=p["id"], gate=g))
    nav = pd.DataFrame({f"{k[0]}|{k[1]}": v for k, v in navs.items()})
    credit = rates - sc.credit_spread
    return {"P": P, "rates": rates, "credit": credit, "windows": windows, "formations": pd.DataFrame(form_rows),
            "nav": nav, "orders": pd.concat(orders, ignore_index=True) if orders else pd.DataFrame(),
            "trades": pd.concat(trades, ignore_index=True) if trades else pd.DataFrame(), "ledgers": ledgers,
            "scenario": sc, "rule": rule}


def portfolio_nav(nav: pd.DataFrame, gate: str) -> pd.Series:
    """Equal-capital sleeve fund: each pair ledger starts with the same W0; fund NAV is their sum."""
    return nav[[c for c in nav.columns if c.endswith(f"|{gate}")]].sum(axis=1)


def metrics_table(res) -> pd.DataFrame:
    rows = []
    nav, credit = res["nav"], res["credit"]
    orders, tr = res["orders"], res["trades"]
    for col in nav.columns:
        pair, gate = col.split("|")
        led = res["ledgers"][(pair, gate)]
        ep = tr[(tr["pair"] == pair) & (tr["gate"] == gate)] if len(tr) else tr
        od = orders[(orders["pair"] == pair) & (orders["gate"] == gate)] if len(orders) else orders
        ts = pp.trade_stats(ep)
        m = pp.nav_metrics(nav[col], credit)
        if ts["closed_trades"] + ts["open_trades"] == 0:  # cash-only sleeve: Sharpe undefined
            m["sharpe_excess"] = float("nan")
        rows.append({"pair": pair, "gate": gate, **m, **ts, **pp.turnover_stats(od, nav[col]),
                     **{f"total_{k}": float(v) for k, v in led["totals"].items()},
                     "cash_residual": float(led["cash_residual"])})
    for gate in sorted({c.split("|")[1] for c in nav.columns}):
        pn = portfolio_nav(nav, gate)
        ep = tr[tr["gate"] == gate] if len(tr) else tr
        od = orders[orders["gate"] == gate] if len(orders) else orders
        rows.append({"pair": "PORTFOLIO", "gate": gate, **pp.nav_metrics(pn, credit), **pp.trade_stats(ep),
                     **pp.turnover_stats(od, pn)})
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", choices=["real", "constructed"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-robustness", action="store_true")
    ap.add_argument("--prereg", default=str(PREREG), help="preregistration file (must be schema v2)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    prereg_path = Path(a.prereg)
    prereg_bytes = prereg_path.read_bytes()
    prereg_digest = hashlib.sha256(prereg_bytes).hexdigest()
    prereg = json.loads(prereg_bytes)
    check_prereg(prereg)
    try:
        panel, rates, pairs, meta = load_inputs(a.data, prereg, prereg_sha256=prereg_digest)
    except SystemExit as e:
        if e.code == 3:
            print("BLOCKED: no frozen licensed real panel (see projects/project05/data_manifest.json); "
                  "nothing written", file=sys.stderr)
        raise
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    t0 = time.time()
    res = run_all(panel, rates, pairs, prereg)
    res["formations"].to_csv(out / "formations.csv", index=False)
    res["nav"].to_csv(out / "nav.csv", index_label="date")
    res["orders"].to_csv(out / "orders.csv", index=False)
    res["trades"].to_csv(out / "trades.csv", index=False)
    res["rates"].to_frame("policy_rate_available").to_csv(out / "rates_used.csv", index_label="date")
    mt = metrics_table(res)
    mt.to_csv(out / "metrics.csv", index=False)
    ev = []
    for (pair, gate), led in res["ledgers"].items():
        for e in led["events"]:
            ev.append({"pair": pair, "gate": gate, **{k: (str(v) if isinstance(v, pd.Timestamp) else v)
                                                      for k, v in e.items()}})
    pd.DataFrame(ev).to_csv(out / "ledger_events.csv", index=False)
    robustness = []
    if not a.skip_robustness:
        g = prereg["robustness_all_reported"]
        for hsm, eta, bf in itertools.product(g["cost_grid"]["half_spread_multiplier"], g["cost_grid"]["eta"],
                                              g["cost_grid"]["borrow_fee_annual"]):
            r = run_all(panel, rates, pairs, prereg, gated_only=True,
                        sc_over={"half_spread_multiplier": hsm, "eta": eta, "borrow_fee_annual": bf})
            m = metrics_table(r)
            robustness.append(m.assign(grid="cost", half_spread_multiplier=hsm, eta=eta, borrow_fee_annual=bf))
        for en, ex in itertools.product(g["threshold_grid"]["entry_abs_z"], g["threshold_grid"]["exit_abs_z"]):
            r = run_all(panel, rates, pairs, prereg, gated_only=True,
                        rule=pp.SignalRule(en, ex, prereg["signal"]["stop_abs_z"]))
            robustness.append(metrics_table(r).assign(grid="threshold", entry=en, exit=ex))
        for fd in g["formation_days_alt"]:
            r = run_all(panel, rates, pairs, prereg, formation_days=fd)
            robustness.append(metrics_table(r).assign(grid="formation_days", formation_days=fd))
            r["formations"].to_csv(out / f"formations_f{fd}.csv", index=False)
        for pol in ("matched", "independent"):
            r = run_all(panel, rates, pairs, prereg, gated_only=True, w0=1e9, sc_over={"partial_fill_policy": pol})
            robustness.append(metrics_table(r).assign(grid="partial_fill_stress", policy=pol, w0=1e9))
            r["orders"].to_csv(out / f"orders_stress_{pol}.csv", index=False)
        pd.concat(robustness, ignore_index=True).to_csv(out / "robustness.csv", index=False)
    summary = {**{k: v for k, v in meta.items() if k != "truth"}, "truth": meta.get("truth"),
               "prereg_path": str(prereg_path), "prereg_schema": prereg["schema"],
               "prereg_sha256": prereg_digest,
               "specification_class": ("frozen_main_spec" if prereg_digest ==
                   json.loads(MANIFEST.read_text())["preregistration"]["sha256"] else
                   "constructed_custom_exploration"),
               "prereg_v2_summary": {"select_rule": prereg["screening"]["select_rule"],
                                     "opening_fill_budget": prereg["costs_scenarios_not_calibrated"][
                                         "opening_fill_budget"]["max_fraction_of_adv20"],
                                     "event_order": prereg["event_order"]},
               "eg_pass_total": int(res["formations"]["eg_pass"].sum()), "code_sha256": {p.name: sha256(p) for p in
                                                                 sorted((HERE / "src").glob("*.py"))},
               "cli_sha256": sha256(Path(__file__)), "pairs": [p["id"] for p in pairs],
               "windows": len(res["windows"]), "tests_total": int(len(res["formations"])),
               "selected_total": int(res["formations"]["selected"].sum()),
               "scenario": {k: (sorted(v) if isinstance(v, frozenset) else v) for k, v in
                            asdict(res["scenario"]).items()},
               "rule": asdict(res["rule"]), "seconds": round(time.time() - t0, 1)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({"out": str(out), "data_class": meta["data_class"], "windows": summary["windows"],
                      "tests_total": summary["tests_total"], "selected_total": summary["selected_total"],
                      "seconds": summary["seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
