"""Cost of converting one raw-feature JSON record into a 2,568-d vector (thrember process_raw_features), the step needed
if you vectorise EMBER2024 raw JSONL yourself. Records here come from local benign PEs, NOT from EMBER2024 (whose records
may be larger or smaller), so the per-record time is indicative only. usage: python checks\\vectorize_bench.py corpus
"""
import glob, json, os, sys, time, warnings; warnings.filterwarnings('ignore')
from thrember.features import PEFeatureExtractor
fe = PEFeatureExtractor(); files = sorted(f for f in glob.glob(os.path.join(sys.argv[1], '*')) if not f.endswith('.json'))[:20]
recs = [json.dumps(fe.raw_features(open(f, 'rb').read())) for f in files]
print('records:', len(recs), '| JSON KB min/median/max:', [round(sorted(len(r) for r in recs)[i] / 1024, 1) for i in (0, len(recs) // 2, -1)])
t = time.perf_counter(); n = 0
for _ in range(20):
    for r in recs: fe.process_raw_features(json.loads(r)); n += 1
ms = (time.perf_counter() - t) / n * 1000; print(f'{ms:.2f} ms/record (json.loads + process_raw_features, one core)')
