from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="EMMA_", extra="ignore")

    database_url: str = "sqlite:///./emma.db"

    # Optional: protect the API with a simple static key.
    # If set, clients must send `X-API-Key: <value>`.
    api_key: str | None = None

    # Optional CORS (comma-separated origins). Example: "http://localhost:5173,http://localhost:3000"
    cors_origins: str | None = None

    # Upload validation
    max_upload_bytes: int = 15 * 1024 * 1024  # 15MB
    allowed_upload_mime_types: str = "image/jpeg,image/png,application/pdf"

    # Optional: if provided, backend will POST the invoice image/pdf to this OCR API.
    # Expected response is flexible; see services/ocr.py
    ocr_api_url: str | None = None
    ocr_api_key: str | None = None
    ocr_api_timeout_s: float = 60.0

@lru_cache
def get_settings() -> Settings:
    return Settings()
