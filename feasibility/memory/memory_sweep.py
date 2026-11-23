"""Measures peak private memory, minimum available system memory, Dataset construction time and training time
for increasing row counts, each in a fresh child process. Stops a run (and the sweep) if available system memory
falls below --floor-mb or the child's private memory exceeds --budget-mb, so Windows is not driven into heavy paging.
Synthetic EMBER-shaped data only (make_synth.py). Accuracy is never computed.

usage (Windows):
  python memory\\memory_sweep.py --data D:\\sentinelpe\\synth.npy --rows 50000 100000 150000 200000 --out results\\memory_sweep.csv
Private memory: Windows = psutil private bytes (Task Manager "Commit size"); Linux = RssAnon (excludes memory-mapped file pages);
other = RSS. Sampled every 0.2 s, so very short spikes can be missed.
"""
import argparse, csv, json, os, platform, subprocess, sys, threading, time, psutil
ap = argparse.ArgumentParser()
ap.add_argument('--data', required=True, help='synth .npy, or thrember X_train.dat'); ap.add_argument('--rows', type=int, nargs='+', required=True)
ap.add_argument('--mode', default='sequence', choices=['sequence', 'numpy']); ap.add_argument('--rounds', type=int, default=100)
ap.add_argument('--floor-mb', type=float, default=800); ap.add_argument('--budget-mb', type=float, default=4000)
ap.add_argument('--out', default='memory_sweep.csv'); ap.add_argument('--params', default='{}', help='extra LightGBM params as JSON')
ap.add_argument('--index', help='optional .npy of row numbers to train on (real EMBER2024: labelled training-week rows)')
ap.add_argument('--keep-going', action='store_true', help='continue to larger N after a stopped run')
a = ap.parse_args()
P = {'objective': 'binary', 'num_leaves': 64, 'learning_rate': 0.1, 'min_data_in_leaf': 100, 'num_threads': 2, 'verbose': -1,
     'max_bin': 255, 'bin_construct_sample_cnt': 20000, 'force_col_wise': True, 'seed': 1}
P.update(json.loads(a.params))
def private_mb(p):
    if sys.platform.startswith('linux'):
        for l in open(f'/proc/{p.pid}/status'):
            if l.startswith('RssAnon'): return int(l.split()[1]) / 1024
    mi = p.memory_info(); return (getattr(mi, 'private', 0) or mi.rss) / 1e6
fields = ['os', 'mode', 'rows', 'rounds', 'params', 'status', 'exit_code', 'construct_s', 'train_s', 'peak_private_mb',
          'peak_private_construct_mb', 'min_available_mb', 'available_before_mb', 'total_ram_mb', 'swap_used_delta_mb', 'note']
new = not os.path.exists(a.out); os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
w = csv.DictWriter(open(a.out, 'a', newline=''), fieldnames=fields)
if new: w.writeheader()
here = os.path.dirname(os.path.abspath(__file__))
for N in sorted(a.rows):
    vm0 = psutil.virtual_memory(); sw0 = psutil.swap_memory().used
    child = subprocess.Popen([sys.executable, os.path.join(here, 'train_once.py'), a.data, str(N), a.mode, str(a.rounds), json.dumps(P)] + ([a.index] if a.index else []),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cp = psutil.Process(child.pid); st = {'peak': 0, 'peak_c': 0, 'min_av': vm0.available, 'constructed': False, 'killed': None}
    lines = []
    def reader():
        for l in child.stdout:
            lines.append(l)
            if '"constructed"' in l: st['constructed'] = True
    threading.Thread(target=reader, daemon=True).start()
    while child.poll() is None:
        try: m = private_mb(cp)
        except (psutil.Error, OSError, FileNotFoundError): m = 0
        av = psutil.virtual_memory().available; st['peak'] = max(st['peak'], m); st['min_av'] = min(st['min_av'], av)
        if not st['constructed']: st['peak_c'] = max(st['peak_c'], m)
        if av / 1e6 < a.floor_mb: st['killed'] = f'available memory {av/1e6:.0f} MB < floor {a.floor_mb:.0f} MB'
        elif m > a.budget_mb: st['killed'] = f'private memory {m:.0f} MB > budget {a.budget_mb:.0f} MB'
        if st['killed']: child.kill(); break
        time.sleep(0.2)
    rc = child.wait(); time.sleep(0.3); err = child.stderr.read()[-300:]
    done = next((json.loads(l) for l in lines if '"done"' in l), {})
    cons = next((json.loads(l) for l in lines if '"constructed"' in l), {})
    status = 'stopped_by_monitor' if st['killed'] else ('ok' if rc == 0 and done else 'process_failed')
    row = {'os': platform.platform(), 'mode': a.mode, 'rows': N, 'rounds': a.rounds, 'params': json.dumps(P), 'status': status, 'exit_code': rc,
           'construct_s': done.get('construct_s', cons.get('construct_s')), 'train_s': done.get('train_s'),
           'peak_private_mb': round(st['peak']), 'peak_private_construct_mb': round(st['peak_c']), 'min_available_mb': round(st['min_av'] / 1e6),
           'available_before_mb': round(vm0.available / 1e6), 'total_ram_mb': round(vm0.total / 1e6),
           'swap_used_delta_mb': round((psutil.swap_memory().used - sw0) / 1e6), 'note': st['killed'] or (err.strip().splitlines()[-1] if status != 'ok' and err.strip() else '')}
    w.writerow(row); print({k: row[k] for k in ('rows', 'status', 'construct_s', 'train_s', 'peak_private_mb', 'min_available_mb', 'note')}, flush=True)
    if status != 'ok' and not a.keep_going:
        print('Stopping sweep:', 'the memory limit was reached at this row count.' if st['killed'] else 'the run failed; see the note column.'); break
