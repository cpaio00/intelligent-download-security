// Pure decision logic (unit-tested in tests/js). Any failure produces UNSCANNED; nothing is ever reported "safe".
export const UNSCANNED = {
  NO_MODEL: 'No local model is installed',
  MODEL_SCHEMA_MISMATCH: 'Local model was built for a different feature schema',
  MODEL_METADATA_INVALID: 'Local model metadata is invalid',
  MODEL_USES_UNVERIFIED_FEATURES: 'Local model uses features that have not passed parity testing',
  MODEL_NO_THRESHOLDS: 'Local model has no thresholds for this operating point',
  TOO_LARGE: 'File is larger than the size limit',
  EMPTY: 'File is empty',
  NOT_PE: 'Not a valid Windows PE file',
  EXTRACTION_FAILED: 'Feature extraction failed',
  FEATURE_MISSING: 'A required feature could not be computed',
  DECLINED: 'Local result inconclusive and upload was declined',
  NO_SERVER: 'Local result inconclusive and no server is configured',
  SERVER_UNAVAILABLE: 'Server unreachable',
  SERVER_TIMEOUT: 'Server did not answer in time',
  SERVER_REJECTED: 'Server refused the file',
  SERVER_REPLY_INVALID: 'Server reply was invalid',
  DIGEST_MISMATCH: 'Server analysed different bytes than this file',
  INTERRUPTED: 'Analysis was interrupted before it finished',
};

export function unscanned(code, detail) {
  if (!(code in UNSCANNED)) code = 'EXTRACTION_FAILED';
  return { outcome: 'UNSCANNED', code, message: UNSCANNED[code], detail: detail || null };
}

export const sigmoid = r => 1 / (1 + Math.exp(-r));

// thresholds: model meta thresholds[operatingPoint] = {decision, bands:[{lo,hi,budget}...]}
export function localDecision(s, th, bandIndex) {
  if (!th || typeof th.decision !== 'number') return { kind: 'error', code: 'MODEL_NO_THRESHOLDS' };
  if (!Number.isFinite(s)) return { kind: 'error', code: 'EXTRACTION_FAILED' };
  const bands = (th.bands || []).filter(Boolean);
  if (bands.length === 0) return { kind: 'local', verdict: s >= th.decision ? 'malicious' : 'benign', threshold: th.decision };
  const b = bands[Math.min(Math.max(bandIndex | 0, 0), bands.length - 1)];
  const hi = b.hi === null || b.hi === undefined ? Infinity : b.hi;
  if (s < b.lo) return { kind: 'local', verdict: 'benign', band: b };
  if (s >= hi) return { kind: 'local', verdict: 'malicious', band: b };
  return { kind: 'escalate', band: b };
}

export function validateReply(r, expectedSha256) {
  const ok = r && typeof r === 'object' && r.schema === 'sentinelpe.analysis/1' &&
    (r.verdict === 'malicious' || r.verdict === 'benign') && typeof r.score === 'number' && Number.isFinite(r.score) &&
    typeof r.model_version === 'string' && typeof r.sha256 === 'string' && Array.isArray(r.attributions) &&
    r.attributions.every(a => a && typeof a.feature === 'string' && typeof a.contribution === 'number');
  if (!ok) return unscanned('SERVER_REPLY_INVALID');
  if (r.sha256.toLowerCase() !== expectedSha256.toLowerCase()) return unscanned('DIGEST_MISMATCH');
  return { outcome: 'SERVER', verdict: r.verdict, score: r.score, model_version: r.model_version, attributions: r.attributions, threshold: r.threshold };
}

// Uploads only the bytes and their digest (no filename). Returns a validated SERVER result or UNSCANNED.
export async function uploadAndAnalyse(fetchFn, { serverUrl, token, timeoutMs }, bytes, sha256) {
  if (!serverUrl) return unscanned('NO_SERVER');
  const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetchFn(serverUrl.replace(/\/+$/, '') + '/v1/analyze', { method: 'POST', body: bytes, signal: ctl.signal,
      headers: { 'Content-Type': 'application/octet-stream', 'X-Content-SHA256': sha256, ...(token ? { Authorization: 'Bearer ' + token } : {}) } });
  } catch (e) {
    clearTimeout(timer);
    return unscanned(e && e.name === 'AbortError' ? 'SERVER_TIMEOUT' : 'SERVER_UNAVAILABLE');
  }
  try {
    if (resp.status !== 200) return unscanned(resp.status === 504 ? 'SERVER_TIMEOUT' : 'SERVER_REJECTED', 'HTTP ' + resp.status);
    let body; try { body = await resp.json(); } catch { return unscanned('SERVER_REPLY_INVALID'); }
    return validateReply(body, sha256);
  } catch (e) {
    return unscanned(e && e.name === 'AbortError' ? 'SERVER_TIMEOUT' : 'SERVER_REPLY_INVALID');
  } finally { clearTimeout(timer); }
}
