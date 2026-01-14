from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from photo_organiser.config.settings import Settings

AppFixture = tuple["Settings", ModuleType, ModuleType]


def test_settings_load_and_create_dirs(app: AppFixture) -> None:
    settings, _db, _service_mod = app

    assert settings.debug is True
    assert settings.app_name == "Photo Organizer"
    assert settings.database.url.startswith("sqlite:///")

    assert settings.storage.photo_root_dir.exists()
    assert settings.storage.thumbnail_dir.exists()
    assert settings.storage.export_dir.exists()
    assert settings.storage.temp_dir.exists()

    assert settings.logging.file_path.parent.exists()
    assert settings.logging.error_file_path.parent.exists()

    assert isinstance(settings.chroma_db.path, Path)
    assert settings.chroma_db.path.exists()

    # Sanity-check formats are configured.
    assert ".jpg" in settings.storage.allowed_image_formats
