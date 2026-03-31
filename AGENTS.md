# AGENTS.md

Workflow guidelines for AI agents working in this project.

## Instruction Hierarchy

- This file is the project-wide baseline.
- Greenfield execution guidance lives in `plans/greenfield/AGENTS.md`.
- Feature execution guidance lives in `features/<name>/AGENTS.md`.
- When working in a scoped directory, follow this file first, then the local
  `AGENTS.md` or `CLAUDE.md` in that directory.

## Project Context

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy/Alembic for backend API, PostgreSQL 16, React 18 + TypeScript + Vite + Tailwind/shadcn/ui for frontend, Docker Compose for deployment.

**Dev Server:** `docker compose up` → backend at `http://localhost:8000`, frontend at `http://localhost:80` (wait 10s for startup)

## Core Workflow

1. Load the nearest scoped instructions for the area you are editing.
2. Read the relevant specification and execution-plan documents before changing code.
3. Confirm dependencies and existing patterns before implementing.
4. Make the smallest change that satisfies the active task.
5. Add or update tests when behavior changes.
6. Run configured verification before reporting completion.
7. Update execution-plan checkboxes when scoped work requires it.
8. Commit using the project task format after verification passes.

## Guardrails

- Do not invent requirements that are not in the active spec or plan.
- Do not skip, disable, or misreport failing tests.
- Do not rewrite or revert unrelated user changes.
- Do not introduce new dependencies or APIs without noting the impact.
- If access, secrets, or requirements are missing, stop and ask.

## Verification

- Use `.claude/verification-config.json` when it exists.
- If scoped instructions define additional verification steps, follow them.
- If verification metadata is missing from an execution plan, add it before proceeding.

## Git Conventions

- Work on phase branches for execution-plan work.
- Create one commit per completed task after verification passes.
- Commit format: `task({id}): {description} [REQ-XXX]`
- If no requirement ID applies, omit the bracketed suffix.
- Use `/create-pr` instead of ad hoc PR formatting when available.

## Follow-Up Items

- Track out-of-scope issues in `TODOS.md` instead of silently dropping them.
- Capture durable project patterns in `LEARNINGS.md` when they will help future work.

## Completion Report

When finishing a task, report:
- what changed
- files touched
- verification status
- commit hash
