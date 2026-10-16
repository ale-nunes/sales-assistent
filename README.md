# ResearchMind

[![CI](https://github.com/OWNER/REPOSITORY/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPOSITORY/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

ResearchMind is a multi-agent research assistant designed to retrieve evidence from private documents, search the web, analyze sources, and produce Markdown reports with traceable citations. Telegram is the primary chat interface, with Streamlit as a companion dashboard.

> **Current milestone: Phase 2 scaffold.** This phase establishes the project structure, configuration, development tooling, CI, and a minimal Streamlit setup screen. RAG, tools, agents, Telegram workflow, and Gmail integration are implemented in later phases.

## Planned capabilities

- Multi-agent orchestration with LangGraph and Pydantic output schemas.
- Gemini generation and embeddings via the official `google-genai` SDK.
- Hybrid retrieval: ChromaDB vector search + SQLite FTS5 keyword search.
- PDF, TXT, and Markdown ingestion with source metadata.
- Web search using `ddgs`.
- Safe calculator and persistent notes.
- Telegram interaction and a Streamlit dashboard.
- Gmail search/read using OAuth; draft creation may be added later but sending is not automatic.
- Citation validation, retry/backoff, caching, structured logs, evaluation, and CI.

## Requirements

- Python 3.11 or newer.
- Git.
- A Google AI Studio API key for Gemini calls in later phases.
- Telegram bot token for Telegram integration in a later phase.
- Gmail OAuth credentials only when Gmail integration is implemented.

The exact Gemini models and quotas vary by project and account. Check the current model list and active quotas before running model calls or large ingestion jobs. The configured model names are environment variables so they can be changed without editing source code.

## Setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` locally only when needed. Do not paste real secrets into source files, tests, README files, or GitHub issues.

## Setup (macOS/Linux)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

## Run the Phase 2 dashboard

```powershell
python -m streamlit run src/researchmind/ui/streamlit_app.py
```

The dashboard checks the configuration without displaying API keys. It does not yet call Gemini or Telegram; those integrations are intentionally deferred to later phases.

## Validate the environment

```powershell
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
```

## Project layout

```text
src/researchmind/
├── agents/          # Planner, Retriever, Analyst, Critic, Writer
├── api/             # Optional FastAPI endpoints and webhook
├── graph/           # LangGraph state, nodes, routing, workflow
├── integrations/    # Telegram and Gmail OAuth clients
├── rag/             # Ingestion, chunking, embeddings, retrieval, reranking
├── schemas/         # Pydantic contracts and evidence models
├── storage/         # SQLite memory, cache, audit logs
├── tools/           # Documents, web, calculator, URL summary, notes, Gmail
├── ui/              # Streamlit dashboard
├── config.py        # Environment-driven settings
└── logging_config.py
```

## Security notes

- `.env`, OAuth tokens, credentials, local databases, and vector indexes are excluded from Git.
- Gmail starts with read-only access. Draft creation is disabled by default; sending messages is not part of the initial implementation.
- Only allowlisted Telegram user IDs will be authorized when Telegram access is implemented.
- Retrieved documents, emails, and web pages are untrusted data, never system instructions.
- The calculator will use a restricted parser rather than `eval` or `exec`.

## Gemini documentation checked

- Models: https://ai.google.dev/gemini-api/docs/models
- Embeddings: https://ai.google.dev/gemini-api/docs/embeddings
- Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Official SDK: https://pypi.org/project/google-genai/

The model IDs in `.env.example` are defaults, not a promise that every model has free quota in every project. Verify active availability in Google AI Studio.

## Contribution workflow

See [CONTRIBUTING.md](CONTRIBUTING.md). Use semantic commits such as `feat: add document ingestion`, `fix: handle Gemini quota errors`, and `docs: clarify setup`.

## License

MIT. See [LICENSE](LICENSE).
