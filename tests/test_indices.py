import numpy as np
from src.utils.indices import ndvi, evi, ndwi, mndwi


def test_indices_basic_shapes():
    a = np.ones((10, 10)) * 0.6
    b = np.ones((10, 10)) * 0.2
    c = np.ones((10, 10)) * 0.1
    assert ndvi(a, b).shape == (10, 10)
    assert evi(a, b, c).shape == (10, 10)
    assert ndwi(b, a).shape == (10, 10)
    assert mndwi(b, c).shape == (10, 10)


def test_ndvi_range():
    nir = np.array([0.8, 0.1])
    red = np.array([0.2, 0.1])
    v = ndvi(nir, red)
    assert np.all(v <= 1.0 + 1e-6)
    assert np.all(v >= -1.0 - 1e-6)

