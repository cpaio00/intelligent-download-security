# COMPUTE-COST check only. Scores and labels are random numbers; the recall values printed are meaningless.
# Timing check for the offline routing evaluation on synthetic scores (NOT real results; labels are random).
# Simulates N test files, finds the escalation set for confidence routing at 20 budgets,
# and repeats random routing R times per budget. usage: python checks/routing_cost.py [N] [R]
import sys, time, numpy as np
N = int(sys.argv[1]) if len(sys.argv) > 1 else 540000; R = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
rng = np.random.default_rng(0); y = rng.random(N) < 0.5
local = np.clip(rng.normal(np.where(y, .7, .3), .2), 0, 1); server = np.clip(rng.normal(np.where(y, .8, .2), .15), 0, 1)
lp, sp = local >= .5, server >= .5; t0 = time.perf_counter(); out = []
order = np.argsort(np.abs(local - .5))                               # least confident first
for budget in np.arange(.05, 1.0001, .05):
    k = int(round(budget * N)); esc = np.zeros(N, bool); esc[order[:k]] = True
    conf_recall = np.where(esc, sp, lp)[y].mean()
    rec = np.empty(R)
    for r in range(R):
        e = np.zeros(N, bool); e[np.random.default_rng(r).choice(N, k, replace=False)] = True
        rec[r] = np.where(e, sp, lp)[y].mean()
    out.append((round(budget, 2), conf_recall, rec.mean(), np.percentile(rec, [2.5, 97.5])))
print(f'N={N} budgets=20 random repetitions/budget={R}: {time.perf_counter() - t0:.1f} s total')
