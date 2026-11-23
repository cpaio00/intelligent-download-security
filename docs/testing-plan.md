# SentinelPE Testing and Evaluation Plan

> **Status: proposed protocol.** No test here has been run. Record environment, outputs, failures and evidence before marking a test complete.

## 1. Evidence types

Each objective produces a different kind of evidence, and each supports only its own claim.

| Objective | Evidence | Cannot show |
|---|---|---|
| O1 | Extraction parity between JavaScript and thrember | Anything about detection |
| O2 | Detection on labelled EMBER2024 records | Browser correctness, except for groups that passed O1 |
| O3 | Correct workflow, consent and failure handling | Detection performance |
| O4 | Recall–upload trade-off, random and oracle comparisons, prototype latency | Performance outside the EMBER2024 test period or under real-world prevalence |

## 2. Chrome feasibility (benign files, disposable profile)

| ID | Test | Acceptance |
|---|---|---|
| CH-01 | Event sequence with timestamps | Recorded and repeatable |
| CH-02 | Delaying filename determination | Outcome recorded |
| CH-03 | Pause, resume, cancel | State and filesystem observations recorded |
| CH-04 | When the file becomes readable in Downloads | Established for each state |
| CH-05 | Analysed bytes vs delivered bytes | Digests compared |
| CH-06 | Service-worker restart; concurrent downloads | Behaviour recorded |

Pre-release analysis is adopted only if the file is inaccessible until a decision and the analysed bytes equal the delivered bytes, repeatably. Otherwise the user-selected workflow is the only workflow.

## 3. Input validation

| ID | Input | Expected |
|---|---|---|
| PE-01 | Valid benign PE | Features extracted |
| PE-02 | Non-PE renamed `.exe` | UNSCANNED |
| PE-03 | Truncated PE | UNSCANNED, no crash |
| PE-04 | Invalid offsets or headers | UNSCANNED, bounded memory |
| PE-05 | Empty file | UNSCANNED |
| PE-06 | Above size limit | UNSCANNED before parsing |
| PE-07 | Same file twice | Identical features and result |

No file is ever executed.

## 4. Feature parity (O1)

**Corpus:** benign files from clean Windows installations and licensed open-source builds; files built for the purpose (32-bit, 64-bit, .NET, signed, packed); systematically truncated and corrupted variants. Each recorded with SHA-256, source and licence. No malware binaries, so parity on unusual malicious structures is covered only indirectly (stated limitation).

**Rules (fixed before testing):**

| Feature type | Rule |
|---|---|
| Integer | Exact equality |
| Categorical | Exact equality of the encoded value |
| Floating point | Compared as 32-bit floats (the reference casts its final vector to float32). Differences reported in ULP; a group whose only differences are 1 ULP passes only if local-model predictions on the corpus are unchanged |
| Array / hashed | Length and order first, then element-wise; same hash function and sign convention as scikit-learn `FeatureHasher` |

A group that fails is excluded from the local model by design; an extraction failure on a particular file produces UNSCANNED.

**Expected difficulty (planning expectation, not a result):** byte-level groups (general, byte histogram, byte-entropy) most straightforward; strings depend on Python regex behaviour; header, section, data-directory, import, export and rich-header groups depend on pefile behaviour; Authenticode (signify) and PE-format warnings (pefile messages) expected to be impractical.

**Evidence:** corpus manifest (hashes, not binaries), machine-readable comparison output, mismatch analysis, automated tests.

## 5. Model-inference equivalence

| ID | Test | Acceptance |
|---|---|---|
| ML-01 | JavaScript evaluator vs Python on identical EMBER2024 vectors of both classes | Raw scores equal; any probability difference reported |
| ML-02 | Categorical splits and missing values | Covered by ML-01 vectors |
| ML-03 | Exported model size and browser load/inference time | Measured and reported |
| ML-04 | Wrong feature count or schema version | Rejected → UNSCANNED |

## 6. Data audit and split

- Week of each record = whole days between its first-submission timestamp and 2023-09-24, divided by seven (official weeks 0–63). This project numbers weeks from 1 (week *n* = official week *n* − 1).
- Confirm training-file records fall in weeks 0–51 and test-file records in 52–63; count labelled records per week and class, and unlabelled records (label −1).
- Proposed split: training 1–40, validation 41–46, calibration 47–52, test 53–64; used only if the audit confirms it.
- Test weeks are never used for training, feature selection, early stopping, calibration or thresholds. The reference `train_model` random 10% validation split is not used. The challenge set is reported separately.

## 7. Routing evaluation (O4)

**Definitions:** upload rate = escalated test files / test files; recall = malicious files classed malicious by the system / malicious files; realised false-positive rate = benign files classed malicious / benign files. The offline evaluation assumes consent for every escalation (the largest possible upload count).

**Operating points:** 1% false-positive rate (primary), 0.1% (secondary; weekly reporting at 0.1% only if the audited benign counts make it meaningful). Thresholds meet the operating point on calibration weeks; the realised test false-positive rate is reported with Wilson intervals.

**Strategies:**

1. Always Local — local model at its operating-point threshold.
2. Always Server — server model at its operating-point threshold.
3. Confidence Routing — for each budget in 5% steps, lower and upper thresholds chosen on calibration weeks to maximise recall with overall false-positive rate at or below the operating point.
4. Random Routing — escalates exactly the same number of test files as Confidence Routing, uniformly at random from the same test population; other files decided locally. Repeated with recorded seeds; mean and 2.5th/97.5th percentiles reported.
5. Oracle Routing — offline, non-deployable upper bound using true labels to escalate first the files the local model misclassifies and the server classifies correctly.

**Repetitions:** chosen before the test by a stability test on calibration-week scores (100, 200, 500, 1,000); the smallest number whose mean and percentiles change by less than a tolerance fixed in advance. The tolerance is recorded with the results.

**Superiority criterion (supervisor-approved):** Confidence Routing is better than Random Routing at an upload count only if its recall is higher, its realised false-positive rate is no higher, and a 95% week-level block-bootstrap interval for the recall difference lies above zero. The block bootstrap resamples the 12 test weeks with replacement as whole weeks a fixed number of times; matching upload counts alone does not establish superiority.

**Also reported:** per-week recall and false-positive rate for every strategy; margin δ (SD of Always-Server weekly recall on validation weeks) and the answer to SQ2.

## 8. Server and failure injection (O3)

| ID | Test | Expected |
|---|---|---|
| SRV-01 | User declines | No file content transmitted (network capture); UNSCANNED |
| SRV-02 | User consents | Only the selected file and its digest sent; filename not sent |
| SRV-03 | Server unavailable | UNSCANNED |
| SRV-04 | Timeout | UNSCANNED; cleanup |
| SRV-05 | Malformed or schema-invalid reply | UNSCANNED |
| SRV-06 | Digest mismatch | UNSCANNED |
| SRV-07 | Unauthorised or oversized request | Rejected by server |
| SRV-08 | Temporary-file cleanup | Files deleted after analysis |
| SRV-09 | Service-worker termination mid-analysis | UNSCANNED or resumed; never benign |

Completion: every defined failure state ends in UNSCANNED.

## 9. Latency (O4)

Measure local inference, end-to-end analysis time and server round-trip latency in the prototype, with hardware and browser versions recorded. Reported as measurements, not targets.

## 10. Reproducibility and hygiene

Record software versions, hardware, seeds and configuration; freeze the protocol before using the test weeks; record negative results and deviations; never commit malware, credentials or file contents.
