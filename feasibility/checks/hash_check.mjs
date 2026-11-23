// Compares WebCrypto SHA-256 (same API as Chrome: crypto.subtle.digest) with Python hashlib values in corpus_manifest.json.
// usage: node checks/hash_check.mjs corpus corpus_tools/wheel_manifest.json
import fs from 'fs'; import path from 'path';
const [dir, man] = process.argv.slice(2); const m = JSON.parse(fs.readFileSync(man));
const entries = Array.isArray(m) ? m : (m.files || Object.values(m));
let ok = 0, bad = 0, missing = 0;
for (const e of entries) {
  const p = path.join(dir, e.file); if (!fs.existsSync(p)) { missing++; continue; }
  const d = Buffer.from(await crypto.subtle.digest('SHA-256', fs.readFileSync(p))).toString('hex');
  d === e.sha256 ? ok++ : bad++;
}
console.log(JSON.stringify({ compared: ok + bad, match: ok, mismatch: bad, missing }));
process.exit(bad || !ok || missing ? 1 : 0);
