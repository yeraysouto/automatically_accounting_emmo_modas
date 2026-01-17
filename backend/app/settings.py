from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="EMMO_", extra="ignore")

    database_url: str = "sqlite:///./emmo.db"

    # Optional: protect the API with a simple static key.
    # If set, clients must send `X-API-Key: <value>`.
    api_key: str | None = None

    # Require API key for write endpoints (POST/PUT) when api_key is set.
    require_api_key_for_write: bool = True

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

    # Pricing rules (non-AI)
    price_correction_mode: str = "flag_only"  # flag_only | floor_to_cost
    price_min_ratio: float = 0.7

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
