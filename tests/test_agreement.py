import math

import pytest

from modegrid.agreement import exact_agreement, krippendorff_alpha

# Raters x units, None = missing.
DATA = [
    [0, 1, 2, 2, 1, 0, None, 2, 1, 0],
    [0, 1, 2, 1, 1, 0, 2, 2, 0, 0],
    [1, 1, 2, 2, None, 0, 2, 1, 1, 0],
]


def test_perfect_agreement_is_one():
    assert krippendorff_alpha([[0, 1, 2, 1], [0, 1, 2, 1]]) == pytest.approx(1.0)


def test_no_variation_is_nan():
    assert math.isnan(krippendorff_alpha([[1, 1, 1], [1, 1, 1]]))


@pytest.mark.parametrize("level", ["nominal", "ordinal", "interval"])
def test_matches_reference_package(level):
    kp = pytest.importorskip("krippendorff")
    import numpy as np

    ref = kp.alpha(
        reliability_data=np.array([[np.nan if v is None else v for v in r] for r in DATA], dtype=float),
        level_of_measurement=level,
    )
    assert krippendorff_alpha(DATA, level) == pytest.approx(ref, abs=1e-9)


def test_exact_agreement_skips_missing():
    assert exact_agreement([0, 1, None, 2], [0, 2, 1, 2]) == pytest.approx(2 / 3)
