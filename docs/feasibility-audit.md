# SentinelPE Feasibility Audit (November 2026)

> **Status: feasibility evidence, not project results.** Every number below was measured in a cloud workspace,
> not on the development laptop: Linux, 2 vCPU Xeon @ 2.30 GHz, 8,414 MB RAM, no swap, Python 3.13.18,
> LightGBM 4.7.0, Node 22.23.5, headless Chromium 157. Laptop figures will come from
> [`feasibility/RUN_ON_LAPTOP.md`](../feasibility/RUN_ON_LAPTOP.md). No malware was used or executed, and no
> detection performance is claimed.

Evidence classes:
- **M-syn**: measured on synthetic EMBER-shaped data
- **M-proto**: measured with the exploratory JS prototype
- **M-real**: measured on real benign PE files
- **SRC**: verified in source code or documentation
- **EST**: estimate

The full table, with scripts and methods, is
[`feasibility/CLOUD_REFERENCE_RESULTS.md`](../feasibility/CLOUD_REFERENCE_RESULTS.md).

## 1. Kit corrections

Kit v1 had 13 defects. They included vacuous passes on empty test sets, a feature-count mismatch, an unsupported
claim about categorical and missing-value handling, hard-coded paths, and a disk check on the wrong drive. All 13
were reproduced, fixed and re-tested; see [`feasibility/CHANGES.md`](../feasibility/CHANGES.md).

## 2. Model-inference equivalence (ML-01, ML-02: synthetic stage)

- **Result:** 62,400 of 62,400 raw scores were bit-identical between LightGBM 4.7.0 (Python) and the JavaScript
  evaluator, in Node and in Chromium. **(M-syn)**
- **Models:** six cases covering numeric splits, categorical splits (up to 200 levels), NaN as missing, zero as
  missing, `use_missing=false`, and 50–500 trees.
- **Vectors:** boundary values at every tested threshold.
- **Rules corrected** (LightGBM `tree.h`, `meta.h`, `common.h`, all **SRC**):
  - the zero threshold is float32 1e-35, and values up to it become 0
  - ±1e300 thresholds mean ±infinity
  - NaN at a categorical split goes right
- **Still required:** repeat on the real local model with EMBER2024 vectors.

## 3. Feature-group audit (O1: exploratory prototype only)

**Corpus.** 106 benign PEs (100 from pinned, licensed PyPI wheels and 6 pip launchers) and 63 malformed variants;
159 files were compared. **(M-real + M-proto)**

| Group (dims) | Prototype | Evidence | Verdict |
|---|---|---|---|
| general (7) | implemented | 1,113/1,113 identical | PASS |
| histogram (256) | implemented | 40,704/40,704 | PASS |
| byteentropy (256) | implemented | 161 values at 1 ULP and 42 at 2 ULP, all in one 20.4 MB DLL | FAIL |
| strings (177) | implemented | 28,143/28,143 | PASS |
| header (74) | implemented | 11,766/11,766 | PASS |
| section (224) | implemented | 35,616/35,616 | PASS |
| datadirectories (34) | dims 0–29 only | 4,770/4,770 on dims 0–29 | partial. Dims 30–31 are always 0 in thrember; 32–33 are not implemented |
| imports (1,282), exports (129), richheader (33) | missing | — | not attempted; expected reproducible |
| authenticode (8), pefilewarnings (88) | missing | — | expected impractical (planning expectation) |

This is partial coverage, not parity. The local model may use only groups that pass, which is 768 features at
present. The server uses the full thrember extractor on uploaded bytes.

**Parser behaviour:**
- The strict JS parser rejected 10 of 169 files; thrember accepts 4 of those as PE.
- thrember raised an IndexError on the empty file.
- Truncated files with intact headers are accepted by both extractors.
- Packed files are **untested**.

## 4. Training memory (O2)

Results from `memory_sweep.py` on synthetic data with 2,568 columns, 64 leaves, 100 rounds and 2 threads
**(M-syn, cloud)**:

| Rows | Streamed Sequence, peak private MB | Build / train, s | In-memory copy, peak private MB |
|---|---|---|---|
| 50,000 | 881 | 8.1 / 30.0 | 1,489 |
| 100,000 | 883 | 14.3 / 42.2 | 2,885 |
| 200,000 | 1,194 | 42.7 / 70.0 | 5,654 |
| 300,000 | 1,574 | 62.4 / 93.8 | — |
| 400,000 | 2,059 | 80.1 / 127.4 | — |

What this means:
- thrember's `read_vectorized_features` and `train_model` copy the whole matrix into RAM, and `train_model` uses a
  random 10% validation split **(SRC)**. Neither is used.
- Weeks 1–40 hold roughly 1.8 million PE rows **(EST)**, so full training is unlikely to fit in 8 GB **(EST)**.
- The training size must be measured on the laptop with real vectors (Test 10). No row count is recommended here.
- Validation, calibration and test weeks stay complete; they are scored in batches.

## 5. Other measurements (cloud)

| Item | Result | Class |
|---|---|---|
| FastAPI benchmark server, 106 benign files | all answered; median 57.5 ms, max 4,926 ms; peak 343 MB private; wrong digest → 409; > 50 MB rejected (413 or connection reset) | M-real files, synthetic model |
| Server TreeSHAP (`pred_contrib`) | 2.01 ms per file; additivity gap 2.0e-12 | M-syn |
| Extraction of a 200 MB file | JS prototype 4.2 s / 495 MB; thrember 57.9 s / 2,091 MB | M-proto |
| Chromium Web Worker | 200 MB file in 4.7 s; main thread never blocked > 72 ms | M-proto (not Chrome, no extension) |
| SHA-256 | WebCrypto = hashlib, 100/100 files | M-real |
| Offline routing cost | 540,000 files × 20 budgets × 1,000 random repeats = 66.7 s | M-syn (timing only) |
| EMBER2024 PE zips | 23.1 GB | SRC (Hugging Face listing) |
| Vectorised X_train / X_test | ≈ 24.0 / 5.5 GB | EST |
| Unzipped JSONL size | **UNVERIFIED** | — |

## 6. Architecture status

| Component | Status |
|---|---|
| User-selected analysis | Shown in a web page (Chromium), not yet in an MV3 extension |
| JS extraction | Partial (768 features pass) |
| Local inference | Method shown on synthetic models |
| Escalation, consent | Design only |
| FastAPI + SHAP | Benchmark server only |
| Hash validation | Shown |
| Failure handling | Server-side rejections shown; SRV-03 to SRV-09 **not tested** |
| Offline routing | Compute cost shown; needs real scores |
| Pre-release interception | **Not demonstrated; not claimed** |

## 7. Claims that must stay estimates or be removed

- Any laptop memory, time or latency figure, until measured.
- Any fixed training size.
- Full-data training on the laptop.
- "60 GB is enough".
- "1,024 local features", "complete parity", "FastAPI ≈ 190 MB".
- Any detection metric.
- Pre-release quarantine.
- Packed or .NET support.
- "Truncated files are always UNSCANNED".

## 8. Decisions awaiting the supervisor

See the [README](../README.md) (Section 10) and [ADR 0004](decisions/0004-training-size-and-memory.md).
