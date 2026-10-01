import numpy as np
import pytest

from modegrid.anova import bootstrap, cell_spreads, decompose, permutation_p, rank_transform, residualise


def test_hand_computed_two_by_two():
    # families x modes x replicates. Cell means: [[1, 3], [2, 4]], grand mean 2.5.
    y = np.array([[[0, 2], [2, 4]], [[1, 3], [3, 5]]], dtype=float)
    d = decompose(y)
    # SS_family = b*n*sum((fam_mean - grand)^2) = 2*2*((2-2.5)^2 + (3-2.5)^2) = 2
    assert d.ss["family"] == pytest.approx(2.0)
    # SS_mode = a*n*((1.5-2.5)^2 + (3.5-2.5)^2) = 8
    assert d.ss["mode"] == pytest.approx(8.0)
    assert d.ss["interaction"] == pytest.approx(0.0)
    # every replicate is cell mean +/- 1 -> SS_E = 8
    assert d.ss["residual"] == pytest.approx(8.0)
    assert d.ss_total == pytest.approx(18.0)
    assert sum(d.eta2[k] for k in d.eta2) == pytest.approx(1.0)
    assert d.df == {"family": 1, "mode": 1, "interaction": 1, "residual": 4}


def test_sums_of_squares_partition_on_random_data():
    rng = np.random.default_rng(3)
    y = rng.integers(0, 3, size=(6, 2, 3)).astype(float)
    d = decompose(y)
    assert sum(d.ss.values()) == pytest.approx(d.ss_total)


def test_batched_matches_single():
    rng = np.random.default_rng(4)
    y = rng.integers(0, 3, size=(5, 6, 2, 3)).astype(float)
    batched = decompose(y)
    for i in range(5):
        assert decompose(y[i]).delta_omega2 == pytest.approx(batched.delta_omega2[i], nan_ok=True)


def test_constant_scores_give_nan_not_crash():
    d = decompose(np.ones((6, 2, 3)))
    assert np.isnan(d.eta2["mode"])


def test_pure_mode_effect_is_detected():
    y = np.zeros((6, 2, 3))
    y[:, 1, :] = 2
    y[:, :, 0] += 0  # no noise
    y[0, 0, 1] = 1  # a little residual variance so omega2 is defined
    d = decompose(y)
    assert d.delta_omega2 > 0.8
    assert permutation_p(y, "mode", n_perm=500) < 0.01
    assert permutation_p(y, "family", n_perm=500) > 0.05


def test_pure_family_effect_is_detected():
    y = np.repeat(np.array([0, 0, 1, 1, 2, 2], dtype=float)[:, None, None], 2, axis=1).repeat(3, axis=2)
    y[0, 0, 0] = 1
    d = decompose(y)
    assert d.delta_omega2 < -0.5


def test_bootstrap_is_reproducible():
    rng = np.random.default_rng(5)
    y = rng.integers(0, 3, size=(6, 2, 3)).astype(float)
    a = bootstrap(y, n_boot=200, seed=9).delta_omega2
    b = bootstrap(y, n_boot=200, seed=9).delta_omega2
    np.testing.assert_array_equal(a, b)


def test_rank_transform_handles_ties():
    r = rank_transform(np.array([[0.0, 0.0, 2.0]]))
    np.testing.assert_allclose(r, [[1.5, 1.5, 3.0]])


def test_residualise_removes_linear_covariate():
    x = np.arange(12, dtype=float).reshape(6, 2, 1).repeat(2, axis=2)
    y = 3 * x + 1
    out = residualise(y, x)
    assert np.ptp(out) == pytest.approx(0.0, abs=1e-9)


def test_cell_spreads():
    y = np.zeros((3, 2, 2))
    y[:, 1, :] = 2
    s = cell_spreads(y)
    assert s["between_model"] == 0
    assert s["within_model_mode"] == pytest.approx(2.0)


def test_rejects_too_small_design():
    with pytest.raises(ValueError):
        decompose(np.zeros((1, 2, 3)))
