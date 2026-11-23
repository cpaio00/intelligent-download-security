# Feasibility kit (exploratory)

> **Status: feasibility tooling, not the SentinelPE implementation.** These scripts were produced with AI
> assistance during the feasibility study (November 2026). They check whether the planned approach can work on the
> development laptop. They are not the deliverable extractor, models, extension or server. Nothing here is a
> project result.

| File or folder | Purpose |
|---|---|
| `RUN_ON_LAPTOP.md` | Step-by-step Windows instructions (Tests 1–10) |
| `CHANGES.md` | Audit of the defects found in kit v1 and how each was fixed and re-tested |
| `CLOUD_REFERENCE_RESULTS.md` | Every number measured in the cloud workspace, with its script, configuration and method. **These are not laptop measurements** |
| `equivalence/` | LightGBM `dump_model()` JSON evaluator in JavaScript, plus an equivalence suite (numeric, categorical, missing, zero, boundary, default-left/right, 50–500 trees) |
| `memory/` | Training-memory sweep with a safety stop (private memory, available memory, page file, timings, CSV) |
| `corpus_tools/` | Rebuilds the benign parity corpus from pinned, licensed PyPI wheels (SHA-256 checked) and makes malformed variants |
| `parity/` | Per-group parity of the exploratory JS extractor against thrember, using the pre-declared ULP rule |
| `proto_js/` | Exploratory JS feature extractor: 1,024 of 2,568 dims attempted, 768 passing. **Not parity-approved** |
| `compact/`, `server/`, `checks/`, `browser_test/`, `tools/` | Model size and speed, FastAPI + SHAP benchmark, hashing, extraction speed, routing cost, browser worker test |

Safety rules:
- Only benign files are used.
- No PE file is ever executed.
- Synthetic data (`make_synth.py`) is for memory and speed only. Its accuracy means nothing.

Generated files are ignored by git: corpus, variants, large test files, `.npy` and `.dat` matrices, models, and
local results. **Do not commit them.**

Not yet tested:
- anything on Windows
- real Google Chrome
- a Chrome extension
- real EMBER2024 data (`tools/make_week_index.py` is UNTESTED on it)
