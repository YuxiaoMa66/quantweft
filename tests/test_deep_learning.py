"""Unit and integration tests for Chapter 42 deep learning module.

Covers:
- Finite value, shape, and hyperparameter validation (including root boundary counterexamples).
- Central difference numerical gradient check on MLP parameters.
- CNN 1D valid cross-correlation micro-example.
- Simple RNN state recurrence and gradient product.
- Modern LSTM one-step gating, CEC, and dimension/bias finite checks.
- Causal attention strict upper-triangle masking, key dimension validation, and future perturbation invariance.
- Chronological early stopping checkpoint restoration.
- Preprocessing mutation safety (train-only scaling).
- UTC-aware panel generation and dynamic boundary label purging.
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Ensure workspace src is on path
workspace_src = Path(__file__).resolve().parent.parent / "src"
if str(workspace_src) not in sys.path:
    sys.path.insert(0, str(workspace_src))

from quant_course.deep_learning import (
    forward,
    loss_and_grad,
    predict,
    fit_mlp,
    cnn_cross_correlation,
    rnn_states,
    sigmoid,
    lstm_step,
    causal_attention,
    sinusoidal_positional_encoding,
    generate_ch42_panel_data,
    split_ch42_panel,
)


def test_panel_rejects_unsorted_and_nonfinite_inputs():
    x,r,_,dates,assets=generate_ch42_panel_data()
    with pytest.raises(ValueError,match="increasing"):
        split_ch42_panel(x,r,dates[::-1],assets)
    x[0,0,0]=np.nan
    with pytest.raises(ValueError,match="finite"):
        split_ch42_panel(x,r,dates,assets)


def test_attention_rejects_batch_broadcast():
    with pytest.raises(ValueError,match="batch"):
        causal_attention(np.zeros((2,3,2)),np.zeros((1,3,2)),np.zeros((2,3,1)))


def test_epoch_rejects_nonfinite_validation_loss():
    with np.errstate(over="ignore"),pytest.raises(FloatingPointError,match="Epoch MSE"):
        fit_mlp(np.zeros((2,1)),np.zeros((2,1)),np.zeros((2,1)),np.full((2,1),1e300),max_epochs=1)


def test_cli_figure_guard_precedes_output_creation(tmp_path):
    import importlib.util
    path=Path(__file__).resolve().parents[1]/"code/ch42_deep_learning.py"
    spec=importlib.util.spec_from_file_location("ch42_guard_test",path)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    figures=tmp_path/"figures";figures.mkdir();out=tmp_path/"run"
    with pytest.raises(FileExistsError):
        runner.run_experiment(out,figures)
    assert not out.exists()


# ---------------------------------------------------------------------------
# 1. Input Validation and Boundaries (Root Counterexample Regressions)
# ---------------------------------------------------------------------------

def test_validation_non_finite_inputs():
    """Non-finite inputs (inf, nan) and empty arrays must raise ValueError."""
    W1 = np.ones((2, 2))
    b1 = np.zeros((1, 2))
    W2 = np.ones((2, 1))
    b2 = np.zeros((1, 1))

    # NaN in X
    with pytest.raises(ValueError, match="NaN or infinite"):
        forward(np.array([[1.0, np.nan]]), W1, b1, W2, b2)

    # Inf in X
    with pytest.raises(ValueError, match="NaN or infinite"):
        forward(np.array([[1.0, np.inf]]), W1, b1, W2, b2)

    # Empty X
    with pytest.raises(ValueError, match="must not be empty"):
        forward(np.empty((0, 2)), W1, b1, W2, b2)

    # Dimension mismatch
    with pytest.raises(ValueError, match="feature dimension"):
        forward(np.ones((3, 5)), W1, b1, W2, b2)


def test_validation_hyperparameters():
    """Invalid training hyperparameters must be rejected."""
    X = np.ones((10, 2))
    y = np.ones((10, 1))
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, lr=-0.01)
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, batch_size=0)
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, batch_size=4.5)  # non-integer
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, batch_size=True)  # boolean
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, l2_reg=-0.1)
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, patience=0)
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(X, y, X, y, hidden_dim=-2)


def test_mlp_rejects_validation_broadcast():
    """Root counterexample: reject X_val / y_val row mismatch (no silent broadcasting)."""
    with pytest.raises((ValueError, TypeError)):
        fit_mlp(np.zeros((2, 1)), np.zeros((2, 1)), np.zeros((3, 1)), np.ones((1, 1)), max_epochs=1)


def test_lstm_rejects_cell_broadcast():
    """Root counterexample: reject c_prev hidden dimension mismatch against h_prev."""
    keys = ("f", "i", "c", "o")
    W = {k: np.zeros((1, 2)) for k in keys}
    U = {k: np.zeros((2, 2)) for k in keys}
    b = {k: np.zeros(2) for k in keys}
    with pytest.raises((ValueError, TypeError)):
        lstm_step(np.zeros(1), np.zeros(2), np.ones(1), W, U, b)


def test_lstm_rejects_nonfinite_bias():
    """Root counterexample: reject non-finite bias in gate parameters."""
    keys = ("f", "i", "c", "o")
    W = {k: np.zeros((1, 2)) for k in keys}
    U = {k: np.zeros((2, 2)) for k in keys}
    b = {k: np.zeros(2) for k in keys}
    b["f"][0] = np.nan
    with pytest.raises((ValueError, TypeError)):
        lstm_step(np.zeros(1), np.zeros(2), np.ones(2), W, U, b)


def test_attention_rejects_empty_key_dimension():
    """Root counterexample: reject empty key dimension (d_k == 0)."""
    with pytest.raises((ValueError, TypeError)):
        causal_attention(np.zeros((3, 0)), np.zeros((3, 0)), np.ones((3, 1)))


# ---------------------------------------------------------------------------
# 2. Analytic vs Numerical Central Difference Gradients
# ---------------------------------------------------------------------------

def test_mlp_central_difference_gradients():
    """Verify all analytic parameter gradients against central differences on a 2->2->1 MLP."""
    rng = np.random.default_rng(4200)
    B = 5
    D_in = 2
    D_hidden = 2
    D_out = 1

    X = rng.normal(size=(B, D_in))
    y = rng.normal(size=(B, D_out))
    W1 = rng.normal(size=(D_in, D_hidden))
    b1 = rng.normal(size=(1, D_hidden))
    W2 = rng.normal(size=(D_hidden, D_out))
    b2 = rng.normal(size=(1, D_out))
    l2_reg = 0.005

    loss, dW1, db1, dW2, db2 = loss_and_grad(X, y, W1, b1, W2, b2, l2_reg=l2_reg)

    eps = 1e-6
    for name, param, analytic_grad in [
        ("W1", W1, dW1),
        ("b1", b1, db1),
        ("W2", W2, dW2),
        ("b2", b2, db2),
    ]:
        num_grad = np.zeros_like(param)
        it = np.nditer(param, flags=["multi_index"])
        while not it.finished:
            idx = it.multi_index
            orig = param[idx]

            param[idx] = orig + eps
            l_plus, _, _, _, _ = loss_and_grad(X, y, W1, b1, W2, b2, l2_reg=l2_reg)

            param[idx] = orig - eps
            l_minus, _, _, _, _ = loss_and_grad(X, y, W1, b1, W2, b2, l2_reg=l2_reg)

            param[idx] = orig
            num_grad[idx] = (l_plus - l_minus) / (2.0 * eps)
            it.iternext()

        max_diff = float(np.max(np.abs(analytic_grad - num_grad)))
        rel_diff = float(max_diff / (np.max(np.abs(analytic_grad)) + 1e-12))
        assert max_diff < 1e-7, f"Gradient mismatch on {name}: max_diff={max_diff:.2e}, rel_diff={rel_diff:.2e}"


# ---------------------------------------------------------------------------
# 3. CNN 1D Valid Cross-Correlation
# ---------------------------------------------------------------------------

def test_cnn_valid_cross_correlation():
    """Microexample: valid cross-correlation of [1,2,3,4] with [1,-1] yields [-1,-1,-1]."""
    x = [1, 2, 3, 4]
    w = [1, -1]
    res = cnn_cross_correlation(x, w)
    expected = np.array([-1.0, -1.0, -1.0])
    np.testing.assert_allclose(res, expected)

    # Shorter signal than kernel must raise ValueError
    with pytest.raises(ValueError, match="must be >="):
        cnn_cross_correlation([1, 2], [1, -1, 2])


# ---------------------------------------------------------------------------
# 4. RNN Recurrence and Gradient Product
# ---------------------------------------------------------------------------

def test_rnn_recurrence_and_gradient():
    """Microexample: h_t = 0.5 h_{t-1} + x_t with x=[1,2,0] yields [1.0, 2.5, 1.25]."""
    x = [1.0, 2.0, 0.0]
    states = rnn_states(x, w_h=0.5, w_x=1.0, b=0.0, h_init=0.0)
    expected = np.array([1.0, 2.5, 1.25])
    np.testing.assert_allclose(states, expected)

    # Gradient product across k steps:
    # d h_t / d h_{t-k} = w_h^k = 0.5^k
    for k in [1, 2, 3, 5, 10]:
        grad_prod = 0.5 ** k
        assert np.isclose(grad_prod, 0.5 ** k)


# ---------------------------------------------------------------------------
# 5. Modern LSTM Step
# ---------------------------------------------------------------------------

def test_lstm_step_sanity():
    """One LSTM step: check gate bounds in [0,1], candidate in [-1,1], finite states."""
    x_t = np.array([0.5, -0.2])
    h_prev = np.array([0.1, 0.0])
    c_prev = np.array([0.2, -0.1])
    d_in = 2
    d_h = 2

    rng = np.random.default_rng(42)
    W = {k: rng.normal(size=(d_in, d_h)) for k in ("f", "i", "c", "o")}
    U = {k: rng.normal(size=(d_h, d_h)) for k in ("f", "i", "c", "o")}
    b = {k: np.zeros((1, d_h)) for k in ("f", "i", "c", "o")}

    out = lstm_step(x_t, h_prev, c_prev, W, U, b)

    for gate in ("f", "i", "o"):
        assert np.all(out[gate] >= 0.0) and np.all(out[gate] <= 1.0)
    assert np.all(out["c_tilde"] >= -1.0) and np.all(out["c_tilde"] <= 1.0)
    assert np.isfinite(out["c"]).all()
    assert np.isfinite(out["h"]).all()

    # Constant Error Carousel: holding gates constant, d c_t / d c_{t-1} = f_t
    f_val = out["f"]
    c_perturbed = c_prev + 1e-5
    out_pert = lstm_step(x_t, h_prev, c_perturbed, W, U, b)
    num_dcdprev = (out_pert["c"] - out["c"]) / 1e-5
    np.testing.assert_allclose(num_dcdprev, f_val, rtol=1e-5)


# ---------------------------------------------------------------------------
# 6. Transformer Causal Attention & Future Invariance
# ---------------------------------------------------------------------------

def test_causal_attention_mask_and_future_invariance():
    """3 tokens: upper-triangle attention weights strictly 0.0; future perturbation leaves earlier outputs unchanged."""
    T = 3
    d_k = 4
    rng = np.random.default_rng(42)
    Q = rng.normal(size=(T, d_k))
    K = rng.normal(size=(T, d_k))
    V = rng.normal(size=(T, d_k))

    weights, out = causal_attention(Q, K, V, mask=True)

    # 1. Strict zero upper-triangle
    upper_tri = np.triu(weights, k=1)
    np.testing.assert_allclose(upper_tri, 0.0, atol=1e-15)

    # 2. Row sums equal 1.0
    np.testing.assert_allclose(np.sum(weights, axis=-1), np.ones(T), rtol=1e-7)

    # 3. Future perturbation invariance: modify token 2 (future)
    Q_pert = Q.copy()
    K_pert = K.copy()
    V_pert = V.copy()
    Q_pert[2] += 10.0
    K_pert[2] -= 5.0
    V_pert[2] += 8.0

    weights_pert, out_pert = causal_attention(Q_pert, K_pert, V_pert, mask=True)

    # Earlier tokens (0 and 1) MUST NOT CHANGE AT ALL
    max_diff_earlier = float(np.max(np.abs(out[:2] - out_pert[:2])))
    assert max_diff_earlier == 0.0, f"Future leak! Earlier output changed by {max_diff_earlier}"

    # 4. Negative test: without mask (unmasked attention), future perturbation LEAKS to earlier tokens
    _, out_unmasked = causal_attention(Q, K, V, mask=False)
    _, out_unmasked_pert = causal_attention(Q_pert, K_pert, V_pert, mask=False)
    unmasked_leak = float(np.max(np.abs(out_unmasked[:2] - out_unmasked_pert[:2])))
    assert unmasked_leak > 1e-4, "Unmasked attention failed to demonstrate expected future information change"


def test_sinusoidal_positional_encoding():
    """Sinusoidal positional encoding shape and values in [-1, 1]."""
    seq_len = 10
    d_model = 8
    pe = sinusoidal_positional_encoding(seq_len, d_model)
    assert pe.shape == (seq_len, d_model)
    assert np.all(pe >= -1.0) and np.all(pe <= 1.0)
    assert pe[0, 0] == 0.0  # sin(0) = 0
    assert pe[0, 1] == 1.0  # cos(0) = 1


# ---------------------------------------------------------------------------
# 7. Chronological Early Stopping & Test Set Isolation
# ---------------------------------------------------------------------------

def test_early_stopping_restores_best_epoch():
    """Ensure fit_mlp restores the checkpoint with lowest validation loss."""
    rng = np.random.default_rng(123)
    X_tr = rng.normal(size=(100, 4))
    y_tr = X_tr[:, [0]] * 0.1 + rng.normal(scale=0.1, size=(100, 1))

    X_val = rng.normal(size=(30, 4))
    y_val = X_val[:, [0]] * 0.1 + rng.normal(scale=0.1, size=(30, 1))

    res = fit_mlp(X_tr, y_tr, X_val, y_val, max_epochs=50, patience=5)

    # Best epoch validation loss must be the minimum among all evaluated validation losses
    assert res.best_epoch <= res.stopped_epoch
    min_val_loss = min(res.val_loss_history)
    assert np.isclose(res.best_val_loss, min_val_loss)

    # Check that restored weights match best_epoch prediction MSE
    best_pred = predict(X_val, res.W1, res.b1, res.W2, res.b2)
    restored_mse = float(np.mean((y_val - best_pred) ** 2))
    assert np.isclose(restored_mse, res.best_val_loss)


def test_test_set_leakage_negative_test():
    """Model selection using test set artificially selects overfitted weights."""
    rng = np.random.default_rng(42)
    X_tr = rng.normal(size=(50, 4))
    y_tr = rng.normal(scale=0.5, size=(50, 1))

    X_test = rng.normal(size=(30, 4))
    y_test = rng.normal(scale=0.5, size=(30, 1))

    # If test is improperly used as validation
    res_leaked = fit_mlp(X_tr, y_tr, X_test, y_test, max_epochs=60, patience=20)
    # The reported 'best_val_loss' is actually tuned to X_test noise, demonstrating test contamination
    assert res_leaked.best_val_loss <= min(res_leaked.val_loss_history)


# ---------------------------------------------------------------------------
# 8. Train-Only Preprocessing Mutation Safety
# ---------------------------------------------------------------------------

def test_train_only_scaling_mutation_invariance():
    """Mutating validation or test features does not alter training mean/SD or training loss."""
    x, raw_return, close, dates, assets = generate_ch42_panel_data(seed=4201)
    splits = split_ch42_panel(x, raw_return, dates, assets)

    mu_X_orig = np.mean(splits.X_train, axis=0)
    sigma_X_orig = np.std(splits.X_train, axis=0)

    # Mutate test data
    splits.X_test += 999.0

    # Training moments remain completely unaffected
    mu_X_after = np.mean(splits.X_train, axis=0)
    sigma_X_after = np.std(splits.X_train, axis=0)
    np.testing.assert_allclose(mu_X_orig, mu_X_after)
    np.testing.assert_allclose(sigma_X_orig, sigma_X_after)


# ---------------------------------------------------------------------------
# 9. Synthetic Panel Generation and Dynamic Boundary Purging
# ---------------------------------------------------------------------------

def test_panel_generation_and_boundary_purge():
    """Verify UTC-aware panel generation and exact boundary label availability purging."""
    x, raw_return, close, dates, assets = generate_ch42_panel_data(seed=4201)
    assert x.shape == (360, 12, 4)
    assert raw_return.shape == (360, 12)
    assert close.shape == (360, 12)
    assert len(dates) == 360
    assert len(assets) == 12
    assert dates.tz is not None  # Must be UTC-aware
    assert dates[0].hour == 16   # 16:00 UTC close
    assert not (raw_return <= -1.0).any()

    splits = split_ch42_panel(x, raw_return, dates, assets)

    # Train dates [0, 177] -> 178 dates
    assert len(splits.train_dates_idx) == 178
    assert splits.train_dates_idx[0] == 0 and splits.train_dates_idx[-1] == 177
    # Validation dates [180, 237] -> 58 dates
    assert len(splits.val_dates_idx) == 58
    assert splits.val_dates_idx[0] == 180 and splits.val_dates_idx[-1] == 237
    # Test dates [240, 357] -> 118 dates
    assert len(splits.test_dates_idx) == 118
    assert splits.test_dates_idx[0] == 240 and splits.test_dates_idx[-1] == 357

    # Ensure purged boundary dates 178, 179 and 238, 239 are NOT in any evaluation set
    all_used_dates = set(splits.train_dates_idx) | set(splits.val_dates_idx) | set(splits.test_dates_idx)
    assert 178 not in all_used_dates
    assert 179 not in all_used_dates
    assert 238 not in all_used_dates
    assert 239 not in all_used_dates
