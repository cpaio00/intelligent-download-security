"""UNTESTED: written without access to EMBER2024 (downloads are blocked in the environment where the kit was checked).
Builds row-index files for the thrember-vectorised training file, so that memory and training tests use ONLY labelled rows
of chosen weeks, and writes per-week counts for the data audit.

Row order: thrember writes X_train.dat in the order of sorted(*.jsonl containing 'train') and line order inside each file
(gather_feature_paths + raw_feature_iterator in thrember/model.py, commit 0ef753e). This script reads lines in that same order.
Week: whole days between first_submission_date and 2023-09-24, divided by 7 (official weeks 0-63; project week = official + 1).

usage: python tools\\make_week_index.py --data-dir D:\\sentinelpe\\ember --subset train --weeks 0-39 --out results\\idx_weeks1-40.npy
Check the printed first records: if first_submission_date is not a Unix timestamp or ISO date, stop and fix the parser.
"""
import argparse, collections, datetime as dt, json, os, sys, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('--data-dir', required=True); ap.add_argument('--subset', default='train')
ap.add_argument('--weeks', required=True, help='official week range, e.g. 0-39'); ap.add_argument('--out', required=True); a = ap.parse_args()
lo, hi = map(int, a.weeks.split('-')); origin = dt.datetime(2023, 9, 24, tzinfo=dt.timezone.utc)
def week(v):
    if isinstance(v, (int, float)): t = dt.datetime.fromtimestamp(v, dt.timezone.utc)
    else:
        t = dt.datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
    return (t - origin).days // 7
files = [f for f in sorted(os.listdir(a.data_dir)) if f.endswith('.jsonl') and a.subset in f]
if not files: sys.exit('no matching .jsonl files')
keep = []; counts = collections.Counter(); row = 0
for f in files:
    with open(os.path.join(a.data_dir, f), 'r') as fin:
        for line in fin:
            r = json.loads(line); w = week(r['first_submission_date']); lab = r['label']
            if row < 3: print('record', row, 'file', f, 'first_submission_date =', repr(r['first_submission_date']), '-> week', w, 'label', lab)
            counts[(w, lab)] += 1
            if lo <= w <= hi and lab in (0, 1): keep.append(row)
            row += 1
np.save(a.out, np.array(keep, dtype=np.int64))
print(f'rows read {row} | rows kept {len(keep)} -> {a.out}')
json.dump({f'{w}|{l}': c for (w, l), c in sorted(counts.items(), key=str)}, open(a.out[:-4] + '_week_label_counts.json', 'w'), indent=1)
print('per-week/label counts written; check them against the expected 64 weeks before using the split.')
