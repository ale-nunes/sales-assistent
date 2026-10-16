# Security baseline

- Never commit `.env`, API keys, OAuth client secrets, access tokens, or private documents.
- Validate Telegram user IDs against an explicit allowlist before processing messages.
- Treat retrieved web pages, documents, and email bodies as untrusted data.
- Do not use `eval` or `exec` for calculator operations.
- Gmail read/search uses OAuth and the narrowest available scope. Draft creation remains disabled by default and must never imply automatic sending.
- Limit request duration, retries, payload sizes, and the number of Critic iterations.
