"""SYNTHETIC development models so that the extension and server can be built and tested before EMBER2024 is
available. The data are random numbers; the models say nothing about malware. model_version starts with
'DEV-SYNTHETIC' and the extension and server display it, so a dev model cannot be mistaken for a real one."""
import json
import os

import numpy as np

from .features import CATEGORICAL, N_FEATURES, local_columns
from .thresholds import routing_band, threshold_at_fpr
from .train import save, train


def synthetic(n: int, seed: int):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, N_FEATURES)).astype(np.float32)
    X[:, list(CATEGORICAL)] = rng.integers(0, 4, (n, len(CATEGORICAL)))
    lc = local_columns(); server_only = np.setdiff1d(np.arange(N_FEATURES), lc)
    logit = 0.9 * X[:, lc[10]] + 0.6 * X[:, lc[200]] + 1.2 * X[:, server_only[5]] + 0.8 * X[:, server_only[900]]
    y = (logit + rng.normal(scale=0.7, size=n) > 0).astype(np.int32)
    weeks = np.sort(rng.integers(0, 64, n)).astype(np.int16)
    return X, y, weeks


def make_dev_models(out: str, n: int = 20000, seed: int = 7, rounds: int = 40):
    os.makedirs(out, exist_ok=True)
    X, y, weeks = synthetic(n, seed)
    tr, cal = np.flatnonzero(weeks <= 39), np.flatnonzero((weeks >= 46) & (weeks <= 51))
    info = {"synthetic": True, "seed": seed}
    sb, sm = train(X, y, tr, np.arange(N_FEATURES), rounds, "server", {"min_data_in_leaf": 20}, info)
    lb, lm = train(X, y, tr, local_columns(), rounds, "local", {"min_data_in_leaf": 20}, info)
    for m in (sm, lm):
        m["model_version"] = "DEV-SYNTHETIC-" + m["model_version"]
    sl = lb.predict(X[cal][:, local_columns()]); ss = sb.predict(X[cal]); yc = y[cal]
    tl, ts = threshold_at_fpr(sl, yc, 0.01), threshold_at_fpr(ss, yc, 0.01)
    lm["thresholds"]["0.01"] = {"decision": tl, "bands": [routing_band(sl, ss >= ts, yc, b, 0.01) for b in (0.1, 0.2, 0.3)]}
    sm["thresholds"]["0.01"] = {"decision": ts}
    save(sb, sm, os.path.join(out, "server_model")); save(lb, lm, os.path.join(out, "local_model"))
    from .export import export_browser
    export_browser(lb, lm, os.path.join(out, "browser"))
    print(json.dumps({"out": out, "server": sm["model_version"], "local": lm["model_version"], "t_local": tl, "t_server": ts}, indent=1))
