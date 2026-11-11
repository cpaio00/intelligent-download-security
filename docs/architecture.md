# Proposed System Architecture

> Status: design proposal. Components and flows below must be validated during implementation.

## 1. Design principles

- Treat downloaded content as untrusted until an explicit decision is made.
- Separate the browser interface from file analysis.
- Keep analysis isolated from the host and restrict network access.
- Use deterministic baselines before adding machine learning.
- Preserve evidence for decisions and communicate uncertainty.
- Prefer reproducible experiments and least-privilege components.

## 2. High-level components

### Browser extension

A Chrome Manifest V3 extension will provide the user-facing interface and integrate with supported browser download events. It should display the download state, analysis progress, and final assessment.

**Feasibility gate:** Confirm the exact guarantees of the Chrome downloads APIs. In particular, establish whether the extension can reliably prevent a file from becoming available in the normal download location before analysis completes. Do not assume that observing or pausing a download is equivalent to pre-save quarantine.

### Staging and orchestration service

A local service may receive a file or a controlled reference to it, assign an analysis job identifier, enforce size and type limits, and coordinate the worker. Authentication and access controls are required even for a localhost service.

### Analysis worker

The worker performs bounded static inspection, records metadata, and requests sandbox analysis only when appropriate. It must validate inputs, impose time and resource limits, and avoid trusting file names or declared MIME types.

### Isolation environment

The sandbox should be disposable and separated from the host. The design should consider filesystem isolation, process restrictions, memory and CPU limits, network policy, snapshot/revert capability, and safe disposal of artefacts.

### Detection and decision layer

The decision layer may combine static indicators, sandbox observations, reputation information (if permitted), and a machine-learning score. It must distinguish observed evidence from model inference. A model score alone must not be treated as a guarantee of safety.

### User interface

The extension should communicate states such as pending, analysing, suspicious, malicious (only when supported by defined evidence), inconclusive, and completed. The UI should explain why a result was produced and avoid implying certainty where none exists.

## 3. Proposed data flow

1. The browser reports a download event to the extension.
2. The extension applies the verified download-handling mechanism.
3. A staged file or controlled file reference is passed to the local orchestration service.
4. The service validates the request and creates an analysis job.
5. The worker performs static checks and, if enabled, submits the file to the isolated environment.
6. Analysis results are normalised and passed to the decision layer.
7. The service returns a result and supporting evidence to the extension.
8. The user receives the result and an appropriate next action.
9. Temporary files and sandbox state are cleaned up according to the retention policy.

The precise ordering of steps 2 and 3 depends on the browser feasibility test. If safe pre-release staging cannot be guaranteed, the product description and threat model must be adjusted rather than overstating the protection.

## 4. Trust boundaries

| Boundary | Main concern | Required control |
|---|---|---|
| Browser to local service | Unauthorised local requests | Local binding, request authentication, origin validation, strict input validation |
| Service to worker | Malformed jobs or resource exhaustion | Schema validation, queue limits, timeouts, least privilege |
| Worker to sandbox | Escape or host compromise | Disposable isolation, restricted mounts, no host credentials |
| Sandbox to network | Malware communication or lateral movement | Network disabled by default; tightly controlled test network when authorised |
| Analysis result to UI | Misleading or tampered results | Structured schema, provenance, explicit uncertainty |
| Repository and build pipeline | Secret or sample leakage | Secret scanning, ignore rules, dependency review, no live samples in Git |

## 5. Threats and abuse cases to consider

- Malformed files designed to crash parsers or exhaust resources
- Archive bombs and deeply nested archives
- Files that misrepresent their type or extension
- Time-delayed or environment-aware malicious behaviour
- Sandbox escape attempts
- Localhost request abuse and cross-origin requests
- Race conditions in the browser download workflow
- False positives that block legitimate files
- False negatives that incorrectly reassure users
- Leakage of confidential files through external analysis services

## 6. Data handling

The implementation should define:
- Maximum file size and supported file types
- Temporary storage location and access permissions
- Retention and secure deletion rules
- Whether file contents ever leave the local machine
- Logging fields and redaction rules
- Dataset provenance and licence records

Avoid storing full file contents in logs. Use hashes and minimal metadata where sufficient.

## 7. Early technical proof-of-concept tests

1. Verify the browser event lifecycle and available control points for downloads.
2. Measure whether a file can be staged without being exposed in the normal download directory.
3. Test interrupted, resumed, duplicate, and cancelled downloads.
4. Test large files, archives, unsupported formats, and network failures.
5. Demonstrate that the analysis worker cannot access sensitive host paths.
6. Demonstrate that the sandbox is disposable and cannot access the host's credentials.
7. Verify cleanup after success, failure, timeout, and service restart.

## 8. Architecture decision records

Important choices should be recorded in short decision records under docs/decisions/, including context, options considered, decision, trade-offs, and date. This will make the research and implementation rationale auditable.
