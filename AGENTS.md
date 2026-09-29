# AGENTS.md

Project-wide guidance for AI agents working on Microsoft Vibe.

- Stack: Python with FastAPI and SQLAlchemy/Alembic, PostgreSQL, React,
  TypeScript, Vite, Tailwind/shadcn, and Docker Compose.
- `docker compose up` serves the API at `http://localhost:8000` and frontend at
  `http://localhost:80`.
- Existing plans are historical product and architecture context, not a
  mandatory workflow or authorization boundary.
- Follow the user's current request and the nearest scoped project instructions.
- Make the smallest change that satisfies the request and preserve unrelated work.
- Add or update tests for behavior changes; do not skip or misreport failures.
- Call out new dependencies, APIs, credentials, or security-sensitive changes.
- Track out-of-scope work in `TODOS.md` and durable patterns in `LEARNINGS.md`.

Run repository-native verification proportionate to the change. Treat
instruction, automation, CI, database, and security files as high-impact
configuration.
