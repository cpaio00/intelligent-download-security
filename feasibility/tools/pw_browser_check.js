// OPTIONAL automation used for the cloud verification (Playwright + Chromium). Not needed on the laptop: use Chrome manually.
// usage: node tools/pw_browser_check.js <kitRoot> <file1> [file2 ...]   (requires: npm i playwright; npx playwright install chromium)
const { chromium } = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path');
const root = path.resolve(process.argv[2]); const files = process.argv.slice(3);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json' };
const srv = http.createServer((q, s) => { const p = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { s.writeHead(404); return s.end(); }
  s.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(s); }).listen(8766);
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage(); console.log('browser', b.version());
  await pg.goto('http://localhost:8766/equivalence/run_browser.html');
  await pg.waitForFunction(() => /PASS|FAIL/.test(document.getElementById('out').textContent), null, { timeout: 600000 });
  console.log(await pg.textContent('#out'));
  if (files.length) { await pg.goto('http://localhost:8766/browser_test/index.html'); await pg.setInputFiles('#f', files);
    await pg.waitForFunction(() => document.getElementById('out').textContent.includes('done'), null, { timeout: 600000 }); console.log(await pg.textContent('#out')); }
  await b.close(); srv.close();
})();
