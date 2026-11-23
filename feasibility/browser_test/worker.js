// Web Worker: SHA-256 (WebCrypto) + exploratory prototype feature extraction. Any rejection or error => UNSCANNED.
import { extractBrowserFeatures } from '../proto_js/sentinel_features.mjs';
const C = await (await fetch('../proto_js/constants.json')).json();
const MAX_BYTES = 200 * 1024 * 1024;
onmessage = async e => {
  const { name, size, readMs, buf } = e.data; const r = { file: name, MB: +(size / 1e6).toFixed(2), readMs };
  if (size > MAX_BYTES) { postMessage({ ...r, status: 'UNSCANNED', reason: 'over size limit' }); return; }
  let t = performance.now(); r.sha256 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buf)), b => b.toString(16).padStart(2, '0')).join('');
  r.hashMs = Math.round(performance.now() - t); t = performance.now();
  try { const x = extractBrowserFeatures(new Uint8Array(buf), C, { mode: 'f32' }); r.status = x.status === 'ok' ? 'EXTRACTED' : 'UNSCANNED'; r.reason = x.reason || null; }
  catch (err) { r.status = 'UNSCANNED'; r.reason = 'exception: ' + String(err).slice(0, 120); }
  r.extractMs = Math.round(performance.now() - t); postMessage(r);
};
