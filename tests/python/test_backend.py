import hashlib
import os

import pytest

pytest.importorskip("thrember")
from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

TOKEN = "test-token"


def benign_pe() -> bytes:
    import pip._vendor.distlib as d                       # MIT-licensed launcher shipped with pip; never executed
    return open(os.path.join(os.path.dirname(d.__file__), "t64.exe"), "rb").read()


@pytest.fixture(scope="module")
def models(tmp_path_factory):
    from sentinelpe_ml.devmodels import make_dev_models
    out = tmp_path_factory.mktemp("dev")
    make_dev_models(str(out), n=4000, rounds=10)
    return str(out / "server_model")


def client(models, **kw):
    s = Settings(model_prefix=models, api_token=kw.pop("api_token", TOKEN), **kw)
    return TestClient(create_app(s))


def h(data, token=TOKEN):
    return {"Authorization": f"Bearer {token}", "X-Content-SHA256": hashlib.sha256(data).hexdigest()}


def test_refuses_to_start_without_auth(models):
    with pytest.raises(RuntimeError):
        create_app(Settings(model_prefix=models, api_token=""))


def test_analysis_and_rejections(models):
    pe = benign_pe()
    with client(models) as c:
        assert c.get("/v1/health").json()["model_version"].startswith("DEV-SYNTHETIC")
        r = c.post("/v1/analyze", content=pe, headers=h(pe))
        assert r.status_code == 200
        j = r.json()
        assert j["schema"] == "sentinelpe.analysis/1" and j["sha256"] == hashlib.sha256(pe).hexdigest()
        assert j["verdict"] in ("benign", "malicious") and len(j["attributions"]) == 10
        assert c.post("/v1/analyze", content=pe, headers=h(pe, "wrong")).status_code == 401
        assert c.post("/v1/analyze", content=pe, headers={**h(pe), "X-Content-SHA256": "0" * 64}).status_code == 409
        assert c.post("/v1/analyze", content=pe, headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 400
        notpe = b"\x00" * 5000
        assert c.post("/v1/analyze", content=notpe, headers=h(notpe)).status_code == 422
        garbage = b"MZ" + os.urandom(9000)
        assert c.post("/v1/analyze", content=garbage, headers=h(garbage)).status_code == 422


def test_size_limit(models):
    pe = benign_pe()
    with client(models, max_bytes=len(pe) - 1) as c:
        assert c.post("/v1/analyze", content=pe, headers=h(pe)).status_code == 413


def test_extraction_timeout_returns_504_and_recovers(models):
    pe = benign_pe()
    with client(models, extract_timeout_s=0.001) as c:
        assert c.post("/v1/analyze", content=pe, headers=h(pe)).status_code == 504
        assert c.post("/v1/analyze", content=pe, headers=h(pe)).status_code == 504   # pool rebuilt, still answers
