"""Command line for the SentinelPE research pipeline. Run `python -m sentinelpe_ml <command> --help`.

Typical order on real data (UNTESTED on EMBER2024):
  audit -> sample -> train (server, local) -> score -> fit-thresholds -> evaluate -> export-browser
"""
import argparse
import json
import os
import sys

import numpy as np


def _rows(path):
    return np.load(path).astype(np.int64)


def cmd_audit(a):
    from .data import week_table
    w, l = week_table(a.data_dir, a.subset)
    np.save(f"{a.out_prefix}_weeks.npy", w); np.save(f"{a.out_prefix}_labels.npy", l)
    keys, cnt = np.unique(np.stack([w.astype(np.int32), l.astype(np.int32)], 1), axis=0, return_counts=True)
    counts = {f"week{int(k[0])}|label{int(k[1])}": int(c) for k, c in zip(keys, cnt)}
    json.dump({"rows": int(len(w)), "weeks_min": int(w.min()), "weeks_max": int(w.max()), "counts": counts},
              open(f"{a.out_prefix}_audit.json", "w"), indent=1)
    print(f"{len(w)} rows, official weeks {w.min()}-{w.max()}; unlabelled {(l == -1).sum()}")


def cmd_sample(a):
    from .data import stratified_sample, week_rows
    w, l = np.load(a.weeks), np.load(a.labels)
    rows = week_rows(w, l, a.week_lo, a.week_hi)
    idx = rows if a.n <= 0 else stratified_sample(rows, w, l, a.n, a.seed)
    np.save(a.out, idx)
    json.dump({"weeks": [a.week_lo, a.week_hi], "eligible": int(len(rows)), "n": int(len(idx)), "seed": a.seed,
               "rule": "stratified by (week, label), largest remainder"}, open(a.out[:-4] + ".json", "w"), indent=1)
    print(f"eligible {len(rows)} -> selected {len(idx)}")


def cmd_train(a):
    from .data import open_vectors
    from .features import N_FEATURES, local_columns
    from .train import save, train
    X, y = open_vectors(a.x, a.y)
    cols = np.arange(N_FEATURES) if a.role == "server" else local_columns()
    rows = _rows(a.rows)
    side = a.rows[:-4] + ".json"
    info = json.load(open(side)) if os.path.exists(side) else {}
    b, meta = train(X, y, rows, cols, a.rounds, a.role, json.loads(a.params), info)
    save(b, meta, a.out)
    print(f"{meta['model_version']}: {len(cols)} features, {meta['trees']} trees, build {meta['construct_s']} s, train {meta['train_s']} s")


def cmd_score(a):
    from .data import open_vectors
    from .score import score
    from .train import load
    b, meta = load(a.model); X, y = open_vectors(a.x, a.y)
    rows = _rows(a.rows); s = score(b, X, rows, np.array(meta["columns"]))
    np.save(a.out, s); print(f"scored {len(s)} rows")


def cmd_fit_thresholds(a):
    from .thresholds import routing_band, threshold_at_fpr
    from .train import load
    sl, ss, y = np.load(a.local_scores), np.load(a.server_scores), np.load(a.labels)
    tl, ts = threshold_at_fpr(sl, y, a.target_fpr), threshold_at_fpr(ss, y, a.target_fpr)
    bands = [routing_band(sl, ss >= ts, y, b, a.target_fpr) for b in a.budgets]
    for prefix, t in ((a.local_model, tl), (a.server_model, ts)):
        _, meta = load(prefix); meta["thresholds"][str(a.target_fpr)] = {"decision": t}
        if prefix == a.local_model:
            meta["thresholds"][str(a.target_fpr)]["bands"] = bands
        json.dump(meta, open(prefix + ".meta.json", "w"), indent=1)
    print(json.dumps({"t_local": tl, "t_server": ts, "bands": bands}, indent=1))


def cmd_evaluate(a):
    from .routing import evaluate
    from .train import load
    _, lm = load(a.local_model); _, sm = load(a.server_model); key = str(a.target_fpr)
    if key not in lm["thresholds"] or key not in sm["thresholds"]:
        sys.exit("fit-thresholds must be run for this operating point first")
    res = evaluate(np.load(a.local_scores), np.load(a.server_scores), np.load(a.labels), np.load(a.weeks),
                   lm["thresholds"][key]["decision"], sm["thresholds"][key]["decision"], lm["thresholds"][key]["bands"],
                   seeds=list(range(a.seed0, a.seed0 + a.repetitions)), n_boot=a.bootstrap)
    res["operating_point_fpr"] = a.target_fpr
    json.dump(res, open(a.out, "w"), indent=1, default=float); print("written", a.out)


def cmd_export(a):
    from .export import export_browser
    from .train import load
    b, meta = load(a.model)
    if not meta["thresholds"]:
        sys.exit("fit thresholds before exporting: the extension needs them")
    export_browser(b, meta, a.out); print("exported to", a.out)


def cmd_dev_models(a):
    from .devmodels import make_dev_models
    make_dev_models(a.out, a.rows, a.seed)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sentinelpe_ml"); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("audit", help="week and label of every row, in thrember row order")
    p.add_argument("--data-dir", required=True); p.add_argument("--subset", required=True); p.add_argument("--out-prefix", required=True); p.set_defaults(f=cmd_audit)
    p = sub.add_parser("sample", help="labelled rows of official weeks lo..hi, optionally a stratified sample of n")
    for k in ("--weeks", "--labels", "--out"): p.add_argument(k, required=True)
    p.add_argument("--week-lo", type=int, required=True); p.add_argument("--week-hi", type=int, required=True)
    p.add_argument("--n", type=int, default=0); p.add_argument("--seed", type=int, default=2026); p.set_defaults(f=cmd_sample)
    p = sub.add_parser("train", help="streamed training (server: all 2,568 features; local: parity-passed groups)")
    p.add_argument("--x", required=True); p.add_argument("--y"); p.add_argument("--rows", required=True)
    p.add_argument("--role", choices=["server", "local"], required=True); p.add_argument("--rounds", type=int, required=True)
    p.add_argument("--params", default="{}"); p.add_argument("--out", required=True); p.set_defaults(f=cmd_train)
    p = sub.add_parser("score", help="batch scores for selected rows")
    p.add_argument("--model", required=True); p.add_argument("--x", required=True); p.add_argument("--y")
    p.add_argument("--rows", required=True); p.add_argument("--out", required=True); p.set_defaults(f=cmd_score)
    p = sub.add_parser("fit-thresholds", help="operating-point thresholds and routing bands on calibration weeks")
    for k in ("--local-scores", "--server-scores", "--labels", "--local-model", "--server-model"): p.add_argument(k, required=True)
    p.add_argument("--target-fpr", type=float, default=0.01)
    p.add_argument("--budgets", type=float, nargs="+", default=[round(0.05 * i, 2) for i in range(1, 20)]); p.set_defaults(f=cmd_fit_thresholds)
    p = sub.add_parser("evaluate", help="offline routing evaluation on test weeks")
    for k in ("--local-scores", "--server-scores", "--labels", "--weeks", "--local-model", "--server-model", "--out"): p.add_argument(k, required=True)
    p.add_argument("--target-fpr", type=float, default=0.01); p.add_argument("--repetitions", type=int, required=True)
    p.add_argument("--seed0", type=int, default=0); p.add_argument("--bootstrap", type=int, default=1000); p.set_defaults(f=cmd_evaluate)
    p = sub.add_parser("export-browser", help="local model JSON + metadata for the extension")
    p.add_argument("--model", required=True); p.add_argument("--out", required=True); p.set_defaults(f=cmd_export)
    p = sub.add_parser("make-dev-models", help="SYNTHETIC models for developing the extension and server (not results)")
    p.add_argument("--out", required=True); p.add_argument("--rows", type=int, default=20000); p.add_argument("--seed", type=int, default=7)
    p.set_defaults(f=cmd_dev_models)
    a = ap.parse_args(argv); a.f(a)


if __name__ == "__main__":
    main()
