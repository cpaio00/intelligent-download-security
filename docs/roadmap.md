# SENTINELPE Development Roadmap

> Project period: October 2026 – May 2027. This is a working plan, not evidence that any milestone has been completed. Confirm exact submission and supervisor milestones before treating dates as fixed.

## Scope guardrails

The current FYP is a local-first browser-based system for static Windows PE malware detection, initially supporting `.exe` and `.dll`. The intended design is a lightweight local assessment with optional, explicit user-consented escalation to a server-side classifier.

Out of scope unless the supervisor formally approves a change: dynamic execution, behavioural analysis, execution sandboxing, URL detection, archive scanning, automatic remote file upload, and guaranteed pre-release download quarantine.

## Phase 1 — Research and approved scope (October–November 2026)

- [ ] Confirm the approved title, problem statement, aim, objectives, and research questions with the supervisor.
- [ ] Complete a focused literature review of recent static PE malware detection, browser-based security, lightweight inference, and privacy-aware analysis.
- [ ] Select and document the candidate dataset(s), permitted use, provenance, labels, limitations, and licensing.
- [ ] Define the supported PE file scope, threat model, privacy boundary, and explicit exclusions.
- [ ] Select simple baseline methods and define the evaluation metrics.
- [ ] Create a literature comparison matrix and identify the specific research gap addressed by this prototype.

**Exit evidence:** Supervisor-aligned scope; cited literature matrix; dataset feasibility note; written threat model; baseline and metric definitions.

## Phase 2 — Browser and feature feasibility (November–December 2026)

- [ ] Create a minimal Manifest V3 extension that observes the relevant download lifecycle events.
- [ ] Test the exact Chrome download API behaviour using benign files: event ordering, pause/resume, cancellation, filename handling, and filesystem visibility.
- [ ] Determine whether any tested workflow genuinely prevents access to the file before analysis. Record the limits; do not infer quarantine from a paused state.
- [ ] Define a safe fallback workflow based on explicit user selection of a completed file if pre-release staging cannot be demonstrated.
- [ ] Select a bounded PE feature set and implement a small reference extractor.
- [ ] Test whether the selected features can be extracted reliably in the browser environment and compare results with the reference extractor.

**Exit evidence:** Reproducible browser feasibility report; chosen workflow and documented protection boundary; feature specification; initial feature-parity results.

## Phase 3 — Local prototype (December 2026–January 2027)

- [ ] Implement supported-file validation, size limits, and safe error handling.
- [ ] Implement browser-side PE feature extraction for the selected feature set.
- [ ] Establish a simple local baseline classifier before introducing a more complex model.
- [ ] Implement the extension UI for file selection/workflow state and local assessment.
- [ ] Add unit tests for malformed, truncated, unsupported, and boundary-size inputs.
- [ ] Record local processing time and resource use on the available development hardware.

**Exit evidence:** Demonstrable local-only prototype for the supported test cases; automated feature and validation tests; reproducible baseline results.

## Phase 4 — Optional server escalation and model evaluation (February–March 2027)

- [ ] Decide, based on local results and feasibility, whether a server-side classifier adds measurable value.
- [ ] If retained, implement a minimal API with strict input limits, authentication or equivalent access control, and explicit user consent before file transfer.
- [ ] Explain the data transfer, destination, and retention to the user; provide a decline path.
- [ ] Train and compare only justified candidate models using documented splits and leakage checks.
- [ ] Define the local uncertainty/escalation rule using validation data, not the held-out test set.
- [ ] Test agreement and differences between local and server-side feature extraction where applicable.
- [ ] Measure detection metrics, latency, and resource costs; record limitations and negative results.

**Exit evidence:** Reproducible model/baseline comparison; tested consent-gated escalation if implemented; documented privacy and performance results.

## Phase 5 — Integration and controlled evaluation (April 2027)

- [ ] Run end-to-end tests for every supported workflow.
- [ ] Test user decline, server unavailable, timeout, malformed file, unsupported file, and oversized file cases.
- [ ] Freeze the evaluation protocol before running the final held-out test.
- [ ] Report confusion matrix, precision, recall, F1, false-positive and false-negative rates, and relevant latency measurements.
- [ ] Review false positives and false negatives without silently changing the test protocol.
- [ ] Capture genuine screenshots, logs, test records, and sanitised results.
- [ ] Review privacy, security, dependencies, and repository hygiene.

**Exit evidence:** Frozen evaluation protocol; end-to-end test record; final metrics and error analysis; reproducible artefacts.

## Phase 6 — Dissertation and submission (May 2027)

- [ ] Complete methodology, design, implementation, evaluation, discussion, limitations, and conclusion chapters.
- [ ] Ensure every implementation and result claim is supported by code, test evidence, or a cited source.
- [ ] Check consistency between proposal, objectives, repository, dissertation, and demonstration.
- [ ] Prepare the final demonstration and submission artefacts.
- [ ] Confirm supervisor feedback and official submission requirements.

**Exit evidence:** Submission-ready dissertation and demonstrable prototype, subject to university requirements.

## Weekly execution rule

At each weekly review, report (1) merged or committed code, (2) experiments actually run and their evidence, (3) documentation changes, (4) blockers, and (5) the next three priorities. A planned task is not complete until its exit evidence exists. Record failed experiments; do not hide them.

## Critical path

1. Confirm the supervisor-approved scope.
2. Resolve Chrome download workflow feasibility and choose the honest fallback if needed.
3. Prove browser-side feature extraction can match a reference implementation.
4. Establish a baseline and reproducible evaluation before adding complexity.
5. Add optional server escalation only if it is feasible, privacy-conscious, and contributes measurable value.
