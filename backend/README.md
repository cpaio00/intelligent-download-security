# backend/ — analysis server (FastAPI)

> **Status: initial implementation, tested only with a synthetic dev model** (`tests/python/test_backend.py`,
> `tests/e2e`). No TLS, rate limiting or deployment hardening yet.

```
python -m pip install -r requirements.txt
python -m pip install "thrember @ git+https://github.com/FutureComputing4AI/EMBER2024@0ef753e81d98bf209f71b03cd331dfc190b5b54d"
set SENTINELPE_MODEL=..\dev_models\server_model
set SENTINELPE_API_TOKEN=choose-a-long-random-token
python -m uvicorn app.asgi:app --host 127.0.0.1 --port 8000
```

| Endpoint | Behaviour |
|---|---|
| `GET /v1/health` | Model version, schema version, size limit |
| `POST /v1/analyze` | Body: raw file bytes. Headers: `Authorization: Bearer <token>`, `X-Content-SHA256`. Returns the verdict at the operating point, score, model version, the SHA-256 of the analysed bytes, and the top TreeSHAP attributions |

Refusals:
- 401: bad token
- 400: no digest
- 409: digest mismatch
- 413: over `SENTINELPE_MAX_BYTES` (default 50 MB), rejected before the body is read
- 422: not PE, or malformed
- 504: extraction timeout

The extension shows **UNSCANNED** for every refusal.

How files are handled:
- Extraction runs thrember in a separate worker process. That process has a time limit (`SENTINELPE_EXTRACT_TIMEOUT_S`) and, on Linux, a memory limit (`SENTINELPE_WORKER_MEMORY_MB`). If it hangs, it is killed and replaced.
- Files are kept in memory only. They are never written to disk, logged or executed.

The server refuses to start without a token, unless `SENTINELPE_ALLOW_NO_AUTH=1` is set (local development only).
