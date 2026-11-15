# SENTINELPE Proposed System Architecture

> **Status: design proposal, not implemented.** The components and data flows below are hypotheses to validate. The repository must not describe a proposed feature as working until code and test evidence exist.

## 1. Purpose and scope

SENTINELPE investigates a local-first browser-based workflow for static malware assessment of Windows Portable Executable (PE) files, initially `.exe` and `.dll`.

The intended sequence is:

1. A supported PE file is selected through a browser workflow that has been experimentally verified.
2. The browser-side component validates the input and extracts a defined set of static PE features.
3. A lightweight local classifier produces an initial assessment.
4. Only when the local result is uncertain, the user may explicitly consent to sending the selected file to a server-side classifier.
5. The result is returned with its source (local or server), confidence/uncertainty information, and limitations.

This is a research prototype, not a replacement for antivirus software and not a guarantee that a file is safe.

## 2. Scope boundaries

### In scope

- Static inspection of supported Windows PE files.
- A Chrome Manifest V3 user interface and tested file-selection/download integration.
- Browser-side feature extraction and local inference.
- Optional server-side classification after explicit consent.
- A Python reference pipeline for dataset preparation, feature extraction, training, and evaluation.
- Measurable evaluation of detection quality, feature consistency, latency, and workflow reliability.

### Out of scope

- Running or executing submitted files.
- Dynamic or behavioural analysis.
- An execution sandbox or virtual-machine detonation pipeline.
- URL reputation, phishing detection, and archive scanning.
- Automatic upload of files to remote services.
- Claiming that Chrome extension APIs provide guaranteed pre-release quarantine without experimental proof.

## 3. Logical components

### 3.1 Chrome extension (Manifest V3)

Responsibilities:

- Provide a user-facing entry point for supported PE analysis.
- Observe only the download events required by the selected workflow.
- Offer explicit file selection when the download lifecycle cannot safely provide pre-release staging.
- Display validation, analysis, consent, and result states.
- Never represent an observed or paused download as quarantined unless filesystem tests demonstrate that guarantee.

The extension should request the minimum permissions required. Download interception and file-content access are separate concerns: access to download metadata does not automatically provide read access to the downloaded file's bytes.

### 3.2 Input validation and PE feature extraction

Responsibilities:

- Enforce supported file types and a configurable maximum file size.
- Validate PE structure rather than trusting the filename or MIME type.
- Reject or safely handle truncated, malformed, and unsupported inputs.
- Extract a documented, bounded feature vector from PE headers and selected structural metadata.
- Avoid executing the submitted file.
- Return structured errors for invalid input.

The feature specification must define field names, data types, missing-value handling, bounds, and versioning. Browser and reference implementations must be tested for feature-level agreement on the same benign and authorised test files.

### 3.3 Local classifier

Responsibilities:

- Load a versioned model compatible with browser execution.
- Apply exactly the feature ordering and preprocessing expected by the model.
- Return a class/score and a calibrated or otherwise clearly described confidence measure.
- Apply a threshold selected using validation data.
- Mark out-of-distribution, malformed, or low-confidence inputs as inconclusive rather than forcing a safe/malicious label.

A model score is not proof of file safety. The initial implementation should compare a simple baseline before adding model complexity.

### 3.4 Optional server-side classifier

This component is conditional on feasibility and demonstrated research value.

Responsibilities:

- Accept a file only after the user has explicitly consented to that particular transfer.
- Enforce authentication or an equivalent access-control mechanism, request-size limits, input validation, and timeouts.
- Apply a documented server-side feature/model pipeline.
- Return a structured result with model/version metadata and an explicit indication that the assessment came from the server.
- Apply a defined retention policy and avoid storing file contents or sensitive metadata longer than necessary.

The user must be able to decline escalation. No file should be transmitted silently or automatically merely because the local classifier is uncertain.

### 3.5 Python research and evaluation pipeline

Responsibilities:

- Record dataset provenance, licence/terms, labels, and known limitations.
- Deduplicate and split data before model tuning.
- Extract the same documented features used by the browser implementation, where feasible.
- Train baseline and candidate models.
- Export model artefacts and preprocessing metadata in a versioned format.
- Produce reproducible metrics and error analysis.

## 4. Proposed data flow

1. The user starts analysis from the extension or chooses a supported file through the explicitly tested workflow.
2. The extension obtains access to the selected file through a supported user-mediated browser mechanism.
3. Input validation checks size, file structure, and supported PE type.
4. The browser-side extractor generates the versioned feature vector.
5. The local classifier produces an assessment.
6. If the assessment is inconclusive under the validation-defined policy, the extension explains the uncertainty and offers optional server analysis.
7. If the user declines, the local result and its uncertainty are shown; no upload occurs.
8. If the user consents, the selected file is sent to the configured API over a protected connection, subject to the deployment model and documented controls.
9. The server returns a structured result; the extension labels it as a server assessment.
10. Temporary data is removed according to the documented retention policy.

The browser download lifecycle may not permit steps 1–2 to happen before the file reaches the normal download location. That is a separate feasibility question, not an assumption embedded in this data flow.

## 5. Chrome download staging feasibility gate

This is the highest-priority technical risk and must be resolved before describing the product as a pre-release download protection system.

The Chrome downloads API exposes download lifecycle events and controls such as pause, resume, cancel, and filename suggestion. These controls must not be conflated with guaranteed interception of file bytes or guaranteed isolation from the user's normal Downloads directory.

### Minimal experiment

Use a disposable Chrome profile and benign test files only.

1. Record the Chrome version, operating system, extension manifest, and requested permissions.
2. Implement a minimal Manifest V3 extension that records relevant download events and state transitions with timestamps.
3. Test `onCreated`, `onChanged`, `onDeterminingFilename` (where applicable), pause, resume, and cancel independently.
4. During each test, inspect the actual filesystem and verify when the file first becomes readable in the normal download location.
5. Repeat for small and larger benign files, interrupted/resumed downloads, duplicate names, and user cancellation.
6. Record event logs, file paths, timestamps, and any race conditions.
7. Do not use malware samples or claim quarantine from API state alone.

### Decision rule

- **Pass:** only if repeated tests demonstrate that the chosen workflow prevents user access to the file until the analysis decision, with a clearly defined and reproducible mechanism.
- **Fail:** if the file becomes accessible before the decision, or the mechanism is unreliable.
- **Inconclusive:** if the experiment cannot establish the filesystem visibility boundary.

If the result is fail or inconclusive, use an explicit user-selected completed-file analysis workflow for the prototype and revise all claims accordingly. Do not build the project around an unverified quarantine guarantee.

## 6. Trust boundaries and controls

| Boundary | Risk | Planned control |
|---|---|---|
| Download/file selection to extension | Wrong file, spoofed extension, malformed input | Structural PE validation, size limits, user-visible selected filename |
| Extension to local inference | Unexpected feature shape or parser failure | Versioned schema, bounded parser, safe error states |
| Extension to server | Unconsented disclosure or local request abuse | Explicit per-file consent, protected transport, authentication/access control, strict CORS/origin policy |
| API to classifier | Resource exhaustion or malformed request | Request limits, timeouts, validation, bounded processing |
| Dataset to training pipeline | Label noise, duplicates, leakage, licence violation | Provenance records, deduplication, split controls, licence review |
| Model to user interface | False reassurance or misleading score | Clear uncertainty, model/version display, no absolute safety claim |
| Repository/build pipeline | Secret or sample leakage | Ignore rules, secret scanning, no malware samples or credentials in Git |

## 7. Data handling and privacy

Document before implementation:

- Supported PE types and maximum file size.
- Exact feature fields extracted locally.
- Whether raw file bytes ever leave the user's device.
- The user-consent wording and the exact trigger for server transfer.
- Server destination, access controls, retention period, and deletion behaviour.
- Log fields, redaction, and whether hashes or metadata are retained.
- Dataset source, licence, permitted use, and retention.

The default design should keep initial feature extraction and inference local. Server escalation is optional and must be user-authorised.

## 8. Failure states

The extension should distinguish at least:

- Unsupported file type.
- Invalid or malformed PE.
- File exceeds configured size limit.
- Local feature extraction failed.
- Local result is inconclusive.
- User declined server escalation.
- Server unavailable or request timed out.
- Server result returned.
- Analysis completed with a documented limitation.

A failure to analyse must never be presented as a clean or safe result.

## 9. Architecture decision records

Record consequential choices under `docs/decisions/`, including:

- Chrome file-access and download workflow.
- Supported PE feature set and schema version.
- Local model format and inference runtime.
- Local uncertainty threshold and escalation policy.
- Whether server escalation is retained in the final scope.

Each record should include context, options, evidence, decision, trade-offs, and date.
