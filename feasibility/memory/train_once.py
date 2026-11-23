"""Child process: build a LightGBM Dataset from rows [0, N) of a .npy matrix and train. Started by memory_sweep.py.
usage: python train_once.py <X.npy|X_train.dat> <N> <mode numpy|sequence> <rounds> <json params> [index.npy]
X_train.dat / y_train.dat: thrember vectorised files (raw float32 / int32 memmaps, 2,568 columns).
index.npy (optional): sorted row numbers to use, e.g. labelled rows of training weeks only; the first N are used.
Prints one JSON line with timings. Synthetic data only: no accuracy is computed.
"""
import json, sys, time, numpy as np, lightgbm as lgb
path, N, mode, rounds, P = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), json.loads(sys.argv[5])
if path.endswith('.dat'):                    # thrember layout: X_<subset>.dat float32, y_<subset>.dat int32
    Xm = np.memmap(path, dtype=np.float32, mode='r').reshape(-1, 2568)
    y = np.memmap(path.replace('X_', 'y_'), dtype=np.int32, mode='r')
else:
    Xm = np.load(path, mmap_mode='r'); y = np.load(path[:-4] + '_y.npy', mmap_mode='r')
idx = np.load(sys.argv[6]) if len(sys.argv) > 6 else None
if idx is not None:
    if idx.size < N: sys.exit(f'index file has only {idx.size} rows, N={N} requested')
    idx = np.sort(idx[:N]); assert idx[-1] < Xm.shape[0]
elif Xm.shape[0] < N: sys.exit(f'{path} has only {Xm.shape[0]} rows, N={N} requested')
y = np.asarray(y[idx] if idx is not None else y[:N], dtype=np.float64)
if (y < 0).any(): sys.exit('unlabelled rows (label -1) selected: build the index from labelled rows only')
print(json.dumps({'phase': 'start'}), flush=True); t0 = time.perf_counter()
if mode == 'numpy':                         # what thrember.read_vectorized_features + lgb.Dataset does: full copy into RAM
    X = np.array(Xm[idx] if idx is not None else Xm[:N]); ds = lgb.Dataset(X, y, params=P, free_raw_data=True)
else:                                       # streams rows from the memory-mapped file
    class Seq(lgb.Sequence):
        batch_size = 4096
        def __init__(s, a, n, ix): s.a, s.n, s.ix = a, n, ix
        def __getitem__(s, i):                                          # int or slice; LightGBM requires float64 batches
            return np.asarray(s.a[i] if s.ix is None else s.a[s.ix[i]], dtype=np.float64)
        def __len__(s): return s.n
    ds = lgb.Dataset(Seq(Xm, N, idx), y, params=P, free_raw_data=True)
ds.construct(); t1 = time.perf_counter()
if mode == 'numpy': del X
print(json.dumps({'phase': 'constructed', 'construct_s': round(t1 - t0, 1)}), flush=True)
b = lgb.train(P, ds, num_boost_round=rounds); t2 = time.perf_counter()
print(json.dumps({'phase': 'done', 'construct_s': round(t1 - t0, 1), 'train_s': round(t2 - t1, 1), 'trees': b.num_trees()}), flush=True)
