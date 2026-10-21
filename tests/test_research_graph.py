"""Tests for the main ResearchMind graph."""

from pathlib import Path
from typing import Any

import pytest

import researchmind.graph.research_graph as research_graph_module


class FakeSalesGraph:
    """Mock the sales graph."""

    def invoke(self, state: dict[str, str]) -> dict[str, str]:
        assert state["question"] == "Qual foi o faturamento total?"
        return {
            "answer": "Faturamento total: 127.567,69.",
            "error": "",
        }


def test_classify_sales_question() -> None:
    assert research_graph_module._classify_question("Qual foi o faturamento total?") == "sales"


def test_classify_gmail_question() -> None:
    assert research_graph_module._classify_question("Quais e-mails recebi ontem?") == "gmail"


def test_classify_ambiguous_question() -> None:
    assert research_graph_module._classify_question("Olá, pode me ajudar?") == "ambiguous"


def test_graph_routes_sales_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "Qual foi o faturamento total?"})

    assert result["source"] == "sales"
    assert result["answer"] == "Faturamento total: 127.567,69."
    assert result["error"] == ""


def test_graph_asks_for_clarification_on_ambiguous_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "Olá, pode me ajudar?"})

    assert result["source"] == "ambiguous"
    assert "não consegui identificar" in result["answer"].casefold()
    assert result["error"] == ""


def test_graph_routes_gmail_question(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        research_graph_module,
        "create_sales_graph",
        lambda file_path: FakeSalesGraph(),
    )

    captured: dict[str, Any] = {}

    def fake_search_gmail(
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, str]]:
        captured["query"] = query
        captured["max_results"] = max_results
        return [
            {
                "subject": "Orçamento",
                "from": "joao@example.com",
                "date": "Mon, 19 Oct 2026 10:00:00 -0300",
                "snippet": "Segue o orçamento solicitado.",
            }
        ]

    monkeypatch.setattr(
        research_graph_module,
        "search_gmail",
        fake_search_gmail,
    )

    graph = research_graph_module.create_research_graph(tmp_path / "sales.csv")
    result = graph.invoke({"question": "Quais e-mails recebi ontem?"})

    assert result["source"] == "gmail"
    assert captured["query"].startswith("after:")
    assert "before:" in captured["query"]

    assert captured["max_results"] == 10
    assert "Orçamento" in result["answer"]
    assert result["error"] == ""
