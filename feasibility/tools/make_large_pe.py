"""Makes large benign test files by appending seeded random bytes (an overlay) to a benign PE (e.g. corpus\\w64.exe).
The result is never executed; it only tests extraction speed and memory on big inputs.
usage: python tools\\make_large_pe.py corpus\\w64.exe large 10 100 200      (sizes in MB, written to folder 'large')
"""
import os, sys, numpy as np
src, out, sizes = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3:]]; os.makedirs(out, exist_ok=True); base = open(src, 'rb').read()
rng = np.random.default_rng(0)
for mb in sizes:
    p = os.path.join(out, f'{os.path.splitext(os.path.basename(src))[0]}_{mb}MB.exe')
    with open(p, 'wb') as f:
        f.write(base); left = mb * 1024 * 1024 - len(base)
        while left > 0: n = min(left, 8 << 20); f.write(rng.integers(0, 256, n, dtype=np.uint8).tobytes()); left -= n
    print('wrote', p, os.path.getsize(p))
