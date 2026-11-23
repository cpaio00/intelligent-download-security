// Evaluates a LightGBM model exported with Booster.dump_model() (JSON), mirroring LightGBM 4.x prediction:
//  * kZeroThreshold is the float32 value 1e-35f (= 1.0000000180025095e-35 as a double).
//  * Dense inputs with |v| <= kZeroThreshold are treated as exact 0 (LightGBM drops them when it
//    converts a dense row to its sparse form), NaN is kept.
//  * The JSON export writes infinite thresholds as +/-1e300; they are restored to +/-Infinity.
//  * Numerical rule: NaN -> 0 unless missing_type is NaN; Zero/NaN missing values follow default_left;
//    otherwise left iff value <= threshold.
//  * Categorical rule (LightGBM tree.h CategoricalDecision): NaN -> right; negative -> right;
//    otherwise left iff trunc(value) is in the split's category list.
// Verified against LightGBM 4.7.0 by run_node.mjs and run_browser.html (see results).
const kZero = Math.fround(1e-35);
const fixThreshold = t => (t >= 1e300 ? Infinity : t <= -1e300 ? -Infinity : t);
export function prepare(model) {
  const walk = n => { if (n.leaf_value !== undefined) return;
    if (n.decision_type === '==') n._cats = new Set(String(n.threshold).split('||').map(Number));
    else n._th = fixThreshold(n.threshold);
    walk(n.left_child); walk(n.right_child); };
  model.tree_info.forEach(t => walk(t.tree_structure)); return model;
}
export function goLeft(n, v) {
  const mt = n.missing_type;
  if (v === null || v === undefined) v = NaN;            // JSON null encodes NaN
  else if (Math.abs(v) <= kZero) v = 0;                  // dense-to-sparse zero flush
  if (n.decision_type === '==') {
    if (Number.isNaN(v)) return false;
    const iv = Math.trunc(v); if (iv < 0) return false;
    return n._cats.has(iv);
  }
  if (Number.isNaN(v) && mt !== 'NaN') v = 0;
  if ((mt === 'Zero' && v >= -kZero && v <= kZero) || (mt === 'NaN' && Number.isNaN(v))) return n.default_left;
  return v <= n._th;
}
export function rawScore(model, x, trace) {
  let s = 0;
  for (const t of model.tree_info) { let n = t.tree_structure;
    while (n.leaf_value === undefined) { const l = goLeft(n, x[n.split_feature]); if (trace) trace(n, x[n.split_feature], l); n = l ? n.left_child : n.right_child; }
    s += n.leaf_value; }
  return s;
}
