"""Operating-point and routing thresholds, fitted on calibration weeks only (testing plan, Section 7)."""
import numpy as np


def threshold_at_fpr(scores: np.ndarray, labels: np.ndarray, target_fpr: float) -> float:
    """Smallest threshold t with FPR(t) = P(s >= t | benign) <= target_fpr (ties handled conservatively)."""
    b = np.sort(scores[labels == 0])[::-1]
    if len(b) == 0:
        raise ValueError("no benign calibration scores")
    k = int(np.floor(target_fpr * len(b)))
    if k >= len(b):
        raise ValueError("target_fpr allows every benign file to be flagged; choose a smaller operating point")
    t = float(np.nextafter(b[k], np.inf))
    assert (b >= t).sum() <= k
    return t


def routing_band(s_local, server_pred, labels, budget: float, target_fpr: float):
    """Escalation band [lo, hi) on the local score that escalates round(budget * n) calibration files and maximises
    recall subject to overall FPR <= target_fpr. Outside the band: s < lo -> benign, s >= hi -> malicious; inside:
    the server decision. Returns a dict, or None if no band meets the FPR constraint."""
    n = len(s_local)
    k = int(round(budget * n))
    order = np.argsort(s_local, kind="stable")
    s = s_local[order]; y = labels[order].astype(np.int64); sp = server_pred[order].astype(np.int64)
    if k <= 0 or k > n:
        raise ValueError("budget must give 1..n escalated files")
    P, N = y.sum(), (1 - y).sum()
    cy = np.concatenate([[0], np.cumsum(y)]); cb = np.concatenate([[0], np.cumsum(1 - y)])
    cys = np.concatenate([[0], np.cumsum(y * sp)]); cbs = np.concatenate([[0], np.cumsum((1 - y) * sp)])
    i = np.arange(0, n - k + 1)
    tp = (cy[n] - cy[i + k]) + (cys[i + k] - cys[i])          # above band: malicious; in band: server says malicious
    fp = (cb[n] - cb[i + k]) + (cbs[i + k] - cbs[i])
    ok = fp <= np.floor(target_fpr * N)
    if not ok.any():
        return None
    cand = np.flatnonzero(ok)
    best = cand[np.lexsort((fp[cand], -tp[cand]))[0]]       # max recall, then fewest false positives
    lo = float(s[best]); hi = float(s[best + k]) if best + k < n else None   # None = no upper edge (JSON-safe)
    hi_v = np.inf if hi is None else hi
    # Ties in s can make the band rule select a slightly different set than the sorted positions, so the
    # reported calibration figures are recomputed with the rule itself.
    esc = (s_local >= lo) & (s_local < hi_v)
    pred = np.where(esc, server_pred.astype(bool), s_local >= hi_v)
    yb = labels.astype(bool)
    rec = float(pred[yb].mean()) if P else None; fpr = float(pred[~yb].mean()) if N else None
    return {"budget": budget, "lo": lo, "hi": hi, "cal_recall": rec, "cal_fpr": fpr, "cal_escalated": int(esc.sum()),
            "meets_target_on_calibration": fpr is not None and fpr <= target_fpr}
