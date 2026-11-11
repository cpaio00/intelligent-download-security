# Intelligent Download Security

An AI-assisted browser download security system that investigates potentially malicious downloads using staged handling, isolated analysis, and machine-learning-assisted risk assessment.

> **Project status:** Research and development — early planning stage. The architecture and components described here are proposed; they are not claims of completed implementation or validated detection performance.

## Overview

Browser downloads are a common way users encounter malicious files. File extensions, reputation checks, signatures, and conventional antivirus products are useful controls, but no single method can identify every suspicious or previously unseen file.

This Final Year Project (FYP) explores a layered approach to download security. The proposed system will investigate whether a browser extension, a controlled analysis service, an isolated execution environment, and machine-learning-assisted classification can work together to provide useful risk assessments before a user chooses to access a downloaded file.

The project is being developed independently as an undergraduate cybersecurity FYP at Asia Pacific University of Technology & Innovation (APU), Malaysia.

## Problem statement

Users may open files before they understand their origin or risk. Static indicators can be incomplete, file reputation may be unavailable, and machine-learning models can produce false positives and false negatives. A useful download-security workflow therefore needs more than a single model prediction: it needs controlled file handling, multiple analysis signals, clear decisions, and measurable evaluation.

## Aim

Design, implement, and evaluate a prototype that assesses downloaded files through a controlled workflow and communicates an understandable risk result to the user.

## Proposed objectives

1. Investigate browser extension capabilities and limitations for observing and controlling download workflows.
2. Design a secure staging and analysis workflow that avoids treating untrusted files as safe by default.
3. Implement an isolated analysis component with clearly defined resource and network restrictions.
4. Evaluate suitable static and, where feasible, behavioural analysis features.
5. Establish a reproducible machine-learning pipeline and compare it with appropriate non-ML baselines.
6. Evaluate detection quality, false-positive behaviour, processing time, and operational limitations.
7. Document the design, experiments, limitations, and lessons learned for possible future open-source collaboration.

## Proposed architecture

The following components are planned and subject to revision after feasibility testing:

- **Browser extension:** User interface and download-workflow integration using Chrome Manifest V3.
- **Staging / orchestration service:** Coordinates file metadata, analysis requests, and result delivery.
- **Analysis worker:** Performs controlled static inspection and coordinates sandbox execution where appropriate.
- **Isolation layer:** Restricts the analysis environment's access to host resources and external networks.
- **Detection and scoring:** Combines defined analysis signals and, if justified by evaluation, a machine-learning model.
- **User feedback:** Presents a risk assessment with supporting reasons and safe next steps.

See docs/architecture.md for the proposed components, data flow, trust boundaries, and early feasibility questions.

### Important feasibility question

A browser extension's download APIs may not guarantee that every download can be held before any bytes are written to the user's normal download location. This must be tested early. The project will not claim pre-release quarantine until the selected browser workflow demonstrates that behaviour reliably. If required, the design may use a controlled staging workflow or another explicitly documented mechanism.

## Research questions

- **RQ1:** To what extent can a browser-integrated workflow safely stage and inspect downloaded files before user access?
- **RQ2:** How does a layered detection approach compare with selected static-analysis and baseline methods on the chosen evaluation dataset?
- **RQ3:** What trade-offs arise between detection performance, false positives, analysis latency, and resource consumption?
- **RQ4:** How effectively can the system communicate the evidence behind a risk assessment?

These questions may be refined with the project supervisor and after the literature review.

## Evaluation plan

The prototype will be evaluated using a documented dataset and reproducible test procedure. Depending on dataset suitability and the final scope, measurements may include:

- Precision, recall, F1-score, and confusion matrix
- False-positive rate and false-negative rate
- ROC-AUC or PR-AUC where appropriate
- Analysis time and resource consumption
- Robustness to missing, malformed, or unsupported file inputs
- Workflow reliability and usability observations

Dataset provenance, licensing, class balance, train/test separation, and possible data leakage will be documented. No zero-day detection claim will be made without a defensible experimental design.

## Technology direction

| Area | Initial direction |
|---|---|
| Browser integration | Chrome Extension, Manifest V3 |
| Backend | Python |
| API layer | To be selected after the architecture prototype |
| Isolation | Dedicated disposable analysis environment |
| Machine learning | To be selected after baseline experiments |
| Testing | Automated tests and controlled security test cases |
| Documentation | Markdown and reproducible experiment records |

Technology choices may change based on feasibility, security, and evaluation results.

## Repository structure

- extension/ — browser extension (planned)
- backend/ — API and orchestration service (planned)
- sandbox/ — isolated analysis components (planned)
- ml/ — data processing, models, and evaluation (planned)
- tests/ — automated and integration tests
- docs/research/ — literature review and research notes
- docs/architecture.md — proposed architecture
- docs/roadmap.md — development roadmap
- docs/testing-plan.md — testing and evaluation plan
- results/ — sanitised experiment outputs only

## Development roadmap

The initial roadmap is maintained in docs/roadmap.md. The project is expected to progress through literature review, feasibility testing, architecture, implementation, controlled evaluation, and final documentation.

## Safe research practices

- Do not commit malware samples, live payloads, credentials, private keys, access tokens, or personal data.
- Do not run untrusted files on a personal or university production machine.
- Use authorised datasets and controlled, disposable analysis environments.
- Keep sandbox networking disabled by default unless a specific experiment requires otherwise and has been safely authorised.
- Record dataset sources, licences, hashes, and handling procedures where appropriate.
- Treat all model outputs as uncertain assessments, not proof that a file is safe.
- Do not upload confidential or restricted files to third-party analysis services.

## Current status

At this stage, this repository contains project planning and documentation. No functioning extension, backend, sandbox, or trained detection model is claimed to exist yet. Progress and completed tests will be recorded as they are implemented and verified.

## Licence

The project currently uses the MIT License. Review ownership, university rules, and any third-party dataset or dependency licences before distributing implementation code or research materials.
