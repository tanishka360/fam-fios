
import pytest
import numpy as np
from app.engines.fafie.local_trainer import FafieLocalTrainer
from app.core.config import settings
from app.database import db_store

def compute_raw_clipped_gradient(weights, X, y, clip_c=1.0):
    N = len(X)
    w = np.array(weights)
    pred = np.dot(X, w)
    err = pred - y
    grad = np.dot(X.T, err) / N
    norm = np.linalg.norm(grad)
    if norm > clip_c:
        grad = grad * (clip_c / norm)
    return grad

def test_dp_noise_injection_and_non_determinism():
    trainer = FafieLocalTrainer('tenant_dp_test')
    weights = [0.5, -0.2, 0.1, 0.8, -0.4]
    np.random.seed(42)
    X = np.random.randn(30, len(weights))
    y = np.dot(X, weights) + 0.15

    raw_grad = compute_raw_clipped_gradient(weights, X, y, settings.FAFIE_DIFF_PRIVACY_CLIP_NORM)

    up1 = trainer.compute_local_gradient_update(weights, X, y)
    up2 = trainer.compute_local_gradient_update(weights, X, y)

    g1 = np.array(up1['gradient'])
    g2 = np.array(up2['gradient'])

    pert1 = np.linalg.norm(g1 - raw_grad)
    pert2 = np.linalg.norm(g2 - raw_grad)
    assert pert1 > 0.001
    assert pert2 > 0.001
    assert not np.allclose(g1, g2, atol=1e-5)

def test_dp_noise_distribution_and_scale_bounding():
    trainer = FafieLocalTrainer('tenant_dp_test')
    weights = [0.2, 0.4, -0.1, 0.3, 0.5]
    np.random.seed(123)
    X = np.random.randn(40, len(weights))
    y = np.dot(X, weights) + 0.05

    raw_grad = compute_raw_clipped_gradient(weights, X, y, settings.FAFIE_DIFF_PRIVACY_CLIP_NORM)
    expected_sigma = settings.FAFIE_NOISE_SCALE

    K = 100
    noise_samples = []
    for _ in range(K):
        up = trainer.compute_local_gradient_update(weights, X, y)
        noisy_g = np.array(up['gradient'])
        noise_samples.append(noisy_g - raw_grad)

    all_noise = np.array(noise_samples).flatten()
    empirical_mean = float(np.mean(all_noise))
    assert abs(empirical_mean) < 0.02
    empirical_std = float(np.std(all_noise))
    assert 0.035 < empirical_std < 0.065

def test_dp_gradient_clipping_bound():
    trainer = FafieLocalTrainer('tenant_dp_test')
    weights = [1.0, 1.0, 1.0]
    clip_c = settings.FAFIE_DIFF_PRIVACY_CLIP_NORM
    sigma = settings.FAFIE_NOISE_SCALE

    X_extreme = np.ones((10, 3)) * 50.0
    y_extreme = np.zeros(10)

    raw_unclipped_norm = np.linalg.norm(np.dot(X_extreme.T, np.dot(X_extreme, weights)) / 10)
    assert raw_unclipped_norm > 100.0

    up = trainer.compute_local_gradient_update(weights, X_extreme, y_extreme)
    noisy_grad = np.array(up['gradient'])
    noisy_norm = float(np.linalg.norm(noisy_grad))

    max_expected_norm = clip_c + 4 * sigma * np.sqrt(3)
    min_expected_norm = max(0.0, clip_c - 4 * sigma * np.sqrt(3))
    assert min_expected_norm <= noisy_norm <= max_expected_norm

def test_dp_obscures_adjacent_individual_sample():
    trainer = FafieLocalTrainer('tenant_dp_test')
    weights = [0.3, -0.5, 0.2]
    dim = len(weights)
    np.random.seed(99)

    N = 25
    X_base = np.random.randn(N, dim)
    y_base = np.dot(X_base, weights) + 0.1

    X_adj = np.copy(X_base)
    y_adj = np.copy(y_base)
    X_adj[-1] = np.array([2.5, -2.0, 1.8])
    y_adj[-1] = 5.0

    raw_base = compute_raw_clipped_gradient(weights, X_base, y_base, settings.FAFIE_DIFF_PRIVACY_CLIP_NORM)
    raw_adj = compute_raw_clipped_gradient(weights, X_adj, y_adj, settings.FAFIE_DIFF_PRIVACY_CLIP_NORM)
    raw_diff = raw_adj - raw_base
    raw_diff_norm = np.linalg.norm(raw_diff)
    assert raw_diff_norm > 0.01

    dp_base_draws = [np.array(trainer.compute_local_gradient_update(weights, X_base, y_base)['gradient']) for _ in range(30)]
    dp_adj_draws = [np.array(trainer.compute_local_gradient_update(weights, X_adj, y_adj)['gradient']) for _ in range(30)]

    dp_diffs = [np.linalg.norm(b - a) for b, a in zip(dp_base_draws, dp_adj_draws)]
    noise_fluctuation = np.std(dp_diffs)
    assert noise_fluctuation > 0.005
