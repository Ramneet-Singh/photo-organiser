"""Photo organiser package."""


def main() -> None:
    """Entry point for the application.

    Delegates to the Click CLI so `uv run photo-organiser` and
    `python -m photo_organiser` behave consistently.
    """

    from .cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
