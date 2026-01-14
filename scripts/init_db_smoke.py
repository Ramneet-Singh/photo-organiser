"""Basic photo organizer CLI for testing."""

import sys
from pathlib import Path

from photo_organiser.config.settings import settings
from photo_organiser.core.database import create_database


def main() -> None:
    """Basic CLI for testing."""
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        print("Initializing database...")
        try:
            # Create directories manually first
            sqlite_prefix = "sqlite:///"
            db_dir = None
            if settings.database.url.startswith(sqlite_prefix):
                db_dir = Path(settings.database.url.removeprefix(sqlite_prefix)).parent

            for directory in [
                d
                for d in [
                    db_dir,
                    settings.chroma_db.path,
                    settings.storage.photo_root_dir,
                    settings.storage.thumbnail_dir,
                    settings.storage.export_dir,
                    settings.storage.temp_dir,
                ]
                if d is not None
            ]:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)

            create_database()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("Usage: python -m photo_organiser init-db")


if __name__ == "__main__":
    main()
