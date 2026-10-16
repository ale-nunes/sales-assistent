"""Tests for ResearchMind note persistence and tools."""

from pathlib import Path
from types import SimpleNamespace

import pytest

import researchmind.tools.notes as note_tools
from researchmind.storage.notes import read_note, save_note


def test_save_and_read_note(tmp_path: Path) -> None:
    database = tmp_path / "notes.sqlite3"

    saved = save_note("Project", "ResearchMind notes", database)
    retrieved = read_note("Project", database)

    assert retrieved == saved
    assert saved.content == "ResearchMind notes"
    assert saved.updated_at


def test_saving_same_title_updates_note(tmp_path: Path) -> None:
    database = tmp_path / "notes.sqlite3"

    save_note("Project", "Old content", database)
    updated = save_note("Project", "New content", database)

    assert read_note("Project", database) == updated
    assert updated.content == "New content"


def test_read_missing_note_returns_none(tmp_path: Path) -> None:
    assert read_note("Missing", tmp_path / "notes.sqlite3") is None


def test_empty_title_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="title cannot be empty"):
        save_note(" ", "Some content", tmp_path / "notes.sqlite3")


def test_empty_content_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="content cannot be empty"):
        save_note("Project", " ", tmp_path / "notes.sqlite3")


def test_sql_injection_text_is_stored_as_data(tmp_path: Path) -> None:
    database = tmp_path / "notes.sqlite3"
    title = "Project'; DROP TABLE notes; --"

    save_note(title, "Safe content", database)

    assert read_note(title, database) is not None


def test_tool_wrappers_use_configured_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "configured.sqlite3"
    monkeypatch.setattr(
        note_tools,
        "get_settings",
        lambda: SimpleNamespace(database_path=database),
    )

    saved = note_tools.save_note("Test", "Tool content")

    assert saved["title"] == "Test"
    assert note_tools.read_note("Test") == saved
