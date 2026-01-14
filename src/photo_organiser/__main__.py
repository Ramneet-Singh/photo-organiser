"""Module entry point.

Runs the Click CLI so `python -m photo_organiser` behaves the same as the
`photo-organiser` console script.
"""

from .cli import main

if __name__ == "__main__":
    main()
