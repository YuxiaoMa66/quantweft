"""Project 5 pairs-trading pipeline: daily panel -> formation screen -> frozen spread signals -> two-leg ledger.

Contract (frozen in ``configs/preregistration_v2.json``, which supersedes v1 for every new run; Part VI interfaces in
``qa/a7/project05_batch/PART_VI_CONSISTENCY.md``):

* Input panel is vendor-agnostic and long: ``date, ticker, open, close, volume, split_ratio, dividend``. ``open`` and
  ``close`` are *unadjusted* trade prices (USD/share), ``volume`` unadjusted shares, ``split_ratio`` new shares per old
  share on the ex-date (1 = none), ``dividend`` cash per post-event share on the ex-date (0 = none). Every ticker must
  have every calendar date; nothing is forward-filled and no missing day is dropped.
* Signal series is a forward-built total-return index ``TR_t = TR_{t-1} * r_t (C_t + D_t) / C_{t-1}`` that uses only
  events dated <= t. Trade prices and corporate actions go to the ledger; the TR index never does (no double count).
* Formation window: OLS ``log TR_y = alpha + beta log TR_x + e``; Engle-Granger (statsmodels ``coint``, constant,
  AIC lags, MacKinnon residual critical values) on trading-day steps; spread mean/sd frozen. Nothing after the
  formation end is read by the formation step.
* Signal at the 16:00 ET close of day t; orders fill at the 09:30 ET open of day t+1. Event order on a day: accrue
  interest/borrow to 09:30 on the previous marks -> split -> dividend -> mark both legs at the 09:30 open ->
  fills -> accrue to 16:00 (borrow basis = open marks) -> mark at close.
* Financing: ACT/360 simple interest on the cash balance at the start of each interval, at a rate known at that start;
  borrow fee on |short shares| x the last available mark at the interval start. Same rule as the A7-B ledger.
* Fill price = open x (1 + side x (half_spread + eta x sigma20 x sqrt(q / ADV20))). Spread and impact live in the
  fill price only; commission is cash. The opening fill is limited by an ex-ante budget ``max_participation`` x ADV20
  known at the signal close (restated to the fill day's post-split shares). This is an uncalibrated opening-fill
  scenario, not a realised participation guarantee; the fill day's full-day volume is only known after the close and
  is recorded as a post-close diagnostic that never changes the 09:30 fill.

All costs, borrow fees and participation limits are scenario parameters, not calibrated estimates.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint

PANEL_COLUMNS = ["date", "ticker", "open", "close", "volume", "split_ratio", "dividend"]
OPEN_TIME = pd.Timedelta(hours=9, minutes=30)
CLOSE_TIME = pd.Timedelta(hours=16)
TZ = "America/New_York"


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Panel:
    """Wide, validated daily frames indexed by trading date (tz-naive dates, NY calendar)."""
    open: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame
    split_ratio: pd.DataFrame
    dividend: pd.DataFrame

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.close.index

    @property
    def tickers(self) -> list[str]:
        return list(self.close.columns)


def load_panel(long: pd.DataFrame, tickers: list[str] | None = None) -> Panel:
    """Validate a long panel and pivot it. Missing ticker-days, duplicates or bad values raise ``ValueError``."""
    missing_cols = set(PANEL_COLUMNS) - set(long.columns)
    if missing_cols:
        raise ValueError(f"panel lacks columns {sorted(missing_cols)}")
    df = long[PANEL_COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"])
    if tickers is not None:
        absent = set(tickers) - set(df["ticker"])
        if absent:
            raise ValueError(f"tickers absent from panel: {sorted(absent)}")
        df = df[df["ticker"].isin(tickers)]
    if df.duplicated(["date", "ticker"]).any():
        raise ValueError("duplicate (date, ticker) rows")
    num = df[["open", "close", "volume", "split_ratio", "dividend"]].to_numpy(float)
    if not np.isfinite(num).all():
        raise ValueError("panel contains non-finite values")
    if (df[["open", "close", "split_ratio"]] <= 0).any().any():
        raise ValueError("open, close and split_ratio must be positive")
    if (df[["volume", "dividend"]] < 0).any().any():
        raise ValueError("volume and dividend must be non-negative")
    wide = {c: df.pivot(index="date", columns="ticker", values=c).sort_index() for c in PANEL_COLUMNS[2:]}
    if wide["close"].isna().any().any():
        bad = wide["close"].isna().stack()
        raise ValueError(f"missing ticker-days (no forward fill): {list(bad[bad].index[:5])}")
    order = sorted(wide["close"].columns) if tickers is None else list(tickers)
    return Panel(**{k: v[order].astype(float) for k, v in wide.items()})


def total_return_index(panel: Panel) -> pd.DataFrame:
    """Forward-built TR index (base 1 on the first date) from unadjusted closes, splits and dividends."""
    c, r, d = panel.close, panel.split_ratio, panel.dividend
    gross = (r * (c + d)) / c.shift(1)
    gross.iloc[0] = 1.0
    return gross.cumprod()


def load_rates(rates: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.Series:
    """Annual decimal policy rate *available* on each trading date (prior observation, publication lag 1 day).

    ``rates`` has columns ``date`` and ``rate`` (decimal, e.g. 0.0525). The rate observed for calendar day s is taken as
    available from the next calendar day, so a trading date d uses the last observation dated < d.
    """
    r = rates.copy()
    r["date"] = pd.to_datetime(r["date"])
    r = r.dropna().sort_values("date").set_index("date")["rate"].astype(float)
    if r.index.has_duplicates or not np.isfinite(r.to_numpy()).all():
        raise ValueError("rates must have unique dates and finite values")
    avail = r.copy()
    avail.index = avail.index + pd.Timedelta(days=1)
    out = avail.reindex(avail.index.union(dates)).ffill().reindex(dates)
    if out.isna().any():
        raise ValueError("no rate available before the first trading date")
    return out


# ---------------------------------------------------------------------------
# Formation (training only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Formation:
    pair: str
    y: str
    x: str
    start: pd.Timestamp
    end: pd.Timestamp
    n: int
    alpha: float
    beta: float
    spread_mean: float
    spread_sd: float
    eg_stat: float
    eg_pvalue: float
    eg_crit_5: float
    corr_level: float
    corr_return: float
    half_life_days: float


def half_life(spread: np.ndarray) -> float:
    """AR(1) half-life in days from ds_t = a + b s_{t-1}; inf when b >= 0 (no mean reversion)."""
    s = np.asarray(spread, float)
    lag, ds = s[:-1], np.diff(s)
    X = np.column_stack([np.ones_like(lag), lag])
    b = np.linalg.lstsq(X, ds, rcond=None)[0][1]
    return float(-math.log(2) / math.log(1 + b)) if -1 < b < 0 else float("inf")


def fit_formation(log_tr: pd.DataFrame, pair: str, y: str, x: str, start: pd.Timestamp,
                  end: pd.Timestamp) -> Formation:
    """Estimate everything that the trading window will freeze, using rows start..end only."""
    w = log_tr.loc[start:end, [y, x]]
    if w.isna().any().any() or len(w) < 60:
        raise ValueError("formation window must be complete and have >= 60 days")
    yv, xv = w[y].to_numpy(), w[x].to_numpy()
    X = np.column_stack([np.ones_like(xv), xv])
    alpha, beta = np.linalg.lstsq(X, yv, rcond=None)[0]
    spread = yv - alpha - beta * xv
    stat, pvalue, crit = coint(yv, xv, trend="c", autolag="AIC")
    rets = w.diff().dropna()
    return Formation(
        pair=pair, y=y, x=x, start=w.index[0], end=w.index[-1], n=len(w),
        alpha=float(alpha), beta=float(beta), spread_mean=float(spread.mean()),
        spread_sd=float(spread.std(ddof=1)), eg_stat=float(stat), eg_pvalue=float(pvalue),
        eg_crit_5=float(crit[1]), corr_level=float(np.corrcoef(yv, xv)[0, 1]),
        corr_return=float(rets[y].corr(rets[x])), half_life_days=half_life(spread),
    )


def bh_qvalues(pvalues: np.ndarray) -> np.ndarray:
    p = np.asarray(pvalues, float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out


# ---------------------------------------------------------------------------
# Signals (pure function of frozen formation + log TR up to the signal close)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalRule:
    entry: float = 2.0
    exit: float = 0.5
    stop: float = 4.0

    def __post_init__(self) -> None:
        if not 0 <= self.exit < self.entry < self.stop:
            raise ValueError("need 0 <= exit < entry < stop")


def zscores(log_tr: pd.DataFrame, f: Formation, dates: pd.DatetimeIndex) -> pd.Series:
    s = log_tr.loc[dates, f.y] - f.alpha - f.beta * log_tr.loc[dates, f.x]
    return (s - f.spread_mean) / f.spread_sd


def target_states(z: pd.Series, rule: SignalRule) -> pd.Series:
    """State after each close: +1 long spread (long y, short x), -1 short spread, 0 flat.

    Enter when |z| >= entry, exit when |z| <= exit or the sign crosses, stop when |z| >= stop; no re-entry after a
    stop inside the same window. The last close of the window is forced flat.
    """
    out, state, stopped = [], 0, False
    vals = z.to_numpy()
    for i, v in enumerate(vals):
        if not np.isfinite(v):
            raise ValueError("non-finite z-score")
        if state != 0:
            if abs(v) >= rule.stop:
                state, stopped = 0, True
            elif abs(v) <= rule.exit or np.sign(v) == state:
                state = 0
        elif not stopped and rule.entry <= abs(v) < rule.stop:
            state = -int(np.sign(v))
        if i == len(vals) - 1:
            state = 0
        out.append(state)
    return pd.Series(out, index=z.index, dtype=int)


# ---------------------------------------------------------------------------
# Cost and execution scenario
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CostScenario:
    commission_per_share: float = 0.005
    half_spread_bps: dict[str, float] = field(default_factory=dict)  # per ticker; default below
    default_half_spread_bps: float = 2.0
    eta: float = 0.1
    max_participation: float = 0.05  # fraction of ADV20 known at the signal close (ex-ante opening-fill budget)
    borrow_fee_annual: float = 0.0025
    credit_spread: float = 0.0025
    debit_spread: float = 0.005
    partial_fill_policy: str = "matched"  # or "independent"
    locate_unavailable: frozenset = frozenset()  # {(ticker, date)} on which a new short cannot be located

    def __post_init__(self) -> None:
        for name in ("commission_per_share", "default_half_spread_bps", "eta", "borrow_fee_annual"):
            v = getattr(self, name)
            if not math.isfinite(v) or v < 0:
                raise ValueError(f"{name} must be finite and >= 0")
        if not 0 < self.max_participation <= 1:
            raise ValueError("max_participation must be in (0, 1]")
        if self.partial_fill_policy not in {"matched", "independent"}:
            raise ValueError("partial_fill_policy must be matched or independent")

    def half_spread(self, ticker: str) -> float:
        return self.half_spread_bps.get(ticker, self.default_half_spread_bps) / 1e4


def trailing_inputs(panel: Panel, log_tr: pd.DataFrame, window: int = 20) -> tuple[pd.DataFrame, pd.DataFrame]:
    """sigma20 (daily log TR return sd) and ADV20 (unadjusted shares) over the ``window`` days ending at each close.

    Volumes before a split are converted to post-split shares so ADV is in the units of the next order.
    """
    sigma = log_tr.diff().rolling(window).std(ddof=1)
    later_splits = panel.split_ratio[::-1].cumprod()[::-1].shift(-1).fillna(1.0)  # product of splits after date
    # shares of day s expressed in shares as of date t: multiply by product of splits in (s, t]
    vol_post = panel.volume * later_splits  # in "final" shares
    adv_final = vol_post.rolling(window).mean()
    adv = adv_final / later_splits  # back to shares as of each date t
    return sigma, adv


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

def _ts(date: pd.Timestamp, at: pd.Timedelta) -> pd.Timestamp:
    return (pd.Timestamp(date) + at).tz_localize(TZ)


@dataclass
class PairLedger:
    """Cash + two share positions with explicit financing intervals and corporate actions."""
    y: str
    x: str
    cash: float
    time: pd.Timestamp
    shares: dict[str, float] = field(default_factory=dict)
    marks: dict[str, float] = field(default_factory=dict)  # last available mark (close or fill-time open)
    events: list[dict[str, Any]] = field(default_factory=list)
    totals: dict[str, float] = field(default_factory=lambda: {
        "interest": 0.0, "borrow": 0.0, "dividends": 0.0, "commission": 0.0, "trade_flow": 0.0,
        "spread_cost": 0.0, "impact_cost": 0.0})

    def __post_init__(self) -> None:
        self.shares = {self.y: 0.0, self.x: 0.0}
        self.initial_cash = self.cash

    def nav(self) -> float:
        return self.cash + sum(q * self.marks[t] for t, q in self.shares.items() if q != 0)

    def accrue(self, to: pd.Timestamp, policy_rate: float, sc: CostScenario) -> None:
        if to < self.time:
            raise ValueError("ledger clock cannot move backwards")
        days = (to - self.time).total_seconds() / 86400.0
        if days <= 0:
            return
        rate = policy_rate - sc.credit_spread if self.cash >= 0 else policy_rate + sc.debit_spread
        interest = self.cash * rate * days / 360.0
        borrow = sum(-q * self.marks[t] for t, q in self.shares.items() if q < 0) * sc.borrow_fee_annual * days / 360.0
        self.events.append({"time": to, "type": "ACCRUAL", "interval_start": self.time, "days": days,
                            "cash_before": self.cash, "rate": rate, "interest": interest, "borrow": borrow,
                            "short_value_basis": sum(-q * self.marks[t] for t, q in self.shares.items() if q < 0)})
        self.cash += interest - borrow
        self.totals["interest"] += interest
        self.totals["borrow"] += borrow
        self.time = to

    def corporate_actions(self, when: pd.Timestamp, split: dict[str, float], div: dict[str, float]) -> None:
        for t in (self.y, self.x):
            r, d = split[t], div[t]
            if r != 1.0:
                before = self.shares[t]
                self.shares[t] = _split_shares(before, r)
                if t in self.marks:
                    self.marks[t] /= r
                self.events.append({"time": when, "type": "SPLIT", "ticker": t, "ratio": r,
                                    "shares_before": before, "shares_after": self.shares[t]})
            if d != 0.0 and self.shares[t] != 0:
                amt = self.shares[t] * d
                self.cash += amt
                self.totals["dividends"] += amt
                self.events.append({"time": when, "type": "DIVIDEND", "ticker": t, "per_share": d,
                                    "shares": self.shares[t], "cash": amt})

    def open_marks(self, when: pd.Timestamp, opens: dict[str, float]) -> None:
        """09:30 open prices become the available marks for both legs (after corporate actions, before fills)."""
        self.marks.update(opens)
        self.events.append({"time": when, "type": "OPEN_MARK", **{f"mark_{t}": p for t, p in opens.items()},
                            **{f"shares_{t}": q for t, q in self.shares.items()}})

    def fill(self, when: pd.Timestamp, ticker: str, qty: float, mid: float, price: float, commission: float,
             spread_cost: float, impact_cost: float, order_id: str) -> None:
        flow = qty * price
        self.cash -= flow + commission
        self.shares[ticker] += qty
        self.marks[ticker] = mid
        for k, v in (("trade_flow", flow), ("commission", commission), ("spread_cost", spread_cost),
                     ("impact_cost", impact_cost)):
            self.totals[k] += v
        self.events.append({"time": when, "type": "FILL", "ticker": ticker, "qty": qty, "mid": mid,
                            "price": price, "commission": commission, "order_id": order_id})

    def mark(self, when: pd.Timestamp, closes: dict[str, float]) -> float:
        self.marks.update(closes)
        nav = self.nav()
        self.events.append({"time": when, "type": "MARK", "cash": self.cash, **{f"shares_{t}": q for t, q in
                            self.shares.items()}, "nav": nav})
        return nav

    def cash_residual(self) -> float:
        t = self.totals
        expected = self.initial_cash + t["interest"] - t["borrow"] + t["dividends"] - t["trade_flow"] - t["commission"]
        return self.cash - expected


# ---------------------------------------------------------------------------
# Pair simulation across walk-forward windows
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Window:
    k: int
    formation_start: pd.Timestamp
    formation_end: pd.Timestamp
    signal_dates: pd.DatetimeIndex  # closes at which a state is computed (formation_end .. last-1 of window)


def make_windows(dates: pd.DatetimeIndex, formation: int, trading: int, step: int) -> list[Window]:
    out, end_idx, k = [], formation - 1, 0
    while end_idx + trading < len(dates):
        sig = dates[end_idx:end_idx + trading]  # closes F..F+trading-1; last forced flat -> exit at open F+trading
        out.append(Window(k, dates[end_idx - formation + 1], dates[end_idx], sig))
        end_idx += step
        k += 1
    return out


def _split_entitlement(shares: float, ratio: float) -> Fraction:
    """Exact entitlement for the decimal values represented by the input floats."""
    return Fraction(str(shares)) * Fraction(str(ratio))


def _split_shares(shares: float, ratio: float) -> float:
    entitlement = _split_entitlement(shares, ratio)
    try:
        converted = float(entitlement)
    except OverflowError as exc:
        raise ValueError("split quantity exceeds float support") from exc
    if entitlement.denominator == 1 and Fraction(converted) != entitlement:
        raise ValueError("integer split quantity is not exactly representable as float")
    return converted


def _round_to_zero(x: float) -> float:
    return float(math.trunc(x))


def simulate_pair(panel: Panel, log_tr: pd.DataFrame, rates: pd.Series, pair: str, y: str, x: str,
                  windows: list[Window], formations: dict[int, Formation], active: dict[int, bool],
                  rule: SignalRule, sc: CostScenario, w0: float, gross: float = 1.0) -> dict[str, Any]:
    """Run one pair ledger through all windows; inactive windows hold cash. Returns NAV, trades, orders, events."""
    sigma, adv = trailing_inputs(panel, log_tr)
    dates = panel.dates
    pos = {d: i for i, d in enumerate(dates)}
    first = windows[0].formation_end
    led = PairLedger(y=y, x=x, cash=w0, time=_ts(first, CLOSE_TIME))
    nav = {first: w0}
    # desired state per signal close
    desired: dict[pd.Timestamp, tuple[int, int]] = {}
    for w in windows:
        if not active.get(w.k, False):
            for d in w.signal_dates:
                desired[d] = (0, w.k)
            continue
        z = zscores(log_tr, formations[w.k], w.signal_dates)
        st = target_states(z, rule)
        for d, s in st.items():
            desired[d] = (int(s), w.k)
    beta_of = {w.k: formations[w.k].beta for w in windows}
    state = 0
    pending: list[dict[str, Any]] = []  # orders to fill at the next open
    orders: list[dict[str, Any]] = []
    days = dates[pos[first]:pos[windows[-1].signal_dates[-1]] + 2]  # through the open after the last signal
    for i, d in enumerate(days):
        if i == 0:
            led.marks.update({y: panel.close.at[d, y], x: panel.close.at[d, x]})
        else:
            prev = days[i - 1]
            t_open = _ts(d, OPEN_TIME)
            # Whole-share fills cannot settle split-created fractions; reject before changing today's ledger.
            for ticker in (y, x):
                ratio = panel.split_ratio.at[d, ticker]
                entitlement = _split_entitlement(led.shares[ticker], ratio)
                try:
                    post_split = _split_shares(led.shares[ticker], ratio)
                except OverflowError as exc:
                    raise ValueError(f"split holding exceeds float support at {d.date()}: {ticker}") from exc
                if not math.isfinite(post_split) or entitlement.denominator != 1:
                    raise ValueError(
                        f"unsupported fractional holding after split: {pair}/{ticker} at {d.date()} "
                        f"({led.shares[ticker]} shares x {ratio} = {post_split}); requires an explicit fractional-fill or cash-in-lieu policy"
                    )
            led.accrue(t_open, rates.at[prev], sc)  # overnight interval: rate known at the previous close
            split_d = {t: panel.split_ratio.at[d, t] for t in (y, x)}
            div_d = {t: panel.dividend.at[d, t] for t in (y, x)}
            led.corporate_actions(t_open, split_d, div_d)
            led.open_marks(t_open, {y: panel.open.at[d, y], x: panel.open.at[d, x]})
            still = []
            for o in pending:
                if o.get("carried"):  # remainder ordered in yesterday's shares: restate at today's events
                    o = {**o, "delta": {t: _split_shares(q, split_d[t]) for t, q in o["delta"].items()},
                         "decision": {t: p / split_d[t] - div_d[t] for t, p in o["decision"].items()},
                         "arrival": {t: p / split_d[t] - div_d[t] for t, p in o["arrival"].items()}}
                o = _execute(o, d, t_open, panel, sigma, adv, led, sc, orders)
                if o is not None:
                    still.append(o)
            pending = still
            led.accrue(_ts(d, CLOSE_TIME), rates.at[d], sc)  # intraday interval: rate available at today's open
            nav[d] = led.mark(_ts(d, CLOSE_TIME), {y: panel.close.at[d, y], x: panel.close.at[d, x]})
        if d not in desired:
            continue
        want, k = desired[d]
        if want == state:
            continue
        nxt = dates[pos[d] + 1]
        # decision prices restated in the post-event units of the next open
        r_next = {t: panel.split_ratio.at[nxt, t] for t in (y, x)}
        d_next = {t: panel.dividend.at[nxt, t] for t in (y, x)}
        dec = {t: panel.close.at[d, t] / r_next[t] - d_next[t] for t in (y, x)}
        if state != 0:  # target_states only moves +-1 -> 0, so this is always a full exit
            tgt, kind = {t: 0.0 for t in (y, x)}, "exit"
        else:
            beta = beta_of[k]
            wy, wx = want / (1 + abs(beta)), -want * beta / (1 + abs(beta))  # gross |wy|+|wx| = 1 for any sign
            # Round in signal-close share units before converting for the next split; dividends only affect IS.
            tgt = {t: _split_shares(_round_to_zero(w * gross * nav[d] / panel.close.at[d, t]), r_next[t])
                   for t, w in ((y, wy), (x, wx))}
            # every leg that would be sold short needs a locate; with beta < 0 both legs share one sign
            blocked = [t for t in (y, x) if tgt[t] < 0 and (t, nxt) in sc.locate_unavailable]
            if blocked:
                orders.append({"order_id": f"{pair}-{d.date()}-entry", "kind": "entry_skipped",
                               "signal_date": d, "ticker": ",".join(blocked), "reason": "locate unavailable"})
                continue  # state stays flat; the signal is re-evaluated at the next close
            kind = "entry"
        cur = {t: _split_shares(led.shares[t], r_next[t]) for t in (y, x)}
        for o in pending:  # a carried exit remainder is superseded: close its IS record at this decision price
            for t, q in o["delta"].items():
                if q != 0:
                    q_n, arr_n = _split_shares(q, r_next[t]), o["arrival"][t] / r_next[t] - d_next[t]
                    orders.append({"order_id": o["order_id"], "kind": "superseded_remainder",
                                   "signal_date": o["signal_date"], "fill_date": d, "ticker": t,
                                   "attempt_ordered": q_n, "filled": 0.0, "remainder": q_n,
                                   "decision_price": o["decision"][t] / r_next[t] - d_next[t],
                                   "first_arrival_price": arr_n, "is_delay": 0.0, "is_execution": 0.0,
                                   "is_fees": 0.0, "is_opportunity": q_n * (dec[t] - arr_n)})
        # the new order nets against actual holdings, so it replaces the carried remainder
        pending = [{"order_id": f"{pair}-{d.date()}-{kind}", "signal_date": d, "kind": kind, "pair": pair,
                    "delta": {t: tgt[t] - cur[t] for t in (y, x)}, "decision": dec}]
        state = want if kind == "entry" else 0
    last = days[-1]
    for o in pending:  # exit remainders still open when the sample ends: opportunity cost at the last close
        for t, q in o["delta"].items():
            if q != 0:
                arr = o.get("arrival", {}).get(t, panel.close.at[last, t])
                orders.append({"order_id": o["order_id"], "kind": "unfilled_at_end", "signal_date": o["signal_date"],
                               "fill_date": last, "ticker": t, "attempt_ordered": q, "filled": 0.0, "remainder": q,
                               "decision_price": o["decision"][t], "first_arrival_price": arr,
                               "is_delay": 0.0, "is_execution": 0.0, "is_fees": 0.0,
                               "is_opportunity": q * (panel.close.at[last, t] - arr)})
    nav_s = pd.Series(nav).sort_index()
    return {"nav": nav_s, "orders": pd.DataFrame(orders),
            "trades": episodes(led.events, dates, pair, nav_s, {y: panel.close.at[last, y], x: panel.close.at[last, x]}),
            "events": led.events, "totals": dict(led.totals), "cash_residual": led.cash_residual(),
            "final_shares": dict(led.shares), "unfilled_pending": pending}


def _execute(o: dict[str, Any], d: pd.Timestamp, t_open: pd.Timestamp, panel: Panel, sigma: pd.DataFrame,
             adv: pd.DataFrame, led: PairLedger, sc: CostScenario, orders: list) -> dict[str, Any] | None:
    """Fill (part of) an order at the open of d. Returns the carried remainder (exits only) or None."""
    prev = panel.dates[panel.dates.get_loc(d) - 1]
    want = {t: q for t, q in o["delta"].items() if q != 0}
    if not want:
        return None
    # ex-ante budget: ADV20 as of the signal close, in the fill day's post-split shares (never the fill day's volume)
    cap = {t: sc.max_participation * adv.at[prev, t] * panel.split_ratio.at[d, t] for t in want}
    if not all(np.isfinite(c) for c in cap.values()):
        raise ValueError(f"ADV20 not available at {prev.date()} for an order filling {d.date()}")
    frac = {t: min(1.0, cap[t] / abs(q)) for t, q in want.items()}
    if sc.partial_fill_policy == "matched":
        f = min(frac.values())
        frac = {t: f for t in want}
    filled = {}
    for t, q in want.items():
        qf = _round_to_zero(q * frac[t])
        mid = panel.open.at[d, t]
        side = 1.0 if qf > 0 else -1.0
        hs = sc.half_spread(t)
        s20, a20 = sigma.at[prev, t], adv.at[prev, t] * panel.split_ratio.at[d, t]
        imp = sc.eta * s20 * math.sqrt(abs(qf) / a20) if qf != 0 and np.isfinite(s20) and a20 > 0 else 0.0
        price = mid * (1 + side * (hs + imp))
        comm = sc.commission_per_share * abs(qf)
        if qf != 0:
            led.fill(t_open, t, qf, mid, price, comm, abs(qf) * mid * hs, abs(qf) * mid * imp, o["order_id"])
        filled[t] = qf
        dec = o["decision"][t]
        first = "arrival" not in o
        arr = mid if first else o["arrival"][t]
        # Chapter 36 IS with one arrival price per parent order: delay once on the full parent quantity, every fill
        # against that first arrival, the cancelled/unfilled remainder as opportunity (zero when cancelled at arrival)
        orders.append({"order_id": o["order_id"], "kind": o["kind"], "signal_date": o["signal_date"],
                       "fill_date": d, "ticker": t, "attempt_ordered": q, "filled": qf, "remainder": q - qf,
                       "decision_price": dec, "first_arrival_price": arr, "open_price": mid, "fill_price": price,
                       "commission": comm, "is_delay": q * (arr - dec) if first else 0.0,
                       "is_execution": qf * (price - arr), "is_fees": comm,
                       "is_opportunity": 0.0, "budget_adv20": cap[t],
                       # post-close diagnostics only: known after 16:00, never used for the 09:30 fill
                       "day_volume_diag": panel.volume.at[d, t],
                       "day_participation_diag": abs(qf) / panel.volume.at[d, t] if panel.volume.at[d, t] > 0
                       else float("nan")})
    if "arrival" not in o:
        o = {**o, "arrival": {t: panel.open.at[d, t] for t in o["delta"]}}
    rem = {t: o["delta"][t] - filled.get(t, 0.0) for t in o["delta"]}
    if all(v == 0 for v in rem.values()):
        return None
    if o["kind"] == "exit":
        return {**o, "delta": rem, "carried": True}  # an exit is never cancelled: retried at the next open
    return None  # entry remainder cancelled (logged in orders)


# ---------------------------------------------------------------------------
# Episodes (closed-trade statistics)
# ---------------------------------------------------------------------------

def episodes(events: list[dict[str, Any]], dates: pd.DatetimeIndex, pair: str, nav: pd.Series,
             last_close: dict[str, float]) -> pd.DataFrame:
    """Position-based episodes: one starts at the first fill that leaves the flat state, ends at the fill that
    returns both legs to zero shares. A new entry order before the position is flat (carried exit remainder)
    belongs to the same episode and is counted in ``entry_orders``. Episode P&L is trading P&L only: fill cash flows
    and commissions, dividends and borrow fees while the episode is open; cash interest is excluded. An episode
    still open at the end has status ``open`` and is excluded from the win rate.
    """
    pos = {d: i for i, d in enumerate(dates)}
    shares: dict[str, float] = {}
    rows, cur = [], None
    for e in events:
        typ = e["type"]
        if typ == "SPLIT":
            shares[e["ticker"]] = e["shares_after"]
        if cur is not None and typ == "DIVIDEND":
            cur["dividends"] += e["cash"]
        if cur is not None and typ == "ACCRUAL":
            cur["borrow"] += e["borrow"]
        if typ != "FILL":
            continue
        flat_before = all(abs(q) < 1e-9 for q in shares.values())
        if flat_before:
            cur = {"pair": pair, "start": e["time"], "fill_flow": 0.0, "commission": 0.0, "dividends": 0.0,
                   "borrow": 0.0, "order_ids": set(), "entry_orders": set(), "first_signs": {}}
        shares[e["ticker"]] = shares.get(e["ticker"], 0.0) + e["qty"]
        cur["fill_flow"] -= e["qty"] * e["price"]
        cur["commission"] += e["commission"]
        cur["order_ids"].add(e["order_id"])
        if e["order_id"].endswith("-entry"):
            cur["entry_orders"].add(e["order_id"])
            cur["first_signs"].setdefault(e["ticker"], float(np.sign(e["qty"])))
        if all(abs(q) < 1e-9 for q in shares.values()):
            rows.append(_close_episode(cur, e["time"], pos, "closed", 0.0))
            cur = None
    if cur is not None:
        mtm = sum(q * last_close[t] for t, q in shares.items())
        rows.append(_close_episode(cur, nav.index[-1], pos, "open", mtm))
    cols = ["pair", "status", "start_date", "end_date", "holding_days", "calendar_days", "entry_orders",
            "reentries", "same_sign_legs", "fill_flow", "commission", "dividends", "borrow", "open_mtm", "pnl"]
    return pd.DataFrame(rows, columns=cols)


def _close_episode(cur: dict[str, Any], end: pd.Timestamp, pos: dict, status: str, mtm: float) -> dict[str, Any]:
    start_d = pd.Timestamp(cur["start"]).tz_localize(None).normalize()
    end_d = pd.Timestamp(end).tz_localize(None).normalize() if pd.Timestamp(end).tzinfo else pd.Timestamp(end)
    signs = list(cur["first_signs"].values())
    pnl = cur["fill_flow"] - cur["commission"] + cur["dividends"] - cur["borrow"] + mtm
    return {"pair": cur["pair"], "status": status, "start_date": start_d, "end_date": end_d,
            "holding_days": pos[end_d] - pos[start_d], "calendar_days": (end_d - start_d).days,
            "entry_orders": len(cur["entry_orders"]), "reentries": max(len(cur["entry_orders"]) - 1, 0),
            "same_sign_legs": bool(len(signs) == 2 and signs[0] == signs[1]),
            "fill_flow": cur["fill_flow"], "commission": cur["commission"], "dividends": cur["dividends"],
            "borrow": cur["borrow"], "open_mtm": mtm, "pnl": pnl}


def trade_stats(ep: pd.DataFrame) -> dict[str, float]:
    """Closed-episode win rate and holding days; missing (NaN) when there is no closed episode."""
    closed = ep[ep["status"] == "closed"] if len(ep) else ep
    n = int(len(closed))
    return {"closed_trades": n, "open_trades": int(len(ep) - n),
            "win_rate": float((closed["pnl"] > 0).mean()) if n else float("nan"),
            "mean_holding_days": float(closed["holding_days"].mean()) if n else float("nan"),
            "median_holding_days": float(closed["holding_days"].median()) if n else float("nan")}


def turnover_stats(orders: pd.DataFrame, nav: pd.Series) -> dict[str, float]:
    """Executed notional only (never order quantities). Two-sided = sum |filled x fill_price|; one-sided = half of it.
    Annualised turnover = one-sided notional / mean daily NAV x 252 / N returns."""
    n = len(nav) - 1
    if len(orders) and "fill_price" in orders:
        f = orders[orders["filled"].fillna(0) != 0]
        notional = float((f["filled"].abs() * f["fill_price"]).sum())
    else:
        notional = 0.0
    mean_nav = float(nav.mean())
    return {"traded_notional_two_sided": notional,
            "turnover_one_sided_ann": 0.5 * notional / mean_nav * 252 / n if n > 0 else float("nan")}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def nav_metrics(nav: pd.Series, credit_rate: pd.Series | None = None) -> dict[str, float]:
    """N+1 NAV marks -> N simple returns. Sharpe on excess over the daily credit rate when given."""
    r = nav.pct_change().dropna()
    out = {"n_returns": int(len(r)), "total_return": float(nav.iloc[-1] / nav.iloc[0] - 1),
           "ann_return": float((nav.iloc[-1] / nav.iloc[0]) ** (252 / len(r)) - 1) if len(r) else float("nan"),
           "ann_vol": float(r.std(ddof=1) * math.sqrt(252)) if len(r) > 1 else float("nan")}
    if credit_rate is None:
        ex = r
    else:  # cash benchmark for each interval: credit rate known at its start, ACT/360
        days = np.diff(nav.index.values).astype("timedelta64[D]").astype(float)
        ex = r - credit_rate.reindex(nav.index[:-1]).to_numpy() * days / 360.0
    sd = ex.std(ddof=1)
    out["sharpe_excess"] = float(ex.mean() / sd * math.sqrt(252)) if sd > 0 else float("nan")
    out["max_drawdown"] = float((nav / nav.cummax() - 1).min())
    return out
