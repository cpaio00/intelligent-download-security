"""Train compact LightGBM models on the prototype's 1,024 feature positions of the synthetic EMBER-shaped matrix,
export them with dump_model(), and save held-out test vectors with Python raw scores for the JavaScript check.
Synthetic data only: the models are for size/speed/equivalence tests, never for detection results.
usage: python compact\\compact_bench.py --data D:\\sentinelpe\\synth.npy --train-rows 100000 --out compact_models
Test rows are the LAST --test-rows rows of the matrix and never overlap the training rows.
"""
import argparse, json, os, sys, time, numpy as np, lightgbm as lgb
ap = argparse.ArgumentParser(); ap.add_argument('--data', required=True); ap.add_argument('--train-rows', type=int, default=100000)
ap.add_argument('--test-rows', type=int, default=2000); ap.add_argument('--out', default='compact_models'); a = ap.parse_args()
Xm = np.load(a.data, mmap_mode='r'); y = np.load(a.data[:-4] + '_y.npy', mmap_mode='r'); T = Xm.shape[0]
if T < a.train_rows + a.test_rows:
    sys.exit(f'{a.data} has {T} rows; need train-rows + test-rows = {a.train_rows + a.test_rows}. Generate more rows or lower --train-rows.')
# EMBER2024 positions of the groups the exploratory JS prototype computes: general, histogram, byteentropy, strings,
# header, section (0-993) and datadirectories dims 0-29 (2405-2434) = 1,024 columns.
cols = np.r_[0:994, 2405:2435]; assert cols.size == 1024
X = np.asarray(Xm[:a.train_rows][:, cols]); Xt = np.asarray(Xm[T - a.test_rows:T][:, cols]); yt = np.asarray(y[:a.train_rows])
assert Xt.shape[0] == a.test_rows > 0
os.makedirs(a.out, exist_ok=True)
for trees, leaves in [(100, 31), (300, 64), (500, 64)]:
    P = {'objective': 'binary', 'num_leaves': leaves, 'learning_rate': 0.1, 'min_data_in_leaf': 100, 'num_threads': 2, 'verbose': -1, 'seed': 1}
    t = time.perf_counter(); b = lgb.train(P, lgb.Dataset(X, yt), num_boost_round=trees); tt = time.perf_counter() - t
    name = os.path.join(a.out, f'm{trees}x{leaves}'); js = json.dumps(b.dump_model(), separators=(',', ':'))
    open(name + '.json', 'w').write(js); b.save_model(name + '.txt')
    json.dump({'X': Xt.tolist(), 'raw': b.predict(Xt, raw_score=True).tolist(), 'train_rows': a.train_rows, 'test_rows': [T - a.test_rows, T]}, open(name + '_test.json', 'w'))
    print(f'{os.path.basename(name)}: features {b.num_feature()} | trees {b.num_trees()} | JSON {len(js)/1e6:.2f} MB | train {tt:.1f} s | test vectors {Xt.shape[0]}')
