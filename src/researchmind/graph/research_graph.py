"""Main LangGraph workflow for sales and Gmail questions."""

import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from researchmind.graph.sales_graph import create_sales_graph
from researchmind.integrations.gemini import generate_grounded_answer
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


def _build_gmail_query(
    question: str,
    today: date | None = None,
) -> str:
    """Convert supported Portuguese requests to Gmail search queries."""
    normalized = _normalize(question)
    current_date = today or date.today()
    query_parts: list[str] = []

    # Date filters.
    if "ontem" in normalized:
        yesterday = current_date - timedelta(days=1)
        start_date = yesterday.strftime("%Y/%m/%d")
        end_date = current_date.strftime("%Y/%m/%d")
        query_parts.append(f"after:{start_date} before:{end_date}")
    elif "hoje" in normalized:
        tomorrow = current_date + timedelta(days=1)
        start_date = current_date.strftime("%Y/%m/%d")
        end_date = tomorrow.strftime("%Y/%m/%d")
        query_parts.append(f"after:{start_date} before:{end_date}")

    # Sender filter.
    sender_match = re.search(
        r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b",
        question,
    )
    if sender_match:
        query_parts.append(f"from:{sender_match.group(0)}")

    # Subject filter.
    subject_match = re.search(
        r"(?:assunto|com o assunto)\s+['\"]?(.+?)['\"]?$",
        question,
        flags=re.IGNORECASE,
    )
    if subject_match:
        subject = subject_match.group(1).strip().strip("'\"")
        if subject:
            query_parts.append(f"subject:({subject})")

    # Content filter when the user explicitly specifies a term.
    content_match = re.search(
        r"(?:mencionam|menciona|cont[eê]m|contendo|palavra|termo)"
        r"\s+['\"]?(.+?)['\"]?$",
        question,
        flags=re.IGNORECASE,
    )
    if content_match:
        term = content_match.group(1).strip().strip("'\"")
        if term:
            query_parts.append(f'"{term}"')

    if query_parts:
        return " ".join(query_parts)

    raise ValueError(
        "Não consegui transformar a pergunta em uma busca Gmail segura. "
        "Informe um período, endereço do remetente, assunto ou termo "
        "explícito. Exemplos: 'E-mails de hoje', "
        "'E-mails de joao@empresa.com', "
        "'E-mails com assunto orçamento' ou "
        "'E-mails que mencionam pagamento'."
    )


def _format_gmail_results(
    messages: list[dict[str, str]],
) -> str:
    """Format Gmail search results for display."""
    if not messages:
        return "Nenhum e-mail encontrado com os critérios informados."

    sections: list[str] = []

    for index, message in enumerate(messages, start=1):
        sections.append(
            f"**E-mail {index}**\n\n"
            f"- **Assunto:** "
            f"{message.get('subject') or '(sem assunto)'}\n"
            f"- **De:** "
            f"{message.get('from') or 'Não informado'}\n"
            f"- **Data:** "
            f"{message.get('date') or 'Não informada'}\n"
            f"- **Resumo:** "
            f"{message.get('snippet') or 'Sem resumo disponível'}"
        )

    return "\n\n".join(sections)


def _answer_with_gemini(
    question: str,
    source: str,
    evidence: str,
) -> str:
    """Use Gemini when configured, otherwise preserve the original answer."""
    try:
        answer = generate_grounded_answer(
            question=question,
            source=source,
            evidence=evidence,
        )
    except Exception:
        # Keep the deterministic result if the integration fails.
        return evidence

    return answer if answer else evidence


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
            original_answer = str(result.get("answer", ""))
            error = str(result.get("error", ""))

            if error or not original_answer.strip():
                return {
                    "source": source,
                    "answer": original_answer,
                    "error": error,
                }

            answer = _answer_with_gemini(
                question=question,
                source="base de vendas",
                evidence=original_answer,
            )

            return {
                "source": source,
                "answer": answer,
                "error": "",
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
            messages = search_gmail(
                query=query,
                max_results=10,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            return {
                "answer": "",
                "error": str(exc),
            }

        original_answer = _format_gmail_results(messages)

        answer = _answer_with_gemini(
            question=query,
            source="Gmail",
            evidence=original_answer,
        )

        return {
            "answer": answer,
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
