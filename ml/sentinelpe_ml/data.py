"""Access to thrember-vectorised EMBER2024 files without loading them into RAM, week indexing and sampling.

thrember writes X_<subset>.dat (float32, rows x 2568) and y_<subset>.dat (int32) as raw memmaps, in the order of
sorted JSONL file names and line order (gather_feature_paths + raw_feature_iterator). week_table() reads metadata in
that same order. UNTESTED on real EMBER2024 data.
"""
import datetime as dt
import json
import os

import lightgbm as lgb
import numpy as np

from .features import N_FEATURES

ORIGIN = dt.datetime(2023, 9, 24, tzinfo=dt.timezone.utc)   # official week 0 starts here (testing plan, Section 6)


def open_vectors(path_x: str, path_y: str | None = None, n_features: int = N_FEATURES):
    """Memory-map a thrember .dat (float32) or a .npy matrix, and its labels."""
    if path_x.endswith(".npy"):
        X = np.load(path_x, mmap_mode="r")
        y = np.load(path_y or path_x[:-4] + "_y.npy", mmap_mode="r")
    else:
        X = np.memmap(path_x, dtype=np.float32, mode="r")
        if X.size % n_features:
            raise ValueError(f"{path_x}: size is not a multiple of {n_features}")
        X = X.reshape(-1, n_features)
        y = np.memmap(path_y or path_x.replace("X_", "y_"), dtype=np.int32, mode="r")
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"row count mismatch: X {X.shape[0]} vs y {y.shape[0]}")
    return X, y


def official_week(first_submission_date) -> int:
    """Whole days since 2023-09-24 divided by 7. Accepts a Unix timestamp or an ISO-8601 string."""
    if isinstance(first_submission_date, (int, float)):
        t = dt.datetime.fromtimestamp(first_submission_date, dt.timezone.utc)
    else:
        t = dt.datetime.fromisoformat(str(first_submission_date).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
    return (t - ORIGIN).days // 7


def week_table(data_dir: str, subset: str):
    """(weeks, labels) arrays in thrember row order for the JSONL files of a subset ('train', 'test', 'challenge')."""
    files = [f for f in sorted(os.listdir(data_dir)) if f.endswith(".jsonl") and subset in f]
    if not files:
        raise FileNotFoundError(f"no .jsonl files containing '{subset}' in {data_dir}")
    weeks, labels = [], []
    for f in files:
        with open(os.path.join(data_dir, f), "r", encoding="utf-8") as fin:
            for line in fin:
                r = json.loads(line)
                weeks.append(official_week(r["first_submission_date"]))
                labels.append(int(r["label"]))
    return np.array(weeks, dtype=np.int16), np.array(labels, dtype=np.int8)


def week_rows(weeks: np.ndarray, labels: np.ndarray, lo: int, hi: int) -> np.ndarray:
    """Row numbers of labelled (0/1) records in official weeks lo..hi inclusive."""
    return np.flatnonzero((weeks >= lo) & (weeks <= hi) & ((labels == 0) | (labels == 1)))


def stratified_sample(rows: np.ndarray, weeks: np.ndarray, labels: np.ndarray, n: int, seed: int) -> np.ndarray:
    """Sample n rows, allocated to (week, label) cells in proportion to their size (largest remainder), sorted."""
    if n >= len(rows):
        return np.sort(rows)
    rng = np.random.default_rng(seed)
    cells = {}
    for r in rows:
        cells.setdefault((int(weeks[r]), int(labels[r])), []).append(r)
    keys = sorted(cells)
    sizes = np.array([len(cells[k]) for k in keys], dtype=float)
    quota = sizes / sizes.sum() * n
    take = np.floor(quota).astype(int)
    for i in np.argsort(-(quota - take))[: n - take.sum()]:
        take[i] += 1
    out = [rng.choice(np.array(cells[k]), t, replace=False) for k, t in zip(keys, take) if t]
    return np.sort(np.concatenate(out))


class RowSequence(lgb.Sequence):
    """Streams selected rows/columns of a memmap to LightGBM in float64 batches (LightGBM requires float64)."""
    batch_size = 4096

    def __init__(self, X, rows: np.ndarray | None = None, cols: np.ndarray | None = None):
        self.X, self.rows, self.cols = X, rows, cols
        self.n = X.shape[0] if rows is None else len(rows)

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        r = i if self.rows is None else self.rows[i]
        a = self.X[r]
        if self.cols is not None:
            a = a[..., self.cols]
        return np.asarray(a, dtype=np.float64)


def batches(X, rows: np.ndarray, cols: np.ndarray | None = None, size: int = 10000):
    """Yield float64 blocks of selected rows (for scoring large sets with little memory)."""
    for s in range(0, len(rows), size):
        a = np.asarray(X[rows[s:s + size]], dtype=np.float64)
        yield a if cols is None else a[:, cols]
