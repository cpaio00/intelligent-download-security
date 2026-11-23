# SentinelPE Proposed System Architecture

> **Status: design proposal, not implemented.** The components and data flows below are the planned design. Nothing here is claimed to work until code and test evidence exist.

## 1. Purpose

SentinelPE is a local-first browser-based prototype for static malware detection of Windows PE files (`.exe`, `.dll`). A compact local classifier decides most files on the user's device; files in an uncertain band are offered for escalation to a stronger server-side classifier, and are sent only after explicit per-file consent. It is a research prototype, not a replacement for antivirus software, and no verdict proves that a file is safe.

## 2. Components

### 2.1 Chrome extension (Manifest V3)

- Provides an extension page in which the user selects a PE file. The page reads the file through the File API, which lets web content read files the user selects with a file input or by drag and drop.
- Runs validation, feature extraction, local inference, the consent prompt and result display.
- Persists analysis state, because Chrome terminates an extension service worker after 30 seconds of inactivity, when one event or API call takes longer than five minutes, or when a fetch response takes longer than 30 seconds.
- Requests the minimum permissions required.

The Chrome downloads API reports download events, and `onDeterminingFilename` delays completion until every listener has answered, but no method of the API returns a downloaded file's contents. Holding a download is therefore not the same as being able to analyse it (see Section 5).

### 2.2 Input validation and feature extraction

- Validates PE structure rather than trusting the filename or MIME type, and enforces a size limit.
- Extracts only the EMBER2024 feature groups that pass the parity test (O1).
- A file that fails PE validation, or a required feature group that cannot be computed for that file, produces **UNSCANNED**. (The reference extractor still emits a vector when its PE parser fails; SentinelPE deliberately does not.)
- Computes the file's SHA-256 digest so that a server reply can be matched to the exact bytes analysed.

### 2.3 Local classifier

- A compact LightGBM model trained only on parity-verified feature groups.
- Proposed deployment: export with LightGBM `dump_model()` (a JSON description of the trees) and evaluate with a JavaScript tree evaluator. Equivalence with Python predictions, including categorical splits and missing values, must be shown on identical EMBER2024 vectors, and the exported file size measured.
- Output: the **uncalibrated predicted probability *s***.

### 2.4 Routing

| Concept | Meaning in SentinelPE |
|---|---|
| Classifier score | *s*, LightGBM's predicted probability before calibration |
| Uncertainty measure | Whether *s* lies between the lower and upper thresholds |
| Routing decision | *s* ≤ lower → local benign; *s* ≥ upper → local malicious; otherwise offer escalation |
| Calibrated probability | Platt or isotonic mapping of *s*, used only to show interpretable confidence to the user |

Thresholds are fitted on the calibration weeks and then kept fixed. Because Platt scaling is strictly monotonic (order-preserving when its fitted slope is positive in *s*, checked after fitting) and isotonic regression is non-decreasing (it can create ties), calibration cannot enlarge the set of routing outcomes achievable with two thresholds on *s*. Routing therefore uses *s* directly.

### 2.5 Server (FastAPI)

- Accepts a file only after consent for that file; authenticates requests; enforces size limits; checks the PE signature; parses in a resource- and time-limited process; never executes uploads; deletes temporary files after analysis; does not log file contents.
- Classifies with a full-feature LightGBM model.
- Returns verdict, model version, SHAP attributions (LightGBM feature contributions) and the SHA-256 digest of the analysed bytes.
- Attributions explain how features moved the model's output; they do not show that the prediction is correct or what the program would do when run.

### 2.6 Python research pipeline

Data audit, reference feature extraction (thrember), training of the server and local models, calibration, threshold fitting and the offline routing evaluation, all with recorded versions and seeds.

## 3. Data flow

| Situation | What stays on the device | What leaves the device | Result |
|---|---|---|---|
| *s* outside the band | File and features | Nothing | Local verdict |
| *s* inside the band, user declines | File and features | Nothing | UNSCANNED (local result inconclusive) |
| *s* inside the band, user consents | — | File bytes, SHA-256 digest, and the request metadata any web request reveals (e.g. IP address, time). The filename is not sent | Server verdict and attributions |
| Server unavailable, timeout, invalid reply or digest mismatch | — | As above, if already sent | UNSCANNED |
| Any analysis failure | — | — | UNSCANNED |

Local-first processing reduces, but does not remove, the transfer of file contents.

## 4. Failure states

Each of the following ends in **UNSCANNED**, never in a benign verdict:

- Unsupported file type or non-PE input.
- Invalid, truncated or malformed PE.
- File exceeds the size limit.
- Local feature extraction failed.
- Local result inconclusive and the user declined escalation.
- Server unavailable or request timed out.
- Server reply invalid or digest mismatch.
- Service-worker termination interrupted the analysis.

## 5. Chrome download-interception feasibility gate

The primary workflow is user-selected file analysis (supervisor-approved). Pre-release interception is investigated in a two-week experiment with benign files and a disposable browser profile, recording the event sequence, the effect of delaying filename determination, pause, resume and cancel, when the file becomes readable in the Downloads folder, service-worker restarts and behaviour under repeated and concurrent downloads.

- **Adopt** pre-release analysis only if repeated tests show that the file is inaccessible until a decision is made and that the analysed bytes equal the delivered bytes.
- **Otherwise** the user-selected workflow remains the only workflow, and reports describe the protection boundary actually tested.

## 6. Trust boundaries

| Boundary | Risk | Planned control |
|---|---|---|
| File selection → extension | Malformed or non-PE input | Structural validation, size limit, UNSCANNED on failure |
| Extension → local inference | Feature mismatch with training | Parity-verified groups only; evaluator equivalence test |
| Extension → server | Unconsented disclosure | Per-file consent; nothing sent on decline |
| Server reply → extension | Wrong or tampered reply | Schema validation and digest match, else UNSCANNED |
| API → classifier | Resource exhaustion | Limits, timeouts, isolated parsing |
| Dataset → training | Leakage across time | Chronological split audited from metadata; test weeks used once |
| Model → user | False reassurance | No absolute safety claim; calibrated confidence shown |
| Repository | Sample or secret leakage | No malware, credentials or file contents committed |

## 7. Decision records

See [`docs/decisions/`](decisions/).
