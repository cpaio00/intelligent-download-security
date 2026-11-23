# Minimal SentinelPE-style analysis server for BENCHMARKING ONLY (not the project implementation: no authentication,
# no TLS, no rate limiting). Binds to 127.0.0.1 via server_bench.py.
# Accepts raw PE bytes, enforces a size limit, validates PE, extracts thrember features, predicts, returns SHAP.
import hashlib, os, warnings, numpy as np, lightgbm as lgb
from fastapi import FastAPI, Request, HTTPException
from thrember.features import PEFeatureExtractor
warnings.filterwarnings('ignore')
MAX_BYTES = int(os.environ.get('MAX_BYTES', 50 * 1024 * 1024))
app = FastAPI(); FE = PEFeatureExtractor(); MODEL = lgb.Booster(model_file=os.environ.get('MODEL', 'full_model.txt'))
@app.post('/analyze')
async def analyze(request: Request):
    declared = request.headers.get('content-length')
    if declared and declared.isdigit() and int(declared) > MAX_BYTES: raise HTTPException(413, 'file too large')   # before reading the body
    body = await request.body()
    if len(body) > MAX_BYTES: raise HTTPException(413, 'file too large')
    if len(body) < 64 or body[:2] != b'MZ': raise HTTPException(422, 'not a PE file')
    if request.headers.get('x-sha256') and request.headers['x-sha256'].lower() != hashlib.sha256(body).hexdigest():
        raise HTTPException(409, 'digest mismatch')                      # client-declared SHA-256 must match received bytes
    try: vec = FE.feature_vector(body)
    except Exception as e: raise HTTPException(422, f'extraction failed: {type(e).__name__}')
    if vec[2] != 1: raise HTTPException(422, 'malformed PE')               # general.is_pe flag
    x = vec.reshape(1, -1).astype(np.float64)
    contrib = MODEL.predict(x, pred_contrib=True)[0]
    top = np.argsort(-np.abs(contrib[:-1]))[:10]
    return {'sha256': hashlib.sha256(body).hexdigest(), 'score': float(MODEL.predict(x)[0]),
            'top_features': [[int(i), float(contrib[i])] for i in top], 'expected_value': float(contrib[-1])}
