"""Optional FastAPI health endpoint; no external integrations are called in Phase 2."""

from fastapi import FastAPI

app = FastAPI(title="ResearchMind API", version="0.2.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a basic liveness response."""
    return {"status": "ok", "phase": "2"}
