"""Teaching-constructed daily panel for Project 5 tests and the data-blocked demo. NOT market data.

Every output carries ``data_class = "constructed"``. Log total-return paths are designed (one cointegrated pair, one
common-trend non-cointegrated pair, one independent pair); unadjusted closes are then derived by removing dividends
and splits, so the panel exercises the same corporate-action code as real data:

    C_t = (C_{t-1} / r_t) * (TR_t / TR_{t-1}) - D_t,   D_t = q * C_{t-1} / r_t on ex-dates,

which makes the forward TR rebuild r_t (C_t + D_t) / C_{t-1} return TR_t / TR_{t-1} exactly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DATA_CLASS = "constructed"


def _derive_prices(tr: np.ndarray, start_price: float, splits: dict[int, float], div_days: set[int],
                   div_yield: float, rng: np.random.Generator) -> tuple[np.ndarray, ...]:
    n = len(tr)
    close, div, ratio = np.empty(n), np.zeros(n), np.ones(n)
    close[0] = start_price
    for t in range(1, n):
        ratio[t] = splits.get(t, 1.0)
        base = close[t - 1] / ratio[t]
        div[t] = div_yield * base if t in div_days else 0.0
        close[t] = base * tr[t] / tr[t - 1] - div[t]
    gap = np.exp(rng.normal(0, 0.002, n))
    opn = np.empty(n)
    opn[0] = close[0]
    opn[1:] = (close[:-1] / ratio[1:] - div[1:]) * gap[1:]
    vol = rng.lognormal(np.log(2e6), 0.3, n)
    vol = vol * np.cumprod(ratio)  # share volume scales with splits
    return opn, close, vol, ratio, div


def constructed_panel(n: int = 1600, seed: int = 20261010) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (long panel, daily rates, truth). Pairs: CA/CB cointegrated (beta 1.2, AR phi 0.97),
    TA/TB common trend not cointegrated, IA/IB independent random walks."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2012-01-03", periods=n)
    common = np.cumsum(rng.normal(0.0002, 0.01, n))
    u = np.zeros(n)
    for t in range(1, n):
        u[t] = 0.97 * u[t - 1] + rng.normal(0, 0.006)
    logs = {
        "CB": common,
        "CA": 0.1 + 1.2 * common + u,
        "TA": np.cumsum(rng.normal(0, 0.01, n)) * 0.5 + common,
        "TB": np.cumsum(rng.normal(0, 0.01, n)) * 0.5 + common,
        "IA": np.cumsum(rng.normal(0.0002, 0.012, n)),
        "IB": np.cumsum(rng.normal(0.0002, 0.012, n)),
    }
    splits = {"CA": {700: 2.0}, "TB": {1100: 3.0}}
    div_days = set(range(40, n, 63))
    rows, start = [], {"CA": 80.0, "CB": 50.0, "TA": 30.0, "TB": 120.0, "IA": 60.0, "IB": 45.0}
    for tk, lg in logs.items():
        tr = np.exp(lg - lg[0])
        o, c, v, r, d = _derive_prices(tr, start[tk], splits.get(tk, {}), div_days, 0.004, rng)
        rows.append(pd.DataFrame({"date": dates, "ticker": tk, "open": o, "close": c, "volume": v,
                                  "split_ratio": r, "dividend": d}))
    panel = pd.concat(rows, ignore_index=True)
    rates = pd.DataFrame({"date": pd.date_range(dates[0] - pd.Timedelta(days=10), dates[-1]),})
    rates["rate"] = 0.02
    truth = {"data_class": DATA_CLASS, "seed": seed, "cointegrated": ["CA", "CB"], "beta_true": 1.2,
             "phi": 0.97, "common_trend_not_cointegrated": ["TA", "TB"], "independent": ["IA", "IB"],
             "splits": {k: {str(dates[i].date()): r for i, r in v.items()} for k, v in splits.items()}}
    return panel, rates, truth
