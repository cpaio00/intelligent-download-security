"""Streamed LightGBM training on selected rows/columns of a memory-mapped matrix, with a metadata record."""
import datetime as dt
import hashlib
import json
import platform
import time

import lightgbm as lgb
import numpy as np

from . import SCHEMA_VERSION
from .data import RowSequence
from .features import N_FEATURES, categorical_positions

BASE_PARAMS = {
    "objective": "binary", "num_leaves": 64, "learning_rate": 0.1, "min_data_in_leaf": 100, "num_threads": 2,
    "verbose": -1, "max_bin": 255, "bin_construct_sample_cnt": 20000, "force_col_wise": True, "seed": 1,
}


def train(X, y, rows: np.ndarray, cols: np.ndarray, rounds: int, role: str, params: dict | None = None,
          sample_info: dict | None = None):
    """Train on X[rows][:, cols]. Labels must be 0/1. Returns (booster, metadata)."""
    if role not in ("server", "local"):
        raise ValueError("role must be 'server' or 'local'")
    labels = np.asarray(y[rows], dtype=np.float64)
    if not np.isin(labels, (0, 1)).all():
        raise ValueError("training rows include labels other than 0/1 (exclude unlabelled -1 rows)")
    P = dict(BASE_PARAMS, **(params or {}))
    cat = categorical_positions(cols)
    t0 = time.perf_counter()
    ds = lgb.Dataset(RowSequence(X, rows, cols), labels, params=P, free_raw_data=True,
                     categorical_feature=cat if cat else "auto")
    ds.construct()
    t1 = time.perf_counter()
    booster = lgb.train(P, ds, num_boost_round=rounds)
    t2 = time.perf_counter()
    text = booster.model_to_string()
    meta = {
        "schema_version": SCHEMA_VERSION, "role": role,
        "model_version": f"{role}-{hashlib.sha256(text.encode()).hexdigest()[:12]}",
        "columns": [int(c) for c in cols], "n_input_features": N_FEATURES, "categorical_positions": cat,
        "lightgbm_version": lgb.__version__, "params": P, "rounds": rounds, "trees": booster.num_trees(),
        "train_rows": int(len(rows)), "train_positive_rate": float(labels.mean()),
        "sample": sample_info or {}, "construct_s": round(t1 - t0, 1), "train_s": round(t2 - t1, 1),
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "platform": platform.platform(),
        "thresholds": {},
    }
    return booster, meta


def save(booster, meta: dict, path_prefix: str):
    booster.save_model(path_prefix + ".txt")
    with open(path_prefix + ".meta.json", "w") as f:
        json.dump(meta, f, indent=1, allow_nan=False)   # browser JSON has no NaN or Infinity


def load(path_prefix: str):
    with open(path_prefix + ".meta.json") as f:
        meta = json.load(f)
    return lgb.Booster(model_file=path_prefix + ".txt"), meta
