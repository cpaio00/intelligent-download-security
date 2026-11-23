"""Test 1 - record the environment. Paste the output into your test log.
usage: python env_check.py --data-dir D:\\ember2024 [--need-gb 60]
--data-dir is the folder where the EMBER2024 files will be stored; the free space reported is for THAT drive.
"""
import argparse, os, platform, shutil, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument('--data-dir', required=True); ap.add_argument('--need-gb', type=float, default=60)
a = ap.parse_args()
try: import psutil
except ImportError: sys.exit('psutil missing: python -m pip install psutil')
d = os.path.abspath(a.data_dir)
probe = d
while not os.path.exists(probe):                      # folder may not exist yet: check the drive it will live on
    parent = os.path.dirname(probe)
    if parent == probe: break
    probe = parent
du = shutil.disk_usage(probe); vm = psutil.virtual_memory()
print('OS:', platform.platform(), '| release', platform.release(), '| version', platform.version())
print('Python:', sys.version.split()[0], platform.architecture()[0])
print('CPU:', platform.processor(), '| physical cores', psutil.cpu_count(False), '| logical', psutil.cpu_count())
print(f'RAM total {vm.total/1e9:.2f} GB | available now {vm.available/1e9:.2f} GB | used {vm.percent}%')
sw = psutil.swap_memory(); print(f'Page file / swap total {sw.total/1e9:.2f} GB | used {sw.used/1e9:.2f} GB')
print(f'Data directory: {d} (checked at {probe})')
print(f'  drive total {du.total/1e9:.0f} GB | free {du.free/1e9:.1f} GB | needed {a.need_gb:.0f} GB ->', 'OK' if du.free/1e9 >= a.need_gb else 'NOT ENOUGH SPACE')
for mod in ('numpy', 'lightgbm', 'sklearn', 'shap', 'fastapi', 'uvicorn', 'pefile', 'thrember'):
    try: m = __import__(mod); print(f'  {mod:10s}', getattr(m, '__version__', 'ok'))
    except Exception as e: print(f'  {mod:10s} MISSING: {type(e).__name__}')
try: print('  node      ', subprocess.run(['node', '--version'], capture_output=True, text=True).stdout.strip())
except FileNotFoundError: print('  node       MISSING')
print('Top memory users now (private/USS where available):')
rows = []
for p in psutil.process_iter(['name']):
    try:
        mi = p.memory_info(); rows.append((getattr(mi, 'private', 0) or mi.rss, p.info['name']))
    except (psutil.Error, OSError): pass
for m, n in sorted(rows, reverse=True)[:8]: print(f'  {str(n):30s} {m/1e6:7.0f} MB')
sys.exit(0 if du.free/1e9 >= a.need_gb else 2)
