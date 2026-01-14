"""Database models for photo organizer application."""

import hashlib
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProcessingStatus(str, Enum):
    """Processing status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContentType(str, Enum):
    """Content type enumeration."""

    PHOTO = "photo"
    MEME = "meme"
    SCREENSHOT = "screenshot"
    TEXT_MESSAGE = "text_message"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class Photo(Base):
    """Photo model representing an image file in the system."""

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    modified_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Processing status
    has_faces: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_text: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_screenshot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(20), default=ContentType.UNKNOWN, nullable=False
    )
    processing_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.PENDING, nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    faces: Mapped[list["Face"]] = relationship(
        "Face", back_populates="photo", cascade="all, delete-orphan"
    )
    processing_logs: Mapped[list["ProcessingLog"]] = relationship(
        "ProcessingLog", back_populates="photo", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_photos_file_path", "file_path"),
        Index("idx_photos_file_hash", "file_hash"),
        Index("idx_photos_processing_status", "processing_status"),
        Index("idx_photos_content_type", "content_type"),
        Index("idx_photos_created_date", "created_at"),
        Index("idx_photos_has_faces", "has_faces"),
    )

    @property
    def file_name(self) -> str:
        """Get filename from file path."""
        return Path(self.file_path).name

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return Path(self.file_path).suffix.lower()

    @property
    def aspect_ratio(self) -> float | None:
        """Calculate aspect ratio of photo."""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return None

    @classmethod
    def compute_file_hash(cls, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, file_path='{self.file_path}', status='{self.processing_status}')>"


class Person(Base):
    """Person model representing an identified individual."""

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    face_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    faces: Mapped[list["Face"]] = relationship("Face", back_populates="person")

    # Indexes
    __table_args__ = (
        Index("idx_persons_name", "name"),
        Index("idx_persons_face_count", "face_count"),
    )

    @property
    def photo_count(self) -> int:
        """Get number of unique photos containing this person."""
        if not self.faces:
            return 0
        unique_photos = {face.photo_id for face in self.faces}
        return len(unique_photos)

    def __repr__(self) -> str:
        return (
            f"<Person(id={self.id}, name='{self.name}', face_count={self.face_count})>"
        )


class Face(Base):
    """Face model representing a detected face in a photo."""

    __tablename__ = "faces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id"), nullable=False, index=True
    )
    embedding_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Reference to ChromaDB embedding
    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )

    # Bounding box coordinates
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_width: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_height: Mapped[int] = mapped_column(Integer, nullable=False)

    # Detection confidence
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Quality metrics
    sharpness: Mapped[float | None] = mapped_column(Float, nullable=True)
    brightness: Mapped[float | None] = mapped_column(Float, nullable=True)
    blur_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    photo: Mapped["Photo"] = relationship("Photo", back_populates="faces")
    person: Mapped[Optional["Person"]] = relationship("Person", back_populates="faces")

    # Indexes
    __table_args__ = (
        Index("idx_faces_photo_id", "photo_id"),
        Index("idx_faces_person_id", "person_id"),
        Index("idx_faces_embedding_id", "embedding_id"),
        Index("idx_faces_confidence", "confidence"),
    )

    @property
    def bbox(self) -> dict[str, int]:
        """Get bounding box as a dictionary."""
        return {
            "x": self.bbox_x,
            "y": self.bbox_y,
            "width": self.bbox_width,
            "height": self.bbox_height,
        }

    @property
    def center_point(self) -> tuple[int, int]:
        """Get center point of bounding box."""
        center_x = self.bbox_x + self.bbox_width // 2
        center_y = self.bbox_y + self.bbox_height // 2
        return (center_x, center_y)

    @property
    def area(self) -> int:
        """Get area of bounding box."""
        return self.bbox_width * self.bbox_height

    def __repr__(self) -> str:
        person_name = self.person.name if self.person else "Unassigned"
        return f"<Face(id={self.id}, photo_id={self.photo_id}, person='{person_name}')>"


class ProcessingLog(Base):
    """Processing log for tracking operations and debugging."""

    __tablename__ = "processing_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    photo_id: Mapped[int | None] = mapped_column(
        ForeignKey("photos.id"), nullable=True, index=True
    )
    operation: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Timing and performance
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Error details
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional metadata
    metadata_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string for additional data

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    photo: Mapped[Optional["Photo"]] = relationship(
        "Photo", back_populates="processing_logs"
    )

    # Indexes
    __table_args__ = (
        Index("idx_logs_photo_id", "photo_id"),
        Index("idx_logs_operation", "operation"),
        Index("idx_logs_status", "status"),
        Index("idx_logs_created_at", "created_at"),
    )

    @property
    def metadata_dict(self) -> dict[str, Any]:
        """Parse metadata JSON string."""
        if self.metadata_json:
            return json.loads(self.metadata_json)  # type: ignore
        return {}

    @metadata_dict.setter
    def metadata_dict(self, value: dict[str, Any]) -> None:
        """Set metadata from dictionary."""
        self.metadata_json = json.dumps(value)

    def __repr__(self) -> str:
        return f"<ProcessingLog(id={self.id}, photo_id={self.photo_id}, operation='{self.operation}', status='{self.status}')>"


class ReviewDecision(Base):
    """Review decision model for tracking user decisions during photo review."""

    __tablename__ = "review_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id"), nullable=False, unique=True, index=True
    )
    decision: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # keep, remove, maybe
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Review session
    session_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    reviewer_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Additional context
    review_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    photo: Mapped["Photo"] = relationship("Photo")

    # Indexes
    __table_args__ = (
        Index("idx_decisions_photo_id", "photo_id"),
        Index("idx_decisions_decision", "decision"),
        Index("idx_decisions_session_id", "session_id"),
        Index("idx_decisions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReviewDecision(id={self.id}, photo_id={self.photo_id}, decision='{self.decision}')>"


class ExportJob(Base):
    """Export job model for tracking photo export operations."""

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Export criteria
    filter_criteria_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string of filters
    destination_path: Mapped[str] = mapped_column(Text, nullable=False)

    # Job status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    total_photos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_photos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_photos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processing_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional info
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Indexes
    __table_args__ = (
        Index("idx_exports_status", "status"),
        Index("idx_exports_created_at", "created_at"),
        Index("idx_exports_created_by", "created_by"),
    )

    @property
    def filter_criteria(self) -> dict[str, Any]:
        """Parse filter criteria JSON string."""
        if self.filter_criteria_json:
            return json.loads(self.filter_criteria_json)  # type: ignore
        return {}

    @filter_criteria.setter
    def filter_criteria(self, value: dict[str, Any]) -> None:
        """Set filter criteria from dictionary."""
        self.filter_criteria_json = json.dumps(value)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_photos == 0:
            return 0.0
        return (self.processed_photos / self.total_photos) * 100

    @property
    def is_completed(self) -> bool:
        """Check if export is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if export failed."""
        return self.status == "failed"

    def __repr__(self) -> str:
        return (
            f"<ExportJob(id={self.id}, name='{self.job_name}', status='{self.status}')>"
        )
