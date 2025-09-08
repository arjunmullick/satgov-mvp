import numpy as np


def _safe_div(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.true_divide(a, b)
        out[~np.isfinite(out)] = 0.0
    return out


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    denom = nir + red
    return _safe_div(nir - red, denom)


def evi(nir: np.ndarray, red: np.ndarray, blue: np.ndarray, G: float = 2.5, C1: float = 6.0, C2: float = 7.5, L: float = 1.0) -> np.ndarray:
    return G * _safe_div(nir - red, (nir + C1 * red - C2 * blue + L))


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    denom = green + nir
    return _safe_div(green - nir, denom)


def mndwi(green: np.ndarray, swir1: np.ndarray) -> np.ndarray:
    denom = green + swir1
    return _safe_div(green - swir1, denom)

