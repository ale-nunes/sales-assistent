"""Tests for the ResearchMind sales dataset tool."""

import pandas as pd
import pytest

from researchmind.tools.sales_data import (
    get_sales_data_summary,
    load_sales_data,
)


def test_load_sales_data_reads_only_first_1000_rows(
    tmp_path: pytest.TempPathFactory,
) -> None:
    path = tmp_path / "BaseVendas.csv"
    source = pd.DataFrame(
        {
            "Nome do Produto": [f"Produto {index}" for index in range(1005)],
            "Valor da venda": list(range(1005)),
        }
    )
    source.to_csv(path, sep=";", index=False, encoding="utf-8-sig")

    data = load_sales_data(path)

    assert len(data) == 1000
    assert data.iloc[0]["Nome do Produto"] == "Produto 0"
    assert data.iloc[999]["Nome do Produto"] == "Produto 999"
    assert "Produto 1000" not in data["Nome do Produto"].values


def test_load_sales_data_preserves_columns(
    tmp_path: pytest.TempPathFactory,
) -> None:
    path = tmp_path / "BaseVendas.csv"
    source = pd.DataFrame(
        {
            "Categoria": ["Móveis"],
            "Nome do Produto": ["Mesa"],
            "Valor da venda": [250.0],
        }
    )
    source.to_csv(path, sep=";", index=False, encoding="utf-8-sig")

    data = load_sales_data(path)

    assert data.columns.tolist() == [
        "Categoria",
        "Nome do Produto",
        "Valor da venda",
    ]


def test_load_sales_data_rejects_missing_file(
    tmp_path: pytest.TempPathFactory,
) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_sales_data(tmp_path / "missing.csv")


def test_load_sales_data_rejects_empty_file(
    tmp_path: pytest.TempPathFactory,
) -> None:
    path = tmp_path / "BaseVendas.csv"
    pd.DataFrame(columns=["Categoria"]).to_csv(path, sep=";", index=False, encoding="utf-8-sig")

    with pytest.raises(ValueError, match="no data rows"):
        load_sales_data(path)


def test_get_sales_data_summary(
    tmp_path: pytest.TempPathFactory,
) -> None:
    path = tmp_path / "BaseVendas.csv"
    pd.DataFrame(
        {
            "Categoria": ["Móveis", "Tecnologia"],
            "Valor da venda": [100.0, 200.0],
        }
    ).to_csv(path, sep=";", index=False, encoding="utf-8-sig")

    summary = get_sales_data_summary(path)

    assert summary["rows"] == 2
    assert summary["columns"] == ["Categoria", "Valor da venda"]
    assert "float" in summary["column_types"]["Valor da venda"]
