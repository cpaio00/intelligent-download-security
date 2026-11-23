import { prepare, rawScore } from './lib/lgbm_eval.mjs';
import { assemble, checkModelMeta } from './lib/vector.mjs';
import { localDecision, sigmoid, unscanned, uploadAndAnalyse } from './lib/decision.mjs';

const OPERATING_POINT = '0.01';
const MAX_LOCAL_BYTES = 200 * 1024 * 1024;
const SERVER_TIMEOUT_MS = 120000;
const $ = id => document.getElementById(id);
const store = chrome.storage.local, session = chrome.storage.session;
let model = null, meta = null, modelError = null, settings = { server: 'http://127.0.0.1:8000', token: '', band: 0, timeoutMs: SERVER_TIMEOUT_MS };
const worker = new Worker('worker.js', { type: 'module' });
let jobId = 0; const pending = new Map();
worker.onmessage = e => { const p = pending.get(e.data.id); if (p) { pending.delete(e.data.id); p(e.data); } };
worker.onerror = () => { for (const [, p] of pending) p({ status: 'error', reason: 'worker crashed' }); pending.clear(); };
const extract = buf => new Promise(res => { const id = ++jobId; pending.set(id, res); worker.postMessage({ id, buf }, [buf]); });

async function loadModel() {
  try {
    meta = await (await fetch(chrome.runtime.getURL('model/local_model.meta.json'))).json();
    modelError = checkModelMeta(meta);
    if (!modelError && !meta.thresholds?.[OPERATING_POINT]) modelError = 'MODEL_NO_THRESHOLDS';
    if (!modelError) model = prepare(await (await fetch(chrome.runtime.getURL('model/local_model.json'))).json());
  } catch { modelError = 'NO_MODEL'; }
  const banner = $('model-banner');
  if (modelError) { banner.hidden = false; banner.textContent = 'Local model unavailable: ' + unscanned(modelError).message + '. Every file will be UNSCANNED.'; }
  else if (meta.model_version.startsWith('DEV-SYNTHETIC')) { banner.hidden = false; banner.textContent = 'Development model trained on random numbers (' + meta.model_version + '). Results are meaningless.'; }
  const sel = $('band'); sel.innerHTML = '';
  (meta?.thresholds?.[OPERATING_POINT]?.bands || []).filter(Boolean).forEach((b, i) => {
    const o = document.createElement('option'); o.value = i; o.textContent = `escalate about ${Math.round(b.budget * 100)}% of files`; sel.append(o); });
}

async function loadSettings() {
  settings = { ...settings, ...(await store.get(['server', 'token', 'band', 'timeoutMs'])) };
  $('server').value = settings.server || ''; $('token').value = settings.token || ''; $('band').value = String(settings.band || 0);
  // An analysis that was running when the page closed is reported, never silently dropped or shown as safe.
  const { inProgress } = await session.get('inProgress');
  if (inProgress) { show({ ...unscanned('INTERRUPTED'), name: inProgress.name }); await session.remove('inProgress'); }
}

$('save').onclick = async () => {
  const server = $('server').value.trim();
  if (server.startsWith('https://')) {
    const ok = await chrome.permissions.request({ origins: [new URL(server).origin + '/*'] });
    if (!ok) { $('saved').textContent = 'Permission for that server was not granted.'; return; }
  }
  settings = { ...settings, server, token: $('token').value, band: Number($('band').value || 0) };
  await store.set(settings); $('saved').textContent = 'Saved.';
};

function askConsent(name) {
  $('consent-name').textContent = name; $('consent-server').textContent = settings.server || '(none configured)'; $('consent').hidden = false;
  return new Promise(res => {
    $('send').onclick = () => { $('consent').hidden = true; res(true); };
    $('decline').onclick = () => { $('consent').hidden = true; res(false); };
  });
}

function show(r) {
  const el = $('result'); el.hidden = false; el.innerHTML = '';
  const h = document.createElement('p'); h.className = 'verdict';
  if (r.outcome === 'UNSCANNED') { h.classList.add('unscanned'); h.textContent = 'UNSCANNED'; }
  else if (r.verdict === 'malicious') { h.classList.add('malicious'); h.textContent = 'Likely malicious'; }
  else { h.classList.add('benign'); h.textContent = 'No malicious indicators found (not a guarantee of safety)'; }
  el.append(h);
  const add = (t, cls) => { const p = document.createElement('p'); p.textContent = t; if (cls) p.className = cls; el.append(p); };
  if (r.name) add('File: ' + r.name, 'muted');
  if (r.outcome === 'UNSCANNED') add(r.message + (r.detail ? ' (' + r.detail + ')' : '') + '. Treat this file as unknown.');
  else add((r.outcome === 'LOCAL' ? 'Decided on this device' : 'Decided by the analysis server') + ` · score ${r.score.toFixed(4)} · model ${r.model_version}`, 'muted');
  if (r.sha256) add('SHA-256: ' + r.sha256, 'muted');
  if (r.attributions?.length) {
    add('Features that moved the server model most (they explain the score, not what the program does):', 'muted');
    const t = document.createElement('table'); t.innerHTML = '<tr><th>Feature</th><th>Contribution</th></tr>';
    for (const a of r.attributions) { const tr = t.insertRow(); tr.insertCell().textContent = a.feature; tr.insertCell().textContent = a.contribution.toFixed(4); }
    el.append(t);
  }
}

async function analyse(file) {
  $('result').hidden = true; $('consent').hidden = true; const name = file.name;
  const progress = t => { $('progress').textContent = t; };
  await session.set({ inProgress: { name, started: Date.now() } });
  try {
    if (modelError) return show({ ...unscanned(modelError), name });
    if (file.size === 0) return show({ ...unscanned('EMPTY'), name });
    if (file.size > MAX_LOCAL_BYTES) return show({ ...unscanned('TOO_LARGE'), name });
    progress('Reading and extracting features…');
    const bytes = await file.arrayBuffer();
    const r = await extract(bytes.slice(0));
    if (r.status === 'reject') return show({ ...unscanned('NOT_PE', r.reason), name, sha256: r.sha256 });
    if (r.status !== 'ok') return show({ ...unscanned('EXTRACTION_FAILED', r.reason), name });
    let x; try { x = assemble(r.vec, meta.columns); } catch { return show({ ...unscanned('FEATURE_MISSING'), name, sha256: r.sha256 }); }
    const s = sigmoid(rawScore(model, x));
    const d = localDecision(s, meta.thresholds[OPERATING_POINT], settings.band);
    if (d.kind === 'error') return show({ ...unscanned(d.code), name });
    if (d.kind === 'local') return show({ outcome: 'LOCAL', verdict: d.verdict, score: s, model_version: meta.model_version, name, sha256: r.sha256 });
    progress('');
    if (!settings.server) return show({ ...unscanned('NO_SERVER'), name, sha256: r.sha256 });
    if (!(await askConsent(name))) return show({ ...unscanned('DECLINED'), name, sha256: r.sha256 });
    progress('Waiting for the analysis server…');
    const res = await uploadAndAnalyse(fetch, { serverUrl: settings.server, token: settings.token, timeoutMs: settings.timeoutMs }, bytes, r.sha256);
    show({ ...res, name, sha256: r.sha256 });
  } catch (e) {
    show({ ...unscanned('EXTRACTION_FAILED', String(e).slice(0, 120)), name });
  } finally { progress(''); await session.remove('inProgress'); }
}

$('file').onchange = e => { const f = e.target.files[0]; if (f) analyse(f); e.target.value = ''; };
const drop = $('drop');
drop.ondragover = e => e.preventDefault();
drop.ondrop = e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) analyse(f); };
await loadModel(); await loadSettings();
