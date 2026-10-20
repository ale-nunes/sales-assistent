"""LangGraph workflow for questions about the authorized sales dataset."""

import unicodedata
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from researchmind.tools.sales_analytics import (
    get_sales_metrics,
    rank_sales,
)
from researchmind.tools.sales_data import DEFAULT_DATASET_PATH

GROUPS = {
    "categoria": "Categoria",
    "subcategoria": "Subcategoria",
    "regiao": "Região",
    "estado": "Estado",
    "cidade": "Cidade",
    "pais": "Pais",
    "segmento": "Segmento",
    "produto": "Nome do Produto",
    "produtos": "Nome do Produto",
    "cliente": "Customer Name",
    "clientes": "Customer Name",
    "envio": "Tipo de Envio",
}


class SalesState(TypedDict, total=False):
    """State passed between sales workflow nodes."""

    question: str
    answer: str
    error: str


def _normalize(text: str) -> str:
    """Normalize text for simple Portuguese intent matching."""
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _format_number(value: int | float) -> str:
    """Format a number using Brazilian separators."""
    formatted = f"{value:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _answer_question(
    question: str,
    file_path: str | Path,
) -> str:
    """Route a supported question to deterministic analytics."""
    normalized = _normalize(question.strip())

    if not normalized:
        return "Digite uma pergunta sobre a base de vendas."

    metrics = get_sales_metrics(file_path)

    if "lucro total" in normalized or "total de lucro" in normalized:
        return (
            f"Lucro total nas linhas analisadas: {_format_number(float(metrics['total_profit']))}."
        )

    if (
        "quantidade total" in normalized
        or "total de unidades" in normalized
        or "unidades vendidas" in normalized
    ):
        return f"Quantidade total nas linhas analisadas: {metrics['total_quantity']} unidades."

    if (
        "ticket medio" in normalized
        or "valor medio das vendas" in normalized
        or "media das vendas" in normalized
    ):
        return (
            "Valor médio por linha de venda analisada: "
            f"{_format_number(float(metrics['average_sale']))}."
        )

    if "quantas notas fiscais" in normalized or "numero de notas fiscais" in normalized:
        return f"Notas fiscais distintas nas linhas analisadas: {metrics['invoice_count']}."

    if (
        "total de vendas" in normalized
        or "valor total das vendas" in normalized
        or "faturamento total" in normalized
    ):
        return (
            "Valor total das vendas nas linhas analisadas: "
            f"{_format_number(float(metrics['total_sales']))}."
        )

    group_by = next(
        (column for keyword, column in GROUPS.items() if keyword in normalized),
        None,
    )

    is_ranking = any(
        term in normalized
        for term in (
            "maior",
            "menor",
            "mais vendido",
            "mais vendidos",
            "ranking",
            "top ",
            "por categoria",
            "por regiao",
            "por estado",
            "por cidade",
            "por produto",
            "por subcategoria",
            "por segmento",
            "por cliente",
        )
    )

    if group_by is not None and is_ranking:
        if "lucro" in normalized:
            metric = "profit"
            metric_label = "lucro"
        elif "quantidade" in normalized or "unidades" in normalized:
            metric = "quantity"
            metric_label = "quantidade"
        else:
            metric = "sales"
            metric_label = "valor de vendas"

        limit = 5 if "top 5" in normalized else 10

        results = rank_sales(
            group_by=group_by,
            metric=metric,
            limit=limit,
            file_path=file_path,
        )

        if not results:
            return "Não foram encontrados resultados para essa consulta."

        lines = []
        for index, item in enumerate(results, start=1):
            value = item["value"]

            if not isinstance(value, (int, float)):
                raise ValueError("Analytics returned a non-numeric metric value.")

            lines.append(f"{index}. {item['group']}: {_format_number(value)}")

        return (
            f"Ranking por {group_by}, ordenado por {metric_label} "
            f"(primeiras linhas autorizadas):\n" + "\n".join(lines)
        )

    return (
        "Ainda não reconheço essa pergunta. Posso consultar o total de vendas, "
        "lucro total, quantidade de unidades, valor médio, notas fiscais "
        "distintas e rankings por categoria, produto, região, estado, cidade, "
        "subcategoria, segmento ou cliente."
    )


def create_sales_graph(
    file_path: str | Path = DEFAULT_DATASET_PATH,
) -> Any:
    """Build the sales question-answering graph."""

    def answer_node(state: SalesState) -> SalesState:
        question = state.get("question", "")

        try:
            answer = _answer_question(question, file_path)
        except (OSError, ValueError, KeyError) as exc:
            return {
                "answer": "",
                "error": str(exc),
            }

        return {"answer": answer, "error": ""}

    builder = StateGraph(SalesState)
    builder.add_node("answer_sales_question", answer_node)
    builder.add_edge(START, "answer_sales_question")
    builder.add_edge("answer_sales_question", END)

    return builder.compile()
