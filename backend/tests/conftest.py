import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Configure env for this test run
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("EMMO_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("EMMO_API_KEY", "test-key")
    monkeypatch.setenv("EMMO_ENFORCE_REFERENCE_CODE_PREFIX", "true")
    monkeypatch.setenv("EMMO_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("EMMO_STORE_UPLOADS", "true")
    monkeypatch.delenv("EMMO_OCR_API_URL", raising=False)

    # Clear settings cache so env vars are picked up
    import app.settings as settings_module

    settings_module.get_settings.cache_clear()

    # Re-init engine with the new DB URL
    import app.db.session as session_module

    session_module.init_engine(settings_module.get_settings().database_url)

    # Build app
    import app.main as main_module

    importlib.reload(main_module)
    app = main_module.create_app()

    with TestClient(app) as test_client:
        yield test_client
