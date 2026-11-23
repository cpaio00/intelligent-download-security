import itertools

import numpy as np
import pytest

from sentinelpe_ml.routing import (choose_repetitions, confidence_pred, evaluate, metrics, oracle_escalation,
                                   random_escalation, weekly_recall_sd, wilson)
from sentinelpe_ml.thresholds import routing_band, threshold_at_fpr


def scores(n=4000, seed=0):
    rng = np.random.default_rng(seed); y = rng.random(n) < 0.4
    sl = np.clip(rng.normal(np.where(y, 0.65, 0.35), 0.18), 0, 1); ss = np.clip(rng.normal(np.where(y, 0.8, 0.2), 0.12), 0, 1)
    return sl, ss, y.astype(int), np.sort(rng.integers(52, 64, n))


def test_wilson_reference_values():
    lo, hi = wilson(10, 100)
    assert abs(lo - 0.0552) < 1e-3 and abs(hi - 0.1744) < 1e-3
    assert wilson(0, 50)[0] == 0.0


def test_threshold_at_fpr_meets_target_and_is_minimal():
    sl, _, y, _ = scores()
    for tgt in (0.01, 0.05, 0.2):
        t = threshold_at_fpr(sl, y, tgt); b = sl[y == 0]
        assert (b >= t).mean() <= tgt
        assert (b >= np.nextafter(t, -np.inf)).mean() > tgt or t <= b.min()
    with pytest.raises(ValueError):
        threshold_at_fpr(sl, y, 1.0)


def test_routing_band_is_optimal_on_small_data():
    sl, ss, y, _ = scores(60, seed=4); sp = ss >= 0.5; k = 12
    band = routing_band(sl, sp, y, k / 60, 0.1)
    assert band["cal_escalated"] == k and band["meets_target_on_calibration"]
    best = -1; srt = np.sort(sl)                               # brute force over all contiguous windows
    for i in range(0, 61 - k):
        lo, hi = srt[i], (srt[i + k] if i + k < 60 else np.inf)
        esc = (sl >= lo) & (sl < hi); pred = np.where(esc, sp, sl >= hi)
        if pred[y == 0].mean() <= 0.1 and esc.sum() == k:
            best = max(best, pred[y == 1].mean())
    assert abs(band["cal_recall"] - best) < 1e-12


def test_random_and_oracle_escalation():
    sl, ss, y, _ = scores(); lp, sp = sl >= 0.6, ss >= 0.5
    e = random_escalation(len(y), 321, seed=5); assert e.sum() == 321
    for k in (100, 800, 4000):
        o = oracle_escalation(lp, sp, y.astype(bool), k); assert o.sum() == k
        rec_o = np.where(o, sp, lp)[y == 1].mean()
        rec_r = np.where(random_escalation(len(y), k, 1), sp, lp)[y == 1].mean()
        assert rec_o >= rec_r - 1e-12


def test_evaluate_end_to_end_and_criterion():
    sl, ss, y, weeks = scores()
    cal_sl, cal_ss, cal_y, _ = scores(seed=9)
    tl, ts = threshold_at_fpr(cal_sl, cal_y, 0.01), threshold_at_fpr(cal_ss, cal_y, 0.01)
    bands = [routing_band(cal_sl, cal_ss >= ts, cal_y, b, 0.01) for b in (0.1, 0.3, 1.0)]
    r = evaluate(sl, ss, y, weeks, tl, ts, bands, seeds=range(50), n_boot=200)
    assert r["always_server"]["upload_rate"] == 1.0 and r["always_local"]["upload_rate"] == 0.0
    for b in r["budgets"]:
        assert b["oracle"]["recall"] >= b["random"]["recall_mean"] - 1e-9
        assert b["recall_diff_ci95"][0] <= b["recall_diff_ci95"][1]
        assert len(b["confidence"]["weekly"]) == 12
    full = r["budgets"][-1]                                     # escalate everything -> equals always-server
    assert full["confidence"]["escalated"] == len(y) and abs(full["confidence"]["recall"] - r["always_server"]["recall"]) < 1e-12


def test_choose_repetitions_and_delta():
    sl, ss, y, weeks = scores()
    R, stats = choose_repetitions(sl, ss, y, 0.6, 0.5, k=400, tolerance=0.01)
    assert R in (100, 200, 500, 1000) and set(stats) == {100, 200, 500, 1000}
    assert weekly_recall_sd(ss >= 0.5, y, weeks) >= 0
