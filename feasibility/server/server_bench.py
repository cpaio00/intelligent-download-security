"""Starts server_app.py on 127.0.0.1, uploads every file in a folder (benign files only), records status, latency,
SHA-256 agreement and server-process memory, then sends one deliberately wrong digest to check rejection.
usage: python server\\server_bench.py --folder corpus --model full_model.txt [--port 8899] [--out server_bench_rows.json]
Oversized files (> MAX_BYTES, default 50 MB) must come back as 413 or 'reset' (connection closed by the server).
Latency is localhost round trip: upload + thrember extraction + prediction + TreeSHAP. No network delay is included.
"""
import argparse, glob, hashlib, json, os, statistics, subprocess, sys, time, urllib.error, urllib.request, psutil
ap = argparse.ArgumentParser(); ap.add_argument('--folder', required=True); ap.add_argument('--model', default='full_model.txt')
ap.add_argument('--port', default='8899'); ap.add_argument('--out', default='server_bench_rows.json'); a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__)); env = dict(os.environ, MODEL=os.path.abspath(a.model))
srv = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server_app:app', '--app-dir', here, '--host', '127.0.0.1', '--port', a.port, '--log-level', 'warning'], env=env)
proc = psutil.Process(srv.pid); url = f'http://127.0.0.1:{a.port}/analyze'
def mem():
    if sys.platform.startswith('linux'):
        return next(int(l.split()[1]) for l in open(f'/proc/{srv.pid}/status') if l.startswith('RssAnon')) / 1024
    mi = proc.memory_info(); return (getattr(mi, 'private', 0) or mi.rss) / 1e6
for _ in range(240):
    try: urllib.request.urlopen(f'http://127.0.0.1:{a.port}/docs', timeout=1); break
    except Exception:
        if srv.poll() is not None: sys.exit('server failed to start (is thrember installed and the model path correct?)')
        time.sleep(0.5)
else: srv.kill(); sys.exit('server did not start within 120 s')
def post(b, digest):
    req = urllib.request.Request(url, data=b, method='POST', headers={'Content-Type': 'application/octet-stream', 'X-SHA256': digest})
    try:
        r = urllib.request.urlopen(req, timeout=300); return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, None
    except (urllib.error.URLError, ConnectionError) as e:
        # The server rejects oversized uploads from the Content-Length header without reading the body, so the client
        # may see a connection reset instead of the 413 reply. Both mean "rejected"; the extension must show UNSCANNED.
        return 'reset', None
idle = mem(); peak = idle; rows = []
try:
    for f in sorted(glob.glob(os.path.join(a.folder, '*'))):
        if not os.path.isfile(f) or f.endswith('.json'): continue
        b = open(f, 'rb').read(); h = hashlib.sha256(b).hexdigest(); t = time.perf_counter(); code, body = post(b, h)
        ms = (time.perf_counter() - t) * 1000; peak = max(peak, mem())
        rows.append({'file': os.path.basename(f), 'MB': round(len(b) / 1e6, 2), 'status': code, 'ms': round(ms), 'hash_matches': (body['sha256'] == h) if body else None})
    probe = next((r['file'] for r in rows if r['status'] == 200), None)
    mismatch = post(open(os.path.join(a.folder, probe), 'rb').read(), '0' * 64)[0] if probe else None
finally: srv.terminate()
ok = [r for r in rows if r['status'] == 200]
print(json.dumps({'files': len(rows), 'status_counts': {str(s): sum(r['status'] == s for r in rows) for s in sorted({r['status'] for r in rows}, key=str)},
  'hash_mismatches_in_replies': sum(r['hash_matches'] is False for r in rows), 'wrong_digest_request_status': mismatch,
  'median_ms_200': statistics.median(r['ms'] for r in ok) if ok else None, 'max_ms_200': max((r['ms'] for r in ok), default=None),
  'server_idle_private_MB': round(idle), 'server_peak_private_MB': round(peak)}, indent=1))
json.dump(rows, open(a.out, 'w'), indent=1)
sys.exit(0 if ok and mismatch == 409 and not any(r['hash_matches'] is False for r in rows) else 1)
