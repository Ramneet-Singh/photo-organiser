from __future__ import annotations

import tempfile
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from photo_organiser.config.settings import Settings

AppFixture = tuple["Settings", ModuleType, ModuleType]


@pytest.mark.asyncio
async def test_scan_directory_returns_expected_files(app: AppFixture) -> None:
    _settings, _db_mod, service_mod = app

    service = service_mod.PhotoProcessingService()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for name in ["test.jpg", "selfie.png", "meme.webp"]:
            (temp_path / name).touch()

        result = await service.scan_directory(temp_path, recursive=False)

        assert "error" not in result
        assert result["photo_count"] == 3
        names = {Path(p).name for p in result["photos"]}
        assert names == {"test.jpg", "selfie.png", "meme.webp"}


@pytest.mark.asyncio
async def test_process_photo_batch_happy_path(app: AppFixture) -> None:
    _settings, db_mod, service_mod = app

    # Service writes to DB; ensure schema exists.
    db_mod.create_database()

    service = service_mod.PhotoProcessingService()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        photo = temp_path / "test.jpg"
        photo.touch()

        result = await service.process_photo_batch([photo])

        assert result["total"] == 1
        assert len(result["photos"]) == 1
        assert result["photos"][0]["file_path"] == str(photo)
        assert "processing_time_ms" in result["photos"][0]
        assert "content_type" in result["photos"][0]
