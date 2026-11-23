import json
import os
import subprocess

import numpy as np
import pytest

from sentinelpe_ml.devmodels import synthetic
from sentinelpe_ml.export import export_browser
from sentinelpe_ml.features import N_FEATURES, local_columns
from sentinelpe_ml.score import score
from sentinelpe_ml.train import load, save, train

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def data():
    return synthetic(6000, seed=3)


def test_train_save_load_score(tmp_path, data):
    X, y, weeks = data
    rows = np.flatnonzero(weeks <= 39)
    b, meta = train(X, y, rows, local_columns(), 20, "local", {"min_data_in_leaf": 20})
    assert meta["train_rows"] == len(rows) and meta["columns"] == local_columns().tolist() and meta["categorical_positions"]
    save(b, meta, str(tmp_path / "m")); b2, meta2 = load(str(tmp_path / "m"))
    test = np.flatnonzero(weeks >= 52)
    s = score(b2, X, test, local_columns(), size=97)
    assert np.allclose(s, b.predict(X[test][:, local_columns()]))
    with pytest.raises(ValueError):
        score(b2, X, test, np.arange(N_FEATURES))


def test_train_rejects_unlabelled_rows(data):
    X, y, _ = data
    y2 = y.copy(); y2[0] = -1
    with pytest.raises(ValueError):
        train(X, y2, np.arange(100), local_columns(), 2, "local")


def test_browser_export_matches_python_raw_scores(tmp_path, data):
    X, y, weeks = data
    b, meta = train(X, y, np.flatnonzero(weeks <= 39), local_columns(), 30, "local", {"min_data_in_leaf": 20})
    meta["thresholds"]["0.01"] = {"decision": 0.5, "bands": []}
    export_browser(b, meta, str(tmp_path))
    test = X[np.flatnonzero(weeks >= 52)][:200][:, local_columns()].astype(np.float64)
    test[0, 3] = np.nan; test[1, 0] = 0.0                     # missing and zero inputs
    (tmp_path / "x.json").write_text(json.dumps([[None if np.isnan(v) else float(v) for v in r] for r in test]))
    js = f"""
import fs from 'node:fs'; import {{ prepare, rawScore }} from '{ROOT}/extension/lib/lgbm_eval.mjs';
const m = prepare(JSON.parse(fs.readFileSync('{tmp_path}/local_model.json')));
const X = JSON.parse(fs.readFileSync('{tmp_path}/x.json')); console.log(JSON.stringify(X.map(x => rawScore(m, x))));"""
    out = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, check=True).stdout
    assert np.array_equal(np.array(json.loads(out)), b.predict(test, raw_score=True))   # bit-identical
    meta_js = json.loads((tmp_path / "local_model.meta.json").read_text())
    assert meta_js["columns"] == local_columns().tolist() and "thresholds" in meta_js


def test_export_refuses_server_model(tmp_path, data):
    X, y, weeks = data
    b, meta = train(X, y, np.arange(500), np.arange(N_FEATURES), 2, "server", {"min_data_in_leaf": 20})
    with pytest.raises(ValueError):
        export_browser(b, meta, str(tmp_path))
