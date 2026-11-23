# 0004 — Training size under the 8 GB laptop limit

- **Date:** 2026-11-24
- **Status:** Proposed. **Awaiting supervisor approval.** Objective O2 is unchanged until approved.

**Context.**
- The development laptop has 8 GB RAM (Intel i7-6600U, 2 cores / 4 threads).
- thrember's `read_vectorized_features` and `train_model` load the full matrix into memory, and `train_model` uses a
  random 10% validation split (source, commit 0ef753e).
- Weeks 1–40 hold an estimated 1.8 million PE rows. A synthetic cloud sweep suggests that training on all of them
  is unlikely to fit in memory (estimate; see [`../feasibility-audit.md`](../feasibility-audit.md)).

**Proposed decision.**
1. Train with LightGBM's streamed `Sequence` interface from the memory-mapped `X_train.dat`, using
   `bin_construct_sample_cnt=20000`, `force_col_wise=true`, 2 threads and the reference categorical features
   `2,3,4,5,6,701,702`.
2. Choose the training size *n* only from laptop measurements on real EMBER2024 vectors (feasibility Test 10).
   Take the largest size that keeps at least 1,000 MB available with no page-file growth, then about 75% of it.
3. Draw the *n* rows from training weeks 1–40 only: stratified by week, keeping the within-week class mix,
   excluding unlabelled rows, with a recorded seed. Use the same rows for the server and the local model.
4. Keep the validation (41–46), calibration (47–52) and test (53–64) weeks complete. Score them in batches. Fix the
   number of rounds by batch-scoring validation at several iteration counts, unless an in-training validation
   Dataset fits in the measured memory.
5. Report *n*, the sampling rule, the seed and the memory CSV. If time allows, add a second-size sensitivity run.

**Alternative needing approval.** Train the server model on all training weeks on other hardware (university or
cloud), keeping the same split and protocol.

**Consequences.**
- Detection figures describe models trained under a laptop budget. They are not like-for-like with published
  EMBER2024 baselines.
- The routing comparison stays internally valid, because all strategies share the same models and the complete
  test weeks.
