"""Deep learning foundations and quantitative applications (Chapter 42).

Provides minimal, transparent, pure-NumPy implementations of:
- Multi-Layer Perceptron (MLP) forward pass, analytic MSE+L2 gradients, mini-batch SGD,
  and chronological validation early stopping restoring best weights.
- 1D Convolutional Neural Network (CNN) valid cross-correlation and parameter sharing
  (translation equivariance).
- Recurrent Neural Network (RNN) state recurrence and vanishing gradient product.
- Long Short-Term Memory (LSTM) one-step gating and Constant Error Carousel (CEC).
- Transformer scaled dot-product attention with strict causal upper-triangle masking
  and sinusoidal positional encoding.
- Synthetic panel data generation with UTC-aware timestamps (16:00 UTC) and
  train/validation/test splitting with boundary purging based on actual label availability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _check_finite_2d(arr: Any, name: str) -> np.ndarray:
    """Validate that input is a 2D finite floating-point numpy array."""
    if arr is None:
        raise ValueError(f"{name} must not be None")
    try:
        a = np.asarray(arr, dtype=float)
    except (ValueError, TypeError) as e:
        raise TypeError(f"{name} cannot be converted to float array: {e}") from e

    if a.ndim != 2:
        raise ValueError(f"{name} must be a 2D array, got shape {a.shape}")
    if a.shape[0] == 0 or a.shape[1] == 0:
        raise ValueError(f"{name} must not be empty, got shape {a.shape}")
    if not np.isfinite(a).all():
        raise ValueError(f"{name} contains NaN or infinite values")
    return a


def _check_finite_1d(arr: Any, name: str) -> np.ndarray:
    """Validate that input is a 1D finite floating-point numpy array."""
    if arr is None:
        raise ValueError(f"{name} must not be None")
    try:
        a = np.asarray(arr, dtype=float)
    except (ValueError, TypeError) as e:
        raise TypeError(f"{name} cannot be converted to float array: {e}") from e

    if a.ndim != 1:
        raise ValueError(f"{name} must be a 1D array, got shape {a.shape}")
    if a.size == 0:
        raise ValueError(f"{name} must not be empty")
    if not np.isfinite(a).all():
        raise ValueError(f"{name} contains NaN or infinite values")
    return a


def _check_pos_int(val: Any, name: str, allow_zero: bool = False) -> int:
    """Check that a parameter is a strictly positive (or non-negative) integer."""
    if isinstance(val, (bool, np.bool_)):
        raise TypeError(f"{name} cannot be boolean, got {val}")
    if not isinstance(val, (int, np.integer)):
        raise TypeError(f"{name} must be an integer, got type {type(val).__name__}")
    int_val = int(val)
    if allow_zero:
        if int_val < 0:
            raise ValueError(f"{name} must be >= 0, got {int_val}")
    else:
        if int_val <= 0:
            raise ValueError(f"{name} must be > 0, got {int_val}")
    return int_val


# ---------------------------------------------------------------------------
# MLP Core: Forward, Loss & Gradients, Predict, Fit
# ---------------------------------------------------------------------------

def forward(
    X: np.ndarray,
    W1: np.ndarray,
    b1: np.ndarray,
    W2: np.ndarray,
    b2: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Forward pass of a 2-layer MLP with tanh hidden activation and linear output.

    Parameters
    ----------
    X : np.ndarray, shape (B, D_in)
        Batch of inputs.
    W1 : np.ndarray, shape (D_in, D_hidden)
        First layer weight matrix.
    b1 : np.ndarray, shape (1, D_hidden)
        First layer bias vector.
    W2 : np.ndarray, shape (D_hidden, D_out)
        Second layer weight matrix.
    b2 : np.ndarray, shape (1, D_out)
        Second layer bias vector.

    Returns
    -------
    z1 : np.ndarray, shape (B, D_hidden)
        Hidden layer pre-activations: z1 = X @ W1 + b1.
    a1 : np.ndarray, shape (B, D_hidden)
        Hidden layer activations: a1 = tanh(z1).
    y_hat : np.ndarray, shape (B, D_out)
        Network output predictions: y_hat = a1 @ W2 + b2.
    """
    X_arr = _check_finite_2d(X, "X")
    W1_arr = _check_finite_2d(W1, "W1")
    b1_arr = _check_finite_2d(b1, "b1")
    W2_arr = _check_finite_2d(W2, "W2")
    b2_arr = _check_finite_2d(b2, "b2")

    if X_arr.shape[1] != W1_arr.shape[0]:
        raise ValueError(f"X feature dimension {X_arr.shape[1]} does not match W1 input dimension {W1_arr.shape[0]}")
    if W1_arr.shape[1] != b1_arr.shape[1] or b1_arr.shape[0] != 1:
        raise ValueError(f"b1 shape {b1_arr.shape} must be (1, {W1_arr.shape[1]})")
    if W1_arr.shape[1] != W2_arr.shape[0]:
        raise ValueError(f"W1 hidden dimension {W1_arr.shape[1]} does not match W2 input dimension {W2_arr.shape[0]}")
    if W2_arr.shape[1] != b2_arr.shape[1] or b2_arr.shape[0] != 1:
        raise ValueError(f"b2 shape {b2_arr.shape} must be (1, {W2_arr.shape[1]})")

    z1 = X_arr @ W1_arr + b1_arr
    a1 = np.tanh(z1)
    y_hat = a1 @ W2_arr + b2_arr
    return z1, a1, y_hat


def loss_and_grad(
    X: np.ndarray,
    y: np.ndarray,
    W1: np.ndarray,
    b1: np.ndarray,
    W2: np.ndarray,
    b2: np.ndarray,
    l2_reg: float = 0.0,
) -> tuple[float, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute MSE loss with L2 regularization and exact backpropagation gradients.

    The total loss is defined as:
        L = (1 / (B * D_out)) * ||y_hat - y||_F^2 + l2_reg * (||W1||_F^2 + ||W2||_F^2)
    Note that biases b1 and b2 are not L2-penalized by deliberate design choice.

    Parameters
    ----------
    X : np.ndarray, shape (B, D_in)
        Inputs.
    y : np.ndarray, shape (B, D_out)
        Ground truth targets.
    W1, b1, W2, b2 : np.ndarray
        Model parameters.
    l2_reg : float, default=0.0
        L2 regularization coefficient (must be >= 0).

    Returns
    -------
    total_loss : float
        Scalar loss value.
    dW1 : np.ndarray, shape (D_in, D_hidden)
        Gradient of loss with respect to W1.
    db1 : np.ndarray, shape (1, D_hidden)
        Gradient of loss with respect to b1.
    dW2 : np.ndarray, shape (D_hidden, D_out)
        Gradient of loss with respect to W2.
    db2 : np.ndarray, shape (1, D_out)
        Gradient of loss with respect to b2.
    """
    if isinstance(l2_reg, (bool, np.bool_)):
        raise TypeError(f"l2_reg cannot be boolean, got {l2_reg}")
    if not isinstance(l2_reg, (int, float, np.floating, np.integer)) or not np.isfinite(l2_reg) or l2_reg < 0.0:
        raise ValueError(f"l2_reg must be a non-negative finite float, got {l2_reg}")

    y_arr = _check_finite_2d(y, "y")
    X_arr = _check_finite_2d(X, "X")
    B = X_arr.shape[0]
    if y_arr.shape[0] != B:
        raise ValueError(f"Number of samples in X ({B}) and y ({y_arr.shape[0]}) do not match")

    z1, a1, y_hat = forward(X_arr, W1, b1, W2, b2)
    if y_hat.shape[1] != y_arr.shape[1]:
        raise ValueError(f"Target dimension {y_arr.shape[1]} does not match output dimension {y_hat.shape[1]}")

    diff = y_hat - y_arr
    D_out = y_arr.shape[1]
    # MSE normalized by total elements B * D_out
    mse = float(np.sum(diff ** 2) / (B * D_out))
    l2_penalty = float(l2_reg * (np.sum(W1 ** 2) + np.sum(W2 ** 2)))
    total_loss = mse + l2_penalty
    if not np.isfinite(total_loss):
        raise FloatingPointError("Loss diverged to non-finite value")

    # Backpropagation via chain rule:
    # dL / dy_hat = (2 / (B * D_out)) * diff
    d_yhat = (2.0 / (B * D_out)) * diff

    dW2 = a1.T @ d_yhat + 2.0 * l2_reg * W2
    db2 = np.sum(d_yhat, axis=0, keepdims=True)

    da1 = d_yhat @ W2.T
    dz1 = da1 * (1.0 - a1 ** 2)  # d tanh(z) / dz = 1 - tanh(z)^2

    dW1 = X_arr.T @ dz1 + 2.0 * l2_reg * W1
    db1 = np.sum(dz1, axis=0, keepdims=True)

    return total_loss, dW1, db1, dW2, db2


def predict(
    X: np.ndarray,
    W1: np.ndarray,
    b1: np.ndarray,
    W2: np.ndarray,
    b2: np.ndarray,
) -> np.ndarray:
    """Predict outputs for given inputs using the MLP parameters."""
    _, _, y_hat = forward(X, W1, b1, W2, b2)
    return y_hat


@dataclass
class MLPResult:
    """Container for MLP training results and checkpointed best parameters."""
    W1: np.ndarray
    b1: np.ndarray
    W2: np.ndarray
    b2: np.ndarray
    best_epoch: int
    stopped_epoch: int
    best_val_loss: float
    train_loss_history: list[float]
    val_loss_history: list[float]


def fit_mlp(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    *,
    hidden_dim: int = 8,
    lr: float = 0.01,
    batch_size: int = 32,
    l2_reg: float = 0.001,
    max_epochs: int = 200,
    patience: int = 15,
    seed_init: int = 4202,
    seed_shuffle: int = 4203,
) -> MLPResult:
    """Train a 2-layer MLP using mini-batch SGD and early stopping.

    Monitors validation MSE, saves the checkpoint with the lowest validation MSE,
    and restores that checkpoint upon termination. The test set is never seen or used.

    Parameters
    ----------
    X_train, y_train : np.ndarray
        Training feature and target matrices (2D).
    X_val, y_val : np.ndarray
        Validation feature and target matrices (2D).
    hidden_dim : int, default=8
        Number of hidden units.
    lr : float, default=0.01
        Learning rate.
    batch_size : int, default=32
        Mini-batch size.
    l2_reg : float, default=0.001
        L2 regularization penalty.
    max_epochs : int, default=200
        Maximum number of training epochs.
    patience : int, default=15
        Early stopping patience in epochs.
    seed_init : int, default=4202
        Random seed for Xavier parameter initialization.
    seed_shuffle : int, default=4203
        Random seed for mini-batch permutations.

    Returns
    -------
    MLPResult
        Trained model weights and training history.
    """
    X_tr = _check_finite_2d(X_train, "X_train")
    y_tr = _check_finite_2d(y_train, "y_train")
    X_v = _check_finite_2d(X_val, "X_val")
    y_v = _check_finite_2d(y_val, "y_val")

    # Strict dimensional consistency checks to prevent broadcasting failures
    if X_tr.shape[0] != y_tr.shape[0]:
        raise ValueError(f"X_train rows ({X_tr.shape[0]}) do not match y_train rows ({y_tr.shape[0]})")
    if X_v.shape[0] != y_v.shape[0]:
        raise ValueError(f"X_val rows ({X_v.shape[0]}) do not match y_val rows ({y_v.shape[0]})")
    if X_tr.shape[1] != X_v.shape[1]:
        raise ValueError(f"Feature count mismatch: X_train has {X_tr.shape[1]}, X_val has {X_v.shape[1]}")
    if y_tr.shape[1] != y_v.shape[1]:
        raise ValueError(f"Target count mismatch: y_train has {y_tr.shape[1]}, y_val has {y_v.shape[1]}")

    # Validate integer hyperparameters
    h_dim = _check_pos_int(hidden_dim, "hidden_dim")
    b_size = _check_pos_int(batch_size, "batch_size")
    m_epochs = _check_pos_int(max_epochs, "max_epochs")
    pat = _check_pos_int(patience, "patience")
    s_init = _check_pos_int(seed_init, "seed_init", allow_zero=True)
    s_shuff = _check_pos_int(seed_shuffle, "seed_shuffle", allow_zero=True)

    if isinstance(lr, (bool, np.bool_)):
        raise TypeError(f"lr cannot be boolean, got {lr}")
    if not isinstance(lr, (int, float, np.floating, np.integer)) or not np.isfinite(lr) or lr <= 0:
        raise ValueError(f"lr must be positive and finite, got {lr}")
    if isinstance(l2_reg, (bool, np.bool_)):
        raise TypeError(f"l2_reg cannot be boolean, got {l2_reg}")
    if not isinstance(l2_reg, (int, float, np.floating, np.integer)) or not np.isfinite(l2_reg) or l2_reg < 0:
        raise ValueError(f"l2_reg must be >= 0 and finite, got {l2_reg}")

    n_samples, in_dim = X_tr.shape
    out_dim = y_tr.shape[1]

    # Xavier/Glorot uniform initialization
    rng_init = np.random.default_rng(s_init)
    limit1 = np.sqrt(6.0 / (in_dim + h_dim))
    W1 = rng_init.uniform(-limit1, limit1, size=(in_dim, h_dim))
    b1 = np.zeros((1, h_dim))

    limit2 = np.sqrt(6.0 / (h_dim + out_dim))
    W2 = rng_init.uniform(-limit2, limit2, size=(h_dim, out_dim))
    b2 = np.zeros((1, out_dim))

    rng_shuffle = np.random.default_rng(s_shuff)

    best_epoch = -1
    best_val_loss = float("inf")
    best_weights: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None
    patience_counter = 0

    train_loss_history: list[float] = []
    val_loss_history: list[float] = []

    for epoch in range(m_epochs):
        perm = rng_shuffle.permutation(n_samples)
        X_shuffled = X_tr[perm]
        y_shuffled = y_tr[perm]

        for start in range(0, n_samples, b_size):
            end = min(start + b_size, n_samples)
            xb = X_shuffled[start:end]
            yb = y_shuffled[start:end]

            _, dW1, db1, dW2, db2 = loss_and_grad(xb, yb, W1, b1, W2, b2, l2_reg=l2_reg)

            W1 -= lr * dW1
            b1 -= lr * db1
            W2 -= lr * dW2
            b2 -= lr * db2

        # Evaluate epoch MSE on validation set (unregularized validation MSE)
        val_pred = predict(X_v, W1, b1, W2, b2)
        val_mse = float(np.mean((y_v - val_pred) ** 2))

        tr_pred = predict(X_tr, W1, b1, W2, b2)
        tr_mse = float(np.mean((y_tr - tr_pred) ** 2))
        if not np.isfinite(val_mse) or not np.isfinite(tr_mse):
            raise FloatingPointError("Epoch MSE diverged to non-finite value")

        train_loss_history.append(tr_mse)
        val_loss_history.append(val_mse)

        if val_mse < best_val_loss:
            best_val_loss = val_mse
            best_epoch = epoch
            best_weights = (W1.copy(), b1.copy(), W2.copy(), b2.copy())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= pat:
                break

    if best_weights is None:
        best_weights = (W1.copy(), b1.copy(), W2.copy(), b2.copy())
        best_epoch = m_epochs - 1

    return MLPResult(
        W1=best_weights[0],
        b1=best_weights[1],
        W2=best_weights[2],
        b2=best_weights[3],
        best_epoch=best_epoch,
        stopped_epoch=len(val_loss_history) - 1,
        best_val_loss=best_val_loss,
        train_loss_history=train_loss_history,
        val_loss_history=val_loss_history,
    )


# ---------------------------------------------------------------------------
# Architecture Micro-Examples: CNN, RNN, LSTM, Attention
# ---------------------------------------------------------------------------

def cnn_cross_correlation(x: Sequence[float] | np.ndarray, w: Sequence[float] | np.ndarray) -> np.ndarray:
    """1D valid cross-correlation (standard deep learning 'convolution' layer without kernel flipping).

    Calculates:
        out[i] = sum_{j=0}^{k-1} x[i + j] * w[j], for i = 0, ..., len(x) - len(w).
    Note that shared kernel convolution is translation equivariant, not invariant.

    Parameters
    ----------
    x : 1D array-like
        Input signal vector.
    w : 1D array-like
        Filter / kernel weights vector.

    Returns
    -------
    np.ndarray
        1D output of length len(x) - len(w) + 1.
    """
    x_arr = _check_finite_1d(x, "x")
    w_arr = _check_finite_1d(w, "w")

    if len(x_arr) < len(w_arr):
        raise ValueError(f"Input length ({len(x_arr)}) must be >= kernel length ({len(w_arr)})")

    k = len(w_arr)
    n_out = len(x_arr) - k + 1
    out = np.zeros(n_out, dtype=float)
    for i in range(n_out):
        out[i] = np.sum(x_arr[i : i + k] * w_arr)
    return out


def rnn_states(
    x: Sequence[float] | np.ndarray,
    w_h: float = 0.5,
    w_x: float = 1.0,
    b: float = 0.0,
    h_init: float = 0.0,
) -> np.ndarray:
    """Compute hidden state recurrence for a scalar Simple RNN:

        h_t = w_h * h_{t-1} + w_x * x_t + b

    Also illustrates vanishing gradient product:
        partial h_t / partial h_{t-k} = w_h^k.

    Parameters
    ----------
    x : 1D array-like
        Input sequence.
    w_h : float, default=0.5
        Recurrent hidden weight.
    w_x : float, default=1.0
        Input weight.
    b : float, default=0.0
        Bias term.
    h_init : float, default=0.0
        Initial hidden state h_{-1}.

    Returns
    -------
    np.ndarray
        Hidden state sequence [h_0, h_1, ..., h_{T-1}].
    """
    x_arr = _check_finite_1d(x, "x")
    for name, val in [("w_h", w_h), ("w_x", w_x), ("b", b), ("h_init", h_init)]:
        if not np.isfinite(val):
            raise ValueError(f"{name} must be finite")

    states = np.zeros(len(x_arr), dtype=float)
    h = float(h_init)
    for t, val in enumerate(x_arr):
        h = w_h * h + w_x * val + b
        states[t] = h
    return states


def sigmoid(z: np.ndarray | float) -> np.ndarray | float:
    """Numerically stable sigmoid function clipped to [-30, 30]."""
    z_arr = np.asarray(z, dtype=float)
    clipped = np.clip(z_arr, -30.0, 30.0)
    res = 1.0 / (1.0 + np.exp(-clipped))
    if np.ndim(z) == 0:
        return float(res)
    return res


def lstm_step(
    x_t: np.ndarray,
    h_prev: np.ndarray,
    c_prev: np.ndarray,
    W: dict[str, np.ndarray],
    U: dict[str, np.ndarray],
    b: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """Execute one step of a modern LSTM cell with forget gate (Gers et al., 2000).

    Formulas:
        f_t = sigmoid(x_t @ W_f + h_{t-1} @ U_f + b_f)       # Forget gate
        i_t = sigmoid(x_t @ W_i + h_{t-1} @ U_i + b_i)       # Input gate
        c~_t = tanh(x_t @ W_c + h_{t-1} @ U_c + b_c)         # Candidate cell
        c_t = f_t * c_{t-1} + i_t * c~_t                     # Cell state update
        o_t = sigmoid(x_t @ W_o + h_{t-1} @ U_o + b_o)       # Output gate
        h_t = o_t * tanh(c_t)                                # Hidden state

    Parameters
    ----------
    x_t : np.ndarray, shape (d_in,) or (B, d_in)
        Current input.
    h_prev : np.ndarray, shape (d_h,) or (B, d_h)
        Previous hidden state.
    c_prev : np.ndarray, shape (d_h,) or (B, d_h)
        Previous cell state.
    W : dict[str, np.ndarray]
        Input weight matrices for keys ['f', 'i', 'c', 'o']. Shape (d_in, d_h).
    U : dict[str, np.ndarray]
        Recurrent weight matrices for keys ['f', 'i', 'c', 'o']. Shape (d_h, d_h).
    b : dict[str, np.ndarray]
        Bias vectors for keys ['f', 'i', 'c', 'o']. Shape (1, d_h) or (d_h,).

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary with keys 'f', 'i', 'c_tilde', 'c', 'o', 'h'.
    """
    is_1d = (np.ndim(x_t) == 1)
    x_2d = np.atleast_2d(np.asarray(x_t, dtype=float))
    h_2d = np.atleast_2d(np.asarray(h_prev, dtype=float))
    c_2d = np.atleast_2d(np.asarray(c_prev, dtype=float))

    _check_finite_2d(x_2d, "x_t")
    _check_finite_2d(h_2d, "h_prev")
    _check_finite_2d(c_2d, "c_prev")

    # Strict dimensional consistency check to prevent cell broadcasting failure
    if h_2d.shape[1] != c_2d.shape[1]:
        raise ValueError(f"h_prev hidden dim ({h_2d.shape[1]}) must match c_prev hidden dim ({c_2d.shape[1]})")
    if h_2d.shape[0] != c_2d.shape[0] or x_2d.shape[0] != h_2d.shape[0]:
        raise ValueError(f"Batch dimension mismatch across x_t ({x_2d.shape[0]}), h_prev ({h_2d.shape[0]}), c_prev ({c_2d.shape[0]})")

    required_keys = ("f", "i", "c", "o")
    for k in required_keys:
        if k not in W or k not in U or k not in b:
            raise ValueError(f"Missing required gate key '{k}' in W, U, or b")

    d_in = x_2d.shape[1]
    d_h = h_2d.shape[1]

    for k in required_keys:
        W_k = _check_finite_2d(W[k], f"W[{k}]")
        U_k = _check_finite_2d(U[k], f"U[{k}]")
        b_raw = np.asarray(b[k], dtype=float)
        if not np.isfinite(b_raw).all():
            raise ValueError(f"b[{k}] contains NaN or infinite values")
        b_k = np.atleast_2d(b_raw)
        if W_k.shape != (d_in, d_h):
            raise ValueError(f"W[{k}] shape {W_k.shape} must be ({d_in}, {d_h})")
        if U_k.shape != (d_h, d_h):
            raise ValueError(f"U[{k}] shape {U_k.shape} must be ({d_h}, {d_h})")
        if b_k.shape != (1, d_h) and b_k.shape != (d_h, 1):
            raise ValueError(f"b[{k}] shape {b_k.shape} must be compatible with (1, {d_h})")

    b_f = np.atleast_2d(b["f"]).reshape(1, d_h)
    b_i = np.atleast_2d(b["i"]).reshape(1, d_h)
    b_c = np.atleast_2d(b["c"]).reshape(1, d_h)
    b_o = np.atleast_2d(b["o"]).reshape(1, d_h)

    f_t = sigmoid(x_2d @ W["f"] + h_2d @ U["f"] + b_f)
    i_t = sigmoid(x_2d @ W["i"] + h_2d @ U["i"] + b_i)
    c_tilde = np.tanh(x_2d @ W["c"] + h_2d @ U["c"] + b_c)
    c_t = f_t * c_2d + i_t * c_tilde
    o_t = sigmoid(x_2d @ W["o"] + h_2d @ U["o"] + b_o)
    h_t = o_t * np.tanh(c_t)

    res = {
        "f": f_t[0] if is_1d else f_t,
        "i": i_t[0] if is_1d else i_t,
        "c_tilde": c_tilde[0] if is_1d else c_tilde,
        "c": c_t[0] if is_1d else c_t,
        "o": o_t[0] if is_1d else o_t,
        "h": h_t[0] if is_1d else h_t,
    }
    return res


def stable_masked_softmax(logits: np.ndarray, axis: int = -1) -> np.ndarray:
    """Compute numerically stable softmax supporting strictly masked -inf entries.

    Guarantees that exp(-inf) = 0.0 without generating NaN from (-inf - (-inf)).
    """
    m = np.max(logits, axis=axis, keepdims=True)
    m_clean = np.where(np.isneginf(m), 0.0, m)
    exp_logits = np.exp(logits - m_clean)
    exp_logits = np.where(np.isneginf(logits), 0.0, exp_logits)
    sum_exp = np.sum(exp_logits, axis=axis, keepdims=True)
    sum_exp_safe = np.where(sum_exp == 0.0, 1.0, sum_exp)
    return exp_logits / sum_exp_safe


def causal_attention(
    Q: np.ndarray,
    K: np.ndarray,
    V: np.ndarray,
    *,
    mask: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Scaled dot-product attention with strict upper-triangle causal mask.

    Computes:
        Attention(Q, K, V) = softmax(Q @ K^T / sqrt(d_k) + M) @ V
    where M_{i,j} = 0 for j <= i and -inf for j > i (strictly preventing attention to future tokens).

    Parameters
    ----------
    Q : np.ndarray, shape (T, d_k) or (B, T, d_k)
        Queries.
    K : np.ndarray, shape (T, d_k) or (B, T, d_k)
        Keys.
    V : np.ndarray, shape (T, d_v) or (B, T, d_v)
        Values.
    mask : bool, default=True
        Whether to apply the causal lower-triangular mask.

    Returns
    -------
    weights : np.ndarray, shape (..., T, T)
        Attention weight matrix. If mask=True, upper triangle is strictly 0.0.
    output : np.ndarray, shape (..., T, d_v)
        Context-weighted representation.
    """
    Q_arr = np.asarray(Q, dtype=float)
    K_arr = np.asarray(K, dtype=float)
    V_arr = np.asarray(V, dtype=float)

    if Q_arr.ndim not in (2,3) or K_arr.ndim != Q_arr.ndim or V_arr.ndim != Q_arr.ndim:
        raise ValueError("Q, K, V must all be 2D or all be 3D")
    if Q_arr.shape[:-2] != K_arr.shape[:-2] or Q_arr.shape[:-2] != V_arr.shape[:-2]:
        raise ValueError("Q, K, V batch dimensions must match exactly")
    if not isinstance(mask, (bool,np.bool_)):
        raise TypeError("mask must be boolean")
    if not np.isfinite(Q_arr).all() or not np.isfinite(K_arr).all() or not np.isfinite(V_arr).all():
        raise ValueError("Q, K, V must contain finite values")

    d_k = Q_arr.shape[-1]
    d_v = V_arr.shape[-1]
    T = Q_arr.shape[-2]

    # Rejection of empty dimensions (e.g. key dimension d_k == 0)
    if d_k <= 0:
        raise ValueError(f"Key dimension d_k must be strictly positive, got {d_k}")
    if d_v <= 0:
        raise ValueError(f"Value dimension d_v must be strictly positive, got {d_v}")
    if T <= 0:
        raise ValueError(f"Sequence length T must be strictly positive, got {T}")

    if K_arr.shape[-1] != d_k:
        raise ValueError(f"Q key dim {d_k} != K key dim {K_arr.shape[-1]}")
    if K_arr.shape[-2] != T or V_arr.shape[-2] != T:
        raise ValueError(f"Sequence length mismatch across Q ({T}), K ({K_arr.shape[-2]}), V ({V_arr.shape[-2]})")

    # Scaled dot-product: (..., T, d_k) @ (..., d_k, T) -> (..., T, T)
    scores = (Q_arr @ K_arr.swapaxes(-1, -2)) / np.sqrt(d_k)
    if not np.isfinite(scores).all():
        raise FloatingPointError("Attention scores overflowed")

    if mask:
        causal_mask = np.triu(np.full((T, T), -np.inf), k=1)
        scores = scores + causal_mask

    weights = stable_masked_softmax(scores, axis=-1)
    output = weights @ V_arr
    return weights, output


def sinusoidal_positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    """Generate Vaswani et al. (2017) sinusoidal positional encodings.

    PE(pos, 2i)   = sin(pos / 10000^(2i / d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i / d_model))

    Parameters
    ----------
    seq_len : int
        Number of sequence positions.
    d_model : int
        Embedding / model dimension (must be even).

    Returns
    -------
    np.ndarray, shape (seq_len, d_model)
        Positional encoding table.
    """
    s_len = _check_pos_int(seq_len, "seq_len")
    d_mod = _check_pos_int(d_model, "d_model")
    if d_mod % 2 != 0:
        raise ValueError(f"d_model must be an even positive integer, got {d_mod}")

    pe = np.zeros((s_len, d_mod), dtype=float)
    position = np.arange(s_len)[:, None]
    div_term = np.exp(np.arange(0, d_mod, 2) * (-np.log(10000.0) / d_mod))

    pe[:, 0::2] = np.sin(position * div_term)
    pe[:, 1::2] = np.cos(position * div_term)
    return pe


# ---------------------------------------------------------------------------
# Chapter 42 Synthetic Panel Data Generator & Partitioning
# ---------------------------------------------------------------------------

def generate_ch42_panel_data(seed: int = 4201) -> tuple[np.ndarray, np.ndarray, pd.DataFrame, pd.DatetimeIndex, list[str]]:
    """Generate synthetic asset pricing panel per Chapter 42 protocol and addendum v1.

    Panel specs:
    - n_dates = 360 weekdays starting 2020-01-02 16:00:00 UTC (synthetic weekday calendar, aware).
    - n_assets = 12 (named A00..A11).
    - features = 4 (x[k, i, :] known at close k).
    - noise ~ N(0, 0.01^2).
    - raw_return[k+2, i] = 0.0004 * x[k, i, 0] + 0.0002 * (x[k, i, 1]^2 - 1) + noise[k+2, i] for k=0..357.
    - First two returns use noise directly.
    - close is cumulative product of (1 + raw_return) from base 100.0.

    Returns
    -------
    x : np.ndarray, shape (360, 12, 4)
    raw_return : np.ndarray, shape (360, 12)
    close : pd.DataFrame, shape (360, 12)
    dates : pd.DatetimeIndex (UTC-aware at 16:00:00)
    assets : list[str]
    """
    rng = np.random.default_rng(seed)
    T, N, K = 360, 12, 4
    # UTC-aware 16:00:00 timestamps
    dates = pd.bdate_range(start="2020-01-02", periods=T, tz="UTC") + pd.Timedelta(hours=16)
    assets = [f"A{i:02d}" for i in range(N)]

    x = rng.normal(size=(T, N, K))
    noise = rng.normal(scale=0.01, size=(T, N))
    raw_return = np.zeros((T, N), dtype=float)
    raw_return[0] = noise[0]
    raw_return[1] = noise[1]

    for k in range(T - 2):
        raw_return[k + 2] = 0.0004 * x[k, :, 0] + 0.0002 * (x[k, :, 1] ** 2 - 1.0) + noise[k + 2]

    if (raw_return <= -1.0).any():
        raise ValueError("Simulated return <= -100%; reject panel")

    close = pd.DataFrame(100.0 * np.cumprod(1.0 + raw_return, axis=0), index=dates, columns=assets)
    return x, raw_return, close, dates, assets


@dataclass
class PanelSplits:
    """Container for time-series panel partitions with boundary purging."""
    train_dates_idx: np.ndarray  # [0, 177], count=178
    val_dates_idx: np.ndarray    # [180, 237], count=58
    test_dates_idx: np.ndarray   # [240, 357], count=118
    X_train: np.ndarray          # shape (178*12, 4)
    y_train: np.ndarray          # shape (178*12, 1)
    X_val: np.ndarray            # shape (58*12, 4)
    y_val: np.ndarray            # shape (58*12, 1)
    X_test: np.ndarray           # shape (118*12, 4)
    y_test: np.ndarray           # shape (118*12, 1)
    train_dates: pd.DatetimeIndex
    val_dates: pd.DatetimeIndex
    test_dates: pd.DatetimeIndex


def split_ch42_panel(
    x: np.ndarray,
    raw_return: np.ndarray,
    dates: pd.DatetimeIndex,
    assets: list[str],
) -> PanelSplits:
    """Split panel into train/val/test with strict boundary label availability purging.

    Signal k occurs at date k (16:00 UTC).
    Execution at date k+1 (16:00 UTC).
    Label measurement from k+1 to k+2 (16:00 UTC).
    Label matures at label_available_at = dates[k+2].

    Boundary Purging Contract:
    - Candidate train dates: positions [0, 179].
      Validation block starts at first decision signal date: dates[180].
      A training signal k is eligible if and only if label_available_at[k] < dates[180].
      Since dates[k+2] < dates[180] <=> k+2 < 180 <=> k <= 177, signals 178 and 179 are purged.
    - Candidate validation dates: positions [180, 239].
      Test block starts at first decision signal date: dates[240].
      A validation signal k is eligible if and only if label_available_at[k] < dates[240].
      Since dates[k+2] < dates[240] <=> k+2 < 240 <=> k <= 237, signals 238 and 239 are purged.
    - Candidate test dates: positions [240, 357].
      Max signal k=357 has label at dates[359], within the 360-day panel.
    """
    x=np.asarray(x,dtype=float);raw_return=np.asarray(raw_return,dtype=float)
    if x.ndim != 3 or raw_return.ndim != 2 or x.shape[:2] != raw_return.shape:
        raise ValueError("x and raw_return must have matching date/asset dimensions")
    if x.shape[0] != 360 or x.shape[1] == 0 or x.shape[2] == 0:
        raise ValueError("This fixed teaching split requires 360 dates and nonempty assets/features")
    if not np.isfinite(x).all() or not np.isfinite(raw_return).all():
        raise ValueError("Panel values must be finite")
    if len(assets) != x.shape[1] or len(set(assets)) != len(assets):
        raise ValueError("assets must be unique and match the panel asset dimension")
    if not isinstance(dates,pd.DatetimeIndex) or dates.hasnans or not dates.is_unique or not dates.is_monotonic_increasing:
        raise ValueError("dates must be a strictly increasing DatetimeIndex without missing values")
    if len(dates) != x.shape[0] or len(dates) != raw_return.shape[0]:
        raise ValueError("Length of dates must match first dimension of x and raw_return")
    if dates.tz is None:
        raise ValueError("dates must be timezone-aware (expected UTC)")

    train_cand = np.arange(0, 180)
    val_cand = np.arange(180, 240)
    test_cand = np.arange(240, 358)

    val_start_time = dates[180]
    test_start_time = dates[240]

    # Timestamp-based label availability filtering
    train_idx = np.array([k for k in train_cand if dates[k + 2] < val_start_time], dtype=int)
    val_idx = np.array([k for k in val_cand if dates[k + 2] < test_start_time], dtype=int)
    test_idx = np.array([k for k in test_cand if (k + 2) < len(dates)], dtype=int)

    K = x.shape[2]

    X_train = x[train_idx].reshape(-1, K)
    y_train = raw_return[train_idx + 2].reshape(-1, 1)

    X_val = x[val_idx].reshape(-1, K)
    y_val = raw_return[val_idx + 2].reshape(-1, 1)

    X_test = x[test_idx].reshape(-1, K)
    y_test = raw_return[test_idx + 2].reshape(-1, 1)

    return PanelSplits(
        train_dates_idx=train_idx,
        val_dates_idx=val_idx,
        test_dates_idx=test_idx,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        train_dates=dates[train_idx],
        val_dates=dates[val_idx],
        test_dates=dates[test_idx],
    )
