"""Times the exploratory JS extractor (Node) and the reference thrember extractor on each file in a folder.
Benign files only. usage: python checks\\extract_speed.py large
Memory: peak resident memory of each child process (psutil, sampled every 50 ms).
"""
import glob, json, os, subprocess, sys, tempfile, time, psutil
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True); pp = psutil.Process(p.pid); peak = 0; t = time.perf_counter()
    while p.poll() is None:
        try: peak = max(peak, pp.memory_info().rss)
        except psutil.Error: pass
        time.sleep(0.05)
    o, e = p.communicate(); return (time.perf_counter() - t) * 1000, peak / 1e6, o, e
REF = 'import sys,warnings,time;warnings.filterwarnings("ignore");from thrember.features import PEFeatureExtractor as F;fe=F();b=open(sys.argv[1],"rb").read();t=time.perf_counter();fe.feature_vector(b);print((time.perf_counter()-t)*1000)'
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*'))):
    lst = tempfile.NamedTemporaryFile('w', delete=False); lst.write(f); lst.close()
    _, jpk, _, _ = run(['node', os.path.join(here, 'proto_js', 'run_extract.mjs'), lst.name, lst.name + '.jsonl'])
    rec = json.loads(open(lst.name + '.jsonl').readline()); os.remove(lst.name); os.remove(lst.name + '.jsonl')
    _, rpk, o, e = run([sys.executable, '-c', REF, f])
    print(json.dumps({'file': os.path.basename(f), 'MB': round(os.path.getsize(f) / 1e6, 1), 'js_status': rec['status'], 'js_extract_ms': round(rec['ms']),
                      'js_peak_rss_MB': round(jpk), 'thrember_extract_ms': round(float(o.strip())) if o.strip() else 'error: ' + e[-120:], 'thrember_peak_rss_MB': round(rpk)}))
