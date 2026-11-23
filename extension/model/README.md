# Local model

The extension loads `local_model.json` and `local_model.meta.json` from this folder. They are generated, not committed:

- Development (synthetic, meaningless results): `python -m sentinelpe_ml make-dev-models --out ../dev_models`, then
  copy `../dev_models/browser/*` here.
- Real model: `python -m sentinelpe_ml export-browser --model <local model prefix> --out extension/model`.

Without these files every analysis is UNSCANNED.
