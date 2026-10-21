"""Tests for the main ResearchMind graph."""

from pathlib import Path

import pytest

from researchmind.graph import research_graph as research_graph_module


class FakeSalesGraph:
    """Minimal sales graph fake for routing tests."""

    def invoke(self, state: dict[str, str]) -> dict[str, str]:
        """Return a predictable sales answer."""
        question = state["question"]

        if "faturamento" in question.casefold():
            return {
                "answer": "Faturamento total: 127.567,69.",
                "error": "",
            }

        return {
            "answer": "Resposta simulada sobre vendas.",
            "error": "",
        }


def test_graph_routes_sales_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Route sales questions and preserve the grounded answer."""
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )
    monkeypatch.setattr(
        research_graph_module,
        "generate_grounded_answer",
        lambda **kwargs: None,
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "Qual foi o faturamento total?"})

    assert result["source"] == "sales"
    assert result["answer"] == "Faturamento total: 127.567,69."
    assert result["error"] == ""


def test_graph_handles_empty_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Return a helpful message when the question is empty."""
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "   "})

    assert result["source"] == "ambiguous"
    assert "Digite uma pergunta" in result["answer"]


def test_graph_handles_ambiguous_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ask for clarification when the source cannot be identified."""
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "O que aconteceu recentemente?"})

    assert result["source"] == "ambiguous"
    assert "base de vendas" in result["answer"]
    assert "e-mails" in result["answer"]


def test_graph_routes_gmail_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Route Gmail questions to the Gmail search node."""
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )
    monkeypatch.setattr(
        research_graph_module,
        "search_gmail",
        lambda query, max_results: [
            {
                "subject": "Orçamento",
                "from": "joao@example.com",
                "date": "20 Oct 2026",
                "snippet": "Solicitação de orçamento",
            }
        ],
    )
    monkeypatch.setattr(
        research_graph_module,
        "generate_grounded_answer",
        lambda **kwargs: None,
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "E-mails de hoje"})

    assert result["source"] == "gmail"
    assert "Orçamento" in result["answer"]
    assert "joao@example.com" in result["answer"]
    assert result["error"] == ""


def test_graph_handles_invalid_gmail_query(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Return a helpful message for unsupported Gmail searches."""
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "E-mails importantes"})

    assert result["source"] == "gmail"
    assert "Não consegui transformar" in result["answer"]


def test_graph_handles_gmail_search_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Expose a controlled error when Gmail search fails."""
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    def raise_error(
        query: str,
        max_results: int,
    ) -> list[dict[str, str]]:
        raise RuntimeError("Falha simulada no Gmail")

    monkeypatch.setattr(
        research_graph_module,
        "search_gmail",
        raise_error,
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "E-mails de hoje"})

    assert result["source"] == "gmail"
    assert result["error"] == "Falha simulada no Gmail"
