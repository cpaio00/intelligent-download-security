# Testing and Evaluation Plan

> This is an initial plan. Test cases, datasets, thresholds, and acceptance criteria must be finalised after the scope and implementation are confirmed.

## 1. Functional tests

| Area | Example test | Evidence |
|---|---|---|
| Download events | New, cancelled, interrupted, and resumed downloads | Event logs and expected state transitions |
| Staging | Confirm file is not exposed prematurely in the normal download location | Controlled filesystem observation |
| API | Valid, malformed, unauthorised, and oversized requests | HTTP responses and service logs |
| File validation | Mismatched extension, MIME type, empty file, and unsupported type | Validation result |
| Worker | Timeout, crash, and resource-limit conditions | Job state and cleanup record |
| Sandbox | Host-path access and network restrictions | Isolation test results |
| UI | Pending, suspicious, inconclusive, and failed analysis | Screenshots and manual test record |

## 2. Detection evaluation

Use a documented dataset whose use is permitted by its licence and terms. Record the source, collection date, label definitions, hashes where appropriate, and known limitations.

Report at minimum:
- Confusion matrix
- Precision
- Recall
- F1-score
- False-positive rate
- False-negative rate
- Analysis latency

Use ROC-AUC or PR-AUC when the dataset and evaluation design make them meaningful. Explain class imbalance and threshold selection.

## 3. Experimental controls

- Separate training, validation, and test data before model tuning.
- Check for duplicate files and near-duplicates across splits.
- Avoid leakage from file names, source folders, timestamps, or dataset-specific artefacts.
- Compare the model with simple baselines.
- Keep a record of software versions, configuration, random seeds, and hardware.
- Do not use the test set repeatedly to tune the model.
- Report uncertainty and limitations rather than selecting only favourable results.

## 4. Performance and reliability

Measure processing time by file size and type, CPU and memory use, service failures, timeout rate, and cleanup success. Include unsupported formats and interrupted workflows.

## 5. Safety

Use benign test files and authorised datasets. Do not execute live malware on a personal or production system. Any behavioural testing must occur in a disposable, isolated environment with controlled networking and a documented safety procedure.

## 6. Results reporting

Store sanitised metrics, plots, and experiment notes under results/. Do not commit malware samples, confidential files, personal data, or raw logs containing sensitive information.
