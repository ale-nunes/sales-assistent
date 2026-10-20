"""Tests for deterministic sales analytics."""

from pathlib import Path

import pandas as pd
import pytest

from researchmind.tools.sales_analytics import (
    get_sales_metrics,
    rank_sales,
)


def create_test_dataset(path: Path) -> None:
    """Create a small dataset with the required sales columns."""
    data = pd.DataFrame(
        {
            "Categoria": ["Móveis", "Tecnologia", "Móveis"],
            "Nome do Produto": ["Mesa", "Monitor", "Cadeira"],
            "Valor da venda": [100.0, 300.0, 200.0],
            "Lucro": [20.0, 60.0, 30.0],
            "Quantidade": [2, 3, 4],
            "Código Nota Fiscal": ["NF-1", "NF-2", "NF-1"],
        }
    )
    data.to_csv(path, sep=";", index=False, encoding="utf-8-sig")


def test_get_sales_metrics(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)

    result = get_sales_metrics(path)

    assert result["rows_analyzed"] == 3
    assert result["total_sales"] == pytest.approx(600.0)
    assert result["total_profit"] == pytest.approx(110.0)
    assert result["total_quantity"] == 9
    assert result["average_sale"] == pytest.approx(200.0)
    assert result["invoice_count"] == 2


def test_rank_sales_by_category(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)

    result = rank_sales("Categoria", metric="sales", file_path=path)

    assert result[0] == {
        "group": "Móveis",
        "metric": "sales",
        "value": 300.0,
    }
    assert result[1] == {
        "group": "Tecnologia",
        "metric": "sales",
        "value": 300.0,
    }


def test_rank_sales_by_quantity(tmp_path: Path) -> None:
    path = tmp_path / "BaseVendas.csv"
    create_test_dataset(path)

    result = rank_sales(
        "Nome do Produto",
        metric="quantity",
        limit=2,
        file_path=path,
    )

    assert len(result) == 2
    assert result[0]["group"] == "Cadeira"
    assert result[0]["value"] == 4


def test_rank_sales_rejects_unsupported_column() -> None:
    with pytest.raises(ValueError, match="Unsupported grouping column"):
        rank_sales("Senha")


def test_rank_sales_rejects_unsupported_metric() -> None:
    with pytest.raises(ValueError, match="Unsupported metric"):
        rank_sales("Categoria", metric="discount")


@pytest.mark.parametrize("limit", [0, 101, -1])
def test_rank_sales_rejects_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        rank_sales("Categoria", limit=limit)


def test_rank_sales_rejects_boolean_limit() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        rank_sales("Categoria", limit=True)
