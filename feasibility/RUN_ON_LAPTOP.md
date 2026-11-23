# SentinelPE feasibility kit v2: running it on the laptop (Windows)

This kit repeats, on your laptop (i7-6600U, 2 cores / 4 threads, 8 GB RAM), the tests I ran in a cloud workspace.
The cloud numbers are in `CLOUD_REFERENCE_RESULTS.md`. They are not laptop measurements. **Only the numbers you
record on the laptop can be quoted as laptop results.**

**Safety rules**
- Use benign files only. The kit builds its own corpus from licensed open-source Python wheels (Test 3).
- Nothing in this kit runs a PE file. Wheels are zip archives; PE files are only copied out of them and read as bytes.
- `make_synth.py` writes random numbers shaped like EMBER2024 (2,568 columns). Use it only for memory and speed tests.
  Any accuracy it produces means nothing and must never be reported.

**Logging:** for every test, write down the date, the command, the full output, what else was open, and whether
Windows became slow, froze, or closed a program. Save every CSV/JSON the scripts write into a `results\` folder.

All commands run from the `feasibility` folder of this repository (the "kit folder") in **Command Prompt** (`cmd`). Replace `D:\sentinelpe` with the folder and
drive where you will keep the large files. Use the same drive that will hold EMBER2024.

---

## 0. Setup (once)

1. Install **Python 3.12, 64-bit**, from python.org. Tick "Add python.exe to PATH".
2. Install **Node.js 22 LTS** from nodejs.org.
3. Install **Git for Windows**, which `thrember` needs.
4. In the kit folder:
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install "thrember @ git+https://github.com/FutureComputing4AI/EMBER2024@0ef753e81d98bf209f71b03cd331dfc190b5b54d"
mkdir results
mkdir D:\sentinelpe
```
`lightgbm==4.7.0` is pinned because the equivalence tests are tied to that version's prediction rules. If you
change the version, run Test 2 again.

## Test 1: Environment and dataset drive
```
python env_check.py --data-dir D:\sentinelpe --need-gb 60 > results\env_check.txt
type results\env_check.txt
```
Free space is checked on the drive that holds `--data-dir`, not on C:. The script exits with code 2 if there is not
enough space. **60 GB is a planning estimate, not a measured requirement** (see `CLOUD_REFERENCE_RESULTS.md`,
section "Disk"). Also record the Windows edition and build from `winver`.

## Test 2: JavaScript and Python model equivalence (Node, then Chrome)
```
cd equivalence
python gen_cases.py
node run_node.mjs > ..\results\equivalence_node.txt
type ..\results\equivalence_node.txt
cd ..
```
**Pass:** six cases, each `"pass": true`, and the final line `ALL CASES PASS (bit-identical raw scores)`.
A case with zero vectors counts as a failure. The six cases cover numerical, categorical, NaN, zero-as-missing,
`use_missing=false`, boundary values (each threshold and the next float either side, ±1e-36, -0), and small to
500-tree models. `*_coverage.json` lists every split rule, input and branch that was actually exercised.

Chrome: in the kit folder run `python -m http.server 8765`, open
`http://localhost:8765/equivalence/run_browser.html` in Chrome, wait for the last line, and save the page text to
`results\equivalence_chrome.txt`. **Pass:** the same as for Node.

## Test 3: Build the benign corpus and its variants
```
python corpus_tools\build_corpus.py --out corpus
python corpus_tools\build_variants.py --corpus corpus --out variants
node checks\hash_check.mjs corpus corpus_tools\wheel_manifest.json
```
**Pass:** `wheel PE files verified: 100/100`, and the hash check reports `"mismatch":0,"missing":0`. This check
compares WebCrypto SHA-256, the same API Chrome uses, with the Python `hashlib` values in the manifest.
The six launcher `.exe` files come from your installed pip. Their hashes go into `corpus\corpus_launchers.json` and
can differ from mine if your pip version differs.

## Test 4: Feature parity (exploratory JS prototype vs thrember)
```
python parity\run_parity.py --files corpus variants --out results\parity_results.json
```
The output gives a verdict for each feature group under the pre-declared rule:
- **PASS:** every value is identical.
- **CONDITIONAL:** the only differences are 1 ULP. The group is still excluded unless you show that local-model
  predictions do not change.
- **FAIL:** any larger difference.

Groups the prototype does not compute are listed as not implemented. Truncated variants whose headers survive are
*accepted* by both extractors; they are not rejected. Whether truncated files should be UNSCANNED is a design
decision (testing plan PE-03), so record what happens rather than treating it as a pass. Record the verdicts, the files the JS extractor
rejected (these become UNSCANNED), and any files thrember accepts but JS rejects.

## Test 5: Training memory (the key laptop test)
Close Chrome, VS Code and other heavy programs, and write down what was still open. Open Task Manager → Performance → Memory.
```
python make_synth.py 402000 D:\sentinelpe\synth.npy
python memory\memory_sweep.py --data D:\sentinelpe\synth.npy --rows 50000 100000 150000 --budget-mb 3000 --floor-mb 800 --out results\memory_sweep.csv
```
`make_synth.py` writes about 4.1 GB. The sweep runs each row count in a new process. For each run it records:
- peak private memory (the same as the "Commit size" column in Task Manager)
- minimum available system memory
- page-file growth
- Dataset construction time
- training time (100 rounds)
- the full LightGBM parameters

It **stops a run itself** if available memory drops below `--floor-mb` or the process goes over `--budget-mb`, and
it does not try larger sizes after that.

If all three runs finish with `status ok`, continue to larger sizes. Add `--keep-going` only if you want to go past
a stopped run.
```
python memory\memory_sweep.py --data D:\sentinelpe\synth.npy --rows 200000 250000 300000 --budget-mb 3000 --floor-mb 800 --out results\memory_sweep.csv
```
Optional comparison, showing the standard in-memory loading that `thrember` uses, at 50,000 rows only:
```
python memory\memory_sweep.py --data D:\sentinelpe\synth.npy --mode numpy --params "{\"bin_construct_sample_cnt\":200000,\"force_col_wise\":false}" --rows 50000 --budget-mb 3000 --out results\memory_sweep_numpy.csv
```
**How to choose the training size:** use the largest row count with `status ok` where:
- `min_available_mb` stayed at or above 1,000 MB
- `swap_used_delta_mb` stayed near 0
- Windows stayed responsive

Then leave a margin by using about 75% of that count. Repeat that size once with your normal background programs
open. The choice must come from your CSV. Do not pick it from my cloud numbers. If a run ends with `process_failed`
or Windows closes a program, record it as a failure at that size.

## Test 6: Compact model export, size and Node speed
```
python compact\compact_bench.py --data D:\sentinelpe\synth.npy --train-rows 100000 --out compact_models
node compact\js_infer_bench.mjs compact_models\m100x31
node compact\js_infer_bench.mjs compact_models\m300x64
node compact\js_infer_bench.mjs compact_models\m500x64
```
The test vectors are the **last 2,000 rows** of the matrix, so they never overlap the training rows. The script
refuses to run if the matrix is too small. **Pass:** `vectors` is 2000, `exact` is 2000, and `"pass":true`.
Record the JSON size, load time and per-vector time.

## Test 7: Browser extraction in Chrome
```
python tools\make_large_pe.py corpus\w64.exe large 10 100 200
python -m http.server 8765
```
Open `http://localhost:8765/browser_test/` in Chrome. Select a few corpus files, then a few variants, then the files
in `large\`.

**Pass:**
- Rejected files show `UNSCANNED`.
- The tick counter keeps increasing.
- `worstMainThreadGapMs` stays small (under about 200 ms).
- Chrome does not crash.

Record `extractMs`, `hashMs` and `readMs` for each file. Note that this is the exploratory extractor, not the
final one.

## Test 8: Server: full-feature model, SHAP and FastAPI
```
python server\make_full_model.py --data D:\sentinelpe\synth.npy --train-rows 50000 --out full_model.txt
python server\shap_bench.py --data D:\sentinelpe\synth.npy --model full_model.txt
python server\server_bench.py --folder corpus --model full_model.txt --out results\server_bench_corpus.json
python server\server_bench.py --folder variants --model full_model.txt --out results\server_bench_variants.json
python server\server_bench.py --folder large --model full_model.txt --out results\server_bench_large.json
```
**Pass:**
- `shap_bench` reports `additivity max gap` below 1e-6 (the SHAP values plus the expected value equal the raw score).
- `server_bench` exits without error.
- There are no hash mismatches in the replies.
- `wrong_digest_request_status` is 409.
- Files over 50 MB come back as `413` or `reset`. `reset` means the server refused the upload from its declared
  size and closed the connection without reading it. Both count as rejected, and the extension must show
  UNSCANNED for either.

Record the median and maximum latency and the server's idle and peak private memory. The server binds to
127.0.0.1 only.

## Test 9: Other compute checks
```
python checks\extract_speed.py large
python checks\vectorize_bench.py corpus
python checks\routing_cost.py 540000 1000
```
`routing_cost.py` uses random scores and only measures how long the offline routing evaluation takes. Its recall
numbers mean nothing.

## Test 10: Real EMBER2024 memory test (after the data audit; partly UNTESTED)
The synthetic sweep only shows how memory grows with row count. Real EMBER2024 rows have a different value
distribution, and LightGBM's binned Dataset size depends on it, so **the real training size must come from this
test**.
1. Download only the PE subsets (`Win32`, `Win64`, `Dot_Net`) to the data drive. thrember's
   `download_dataset(dir, file_type="PE")` unzips each file and then deletes the zip. Check free space after every
   file.
2. Vectorise with `thrember.create_vectorized_features(dir)`. The script that calls it must start with
   `if __name__ == "__main__":`, because thrember uses `multiprocessing.Pool` and Windows needs that guard. It
   writes `X_train.dat` as float32 (about 24.0 GB for 2,340,000 × 2,568) and `X_test.dat` (about 5.5 GB). These
   sizes are arithmetic, not measured.
   **Do not call `thrember.read_vectorized_features` or `thrember.train_model` on the laptop.** They copy the whole
   matrix into RAM with `np.array(...)`.
3. Build the training-week index. `tools\make_week_index.py` is **UNTESTED on real data**. Check the first records it
   prints.
```
python tools\make_week_index.py --data-dir D:\sentinelpe\ember --subset train --weeks 0-39 --out results\idx_train_weeks.npy
```
4. Sweep with the real file, the index, and the same categorical features as the reference `train_model`
   (`2,3,4,5,6,701,702`):
```
python memory\memory_sweep.py --data D:\sentinelpe\ember\X_train.dat --index results\idx_train_weeks.npy --params "{\"categorical_feature\":\"2,3,4,5,6,701,702\"}" --rows 100000 200000 300000 --budget-mb 3000 --floor-mb 800 --out results\memory_sweep_real.csv
```
5. Choose the training size from this CSV using the rule in Test 5. Keep the validation, calibration and test
   weeks complete. Scoring them with `booster.predict` one batch at a time (for example 10,000 rows read from the
   memmap) needs little memory.
   **Exception:** early stopping inside `lgb.train` needs the validation weeks as a second LightGBM Dataset, and
   that memory was *not* included in this sweep. You can either:
   - repeat the sweep with that Dataset added, or
   - avoid it: train a fixed number of rounds, then score the validation weeks in batches at several
     `num_iteration` values and choose the round count from those scores.

## Scripts that were NOT tested in the cloud workspace
- Every command above run **on Windows**. All the scripts were run on Linux. The Windows-specific code paths
  (psutil private bytes, path handling) were written for Windows but not executed there.
- `browser_test` in **real Google Chrome**. It was tested in headless Chromium 157 through `tools\pw_browser_check.js`.
- `tools\make_week_index.py` and Test 10 as a whole: there was no EMBER2024 access. The script was only checked
  on made-up toy metadata, where it gave the correct week and label filtering.
- Anything involving a **Chrome extension** (MV3 service worker, downloads API, consent UI). This kit contains no
  extension.
