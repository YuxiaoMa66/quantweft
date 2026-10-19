"""Derivatives pricing and discrete hedging module.

Part of Chapter 44: Stochastic Calculus and Derivatives.
Implements:
- Black-Scholes-Merton analytic pricing and Greeks with continuous dividend yield q.
- Cox-Ross-Rubinstein (CRR) binomial tree option pricing with strict no-arbitrage validation.
- Risk-neutral terminal Monte Carlo pricing with antithetic variates and paired standard error.
- Discrete delta hedging ledger with dividend accounting, interest accrual, and transaction costs.
"""

from typing import Any, Dict, List, Optional, Union
import math
import numpy as np
from scipy.stats import norm

# Standard 95% normal critical value specified by protocol
Z_CRIT_95: float = 1.95996398454


def _bs_standardized_terms(S: float, K: float, T: float, r: float, q: float, sigma: float) -> tuple[float, float, float]:
    """Compute shared d1/d2 only inside the finite float64 intermediate domain."""
    S, K, T, r, q, sigma = map(float, (S, K, T, r, q, sigma))
    variance = sigma * sigma
    if not math.isfinite(variance):
        raise ValueError("BS float64 domain requires finite sigma squared; variance exceeds floating-point range")
    if not math.isfinite(variance * T):
        raise ValueError("BS float64 time-scaled variance exceeds floating-point range")
    sqrt_T = math.sqrt(T)
    vol = sigma * sqrt_T
    rate_term = r - q + 0.5 * sigma * sigma
    time_term = rate_term * T
    numerator = (math.log(S) - math.log(K)) + time_term
    if vol <= 0 or not all(math.isfinite(x) for x in (sqrt_T, vol, rate_term, time_term, numerator)):
        raise ValueError("BS float64 standardized intermediate is not finite or denominator underflowed")
    d1 = numerator / vol
    d2 = d1 - vol
    if not (math.isfinite(d1) and math.isfinite(d2)):
        raise ValueError("BS float64 d1/d2 exceed floating-point range")
    return sqrt_T, d1, d2


def _validate_common_params(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    kind: str,
) -> str:
    """Validate common parameters across pricing and Greeks functions."""
    for name, value in [("S", S), ("K", K), ("T", T), ("r", r), ("q", q), ("sigma", sigma)]:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
            raise ValueError(f"{name} must be a real scalar")
    if not isinstance(kind, str):
        raise ValueError("kind must be call or put")
    if not (np.isfinite(S) and np.isfinite(K)):
        raise ValueError(f"S and K must be finite real numbers. Got S={S}, K={K}.")
    if S <= 0.0 or K <= 0.0:
        raise ValueError(f"S and K must be strictly positive. Got S={S}, K={K}.")
    if not (np.isfinite(T) and np.isfinite(sigma)):
        raise ValueError(f"T and sigma must be finite real numbers. Got T={T}, sigma={sigma}.")
    if T < 0.0:
        raise ValueError(f"T (time to maturity) cannot be negative. Got T={T}.")
    if sigma < 0.0:
        raise ValueError(f"sigma (volatility) cannot be negative. Got sigma={sigma}.")
    if not (np.isfinite(r) and np.isfinite(q)):
        raise ValueError(f"r and q must be finite real numbers. Got r={r}, q={q}.")

    k = kind.lower().strip()
    if k not in ("call", "put"):
        raise ValueError(f"Option kind must be 'call' or 'put'. Got kind='{kind}'.")
    return k


@np.errstate(over="raise", invalid="raise", divide="raise")
def bs_price(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    kind: str = "call",
) -> float:
    """Black-Scholes-Merton European option price with continuous dividend yield q.

    Parameters
    ----------
    S : float
        Current underlying asset price (strictly positive).
    K : float
        Strike price (strictly positive).
    T : float
        Time to maturity in years (non-negative).
    r : float
        Continuous risk-free interest rate (can be negative, zero, or positive).
    q : float
        Continuous dividend yield (real number).
    sigma : float
        Annualized volatility (non-negative).
    kind : str, default 'call'
        Option type, 'call' or 'put'.

    Returns
    -------
    float
        Theoretical European option price.

    Positive-time stochastic prices require finite float64 sigma squared,
    sigma squared times T, and actual standardized-formula intermediates/d1/d2,
    with a positive representable sigma*sqrt(T) denominator.
    Unsupported intermediates are explicitly rejected rather than returning a finite
    but incorrect price. At tiny positive volatility/time, CDF subtraction can
    lose relative accuracy for near-zero prices; use an absolute currency tolerance.
    """
    k = _validate_common_params(S, K, T, r, q, sigma, kind)

    # Boundary: at expiration (T == 0), option price equals intrinsic value.
    if T == 0.0:
        if k == "call":
            return float(max(S - K, 0.0))
        else:
            return float(max(K - S, 0.0))

    # Boundary: zero volatility (sigma == 0), deterministic forward asset price.
    # Forward price under Q is F = S * exp((r - q) * T).
    # Discounted payoff is exp(-r*T) * max(F - K, 0) = max(S*exp(-q*T) - K*exp(-r*T), 0).
    if sigma == 0.0:
        df_q = math.exp(-q * T)
        df_r = math.exp(-r * T)
        if k == "call":
            return float(max(S * df_q - K * df_r, 0.0))
        else:
            return float(max(K * df_r - S * df_q, 0.0))

    sqrt_T, d1, d2 = _bs_standardized_terms(S, K, T, r, q, sigma)

    df_q = math.exp(-q * T)
    df_r = math.exp(-r * T)

    if k == "call":
        price = S * df_q * norm.cdf(d1) - K * df_r * norm.cdf(d2)
    else:
        price = K * df_r * norm.cdf(-d2) - S * df_q * norm.cdf(-d1)

    if not np.isfinite(price):
        raise ValueError("price exceeds floating-point range")
    return float(price)


@np.errstate(over="raise", invalid="raise", divide="raise")
def bs_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    kind: str = "call",
) -> Dict[str, float]:
    """Analytical Greeks for Black-Scholes-Merton model with continuous dividend yield q.

    Units and conventions:
    - delta: dV/dS (dimensionless)
    - gamma: d²V/dS² (per currency of underlying price)
    - vega: dV/dsigma (currency per unit volatility, NOT per 1 percentage point)
    - theta: dV/dt = -dV/dtau (currency per year, calendar time derivative)
    - rho: dV/dr (currency per unit rate, NOT per 1%)

    Rejection policy:
    Ordinary derivatives are undefined or discontinuous at the payoff kink at expiration (T=0)
    or in deterministic limit (sigma=0). Greeks are explicitly rejected when T <= 0 or sigma <= 0.
    Positive-time Greeks share bs_price's finite float64 variance, time-scaled
    variance and standardized intermediate/d1/d2 domain, with a positive
    representable sigma*sqrt(T) denominator. Later floating range failures still raise.

    Parameters
    ----------
    S, K, T, r, q, sigma, kind : see `bs_price`.

    Returns
    -------
    dict
        Dictionary with keys 'delta', 'gamma', 'vega', 'theta', 'rho'.
    """
    k = _validate_common_params(S, K, T, r, q, sigma, kind)

    if T <= 0.0:
        raise ValueError(
            f"Greeks API requires positive time to maturity (T={T}). "
            "The payoff function has a non-differentiable kink at S=K."
        )
    if sigma <= 0.0:
        raise ValueError(
            f"Greeks API requires positive volatility (sigma={sigma}). "
            "Deterministic Greeks outside the payoff kink are not implemented."
        )

    sqrt_T, d1, d2 = _bs_standardized_terms(S, K, T, r, q, sigma)

    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_d2 = norm.cdf(d2)

    df_q = math.exp(-q * T)
    df_r = math.exp(-r * T)

    gamma = df_q * pdf_d1 / (S * sigma * sqrt_T)
    vega = S * df_q * sqrt_T * pdf_d1

    if k == "call":
        delta = df_q * cdf_d1
        # theta = dV/dt = -dV/dtau
        theta = (
            - (S * df_q * pdf_d1 * sigma) / (2.0 * sqrt_T)
            + q * S * df_q * cdf_d1
            - r * K * df_r * cdf_d2
        )
        rho = K * T * df_r * cdf_d2
    else:
        delta = - df_q * norm.cdf(-d1)  # = df_q * (cdf_d1 - 1.0)
        theta = (
            - (S * df_q * pdf_d1 * sigma) / (2.0 * sqrt_T)
            - q * S * df_q * norm.cdf(-d1)
            + r * K * df_r * norm.cdf(-d2)
        )
        rho = - K * T * df_r * norm.cdf(-d2)

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega),
        "theta": float(theta),
        "rho": float(rho),
    }


@np.errstate(over="raise", invalid="raise", divide="raise")
def crr_price(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    kind: str = "call",
    steps: int = 100,
) -> float:
    """Cox-Ross-Rubinstein (CRR) binomial tree European option price.

    Uses continuous dividend adjustment:
    dt = T / steps
    u = exp(sigma * sqrt(dt)), d = 1 / u
    a = exp((r - q) * dt)
    p = (a - d) / (u - d)

    Strict no-arbitrage rule:
    If risk-neutral probability p is not strictly within [0, 1], this function
    refuses and raises ValueError. It NEVER clips p silently!

    Parameters
    ----------
    S, K, T, r, q, sigma, kind : see `bs_price`.
    steps : int, default 100
        Number of time steps in the binomial lattice. Must be positive integer.

    Returns
    -------
    float
        CRR binomial tree option price.
    """
    k = _validate_common_params(S, K, T, r, q, sigma, kind)

    if isinstance(steps, (bool, np.bool_)) or not isinstance(steps, (int, np.integer)):
        raise ValueError(f"steps must be an integer. Got type={type(steps).__name__}.")
    if steps <= 0:
        raise ValueError(f"steps must be strictly positive. Got steps={steps}.")

    if T == 0.0:
        return bs_price(S, K, 0.0, r, q, sigma, kind=k)

    if sigma == 0.0:
        return bs_price(S, K, T, r, q, 0.0, kind=k)

    dt = T / steps
    u = math.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    a = math.exp((r - q) * dt)

    denom = u - d
    if denom <= 0.0:
        raise ValueError(f"Degenerate CRR step geometry: u - d = {denom}.")

    p = (a - d) / denom

    # Protocol constraint: tree risk-neutral probability p invalid must be rejected, NEVER clipped!
    if p <= 0.0 or p >= 1.0 or not np.isfinite(p):
        raise ValueError(
            f"CRR risk-neutral probability p={p:.6f} must be strictly inside (0, 1). "
            f"The lattice permits arbitrage under step size dt={dt:.6f}. "
            "Refuse execution instead of silent clipping."
        )

    # Terminal stock prices at step N:
    # S_j = S * (u ** j) * (d ** (steps - j)) for j in 0..steps
    j_indices = np.arange(steps + 1)
    S_terminal = S * (u ** j_indices) * (d ** (steps - j_indices))

    if k == "call":
        values = np.maximum(S_terminal - K, 0.0)
    else:
        values = np.maximum(K - S_terminal, 0.0)

    df_step = math.exp(-r * dt)
    q_prob = 1.0 - p

    for _ in range(steps, 0, -1):
        values = df_step * (p * values[1:] + q_prob * values[:-1])

    return float(values[0])


@np.errstate(over="raise", invalid="raise", divide="raise")
def mc_price(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    kind: str = "call",
    pairs: int = 50000,
    seed: Optional[int] = 4401,
    antithetic: bool = True,
) -> Dict[str, Union[float, int]]:
    """European option pricing under Q measure using Monte Carlo terminal simulation.

    When antithetic=True, simulates `pairs` pairs of antithetic Brownian paths:
    Z_i and -Z_i. The pair mean X_i = 0.5 * (Y_i^+ + Y_i^-) forms the i.i.d.
    sample unit. Standard error and 95% CI are computed from these `pairs` independent
    pair observations.

    When antithetic=False, simulates `pairs` independent standard normal samples.

    When sigma=0 or T=0, the terminal value is deterministic, so SE=0 and
    confidence interval collapses to the exact price.

    Parameters
    ----------
    S, K, T, r, q, sigma, kind : see `bs_price`.
    pairs : int, default 50000
        Number of independent sample units (antithetic pairs or standard paths).
    seed : int, optional, default 4401
        Non-negative integer (excluding bool) or None. Uses isolated np.random.default_rng.
    antithetic : bool, default True
        Whether to employ antithetic variates for variance reduction.

    Returns
    -------
    dict
        'price': float
        'se': float (standard error of the mean)
        'ci_low': float (95% CI lower bound)
        'ci_high': float (95% CI upper bound)
        'independent_samples': int (effective number of independent observations)
    """
    k = _validate_common_params(S, K, T, r, q, sigma, kind)

    if seed is not None:
        if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)):
            raise ValueError("seed must be a non-negative integer or None, excluding bool")
        if seed < 0:
            raise ValueError("seed must be non-negative")
    if isinstance(pairs, (bool, np.bool_)) or not isinstance(pairs, (int, np.integer)):
        raise ValueError(f"pairs must be an integer. Got type={type(pairs).__name__}.")
    if pairs <= 0:
        raise ValueError(f"pairs must be strictly positive. Got pairs={pairs}.")

    if not isinstance(antithetic, (bool, np.bool_)):
        raise ValueError("antithetic must be boolean")
    if T > 0 and sigma > 0 and pairs < 2:
        raise ValueError("at least two independent random observations are required to estimate SE")

    # Deterministic limit: T=0 or sigma=0
    if T == 0.0 or sigma == 0.0:
        exact = bs_price(S, K, T, r, q, sigma, kind=k)
        return {
            "price": float(exact),
            "se": 0.0,
            "ci_low": float(exact),
            "ci_high": float(exact),
            "independent_samples": int(pairs),
        }

    rng = np.random.default_rng(seed)
    drift = (r - q - 0.5 * sigma * sigma) * T
    vol_sqrt_T = sigma * np.sqrt(T)
    df_r = math.exp(-r * T)

    if antithetic:
        z = rng.standard_normal(pairs)
        st_pos = S * np.exp(drift + vol_sqrt_T * z)
        st_neg = S * np.exp(drift - vol_sqrt_T * z)

        if k == "call":
            payoff_pos = df_r * np.maximum(st_pos - K, 0.0)
            payoff_neg = df_r * np.maximum(st_neg - K, 0.0)
        else:
            payoff_pos = df_r * np.maximum(K - st_pos, 0.0)
            payoff_neg = df_r * np.maximum(K - st_neg, 0.0)

        # Antithetic pair mean is the independent random variable
        sample_obs = 0.5 * (payoff_pos + payoff_neg)
        independent_samples = int(pairs)
    else:
        z = rng.standard_normal(pairs)
        st = S * np.exp(drift + vol_sqrt_T * z)
        if k == "call":
            sample_obs = df_r * np.maximum(st - K, 0.0)
        else:
            sample_obs = df_r * np.maximum(K - st, 0.0)
        independent_samples = int(pairs)

    if not np.all(np.isfinite(sample_obs)):
        raise ValueError("MC payoffs exceed floating-point range")
    mean_price = float(np.mean(sample_obs))
    if independent_samples > 1:
        sample_var = float(np.var(sample_obs, ddof=1))
        se = float(np.sqrt(sample_var / independent_samples))
    else:
        se = 0.0

    ci_low = float(mean_price - Z_CRIT_95 * se)
    ci_high = float(mean_price + Z_CRIT_95 * se)

    return {
        "price": mean_price,
        "se": se,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "independent_samples": independent_samples,
    }


@np.errstate(over="raise", invalid="raise", divide="raise")
def delta_hedge(
    S_path: Union[List[float], np.ndarray],
    T: float,
    r: float,
    q: float,
    sigma: float,
    K: float,
    kind: str = "call",
    cost_rate: float = 0.0,
) -> Dict[str, Any]:
    """Discrete delta hedging simulation along a given underlying asset price path.

    Accounting and convention (Protocol specification):
    - Strictly uses left-point information for hedging decision.
    - Initial step 0:
        Initial wealth W_0 equals option theoretical price V_0 = bs_price(S_0, K, T, ...).
        Initial delta_0 = bs_greeks(S_0, ...)['delta'].
        Initial stock purchase: delta_0 shares at S_0.
        Initial transaction cost: cost_rate * abs(delta_0) * S_0.
        Initial cash: A_0 = V_0 - delta_0 * S_0 - cost_0.
        Initial portfolio value: W_0 = delta_0 * S_0 + A_0 = V_0 - cost_0.
    - Intermediate steps (step k -> step k+1):
        At the right endpoint of the subinterval dt:
        Cash before rebalancing earns interest and collects continuous stock dividend:
            A_{k+1}^{pre} = A_k * exp(r * dt) + delta_k * S_k * (exp(q * dt) - 1).
        New target delta calculated using left-point info at t_{k+1} (remaining time tau = T - t_{k+1}):
            delta_{k+1} = bs_greeks(S_{k+1}, K, tau, ...)['delta'].
        Stock change: delta_change = delta_{k+1} - delta_k.
        Transaction fee: cost = cost_rate * abs(delta_change) * S_{k+1}.
        Cash after rebalancing:
            A_{k+1} = A_{k+1}^{pre} - delta_change * S_{k+1} - cost.
        Portfolio value:
            W_{k+1} = delta_{k+1} * S_{k+1} + A_{k+1}.
    - Final maturity step N:
        Pre-liquidation cash:
            A_N^{pre} = A_{N-1} * exp(r * dt) + delta_{N-1} * S_{N-1} * (exp(q * dt) - 1).
        Liquidate all shares to zero:
            delta_change = 0 - delta_{N-1}.
        Liquidation fee: cost = cost_rate * abs(delta_{N-1}) * S_N.
        Final cash (terminal wealth):
            A_N = A_N^{pre} + delta_{N-1} * S_N - cost.
        Final stock: delta_N = 0.
        Option payoff: H_T = max(S_N - K, 0) for call, max(K - S_N, 0) for put.
        Tracking error: error = A_N - H_T (terminal portfolio wealth minus option payoff).
        Total cost: sum of all transaction fees (initial, rebalancing, and liquidation).

    Parameters
    ----------
    S_path : array-like of shape (N+1,)
        Sequence of stock prices along the discrete timeline. Must have len >= 2.
    T : float
        Total time horizon in years.
    r, q, sigma, K, kind : see `bs_price`.
    cost_rate : float, default 0.0
        Single-sided proportional transaction cost rate (e.g. 0.001 = 10 bps).

    Returns
    -------
    dict
        'ledger': list of dicts, detailed audit trail of each rebalancing step.
        'error': float, final replication tracking error (W_T - H_T).
        'total_cost': float, sum of all transaction costs incurred.
    """
    path = np.asarray(S_path, dtype=float)
    if path.ndim != 1:
        raise ValueError(f"S_path must be a 1D array. Got ndim={path.ndim}.")
    if len(path) < 2:
        raise ValueError(f"S_path must contain at least 2 price observations. Got len={len(path)}.")
    if not np.all(np.isfinite(path)):
        raise ValueError("S_path contains non-finite values (NaN or Inf).")
    if np.any(path <= 0.0):
        raise ValueError("S_path contains non-positive stock prices.")

    if not np.isfinite(cost_rate) or cost_rate < 0.0:
        raise ValueError(f"cost_rate must be a non-negative finite real number. Got {cost_rate}.")

    k = _validate_common_params(path[0], K, T, r, q, sigma, kind)
    if T <= 0.0 or sigma <= 0.0:
        raise ValueError("delta_hedge requires T > 0 and sigma > 0 for dynamic hedging.")

    num_steps = len(path) - 1
    dt = T / num_steps

    # Step 0: initialization
    S_0 = float(path[0])
    v_0 = bs_price(S_0, K, T, r, q, sigma, kind=k)
    greeks_0 = bs_greeks(S_0, K, T, r, q, sigma, kind=k)
    delta_0 = float(greeks_0["delta"])

    initial_cost = float(cost_rate * abs(delta_0) * S_0)
    initial_trade_cf = float(-delta_0 * S_0)
    cash_0 = float(v_0 + initial_trade_cf - initial_cost)
    stock_val_0 = float(delta_0 * S_0)
    port_val_0 = float(stock_val_0 + cash_0)

    ledger: List[Dict[str, float]] = [
        {
            "step": 0,
            "t": 0.0,
            "S": S_0,
            "delta": delta_0,
            "delta_change": delta_0,
            "cash_pre": float(v_0),
            "interest": 0.0,
            "dividend": 0.0,
            "trade_cash_flow": initial_trade_cf,
            "cost": initial_cost,
            "cash": cash_0,
            "stock_value": stock_val_0,
            "portfolio_value": port_val_0,
            "option_value": float(v_0),
        }
    ]

    curr_delta = delta_0
    curr_cash = cash_0
    curr_S = S_0
    total_cost = initial_cost

    # Intermediate steps 1 to num_steps - 1
    for step_idx in range(1, num_steps):
        t_now = step_idx * dt
        tau_remaining = T - t_now
        S_now = float(path[step_idx])

        # Accrual from left interval (step_idx - 1 -> step_idx)
        interest_accrued = float(curr_cash * (math.exp(r * dt) - 1.0))
        dividend_accrued = float(curr_delta * curr_S * (math.exp(q * dt) - 1.0))
        cash_pre = float(curr_cash * math.exp(r * dt) + curr_delta * curr_S * (math.exp(q * dt) - 1.0))

        # Rebalance target using left point info at t_now
        greeks_now = bs_greeks(S_now, K, tau_remaining, r, q, sigma, kind=k)
        new_delta = float(greeks_now["delta"])
        delta_change = float(new_delta - curr_delta)

        rebal_cost = float(cost_rate * abs(delta_change) * S_now)
        rebal_trade_cf = float(-delta_change * S_now)

        curr_cash = float(cash_pre + rebal_trade_cf - rebal_cost)
        curr_delta = new_delta
        curr_S = S_now
        total_cost += rebal_cost

        opt_val = bs_price(S_now, K, tau_remaining, r, q, sigma, kind=k)
        port_val = float(curr_delta * curr_S + curr_cash)

        ledger.append(
            {
                "step": step_idx,
                "t": float(t_now),
                "S": S_now,
                "delta": curr_delta,
                "delta_change": delta_change,
                "cash_pre": cash_pre,
                "interest": interest_accrued,
                "dividend": dividend_accrued,
                "trade_cash_flow": rebal_trade_cf,
                "cost": rebal_cost,
                "cash": curr_cash,
                "stock_value": float(curr_delta * curr_S),
                "portfolio_value": port_val,
                "option_value": float(opt_val),
            }
        )

    # Step num_steps: terminal liquidation
    S_T = float(path[num_steps])
    interest_accrued_T = float(curr_cash * (math.exp(r * dt) - 1.0))
    dividend_accrued_T = float(curr_delta * curr_S * (math.exp(q * dt) - 1.0))
    cash_pre_T = float(curr_cash * math.exp(r * dt) + curr_delta * curr_S * (math.exp(q * dt) - 1.0))

    # Close out all shares
    liq_change = float(0.0 - curr_delta)
    liq_trade_cf = float(curr_delta * S_T)
    liq_cost = float(cost_rate * abs(curr_delta) * S_T)

    final_cash = float(cash_pre_T + liq_trade_cf - liq_cost)
    total_cost += liq_cost

    if k == "call":
        payoff_T = float(max(S_T - K, 0.0))
    else:
        payoff_T = float(max(K - S_T, 0.0))

    error = float(final_cash - payoff_T)

    ledger.append(
        {
            "step": num_steps,
            "t": float(T),
            "S": S_T,
            "delta": 0.0,
            "delta_change": liq_change,
            "cash_pre": cash_pre_T,
            "interest": interest_accrued_T,
            "dividend": dividend_accrued_T,
            "trade_cash_flow": liq_trade_cf,
            "cost": liq_cost,
            "cash": final_cash,
            "stock_value": 0.0,
            "portfolio_value": final_cash,
            "option_value": payoff_T,
        }
    )

    return {
        "ledger": ledger,
        "error": error,
        "total_cost": total_cost,
    }
