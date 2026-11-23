"""Synthetic EMBER-SHAPED matrix (2,568 float32 columns) for memory and speed tests only.
NOT EMBER2024 data: any accuracy obtained from it is meaningless and must never be reported.
usage: python make_synth.py <rows> <out.npy>        writes <out.npy> and <out>_y.npy
Generated content is identical for a given row count prefix (fixed seed, fixed block size).
"""
import os, shutil, sys, numpy as np
N = int(sys.argv[1]); out = os.path.abspath(sys.argv[2]); D = 2568; B = 20000
need = N * D * 4
free = shutil.disk_usage(os.path.dirname(out)).free
if free < need * 1.1: sys.exit(f'Not enough disk on {os.path.dirname(out)}: need {need/1e9:.1f} GB, free {free/1e9:.1f} GB')
X = np.lib.format.open_memmap(out, mode='w+', dtype=np.float32, shape=(N, D)); y = np.zeros(N, np.int8)
rng = np.random.default_rng(0); dense = int(D * 0.4)
for s in range(0, N, B):
    e = min(N, s + B); n = B; blk = np.zeros((n, D), np.float32)   # always draw a full block -> any N is a prefix of a larger N
    blk[:, :dense] = rng.normal(size=(n, dense))
    sp = rng.random((n, D - dense)) < 0.1; blk[:, dense:] = np.where(sp, rng.integers(1, 50, (n, D - dense)), 0)
    lab = (blk[:, 0] + 0.5 * blk[:, 1] - 0.3 * (blk[:, dense] > 0) + rng.normal(size=n) * 0.8) > 0
    X[s:e] = blk[:e - s]; y[s:e] = lab[:e - s]
X.flush(); np.save(out[:-4] + '_y.npy', y); print(f'wrote {N} rows x {D} cols = {X.nbytes/1e9:.2f} GB to {out}')
