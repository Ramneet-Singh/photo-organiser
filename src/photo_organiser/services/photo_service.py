"""Core photo processing service for handling image analysis and face detection."""

import logging
import time
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..config.settings import settings
from ..core.database import close_session, get_session
from ..models.database import ContentType, Face, Photo, ProcessingLog, ProcessingStatus

logger = logging.getLogger(__name__)


class PhotoProcessingService:
    """Service for processing photos including face detection and content classification."""

    def __init__(self) -> None:
        self.settings = settings

        # Initialize ML models will be added in next steps
        self.face_detector = None  # Will be DeepFace
        self.content_classifier = None  # Will be custom classifier
        self.ocr_reader = None  # Will be EasyOCR

    async def process_photo_batch(self, photo_paths: list[Path]) -> dict[str, Any]:
        """
        Process a batch of photos for face detection and content analysis.

        Args:
            photo_paths: List of photo file paths to process

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        results: dict[str, Any] = {
            "total": len(photo_paths),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "processing_time_ms": 0,
            "photos": [],
        }

        logger.info("Starting batch processing of %d photos", len(photo_paths))

        session: Session = get_session()
        try:
            for photo_path in photo_paths:
                try:
                    # Process individual photo
                    photo_result = await self._process_single_photo(photo_path, session)
                    results["photos"].append(photo_result)

                    if photo_result["status"] == "completed":
                        results["processed"] += 1
                    elif photo_result["status"] == "failed":
                        results["failed"] += 1
                    else:
                        results["skipped"] += 1

                except Exception as e:
                    logger.error("Failed to process photo %s: %s", photo_path, e)
                    results["failed"] += 1

                    # Log error
                    self._log_processing_error(
                        session, photo_path, "batch_processing", str(e)
                    )

            try:
                session.commit()
            except Exception as e:
                logger.error("Failed to commit batch processing results: %s", e)
                session.rollback()
        finally:
            close_session(session)

        results["processing_time_ms"] = int((time.time() - start_time) * 1000)

        logger.info(
            "Batch processing completed: %d/%d photos in %dms",
            results["processed"],
            results["total"],
            results["processing_time_ms"],
        )

        return results

    async def _process_single_photo(
        self, photo_path: Path, session: Session
    ) -> dict[str, Any]:
        """
        Process a single photo for face detection and content analysis.

        Args:
            photo_path: Path to photo file
            session: Database session

        Returns:
            Dictionary with processing results
        """
        photo_start_time = time.time()

        # Check if photo already exists
        existing_photo = (
            session.query(Photo).filter(Photo.file_path == str(photo_path)).first()
        )
        if (
            existing_photo
            and existing_photo.processing_status == ProcessingStatus.COMPLETED
        ):
            return {
                "file_path": str(photo_path),
                "status": "skipped",
                "reason": "already_processed",
                "processing_time_ms": 0,
            }

        try:
            # Create or update photo record
            if existing_photo:
                photo = existing_photo
                photo.processing_status = ProcessingStatus.PROCESSING
            else:
                photo = Photo()
                photo.file_path = str(photo_path)
                photo.file_hash = Photo.compute_file_hash(photo_path)
                photo.processing_status = ProcessingStatus.PROCESSING
                session.add(photo)
                session.flush()  # Get the ID

            # Get basic photo info
            await self._extract_photo_metadata(photo_path, photo)

            # Face detection (placeholder - will be implemented with DeepFace)
            faces = await self._detect_faces(photo_path)
            photo.has_faces = len(faces) > 0
            photo.face_count = len(faces)

            # Save faces to database
            for face_data in faces:
                face = Face()
                face.photo_id = photo.id
                face.embedding_id = str(face_data["embedding_id"])
                face.bbox_x = int(face_data["bbox"]["x"])
                face.bbox_y = int(face_data["bbox"]["y"])
                face.bbox_width = int(face_data["bbox"]["width"])
                face.bbox_height = int(face_data["bbox"]["height"])
                face.confidence = float(face_data["confidence"])
                face.person_id = None
                session.add(face)

            # Content classification (placeholder)
            content_type = await self._classify_content(photo_path)
            photo.content_type = content_type["type"]
            photo.is_screenshot = content_type["is_screenshot"]
            photo.has_text = content_type["has_text"]
            photo.text_content = content_type.get("text", "")

            # Update processing status
            photo.processing_status = ProcessingStatus.COMPLETED

            # Log successful processing
            self._log_processing_success(
                session, photo, "batch_processing", time.time() - photo_start_time
            )

            return {
                "file_path": str(photo_path),
                "status": "completed",
                "photo_id": photo.id,
                "face_count": len(faces),
                "content_type": content_type["type"],
                "processing_time_ms": int((time.time() - photo_start_time) * 1000),
            }

        except Exception as e:
            logger.error("Failed to process photo %s: %s", photo_path, e)

            # Update status to failed
            if "photo" in locals():
                photo.processing_status = ProcessingStatus.FAILED
                self._log_processing_error(
                    session, photo_path, "batch_processing", str(e)
                )

            return {
                "file_path": str(photo_path),
                "status": "failed",
                "error": str(e),
                "processing_time_ms": int((time.time() - photo_start_time) * 1000),
            }

    async def _extract_photo_metadata(self, photo_path: Path, photo: Photo) -> None:
        """
        Extract basic metadata from photo file.

        Args:
            photo_path: Path to photo file
            photo: Photo model to update
        """
        try:
            from PIL import Image, UnidentifiedImageError

            with Image.open(photo_path) as img:
                photo.width = img.width
                photo.height = img.height
                photo.mime_type = img.format.lower() if img.format else "unknown"

                # Get file size
                photo.file_size = photo_path.stat().st_size

        except UnidentifiedImageError as e:
            # Still record file size even if we can't decode the image.
            photo.file_size = photo_path.stat().st_size

            suffix = photo_path.suffix.lower()
            if suffix in {".heic", ".heif"}:
                logger.info(
                    "HEIC/HEIF decode not available for %s (%s). "
                    "Install pillow-heif + libheif to enable metadata extraction.",
                    photo_path,
                    e,
                )
            else:
                logger.info(
                    "Unsupported/corrupt image %s (%s); continuing without metadata.",
                    photo_path,
                    e,
                )

        except Exception as e:
            logger.warning("Failed to extract metadata from %s: %s", photo_path, e)

    async def _detect_faces(self, photo_path: Path) -> list[dict[str, Any]]:
        """
        Detect faces in photo using ML model.

        Args:
            photo_path: Path to photo file

        Returns:
            List of face detection results
        """
        # Placeholder implementation - will be replaced with DeepFace integration
        # For now, return empty list to simulate no faces detected
        logger.debug("Face detection placeholder for %s", photo_path)
        return []

    async def _classify_content(self, photo_path: Path) -> dict[str, Any]:
        """
        Classify photo content type.

        Args:
            photo_path: Path to photo file

        Returns:
            Dictionary with classification results
        """
        # Placeholder implementation - will be replaced with actual ML models
        file_ext = photo_path.suffix.lower()

        # Simple heuristic-based classification for now
        if (
            file_ext in [".png", ".jpg", ".jpeg"]
            and "screenshot" in photo_path.name.lower()
        ):
            return {
                "type": ContentType.SCREENSHOT,
                "is_screenshot": True,
                "has_text": False,
                "confidence": 0.8,
                "text": "",
            }
        elif any(
            keyword in photo_path.name.lower() for keyword in ["meme", "funny", "lol"]
        ):
            return {
                "type": ContentType.MEME,
                "is_screenshot": False,
                "has_text": True,
                "confidence": 0.7,
                "text": "meme text placeholder",
            }
        else:
            return {
                "type": ContentType.PHOTO,
                "is_screenshot": False,
                "has_text": False,
                "confidence": 0.9,
                "text": "",
            }

    def _log_processing_success(
        self, session: Session, photo: Photo, operation: str, duration: float
    ) -> None:
        """
        Log successful processing operation.

        Args:
            session: Database session
            photo: Photo model
            operation: Operation type
            duration: Processing duration in seconds
        """
        log = ProcessingLog()
        log.photo_id = photo.id
        log.operation = operation
        log.status = "success"
        log.processing_time_ms = int(duration * 1000)
        session.add(log)

    def _log_processing_error(
        self, session: Session, photo_path: Path, operation: str, error_message: str
    ) -> None:
        """
        Log processing error.

        Args:
            session: Database session
            photo_path: Path to photo
            operation: Operation type
            error_message: Error message
        """
        # Try to get photo ID if exists
        photo = session.query(Photo).filter(Photo.file_path == str(photo_path)).first()

        log = ProcessingLog()
        log.photo_id = photo.id if photo else None
        log.operation = operation
        log.status = "failed"
        log.error_message = error_message
        session.add(log)

    async def get_processing_status(self, batch_id: str) -> dict[str, Any]:
        """
        Get processing status for a batch.

        Args:
            batch_id: Batch identifier

        Returns:
            Dictionary with status information
        """
        # For now, return a simple status
        # In future implementation, this would track actual batch jobs
        return {
            "batch_id": batch_id,
            "status": "completed",
            "progress": 100,
            "total_photos": 0,
            "processed_photos": 0,
            "failed_photos": 0,
        }

    async def scan_directory(
        self, directory: Path, recursive: bool = True
    ) -> dict[str, Any]:
        """
        Scan directory for supported photo files.

        Args:
            directory: Directory to scan
            recursive: Whether to scan recursively

        Returns:
            Dictionary with scan results
        """
        logger.info("Scanning directory: %s", directory)

        if not directory.exists() or not directory.is_dir():
            return {
                "error": f"Directory {directory} does not exist or is not a directory",
                "photos": [],
            }

        photo_files: list[Path] = []
        pattern = "**/*" if recursive else "*"

        for ext in settings.storage.allowed_image_formats:
            photo_files.extend(directory.glob(f"{pattern}{ext}"))

        # Remove duplicates and sort
        photo_files = list(set(photo_files))
        photo_files.sort()

        logger.info("Found %d photo files", len(photo_files))

        return {
            "directory": str(directory),
            "recursive": recursive,
            "photo_count": len(photo_files),
            "photos": [str(p) for p in photo_files],
        }

    async def get_photo_stats(self) -> dict[str, Any]:
        """
        Get overall photo processing statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            session: Session = get_session()
            try:
                from sqlalchemy import func

                total_photos = session.query(Photo).count()
                processed_photos = (
                    session.query(Photo)
                    .filter(Photo.processing_status == ProcessingStatus.COMPLETED)
                    .count()
                )
                failed_photos = (
                    session.query(Photo)
                    .filter(Photo.processing_status == ProcessingStatus.FAILED)
                    .count()
                )
                pending_photos = (
                    session.query(Photo)
                    .filter(Photo.processing_status == ProcessingStatus.PENDING)
                    .count()
                )

                # Count photos with faces
                photos_with_faces = session.query(Photo).filter(Photo.has_faces).count()

                # Content type distribution
                content_types = (
                    session.query(Photo.content_type, func.count(Photo.content_type))
                    .group_by(Photo.content_type)
                    .all()
                )

                content_type_distribution = {
                    str(content_type): int(count)
                    for content_type, count in content_types
                }

                return {
                    "total_photos": total_photos,
                    "processed_photos": processed_photos,
                    "failed_photos": failed_photos,
                    "pending_photos": pending_photos,
                    "photos_with_faces": photos_with_faces,
                    "content_type_distribution": content_type_distribution,
                    "processing_completion_rate": (
                        processed_photos / total_photos * 100
                    )
                    if total_photos > 0
                    else 0,
                }
            finally:
                close_session(session)
        except Exception as e:
            logger.error("Failed to get photo stats: %s", e)
            return {"error": str(e)}
