// Assembles the local model's input vector from extractor groups, using EMBER2024 (thrember 0ef753e) column indices.
// A model that asks for a column the extractor does not provide, or for a group not listed as parity-passed, is refused.
export const SCHEMA_VERSION = 'ember2024-thrember-0ef753e/2568';
export const GROUPS = { general: [0, 7], histogram: [7, 256], byteentropy: [263, 256], strings: [519, 177], header: [696, 74],
  section: [770, 224], imports: [994, 1282], exports: [2276, 129], datadirectories: [2405, 34], richheader: [2439, 33],
  authenticode: [2472, 8], pefilewarnings: [2480, 88] };
// Columns this extension may feed to the local model: parity-passed groups only (feasibility audit, Nov 2026).
// Update ONLY from the project's real parity results.
export const PARITY_PASSED = { general: null, histogram: null, strings: null, header: null, section: null, datadirectories: 30 };

export function allowedColumns() {
  const s = new Set();
  for (const [g, dims] of Object.entries(PARITY_PASSED)) {
    const [off, n] = GROUPS[g]; const m = dims === null ? n : dims;
    for (let i = 0; i < m; i++) s.add(off + i);
  }
  return s;
}

export function checkModelMeta(meta) {
  if (!meta || meta.schema_version !== SCHEMA_VERSION) return 'MODEL_SCHEMA_MISMATCH';
  if (!Array.isArray(meta.columns) || meta.columns.length === 0) return 'MODEL_METADATA_INVALID';
  const ok = allowedColumns();
  if (meta.columns.some(c => !ok.has(c))) return 'MODEL_USES_UNVERIFIED_FEATURES';
  return null;
}

export function assemble(groups, columns) {
  const x = new Float64Array(columns.length);
  for (let j = 0; j < columns.length; j++) {
    const c = columns[j]; let v;
    for (const [g, [off, n]] of Object.entries(GROUPS)) {
      if (c >= off && c < off + n) { const arr = groups[g]; v = arr ? arr[c - off] : undefined; break; }
    }
    if (v === undefined || Number.isNaN(v)) throw new Error('FEATURE_MISSING');
    x[j] = v;
  }
  return x;
}
