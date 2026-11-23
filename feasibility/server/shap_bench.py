"""Server-side prediction and SHAP timing with the FULL 2,568-feature model on held-out synthetic rows.
usage: python server\\shap_bench.py --data D:\\sentinelpe\\synth.npy --model full_model.txt
Memory: private bytes on Windows, RssAnon on Linux (excludes memory-mapped file pages).
"""
import argparse, sys, time, numpy as np, lightgbm as lgb, psutil
ap = argparse.ArgumentParser(); ap.add_argument('--data', required=True); ap.add_argument('--model', default='full_model.txt')
ap.add_argument('--rows', type=int, default=200); a = ap.parse_args()
def private_mb():
    if sys.platform.startswith('linux'):
        return next(int(l.split()[1]) for l in open('/proc/self/status') if l.startswith('RssAnon')) / 1024
    mi = psutil.Process().memory_info(); return (getattr(mi, 'private', 0) or mi.rss) / 1e6
b = lgb.Booster(model_file=a.model); Xm = np.load(a.data, mmap_mode='r'); T = Xm.shape[0]
X = np.asarray(Xm[T - a.rows:T], dtype=np.float64)
if X.shape[1] != b.num_feature(): sys.exit(f'model expects {b.num_feature()} features, data has {X.shape[1]}')
assert X.shape[0] == a.rows > 0
t = time.perf_counter(); [b.predict(X[i:i+1]) for i in range(a.rows)]; p = (time.perf_counter() - t) / a.rows * 1000
t = time.perf_counter(); C = np.vstack([b.predict(X[i:i+1], pred_contrib=True) for i in range(a.rows)]); c = (time.perf_counter() - t) / a.rows * 1000
# SHAP additivity check: contributions + expected value must equal the raw score
gap = np.abs(C.sum(1) - b.predict(X, raw_score=True)).max()
line = f'rows {a.rows} | predict {p:.2f} ms/file | pred_contrib (TreeSHAP) {c:.2f} ms/file | additivity max gap {gap:.2e}'
try:
    import shap; e = shap.TreeExplainer(b); t = time.perf_counter(); e.shap_values(X[:20]); s = (time.perf_counter() - t) / 20 * 1000
    line += f' | shap.TreeExplainer {s:.2f} ms/file'
except ImportError: line += ' | shap package not installed (skipped)'
print(line + f' | private memory {private_mb():.0f} MB'); sys.exit(0 if gap < 1e-6 else 1)
