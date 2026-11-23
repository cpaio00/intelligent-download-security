// Batch CLI: node run_extract.mjs <listfile> <out.jsonl> [mode]
import fs from 'node:fs';
import { extractBrowserFeatures } from './sentinel_features.mjs';
const C = JSON.parse(fs.readFileSync(new URL('./constants.json', import.meta.url)));
const [,, listFile, outFile, mode='f32'] = process.argv;
const files = fs.readFileSync(listFile,'utf8').split(/\r?\n/).filter(Boolean);   // CRLF-safe: Windows text files
const out = fs.createWriteStream(outFile);
for (const f of files) {
  const u8 = new Uint8Array(fs.readFileSync(f)); let rec; const t0 = process.hrtime.bigint();
  try { const r = extractBrowserFeatures(u8, C, {mode});
    rec = r.status==='ok' ? {file:f,status:'ok',vec:Object.fromEntries(Object.entries(r.vec).map(([k,v])=>[k,Array.from(v)]))} : {file:f,status:'reject',reason:r.reason};
  } catch(e) { rec = {file:f,status:'exception',error:String(e).slice(0,200)}; }
  rec.ms = Number(process.hrtime.bigint()-t0)/1e6; out.write(JSON.stringify(rec)+'\n');
}
out.end();
