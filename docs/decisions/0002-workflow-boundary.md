# 0002 — User-selected file analysis as the primary workflow

- **Date:** 2026-11-24
- **Status:** Accepted (supervisor-approved)

**Context.** The proposal refers to protection before or during file handling. The Chrome downloads API can delay a download's completion but returns no file contents.

**Decision.** The deliverable workflow analyses a file the user selects in an extension page (File API). Pre-release interception is a time-boxed feasibility experiment, adopted only if the file is shown to be inaccessible until a decision and the analysed bytes equal the delivered bytes.

**Consequences.** No quarantine claim unless demonstrated; reports state the protection boundary actually tested.
