"""Train a full-width (2,568-feature) LightGBM model on the synthetic matrix, for server, SHAP and FastAPI benchmarks.
Synthetic data: the model is meaningless for detection. Training rows are [0, train-rows); the last 2,000 rows are reserved.
usage: python server\\make_full_model.py --data D:\\sentinelpe\\synth.npy --train-rows 50000 --rounds 100 --out full_model.txt
"""
import argparse, sys, time, numpy as np, lightgbm as lgb
ap = argparse.ArgumentParser(); ap.add_argument('--data', required=True); ap.add_argument('--train-rows', type=int, default=50000)
ap.add_argument('--rounds', type=int, default=100); ap.add_argument('--out', default='full_model.txt'); a = ap.parse_args()
Xm = np.load(a.data, mmap_mode='r'); y = np.load(a.data[:-4] + '_y.npy', mmap_mode='r')
if Xm.shape[0] < a.train_rows + 2000: sys.exit(f'{a.data} has {Xm.shape[0]} rows; need at least train-rows + 2000 = {a.train_rows + 2000}')
P = {'objective': 'binary', 'num_leaves': 64, 'learning_rate': 0.1, 'min_data_in_leaf': 100, 'num_threads': 2, 'verbose': -1,
     'bin_construct_sample_cnt': 20000, 'force_col_wise': True, 'seed': 1}
t = time.perf_counter(); b = lgb.train(P, lgb.Dataset(np.asarray(Xm[:a.train_rows]), np.asarray(y[:a.train_rows])), num_boost_round=a.rounds)
b.save_model(a.out); print(f'saved {a.out}: {b.num_feature()} features, {b.num_trees()} trees, {time.perf_counter() - t:.1f} s')
