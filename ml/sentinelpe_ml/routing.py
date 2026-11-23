"""Offline routing evaluation on test weeks: Always Local, Always Server, Confidence, Random and Oracle routing,
Wilson intervals and the week-level block bootstrap of the superiority criterion (ADR 0003).
The evaluation assumes consent for every escalation (largest possible upload count)."""
import numpy as np


def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    lo = 0.0 if k == 0 else max(0.0, c - h); hi = 1.0 if k == n else min(1.0, c + h)   # exact at the edges
    return (float(lo), float(hi))


def metrics(pred: np.ndarray, y: np.ndarray, escalated: np.ndarray | None = None, weeks: np.ndarray | None = None):
    yb = y.astype(bool); pred = pred.astype(bool)
    tp, P = int((pred & yb).sum()), int(yb.sum()); fp, N = int((pred & ~yb).sum()), int((~yb).sum())
    m = {"recall": tp / P if P else float("nan"), "fpr": fp / N if N else float("nan"), "fpr_wilson95": wilson(fp, N),
         "tp": tp, "positives": P, "fp": fp, "negatives": N,
         "upload_rate": float(escalated.mean()) if escalated is not None else None,
         "escalated": int(escalated.sum()) if escalated is not None else None}
    if weeks is not None:
        m["weekly"] = {int(w): {"recall": float(pred[(weeks == w) & yb].mean()) if ((weeks == w) & yb).any() else None,
                                "fpr": float(pred[(weeks == w) & ~yb].mean()) if ((weeks == w) & ~yb).any() else None}
                       for w in np.unique(weeks)}
    return m


def confidence_pred(s_local, server_pred, band):
    hi = np.inf if band["hi"] is None else band["hi"]
    esc = (s_local >= band["lo"]) & (s_local < hi)
    return np.where(esc, server_pred, s_local >= hi), esc


def random_escalation(n: int, k: int, seed: int) -> np.ndarray:
    esc = np.zeros(n, bool)
    esc[np.random.default_rng(seed).choice(n, k, replace=False)] = True
    return esc


def oracle_escalation(local_pred, server_pred, y, k: int) -> np.ndarray:
    """Non-deployable upper bound: escalate first the files the local model gets wrong and the server gets right,
    then (budget permitting) files where escalation cannot change correctness."""
    lw_sr = np.flatnonzero((local_pred != y) & (server_pred == y))
    neutral = np.flatnonzero((local_pred == server_pred))
    harmful = np.flatnonzero((local_pred == y) & (server_pred != y))   # used only if the budget is not yet filled
    pick = np.concatenate([lw_sr, neutral, harmful])[:k]
    esc = np.zeros(len(y), bool); esc[pick] = True
    return esc


def evaluate(s_local, s_server, y, weeks, t_local, t_server, bands, seeds, n_boot=1000, boot_seed=0):
    """Returns a dict of results per budget. `bands` come from thresholds.routing_band on calibration weeks."""
    y = y.astype(bool); lp = s_local >= t_local; sp = s_server >= t_server; n = len(y)
    out = {"always_local": metrics(lp, y, np.zeros(n, bool), weeks), "always_server": metrics(sp, y, np.ones(n, bool), weeks),
           "budgets": []}
    uw = np.unique(weeks); widx = np.searchsorted(uw, weeks)
    pos_w = np.bincount(widx, weights=y, minlength=len(uw)); neg_w = np.bincount(widx, weights=~y, minlength=len(uw))
    for band in bands:
        if band is None:
            continue
        cpred, cesc = confidence_pred(s_local, sp, band); k = int(cesc.sum())
        conf = metrics(cpred, y, cesc, weeks)
        tp_r = np.zeros((len(seeds), len(uw))); fp_r = np.zeros((len(seeds), len(uw))); rec_r = []; fpr_r = []
        for j, sd in enumerate(seeds):
            e = random_escalation(n, k, sd); rp = np.where(e, sp, lp)
            tp_r[j] = np.bincount(widx, weights=rp & y, minlength=len(uw)); fp_r[j] = np.bincount(widx, weights=rp & ~y, minlength=len(uw))
            rec_r.append(tp_r[j].sum() / y.sum()); fpr_r.append(fp_r[j].sum() / (~y).sum())
        oesc = oracle_escalation(lp, sp, y, k); orc = metrics(np.where(oesc, sp, lp), y, oesc, weeks)
        # Week-level block bootstrap of the recall difference (confidence - mean random), resampling whole weeks.
        tp_c = np.bincount(widx, weights=cpred & y, minlength=len(uw)); tp_rm = tp_r.mean(0)
        rng = np.random.default_rng(boot_seed); diffs = []
        for _ in range(n_boot):
            w = rng.integers(0, len(uw), len(uw)); p = pos_w[w].sum()
            if p > 0:
                diffs.append((tp_c[w].sum() - tp_rm[w].sum()) / p)
        lo95, hi95 = (np.percentile(diffs, [2.5, 97.5]).tolist() if diffs else [float("nan")] * 2)
        rand = {"recall_mean": float(np.mean(rec_r)), "recall_p2_5": float(np.percentile(rec_r, 2.5)),
                "recall_p97_5": float(np.percentile(rec_r, 97.5)), "fpr_mean": float(np.mean(fpr_r)), "repetitions": len(seeds)}
        better = (conf["recall"] > rand["recall_mean"]) and (conf["fpr"] <= rand["fpr_mean"]) and (lo95 > 0)
        out["budgets"].append({"band": band, "escalated": k, "confidence": conf, "random": rand, "oracle": orc,
                               "recall_diff_ci95": [lo95, hi95], "confidence_better_than_random": bool(better)})
    return out


def choose_repetitions(s_local, s_server, y, t_local, t_server, k: int, tolerance: float,
                       candidates=(100, 200, 500, 1000), seed0: int = 0):
    """Stability test on calibration scores: smallest R whose mean and 2.5/97.5 percentiles of random-routing recall
    differ from those at the largest R by less than `tolerance` (fixed in advance)."""
    y = y.astype(bool); lp = s_local >= t_local; sp = s_server >= t_server; n = len(y)
    rec = np.array([np.where(random_escalation(n, k, seed0 + i), sp, lp)[y].mean() for i in range(max(candidates))])
    stats = {R: np.array([rec[:R].mean(), *np.percentile(rec[:R], [2.5, 97.5])]) for R in candidates}
    ref = stats[max(candidates)]
    for R in sorted(candidates):
        if np.abs(stats[R] - ref).max() < tolerance:
            return R, {r: v.tolist() for r, v in stats.items()}
    return max(candidates), {r: v.tolist() for r, v in stats.items()}


def weekly_recall_sd(pred, y, weeks) -> float:
    """delta for SQ2: SD of weekly recall (e.g. Always Server on validation weeks)."""
    r = [pred[(weeks == w) & y.astype(bool)].mean() for w in np.unique(weeks) if ((weeks == w) & y.astype(bool)).any()]
    return float(np.std(r, ddof=1)) if len(r) > 1 else float("nan")
