"""Test photo service functionality."""

import asyncio
import sys
from pathlib import Path

from photo_organiser.services.photo_service import PhotoProcessingService


async def main() -> None:
    """Test photo processing service."""
    if len(sys.argv) < 2:
        print("Usage: python test_service.py <test_mode>")
        print("test_mode: 'init' or 'scan'")
        return

    mode = sys.argv[1]
    service = PhotoProcessingService()

    if mode == "init":
        print("Testing photo service initialization...")
        print(f"Settings loaded: {service.settings}")
        print("✓ Photo service initialized successfully")

    elif mode == "scan":
        if len(sys.argv) < 3:
            print("Usage: python test_service.py scan <directory>")
            return

        directory = Path(sys.argv[2])
        if not directory.exists():
            print(f"Error: Directory {directory} does not exist")
            return

        print(f"Scanning directory: {directory}")

        # Scan for photos
        scan_result = await service.scan_directory(directory, recursive=False)

        if "error" in scan_result:
            print(f"Error: {scan_result['error']}")
            return

        print(f"Found {scan_result['photo_count']} photos")

        if scan_result["photo_count"] > 0:
            print(f"Processing {scan_result['photo_count']} photos...")

            # Process first 5 photos for testing
            photos_to_process = [Path(p) for p in scan_result["photos"][:5]]
            result = await service.process_photo_batch(photos_to_process)

            print("Processing results:")
            print(f"  Total: {result['total']}")
            print(f"  Processed: {result['processed']}")
            print(f"  Failed: {result['failed']}")
            print(f"  Skipped: {result['skipped']}")
            print(f"  Time: {result['processing_time_ms']}ms")

            if result["photos"]:
                print("  Processed photos:")
                for photo_result in result["photos"]:
                    if photo_result["status"] == "completed":
                        print(
                            f"    ✓ {photo_result['file_path']} ({photo_result['face_count']} faces)"
                        )
                    else:
                        print(
                            f"    ✗ {photo_result['file_path']}: {photo_result.get('error', 'Unknown error')}"
                        )

    else:
        print(f"Unknown mode: {mode}")


if __name__ == "__main__":
    asyncio.run(main())
