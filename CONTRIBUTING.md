# Contributing to ResearchMind

## Development setup

Follow the setup instructions in `README.md`, then run:

```bash
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
```

## Branches

- `main`: stable, tested code.
- `feat/<short-name>`: new features.
- `fix/<short-name>`: bug fixes.
- `docs/<short-name>`: documentation changes.

## Commit convention

Use concise semantic commits:

- `feat: add hybrid document retrieval`
- `fix: respect Gemini retry-after`
- `test: cover critic routing`
- `docs: document Gmail OAuth setup`

## Pull requests

Include purpose, design notes, test commands and results, security impact, and screenshots when changing the UI. Never attach `.env`, API keys, OAuth tokens, private emails, or confidential documents.
