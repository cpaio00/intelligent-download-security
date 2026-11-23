# Reference results from the cloud workspace (NOT laptop measurements)

**Machine:** Linux container; 2 vCPU Intel Xeon @ 2.30 GHz; 8,414 MB RAM (psutil; 8,024 MiB); no swap.
**Software:** Python 3.13.18, LightGBM 4.7.0, numpy 2.5.3, Node 22.23.5, headless Chromium 157.0.8103.78, thrember 0.1.0
(commit 0ef753e).

This machine has the same core count as the i7-6600U (2 cores) but no hyper-threading, a different CPU generation, a
different OS and no page file. **None of these numbers predicts the laptop.** They show only that the scripts work and
the rough scale of each cost.

Evidence classes:
- **M-syn**: measured on synthetic EMBER-shaped data
- **M-proto**: measured with the exploratory JS prototype
- **M-real**: measured on real benign PE files
- **SRC**: verified by reading source code or documentation
- **EST**: arithmetic or extrapolation, not measured

| ID | Claim | Value | Class | Script and configuration | Data | Method |
|---|---|---|---|---|---|---|
| R1 | JS evaluator matches LightGBM | 62,400 of 62,400 raw scores bit-identical (vs in-memory and reloaded models), Node and Chromium | M-syn | `equivalence/gen_cases.py`, `run_node.mjs`, `run_browser.html` | 6 models: 50–500 trees, 15–64 leaves, 20–200 features, categorical (up to 200 levels), NaN, zero-as-missing, `use_missing=false`; 10,400 vectors each | `===` on float64 raw scores; 34 (rule, input, branch) combinations recorded. Not generated: numeric `missing_type=None` with `default_left=false` (per `tree.h`, `default_left` is not consulted in that case) |
| R2 | JS per-vector inference, Chromium | 0.0039–0.1075 ms | M-syn | `run_browser.html` | as R1 | `performance.now()` over 10,400 vectors |
| R3 | Compact 1,024-feature model: size, load time, speed (Node) | 100×31: 1.24 MB, 9 ms, 0.0135 ms/vector; 300×64: 7.13 MB, 37 ms, 0.0395 ms; 500×64: 11.81 MB, 57 ms, 0.0805 ms; all 2,000/2,000 exact | M-syn | `compact/compact_bench.py --train-rows 100000`, `js_infer_bench.mjs` | 100,000 training rows; 2,000 held-out rows | JSON byte length; `performance.now()` |
| R4 | Training memory, streamed (`Sequence`, `bin_construct_sample_cnt=20000`, `force_col_wise=true`, 64 leaves, lr 0.1, `min_data_in_leaf=100`, 2 threads, 100 rounds) | 50k: 881 MB, 8.1 s build / 30.0 s train · 100k: 883 MB, 14.3 / 42.2 · 200k: 1,194 MB, 42.7 / 70.0 · 300k: 1,574 MB, 62.4 / 93.8 · 400k: 2,059 MB, 80.1 / 127.4 | M-syn | `memory/memory_sweep.py` | Synthetic 2,568 columns (40% dense normal, 60% sparse integers) | Child-process RssAnon sampled every 0.2 s (excludes memory-mapped file pages) |
| R5 | Training memory, in-memory copy (as `thrember.read_vectorized_features`; default sampling) | 50k: 1,489 MB · 100k: 2,885 MB · 200k: 5,654 MB (minimum available 1,826 MB) | M-syn | `memory_sweep.py --mode numpy` | as R4 | as R4. An earlier in-process 200k run in this session was killed for lack of memory; the v2 child-process run finished. Treat 200k in-memory as at the limit of an 8 GB machine |
| R6 | Feature parity, JS prototype vs thrember | PASS: general, histogram, strings, header, section, datadirectories dims 0–29. FAIL: byteentropy (161 values at 1 ULP and 42 at 2 ULP, all in one 20.4 MB file). Not implemented: imports, exports, datadirectories 30–33, richheader, authenticode, pefilewarnings | M-real + M-proto | `parity/run_parity.py --files corpus variants` | 106 benign PEs (100 from wheels plus 6 launchers; AMD64, I386, ARM64, one .NET, two signed) and 63 variants; 159 files compared | float32 ULP comparison under the pre-declared rule |
| R7 | Strict-parser rejections | JS rejected 10 of 169 files. thrember accepts 4 of those as PE (TOO_MANY_SECTIONS, SECTION_VA_OVERLAP ×2, BAD_OPT_MAGIC). thrember raised IndexError on the empty file. Truncated variants were accepted by both | M-proto | as R6 | as R6 | status fields |
| R8 | Extraction time and peak RSS (Node prototype / thrember) | 10 MB: 226 ms, 77 MB / 2,784 ms, 308 MB · 60 MB: 1,214 / 17,020 ms · 100 MB: 2,234 ms, 294 MB / 30,090 ms, 1,147 MB · 200 MB: 4,223 ms, 495 MB / 57,900 ms, 2,091 MB | M-proto | `checks/extract_speed.py large` | `w64.exe` plus a random overlay (`tools/make_large_pe.py`) | Wall time; psutil RSS of the child sampled every 50 ms |
| R9 | Browser extraction (Chromium Web Worker) | 10 MB: 231 ms · 100 MB: 2,312 ms · 200 MB: 4,684 ms; SHA-256 14 / 128 / 392 ms; worst main-thread timer gap ≤ 72 ms (50 ms timer) | M-proto | `browser_test/` via `tools/pw_browser_check.js` | 10 files (corpus, variants, large) | `performance.now()`. Headless Chromium, **not Chrome**; no extension |
| R10 | SHA-256 agreement | WebCrypto = hashlib for 100/100 manifest files (Node). The browser digest equalled `sha256sum` for the 3 files checked | M-real | `checks/hash_check.mjs` | corpus | string equality |
| R11 | FastAPI server (uvicorn, 127.0.0.1) | corpus: 106/106 HTTP 200, median 57.5 ms, max 4,926 ms (20.4 MB file), idle 162 MB, peak 343 MB private · variants: 57×200, 6×422 · 10 MB: 3,116 ms · 60/100/200 MB: rejected (connection reset) · wrong digest: 409 | M-real + M-syn model | `server/server_bench.py` with `full_model.txt` (2,568 features, 100 trees, 64 leaves, synthetic) | corpus, variants, large | Localhost round trip; server RssAnon. No network latency, TLS, authentication or concurrency |
| R12 | Server prediction and SHAP | predict 0.04 ms; `pred_contrib` 2.01 ms; `shap.TreeExplainer` 1.12 ms per file; additivity gap 2.0e-12; 163 MB | M-syn | `server/shap_bench.py` | 200 held-out synthetic rows | `perf_counter` |
| R13 | Offline routing evaluation compute cost | 540,000 files × 20 budgets × 1,000 random repetitions = 66.7 s (100 repetitions: 5.6 s). The block bootstrap was not timed | M-syn | `checks/routing_cost.py` | random scores | `perf_counter`. **Recall values are meaningless** |
| R14 | Vectorising one raw record | 0.55 ms (local records of 7.1–19.2 KB) | M-real | `checks/vectorize_bench.py corpus` | 20 local benign records, not EMBER2024 | `perf_counter`. EMBER2024 record sizes are UNVERIFIED |
| D1 | EMBER2024 PE download size | Win32 12.32 + 2.59 GB, Win64 5.85 + 1.18 GB, Dot_Net 0.94 + 0.22 GB (train + test) = 23.1 GB zipped | SRC | Hugging Face API file list, `joyce8/EMBER2024` | — | Listed sizes |
| D2 | Vectorised matrix size | X_train ≈ 24.0 GB, X_test ≈ 5.5 GB (float32) | EST | 2,340,000 × 2,568 × 4 B; 540,000 × 2,568 × 4 B; float32 verified in thrember `vectorize_subset` | — | arithmetic |
| D3 | Unzipped JSONL size | **UNVERIFIED** | — | — | — | Measure after the first download. The 60 GB planning figure is an estimate and may be too low while zip and JSONL coexist |
| S1 | `read_vectorized_features` copies the full matrix into RAM; `train_model` does too and uses a random 10% validation split with `categorical_feature=[2,3,4,5,6,701,702]` | — | SRC | thrember `model.py` (commit 0ef753e) | — | read the source |
| S2 | Row order of `X_train.dat` = sorted JSONL names, then line order | — | SRC | `gather_feature_paths`, `raw_feature_iterator` | — | read the source |
| S3 | LightGBM prediction rules followed by the JS evaluator | — | SRC | LightGBM 4.7.0 `tree.h`, `meta.h`, `common.h` | — | read the source, confirmed by R1 |
