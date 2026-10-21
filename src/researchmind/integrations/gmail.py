"""Read-only Gmail integration for ResearchMind."""

import base64
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from researchmind.config import get_settings

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
MAX_RESULTS_LIMIT = 20
MAX_QUERY_LENGTH = 500


def _get_gmail_credentials() -> Credentials:
    """Load or create credentials restricted to Gmail read-only access."""
    settings = get_settings()

    if not settings.gmail_read_only:
        raise RuntimeError("Gmail integration is restricted to read-only mode.")

    token_path = Path(settings.gmail_token_file)
    secrets_path = Path(settings.gmail_client_secrets_file)

    if not secrets_path.is_file():
        raise FileNotFoundError(
            "Gmail OAuth client secrets were not found. "
            "Configure the client secrets file in the secrets directory."
        )

    token_path.parent.mkdir(parents=True, exist_ok=True)

    credentials: Credentials | None = None

    if token_path.is_file():
        credentials = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
            str(token_path),
            scopes=[GMAIL_READONLY_SCOPE],
        )

        existing_scopes = credentials.scopes or []

        if GMAIL_READONLY_SCOPE not in existing_scopes:
            credentials = None

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())  # type: ignore[no-untyped-call]

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(secrets_path),
            scopes=[GMAIL_READONLY_SCOPE],
        )
        credentials = flow.run_local_server(port=0)

    if GMAIL_READONLY_SCOPE not in (credentials.scopes or []):
        raise RuntimeError(
            "Gmail credentials do not have the required read-only scope. "
            "Reauthorize the application."
        )

    token_path.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    return credentials


def _decode_body(data: str) -> str:
    """Decode a Gmail URL-safe Base64 message body."""
    decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
    return decoded.decode("utf-8", errors="replace")


def _extract_plain_text(payload: dict[str, Any]) -> str:
    """Extract plain-text content from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return _decode_body(data)

    parts = payload.get("parts", [])

    for part in parts:
        extracted = _extract_plain_text(part)
        if extracted:
            return extracted

    return ""


def search_gmail(
    query: str,
    max_results: int = 10,
) -> list[dict[str, str]]:
    """Search Gmail and return message metadata and plain-text content."""
    query = query.strip()

    if not query:
        raise ValueError("Gmail search query cannot be empty.")

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("Gmail search query is too long.")

    if isinstance(max_results, bool) or not isinstance(max_results, int):
        raise ValueError("max_results must be an integer.")

    if not 1 <= max_results <= MAX_RESULTS_LIMIT:
        raise ValueError(f"max_results must be between 1 and {MAX_RESULTS_LIMIT}.")

    credentials = _get_gmail_credentials()

    service = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results,
        )
        .execute()
    )

    messages = response.get("messages", [])
    results: list[dict[str, str]] = []

    for message_ref in messages:
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message_ref["id"],
                format="full",
            )
            .execute()
        )

        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        header_map = {
            str(header.get("name", "")).lower(): str(header.get("value", "")) for header in headers
        }

        body = _extract_plain_text(payload)
        if not body:
            body = str(message.get("snippet", ""))

        results.append(
            {
                "id": str(message.get("id", "")),
                "thread_id": str(message.get("threadId", "")),
                "from": header_map.get("from", ""),
                "to": header_map.get("to", ""),
                "subject": header_map.get("subject", "(sem assunto)"),
                "date": header_map.get("date", ""),
                "snippet": str(message.get("snippet", "")),
                "body": body,
            }
        )

    return results
