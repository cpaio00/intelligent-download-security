// Loads a dump_model() JSON, compares JavaScript raw scores with Python on the held-out vectors, times load and inference.
// Runs in Node (not Chrome; use browser_test for Chrome). Uses the same evaluator as the equivalence suite.
// usage: node compact/js_infer_bench.mjs compact_models/m100x31
import fs from 'node:fs'; import { prepare, rawScore } from '../equivalence/lgbm_eval.mjs';
const name = process.argv[2]; if (!name) { console.error('usage: node compact/js_infer_bench.mjs <model path without .json>'); process.exit(2); }
let t0 = performance.now(); const m = prepare(JSON.parse(fs.readFileSync(name + '.json', 'utf8'))); const loadMs = performance.now() - t0;
const t = JSON.parse(fs.readFileSync(name + '_test.json', 'utf8')); const n = t.X.length;
let exact = 0, maxd = 0; t0 = performance.now();
t.X.forEach((x, i) => { const s = rawScore(m, x); const d = Math.abs(s - t.raw[i]); if (d === 0) exact++; maxd = Math.max(maxd, d); });
const per = n ? (performance.now() - t0) / n : NaN; const pass = n > 0 && exact === n;
console.log(JSON.stringify({ model: name, vectors: n, exact, maxAbsRawDiff: maxd, loadMs: +loadMs.toFixed(1), perVectorMs: +per.toFixed(4), heapMB: Math.round(process.memoryUsage().heapUsed / 1e6), pass }));
process.exitCode = pass ? 0 : 1;
