# Generates LightGBM models covering every split behaviour, plus targeted test vectors and Python raw scores.
# Synthetic data only: tests the export/evaluation method, not detection performance.
import json, numpy as np, lightgbm as lgb, os
rng = np.random.default_rng(2026)
def data(n, d, ncat=0, nan=0.0, zeros=0.0, hicard=False):
    X = rng.normal(size=(n, d))
    for j in range(ncat): X[:, j] = rng.integers(0, 200 if (hicard and j == 0) else 8, n)
    if zeros: X[rng.random((n, d)) < zeros] = 0.0
    if nan: X[rng.random((n, d)) < nan] = np.nan
    s = X[:, ncat] * 1.3 - np.nan_to_num(X[:, ncat + 1]) + (np.nan_to_num(X[:, 0]) % 3 == 0 if ncat else 0)
    s = s + np.isnan(X[:, ncat + 2]) * 1.5 + (X[:, ncat + 3] == 0) * 1.2 + rng.normal(size=n) * 0.5
    return X, (s > 0.2).astype(int)
CASES = {
 'numeric_small':      dict(d=20, trees=50,  leaves=15, data=dict(), params={}),
 'categorical_nan':    dict(d=30, trees=150, leaves=31, data=dict(ncat=3, nan=0.08, hicard=True), params={}, cat=[0, 1, 2]),
 'zero_as_missing':    dict(d=20, trees=100, leaves=31, data=dict(zeros=0.3), params={'zero_as_missing': True}),
 'missing_disabled':   dict(d=20, trees=100, leaves=31, data=dict(nan=0.1), params={'use_missing': False}),
 'categorical_missing_disabled': dict(d=30, trees=150, leaves=31, data=dict(ncat=3, nan=0.08), params={'use_missing': False}, cat=[0, 1, 2]),
 'large_mixed':        dict(d=200, trees=500, leaves=64, data=dict(ncat=2, nan=0.05, zeros=0.2), params={}, cat=[0, 1]),
}
summary = {}
for name, c in CASES.items():
    X, y = data(12000, c['d'], **c['data']); P = {'objective': 'binary', 'num_leaves': c['leaves'], 'verbose': -1, 'seed': 0, 'min_data_in_leaf': 20, **c['params']}
    b = lgb.train(P, lgb.Dataset(X[:9000], y[:9000], categorical_feature=c.get('cat', 'auto')), num_boost_round=c['trees'])
    m = b.dump_model(); json.dump(m, open(f'{name}.json', 'w')); b.save_model(f'{name}.txt')
    tests = [r for r in X[9000:11000]]                                       # 1) ordinary held-out rows (with NaN/zeros where generated)
    nodes = []
    def walk(n):
        if 'leaf_value' in n: return
        nodes.append(n); walk(n['left_child']); walk(n['right_child'])
    for t in m['tree_info']: walk(t['tree_structure'])
    pick = rng.choice(len(nodes), size=min(400, len(nodes)), replace=False)
    base = X[11000]
    for k in pick:                                                           # 2) targeted vectors per split node
        n = nodes[k]; f = n['split_feature']
        if n['decision_type'] == '<=':
            th = float(n['threshold'])
            for v in (th, np.nextafter(th, -np.inf), np.nextafter(th, np.inf), np.nan, 0.0, -0.0, 1e-36, -1e-36):
                r = base.copy(); r[f] = v; tests.append(r)
        else:
            cats = [int(x) for x in str(n['threshold']).split('||')]
            for v in (cats[0], cats[0] + 0.7, max(cats) + 1, -1, -0.5, np.nan, 0.0, 1e12):
                r = base.copy(); r[f] = v; tests.append(r)
    T = np.array(tests, dtype=np.float64)
    T32 = T.astype(np.float32).astype(np.float64)                            # 3) the same vectors as float32 inputs (the real pipeline)
    allT = np.vstack([T, T32])
    raw = b.predict(allT, raw_score=True)
    raw_file = lgb.Booster(model_file=f'{name}.txt').predict(allT, raw_score=True)   # reference 2: model reloaded from disk
    enc = lambda v: None if np.isnan(v) else (('Infinity' if v > 0 else '-Infinity') if np.isinf(v) else float(v))  # JSON has no NaN/Infinity
    json.dump({'X': [[enc(v) for v in r] for r in allT], 'raw': [float(v) for v in raw], 'raw_file': [float(v) for v in raw_file]}, open(f'{name}_test.json', 'w')); np.save(f'{name}_X.npy', allT)
    kinds = {}
    for n in nodes: kinds[(n['decision_type'], n['missing_type'], bool(n['default_left']))] = kinds.get((n['decision_type'], n['missing_type'], bool(n['default_left'])), 0) + 1
    summary[name] = {'trees': c['trees'], 'leaves': c['leaves'], 'features': c['d'], 'test_vectors': len(allT), 'json_MB': round(os.path.getsize(f'{name}.json') / 1e6, 2),
                     'split_kinds': {f'{a} missing={m_} default_left={d}': k for (a, m_, d), k in sorted(kinds.items())}}
json.dump(summary, open('cases_summary.json', 'w'), indent=1)
for k, v in summary.items(): print(k, v)
