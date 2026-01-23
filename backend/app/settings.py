"""Application configuration.

Settings are loaded from environment variables with the `EMMO_` prefix.

- In local dev, values can come from `backend/.env`.
- In production, prefer injecting environment variables via the runtime.

Use `get_settings()` to access a cached `Settings` instance.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Strongly-typed settings for the backend."""
    model_config = SettingsConfigDict(env_file=".env", env_prefix="EMMO_", extra="ignore")

    database_url: str = "sqlite:///./emmo.db"

    # SQLAlchemy engine options
    db_echo: bool = False
    db_pool_pre_ping: bool = True
    # Pool settings apply to non-SQLite URLs.
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # When true, the app will create tables at startup (dev-friendly).
    # In production with Postgres + Alembic, set this to false and run `alembic upgrade head`.
    db_auto_create: bool = True

    # Optional: protect the API with a simple static key.
    # If set, clients must send `X-API-Key: <value>`.
    api_key: str | None = None

    # Require API key for write endpoints (POST/PUT) when api_key is set.
    require_api_key_for_write: bool = True

    # Optional: also require API key for read endpoints (GET).
    require_api_key_for_read: bool = False

    # Security hardening
    enable_trusted_hosts: bool = False
    trusted_hosts: str = "localhost,127.0.0.1"
    https_redirect: bool = False
    enable_hsts: bool = False

    # Basic (in-memory) rate limiting. Set to 0 to disable.
    rate_limit_per_minute: int = 0

    # Optional CORS (comma-separated origins). Example: "http://localhost:5173,http://localhost:3000"
    cors_origins: str | None = None

    # Upload validation
    max_upload_bytes: int = 15 * 1024 * 1024  # 15MB
    allowed_upload_mime_types: str = "image/jpeg,image/png,application/pdf"

    # Storage (invoices/PDFs/images)
    storage_root: str = "./storage"
    store_uploads: bool = True

    # Optional: if provided, backend will POST the invoice image/pdf to this OCR API.
    # Expected response is flexible; see services/ocr.py
    ocr_api_url: str | None = None
    ocr_api_key: str | None = None
    ocr_api_timeout_s: float = 60.0

    # Reference code auto-generation
    auto_reference_code: bool = False
    reference_code_prefix_len: int = 3
    reference_code_hash_len: int = 12

    # Enforce canonical reference codes (SUP_XXX) for storage/search.
    enforce_reference_code_prefix: bool = True

    # Pricing rules (non-AI)
    price_correction_mode: str = "flag_only"  # flag_only | floor_to_cost | floor_to_reference_median
    price_min_ratio: float = 0.7

    # Price history (math-only heuristics)
    price_history_days: int = 365
    price_history_min_samples: int = 3

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reloadable by clearing the cache in tests)."""
    return Settings()
