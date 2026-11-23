"""Export a local model for the browser: dump_model() JSON plus the metadata the extension needs."""
import json


def export_browser(booster, meta: dict, out_dir: str):
    """Writes local_model.json and local_model.meta.json. The extension refuses a model without thresholds."""
    import os
    if meta.get("role") != "local":
        raise ValueError("only a local model is exported to the browser")
    if booster.num_feature() != len(meta["columns"]):
        raise ValueError("model feature count does not match metadata columns")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "local_model.json"), "w") as f:
        json.dump(booster.dump_model(), f, separators=(",", ":"))
    keep = ("schema_version", "model_version", "columns", "n_input_features", "lightgbm_version", "thresholds")
    with open(os.path.join(out_dir, "local_model.meta.json"), "w") as f:
        json.dump({k: meta[k] for k in keep}, f, indent=1, allow_nan=False)
