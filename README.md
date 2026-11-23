# SentinelPE: A Local-First Browser-Based System for Static PE Malware Detection

A Final Year Project (FYP) at Asia Pacific University of Technology & Innovation (APU), Malaysia.

> **Project status:** investigation stage. This repository contains planning and design documentation and an exploratory **feasibility kit** ([`feasibility/`](feasibility/)). No extension, feature extractor, classifier, server or evaluation pipeline of SentinelPE has been implemented, and no experimental result is claimed. The kit's cloud measurements ([`docs/feasibility-audit.md`](docs/feasibility-audit.md)) are feasibility evidence, not project results, and none was taken on the development laptop. Status must be updated only when code and reproducible evidence exist.

## 1. Project overview

SentinelPE investigates whether a browser-compatible classifier can decide most Windows Portable Executable (PE) files locally and escalate only uncertain files to a stronger server-side classifier, with explicit user consent before any file leaves the device.

The proposed workflow:

1. The user selects a PE file (`.exe` or `.dll`) in a Chrome Manifest V3 extension page.
2. The extension validates the PE structure, computes the file's SHA-256 digest and extracts static features in JavaScript.
3. A compact LightGBM model produces an uncalibrated predicted probability *s*.
4. If *s* lies outside an escalation band defined by two thresholds, the verdict is returned locally.
5. If *s* lies inside the band, the user is asked whether that file may be sent to the server.
6. With consent, the FastAPI server classifies the file with a full-feature LightGBM model and returns a verdict, model version, SHAP attributions and the digest of the bytes it analysed.
7. If the user declines, or any step fails, the file is reported as **UNSCANNED** and is never presented as safe.

## 2. Problem statement

Users who download Windows executables lack an evaluated way to obtain a content-based static assessment that is computed mainly on their own device, that uploads a file only when the local result is uncertain and the user agrees, and that never presents a failed or skipped analysis as safe. Deployed browser and operating-system protections rely largely on reputation or vendor-side scanning. Research on escalation from cheap to expensive analysis has measured computational cost rather than file disclosure, and the reviewed PE classifiers operate on pre-extracted features without demonstrating that those features can be recomputed in a browser.

## 3. Aim

To design and evaluate a local-first browser-based prototype that detects malicious Windows PE files through static analysis, using browser-verified features and a compact local classifier, escalates uncertain files to a server classifier only with explicit user consent, and measures the resulting trade-off between server uploads and malware detection.

## 4. Objectives

| ID | Objective | Completion criterion |
|---|---|---|
| O1 | Implement a JavaScript extractor for the EMBER2024 feature set and determine, for each of its twelve feature groups, whether it reproduces the reference Python extractor (thrember) on a documented corpus of benign and systematically malformed PE files, under agreement rules fixed before testing. | Every feature group classed as pass or fail, with mismatches documented. |
| O2 | Train, on chronological EMBER2024 splits, a full-feature server classifier and a compact local classifier restricted to the feature groups that pass O1, and measure their recall and false-positive rate, the local model's size and its browser inference latency. | Recall and realised false-positive rate reported for both models on the test weeks; size and latency measured. |
| O3 | Implement a Chrome MV3 extension and a FastAPI service with local classification, threshold-based escalation, explicit per-file consent and server-side SHAP explanations, and verify by failure-injection testing that every defined failure state produces UNSCANNED. | Every defined failure state ends in UNSCANNED; no upload occurs without consent. |
| O4 | Evaluate, on the held-out EMBER2024 test weeks, recall and realised false-positive rate as a function of upload rate for confidence-based routing against Always Local, Always Server, repeated random routing that escalates the same number of files, and Oracle Routing (non-deployable upper bound), and measure end-to-end and server round-trip latency in the prototype. | Curves and comparisons reported for all strategies, latency measured, and SQ2 answered positively or negatively. |

Quantities such as model size, latency and upload rate are measured and reported, not promised as targets.

### Mapping to the approved proposal

The approved proposal has five objectives; the APU Investigation Report guidelines allow at most four. The restructuring below was approved by the supervisor.

| Approved proposal objective | Addressed by |
|---|---|
| 1. Investigate static PE detection techniques, browser-based security approaches and their limitations | Chapter 2 of the Investigation Report |
| 2. Lightweight local model using browser-computable static features | O1, O2 |
| 3. Confidence-based routing between local and server classification | O3 (implementation), O4 (evaluation) |
| 4. Server-side analysis component with SHAP explanations | O2 (server model), O3 (FastAPI and SHAP) |
| 5. Evaluation of detection, false-positive rate, upload reduction, latency, temporal robustness and routing effectiveness | O2, O4 |

## 5. Research questions

**Main question:** At a fixed false-positive rate, how does malware recall vary with the proportion of files uploaded when a browser-compatible local PE classifier escalates its least-confident predictions to a server classifier, and does confidence-based escalation achieve higher recall than random escalation at the same upload rate?

- **SQ1 (O1):** Which EMBER2024 feature groups can be reproduced from raw PE bytes in browser JavaScript with exact agreement with the reference Python extractor?
- **SQ2 (O4):** What is the smallest upload rate at which the recall of confidence-based routing falls within a margin δ of Always-Server recall, where δ is the week-to-week standard deviation of Always-Server recall on the validation weeks?

The question remains answerable whatever the outcome: if no upload rate below 100% meets the margin, that is a finding, and the curves and the random-escalation comparison are still reported.

## 6. Scope

**Included:** static analysis of Windows PE files; feature-parity testing on benign and deliberately malformed files; server and local LightGBM models on EMBER2024; routing evaluation including an offline oracle upper bound; user-selected file analysis in a Chrome extension; per-file consent before upload; UNSCANNED on any failure; server-side SHAP attributions; technical experiments and document analysis.

**Excluded:** executing or detonating files; handling live malware binaries; dynamic or behavioural sandboxing; URL, archive and non-PE formats; automatic uploads; claims of zero-day or guaranteed detection; a claim of pre-release quarantine unless the feasibility test demonstrates it; explanations computed in the browser; surveys, interviews or other research with human participants.

**Workflow boundary (supervisor-approved):** the deliverable workflow analyses a file that the user selects after it has been downloaded. Interception of downloads before release is investigated as a feasibility question and adopted only if demonstrated. The Chrome downloads API provides no method that returns a downloaded file's contents.

## 7. Evaluation design (summary)

Full detail is in [`docs/testing-plan.md`](docs/testing-plan.md).

- **Dataset:** EMBER2024 PE subsets (Win32, Win64, .NET): 2,340,000 training and 540,000 test records, 2,568 features in 12 groups. EMBER2024 provides feature records and labels, not binaries. The PE zips total about 23.1 GB.
- **Training size:** the development laptop has 8 GB RAM, and full-data training is unlikely to fit (estimate). The training size will be measured on the laptop, not assumed. The proposed approach ([ADR 0004](docs/decisions/0004-training-size-and-memory.md)) awaits supervisor approval. Validation, calibration and test weeks stay complete.
- **Proposed split** (weeks numbered from 1; official weeks are 0–63): training 1–40, validation 41–46, calibration 47–52, test 53–64. Used only if a planned data audit confirms the per-week counts. The official `train_model` function's random 10% validation split is not used.
- **Operating points:** 1% false-positive rate (primary) and 0.1% (secondary). Thresholds are fixed on calibration weeks; the realised test false-positive rate is reported with Wilson intervals.
- **Strategies:** Always Local, Always Server, Confidence Routing, Random Routing (same number of escalated files, same test population, repeated with recorded seeds), Oracle Routing (non-deployable upper bound).
- **Superiority criterion (supervisor-approved):** Confidence Routing is better than Random Routing at an upload count only if its recall is higher, its realised false-positive rate is no higher, and a 95% week-level block-bootstrap interval for the recall difference lies above zero.

## 8. Technology

| Area | Choice | Status |
|---|---|---|
| Browser | Chrome, Manifest V3; File API for user-selected files | Proposed |
| Local features | JavaScript extractor, checked against thrember | Proposed |
| Local inference | LightGBM model exported with `dump_model()` (JSON) and evaluated in JavaScript; equivalence with Python predictions must be validated | Proposed; method checked on synthetic models only (feasibility kit) |
| Server | Python, FastAPI, LightGBM, SHAP via LightGBM feature contributions | Proposed |
| Reference pipeline | Python, thrember, scikit-learn | Proposed |

## 9. Repository structure

- `extension/` — Manifest V3 extension (not started).
- `backend/` — FastAPI server (not started).
- `ml/` — data audit, reference extraction, training and evaluation (not started).
- `tests/` — parity, unit, integration and failure-injection tests (not started).
- `docs/architecture.md` — proposed architecture, data flow and failure states.
- `docs/roadmap.md` — December 2026–May 2027 plan.
- `docs/testing-plan.md` — test and evaluation protocol.
- `docs/research/` — research gap and verified literature notes.
- `docs/decisions/` — decision records.
- `results/` — sanitised experiment outputs only.
- `feasibility/` — exploratory feasibility kit (AI-assisted, not the deliverable) with Windows instructions in `RUN_ON_LAPTOP.md`.
- `docs/feasibility-audit.md` — feasibility findings, each labelled with its evidence class.

## 10. Open decisions

- Assumed malware-prevalence values for an upload-rate sensitivity analysis (not yet decided).
- The tolerance for choosing the number of random-routing repetitions (fixed before the stability test).
- Consent as a formal core requirement, Chapter 3 without human participants, and the ethics-form declaration (supervisor confirmation pending).
- Training on a measured, week-stratified subset of weeks 1–40, or training the server model on other hardware ([ADR 0004](docs/decisions/0004-training-size-and-memory.md); supervisor approval pending).
- Local feature set: limited to groups that pass parity. The exploratory prototype gives 768 features at present, with byteentropy failing.
- Truncated files whose headers parse: accept them, as thrember does, or report UNSCANNED (test PE-03).
- Files the JS parser rejects but the server could analyse: UNSCANNED only, or UNSCANNED with an offer to upload.
- Early stopping: fixed rounds with batch-scored validation, or an in-training validation Dataset (more memory).
- Upload size limit: 50 MB was used in the feasibility benchmark, but the final limit is not yet confirmed.

## 11. Safe research practice

- Do not commit malware samples, credentials, tokens or personal data.
- Never execute submitted or test files.
- Use datasets only within their licence terms; record each dataset's licence before use.
- Keep uploads off by default and require explicit per-file consent.
- Do not log file contents.
- Treat every classifier output as uncertain evidence, not proof.
- Record failed experiments and limitations as well as successes.

## Licence

MIT License. Review university ownership requirements and third-party licences before redistribution.
