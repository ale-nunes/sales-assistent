"""SQLite persistence for ResearchMind notes."""

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 100_000


@dataclass(frozen=True, slots=True)
class Note:
    """A persisted note."""

    title: str
    content: str
    updated_at: str


def _validate_note(title: str, content: str) -> tuple[str, str]:
    title = title.strip()
    content = content.strip()

    if not title:
        raise ValueError("Note title cannot be empty.")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError("Note title is too long.")
    if not content:
        raise ValueError("Note content cannot be empty.")
    if len(content) > MAX_CONTENT_LENGTH:
        raise ValueError("Note content is too long.")

    return title, content


def _initialize_database(database_path: str | Path) -> Path:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                title TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()

    return path


def save_note(
    title: str,
    content: str,
    database_path: str | Path,
) -> Note:
    """Create a note or update an existing note with the same title."""
    title, content = _validate_note(title, content)
    path = _initialize_database(database_path)
    updated_at = datetime.now(UTC).isoformat()

    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row

        with connection:
            connection.execute(
                """
                INSERT INTO notes (title, content, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(title) DO UPDATE SET
                    content = excluded.content,
                    updated_at = excluded.updated_at
                """,
                (title, content, updated_at),
            )
            row = connection.execute(
                "SELECT title, content, updated_at FROM notes WHERE title = ?",
                (title,),
            ).fetchone()

    if row is None:
        raise RuntimeError("Saved note could not be retrieved.")

    return Note(
        title=str(row["title"]),
        content=str(row["content"]),
        updated_at=str(row["updated_at"]),
    )


def read_note(
    title: str,
    database_path: str | Path,
) -> Note | None:
    """Retrieve a note by its exact title."""
    title = title.strip()

    if not title:
        raise ValueError("Note title cannot be empty.")

    path = _initialize_database(database_path)

    with closing(sqlite3.connect(path)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT title, content, updated_at FROM notes WHERE title = ?",
            (title,),
        ).fetchone()

    if row is None:
        return None

    return Note(
        title=str(row["title"]),
        content=str(row["content"]),
        updated_at=str(row["updated_at"]),
    )
