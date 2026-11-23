"""Rebuilds the benign parity corpus from pinned, licensed PyPI wheels and verifies every file against wheel_manifest.json.
Nothing is executed: wheels are zip files; PE files are only copied out of them.
usage: python corpus_tools\\build_corpus.py --out corpus
Also copies pip's bundled distlib launcher executables (t32/t64/w32/w64[-arm].exe, MIT licence). Their bytes depend on the
installed pip version, so their hashes are recorded in corpus_launchers.json rather than checked.
"""
import argparse, glob, hashlib, json, os, shutil, subprocess, sys, tempfile, zipfile
ap = argparse.ArgumentParser(); ap.add_argument('--out', default='corpus'); a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__)); man = json.load(open(os.path.join(here, 'wheel_manifest.json')))
os.makedirs(a.out, exist_ok=True); tmp = tempfile.mkdtemp()
for whl in sorted({m['source'] for m in man}):
    name, ver = whl.split('-')[:2]; plat = whl[:-4].split('-')[-1]; spec = f'{name}=={ver}'
    cmd = [sys.executable, '-m', 'pip', 'download', '--no-deps', '--only-binary=:all:', '-d', tmp, spec]
    if plat != 'any': cmd += ['--platform', plat, '--python-version', '3.12']
    print('downloading', whl); subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    if not os.path.exists(os.path.join(tmp, whl)): sys.exit(f'pip did not produce {whl}; files: {os.listdir(tmp)}')
ok = bad = 0
for m in man:
    pkg, base = m['file'].split('__', 1)
    with zipfile.ZipFile(os.path.join(tmp, m['source'])) as z:
        hits = [n for n in z.namelist() if os.path.basename(n) == base and hashlib.sha256(z.read(n)).hexdigest() == m['sha256']]
        if not hits: print('NOT FOUND / HASH DIFFERS:', m['file']); bad += 1; continue
        open(os.path.join(a.out, m['file']), 'wb').write(z.read(hits[0])); ok += 1
lau = []
import pip._vendor.distlib as dl
for f in sorted(glob.glob(os.path.join(os.path.dirname(dl.__file__), '*.exe'))):
    d = os.path.join(a.out, os.path.basename(f)); shutil.copyfile(f, d)
    lau.append({'file': os.path.basename(f), 'sha256': hashlib.sha256(open(d, 'rb').read()).hexdigest(), 'source': 'pip ' + __import__('pip').__version__ + ' vendored distlib', 'licence': 'MIT'})
json.dump(lau, open(os.path.join(a.out, 'corpus_launchers.json'), 'w'), indent=1); shutil.rmtree(tmp)
print(f'wheel PE files verified: {ok}/{len(man)} | missing or different: {bad} | launchers copied: {len(lau)}')
sys.exit(1 if bad else 0)
