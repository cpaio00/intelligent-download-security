// Sends each selected file to a Web Worker; measures read, extraction and SHA-256 time and main-thread stalls.
const out = document.getElementById('out'); const log = s => { out.textContent += s + '\n'; };
const worker = new Worker('worker.js', { type: 'module' });
let ticks = 0, last = performance.now(), worstGap = 0;
setInterval(() => { const n = performance.now(); worstGap = Math.max(worstGap, n - last); last = n; document.getElementById('tick').textContent = ++ticks; }, 50);
const pending = [];
worker.onmessage = e => { const r = e.data; r.worstMainThreadGapMs = Math.round(worstGap); log(JSON.stringify(r)); (pending.shift() || (() => {}))(); };
document.getElementById('f').onchange = async ev => {
  for (const file of ev.target.files) {
    worstGap = 0; const t0 = performance.now(); const buf = await file.arrayBuffer(); const readMs = Math.round(performance.now() - t0);
    await new Promise(res => { pending.push(res); worker.postMessage({ name: file.name, size: file.size, readMs, buf }, [buf]); });
  }
  log('done');
};
