# Development Roadmap

> Working plan for the FYP period (October 2026 – May 2027). Dates are indicative and must be reconciled with supervisor milestones and the official submission schedule.

## Phase 1 — Research and scope

- [ ] Confirm the project problem, aim, objectives, and research questions with the supervisor.
- [ ] Review recent research on browser download security, malware analysis, sandboxing, and ML-based detection.
- [ ] Identify candidate datasets and record provenance, licence, labels, and limitations.
- [ ] Define a realistic supported-file scope and threat model.
- [ ] Establish evaluation metrics and baseline methods.

**Exit criteria:** Approved scope, research gap, initial literature matrix, and evaluation plan.

## Phase 2 — Feasibility and architecture

- [ ] Build a minimal Manifest V3 experiment for download event handling.
- [ ] Verify whether the selected browser workflow can safely stage downloads before user access.
- [ ] Prototype communication between the extension and a local service.
- [ ] Demonstrate isolated file inspection with resource limits and safe cleanup.
- [ ] Document architecture decisions and security boundaries.

**Exit criteria:** Demonstrated end-to-end proof of concept or a documented redesign based on browser limitations.

## Phase 3 — Core implementation

- [ ] Implement extension UI and download state handling.
- [ ] Implement authenticated local orchestration API.
- [ ] Implement file validation and bounded static analysis.
- [ ] Implement sandbox job execution and result normalisation.
- [ ] Add structured logs, error handling, and cleanup.
- [ ] Add unit and integration tests.

**Exit criteria:** A reproducible prototype that completes the intended workflow for the explicitly supported test cases.

## Phase 4 — Detection and evaluation

- [ ] Establish simple, explainable baseline detection methods.
- [ ] Prepare a documented and appropriately licensed dataset.
- [ ] Split data to avoid leakage between training and test sets.
- [ ] Train and compare candidate models only where justified.
- [ ] Measure precision, recall, F1, false-positive rate, and analysis latency.
- [ ] Perform robustness tests on malformed and unsupported inputs.
- [ ] Record limitations and avoid unsupported zero-day claims.

**Exit criteria:** Reproducible results, baseline comparison, and an honest error analysis.

## Phase 5 — Finalisation

- [ ] Conduct end-to-end testing and fix critical defects.
- [ ] Review security controls and data handling.
- [ ] Prepare architecture, methodology, implementation, and evaluation documentation.
- [ ] Capture genuine screenshots and test evidence.
- [ ] Review code, dependency licences, and repository hygiene.
- [ ] Confirm supervisor requirements and submit the final dissertation and artefacts.

**Exit criteria:** Stable demonstration, complete documentation, and submission-ready FYP deliverables.

## Working rules

- Make small, meaningful commits that describe actual changes.
- Do not commit secrets, private data, or malware samples.
- Record failed experiments as well as successful ones.
- Do not report a feature as complete until it has been implemented and tested.
- Keep the research question and evaluation criteria ahead of unnecessary feature expansion.
