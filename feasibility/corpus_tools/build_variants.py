"""Creates deterministic malformed variants of benign corpus files for robustness tests (never executed).
usage: python corpus_tools\\build_variants.py --corpus corpus --out variants
Per base file: trunc10/50/90 (first 10/50/90 % of bytes), overlay (64 KiB of seeded random bytes appended),
mut (32 seeded random bytes overwritten in bytes 2-1023, so the MZ signature is kept). Plus empty.bin,
notpe.bin (50 KB random), mz_garbage.bin ('MZ' + 10 KB random).
"""
import argparse, hashlib, json, os, numpy as np
BASES = ['numpy___generator.cp312-win_amd64.pyd', 'numpy___mt19937.cp312-win32.pyd', 'numpy___multiarray_tests.cp312-win32.pyd',
         'numpy___multiarray_umath.cp312-win_amd64.pyd', 'numpy___pocketfft_umath.cp312-win32.pyd', 'psutil___psutil_windows.pyd',
         'pywin32___winxptheme.pyd', 'pywin32__axscript.pyd', 'pywin32__servicemanager.pyd', 'pywin32__win32console.pyd', 'pywin32__win32job.pyd', 'w64.exe']
ap = argparse.ArgumentParser(); ap.add_argument('--corpus', default='corpus'); ap.add_argument('--out', default='variants'); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True); man = []
def put(name, data, base=None, kind=None):
    open(os.path.join(a.out, name), 'wb').write(data); man.append({'file': name, 'base': base, 'kind': kind, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
for i, b in enumerate(BASES):
    src = os.path.join(a.corpus, b)
    if not os.path.exists(src): print('missing base file (run build_corpus.py first):', b); continue
    d = open(src, 'rb').read(); rng = np.random.default_rng(1000 + i)
    for p in (10, 50, 90): put(f'trunc{p}__{b}', d[:len(d) * p // 100], b, f'trunc{p}')
    put(f'overlay__{b}', d + rng.integers(0, 256, 65536, dtype=np.uint8).tobytes(), b, 'overlay')
    m = bytearray(d); pos = rng.choice(np.arange(2, min(1024, len(d))), 32, replace=False)
    for p in pos: m[p] = int(rng.integers(0, 256))
    put(f'mut__{b}', bytes(m), b, 'mut')
r = np.random.default_rng(7)
put('empty.bin', b'', kind='empty'); put('notpe.bin', r.integers(0, 256, 50000, dtype=np.uint8).tobytes(), kind='random')
put('mz_garbage.bin', b'MZ' + r.integers(0, 256, 10000, dtype=np.uint8).tobytes(), kind='mz_random')
json.dump(man, open(os.path.join(a.out, 'variants_manifest.json'), 'w'), indent=1); print('variants written:', len(man))
