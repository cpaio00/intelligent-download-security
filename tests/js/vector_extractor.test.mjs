import test from 'node:test'; import assert from 'node:assert/strict'; import fs from 'node:fs';
import { allowedColumns, assemble, checkModelMeta, SCHEMA_VERSION, GROUPS } from '../../extension/lib/vector.mjs';
import { extractBrowserFeatures } from '../../extension/lib/features/sentinel_features.mjs';
const C = JSON.parse(fs.readFileSync(new URL('../../extension/lib/features/constants.json', import.meta.url)));

test('only parity-passed columns are allowed (768 at present)', () => {
  const a = allowedColumns(); assert.equal(a.size, 768);
  assert.ok(!a.has(GROUPS.byteentropy[0])); assert.ok(!a.has(GROUPS.imports[0])); assert.ok(!a.has(2405 + 30));
});

test('model metadata checks', () => {
  assert.equal(checkModelMeta({ schema_version: SCHEMA_VERSION, columns: [0, 7, 2434] }), null);
  assert.equal(checkModelMeta({ schema_version: 'other', columns: [0] }), 'MODEL_SCHEMA_MISMATCH');
  assert.equal(checkModelMeta({ schema_version: SCHEMA_VERSION, columns: [] }), 'MODEL_METADATA_INVALID');
  assert.equal(checkModelMeta({ schema_version: SCHEMA_VERSION, columns: [263] }), 'MODEL_USES_UNVERIFIED_FEATURES');
});

test('assemble maps EMBER columns to group arrays', () => {
  const groups = { general: [1, 2, 3, 4, 5, 6, 7], datadirectories: Array.from({ length: 30 }, (_, i) => 100 + i) };
  assert.deepEqual(Array.from(assemble(groups, [6, 2405, 2434])), [7, 100, 129]);
  assert.throws(() => assemble(groups, [7]), /FEATURE_MISSING/);
});

test('extractor rejects non-PE inputs', () => {
  assert.equal(extractBrowserFeatures(new Uint8Array(0), C).status, 'reject');
  assert.equal(extractBrowserFeatures(new Uint8Array(5000).fill(7), C).status, 'reject');
  const mz = new Uint8Array(4096); mz[0] = 0x4d; mz[1] = 0x5a; mz[0x3c] = 0xff; mz[0x3d] = 0xff;
  assert.equal(extractBrowserFeatures(mz, C).status, 'reject');
});
