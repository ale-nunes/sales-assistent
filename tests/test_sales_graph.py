"""Tests for the sales LangGraph workflow."""

from pathlib import Path

import pandas as pd

from researchmind.graph.sales_graph import create_sales_graph


def create_test_dataset(path: Path) -> None:
    """Create a small dataset for graph tests."""
    pd.DataFrame(
        {
            "Categoria": ["Móveis", "Tecnologia", "Móveis"],
            "Nome do Produto": ["Mesa", "Monitor", "Cadeira"],
            "Valor da venda": [100.0, 300.0, 200.0],
            "Lucro": [20.0, 60.0, 30.0],
            "Quantidade": [2, 3, 4],
            "Código Nota Fiscal": ["NF-1", "NF-2", "NF-1"],
        }
    ).to_csv(path, sep=";", index=False, encoding="utf-8-sig")


def test_graph_answers_total_sales(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)
    graph = create_sales_graph(path)

    result = graph.invoke({"question": "Qual foi o total de vendas?"})

    assert "600,00" in result["answer"]
    assert result["error"] == ""


def test_graph_answers_total_profit(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)
    graph = create_sales_graph(path)

    result = graph.invoke({"question": "Qual foi o lucro total?"})

    assert "110,00" in result["answer"]
    assert result["error"] == ""


def test_graph_ranks_categories_by_profit(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)
    graph = create_sales_graph(path)

    result = graph.invoke({"question": "Qual categoria teve maior lucro?"})

    assert "Tecnologia" in result["answer"]
    assert "60,00" in result["answer"]


def test_graph_ranks_products_by_quantity(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)
    graph = create_sales_graph(path)

    result = graph.invoke({"question": "Quais são os 5 produtos mais vendidos por quantidade?"})

    assert "Cadeira" in result["answer"]
    assert result["error"] == ""


def test_graph_handles_unknown_question(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)
    graph = create_sales_graph(path)

    result = graph.invoke({"question": "Qual é a previsão para amanhã?"})

    assert "Ainda não reconheço" in result["answer"]


def test_graph_handles_empty_question(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)
    graph = create_sales_graph(path)

    result = graph.invoke({"question": "   "})

    assert "Digite uma pergunta" in result["answer"]
