"""Tests for the read-only Gmail integration."""

import base64
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import researchmind.integrations.gmail as gmail_module


class FakeRequest:
    """Mock a Google API request."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response

    def execute(self) -> dict[str, Any]:
        return self.response


class FakeMessages:
    """Mock Gmail message search and retrieval."""

    def list(self, **kwargs: Any) -> FakeRequest:
        assert kwargs["userId"] == "me"
        assert kwargs["q"] == "subject:relatorio"
        assert kwargs["maxResults"] == 5

        return FakeRequest({"messages": [{"id": "message-1"}]})

    def get(self, **kwargs: Any) -> FakeRequest:
        assert kwargs["id"] == "message-1"
        assert kwargs["format"] == "full"

        body = base64.urlsafe_b64encode("Relatório de vendas".encode()).decode("ascii")

        return FakeRequest(
            {
                "id": "message-1",
                "threadId": "thread-1",
                "snippet": "Resumo do relatório",
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [
                        {"name": "From", "value": "equipe@example.com"},
                        {"name": "To", "value": "usuario@example.com"},
                        {"name": "Subject", "value": "Relatório mensal"},
                        {"name": "Date", "value": "Mon, 19 Oct 2026 10:00:00 -0300"},
                    ],
                    "body": {"data": body},
                },
            }
        )


class FakeUsers:
    """Mock the Gmail users resource."""

    def messages(self) -> FakeMessages:
        return FakeMessages()


class FakeGmailService:
    """Mock the Gmail API service."""

    def users(self) -> FakeUsers:
        return FakeUsers()


def test_search_gmail_returns_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gmail_module,
        "_get_gmail_credentials",
        lambda: object(),
    )
    monkeypatch.setattr(
        gmail_module,
        "build",
        lambda *args, **kwargs: FakeGmailService(),
    )

    results = gmail_module.search_gmail(
        "subject:relatorio",
        max_results=5,
    )

    assert len(results) == 1
    assert results[0]["subject"] == "Relatório mensal"
    assert results[0]["from"] == "equipe@example.com"
    assert results[0]["body"] == "Relatório de vendas"


def test_search_gmail_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        gmail_module.search_gmail("  ")


def test_search_gmail_rejects_long_query() -> None:
    with pytest.raises(ValueError, match="too long"):
        gmail_module.search_gmail("a" * 501)


@pytest.mark.parametrize("limit", [0, 21, -1])
def test_search_gmail_rejects_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 20"):
        gmail_module.search_gmail("subject:relatorio", max_results=limit)


def test_search_gmail_rejects_boolean_limit() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        gmail_module.search_gmail("subject:relatorio", max_results=True)


def test_gmail_credentials_require_read_only_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = SimpleNamespace(
        gmail_read_only=False,
        gmail_token_file=tmp_path / "token.json",
        gmail_client_secrets_file=tmp_path / "client-secrets.json",
    )

    monkeypatch.setattr(gmail_module, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match="read-only"):
        gmail_module._get_gmail_credentials()
