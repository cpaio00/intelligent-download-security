"""EMBER2024 (thrember, commit 0ef753e) feature layout and the local feature set.

Offsets were read from thrember.features.PEFeatureExtractor. The local model may only use groups that passed the
parity test (O1); LOCAL_GROUPS records the current exploratory status and must be updated from the real parity
results before the local model is trained.
"""
import numpy as np

N_FEATURES = 2568
GROUPS = {  # name: (offset, dims)
    "general": (0, 7), "histogram": (7, 256), "byteentropy": (263, 256), "strings": (519, 177),
    "header": (696, 74), "section": (770, 224), "imports": (994, 1282), "exports": (2276, 129),
    "datadirectories": (2405, 34), "richheader": (2439, 33), "authenticode": (2472, 8), "pefilewarnings": (2480, 88),
}
# Categorical features used by thrember's reference train_model (general is_pe/start bytes; header dims 701, 702).
CATEGORICAL = (2, 3, 4, 5, 6, 701, 702)

# Exploratory parity status (feasibility audit, Nov 2026): byteentropy FAILED; datadirectories only dims 0-29 pass.
LOCAL_GROUPS = {"general": None, "histogram": None, "strings": None, "header": None, "section": None,
                "datadirectories": range(0, 30)}


def columns(groups: dict) -> np.ndarray:
    """Absolute column indices for {group: None (all dims) | iterable of dims within the group}."""
    cols = []
    for g, dims in groups.items():
        off, n = GROUPS[g]
        idx = range(n) if dims is None else dims
        if any(d < 0 or d >= n for d in idx):
            raise ValueError(f"dimension out of range for group {g}")
        cols.extend(off + d for d in idx)
    cols = np.array(sorted(cols), dtype=np.int64)
    if len(np.unique(cols)) != len(cols):
        raise ValueError("duplicate columns")
    return cols


def local_columns() -> np.ndarray:
    return columns(LOCAL_GROUPS)


def categorical_positions(cols: np.ndarray) -> list:
    """Positions (within cols) of reference categorical features that are present in cols."""
    pos = {int(c): i for i, c in enumerate(cols)}
    return [pos[c] for c in CATEGORICAL if c in pos]
