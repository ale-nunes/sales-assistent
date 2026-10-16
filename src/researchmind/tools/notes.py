"""Note tools exposed to ResearchMind agents."""

from researchmind.config import get_settings
from researchmind.storage.notes import (
    read_note as read_stored_note,
    save_note as save_stored_note,
)


def save_note(title: str, content: str) -> dict[str, str]:
    """Save a note in the configured local SQLite database."""
    note = save_stored_note(
        title=title,
        content=content,
        database_path=get_settings().database_path,
    )
    return {
        "title": note.title,
        "content": note.content,
        "updated_at": note.updated_at,
    }


def read_note(title: str) -> dict[str, str] | None:
    """Read a note from the configured local SQLite database."""
    note = read_stored_note(
        title=title,
        database_path=get_settings().database_path,
    )

    if note is None:
        return None

    return {
        "title": note.title,
        "content": note.content,
        "updated_at": note.updated_at,
    }
