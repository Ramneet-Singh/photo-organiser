"""Run smoke checks in an isolated temporary environment.

This script:
- Creates a temporary directory
- Points all settings (DB, storage, logs, chroma) at that temp directory
- Runs the existing smoke scripts:
  - scripts/init_db_smoke.py init-db
  - scripts/service_smoke.py init
  - scripts/service_smoke.py scan test_photos

Usage:
    uv run python -m scripts.run_smoke
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path


def _set_env(tmp_path: Path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'photo_organizer_smoke.db'}"
    os.environ["CHROMA_PATH"] = str(tmp_path / "chroma_db")

    os.environ["STORAGE_PHOTO_ROOT_DIR"] = str(tmp_path / "photos")
    os.environ["STORAGE_THUMBNAIL_DIR"] = str(tmp_path / "thumbnails")
    os.environ["STORAGE_EXPORT_DIR"] = str(tmp_path / "exports")
    os.environ["STORAGE_TEMP_DIR"] = str(tmp_path / "temp")

    os.environ["LOG_FILE_PATH"] = str(tmp_path / "app.log")
    os.environ["LOG_ERROR_FILE_PATH"] = str(tmp_path / "error.log")

    # Avoid production-style secret key checks.
    os.environ["DEBUG"] = "true"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _set_env(tmp_path)

        if __package__ is None:
            raise RuntimeError(
                "Run this as a module so relative imports work: "
                "`uv run python -m scripts.run_smoke`."
            )

        # Import after env is set (settings loads at import time).
        from . import init_db_smoke, service_smoke

        print("[smoke] init-db")
        sys.argv = ["init_db_smoke.py", "init-db"]
        init_db_smoke.main()

        print("[smoke] service init")
        sys.argv = ["service_smoke.py", "init"]
        asyncio.run(service_smoke.main())

        print("[smoke] service scan test_photos")
        sys.argv = ["service_smoke.py", "scan", "test_photos"]
        asyncio.run(service_smoke.main())


if __name__ == "__main__":
    main()
