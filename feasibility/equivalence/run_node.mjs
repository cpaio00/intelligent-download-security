// node run_node.mjs  -> compares JavaScript raw scores with Python for every case and reports branch coverage.
import fs from 'node:fs'; import { prepare, rawScore } from './lgbm_eval.mjs';
const cases = Object.keys(JSON.parse(fs.readFileSync('cases_summary.json'))); let allPass = cases.length === 6;
for (const c of cases) {
  const m = prepare(JSON.parse(fs.readFileSync(c + '.json'))); const t = JSON.parse(fs.readFileSync(c + '_test.json')); t.X = t.X.map(r => r.map(v => typeof v === 'string' ? Number(v) : v));
  const cov = {}; const tr = (n, v, l) => { const why = v === null ? 'NaN' : (!Number.isFinite(v) ? 'infinite' : (n.decision_type === '==' ? 'category' : (v === 0 ? 'zero' : 'value')));
    const k = `${n.decision_type} missing=${n.missing_type} default_left=${n.default_left} input=${why} -> ${l ? 'left' : 'right'}`; cov[k] = (cov[k] || 0) + 1; };
  let exact = 0, maxd = 0, exactFile = 0;
  t.X.forEach((x, i) => { const s = rawScore(m, x, tr); const d = Math.abs(s - t.raw[i]); if (d === 0) exact++; if (s === t.raw_file[i]) exactFile++; maxd = Math.max(maxd, d); });
  const pass = t.X.length > 0 && exact === t.X.length && exactFile === t.X.length;   // an empty test set is a failure, not a pass allPass &&= pass;
  console.log(JSON.stringify({ case: c, vectors: t.X.length, exactVsInMemoryModel: exact, exactVsReloadedModel: exactFile, maxAbsRawDiff: maxd, pass }));
  fs.writeFileSync(c + '_coverage.json', JSON.stringify(cov, null, 1));
}
console.log(allPass ? 'ALL CASES PASS (bit-identical raw scores)' : 'FAILURES PRESENT'); process.exitCode = allPass ? 0 : 1;
