# SentinelPE Development Roadmap

> Working plan, not evidence of progress. A task is complete only when its exit evidence exists. Dates follow Table 6 of the Investigation Report; confirm them against the APU calendar.

## Scope guardrails

Local-first static detection of Windows PE files with consent-based escalation to a server classifier (core, per the approved proposal). Out of scope: execution or detonation, live malware binaries, behavioural sandboxing, URL/archive/non-PE formats, automatic uploads, human-participant research, and any pre-release quarantine claim not demonstrated by the feasibility gate.

## Phase 1 — Investigation (October–November 2026)

- [ ] Literature and document analysis; research gap (Investigation Report Chapter 2).
- [ ] Scope, requirements, data and evaluation design.
- [ ] Supervisor confirmation of open decisions (see README Section 10).

**Exit evidence:** Investigation Report.

## Phase 2 — Feasibility and data (December 2026)

- [ ] Chrome download-interception feasibility test, time-boxed to two weeks (architecture Section 5).
- [ ] Download EMBER2024 PE subsets; run the data audit (weeks from metadata, labelled counts per week and class, unlabelled records).
- [ ] Build the parity corpus manifest (benign and malformed files, with SHA-256, source and licence).
- [ ] Start the JavaScript feature extractor.

**Exit evidence:** feasibility report and workflow decision; audit tables confirming or revising the split.

## Phase 3 — Parity and server model (January 2027)

- [ ] Complete parity testing for all twelve feature groups (O1).
- [ ] Train the full-feature server model on weeks 1–40 with validation weeks 41–46.

**Exit evidence:** per-group pass/fail table with mismatch analysis; server model with validation results.

## Phase 4 — Local model and calibration (February 2027)

- [ ] Train the compact local model on passing groups (O2).
- [ ] Export with `dump_model()`; validate JavaScript evaluator against Python on identical vectors; measure file size and browser latency.
- [ ] Fit calibration and routing thresholds on calibration weeks 47–52; run the random-repetition stability test; freeze all settings.

**Exit evidence:** local model, equivalence results and measurements; frozen evaluation configuration.

## Phase 5 — Routing evaluation and prototype (March 2027)

- [ ] Run the offline routing evaluation on test weeks 53–64 once (O4).
- [ ] Build the extension and FastAPI server.

**Exit evidence:** recall–upload curves, confidence-vs-random comparison with bootstrap intervals, oracle bound, per-week results.

## Phase 6 — Integration and testing (April 2027)

- [ ] Consent flow, SHAP output and failure-injection tests (O3).
- [ ] Measure end-to-end and server round-trip latency (O4).

**Exit evidence:** failure-injection record (every state → UNSCANNED); latency measurements.

## Phase 7 — Report and submission (May 2027)

- [ ] Final report, limitations and demonstration.

## Critical path

1. Data audit confirms the split.
2. Parity testing decides the local feature set.
3. Models and frozen thresholds.
4. Offline routing evaluation (independent of the extension).
5. Prototype and failure-injection tests.
