"""Chapter 29 teaching ledger: target weights -> lagged orders -> fills -> cash/positions -> NAV.

Market model (frozen A6 contract, see ``part05/chapter29/content.md`` section 5):

* One currency, no external deposits or withdrawals, discrete dates ``d_0 < d_1 < ...`` that are unique and
  increasing. Each date has a mark (close) price ``P[i,t]`` and an execution price ``E[i,t]`` that occurs
  *before* the close of the same date (for example the open). If no execution prices are given, ``E = P``.
* A target-weight row dated ``s`` is formed with information up to the close of ``s``. It is executed at
  ``E`` on date index ``s + lag`` with ``lag >= 1``; a signal is never filled at the close it was computed from.
* Within one date the order of events is: cash interest for the interval just ended -> corporate actions on the
  ex-date (split ratio on shares, cash dividend per share, delisting cash-out) -> execution -> mark at close.
* Fills are deterministic, complete and at ``E`` (no partial fills, queues or impact). Fees are a proportional
  rate ``c`` of traded notional and are paid from cash. Targets are hit *after* fees: the post-trade NAV ``V'``
  solves ``V' = V - c * sum_i |w_i V' - x_i|`` where ``x_i`` is the pre-trade holding value at ``E``.
* Cash earns (or, if negative, pays) the per-period simple rate ``cash_rate``. Short sales credit the full
  proceeds to cash; borrow fees, rebates and margin interest beyond ``cash_rate`` are *not* modelled and are
  therefore only allowed when ``allow_short=True`` is stated explicitly.
* Prices are *unadjusted* trade prices. Total-return or split-adjusted series are not trade prices and must not
  be combined with the dividend/split inputs (that double counts; Chapter 30).
* Missing data policy: duplicate/unsorted dates, NaN target weights, and NaN or non-positive prices for any asset
  that is held or traded raise ``ValueError``; nothing is forward-filled. If NAV at a close is ``<= 0`` the run
  stops (``terminated_at``) and later dates are not produced; the same happens if NAV at the execution price
  is ``<= 0`` before a scheduled trade. A rebalance whose proportional costs would exceed equity raises.

Partial fills, market impact, borrow costs and margin calls are out of scope (Chapters 33-36); the function
refuses inputs that would need them rather than silently pricing them as zero.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

_TOL = 1e-12


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float
    fee_rate: float = 0.0          # proportional, decimal of traded notional
    lag: int = 1                   # date steps from signal close to execution, >= 1
    cash_rate: float = 0.0         # per-period simple rate on the cash balance (both signs)
    allow_short: bool = False
    max_gross: float = 1.0         # sum |w_i| allowed for a target row


@dataclass
class BacktestResult:
    ledger: pd.DataFrame           # one row per produced date
    positions: pd.DataFrame        # shares held after that date's trades
    fills: pd.DataFrame            # long table, one row per (trade date, asset) with nonzero quantity
    weights: pd.DataFrame          # actual close weights q*P/NAV (cash weight = 1 - row sum)
    terminated_at: pd.Timestamp | None


def _check_index(index: pd.Index, name: str) -> None:
    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be unique and increasing")


def solve_post_fee_nav(pre_trade_nav: float, holding_values: np.ndarray, target_weights: np.ndarray,
                       fee_rate: float) -> float:
    """Unique V' with V' = V - c * sum|w V' - x|  (Newton on a convex increasing piecewise-linear function).

    Requires V > 0 and c * sum|w| < 1, which makes f(v) = v + c*sum|w v - x| - V strictly increasing, so the
    real root is unique. It is positive iff f(0) = c*sum|x| - V < 0; with shorts or leverage c*sum|x| >= V is
    possible and the returned root is then <= 0 (costs exceed equity; ``run_backtest`` refuses to trade).
    Starting at v = V (where f >= 0) each Newton step lands on the root of the current linear piece, so the
    iterates decrease monotonically and stop after finitely many pieces.
    """
    w, x = np.asarray(target_weights, float), np.asarray(holding_values, float)
    if w.ndim != 1 or x.ndim != 1 or w.shape != x.shape:
        raise ValueError("holding values and target weights must be aligned vectors")
    if not np.isfinite(w).all() or not np.isfinite(x).all() or not np.isfinite([pre_trade_nav, fee_rate]).all():
        raise ValueError("rebalance inputs must be finite")
    if fee_rate < 0:
        raise ValueError("fee_rate must be nonnegative")
    if pre_trade_nav <= 0:
        raise ValueError("pre-trade NAV must be positive to rebalance")
    if fee_rate * np.abs(w).sum() >= 1:
        raise ValueError("fee_rate * gross weight must be < 1")
    v = pre_trade_nav
    for _ in range(100):
        gap = w * v - x
        f = v + fee_rate * np.abs(gap).sum() - pre_trade_nav
        if abs(f) <= _TOL * pre_trade_nav:
            return v
        slope = 1.0 + fee_rate * float((np.sign(gap) * w).sum())
        v -= f / slope
    raise RuntimeError("post-fee NAV did not converge")


def run_backtest(mark_prices: pd.DataFrame, target_weights: pd.DataFrame, config: BacktestConfig, *,
                 exec_prices: pd.DataFrame | None = None, dividends: pd.DataFrame | None = None,
                 splits: pd.DataFrame | None = None, delistings: dict[str, tuple[object, float]] | None = None,
                 ) -> BacktestResult:
    """Run the ledger. ``target_weights`` rows are signal dates (a subset of the price index); missing columns mean 0.

    ``dividends``: cash per share paid on the ex-date to holders (shorts pay). ``splits``: new shares per old share
    on the ex-date (NaN or 1 = none). ``delistings``: asset -> (date, cash per share paid that date); afterwards
    the asset cannot be held or targeted.
    """
    if not np.isfinite([config.initial_cash, config.fee_rate, config.max_gross, config.cash_rate]).all():
        raise ValueError("backtest configuration must be finite")
    if config.initial_cash <= 0 or config.fee_rate < 0 or config.max_gross <= 0:
        raise ValueError("initial_cash must be > 0, fee_rate >= 0, max_gross > 0")
    if isinstance(config.lag, bool) or not isinstance(config.lag, int) or config.lag < 1:
        raise ValueError("lag must be an integer >= 1: a close signal cannot fill at that same close")
    _check_index(mark_prices.index, "mark_prices")
    _check_index(target_weights.index, "target_weights")
    if len(mark_prices.index) == 0 or not mark_prices.columns.is_unique or not target_weights.columns.is_unique:
        raise ValueError("prices must be nonempty and asset columns must be unique")
    dates, assets = mark_prices.index, list(mark_prices.columns)
    exec_px = mark_prices if exec_prices is None else exec_prices
    if not exec_px.index.equals(dates) or list(exec_px.columns) != assets:
        raise ValueError("exec_prices must have the same dates and assets as mark_prices")
    unknown = set(target_weights.columns) - set(assets)
    if unknown:
        raise ValueError(f"target weights for assets without prices: {sorted(unknown)}")
    missing_dates = target_weights.index.difference(dates)
    if len(missing_dates):
        raise ValueError(f"signal dates not in the price index: {list(missing_dates)[:3]}")
    targets = target_weights.reindex(columns=assets).fillna(0.0) if target_weights.notna().all().all() else None
    if targets is None:
        raise ValueError("target weights contain NaN; write 0 explicitly for a zero target")
    if not np.isfinite(targets.to_numpy(float)).all():
        raise ValueError("target weights must be finite")
    gross = targets.abs().sum(axis=1)
    if (gross > config.max_gross + 1e-12).any():
        raise ValueError("a target row exceeds max_gross")
    if not config.allow_short and (targets < 0).any().any():
        raise ValueError("negative target weights need allow_short=True (borrow costs are not modelled)")
    div = (dividends.reindex(index=dates, columns=assets).fillna(0.0) if dividends is not None
           else pd.DataFrame(0.0, index=dates, columns=assets))
    spl = (splits.reindex(index=dates, columns=assets).fillna(1.0) if splits is not None
           else pd.DataFrame(1.0, index=dates, columns=assets))
    if not np.isfinite(div.to_numpy(float)).all() or not np.isfinite(spl.to_numpy(float)).all():
        raise ValueError("corporate action inputs must be finite where provided")
    if (spl <= 0).any().any():
        raise ValueError("split ratios must be positive")
    delist = {a: (pd.Timestamp(d) if not isinstance(dates, pd.PeriodIndex) else pd.Period(d, dates.freq), float(c))
              for a, (d, c) in (delistings or {}).items()}
    if any(not np.isfinite(c) for _, c in delist.values()):
        raise ValueError("delisting cash must be finite")

    pos = np.searchsorted(dates, targets.index)
    exec_rows = {int(p) + config.lag: s for p, s in zip(pos, targets.index)}
    q = np.zeros(len(assets))
    cash = float(config.initial_cash)
    alive = np.ones(len(assets), bool)
    rows, pos_rows, w_rows, fills = [], [], [], []
    terminated = None
    for t, d in enumerate(dates):
        P, E = mark_prices.iloc[t].to_numpy(float), exec_px.iloc[t].to_numpy(float)
        cash_start = cash
        interest = cash * config.cash_rate if t > 0 else 0.0
        cash += interest
        q = q * spl.iloc[t].to_numpy(float)
        dividend_cash = float((q * div.iloc[t].to_numpy(float)).sum())
        cash += dividend_cash
        delist_cash = 0.0
        for j, a in enumerate(assets):
            if a in delist and delist[a][0] == d:
                delist_cash += q[j] * delist[a][1]
                q[j], alive[j] = 0.0, False
        cash += delist_cash
        row = {"date": d, "cash_start": cash_start, "interest": interest, "dividends": dividend_cash,
               "delist_cash": delist_cash, "signal_time": None, "nav_pre_trade": np.nan,
               "traded_notional": 0.0, "fees": 0.0}
        if t in exec_rows:
            s = exec_rows[t]
            w = targets.loc[s].to_numpy(float)
            if (~alive & (w != 0)).any():
                raise ValueError(f"target on a delisted asset at {d}")
            need = (q != 0) | (w != 0)
            if not np.isfinite(E[need]).all() or (E[need] <= 0).any():
                raise ValueError(f"missing or non-positive execution price for a held/traded asset at {d}")
            x = np.where(need, q * np.nan_to_num(E), 0.0)
            v_pre = cash + x.sum()
            if v_pre <= 0:              # equity already gone at the execution price: ruin, no trade
                row.update(signal_time=s, nav_pre_trade=v_pre, cash_end=cash, holdings_value=x.sum(), nav=v_pre)
                rows.append(row)
                pos_rows.append(q.copy())
                w_rows.append(np.full(len(assets), np.nan))
                terminated = d
                break
            v_post = solve_post_fee_nav(v_pre, x, w, config.fee_rate)
            if v_post <= 0:
                raise ValueError(f"rebalance at {d} is infeasible: proportional costs would exceed equity "
                                 "(needs fee_rate * sum|x_i| < pre-trade NAV)")
            trade_value = w * v_post - x
            trade_value[np.abs(trade_value) <= _TOL * v_pre] = 0.0
            dq = np.divide(trade_value, E, out=np.zeros_like(q), where=trade_value != 0)
            fee_each = config.fee_rate * np.abs(trade_value)
            cash -= trade_value.sum() + fee_each.sum()
            q = q + dq
            for j in np.flatnonzero(dq):
                fills.append({"signal_time": s, "trade_time": d, "asset": assets[j], "quantity": dq[j],
                              "price": E[j], "notional": trade_value[j], "fee": fee_each[j]})
            row.update(signal_time=s, nav_pre_trade=v_pre, traded_notional=float(np.abs(trade_value).sum()),
                       fees=float(fee_each.sum()))
        held = q != 0
        if not np.isfinite(P[held]).all() or (P[held] <= 0).any():
            raise ValueError(f"missing or non-positive close price for a held asset at {d}")
        hv = np.where(held, q * np.nan_to_num(P), 0.0)
        nav = cash + hv.sum()
        row.update(cash_end=cash, holdings_value=hv.sum(), nav=nav)
        rows.append(row)
        pos_rows.append(q.copy())
        w_rows.append(hv / nav if nav > 0 else np.full(len(assets), np.nan))
        if nav <= 0:
            terminated = d
            break
    idx = dates[: len(rows)]
    ledger = pd.DataFrame(rows).set_index("date")
    ledger["ret"] = ledger["nav"] / ledger["nav"].shift(1) - 1.0
    ledger.loc[ledger.index[0], "ret"] = ledger["nav"].iloc[0] / config.initial_cash - 1.0
    return BacktestResult(ledger=ledger,
                          positions=pd.DataFrame(pos_rows, index=idx, columns=assets),
                          fills=pd.DataFrame(fills, columns=["signal_time", "trade_time", "asset", "quantity",
                                                             "price", "notional", "fee"]),
                          weights=pd.DataFrame(w_rows, index=idx, columns=assets),
                          terminated_at=terminated)


def reconcile(result: BacktestResult, mark_prices: pd.DataFrame, config: BacktestConfig, *,
              exec_prices: pd.DataFrame | None = None, splits: pd.DataFrame | None = None,
              delistings: dict[str, tuple[object, float]] | None = None) -> pd.DataFrame:
    """Independent PnL attribution per date; ``residual`` must be ~0.

    NAV_t - NAV_{t-1} = interest + dividends + (delisting cash - last close value of delisted shares)
                        + sum_i q_pre,i (E_i - P_{t-1,i}/split_i) + sum_i q_post,i (P_t,i - E_i) - fees,
    where q_pre are post-split shares before trading and q_post the shares after trading.
    If execution-time equity is non-positive, the terminal mark is E: no E-to-close interval is observed.
    """
    led, positions = result.ledger, result.positions
    dates = led.index
    assets = list(mark_prices.columns)
    E_all = (mark_prices if exec_prices is None else exec_prices).loc[dates]
    P_all = mark_prices.loc[dates]
    spl = (splits.reindex(index=dates, columns=assets).fillna(1.0) if splits is not None
           else pd.DataFrame(1.0, index=dates, columns=assets))
    delist = {a: d for a, (d, _) in (delistings or {}).items()}
    out = []
    prev_nav, prev_q, prev_P = config.initial_cash, np.zeros(len(assets)), np.zeros(len(assets))
    for t, d in enumerate(dates):
        ratio = spl.iloc[t].to_numpy(float)
        q_pre = prev_q * ratio
        P_prev_adj = np.divide(prev_P, ratio)
        delisted = np.array([a in delist and pd.Period(delist[a], d.freq) == d if isinstance(d, pd.Period)
                             else a in delist and pd.Timestamp(delist[a]) == d for a in assets])
        delist_loss = float((q_pre[delisted] * P_prev_adj[delisted]).sum())
        q_pre = np.where(delisted, 0.0, q_pre)
        q_post = positions.iloc[t].to_numpy(float)
        E, P = E_all.iloc[t].to_numpy(float), P_all.iloc[t].to_numpy(float)
        price_before = float(np.where(q_pre != 0, q_pre * (np.nan_to_num(E) - np.nan_to_num(P_prev_adj)), 0).sum()) \
            if not np.isnan(led["nav_pre_trade"].iloc[t]) else float(
                np.where(q_pre != 0, q_pre * (np.nan_to_num(P) - np.nan_to_num(P_prev_adj)), 0).sum())
        price_after = float(np.where(q_post != 0, q_post * (np.nan_to_num(P) - np.nan_to_num(E)), 0).sum()) \
            if led["nav_pre_trade"].iloc[t] > 0 else 0.0
        r = led.iloc[t]
        explained = (r["interest"] + r["dividends"] + r["delist_cash"] - delist_loss
                     + price_before + price_after - r["fees"])
        out.append({"date": d, "nav_change": r["nav"] - prev_nav, "explained": explained,
                    "residual": r["nav"] - prev_nav - explained,
                    "cash_identity": r["cash_end"] - (r["cash_start"] + r["interest"] + r["dividends"]
                                                     + r["delist_cash"] - (q_post - q_pre) @ np.nan_to_num(E)
                                                     - r["fees"])})
        prev_nav, prev_q, prev_P = r["nav"], q_post, np.nan_to_num(P)
    return pd.DataFrame(out).set_index("date")


def drifted_weight_returns(close_prices: pd.DataFrame, trade_weights: pd.DataFrame) -> pd.Series:
    """Vectorized comparison under the SAME assumptions as a zero-fee, zero-rate run with E = P (close fills).

    ``trade_weights`` rows are trade dates (already lagged). From each trade close the weights drift with
    asset returns; the remainder 1 - sum(w) is cash at 0%. Returns per-date portfolio simple returns, 0 before
    the first trade. Omitted asset columns mean zero; explicit NaN/inf weights are rejected.
    This is an algorithm independent of the share ledger, used only as a cross-check.
    """
    if not np.isfinite(trade_weights.to_numpy(dtype=float)).all():
        raise ValueError("trade weights must be finite; write 0 explicitly for a zero target")
    rets = close_prices.pct_change(fill_method=None)
    w = None
    out = []
    for d in close_prices.index:
        if w is None:
            r_p = 0.0
        else:
            r = rets.loc[d].to_numpy(dtype=float)
            missing_held = (w != 0) & ~np.isfinite(r)
            if missing_held.any():
                assets = close_prices.columns[missing_held].astype(str).tolist()
                raise ValueError(f"missing or non-finite close-to-close return for held asset(s) at {d}: {', '.join(assets)}")
            r = np.where(np.isfinite(r), r, 0.0)
            r_p = float(w @ r)
            w = w * (1 + r) / (1 + r_p)
        if d in trade_weights.index:
            w = trade_weights.loc[d].reindex(close_prices.columns, fill_value=0.0).to_numpy(float)
        out.append(r_p)
    return pd.Series(out, index=close_prices.index, name="vectorized_ret")
