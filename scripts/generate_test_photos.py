"""Generate tiny valid image fixtures in ./test_photos.

The repo originally contained 0-byte placeholder files. Pillow can't open those, so
this script regenerates them as real images for local smoke runs.

It intentionally avoids generating HEIC because HEIC decoding typically requires
an optional plugin (e.g. pillow-heif + libheif).
"""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> None:
    root = _repo_root()
    out_dir = root / "test_photos"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "Pillow is required to generate fixtures. Install with 'uv sync'."
        ) from exc

    fixtures: list[tuple[str, str, tuple[int, int, int]]] = [
        ("test.jpg", "JPEG", (220, 20, 60)),
        ("selfie.png", "PNG", (20, 120, 220)),
        ("screenshot.jpg", "JPEG", (240, 240, 240)),
        ("meme.webp", "WEBP", (20, 200, 80)),
    ]

    # Remove the old empty HEIC placeholder if present.
    heic = out_dir / "screenshot.heic"
    if heic.exists():
        heic.unlink()

    for filename, fmt, rgb in fixtures:
        path = out_dir / filename
        img = Image.new("RGB", (32, 32), rgb)
        save_kwargs: dict[str, object] = {}
        if fmt == "JPEG":
            save_kwargs["quality"] = 85
            save_kwargs["optimize"] = True
        if fmt == "WEBP":
            save_kwargs["quality"] = 80
            save_kwargs["method"] = 4
        img.save(path, format=fmt, **save_kwargs)

    print("Generated fixtures:")
    for p in sorted(out_dir.iterdir()):
        if p.is_file():
            print(f"- {p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
