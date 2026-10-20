"""Deterministic analytics over the authorized sales dataset."""

from pathlib import Path

from researchmind.tools.sales_data import (
    DEFAULT_DATASET_PATH,
    load_sales_data,
)

METRICS = {
    "sales": "Valor da venda",
    "profit": "Lucro",
    "quantity": "Quantidade",
}

GROUP_BY_COLUMNS = {
    "Categoria",
    "Subcategoria",
    "Região",
    "Estado",
    "Cidade",
    "Pais",
    "Segmento",
    "Nome do Produto",
    "Tipo de Envio",
    "Status do Envio",
    "Customer Name",
}


def get_sales_metrics(
    file_path: str | Path = DEFAULT_DATASET_PATH,
) -> dict[str, int | float]:
    """Calculate overall metrics using only the authorized dataset."""
    data = load_sales_data(file_path)

    return {
        "rows_analyzed": len(data),
        "total_sales": float(data["Valor da venda"].sum()),
        "total_profit": float(data["Lucro"].sum()),
        "total_quantity": int(data["Quantidade"].sum()),
        "average_sale": float(data["Valor da venda"].mean()),
        "invoice_count": int(data["Código Nota Fiscal"].nunique()),
    }


def rank_sales(
    group_by: str,
    metric: str = "sales",
    limit: int = 10,
    file_path: str | Path = DEFAULT_DATASET_PATH,
) -> list[dict[str, str | int | float]]:
    """Rank groups by sales, profit, or quantity."""
    if group_by not in GROUP_BY_COLUMNS:
        raise ValueError(f"Unsupported grouping column: {group_by}.")

    if metric not in METRICS:
        raise ValueError("Unsupported metric. Use 'sales', 'profit', or 'quantity'.")

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    data = load_sales_data(file_path)
    metric_column = METRICS[metric]

    grouped = (
        data.groupby(group_by, dropna=False)[metric_column]
        .sum()
        .sort_values(ascending=False)
        .head(limit)
    )

    results: list[dict[str, str | int | float]] = []

    for name, value in grouped.items():
        if metric == "quantity":
            numeric_value: int | float = int(value)
        else:
            numeric_value = float(value)

        results.append(
            {
                "group": str(name),
                "metric": metric,
                "value": numeric_value,
            }
        )

    return results
