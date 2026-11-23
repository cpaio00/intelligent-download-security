// Module worker: SHA-256 (WebCrypto) and static feature extraction. Never executes the file.
import { extractBrowserFeatures } from './lib/features/sentinel_features.mjs';
const C = fetch(new URL('./lib/features/constants.json', import.meta.url)).then(r => r.json());
onmessage = async e => {
  const { id, buf } = e.data;
  try {
    const sha256 = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buf)), b => b.toString(16).padStart(2, '0')).join('');
    const t = performance.now(); const r = extractBrowserFeatures(new Uint8Array(buf), await C, { mode: 'f32' });
    const ms = performance.now() - t;
    if (r.status !== 'ok') { postMessage({ id, sha256, status: 'reject', reason: r.reason, ms }); return; }
    const vec = Object.fromEntries(Object.entries(r.vec).map(([k, v]) => [k, Array.from(v)]));
    postMessage({ id, sha256, status: 'ok', vec, ms });
  } catch (err) { postMessage({ id, status: 'error', reason: String(err).slice(0, 200) }); }
};
