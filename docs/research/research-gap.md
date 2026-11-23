# Research Gap and Literature Notes

> Source of record: Investigation Report, Chapter 2 (Sections 2.2.2–2.2.5). The studies below were checked against their full texts. "Not reported" means absent from the publication as reviewed, not that the authors' system lacks it.

## Selected studies

- **Augello, De Paola & Lo Re (2025)**, *Journal of Network and Systems Management*, 33, Art. 36. Android; on-device permission-based random-forest pool with a self-evaluation agent; uncertain apps uploaded to a cloud sandbox. KronoDroid, chronological evaluation 2011–2018. Average F1 0.913 with 27.1% remote analyses; threshold baseline 0.891 at 38.8%; static-only 0.904; dynamic-only 0.843. A random policy was compared at an unmatched rate (49.9%). Latency estimated, energy not measured, calibration not evaluated; privacy mentioned briefly; consent not reported.
- **Nguyen et al. (2023)**, CAMLIS 2022, CEUR Workshop Proceedings Vol. 3391, pp. 81–99. EMBER2018; Bayesian MalConv and LightGBM with predictive entropy; uncertain files deferred to dynamic analysis (a sandbox operated by a third-party company), CAPA or a larger model; thresholds on validation data (November 2018), test on December 2018. Reject matches ensemble accuracy at 13.2% deferred; Defer exceeds it at 17.3%. No random baseline, no fixed-FPR results, calibration and consent not discussed.
- **Yumlembam, Issac & Jacob (2026)**, *Knowledge-Based Systems*, 331, 114723. EMBER (750,000 benign, 800,000 malware), BODMAS, UCSB; EMBER features; LightGBM calibrated with isotonic regression; ensemble uncertainty with inductive conformal evaluation; random 60/10/30 splits. Incorrect acceptances on UCSB reduced from 22.8% to 16%. No random baseline, no ECE/Brier, rejected samples' handling not evaluated, deployment and consent not discussed.

## Comparison

| Criterion | Augello 2025 | Nguyen 2023 | Yumlembam 2026 | SentinelPE (proposed) |
|---|---|---|---|---|
| Windows PE | No (Android) | Yes | Yes | Yes |
| Browser feature extraction | Outside scope | Not reported | Not reported | Planned (O1) |
| Local inference | On-device design | Not reported | Not reported | Planned |
| Escalation of uncertain cases | Yes, cloud sandbox | Yes, costlier analysis | Rejection only | Yes, with consent |
| Consent before file transfer | Not reported | Not reported | Not reported | Planned |
| Detection metric | F1 | Accuracy, AUC | Acceptance rates, F1 | Recall at fixed FPR |
| Chronological evaluation | Yes | Yes, one split | No | Yes, by week |
| Random-escalation baseline | Yes, unmatched rate | Not reported | Not reported | Planned, matched counts |
| Failure-safe behaviour | Not reported | Not reported | Not reported | Planned |

## Gap (within the literature reviewed)

- **Technical:** no reviewed PE study recomputes its feature set in a browser and verifies it against the extractor used for training.
- **Methodological:** escalation has been measured against compute or latency cost, with F1 or accuracy; no reviewed study compares confidence-based and random escalation at matched upload rates and a fixed false-positive operating point.
- **Practical:** users can rely on reputation warnings or, in Chrome's Enhanced protection, choose to send suspicious files to Google; a local-first, consent-gated, inspectable PE option has not been evaluated in terms of uploads and retained detection.

LightGBM, SHAP, browser extensions and confidence-based deferral are existing techniques. The contribution claimed is the evaluated integration and its measured behaviour; the review does not establish that no comparable PE system exists.

## Other works noted

Soliman et al. (2024), Stirewalt et al. (2026), Gálvez et al. (2021) and the preprint Massidda et al. (2026) — see Investigation Report Section 2.2.3. Stirewalt figures used are those confirmed from the paper body on 23 November 2026; the publisher abstract reports different figures.
