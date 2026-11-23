// Copied from feasibility/proto_js (exploratory, AI-assisted). Parity status per group: docs/feasibility-audit.md.
// Only groups that pass the parity test may be used by the local model (enforced in lib/vector.mjs).
// EXPLORATORY PROTOTYPE written during the feasibility study - NOT the SentinelPE implementation and NOT parity-approved.
// Attempts the thrember (EMBER2024) layout for: general(7) histogram(256) byteentropy(256) strings(177) header(74)
//   section(224) datadirectories(dims 0-29 of 34). Parity status of each group: see parity/run_parity.py output.
// NOT implemented: imports, exports, richheader, authenticode, pefilewarnings, datadirectories dims 30-33.
// Policy: STRICT parser. Anything outside the well-formed class returns {status:'reject'} (=> UNSCANNED upstream).
const f32 = Math.fround;
const ID = (x) => x;
const enc = new TextEncoder();

// ---------- numpy-faithful pairwise summation (np.add.reduce: first element + pairwise(rest)) ----------
function pw(a, lo, n, R) {
  if (n < 8) { let res = 0; for (let i = 0; i < n; i++) res = R(res + a[lo + i]); return res; }
  if (n <= 128) {
    const r = [a[lo], a[lo+1], a[lo+2], a[lo+3], a[lo+4], a[lo+5], a[lo+6], a[lo+7]];
    let i;
    for (i = 8; i < n - (n % 8); i += 8) for (let j = 0; j < 8; j++) r[j] = R(r[j] + a[lo + i + j]);
    let res = R(R(R(r[0] + r[1]) + R(r[2] + r[3])) + R(R(r[4] + r[5]) + R(r[6] + r[7])));
    for (; i < n; i++) res = R(res + a[lo + i]);
    return res;
  }
  let n2 = n >> 1; n2 -= n2 % 8;
  return R(pw(a, lo, n2, R) + pw(a, lo + n2, n - n2, R));
}
export function npSum(a, R = ID) { return a.length === 0 ? 0 : R(a[0] + pw(a, 1, a.length - 1, R)); }

// ---------- murmur3 x86_32 (sklearn murmurhash3_bytes_s32) + FeatureHasher ----------
export function murmur3_32(bytes, seed = 0) {
  let h = seed | 0; const len = bytes.length, nb = len >> 2;
  const c1 = 0xcc9e2d51 | 0, c2 = 0x1b873593 | 0;
  for (let i = 0; i < nb; i++) {
    let k = bytes[4*i] | (bytes[4*i+1] << 8) | (bytes[4*i+2] << 16) | (bytes[4*i+3] << 24);
    k = Math.imul(k, c1); k = (k << 15) | (k >>> 17); k = Math.imul(k, c2);
    h ^= k; h = (h << 13) | (h >>> 19); h = (Math.imul(h, 5) + 0xe6546b64) | 0;
  }
  let k = 0; const t = nb * 4;
  switch (len & 3) {
    case 3: k ^= bytes[t+2] << 16;
    case 2: k ^= bytes[t+1] << 8;
    case 1: k ^= bytes[t]; k = Math.imul(k, c1); k = (k << 15) | (k >>> 17); k = Math.imul(k, c2); h ^= k;
  }
  h ^= len; h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b | 0); h ^= h >>> 13;
  h = Math.imul(h, 0xc2b2ae35 | 0); h ^= h >>> 16;
  return h | 0;
}
export function featureHash(pairs, n, alternateSign = true) {
  const out = new Float64Array(n);
  for (const [f, v] of pairs) {
    if (v === 0) continue;
    const h = murmur3_32(enc.encode(f));
    const idx = Math.abs(h) % n;
    out[idx] += alternateSign ? (h >= 0 ? v : -v) : v;
  }
  return out;
}

// ---------- python-compatible helpers ----------
function entropyH(data) { // pefile.entropy_H: Counter order = first appearance, float64
  const len = data.length; if (!len) return 0.0;
  const cnt = new Float64Array(256), order = [];
  for (let i = 0; i < len; i++) { const b = data[i]; if (cnt[b] === 0) order.push(b); cnt[b]++; }
  let e = 0; const ln2 = Math.log(2);
  for (const b of order) { const p = cnt[b] / len; e -= p * (Math.log(p) / ln2); }
  return e;
}
function pyDecodeIgnoreLower(bytes) { // bytes.strip(b"\x00").decode(errors="ignore").lower()
  let s = 0, e = bytes.length;
  while (s < e && bytes[s] === 0) s++;
  while (e > s && bytes[e-1] === 0) e--;
  const b = bytes.subarray(s, e);
  for (let i = 0; i + 2 < b.length; i++) if (b[i] === 0xEF && b[i+1] === 0xBF && b[i+2] === 0xBD) return null; // literal U+FFFD: ambiguous -> reject
  return new TextDecoder('utf-8', { fatal: false }).decode(b).replace(/\uFFFD/g, '').toLowerCase();
}
function adjSecAlign(val, sa, fa) { // pefile cache_adjust_SectionAlignment
  if (sa < 0x1000) sa = fa;
  if (sa && val % sa) return sa * Math.floor(val / sa);
  return val;
}

// ---------- strict PE parse (replicates pefile section semantics) ----------
function rej(reason) { return { ok: false, reason }; }
export function parsePEStrict(u8) {
  const len = u8.length;
  if (len < 0x40) return rej('TOO_SHORT');
  const dv = new DataView(u8.buffer, u8.byteOffset, len);
  if (dv.getUint16(0, true) !== 0x5A4D) return rej('NO_MZ');
  const lfanew = dv.getUint32(0x3C, true);
  if (lfanew < 0x40 || lfanew + 24 > len) return rej('BAD_LFANEW');
  if (dv.getUint32(lfanew, true) !== 0x4550) return rej('NO_PE_SIG');
  const coff = lfanew + 4, opt = coff + 20;
  const machine = dv.getUint16(coff, true), nsec = dv.getUint16(coff + 2, true);
  const ts = dv.getUint32(coff + 4, true), symptr = dv.getUint32(coff + 8, true), nsym = dv.getUint32(coff + 12, true);
  const sizeOpt = dv.getUint16(coff + 16, true), chars = dv.getUint16(coff + 18, true);
  if (opt + 2 > len) return rej('OPT_TRUNC');
  const magic = dv.getUint16(opt, true);
  if (magic !== 0x10b && magic !== 0x20b) return rej('BAD_OPT_MAGIC');
  const p64 = magic === 0x20b, fixed = p64 ? 112 : 96;
  if (opt + fixed > len) return rej('OPT_TRUNC');
  const nrva = dv.getUint32(opt + fixed - 4, true);
  if (nrva > 16) return rej('TOO_MANY_DIRS');
  if (sizeOpt < fixed + nrva * 8 || opt + sizeOpt > len) return rej('OPT_SIZE_INCONSISTENT');
  if (nsec > 96) return rej('TOO_MANY_SECTIONS');
  const tbl = opt + sizeOpt;
  if (tbl + 40 * nsec > len) return rej('SECTION_TABLE_TRUNC');
  const U32 = (o) => dv.getUint32(o, true), U16 = (o) => dv.getUint16(o, true);
  const U64 = (o) => Number(dv.getBigUint64(o, true));
  const o = {
    magic, majLink: u8[opt+2], minLink: u8[opt+3], sizeCode: U32(opt+4), sizeInit: U32(opt+8), sizeUninit: U32(opt+12),
    entry: U32(opt+16), baseCode: U32(opt+20),
    imageBase: p64 ? U64(opt+24) : U32(opt+28),
    secAlign: U32(opt+32), fileAlign: U32(opt+36),
    majOS: U16(opt+40), minOS: U16(opt+42), majImg: U16(opt+44), minImg: U16(opt+46),
    majSub: U16(opt+48), minSub: U16(opt+50), sizeImage: U32(opt+56), sizeHeaders: U32(opt+60),
    checksum: U32(opt+64), subsystem: U16(opt+68), dllChars: U16(opt+70),
    stackRes: p64 ? U64(opt+72) : U32(opt+72), stackCom: p64 ? U64(opt+80) : U32(opt+76),
    heapRes: p64 ? U64(opt+88) : U32(opt+80), heapCom: p64 ? U64(opt+96) : U32(opt+84),
  };
  const dirs = [];
  for (let i = 0; i < nrva; i++) dirs.push({ va: U32(opt + fixed + 8*i), size: U32(opt + fixed + 8*i + 4) });
  // pefile.parse_sections: all-null header => stop; >=3 simultaneous errors in ONE section => abort (this + later sections dropped)
  let secs = [];
  for (let i = 0; i < nsec; i++) {
    const so = tbl + 40 * i;
    let allZero = true; for (let k = 0; k < 40; k++) if (u8[so + k] !== 0) { allZero = false; break; }
    if (allZero) break;
    const s0 = { nameBytes: u8.subarray(so, so + 8), vsize: U32(so+8), va: U32(so+12), rawSize: U32(so+16), ptr: U32(so+20), chars: U32(so+36) };
    let err = 0;
    if (s0.rawSize + s0.ptr > len) err++;
    if (((s0.ptr & ~0x1FF) >>> 0) > len) err++;
    if (s0.vsize > 0x10000000) err++;
    if (adjSecAlign(s0.va, o.secAlign, o.fileAlign) > 0x10000000) err++;
    if (o.fileAlign !== 0 && (s0.ptr % o.fileAlign) !== 0) err++;
    if (err >= 3) break;
    secs.push(s0);
  }
  secs = secs.map((s, idx) => ({ ...s, _i: idx })).sort((a, b) => (a.va - b.va) || (a._i - b._i)); // pefile: stable sort by VirtualAddress
  for (let i = 0; i < secs.length; i++) secs[i].nextVA = i + 1 < secs.length ? secs[i+1].va : null;
  for (const s of secs) {
    let ptrAdj = (s.ptr & ~0x1FF) >>> 0;
    if (o.secAlign < 0x1000 && s.ptr === s.va) ptrAdj = s.va;
    s.ptrAdj = ptrAdj; s.vaAdj = adjSecAlign(s.va, o.secAlign, o.fileAlign);
    let size = (len - ptrAdj < s.rawSize) ? s.vsize : Math.max(s.rawSize, s.vsize);
    if (s.nextVA !== null && s.nextVA > s.va && s.vaAdj + size > s.nextVA) size = s.nextVA - s.vaAdj;
    s.minA = s.vaAdj; s.maxA = s.vaAdj + size;
  }
  // overlapping virtual ranges make pefile's last-used-section cache order-dependent -> reject
  const sorted = secs.filter(s => s.maxA > s.minA).sort((a, b) => a.minA - b.minA);
  for (let i = 1; i < sorted.length; i++) if (sorted[i].minA < sorted[i-1].maxA) return rej('SECTION_VA_OVERLAP');
  return { ok: true, dv, len, opt, fixed, p64, machine, nsec, ts, symptr, nsym, sizeOpt, chars, o, dirs, secs, lfanew, nrva };
}

// ---------- groups ----------
export function groupGeneral(u8) {
  const size = u8.length; const e = entropyH(u8);
  const sb = [u8[0] || 0, size >= 2 ? u8[1] : 0, size >= 3 ? u8[2] : 0, size >= 4 ? u8[3] : 0];
  return Float32Array.from([size, e, 1, ...sb]); // is_pe=1 (strict parse accepted)
}
export function byteHistogram(u8) { const c = new Float64Array(256); for (let i = 0; i < u8.length; i++) c[u8[i]]++; return c; }
export function groupHistogram(counts) {
  const c32 = Array.from(counts, f32); const s = npSum(c32, f32); const out = new Float32Array(256);
  for (let i = 0; i < 256; i++) out[i] = f32(c32[i] / s);
  return out;
}
export function entropyBin(c, mode = 'f32', window = 2048) {
  const R = mode === 'f32' ? f32 : ID;
  const log2 = mode === 'f32' ? (x) => f32(Math.log2(x)) : Math.log2;
  const p = new Array(16).fill(0), nz = [];
  for (let k = 0; k < 16; k++) if (c[k]) { p[k] = R(c[k] / window); nz.push(k); }
  const terms = nz.map((k) => R(R(-p[k]) * log2(p[k])));
  const H = R(npSum(terms, R) * 2);
  let hb = Math.trunc(R(H * 2)); if (hb === 16) hb = 15; return hb;
}
export function byteEntropyCounts(u8, mode = 'f32', window = 2048, step = 1024) {
  const out = new Float64Array(256);
  const addBlock = (lo, hi) => { const c = new Int32Array(16); for (let i = lo; i < hi; i++) c[u8[i] >> 4]++; const hb = entropyBin(c, mode, window); for (let k = 0; k < 16; k++) out[hb*16 + k] += c[k]; };
  if (u8.length < window) addBlock(0, u8.length);
  else for (let st = 0; st + window <= u8.length; st += step) addBlock(st, st + window);
  return out;
}
export function groupByteEntropy(u8, mode = 'f32') {
  const c = Array.from(byteEntropyCounts(u8, mode), f32); const s = npSum(c, f32); const out = new Float32Array(256);
  for (let i = 0; i < 256; i++) out[i] = f32(c[i] / s); return out;
}
export function groupStrings(u8, C) {
  const strs = []; let i = 0; const n = u8.length;
  while (i < n) { if (u8[i] >= 0x20 && u8[i] <= 0x7f) { let j = i; while (j < n && u8[j] >= 0x20 && u8[j] <= 0x7f) j++; if (j - i >= 5) strs.push(u8.subarray(i, j)); i = j; } else i++; }
  const regs = C._regs || (C._regs = C.string_regexes.map((r) => new RegExp(r.pattern, r.ignorecase ? 'i' : '')));
  const counts = new Float64Array(regs.length), dist = new Float64Array(96); let tot = 0, lenSum = 0;
  const dec = new TextDecoder('latin1');
  for (const s of strs) {
    lenSum += s.length; for (let k = 0; k < s.length; k++) dist[s[k] - 0x20]++; tot += s.length;
    const t = dec.decode(s);
    for (let r = 0; r < regs.length; r++) if (regs[r].test(t)) counts[r]++;
  }
  let H = 0, av = 0;
  if (strs.length) { av = lenSum / strs.length; const p = []; for (let k = 0; k < 96; k++) if (dist[k]) p.push(f32(dist[k]) / tot); H = npSum(p.map((x) => -x * Math.log2(x)), ID); }
  const div = tot > 0 ? tot : 1.0;
  const v = [strs.length, av, tot]; for (let k = 0; k < 96; k++) v.push(dist[k] / div); v.push(H); for (const c of counts) v.push(c);
  return Float32Array.from(v);
}
export function groupHeader(pe, C) {
  const o = pe.o, v = [pe.ts, pe.nsec, pe.nsym, pe.sizeOpt, pe.symptr, C.machine[pe.machine] ?? 0, C.subsystem[o.subsystem] ?? 0,
    o.majImg, o.minImg, o.majLink, o.minLink, o.majOS, o.minOS, o.majSub, o.minSub, o.sizeCode, o.sizeHeaders, o.sizeImage, o.sizeInit, o.sizeUninit,
    o.stackRes, o.stackCom, o.heapRes, o.heapCom, o.entry, o.baseCode, o.imageBase, o.secAlign, o.checksum, pe.nrva];
  for (const [, bit] of C.file_flags) v.push((pe.chars & bit) ? 1 : 0);
  for (const [, bit] of C.dll_flags) v.push((o.dllChars & bit) ? 1 : 0);
  const d = pe.dv; for (const off of [0,2,4,6,8,0xA,0xC,0xE,0x10,0x12,0x14,0x16,0x18,0x1A,0x24,0x26]) v.push(d.getUint16(off, true)); v.push(d.getUint32(0x3C, true));
  return Float32Array.from(v);
}
function secData(s, u8) {
  let end = s.ptrAdj + s.rawSize; if (end > s.ptr + s.rawSize) end = s.ptr + s.rawSize;
  const a = Math.min(s.ptrAdj, u8.length), b = Math.max(Math.min(end, u8.length), a); return u8.subarray(a, b);
}
const sectionContains = (s, rva) => s.minA <= rva && rva < s.maxA;
function offsetFromRva(pe, rva, len) { for (const s of pe.secs) if (sectionContains(s, rva)) return (rva - s.vaAdj) + s.ptrAdj; return rva < len ? rva : null; }
export function groupSection(pe, u8, C) {
  const len = u8.length; let entryName = '';
  for (const s of pe.secs) if (sectionContains(s, pe.o.entry)) { const n = pyDecodeIgnoreLower(s.nameBytes); if (n === null) return null; entryName = n; }
  for (let i = 0; entryName === '' && i < pe.secs.length; i++) if ((pe.secs[i].chars & 0x20000000) !== 0) { const n = pyDecodeIgnoreLower(pe.secs[i].nameBytes); if (n === null) return null; entryName = n; }
  const S = [];
  for (const s of pe.secs) {
    const name = pyDecodeIgnoreLower(s.nameBytes); if (name === null) return null;
    const props = C.section_flags.filter(([, bit]) => bit !== 0 && ((s.chars & bit) >>> 0) !== 0).map(([n]) => n);
    S.push({ name, size: s.rawSize, entropy: entropyH(secData(s, u8)), vsize: s.vsize, size_ratio: s.rawSize / len, vsize_ratio: s.rawSize / Math.max(s.vsize, 1), props });
  }
  let lo = 0, ls = 0; const upd = (off, size) => { if (lo + ls < off + size && off + size <= len) { lo = off; ls = size; } };
  upd(pe.opt, pe.sizeOpt); for (const s of pe.secs) upd(s.ptr, s.rawSize);
  pe.dirs.forEach((d, idx) => { if (idx === 4) return; const off = offsetFromRva(pe, d.va, len); if (off === null) return; upd(off, d.size); });
  let ov = { size: 0, size_ratio: 0, entropy: 0 };
  if (len > lo + ls) { const od = u8.subarray(lo + ls); ov = { size: od.length, size_ratio: od.length / len, entropy: entropyH(od) }; }
  const ent = S.map((s) => s.entropy).concat([ov.entropy, 0]), sr = S.map((s) => s.size_ratio).concat([ov.size_ratio, 0]), vr = S.map((s) => s.vsize_ratio).concat([0]);
  const general = [S.length, S.filter((s) => s.size === 0).length, S.filter((s) => s.name === '').length,
    S.filter((s) => s.props.includes('MEM_READ') && s.props.includes('MEM_EXECUTE')).length, S.filter((s) => s.props.includes('MEM_WRITE')).length,
    Math.max(...ent), Math.min(...ent), Math.max(...sr), Math.min(...sr), Math.max(...vr), Math.min(...vr)];
  const sizes = featureHash(S.map((s) => [s.name, s.size]), 50), vsz = featureHash(S.map((s) => [s.name, s.vsize]), 50);
  const ents = featureHash(S.map((s) => [s.name, s.entropy]), 50);
  const chs = featureHash(S.flatMap((s) => s.props.map((p) => [`${s.name}:${p}`, 1])), 50);
  const ent1 = featureHash([[entryName, 1]], 10);
  return Float32Array.from([...general, ...sizes, ...vsz, ...ents, ...chs, ...ent1, ov.size, ov.size_ratio, ov.entropy]);
}
export function groupDataDirs(pe) { // 30 of 34 dims; has_relocs/has_dynamic_relocs DROPPED by the feature gate
  const out = new Float32Array(30);
  for (let i = 1; i < pe.nrva; i++) { const d = pe.dirs[i-1]; out[2*(i-1)] = d.size; out[2*(i-1)+1] = d.va; }
  return out;
}

// ---------- top level ----------
export function extractBrowserFeatures(u8, C, opts = {}) {
  const pe = parsePEStrict(u8);
  if (!pe.ok) return { status: 'reject', reason: pe.reason };
  const sec = groupSection(pe, u8, C);
  if (sec === null) return { status: 'reject', reason: 'AMBIGUOUS_SECTION_NAME' };
  return { status: 'ok', vec: {
    general: groupGeneral(u8), histogram: groupHistogram(byteHistogram(u8)), byteentropy: groupByteEntropy(u8, opts.mode || 'f32'),
    strings: groupStrings(u8, C), header: groupHeader(pe, C), section: sec, datadirectories: groupDataDirs(pe) } };
}
