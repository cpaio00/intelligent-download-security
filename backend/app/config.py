"""Settings from environment variables (no secrets in code)."""
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    model_prefix: str = field(default_factory=lambda: os.environ.get("SENTINELPE_MODEL", "models/server_model"))
    operating_point: str = field(default_factory=lambda: os.environ.get("SENTINELPE_OPERATING_POINT", "0.01"))
    api_token: str = field(default_factory=lambda: os.environ.get("SENTINELPE_API_TOKEN", ""))
    allow_no_auth: bool = field(default_factory=lambda: os.environ.get("SENTINELPE_ALLOW_NO_AUTH") == "1")
    max_bytes: int = field(default_factory=lambda: int(os.environ.get("SENTINELPE_MAX_BYTES", str(50 * 1024 * 1024))))
    extract_timeout_s: float = field(default_factory=lambda: float(os.environ.get("SENTINELPE_EXTRACT_TIMEOUT_S", "60")))
    worker_memory_mb: int = field(default_factory=lambda: int(os.environ.get("SENTINELPE_WORKER_MEMORY_MB", "3072")))
    top_k: int = field(default_factory=lambda: int(os.environ.get("SENTINELPE_TOP_K", "10")))
    allowed_origins: tuple = field(default_factory=lambda: tuple(
        o for o in os.environ.get("SENTINELPE_ALLOWED_ORIGINS", "").split(",") if o))
