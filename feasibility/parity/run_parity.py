"""Feature parity: exploratory JS prototype (proto_js) vs the reference thrember extractor, per EMBER2024 feature group.
Benign files only; nothing is executed. usage: python parity\\run_parity.py --files corpus variants --out parity_results.json
Pre-declared rule (docs/testing-plan.md): values compared as float32; a group PASSES if every compared value is identical;
it is CONDITIONAL if the only differences are 1 ULP (then local-model predictions on the corpus must be shown unchanged);
otherwise it FAILS. Groups the prototype does not compute are reported NOT IMPLEMENTED.
"""
import argparse, glob, json, os, subprocess, sys, tempfile, time, warnings, numpy as np
warnings.filterwarnings('ignore')
from thrember.features import PEFeatureExtractor
ap = argparse.ArgumentParser(); ap.add_argument('--files', nargs='+', required=True); ap.add_argument('--out', default='parity_results.json'); a = ap.parse_args()
JS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'proto_js', 'run_extract.mjs')
FE = PEFeatureExtractor(); OFF = {}; o = 0
for f in FE.features: OFF[f.name] = (o, o + f.dim); o += f.dim
JS_GROUPS = {'general': 7, 'histogram': 256, 'byteentropy': 256, 'strings': 177, 'header': 74, 'section': 224, 'datadirectories': 30}
files = sorted(p for d in a.files for p in glob.glob(os.path.join(d, '*')) if os.path.isfile(p) and not p.endswith('.json'))
lst = tempfile.NamedTemporaryFile('w', delete=False, suffix='.list'); lst.write('\n'.join(files)); lst.close(); jl = lst.name + '.jsonl'
t = time.perf_counter(); subprocess.run(['node', JS, lst.name, jl, 'f32'], check=True); js_s = time.perf_counter() - t
def ulp(a, b):
    a = a.view(np.int32).astype(np.int64); b = b.view(np.int32).astype(np.int64)
    a = np.where(a < 0, -(a & 0x7fffffff), a); b = np.where(b < 0, -(b & 0x7fffffff), b); return np.abs(a - b)
tot = {g: {'values': 0, 'exact': 0, 'ulp1': 0, 'ulp_gt1': 0, 'max_ulp': 0, 'files_with_diff': []} for g in JS_GROUPS}
rows = []; ref_s = 0
for rec in map(json.loads, open(jl)):
    r = {'file': os.path.basename(rec['file']), 'js_status': rec['status'], 'js_reason': rec.get('reason') or rec.get('error'), 'js_ms': round(rec['ms'], 1)}
    t = time.perf_counter()
    try: ref = FE.feature_vector(open(rec['file'], 'rb').read()); r['ref_status'] = 'ok' if ref[2] == 1 else 'not_pe'
    except Exception as e: ref = None; r['ref_status'] = f'exception:{type(e).__name__}'
    ref_s += time.perf_counter() - t
    if rec['status'] == 'ok' and ref is not None and r['ref_status'] == 'ok':
        for g, n in JS_GROUPS.items():
            s, _ = OFF[g]; rv = ref[s:s + n].astype(np.float32); jv = np.array(rec['vec'][g], dtype=np.float64).astype(np.float32)
            if rv.shape != jv.shape: sys.exit(f'shape mismatch in {g} for {r["file"]}')
            u = ulp(rv, jv); T = tot[g]; T['values'] += n; T['exact'] += int((u == 0).sum()); T['ulp1'] += int((u == 1).sum())
            T['ulp_gt1'] += int((u > 1).sum()); T['max_ulp'] = max(T['max_ulp'], int(u.max()))
            if u.max() > 0: T['files_with_diff'].append(r['file'])
    rows.append(r)
os.remove(lst.name); os.remove(jl)
for g, T in tot.items(): T['verdict'] = 'PASS' if T['values'] and T['exact'] == T['values'] else ('CONDITIONAL' if T['ulp_gt1'] == 0 and T['values'] else 'FAIL')
summary = {'files': len(rows), 'js_accepted': sum(r['js_status'] == 'ok' for r in rows),
           'js_rejected': {r['file']: r['js_reason'] for r in rows if r['js_status'] != 'ok'},
           'ref_not_ok': {r['file']: r['ref_status'] for r in rows if r['ref_status'] != 'ok'},
           'compared_files': sum(r['js_status'] == 'ok' and r['ref_status'] == 'ok' for r in rows),
           'js_rejects_ref_accepts': [r['file'] for r in rows if r['js_status'] != 'ok' and r['ref_status'] == 'ok'],
           'groups': tot, 'not_implemented': ['imports', 'exports', 'datadirectories dims 30-33', 'richheader', 'authenticode', 'pefilewarnings'],
           'js_total_s': round(js_s, 1), 'ref_total_s': round(ref_s, 1)}
json.dump({'summary': summary, 'files': rows}, open(a.out, 'w'), indent=1)
for g, T in tot.items(): print(f"{g:16s} values {T['values']:7d} exact {T['exact']:7d} 1ulp {T['ulp1']:4d} >1ulp {T['ulp_gt1']:4d} max {T['max_ulp']} -> {T['verdict']} {T['files_with_diff'][:2]}")
print(json.dumps({k: v for k, v in summary.items() if k != 'groups'}, indent=1))
