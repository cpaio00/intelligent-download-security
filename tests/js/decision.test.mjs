import test from 'node:test'; import assert from 'node:assert/strict';
import { localDecision, validateReply, uploadAndAnalyse, unscanned, UNSCANNED } from '../../extension/lib/decision.mjs';

const sha = 'a'.repeat(64);
const good = { schema: 'sentinelpe.analysis/1', verdict: 'benign', score: 0.2, model_version: 'm', sha256: sha, threshold: 0.9,
  attributions: [{ feature: 'general[0]', contribution: 0.1 }] };
const resp = (status, body, bad) => ({ status, json: async () => { if (bad) throw new SyntaxError('x'); return body; } });

test('every UNSCANNED code is reported as UNSCANNED, never benign', () => {
  for (const c of Object.keys(UNSCANNED)) assert.equal(unscanned(c).outcome, 'UNSCANNED');
  assert.equal(unscanned('NOT_A_CODE').outcome, 'UNSCANNED');
});

test('local decision uses the band: below lo benign, at/above hi malicious, inside escalates', () => {
  const th = { decision: 0.9, bands: [{ lo: 0.3, hi: 0.8, budget: 0.1 }] };
  assert.equal(localDecision(0.29, th, 0).verdict, 'benign');
  assert.equal(localDecision(0.8, th, 0).verdict, 'malicious');
  assert.equal(localDecision(0.3, th, 0).kind, 'escalate');
  assert.equal(localDecision(0.5, { decision: 0.4 }, 0).verdict, 'malicious');      // no bands: decision threshold
  assert.equal(localDecision(0.5, undefined, 0).code, 'MODEL_NO_THRESHOLDS');
  assert.equal(localDecision(NaN, th, 0).kind, 'error');
  assert.equal(localDecision(0.99, { decision: 0.9, bands: [{ lo: 0.1, hi: null, budget: 1 }] }, 0).kind, 'escalate'); // hi = +inf
});

test('reply validation', () => {
  assert.equal(validateReply(good, sha).outcome, 'SERVER');
  assert.equal(validateReply({ ...good, sha256: 'b'.repeat(64) }, sha).code, 'DIGEST_MISMATCH');
  for (const bad of [null, {}, { ...good, schema: 'x' }, { ...good, verdict: 'safe' }, { ...good, score: 'x' }, { ...good, attributions: [{}] }])
    assert.equal(validateReply(bad, sha).code, 'SERVER_REPLY_INVALID');
});

test('upload failure states all end in UNSCANNED', async () => {
  const cfg = { serverUrl: 'http://s', token: 't', timeoutMs: 50 };
  assert.equal((await uploadAndAnalyse(async () => { throw new TypeError('net'); }, cfg, new ArrayBuffer(1), sha)).code, 'SERVER_UNAVAILABLE');
  const hang = (u, o) => new Promise((_, rej) => o.signal.addEventListener('abort', () => rej(Object.assign(new Error('a'), { name: 'AbortError' }))));
  assert.equal((await uploadAndAnalyse(hang, cfg, new ArrayBuffer(1), sha)).code, 'SERVER_TIMEOUT');
  assert.equal((await uploadAndAnalyse(async () => resp(500), cfg, new ArrayBuffer(1), sha)).code, 'SERVER_REJECTED');
  assert.equal((await uploadAndAnalyse(async () => resp(504), cfg, new ArrayBuffer(1), sha)).code, 'SERVER_TIMEOUT');
  assert.equal((await uploadAndAnalyse(async () => resp(200, null, true), cfg, new ArrayBuffer(1), sha)).code, 'SERVER_REPLY_INVALID');
  assert.equal((await uploadAndAnalyse(async () => resp(200, { ...good, sha256: 'c'.repeat(64) }), cfg, new ArrayBuffer(1), sha)).code, 'DIGEST_MISMATCH');
  assert.equal((await uploadAndAnalyse(async () => resp(200, good), { ...cfg, serverUrl: '' }, new ArrayBuffer(1), sha)).code, 'NO_SERVER');
  let seen; const ok = await uploadAndAnalyse(async (u, o) => { seen = { u, o }; return resp(200, good); }, cfg, new ArrayBuffer(1), sha);
  assert.equal(ok.outcome, 'SERVER');
  assert.equal(seen.u, 'http://s/v1/analyze'); assert.equal(seen.o.headers['X-Content-SHA256'], sha);
  assert.ok(!JSON.stringify(seen.o.headers).toLowerCase().includes('filename'));
});
