# Architecture overview

The application has two user-facing channels: Telegram for chat-first research requests and Streamlit for a companion dashboard. LangGraph will coordinate the Planner, Retriever, Analyst, Critic, and Writer agents.

The retrieval layer will combine ChromaDB semantic search with SQLite FTS5 keyword search. SQLite will also store notes, cache metadata, conversation references, and audit events. Gmail will use OAuth with read-only scope by default. Draft creation is a future, separately gated capability; automatic sending is out of scope.

## Phase boundaries

- Phase 2: configuration, dependency management, package structure, tests, CI baseline.
- Phase 3: document ingestion, chunking, embeddings, cache, hybrid retrieval.
- Phase 4: validated tools.
- Phase 5: agents, schemas, Supervisor and LangGraph routing.
- Phase 6: Telegram and Streamlit workflows.
- Phase 7: tests and evaluation.
- Phase 8: CI hardening.
- Phase 9: free deployment validation.
- Phase 10: final README and publication.
