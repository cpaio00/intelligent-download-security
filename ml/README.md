# ml/ — research pipeline (`sentinelpe_ml`)

> **Status: initial implementation, tested only on synthetic data** (`tests/python`). Not yet run on EMBER2024.
> Nothing in this folder produces results until it is run on the audited EMBER2024 split.

Install: `python -m pip install -r requirements.txt` (plus `thrember` for vectorising).

Run from this folder as `python -m sentinelpe_ml <command> --help`. Typical order on real data:

| Step | Command | What it does |
|---|---|---|
| 1 | `audit --data-dir D:\ember --subset train --out-prefix out\train` | Week (from `first_submission_date`) and label of every row, in thrember row order, plus per-week counts. *Untested on real data.* |
| 2 | `sample --weeks out\train_weeks.npy --labels out\train_labels.npy --week-lo 0 --week-hi 39 --n <n> --out out\train_rows.npy` | Labelled training-week rows; with `--n`, a sample stratified by (week, label) with a recorded seed (ADR 0004) |
| 3 | `train --x D:\ember\X_train.dat --rows out\train_rows.npy --role server --rounds <R> --out out\server` (and `--role local`) | Streamed LightGBM training (never loads the matrix into RAM). The server uses 2,568 features; the local model uses parity-passed groups only (`features.LOCAL_GROUPS`) |
| 4 | `score --model out\local --x ... --rows <calibration or test rows> --out ...` | Batch scores, so complete evaluation weeks are scored |
| 5 | `fit-thresholds ...` | Operating-point thresholds and routing bands on **calibration weeks only** |
| 6 | `evaluate ... --repetitions <R>` | Always Local, Always Server, Confidence, Random (repeated) and Oracle routing; Wilson intervals; week-level block bootstrap (ADR 0003) |
| 7 | `export-browser --model out\local --out ..\extension\model` | `dump_model()` JSON plus metadata (columns, thresholds) for the extension |

`make-dev-models --out ..\dev_models` builds **synthetic** models so the extension and server can be developed.
Their `model_version` starts with `DEV-SYNTHETIC`, and their output is meaningless.

Before training the local model, update `features.LOCAL_GROUPS` and `extension/lib/vector.mjs`
(`PARITY_PASSED`) from the project's real parity results.
