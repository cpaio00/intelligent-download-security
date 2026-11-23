"""SentinelPE analysis API.

POST /v1/analyze  body: raw file bytes; headers: Authorization: Bearer <token>, X-Content-SHA256: <hex>
GET  /v1/health

Every refusal is an HTTP error; the extension shows UNSCANNED for any non-200 reply, timeout or invalid reply.
File contents are never logged, stored or executed."""
import asyncio
import hashlib
import hmac
import json
import threading
from contextlib import asynccontextmanager

import lightgbm as lgb
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .extraction import ExtractionError, Extractor

RESPONSE_SCHEMA = "sentinelpe.analysis/1"
GROUPS = [("general", 7), ("histogram", 256), ("byteentropy", 256), ("strings", 177), ("header", 74),
          ("section", 224), ("imports", 1282), ("exports", 129), ("datadirectories", 34), ("richheader", 33),
          ("authenticode", 8), ("pefilewarnings", 88)]


def feature_name(i: int) -> str:
    for g, n in GROUPS:
        if i < n:
            return f"{g}[{i}]"
        i -= n
    return f"unknown[{i}]"


class Analyzer:
    def __init__(self, s: Settings):
        self.s = s
        self.booster = lgb.Booster(model_file=s.model_prefix + ".txt")
        with open(s.model_prefix + ".meta.json") as f:
            self.meta = json.load(f)
        if self.meta.get("role") != "server" or self.booster.num_feature() != 2568:
            raise RuntimeError("SENTINELPE_MODEL must be a 2,568-feature server model")
        th = self.meta.get("thresholds", {}).get(s.operating_point)
        if not th:
            raise RuntimeError(f"model metadata has no threshold for operating point {s.operating_point}")
        self.threshold = float(th["decision"])
        self.extractor = Extractor(s.extract_timeout_s, s.worker_memory_mb)
        self.lock = threading.Lock()          # one extraction at a time per server process (bounded memory)

    def analyse(self, data: bytes) -> dict:
        with self.lock:
            v = self.extractor.extract(data)
        if v.shape != (2568,) or v[2] != 1:   # general.is_pe flag from thrember
            raise ExtractionError("not_pe")
        x = v.reshape(1, -1).astype(np.float64)
        score = float(self.booster.predict(x)[0])
        contrib = self.booster.predict(x, pred_contrib=True)[0]
        top = np.argsort(-np.abs(contrib[:-1]))[: self.s.top_k]
        return {"score": score, "verdict": "malicious" if score >= self.threshold else "benign",
                "attributions": [{"feature_index": int(i), "feature": feature_name(int(i)), "contribution": float(contrib[i])} for i in top],
                "expected_value": float(contrib[-1])}


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings()
    if not s.api_token and not s.allow_no_auth:
        raise RuntimeError("set SENTINELPE_API_TOKEN (or SENTINELPE_ALLOW_NO_AUTH=1 for local development only)")

    @asynccontextmanager
    async def lifespan(app):
        app.state.analyzer = Analyzer(s)
        yield
        app.state.analyzer.extractor.close()

    app = FastAPI(title="SentinelPE analysis server", version="0.1.0", lifespan=lifespan)
    if s.allowed_origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(s.allowed_origins), allow_methods=["POST", "GET"],
                           allow_headers=["Authorization", "X-Content-SHA256", "Content-Type"])

    def check_auth(request: Request):
        if not s.api_token:
            return
        got = request.headers.get("authorization", "")
        if not hmac.compare_digest(got, f"Bearer {s.api_token}"):
            raise HTTPException(401, "unauthorised")

    @app.get("/v1/health")
    async def health(request: Request):
        a = request.app.state.analyzer
        return {"status": "ok", "model_version": a.meta["model_version"], "schema_version": a.meta["schema_version"],
                "max_bytes": s.max_bytes}

    @app.post("/v1/analyze")
    async def analyze(request: Request):
        check_auth(request)
        declared = request.headers.get("x-content-sha256", "").lower()
        if len(declared) != 64 or any(c not in "0123456789abcdef" for c in declared):
            raise HTTPException(400, "missing or invalid X-Content-SHA256")
        cl = request.headers.get("content-length")
        if cl is not None and (not cl.isdigit() or int(cl) > s.max_bytes):
            raise HTTPException(413, "file too large")
        buf = bytearray()
        async for chunk in request.stream():            # also enforces the limit without Content-Length
            buf += chunk
            if len(buf) > s.max_bytes:
                raise HTTPException(413, "file too large")
        data = bytes(buf); digest = hashlib.sha256(data).hexdigest()
        if digest != declared:
            raise HTTPException(409, "digest mismatch")
        if len(data) < 64 or data[:2] != b"MZ":
            raise HTTPException(422, "not a PE file")
        a = request.app.state.analyzer
        try:
            r = await asyncio.to_thread(a.analyse, data)
        except ExtractionError as e:
            if e.kind == "timeout":
                raise HTTPException(504, "analysis timed out")
            raise HTTPException(422, "malformed PE" if e.kind == "not_pe" else "feature extraction failed")
        return {"schema": RESPONSE_SCHEMA, "sha256": digest, "model_version": a.meta["model_version"],
                "operating_point_fpr": float(s.operating_point), "threshold": a.threshold, **r,
                "note": "Attributions show how features moved the model output; they do not prove the file is safe or malicious."}

    return app
