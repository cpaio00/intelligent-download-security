"""Batch scoring of memory-mapped rows (complete validation/calibration/test weeks with little memory)."""
import numpy as np

from .data import batches


def score(booster, X, rows: np.ndarray, cols: np.ndarray, size: int = 10000) -> np.ndarray:
    """Uncalibrated predicted probability s for each selected row."""
    if booster.num_feature() != len(cols):
        raise ValueError("model feature count does not match the selected columns")
    return np.concatenate([booster.predict(b) for b in batches(X, rows, cols, size)]) if len(rows) else np.array([])
