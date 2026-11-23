// End-to-end test of the unpacked MV3 extension in Chromium (Playwright) against the real FastAPI server and
// deliberately faulty servers. Uses SYNTHETIC dev models and a benign pip launcher; nothing is executed.
// usage: node tests/e2e/extension_e2e.js            (needs: python deps, thrember, playwright with Chromium)
// The test copies the extension to a temp folder, installs a model and adds host permissions for the fake servers.
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'); const os = require('os'); const path = require('path'); const http = require('http'); const crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..'); const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'spe-e2e-'));
const py = process.env.PYTHON || 'python3';
let failures = 0; const results = [];
const check = (name, cond, detail) => { results.push(`${cond ? 'PASS' : 'FAIL'}  ${name}${cond ? '' : '  -> ' + detail}`); if (!cond) failures++; };

function prepareExtension(name, mutateMeta) {
  const dir = path.join(TMP, name); fs.cpSync(path.join(ROOT, 'extension'), dir, { recursive: true });
  const m = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')));
  m.host_permissions.push('http://127.0.0.1:8001/*', 'http://127.0.0.1:8002/*', 'http://127.0.0.1:8003/*', 'http://127.0.0.1:8009/*');
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify(m));
  if (mutateMeta) {
    for (const f of ['local_model.json', 'local_model.meta.json']) fs.copyFileSync(path.join(TMP, 'dev', 'browser', f), path.join(dir, 'model', f));
    const p = path.join(dir, 'model', 'local_model.meta.json'); const meta = JSON.parse(fs.readFileSync(p)); mutateMeta(meta); fs.writeFileSync(p, JSON.stringify(meta));
  }
  return dir;
}

async function withExtension(dir, fn) {
  const ctx = await chromium.launchPersistentContext(path.join(TMP, 'profile-' + path.basename(dir)), {
    headless: false, args: ['--headless=new', `--disable-extensions-except=${dir}`, `--load-extension=${dir}`] });   // the headless shell cannot load extensions
  try {
    let [sw] = ctx.serviceWorkers(); if (!sw) sw = await ctx.waitForEvent('serviceworker', { timeout: 15000 });
    const id = new URL(sw.url()).host; const requests = [];
    ctx.on('request', r => { if (r.url().includes('/v1/analyze')) requests.push({ url: r.url(), headers: r.headers(), body: r.postDataBuffer() }); });
    const page = await ctx.newPage(); const url = `chrome-extension://${id}/app.html`;
    await page.goto(url);
    const run = async (settings, file, consent) => {
      requests.length = 0;
      await page.evaluate(s => chrome.storage.local.set(s), settings); await page.goto(url); await page.waitForTimeout(300);
      await page.setInputFiles('#file', file);
      if (consent !== undefined) { await page.waitForSelector('#consent:not([hidden])', { timeout: 30000 }); await page.click(consent ? '#send' : '#decline'); }
      await page.waitForSelector('#result:not([hidden])', { timeout: 60000 });
      return { text: await page.textContent('#result'), requests: [...requests] };
    };
    await fn({ page, run, url, ctx });
  } finally { await ctx.close(); }
}

function fakeServer(port, handler) { return new Promise(r => { const s = http.createServer(handler).listen(port, '127.0.0.1', () => r(s)); }); }

(async () => {
  execFileSync(py, ['-m', 'sentinelpe_ml', 'make-dev-models', '--out', path.join(TMP, 'dev'), '--rows', '4000'], { cwd: path.join(ROOT, 'ml'), stdio: 'ignore' });
  const pe = path.join(TMP, 't64.exe');
  fs.copyFileSync(execFileSync(py, ['-c', 'import pip._vendor.distlib as d,os;print(os.path.join(os.path.dirname(d.__file__),"t64.exe"))']).toString().trim(), pe);
  const notpe = path.join(TMP, 'notes.exe'); fs.writeFileSync(notpe, crypto.randomBytes(5000));
  const sha = crypto.createHash('sha256').update(fs.readFileSync(pe)).digest('hex'); const size = fs.statSync(pe).size;

  const srv = spawn(py, ['-m', 'uvicorn', 'app.asgi:app', '--app-dir', path.join(ROOT, 'backend'), '--host', '127.0.0.1', '--port', '8000', '--log-level', 'warning'],
    { env: { ...process.env, SENTINELPE_MODEL: path.join(TMP, 'dev', 'server_model'), SENTINELPE_API_TOKEN: 'e2e-token' }, stdio: 'ignore' });
  for (let i = 0; i < 120; i++) { try { await new Promise((ok, no) => http.get('http://127.0.0.1:8000/v1/health', r => r.statusCode === 200 ? ok() : no()).on('error', no)); break; } catch { await new Promise(r => setTimeout(r, 500)); } }
  const reply = { schema: 'sentinelpe.analysis/1', verdict: 'benign', score: 0.1, model_version: 'fake', threshold: 0.9, attributions: [] };
  const fakes = [await fakeServer(8001, (q, s) => { q.resume(); q.on('end', () => { s.writeHead(200, { 'Content-Type': 'application/json' }); s.end(JSON.stringify({ ...reply, sha256: '0'.repeat(64) })); }); }),
                 await fakeServer(8002, (q, s) => { q.resume(); q.on('end', () => { s.writeHead(200, { 'Content-Type': 'application/json' }); s.end('{not json'); }); }),
                 await fakeServer(8003, (q, s) => { q.resume(); /* never answers */ })];
  const S = { server: 'http://127.0.0.1:8000', token: 'e2e-token', band: 0, timeoutMs: 120000 };
  try {
    await withExtension(prepareExtension('ext-local', m => { m.thresholds['0.01'].bands = [{ budget: 0, lo: 2, hi: 3 }]; }), async ({ run }) => {
      const r = await run(S, pe);
      check('valid PE decided locally', /Decided on this device/.test(r.text) && /DEV-SYNTHETIC/.test(r.text), r.text);
      check('local decision sends nothing to the server', r.requests.length === 0, r.requests.length + ' requests');
      const n = await run(S, notpe);
      check('non-PE file is UNSCANNED', /UNSCANNED/.test(n.text) && /Not a valid Windows PE/.test(n.text), n.text);
    });
    await withExtension(prepareExtension('ext-escalate', m => { m.thresholds['0.01'].bands = [{ budget: 1, lo: -1, hi: null }]; }), async ({ run, page, url }) => {
      const d = await run(S, pe, false);
      check('declined upload is UNSCANNED', /UNSCANNED/.test(d.text) && /declined/.test(d.text), d.text);
      check('declining sends no file content', d.requests.length === 0, d.requests.length + ' requests');
      const c = await run(S, pe, true);
      check('consented upload is decided by the real server', /Decided by the analysis server/.test(c.text) && /DEV-SYNTHETIC-server/.test(c.text), c.text);
      const rq = c.requests[0] || { headers: {}, body: Buffer.alloc(0) };
      check('exactly one upload with digest header and the exact bytes', c.requests.length === 1 && rq.headers['x-content-sha256'] === sha && rq.body && rq.body.length === size, JSON.stringify(rq.headers));
      check('file name is not sent', !JSON.stringify(rq.headers).includes('t64') && !rq.url.includes('t64'), JSON.stringify(rq.headers));
      const t = await run({ ...S, token: 'wrong' }, pe, true);
      check('rejected request (401) is UNSCANNED', /UNSCANNED/.test(t.text) && /refused/.test(t.text), t.text);
      const u = await run({ ...S, server: 'http://127.0.0.1:8009' }, pe, true);
      check('server unavailable is UNSCANNED', /UNSCANNED/.test(u.text) && /unreachable/.test(u.text), u.text);
      const m = await run({ ...S, server: 'http://127.0.0.1:8001' }, pe, true);
      check('digest mismatch is UNSCANNED', /UNSCANNED/.test(m.text) && /different bytes/.test(m.text), m.text);
      const j = await run({ ...S, server: 'http://127.0.0.1:8002' }, pe, true);
      check('malformed reply is UNSCANNED', /UNSCANNED/.test(j.text) && /reply was invalid/.test(j.text), j.text);
      const h = await run({ ...S, server: 'http://127.0.0.1:8003', timeoutMs: 1500 }, pe, true);
      check('server timeout is UNSCANNED', /UNSCANNED/.test(h.text) && /did not answer in time/.test(h.text), h.text);
      const ns = await run({ ...S, server: '' }, pe);
      check('no server configured is UNSCANNED', /UNSCANNED/.test(ns.text) && /no server/.test(ns.text), ns.text);
      await page.evaluate(() => chrome.storage.session.set({ inProgress: { name: 'x.exe', started: 1 } })); await page.goto(url);
      await page.waitForSelector('#result:not([hidden])'); const it = await page.textContent('#result');
      check('interrupted analysis is reported as UNSCANNED', /UNSCANNED/.test(it) && /interrupted/.test(it), it);
    });
    await withExtension(prepareExtension('ext-nomodel', null), async ({ run, page }) => {
      const r = await run(S, pe);
      check('missing local model is UNSCANNED', /UNSCANNED/.test(r.text) && /No local model/.test(r.text), r.text);
      check('missing model banner shown', /Local model unavailable/.test(await page.textContent('#model-banner')), 'no banner');
    });
    await withExtension(prepareExtension('ext-unverified', m => { m.columns = [...m.columns.slice(0, -1), 263]; }), async ({ run }) => {
      const r = await run(S, pe);
      check('model using non-parity features is refused (UNSCANNED)', /UNSCANNED/.test(r.text) && /not passed parity/.test(r.text), r.text);
    });
  } finally { srv.kill(); fakes.forEach(f => f.close()); }
  console.log(results.join('\n')); console.log(failures ? `${failures} FAILED` : `ALL ${results.length} CHECKS PASSED`);
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
