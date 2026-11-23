import numpy as np
import pytest

from sentinelpe_ml.data import RowSequence, open_vectors, official_week, stratified_sample, week_rows
from sentinelpe_ml.features import CATEGORICAL, N_FEATURES, categorical_positions, columns, local_columns


def test_local_columns_are_parity_passed_groups_only():
    c = local_columns()
    assert len(c) == 768
    assert not np.isin(np.arange(263, 519), c).any()          # byteentropy (failed parity)
    assert not np.isin(np.arange(994, 2405), c).any()         # imports, exports
    assert np.isin(np.arange(2405, 2435), c).all() and not np.isin(np.arange(2435, 2568), c).any()
    assert [c[p] for p in categorical_positions(c)] == list(CATEGORICAL)


def test_columns_rejects_bad_dims():
    with pytest.raises(ValueError):
        columns({"general": range(0, 8)})


def test_open_vectors_dat_and_npy(tmp_path):
    X = np.arange(3 * N_FEATURES, dtype=np.float32).reshape(3, N_FEATURES)
    X.tofile(tmp_path / "X_train.dat"); np.array([0, 1, -1], np.int32).tofile(tmp_path / "y_train.dat")
    Xm, y = open_vectors(str(tmp_path / "X_train.dat"))
    assert Xm.shape == (3, N_FEATURES) and Xm[2, 5] == X[2, 5] and list(y) == [0, 1, -1]
    np.array([0, 1], np.int32).tofile(tmp_path / "y_bad.dat")
    with pytest.raises(ValueError):
        open_vectors(str(tmp_path / "X_train.dat"), str(tmp_path / "y_bad.dat"))


def test_official_week():
    assert official_week("2023-09-24T00:00:00Z") == 0
    assert official_week("2023-09-30T23:59:59") == 0
    assert official_week("2023-10-01") == 1
    assert official_week(1695513600 + 7 * 86400 * 51) == 51      # 2023-09-24 00:00 UTC + 51 weeks


def test_week_rows_and_stratified_sample():
    rng = np.random.default_rng(0)
    weeks = rng.integers(0, 64, 20000); labels = rng.choice([0, 1, -1], 20000, p=[0.5, 0.45, 0.05])
    rows = week_rows(weeks, labels, 0, 39)
    assert ((weeks[rows] <= 39) & (labels[rows] >= 0)).all()
    s1 = stratified_sample(rows, weeks, labels, 3000, seed=1); s2 = stratified_sample(rows, weeks, labels, 3000, seed=1)
    assert len(s1) == 3000 and len(np.unique(s1)) == 3000 and np.array_equal(s1, s2) and np.isin(s1, rows).all()
    for w in (0, 20, 39):                                     # per-week share preserved to within rounding
        assert abs((weeks[s1] == w).sum() - (weeks[rows] == w).sum() * 3000 / len(rows)) <= 2


def test_row_sequence_selects_rows_and_columns():
    X = np.arange(40, dtype=np.float32).reshape(10, 4)
    seq = RowSequence(X, np.array([1, 3, 5]), np.array([0, 2]))
    assert len(seq) == 3 and seq[1].tolist() == [12.0, 14.0] and seq[0:2].dtype == np.float64
