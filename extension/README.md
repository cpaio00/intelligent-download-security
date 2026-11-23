# extension/ — Chrome MV3 extension

> **Status: initial implementation, tested in headless Chromium with synthetic dev models**
> (`tests/js`, `tests/e2e`). Not yet tested in Google Chrome on Windows. It does **not** intercept downloads.
> It analyses files the user selects (primary workflow, ADR 0002).

**Load it:** generate a model (see `model/README.md`), then open `chrome://extensions` → Developer mode →
**Load unpacked** → this folder → click the SentinelPE toolbar icon.

What happens to a file:
1. You select a file. It is read in the page, and a Web Worker computes its SHA-256 and the static features. The file is never run.
2. The local LightGBM model (`lib/lgbm_eval.mjs`, bit-identical to LightGBM on the tested models) scores it.
3. The score is compared with the band fitted on calibration weeks:
   - below the band: benign, decided locally
   - at or above its upper edge: malicious, decided locally
   - inside the band: you are asked whether to send the file
4. Only with your consent, the file's bytes and SHA-256 are sent to the server; the file name is not. The reply must match the schema and the digest.
5. Every failure is **UNSCANNED**: no model, wrong schema, unverified features, non-PE, extraction failure, missing feature, declined, no server, server unreachable, timeout, refusal, invalid reply, digest mismatch, interrupted analysis.

`lib/vector.mjs` refuses a model that uses features outside the parity-passed set (`PARITY_PASSED`).
`lib/features/` is the exploratory extractor from `feasibility/proto_js`.
