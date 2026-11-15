# SENTINELPE Testing and Evaluation Plan

> **Status: proposed test plan.** No test in this document is claimed to have been executed. Record actual environment details, outputs, failures, and evidence before marking a test complete.

## 1. Testing objectives

The testing process must establish:

1. Whether the selected Chrome workflow can provide the claimed file-access boundary.
2. Whether supported PE files are validated and parsed safely.
3. Whether browser-side features agree with the reference feature pipeline.
4. Whether the local classifier performs better than an appropriate simple baseline.
5. Whether optional server escalation is genuinely consent-gated and handles failures safely.
6. What accuracy, false-positive, latency, and resource limitations remain.

## 2. Chrome workflow and staging feasibility

Use benign files only and a disposable browser profile.

| ID | Test | Procedure / evidence required | Acceptance condition |
|---|---|---|---|
| CH-01 | Download event lifecycle | Timestamp event callbacks and download state changes | Event sequence recorded and repeatable |
| CH-02 | Filename suggestion | Test `onDeterminingFilename` with a benign file | Actual chosen path and API outcome recorded |
| CH-03 | Pause/resume | Pause and resume downloads at controlled points | State transitions and filesystem observations recorded |
| CH-04 | File visibility | Inspect whether the file is readable in the normal Downloads location during each state | The first time the file becomes accessible is established |
| CH-05 | Interrupted/resumed | Interrupt and resume benign downloads | No incorrect state or premature completion assumption |
| CH-06 | Cancelled download | Cancel at different stages | Cancellation and partial-file cleanup behaviour recorded |
| CH-07 | Repetition/race | Repeat tests across small and larger benign files | Consistency and race conditions documented |

**Critical interpretation:** A paused download state, a suggested filename, or an event callback is not by itself proof of quarantine. The acceptance criterion for a pre-release protection claim is observed, repeatable prevention of user access before the decision. If this cannot be demonstrated, the implementation and dissertation must use the user-selected completed-file workflow and state its narrower protection boundary.

Record Chrome version, operating system, extension version, permissions, test file size and hash, timestamps, destination path, and screenshots/logs. Do not use live malware for this experiment.

## 3. Input validation and PE parsing

| ID | Test input | Expected behaviour |
|---|---|---|
| PE-01 | Valid supported benign PE | Parse and produce the documented feature schema |
| PE-02 | Non-PE file renamed `.exe` | Reject as unsupported/invalid; do not classify as safe |
| PE-03 | Truncated PE | Return controlled parse error |
| PE-04 | Malformed header or invalid offsets | Reject safely without crash or unbounded allocation |
| PE-05 | Empty file | Reject with clear validation result |
| PE-06 | File at configured size limit | Handle according to documented limit |
| PE-07 | File above size limit | Reject before expensive processing |
| PE-08 | Unsupported PE variant or architecture | Return explicit unsupported/inconclusive result |
| PE-09 | Missing optional PE fields | Apply documented missing-value behaviour |
| PE-10 | Repeated identical file | Produce deterministic features and result for fixed versions/configuration |

No submitted file should be executed as part of static parsing tests.

## 4. Feature extraction parity

The browser-side extractor and Python reference extractor must implement the same versioned feature specification.

- Define each feature's name, type, source field, bounds, missing-value handling, and transformation.
- Prepare an authorised set of benign PE files covering supported variations.
- Run both extractors on identical file bytes.
- Compare feature names, ordering, values, types, and missing-value representation.
- Define numeric tolerances before comparing floating-point values.
- Investigate every mismatch; do not silently discard inconvenient cases.

**Minimum evidence:** feature schema document, test corpus manifest containing hashes (not malware binaries), machine-readable comparison output, mismatch analysis, and automated parity tests.

## 5. Local classifier evaluation

Use a documented, authorised dataset. Before training, record:

- Dataset name/version, source, access date, licence/terms, permitted research use, labels, and known limitations.
- File counts by class and any exclusions.
- Hash-based duplicate detection and, where feasible, near-duplicate checks.
- Train/validation/test split method and random seed.
- Any family, source, time, or collection grouping used to reduce leakage.

Establish a simple baseline first. Candidate models should be compared only when justified by the data and project time.

Report at minimum:

- Confusion matrix.
- Precision, recall, and F1-score.
- False-positive rate and false-negative rate.
- ROC-AUC or PR-AUC where appropriate.
- Threshold-selection method.
- Inference time and resource use.
- Error analysis, including representative false positives and false negatives.

Use validation data for model and threshold selection. Keep the final test set held out until the evaluation protocol is frozen. Do not claim zero-day detection from a random split or a high test score alone.

## 6. Local inference and robustness

| ID | Test | Evidence |
|---|---|---|
| ML-01 | Valid feature vector | Expected prediction schema and model version |
| ML-02 | Missing or extra feature | Controlled validation error |
| ML-03 | Wrong feature order/schema version | Rejection or explicit schema conversion |
| ML-04 | Low-confidence result | Marked inconclusive according to validation-defined policy |
| ML-05 | Repeated inference | Deterministic output for fixed model and input |
| ML-06 | Large supported file | Processing time and memory measured |
| ML-07 | Parser/model failure | No crash into a misleading safe state |

## 7. Consent-gated server escalation (if implemented)

| ID | Test | Expected behaviour |
|---|---|---|
| SRV-01 | User declines escalation | No file content is transmitted |
| SRV-02 | User explicitly consents | Only the selected file is sent to the configured endpoint |
| SRV-03 | Server unavailable | Clear error; preserve local result and do not label file safe |
| SRV-04 | Request timeout | Controlled timeout and cleanup |
| SRV-05 | Oversized/malformed request | Rejected within defined limits |
| SRV-06 | Unauthorised request | Rejected |
| SRV-07 | Server result | Display source, model/version, and uncertainty |
| SRV-08 | Retention/deletion | Verify documented temporary-file retention and cleanup |

Capture network evidence showing that declining consent results in no file upload. Do not send research files to an unapproved third-party service.

## 8. End-to-end and usability tests

Test the supported user journey from file selection to local result, including:

- Supported benign PE.
- Invalid or unsupported file.
- Local inconclusive result.
- User declines escalation.
- User consents and server returns a result (if implemented).
- Server unavailable or times out (if implemented).

The interface must distinguish analysis failure, inconclusive assessment, and a positive or negative classifier output. It must not promise that a file has been blocked or quarantined unless the relevant browser behaviour has passed the staging feasibility gate.

## 9. Experimental controls and reproducibility

- Record software versions, operating system, hardware, model version, configuration, and random seeds.
- Freeze feature definitions and evaluation protocol before final testing.
- Keep training, validation, and test sets separate.
- Check for duplicate and near-duplicate files across splits.
- Do not tune repeatedly against the held-out test set.
- Store scripts, configuration, sanitised metrics, and test manifests where licensing permits.
- Record negative results and deviations from the plan.

## 10. Safety, privacy, and repository hygiene

- Use benign files for browser workflow tests.
- Use only authorised datasets and follow their handling requirements.
- Do not execute malware samples on a personal or production device.
- Do not commit malware binaries, confidential files, credentials, tokens, or raw logs containing personal data.
- Keep server upload off by default and require explicit per-file consent.
- Avoid logging file contents; retain only the minimum metadata needed for reproducibility.
- Verify temporary-file cleanup and document retention.

## 11. Results reporting

Store sanitised experiment outputs under `results/`. Each experiment record should include:

- Test or experiment ID and date.
- Research question/objective addressed.
- Environment and software versions.
- Dataset/test input manifest and hashes where permitted.
- Procedure and configuration.
- Actual outcome, metrics, and evidence location.
- Failures, deviations, and limitations.

A test is complete only when the procedure has been run and its evidence reviewed. A planned test, code stub, or screenshot of an interface is not proof of detection performance or secure quarantine.
