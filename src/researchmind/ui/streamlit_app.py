"""Streamlit dashboard for ResearchMind sales queries."""

import logging

import streamlit as st

from researchmind.config import get_settings
from researchmind.graph.research_graph import create_research_graph

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="ResearchMind",
    page_icon="🔎",
    layout="wide",
)

settings = get_settings()

st.title("ResearchMind")
st.caption("Assistente inteligente para consulta à base de vendas")

st.info(
    "Vendas: consultas limitadas às primeiras 1.000 linhas de BaseVendas.csv. "
    "Gmail: pesquisa de mensagens com acesso somente para leitura. "
    "Nenhuma pesquisa na internet é realizada."
)

st.subheader("Consulte suas fontes autorizadas")

st.write("Faça perguntas sobre a base de vendas ou sobre seus e-mails do Gmail.")

with st.form("sales_question_form"):
    question = st.text_input(
        "Sua pergunta",
        placeholder="Ex.: Qual categoria teve maior lucro?",
    )
    submitted = st.form_submit_button(
        "Consultar",
        type="primary",
        use_container_width=True,
    )

if "sales_history" not in st.session_state:
    st.session_state.sales_history = []

if submitted:
    if not question.strip():
        st.warning("Digite uma pergunta antes de consultar.")
    else:
        try:
            graph = create_research_graph()
            result = graph.invoke({"question": question.strip()})

            if result.get("error"):
                logger.warning(
                    "Sales graph returned an error: %s",
                    result["error"],
                )
                st.error(
                    "Não foi possível concluir a consulta. "
                    "Verifique se a base está disponível e tente novamente."
                )
            else:
                answer = result.get("answer", "")

                if answer:
                    st.session_state.sales_history.insert(
                        0,
                        {
                            "question": question.strip(),
                            "answer": answer,
                        },
                    )
                    st.subheader("Resposta")
                    st.markdown(answer)
                else:
                    st.warning("Não foi possível obter uma resposta para essa pergunta.")

        except Exception:
            logger.exception("Unexpected error while querying sales data.")
            st.error(
                "Ocorreu um erro ao consultar a base. "
                "Verifique os logs do terminal para identificar o problema."
            )

if st.session_state.sales_history:
    st.divider()
    st.subheader("Histórico da sessão")

    for index, item in enumerate(st.session_state.sales_history):
        with st.expander(
            item["question"],
            expanded=(index == 0),
        ):
            st.markdown(item["answer"])

    if st.button("Limpar histórico"):
        st.session_state.sales_history = []
        st.rerun()

st.divider()

with st.expander("Configuração do ResearchMind"):
    left, right = st.columns(2)

    with left:
        st.subheader("Configuração")
        st.write(f"Ambiente: `{settings.app_env}`")
        st.write(f"Modelo de geração: `{settings.gemini_model}`")
        st.write(f"Modelo de embeddings: `{settings.gemini_embedding_model}`")
        st.write(f"Limite de iterações do crítico: `{settings.max_critic_iterations}`")

    with right:
        st.subheader("Status das credenciais")
        st.write(
            "Chave Gemini:",
            "configurada" if settings.gemini_api_key else "não configurada",
        )
        st.write(
            "Token Telegram:",
            "configurado" if settings.telegram_bot_token else "não configurado",
        )
        st.write(
            "Gmail somente leitura:",
            "habilitado" if settings.gmail_read_only else "desabilitado",
        )
        st.write(
            "Criação de rascunhos Gmail:",
            "habilitada" if settings.gmail_allow_draft_creation else "desabilitada",
        )

    st.caption("Os valores secretos nunca são exibidos nesta interface.")
