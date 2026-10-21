"""Main LangGraph workflow for sales and Gmail questions."""

import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from researchmind.graph.sales_graph import create_sales_graph
from researchmind.integrations.gmail import search_gmail
from researchmind.tools.sales_data import DEFAULT_DATASET_PATH


class ResearchState(TypedDict, total=False):
    """State passed between ResearchMind workflow nodes."""

    question: str
    source: str
    answer: str
    error: str


def _normalize(text: str) -> str:
    """Normalize text for Portuguese keyword matching."""
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _classify_question(question: str) -> str:
    """Classify a question as sales, Gmail, or ambiguous."""
    normalized = _normalize(question)

    gmail_keywords = (
        "email",
        "emails",
        "e-mail",
        "e-mails",
        "gmail",
        "mensagem recebida",
        "mensagens recebidas",
        "caixa de entrada",
        "remetente",
        "assunto",
    )

    sales_keywords = (
        "venda",
        "vendas",
        "faturamento",
        "lucro",
        "produto",
        "produtos",
        "categoria",
        "categorias",
        "cliente",
        "clientes",
        "quantidade vendida",
        "notas fiscais",
        "regiao",
    )

    has_gmail_keyword = any(keyword in normalized for keyword in gmail_keywords)
    has_sales_keyword = any(keyword in normalized for keyword in sales_keywords)

    if has_gmail_keyword and not has_sales_keyword:
        return "gmail"

    if has_sales_keyword and not has_gmail_keyword:
        return "sales"

    return "ambiguous"


def _build_gmail_query(question: str, today: date | None = None) -> str:
    """Convert supported Portuguese requests to safe Gmail search queries."""
    normalized = _normalize(question)
    current_date = today or date.today()

    if "ontem" in normalized:
        yesterday = current_date - timedelta(days=1)
        start_date = yesterday.strftime("%Y/%m/%d")
        end_date = current_date.strftime("%Y/%m/%d")
        return f"after:{start_date} before:{end_date}"

    if "hoje" in normalized:
        tomorrow = current_date + timedelta(days=1)
        start_date = current_date.strftime("%Y/%m/%d")
        end_date = tomorrow.strftime("%Y/%m/%d")
        return f"after:{start_date} before:{end_date}"

    sender_match = re.search(
        r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b",
        question,
    )
    if sender_match:
        return f"from:{sender_match.group(0)}"

    subject_match = re.search(
        r"(?:assunto|sobre|com o assunto)\s+['\"]?(.+?)['\"]?$",
        question,
        flags=re.IGNORECASE,
    )
    if subject_match:
        subject = subject_match.group(1).strip().strip("'\"")
        if subject:
            return f"subject:{subject}"

    raise ValueError(
        "Não consegui transformar a pergunta em uma busca Gmail segura. "
        "Informe se deseja pesquisar por data, endereço do remetente "
        "ou assunto. Ex.: 'E-mails de hoje', "
        "'E-mails de joao@empresa.com' ou "
        "'E-mails com assunto orçamento'."
    )


def _format_gmail_results(messages: list[dict[str, str]]) -> str:
    """Format Gmail search results for display."""
    if not messages:
        return "Nenhum e-mail encontrado com os critérios informados."

    sections: list[str] = []

    for index, message in enumerate(messages, start=1):
        sections.append(
            f"**E-mail {index}**\n\n"
            f"- **Assunto:** {message.get('subject') or '(sem assunto)'}\n"
            f"- **De:** {message.get('from') or 'Não informado'}\n"
            f"- **Data:** {message.get('date') or 'Não informada'}\n"
            f"- **Resumo:** {message.get('snippet') or 'Sem resumo disponível'}"
        )

    return "\n\n".join(sections)


def create_research_graph(
    file_path: str | Path = DEFAULT_DATASET_PATH,
) -> Any:
    """Build the main ResearchMind question-routing graph."""
    sales_graph = create_sales_graph(file_path)

    def route_question(state: ResearchState) -> ResearchState:
        question = state.get("question", "").strip()

        if not question:
            return {
                "source": "ambiguous",
                "answer": "Digite uma pergunta sobre vendas ou e-mails.",
                "error": "",
            }

        source = _classify_question(question)

        if source == "ambiguous":
            return {
                "source": source,
                "answer": (
                    "Não consegui identificar a fonte da consulta. "
                    "Informe se sua pergunta é sobre a base de vendas "
                    "ou sobre seus e-mails."
                ),
                "error": "",
            }

        if source == "sales":
            result = sales_graph.invoke({"question": question})
            return {
                "source": source,
                "answer": str(result.get("answer", "")),
                "error": str(result.get("error", "")),
            }

        try:
            query = _build_gmail_query(question)
        except ValueError as exc:
            return {
                "source": "gmail",
                "answer": str(exc),
                "error": "",
            }

        return {
            "source": "gmail",
            "answer": "",
            "error": "",
            "question": query,
        }

    def search_gmail_node(state: ResearchState) -> ResearchState:
        query = state.get("question", "")

        try:
            messages = search_gmail(query=query, max_results=10)
        except (OSError, RuntimeError, ValueError) as exc:
            return {"answer": "", "error": str(exc)}

        return {
            "answer": _format_gmail_results(messages),
            "error": "",
        }

    builder = StateGraph(ResearchState)
    builder.add_node("route_question", route_question)
    builder.add_node("search_gmail", search_gmail_node)

    builder.add_edge(START, "route_question")
    builder.add_conditional_edges(
        "route_question",
        lambda state: (
            "search_gmail"
            if state.get("source") == "gmail" and not state.get("error") and not state.get("answer")
            else END
        ),
        {
            "search_gmail": "search_gmail",
            END: END,
        },
    )
    builder.add_edge("search_gmail", END)

    return builder.compile()
