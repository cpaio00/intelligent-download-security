# 0003 — Criterion for confidence vs random routing

- **Date:** 2026-11-24
- **Status:** Accepted (supervisor-approved); the stability tolerance is to be fixed before the test

**Decision.**
1. Random Routing escalates exactly the number of test files that Confidence Routing escalated, from the same test population, repeated with recorded seeds.
2. The number of repetitions is chosen by a stability test (100, 200, 500, 1,000) on calibration-week scores against a tolerance fixed in advance.
3. Confidence Routing is better at an upload count only if its recall is higher, its realised false-positive rate is no higher, and a 95% week-level block-bootstrap interval for the recall difference lies above zero.

**Consequences.** Matching upload counts alone does not establish superiority; with 12 test weeks the interval will be wide and the criterion conservative.
