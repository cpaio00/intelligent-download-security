# tests/

> All tests use **synthetic dev models** and a benign, MIT-licensed pip launcher. None is evidence of detection
> performance. Browser tests run in headless **Chromium** via Playwright, not Google Chrome, on Linux; nothing
> here has run on Windows.

| Suite | Command | Covers |
|---|---|---|
| Python | `python -m pytest -q tests/python` | Pipeline: data access, week index, stratified sampling, streamed training, batch scoring, browser export (bit-identical JS vs Python raw scores, including NaN and zero), thresholds (meets the target FPR; brute-force optimal band), routing (random, oracle, bootstrap, Wilson, stability). Server: auth, digest, size limit, non-PE and malformed input, timeout and recovery |
| JavaScript | `npm run test:js` | Decision logic, reply validation, upload failure states, parity-gated columns, extractor rejections |
| End to end | `npm run test:e2e` | Unpacked extension + real FastAPI server + faulty fake servers: 18 checks |

Testing-plan coverage. The tests exercise these IDs on the prototype; the tests that need real EMBER2024 data are
still to come:

| ID | How it is exercised |
|---|---|
| SRV-01 | Declined upload: UNSCANNED, and the browser network capture shows no request |
| SRV-02 | Consented upload: one request, exact bytes, digest header, no file name |
| SRV-03 | Server unavailable |
| SRV-04 | Server timeout (client timeout shortened for the test) |
| SRV-05 | Malformed reply |
| SRV-06 | Digest mismatch |
| SRV-07 | 401 in the e2e test; 413 and 401 in the server tests |
| SRV-09 | Interrupted analysis is reported on reopen. This is simulated with the stored in-progress flag; a real page or service-worker kill is not tested |
| PE-02, PE-05 | Non-PE and empty input |
| ML-04 | Wrong schema or unverified columns are refused |

Not covered: SRV-08 (the server writes no temporary files, so there is nothing to clean up; this is not tested),
PE-03 and PE-04 policy, Chrome on Windows, and real models.
