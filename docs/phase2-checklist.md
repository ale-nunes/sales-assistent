# Phase 2 checklist

- [ ] Python 3.11+ installed.
- [ ] Virtual environment created and activated.
- [ ] Project installed with `python -m pip install -e ".[dev]"`.
- [ ] `.env` copied from `.env.example`; secrets kept local.
- [ ] Streamlit setup dashboard opens.
- [ ] `python -m pytest` passes.
- [ ] `python -m ruff check src tests` passes.
- [ ] `python -m ruff format --check src tests` passes.
- [ ] `python -m mypy src` passes.
- [ ] `git status --ignored` confirms `.env`, `.local`, virtualenv and local data are ignored.
- [ ] No API keys, OAuth tokens, or private documents are tracked by Git.

This is a scaffold. Do not consider Telegram, Gmail, RAG, or Gemini calls functionally complete until their dedicated phases are implemented and tested.
