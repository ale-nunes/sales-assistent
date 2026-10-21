"""Tests for the Gemini integration without real API calls."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from pydantic import SecretStr

from researchmind.integrations import gemini


def test_returns_none_when_api_key_is_missing(
    monkeypatch,
) -> None:
    """Do not call Gemini when no API key is configured."""
    settings = SimpleNamespace(gemini_api_key=None)
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)

    result = gemini.generate_grounded_answer(
        question="Qual foi o faturamento?",
        source="base de vendas",
        evidence="Faturamento: R$ 10.000,00",
    )

    assert result is None


def test_returns_none_when_evidence_is_empty(
    monkeypatch,
) -> None:
    """Do not generate an answer without evidence."""
    settings = SimpleNamespace(
        gemini_api_key=SecretStr("test-key"),
        gemini_model="test-model",
    )
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)

    client_constructor = MagicMock()
    monkeypatch.setattr(gemini.genai, "Client", client_constructor)

    result = gemini.generate_grounded_answer(
        question="Qual foi o faturamento?",
        source="base de vendas",
        evidence="   ",
    )

    assert result is None
    client_constructor.assert_not_called()


def test_generates_answer_with_gemini(
    monkeypatch,
) -> None:
    """Return the generated answer when Gemini succeeds."""
    settings = SimpleNamespace(
        gemini_api_key=SecretStr("test-key"),
        gemini_model="test-model",
    )
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)

    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(
        text="O faturamento foi de R$ 10.000,00."
    )
    monkeypatch.setattr(
        gemini.genai,
        "Client",
        MagicMock(return_value=client),
    )

    result = gemini.generate_grounded_answer(
        question="Qual foi o faturamento?",
        source="base de vendas",
        evidence="Faturamento: R$ 10.000,00",
    )

    assert result == "O faturamento foi de R$ 10.000,00."
    client.models.generate_content.assert_called_once()


def test_returns_none_when_api_raises_exception(
    monkeypatch,
) -> None:
    """Return None when the Gemini API fails."""
    settings = SimpleNamespace(
        gemini_api_key=SecretStr("test-key"),
        gemini_model="test-model",
    )
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)

    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError("Simulated API failure")
    monkeypatch.setattr(
        gemini.genai,
        "Client",
        MagicMock(return_value=client),
    )

    result = gemini.generate_grounded_answer(
        question="Qual foi o faturamento?",
        source="base de vendas",
        evidence="Faturamento: R$ 10.000,00",
    )

    assert result is None


def test_returns_none_when_api_response_is_empty(
    monkeypatch,
) -> None:
    """Return None when Gemini produces no text."""
    settings = SimpleNamespace(
        gemini_api_key=SecretStr("test-key"),
        gemini_model="test-model",
    )
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)

    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=None)
    monkeypatch.setattr(
        gemini.genai,
        "Client",
        MagicMock(return_value=client),
    )

    result = gemini.generate_grounded_answer(
        question="Qual foi o faturamento?",
        source="base de vendas",
        evidence="Faturamento: R$ 10.000,00",
    )

    assert result is None


def test_returns_none_when_api_response_contains_only_spaces(
    monkeypatch,
) -> None:
    """Reject responses containing only whitespace."""
    settings = SimpleNamespace(
        gemini_api_key=SecretStr("test-key"),
        gemini_model="test-model",
    )
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)

    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text="   ")
    monkeypatch.setattr(
        gemini.genai,
        "Client",
        MagicMock(return_value=client),
    )

    result = gemini.generate_grounded_answer(
        question="Qual foi o faturamento?",
        source="base de vendas",
        evidence="Faturamento: R$ 10.000,00",
    )

    assert result is None
