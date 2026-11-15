# SENTINELPE: Local-First Browser-Based Static PE Malware Detection

A Final Year Project (FYP) investigating a local-first browser-integrated system for static malware detection of Windows Portable Executable (PE) files.

> **Project status:** Research and feasibility stage. The repository currently contains planning documentation only. No functioning extension, feature extractor, classifier, server escalation service, or evaluated model is claimed to exist.

## 1. Project overview

Windows PE files, particularly executable files such as `.exe` and `.dll`, can carry malicious code. Users may download and open these files without having enough information to assess their risk. This project investigates whether a browser-based workflow can provide an initial local static assessment and, when the local result is uncertain and the user consents, request a stronger assessment from a separate server-side classifier.

The design is **local-first**: the initial assessment is intended to run locally in the browser environment. File contents should not be sent to a remote service automatically. Any server-side escalation must be explicit, explained to the user, and limited to the file selected for analysis.

The project is being developed as an undergraduate cybersecurity FYP at Asia Pacific University of Technology & Innovation (APU), Malaysia. The implementation and evaluation scope must remain achievable within the October 2026–May 2027 project period.

## 2. Problem statement

Many users lack accessible, understandable information about the risk of downloaded Windows executable files. Conventional file reputation and signature-based approaches may not provide a useful assessment for every file, while server-side analysis can raise privacy and data-handling concerns. A local-first approach may reduce unnecessary file disclosure, but it introduces technical challenges: extracting consistent PE features in a browser, maintaining acceptable analysis performance, and deciding when local confidence is insufficient.

A further challenge is the browser download lifecycle. Chrome extension APIs must be tested before the project claims that a download can be held in quarantine before becoming accessible to the user. The system must not promise prevention or pre-release protection unless that behaviour is demonstrated experimentally.

## 3. Aim

To design, implement, and evaluate a local-first browser-based prototype for static malware detection of supported Windows PE files, with optional consent-based escalation to a server-side classifier when the local assessment is inconclusive.

## 4. Proposed objectives

1. Review recent research on static PE malware detection, browser-based security, lightweight machine-learning inference, and privacy-aware analysis.
2. Design a Chrome Manifest V3 extension workflow for supported PE files and investigate the practical limits of download interception and staging.
3. Implement a bounded PE feature-extraction process and a lightweight local classifier for an initial risk assessment.
4. Implement an optional, consent-based mechanism for escalating uncertain cases to a server-side classifier, with clear file-transfer and privacy information.
5. Evaluate feature-extraction consistency, classification performance, false-positive behaviour, processing time, and workflow reliability using documented and authorised data.
6. Compare the proposed approach with simple baselines and report limitations without making unsupported zero-day or prevention claims.

These objectives are provisional until confirmed against the supervisor-approved proposal and final assessment requirements.

## 5. Scope and exclusions

### Included

- Windows Portable Executable (PE) files within the explicitly supported test scope, initially `.exe` and `.dll`.
- Static analysis of PE metadata and selected structural features.
- A browser extension prototype using Chrome Manifest V3.
- A lightweight local feature extraction and classification path.
- Optional server-side classification only after an explicit user decision.
- Evaluation using authorised datasets and benign test files.
- User-facing results that communicate confidence, limitations, and next steps.

### Excluded from the current FYP scope

- Dynamic execution of submitted files.
- Behavioural malware analysis and execution sandboxes.
- URL reputation or phishing detection.
- Archive extraction and recursive archive scanning.
- A claim that all downloads are securely quarantined before they reach the normal Downloads folder.
- Automatic upload of downloaded files to a remote service.
- Production-grade antivirus replacement or guaranteed malware prevention.

Any proposed scope change requires supervisor agreement and a documented rationale.

## 6. Proposed system workflow

1. The extension identifies a supported PE file in the tested browser workflow or the user explicitly selects a file for analysis.
2. The system validates the file type and size and extracts the defined static PE features.
3. The local classifier returns a result and confidence or uncertainty measure.
4. If the local result meets the defined decision threshold, the extension presents the local assessment and its limitations.
5. If the result is uncertain, the user may explicitly consent to sending the file to the configured server-side classifier. Declining must remain possible.
6. The server returns a structured assessment; the extension presents it separately from the local result.
7. Temporary data is removed according to the documented retention policy.

**Important:** The exact download-handling sequence depends on the Chrome feasibility experiment. Until pre-release staging is demonstrated, the safe baseline workflow is user-initiated analysis of a completed or otherwise accessible file. The project will describe the actual tested protection boundary, not imply that a browser event listener is equivalent to quarantine.

## 7. Research questions

- **RQ1:** To what extent can a Chrome Manifest V3 extension support a reliable and privacy-conscious workflow for analysing downloaded Windows PE files?
- **RQ2:** How accurately can selected static PE features support lightweight local malware classification compared with simple baselines?
- **RQ3:** What performance and privacy trade-offs arise when uncertain local assessments are optionally escalated to a server-side classifier?
- **RQ4:** How consistent are the PE features extracted by the browser-side implementation and the reference feature-extraction pipeline?

## 8. Evaluation approach

The evaluation will use authorised datasets and a reproducible methodology. The exact dataset, feature set, model, thresholds, and split strategy must be recorded before final testing.

Candidate measures include:

- Confusion matrix, precision, recall, F1-score, false-positive rate, and false-negative rate.
- ROC-AUC or PR-AUC where appropriate for the dataset and class distribution.
- Browser-side feature-extraction agreement against a reference implementation.
- Local inference time and, where applicable, server response time.
- File-size limits, memory use, failure rate, and behaviour for malformed or unsupported inputs.
- User-consent and file-transfer workflow correctness.

Dataset provenance, licence and permitted use, label definitions, duplicates, class balance, and train/validation/test separation must be documented. Avoid leakage between splits. Do not claim zero-day detection unless a separate, defensible temporal or family-held-out evaluation supports that claim.

## 9. Technology direction

| Area | Initial direction |
|---|---|
| Browser integration | Chrome Extension, Manifest V3 |
| Local feature extraction | JavaScript/TypeScript; exact implementation to be selected |
| Local inference | Lightweight model suitable for browser execution |
| Server-side classifier | Python service, optional and consent-gated |
| PE reference processing | Documented Python tooling |
| Testing | Unit, feature-parity, integration, and controlled evaluation tests |
| Documentation | Markdown, experiment records, and architecture decisions |

Technology choices remain provisional until feasibility and baseline experiments are completed.

## 10. Repository structure

- `extension/` — Manifest V3 extension and browser-side workflow.
- `backend/` — optional server-side classification API.
- `ml/` — dataset preparation, reference feature extraction, training, and evaluation.
- `tests/` — unit, integration, parity, and workflow tests.
- `docs/research/` — literature review and research notes.
- `docs/architecture.md` — proposed architecture and trust boundaries.
- `docs/roadmap.md` — October 2026–May 2027 development roadmap.
- `docs/testing-plan.md` — test strategy and evaluation criteria.
- `docs/decisions/` — architecture decision records.
- `results/` — sanitised metrics and experiment notes only.

Legacy `sandbox/` material, if present, is not part of the current implementation scope.

## 11. Safe research and privacy practices

- Do not commit malware samples, credentials, access tokens, private keys, or personal data.
- Do not execute untrusted files on a personal or university production machine.
- Use datasets only where their licence and terms permit the intended research use.
- Keep server escalation disabled unless the user explicitly consents to the specific transfer.
- Explain what data is sent, where it is processed, and how long it is retained.
- Do not store full file contents in application logs.
- Treat classifier output as an uncertain assessment, not proof that a file is safe or malicious.
- Record failed experiments and limitations as well as successful results.

## 12. Current status

The current branch is a documentation realignment. The default branch's initial repository setup contained planning files and workspace placeholders. This documentation does not claim that the extension, PE parser, local classifier, server API, or tests have been implemented. Implementation status must be updated only when code and reproducible evidence exist.

## Licence

The repository currently uses the MIT License. Confirm university ownership requirements and review third-party code, dataset, and dependency licences before redistribution.
