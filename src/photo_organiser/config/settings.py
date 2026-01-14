"""Application configuration (single source of truth).

Uses Pydantic Settings for typed, validated configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(default="sqlite:///./data/photo_organizer.db")
    echo: bool = Field(default=False)


class ChromaDBSettings(BaseSettings):
    """ChromaDB configuration settings."""

    model_config = SettingsConfigDict(env_prefix="CHROMA_")

    path: Path = Field(default=Path("./data/chroma_db"))
    collection_name: str = Field(default="face_embeddings")
    embedding_dimension: int = Field(default=512)


class ProcessingSettings(BaseSettings):
    """Photo processing configuration settings."""

    model_config = SettingsConfigDict(env_prefix="PROCESSING_")

    batch_size: int = Field(default=32)
    max_workers: int = Field(default=4)
    memory_threshold_gb: float = Field(default=8.0)
    processing_timeout_seconds: int = Field(default=300)

    # Face detection settings
    face_detector_backend: str = Field(default="retinaface")
    face_model_name: str = Field(default="Facenet512")
    face_confidence_threshold: float = Field(default=0.9)

    # Content classification settings
    content_confidence_threshold: float = Field(default=0.7)
    text_confidence_threshold: float = Field(default=0.8)


class FileStorageSettings(BaseSettings):
    """File storage configuration settings."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    photo_root_dir: Path = Field(default=Path("./data/photos"))
    thumbnail_dir: Path = Field(default=Path("./data/thumbnails"))
    export_dir: Path = Field(default=Path("./data/exports"))
    temp_dir: Path = Field(default=Path("./data/temp"))

    max_photo_size_mb: int = Field(default=100)

    allowed_image_formats: list[str] = Field(
        default_factory=lambda: [
            ".jpg",
            ".jpeg",
            ".png",
            ".heic",
            ".webp",
            ".tiff",
            ".bmp",
        ]
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO")
    file_path: Path = Field(default=Path("./logs/app.log"))
    error_file_path: Path = Field(default=Path("./logs/error.log"))


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    model_config = SettingsConfigDict()

    secret_key: str = Field(
        default="development-secret-key",
        validation_alias=AliasChoices("SECURITY_SECRET_KEY", "SECRET_KEY"),
    )
    algorithm: str = Field(default="HS256")

    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )


class PerformanceSettings(BaseSettings):
    """Performance optimization settings."""

    model_config = SettingsConfigDict(env_prefix="PERFORMANCE_")

    cache_ttl_seconds: int = Field(default=3600)
    use_gpu: bool = Field(default=False)


class Settings(BaseSettings):
    """Main application settings combining all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Photo Organizer")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    chroma_db: ChromaDBSettings = Field(default_factory=ChromaDBSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    storage: FileStorageSettings = Field(default_factory=FileStorageSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)

    def model_post_init(self, __context: Any, /) -> None:
        self._ensure_directories()
        self.validate_settings()

    def _ensure_directories(self) -> None:
        sqlite_prefix = "sqlite:///"
        database_dir: Path | None = None
        if self.database.url.startswith(sqlite_prefix):
            db_path = Path(self.database.url.removeprefix(sqlite_prefix))
            database_dir = db_path.parent

        directories: list[Path] = [
            d
            for d in [
                database_dir,
                self.chroma_db.path,
                self.storage.photo_root_dir,
                self.storage.thumbnail_dir,
                self.storage.export_dir,
                self.storage.temp_dir,
                self.logging.file_path.parent,
                self.logging.error_file_path.parent,
            ]
            if d is not None
        ]

        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)

    def validate_settings(self) -> None:
        """Validate critical settings."""
        if not self.debug and self.security.secret_key == "development-secret-key":
            raise ValueError("SECURITY_SECRET_KEY must be set in production")

        if self.processing.memory_threshold_gb < 1:
            raise ValueError("PROCESSING_MEMORY_THRESHOLD_GB must be at least 1")

        if self.processing.batch_size < 1:
            raise ValueError("PROCESSING_BATCH_SIZE must be at least 1")


settings = Settings()
