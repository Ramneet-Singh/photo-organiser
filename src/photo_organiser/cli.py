"""Photo organizer CLI commands."""

import asyncio
import sys
from pathlib import Path

import click
from loguru import logger

from .config.settings import settings
from .core.database import create_database, db_manager, drop_database
from .models.database import Person


@click.group()
def cli() -> None:
    """Photo Organizer CLI"""
    # Configure logging
    logger.remove()  # Remove default handler

    logger.add(
        settings.logging.file_path,
        rotation="10 MB",
        retention="7 days",
        level=settings.logging.level,
    )

    logger.add(sys.stderr, level=settings.logging.level)


@cli.command()
@click.option("--force", is_flag=True, help="Force drop existing database")
def init_db(force: bool) -> None:
    """Initialize the database."""
    try:
        if force:
            logger.warning("Dropping existing database...")
            drop_database()

        logger.info("Creating database tables...")
        create_database()
        logger.info("Database initialized successfully!")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


@cli.command()
@click.option("--count", default=10, help="Number of sample photos to create")
def create_sample_data(count: int) -> None:
    """Create sample data for testing."""
    try:
        with db_manager.get_session() as session:
            # Create sample person
            person = Person()
            person.name = "John Doe"
            person.display_name = "John"
            person.description = "Sample person for testing"
            session.add(person)
            session.commit()

            logger.info(f"Created sample person: {person.name}")
            logger.info("Sample data created successfully!")

    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        sys.exit(1)


@cli.command()
def db_status() -> None:
    """Show database status and statistics."""
    try:
        # Check connection
        if not db_manager.check_connection():
            logger.error("Database connection failed!")
            sys.exit(1)

        logger.info("=== Database Status ===")
        logger.info("Connection: ✓ Working")
        logger.info("Database: %s", settings.database.url)

    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        sys.exit(1)


@cli.command()
@click.argument("photo_dir", type=click.Path(exists=True))
@click.option("--recursive", is_flag=True, help="Search recursively")
def scan_photos(photo_dir: str, recursive: bool) -> None:
    """Scan directory for photos and add to database."""
    try:
        from .services.photo_service import PhotoProcessingService

        photo_path = Path(photo_dir)
        if not photo_path.is_dir():
            logger.error(f"{photo_dir} is not a directory!")
            sys.exit(1)

        # Find photo files
        photo_files: list[Path] = []
        pattern = "**/*" if recursive else "*"

        for ext in settings.storage.allowed_image_formats:
            photo_files.extend(photo_path.glob(f"{pattern}{ext}"))

        if not photo_files:
            logger.warning("No photo files found!")
            return

        logger.info(f"Found {len(photo_files)} photo files")

        # Process photos
        processor = PhotoProcessingService()

        async def process() -> None:
            await processor.process_photo_batch(photo_files)

        asyncio.run(process())

        logger.info("Photo scanning completed!")

    except Exception as e:
        logger.error(f"Failed to scan photos: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
