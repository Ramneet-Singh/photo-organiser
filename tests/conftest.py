from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from photo_organiser.config.settings import Settings

AppFixture = tuple["Settings", ModuleType, ModuleType]


@pytest.fixture()
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppFixture:
    """Load the app with an isolated filesystem + sqlite DB.

    This avoids tests depending on a developer's local `.env` or `./data` folder.
    """

    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("DATABASE_ECHO", "false")

    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma_db"))

    monkeypatch.setenv("STORAGE_PHOTO_ROOT_DIR", str(tmp_path / "photos"))
    monkeypatch.setenv("STORAGE_THUMBNAIL_DIR", str(tmp_path / "thumbnails"))
    monkeypatch.setenv("STORAGE_EXPORT_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("STORAGE_TEMP_DIR", str(tmp_path / "temp"))

    monkeypatch.setenv("LOG_FILE_PATH", str(tmp_path / "logs" / "app.log"))
    monkeypatch.setenv("LOG_ERROR_FILE_PATH", str(tmp_path / "logs" / "error.log"))

    # Accept both SECURITY_SECRET_KEY and SECRET_KEY; set the preferred one.
    monkeypatch.setenv("SECURITY_SECRET_KEY", "test-secret")

    import photo_organiser.config.settings as settings_mod

    settings_mod = importlib.reload(settings_mod)

    import photo_organiser.core.database as db_mod

    db_mod = importlib.reload(db_mod)

    import photo_organiser.services.photo_service as service_mod

    service_mod = importlib.reload(service_mod)

    return settings_mod.settings, db_mod, service_mod
