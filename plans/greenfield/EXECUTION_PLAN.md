# Execution Plan: Agent Observability Dashboard

## Overview

| Metric | Value |
|--------|-------|
| Feature | Greenfield MVP: Agent Observability Dashboard |
| Target Project | microsoft_vibe |
| Total Phases | 7 |
| Total Steps | 14 |
| Total Tasks | 21 |

## Current Status

The following frontend tasks are **complete with mock data** (UI built, working, builds clean):
- **Task 1.1.C** — Frontend foundation (Vite, React, TypeScript, Tailwind, routing, types)
- **Task 3.2.A** — Dashboard page (StatsBar, RunsTable with TanStack Table, failure highlighting)
- **Task 3.2.B** — Utilities (formatDuration, formatTimestamp, formatRelativeTime, truncateJson)
- **Task 4.2.A** — Trace viewer page (TraceTimeline, recursive TraceStep with nested events, error highlighting)
- **Task 5.1.B** — Frontend filters (RunFilters with agent dropdown, status toggle, text search, URL state)
- **Task 6.3.A** — Alerts settings UI (AlertRuleForm, AlertRulesList with toggle/delete)
- **Task 6.3.B** — Alert history display (table with metric values, timestamps, email status)

**Remaining work:** All backend tasks (Phases 1-2 backend scaffolding, models, migrations, APIs, alert evaluation, email, retention) plus swapping mock data imports in frontend pages for real API calls via `frontend/src/api/client.ts`.

**Not yet created:** `backend/` directory, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`

## Integration Points

| Existing Component | Integration Type | Notes |
|--------------------|------------------|-------|
| PostgreSQL 16 | uses | Materializes runs, events, agents, alert rules, and alert history |
| SMTP | uses | Sends notification emails for threshold breaches |
| Docker Compose | extends | Orchestrates backend, frontend, and database services |

## Phase Dependency Graph

Phase 1 (Foundation)
  -> Phase 2 (Ingestion)
  -> Phase 3 (Run Overview)
  -> Phase 4 (Trace Viewer)
  -> Phase 5 (Search & Filtering)
  -> Phase 6 (Alerts)
  -> Phase 7 (Deployment & Hardening)

---

## Phase 1: Foundation

**Goal:** Create a runnable project skeleton with backend/frontend containers, database configuration, and shared conventions.
**Depends On:** None

### Pre-Phase Setup
Human must complete before starting:
- [ ] Confirm Docker and Python are available.
  - Verify: `docker --version`
- [ ] Confirm Node.js and npm are available.
  - Verify: `node --version && npm --version`
- [ ] Confirm PostgreSQL tooling available for local verification.
  - Verify: `psql --version`

### Step 1.1: Repository Scaffolding
**Depends On:** None

#### Task 1.1.A: Create backend and frontend project structure

**Description:**
Create top-level project structure and base files for API and UI containers.
This includes app entrypoints, dependency manifests, and Dockerfiles so later phases
can add service code without repo restructuring.

**Requirement:** None

**Acceptance Criteria:**
- [ ] (CODE) Backend and frontend directories exist with required scaffold files for a FastAPI + Vite app.
  - Verify: `test -d backend && test -d frontend`
- [ ] (CODE) Dockerfiles and top-level docker-compose file exist.
  - Verify: `test -f docker-compose.yml && test -f backend/Dockerfile && test -f frontend/Dockerfile`
- [ ] (CODE) Backend bootstrapping file exists with a mountable FastAPI app and startup path.
  - Verify: `test -f backend/app/main.py`

**Files to Create:**
- `backend/Dockerfile` — Container build config
- `backend/pyproject.toml` — Backend dependencies and metadata
- `backend/app/main.py` — FastAPI application entrypoint
- `backend/app/config.py` — Environment settings and defaults
- `frontend/Dockerfile` — Frontend build and runtime image
- `frontend/package.json` — Frontend dependencies and scripts
- `docker-compose.yml` — Full stack orchestration

**Files to Modify:**
- `plans/greenfield/EXECUTION_PLAN.md` — add references once scaffolding is done

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — architecture and stack declarations
- `plans/greenfield/PRODUCT_SPEC.md` — deployment and platform constraints

**Dependencies:**
- None

**Spec Reference:** Project Structure

**Browser Verification:**
- Criteria IDs: 1.1.A
- Notes: not applicable

#### Task 1.1.B: Configure initial backend dependencies and runtime conventions

**Description:**
Set up Poetry/pyproject dependencies required for async SQLAlchemy, migrations,
and validation, and scheduler-based background jobs.

**Requirement:** None

**Acceptance Criteria:**
- [ ] (CODE) Backend dependency manifest includes FastAPI, SQLAlchemy, asyncpg, Alembic, Pydantic v2, APScheduler, and aiosmtplib.
  - Verify: `grep -q "fastapi\|sqlalchemy\|asyncpg\|alembic\|pydantic" backend/pyproject.toml`
- [ ] (CODE) API project includes an explicit `migrate` command or script for Alembic bootstrap.
  - Verify: `grep -q "alembic" backend/pyproject.toml`
- [ ] (CODE) Backend package initializer exists.
  - Verify: `test -f backend/app/__init__.py`

**Files to Create:**
- `backend/pyproject.toml` — Pinned runtime and dev dependencies
- `backend/app/__init__.py` — Package marker
- `backend/app/config.py` — Typed settings defaults

**Files to Modify:**
- `backend/pyproject.toml` — add dependency lines
- `backend/app/config.py` — environment parsing helpers

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — dependency table
- `backend/Dockerfile` — runtime setup location

**Dependencies:**
- Task 1.1.A

**Spec Reference:** Tech Stack and assumptions

**Browser Verification:**
- Criteria IDs: none
- Notes: backend-only task

#### Task 1.1.C: Configure frontend app foundation ✅ COMPLETE

**Description:**
Initialize frontend tooling (TypeScript, Vite, Tailwind, shadcn-compatible structure)
so subsequent pages and components can be implemented in later phases.

**Requirement:** None

**Acceptance Criteria:**
- [x] (CODE) Frontend app entrypoint and root component paths exist.
  - Verify: `test -f frontend/src/main.tsx && test -f frontend/src/App.tsx`
- [x] (CODE) Router and API utility file exist to support future page navigation and data fetching.
  - Verify: `test -f frontend/src/main.tsx && test -f frontend/src/api/client.ts`
- [x] (CODE) TypeScript config and Vite config files exist.
  - Verify: `test -f frontend/tsconfig.json && test -f frontend/vite.config.ts`

**Files to Create:**
- `frontend/src/main.tsx` — App bootstrap with router
- `frontend/src/App.tsx` — Route shell
- `frontend/src/api/client.ts` — API client wrapper
- `frontend/tsconfig.json` — TS compiler settings
- `frontend/vite.config.ts` — Build/start scripts

**Files to Modify:**
- `frontend/package.json` — scripts and dependencies

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — frontend architecture and routes

**Dependencies:**
- Task 1.1.A

**Spec Reference:** Frontend architecture

**Browser Verification:**
- Criteria IDs: 1.1.C
- Notes: not applicable

### Step 1.2: Data model and migrations
**Depends On:** Step 1.1

#### Task 1.2.A: Add SQLAlchemy models for agents, runs, events, alert rules, and alert history

**Description:**
Implement core database models with constraints needed to support ingestion, dashboard,
trace, and alert features.

**Requirement:** REQ-019, REQ-002

**Acceptance Criteria:**
- [ ] (CODE) SQLAlchemy models include `agents`, `runs`, `events`, `alert_rules`, `alert_history` tables with required columns.
  - Verify: `grep -q "class Agent\|class Run\|class Event\|class AlertRule\|class AlertHistory" backend/app/models.py`
- [ ] (CODE) Run status enum or constrained string values include `running`, `success`, `failure`, and `error`.
  - Verify: `grep -q "running\|success\|failure\|error" backend/app/models.py`
- [ ] (CODE) `events` model includes `parent_step_id` and `search_vector` fields for nesting and full-text search.
  - Verify: `grep -q "parent_step_id\|search_vector" backend/app/models.py`

**Files to Create:**
- `backend/app/models.py` — SQLAlchemy model definitions

**Files to Modify:**
- `backend/app/models.py` — add constraints and index annotations

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — data model tables and indexes

**Dependencies:**
- Task 1.1.B

**Spec Reference:** Data Models, Indexes

**Browser Verification:**
- Criteria IDs: none
- Notes: DB schema task only

#### Task 1.2.B: Configure database session handling and migration baseline

**Description:**
Add async SQLAlchemy engine/session setup and Alembic migration environment so
schema changes can be managed safely through versioned migrations.

**Requirement:** REQ-019

**Acceptance Criteria:**
- [ ] (CODE) Database session factory module exists and exposes async session dependency.
  - Verify: `test -f backend/app/database.py`
- [ ] (CODE) Alembic configuration points to app metadata for autogeneration.
  - Verify: `test -f alembic.ini && test -f backend/alembic/env.py`
- [ ] (CODE) Initial migration files directory exists for tracked version history.
  - Verify: `test -d backend/alembic/versions`

**Files to Create:**
- `backend/app/database.py` — engine/session utilities
- `backend/alembic/env.py` — Alembic environment config
- `backend/alembic.ini` — Alembic configuration
- `backend/alembic/versions/.gitkeep` — version directory placeholder

**Files to Modify:**
- `backend/app/database.py` — engine/session wiring
- `backend/alembic.ini` — include metadata and DB URL

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — Alembic + SQLAlchemy assumptions

**Dependencies:**
- Task 1.2.A

**Spec Reference:** Data model and Docker DB setup

**Browser Verification:**
- Criteria IDs: none
- Notes: backend-only task

### Phase 1 Checkpoint

**Automated Checks:**
- [ ] (CODE) Backend scaffold files exist.
  - Verify: `test -d backend && test -d backend/app && test -d frontend && test -d frontend/src`
- [ ] (CODE) Frontend scaffold files exist.
  - Verify: `test -f frontend/package.json && test -f frontend/src/main.tsx`
- [ ] (CODE) Docker compose references backend and frontend services.
  - Verify: `grep -q "services:" docker-compose.yml && grep -q "backend\|frontend" docker-compose.yml`

**Regression Verification:**
- [ ] (CODE) Root plans and templates remain readable.
  - Verify: `test -f AGENTS.md && test -f plans/greenfield/AGENTS.md`

---

## Phase 2: Ingestion Pipeline

**Goal:** Implement event ingestion, schema validation, and run materialization for agent run tracking.
**Depends On:** Phase 1

### Pre-Phase Setup
Human must complete before starting:
- [ ] Ensure backend can connect to PostgreSQL with default credentials.
  - Verify: `grep -q "DATABASE_URL" backend/app/config.py`
- [ ] Ensure event schema file is aligned with spec.
  - Verify: `test -f plans/greenfield/TECHNICAL_SPEC.md`

### Step 2.1: Ingestion schemas and services
**Depends On:** None

#### Task 2.1.A: Define request/response schemas for ingestion

**Description:**
Implement Pydantic schemas for single-event and batch ingestion, including strict
validation of required fields and allowed values.

**Requirement:** REQ-001, REQ-017, REQ-018

**Acceptance Criteria:**
- [ ] (CODE) Single-event schema validates allowed `step_type` values.
  - Verify: `grep -q "step_type" backend/app/schemas.py`
- [ ] (CODE) Batch schema accepts both object and array payloads.
  - Verify: `grep -q "events" backend/app/schemas.py`
- [ ] (CODE) Metadata field is modeled as free-form JSONB-compatible data.
  - Verify: `grep -q "metadata" backend/app/schemas.py`

**Files to Create:**
- `backend/app/schemas.py` — API schema models

**Files to Modify:**
- None

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — ingestion request/response examples

**Dependencies:**
- Phase 1 completion

**Spec Reference:** Log Event Schema, API Contracts

**Browser Verification:**
- Criteria IDs: none
- Notes: backend schema task

#### Task 2.1.B: Implement ingestion processing service

**Description:**
Build service logic that upserts agents, creates and updates runs,
assigns step counts, tracks run state, and stores events with parent-child relation support.

**Requirement:** REQ-002, REQ-017, REQ-018

**Acceptance Criteria:**
- [ ] (CODE) Ingestion service inserts new agents automatically when unknown `agent_name` is seen.
  - Verify: `grep -q "upsert\|get_or_create\|agents" backend/app/services/ingest.py`
- [ ] (CODE) Run materialization updates on `run_start` and `run_end` events.
  - Verify: `grep -q "run_start\|run_end" backend/app/services/ingest.py`
- [ ] (CODE) Event persistence stores `parent_step_id` and handles optional step IDs.
  - Verify: `grep -q "parent_step_id\|step_id" backend/app/services/ingest.py`

**Files to Create:**
- `backend/app/services/ingest.py` — ingestion processing logic

**Files to Modify:**
- `backend/app/schemas.py` — use typed payload definitions
- `backend/app/models.py` — validate field names against service writes

**Existing Code to Reference:**
- `backend/app/models.py` — model field names and constraints
- `plans/greenfield/TECHNICAL_SPEC.md` — run materialization logic

**Dependencies:**
- Task 2.1.A

**Spec Reference:** Ingestion flow, Edge cases

**Browser Verification:**
- Criteria IDs: none
- Notes: service logic task

### Step 2.2: Ingestion API endpoint and tests
**Depends On:** Step 2.1

#### Task 2.2.A: Implement `/api/v1/ingest`

**Description:**
Expose endpoint for accepting one event or a batch, returning per-event validation
results for partial failures and preserving accepted/rejected counts.

**Requirement:** REQ-001, REQ-002, REQ-017, REQ-018

**Acceptance Criteria:**
- [ ] (CODE) Route `POST /api/v1/ingest` exists and is mounted under `/api/v1`.
  - Verify: `grep -q "/api/v1/ingest" backend/app/routers/ingest.py`
- [ ] (TEST) Endpoint returns HTTP 201 on valid payload and includes accepted/error structure.
  - Verify: `pytest -q backend/tests/test_ingest.py -k ingest`
- [ ] (TEST) Invalid payload returns HTTP 400 with indexed per-item error details.
  - Verify: `pytest -q backend/tests/test_ingest.py -k validation`

**Files to Create:**
- `backend/app/routers/ingest.py` — route definitions
- `backend/app/main.py` — register router
- `backend/tests/test_ingest.py` — ingestion tests

**Files to Modify:**
- `backend/app/routers/__init__.py` — expose router
- `backend/app/services/ingest.py` — endpoint-level calls

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — endpoint contract examples

**Dependencies:**
- Task 2.1.B

**Spec Reference:** Ingestion endpoint contract

**Browser Verification:**
- Criteria IDs: 2.2.A
- Notes: endpoint API check via curl is preferred over browser

### Phase 2 Checkpoint

**Automated Checks:**
- [ ] (TEST) Ingestion tests pass.
  - Verify: `pytest -q backend/tests/test_ingest.py`
- [ ] (CODE) Ingest router imports cleanly from app startup.
  - Verify: `python -m py_compile backend/app/routers/ingest.py`
- [ ] (CODE) AC schema and models are still in sync.
  - Verify: `grep -q "status" backend/app/schemas.py && grep -q "status" backend/app/models.py`

**Regression Verification:**
- [ ] (CODE) Existing scaffold files unchanged outside scope.
  - Verify: `test -f backend/app/main.py && test -f frontend/package.json`

---

## Phase 3: Dashboard API and Overview UI

**Goal:** Provide run-level listing APIs and a dashboard page with sorting, pagination, status totals, and error highlighting.
**Depends On:** Phase 2

### Pre-Phase Setup
Human must complete before starting:
- [ ] Confirm ingestion endpoint is available in local build context.
  - Verify: `grep -q "api/v1/ingest" backend/app/main.py`
- [ ] Confirm React Query and TanStack Table are declared dependencies.
  - Verify: `grep -q "@tanstack/react-query\|@tanstack/react-table" frontend/package.json`

### Step 3.1: Run APIs and aggregation
**Depends On:** None

#### Task 3.1.A: Implement `/api/v1/runs` with filters, pagination, and sorting

**Description:**
Build list endpoint used by dashboard page with support for agent/status/time-range filters,
text search placeholder, and deterministic pagination/sort semantics.

**Requirement:** REQ-003, REQ-006, REQ-007

**Acceptance Criteria:**
- [ ] (CODE) Route `GET /api/v1/runs` accepts query params for agent/status/time window/pagination/sort.
  - Verify: `grep -q "def get_runs\|agent_name\|status\|time_start\|page" backend/app/routers/runs.py`
- [ ] (TEST) List endpoint returns `runs`, `total`, `page`, and `page_size` fields.
  - Verify: `pytest -q backend/tests/test_runs.py -k list`
- [ ] (TEST) Filter parameters do not break default response format.
  - Verify: `pytest -q backend/tests/test_runs.py -k filters`

**Files to Create:**
- `backend/app/routers/runs.py` — run listing and stats endpoints
- `backend/tests/test_runs.py` — run listing tests

**Files to Modify:**
- `backend/app/main.py` — mount runs router

**Existing Code to Reference:**
- `backend/app/services/ingest.py` — event-to-run materialization relationship

**Dependencies:**
- Task 2.2.A

**Spec Reference:** Dashboard API contract

**Browser Verification:**
- Criteria IDs: none
- Notes: API-first verification via curl

#### Task 3.1.B: Implement `/api/v1/runs/stats` summary endpoint

**Description:**
Add aggregate endpoint that returns total runs, failure rate, and average duration for
selected filters/time windows.

**Requirement:** REQ-005

**Acceptance Criteria:**
- [ ] (CODE) Route `GET /api/v1/runs/stats` returns total, success_count, failure_count, failure_rate, and avg_duration_ms.
  - Verify: `grep -q "runs/stats\|failure_rate\|avg_duration_ms" backend/app/routers/runs.py`
- [ ] (TEST) Stats endpoint works when no filters are provided.
  - Verify: `pytest -q backend/tests/test_runs.py -k stats`
- [ ] (TEST) Stats endpoint handles time window filters and returns numeric values.
  - Verify: `pytest -q backend/tests/test_runs.py -k time_window`

**Files to Create:**
- `backend/app/routers/runs.py` — stats endpoint function

**Files to Modify:**
- `backend/tests/test_runs.py` — stats assertions and fixtures

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — stats response format

**Dependencies:**
- Task 3.1.A

**Spec Reference:** Dashboard metrics contract

**Browser Verification:**
- Criteria IDs: none
- Notes: API contract checks via curl

#### Task 3.1.C: Add `GET /api/v1/agents`

**Description:**
Expose current list of known agents for filtering controls and UI dropdowns.

**Requirement:** REQ-006

**Acceptance Criteria:**
- [ ] (CODE) Route `GET /api/v1/agents` returns array of agents with name, first_seen_at, last_seen_at.
  - Verify: `grep -q "/api/v1/agents" backend/app/routers/agents.py`
- [ ] (TEST) Agent endpoint returns a successful response and list shape.
  - Verify: `pytest -q backend/tests/test_agents.py`
- [ ] (CODE) Endpoint can be consumed by filter controls with stable agent name fields.
  - Verify: `grep -q "agent_name\|first_seen_at\|last_seen_at" backend/app/routers/agents.py`

**Files to Create:**
- `backend/app/routers/agents.py` — agent lookup endpoint
- `backend/tests/test_agents.py` — agent endpoint tests

**Files to Modify:**
- `backend/app/main.py` — register agents router

**Existing Code to Reference:**
- `backend/app/services/ingest.py` — upsert behavior determines agent list

**Dependencies:**
- Task 3.1.A

**Spec Reference:** Run Overview dashboard contract

**Browser Verification:**
- Criteria IDs: none
- Notes: API verification

### Step 3.2: Dashboard UI
**Depends On:** Step 3.1

#### Task 3.2.A: Build dashboard page shell with summary stats and run list ✅ COMPLETE (mock data)

**Description:**
Implement default route dashboard with paginated runs table and summary metrics bar,
including failure highlighting and empty-state handling.

**Requirement:** REQ-003, REQ-004, REQ-005

**Note:** Built with mock data. Swap `mockRuns`/`mockStats` imports for API calls when backend is ready.

**Acceptance Criteria:**
- [x] (BROWSER:DOM) Route `/` loads and shows metrics and run table area.
  - Verify: route=`/`, selector=`main`
- [x] (BROWSER:DOM) Failed runs are visually distinct through status class or icon marker.
  - Verify: route=`/`, selector=`.run-status-failed`
- [x] (BROWSER:DOM) Run rows include agent name, start/end, duration, status, and step count.
  - Verify: route=`/`, selector=`[data-testid="run-row"]`

**Files to Create:**
- `frontend/src/pages/DashboardPage.tsx` — shell and data orchestration
- `frontend/src/components/StatsBar.tsx` — totals and summary metrics
- `frontend/src/components/RunsTable.tsx` — paginated run list

**Files to Modify:**
- `frontend/src/App.tsx` — register route `/`
- `frontend/src/api/client.ts` — add runs and stats fetch helpers

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — frontend architecture and routes

**Dependencies:**
- Task 3.1.A, Task 3.1.B, Task 3.1.C

**Spec Reference:** Run Overview Dashboard

**Browser Verification:**
- Criteria IDs: 3.2.A, 3.2.B
- Notes: requires frontend build and API available during verification

#### Task 3.2.B: Implement reusable utilities and poll interval ✅ PARTIAL (utils done, polling deferred to API wiring)

**Description:**
Add duration formatting, URL query-state helpers, and periodic polling integration for
near-real-time dashboard refreshes.

**Requirement:** REQ-003, REQ-005

**Note:** Utils complete. TanStack Query polling will be added when frontend is wired to real APIs.

**Acceptance Criteria:**
- [x] (CODE) Shared formatting utilities exist for ISO timestamp and duration display.
  - Verify: `test -f frontend/src/lib/utils.ts`
- [ ] (TEST) Dashboard list fetches data via TanStack Query with a non-zero polling interval.
  - Verify: `grep -q "refetchInterval\|TanStack Query\|useQuery" frontend/src/pages/DashboardPage.tsx`
- [ ] (BROWSER:DOM) Polling changes reflect updated run list after refetch interval.
  - Verify: route=`/`, selector=`[data-testid="dashboard-refresh"]`

**Files to Create:**
- `frontend/src/lib/utils.ts` — shared date and duration helpers
- `frontend/src/pages/DashboardPage.tsx` — query configuration update

**Files to Modify:**
- `frontend/src/api/client.ts` — reusable fetch client

**Existing Code to Reference:**
- `frontend/src/pages/DashboardPage.tsx` — existing query wiring

**Dependencies:**
- Task 3.2.A

**Spec Reference:** Frontend architecture patterns

**Browser Verification:**
- Criteria IDs: 3.2.B
- Notes: data refresh behavior captured after task verification window

### Phase 3 Checkpoint

**Automated Checks:**
- [ ] (TEST) Run list and stats tests pass.
  - Verify: `pytest -q backend/tests/test_runs.py backend/tests/test_agents.py`
- [ ] (TEST) Frontend tests pass where available.
  - Verify: `cd frontend && npm test -- --runInBand`
- [ ] (BROWSER:DOM) Core dashboard page renders and displays run list and stats fields.
  - Verify: route=`/`, selector=`.stats-bar`

**Regression Verification:**
- [ ] (CODE) API route registration remains complete.
  - Verify: `grep -q "/api/v1/runs\|/api/v1/runs/stats\|/api/v1/agents" backend/app/main.py`

---

## Phase 4: Trace Viewer

**Goal:** Provide nested event timeline for each run and a drill-down frontend view.
**Depends On:** Phase 3

### Pre-Phase Setup
Human must complete before starting:
- [ ] Ensure dashboard run list has clickable run IDs.
  - Verify: `grep -q "runs/" frontend/src/pages/DashboardPage.tsx`

### Step 4.1: Trace API and tree assembly
**Depends On:** None

#### Task 4.1.A: Implement `/api/v1/runs/{run_id}` with nested event tree

**Description:**
Build run detail endpoint that assembles events into a parent-child tree and computes
per-event durations using the spec-defined algorithm.

**Requirement:** REQ-009, REQ-010, REQ-011, REQ-012

**Acceptance Criteria:**
- [ ] (CODE) Route `GET /api/v1/runs/{run_id}` returns `run` plus `events` array.
  - Verify: `grep -q "run_id\|children\|duration_ms" backend/app/routers/runs.py`
- [ ] (CODE) Tree assembly code uses `parent_step_id` to connect parents and children.
  - Verify: `grep -q "parent_step_id" backend/app/services/search.py backend/app/routers/runs.py`
- [ ] (TEST) Trace endpoint returns nested events with expected keys for at least one level of child.
  - Verify: `pytest -q backend/tests/test_runs.py -k trace`

**Files to Create:**
- `backend/app/services/search.py` — trace assembly and tree utility functions

**Files to Modify:**
- `backend/app/routers/runs.py` — add trace response endpoint
- `backend/tests/test_runs.py` — add trace assertion test

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — duration algorithm and nested response

**Dependencies:**
- Task 3.1.A

**Spec Reference:** Trace Viewer contract

**Browser Verification:**
- Criteria IDs: none
- Notes: API verification via JSON shape first

#### Task 4.1.B: Handle trace error highlighting metadata in API response

**Description:**
Ensure trace response includes status and error fields per event so UI can style
error states and show stack/error text inline.

**Requirement:** REQ-012

**Acceptance Criteria:**
- [ ] (CODE) Trace response includes `status` for each event.
  - Verify: `grep -q "status" backend/app/services/search.py`
- [ ] (CODE) Trace response includes `error_message` and preserves nested structure ordering logic.
  - Verify: `grep -q "error_message" backend/app/routers/runs.py`
- [ ] (TEST) Trace endpoint test covers error event case with non-null stack/error payload.
  - Verify: `pytest -q backend/tests/test_runs.py -k "error\|trace"`

**Files to Modify:**
- `backend/app/services/search.py` — include error/message fields
- `backend/app/routers/runs.py` — response serializer

**Existing Code to Reference:**
- `backend/app/services/search.py` — event tree assembly

**Dependencies:**
- Task 4.1.A

**Spec Reference:** Trace viewer and error visibility requirements

**Browser Verification:**
- Criteria IDs: none
- Notes: API contract checks

### Step 4.2: Trace frontend timeline
**Depends On:** Step 4.1

#### Task 4.2.A: Build trace viewer page and timeline components ✅ COMPLETE (mock data)

**Description:**
Create a dedicated run detail view with recursive components to display nested steps,
showing durations, types, input/output summary, and expandable details.

**Requirement:** REQ-009, REQ-010, REQ-011, REQ-012

**Note:** Built with mock data. Swap `getRunDetail` import for API call when backend is ready.

**Acceptance Criteria:**
- [x] (BROWSER:DOM) Route `/runs/{runId}` loads details and shows a timeline container.
  - Verify: route=`/runs/run-001`, selector=`[data-testid="run-header"]`
- [x] (BROWSER:DOM) Child steps are visibly nested beneath parent step nodes.
  - Verify: route=`/runs/run-001`, selector=`[data-testid="trace-step-children"]`
- [x] (BROWSER:DOM) Error status steps render error styling and message block.
  - Verify: route=`/runs/run-002`, selector=`[data-status="failure"]`

**Files to Create:**
- `frontend/src/pages/TraceViewerPage.tsx` — run detail route page
- `frontend/src/components/TraceTimeline.tsx` — timeline container
- `frontend/src/components/TraceStep.tsx` — recursive step node component

**Files to Modify:**
- `frontend/src/App.tsx` — add `/runs/:runId` route
- `frontend/src/api/client.ts` — add run detail fetch helper

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — API and component plan

**Dependencies:**
- Task 4.1.A, Task 4.1.B

**Spec Reference:** Trace Viewer drill-down

**Browser Verification:**
- Criteria IDs: 4.2.A
- Notes: must run after backend and frontend are started

### Phase 4 Checkpoint

**Automated Checks:**
- [ ] (TEST) Trace API and service tests pass.
  - Verify: `pytest -q backend/tests/test_runs.py -k trace`
- [ ] (BROWSER:DOM) Trace page renders and shows nested events.
  - Verify: route=`/runs/550e8400-e29b-41d4-a716-446655440000`, selector=`[data-testid="trace-timeline"]`

**Regression Verification:**
- [ ] (CODE) Run list route still links to run detail route format.
  - Verify: `grep -q "runId" frontend/src/pages/DashboardPage.tsx`

---

## Phase 5: Search and Filtering

**Goal:** Add robust filtering and text search composition across run list and trace retrieval.
**Depends On:** Phase 4

### Pre-Phase Setup
Human must complete before starting:
- [ ] Confirm search indexes are planned in schema and model definitions.
  - Verify: `grep -q "GIN\|tsvector\|search_vector" backend/app/models.py`

### Step 5.1: API search and composable filters
**Depends On:** None

#### Task 5.1.A: Compose filters in `/api/v1/runs` using AND conditions

**Description:**
Implement filter composition over agent name, status, and time window that combines with text search safely.

**Requirement:** REQ-006, REQ-007, REQ-008

**Acceptance Criteria:**
- [ ] (CODE) Filter query builder combines optional agent, status, and time range.
  - Verify: `grep -q "agent_name\|status\|time_start\|time_end" backend/app/routers/runs.py`
- [ ] (CODE) Search query integration uses PostgreSQL full-text vector with tsquery when `search` is provided.
  - Verify: `grep -q "plainto_tsquery\|search_vector" backend/app/routers/runs.py backend/app/services/search.py`
- [ ] (TEST) Filter and search endpoint behavior composes correctly in one call.
  - Verify: `pytest -q backend/tests/test_runs.py -k filter_search`

**Files to Modify:**
- `backend/app/routers/runs.py` — query filter composition
- `backend/app/services/search.py` — database query helpers if separated

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — search query pseudo-SQL and filters

**Dependencies:**
- Task 3.1.A

**Spec Reference:** Search Implementation section

**Browser Verification:**
- Criteria IDs: none
- Notes: use API checks first

#### Task 5.1.B: Add frontend filtering controls and composed query state ✅ COMPLETE (mock data)

**Description:**
Implement filter UI controls that maintain query state and request server-side filtered results
from dashboard list endpoint.

**Requirement:** REQ-006, REQ-007, REQ-008

**Note:** Built with client-side filtering on mock data. Will switch to server-side API params when backend is ready.

**Acceptance Criteria:**
- [x] (BROWSER:DOM) Filter controls render for agent, status, and time window.
  - Verify: route=`/`, selector=`[data-testid="run-filters"]`
- [x] (BROWSER:DOM) Filter interaction triggers data refetch with updated query params.
  - Verify: route=`/`, selector=`[data-testid="run-table"][data-filter-state]`
- [ ] (TEST) Frontend tests or hooks verify filter parameter encoding when changed.
  - Verify: `cd frontend && npm test -- --runInBand -t filter`

**Files to Create:**
- `frontend/src/components/RunFilters.tsx` — control set

**Files to Modify:**
- `frontend/src/pages/DashboardPage.tsx` — pass filters to API query
- `frontend/src/api/client.ts` — include optional query params

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — required filter fields and time ranges

**Dependencies:**
- Task 3.2.A, Task 5.1.A

**Spec Reference:** Search & filtering user flows

**Browser Verification:**
- Criteria IDs: 5.1.B
- Notes: browser DOM check for control behavior

### Phase 5 Checkpoint

**Automated Checks:**
- [ ] (TEST) Filter/search backend behavior is covered.
  - Verify: `pytest -q backend/tests/test_runs.py -k filter_search`
- [ ] (TEST) Frontend filter unit tests pass.
  - Verify: `cd frontend && npm test -- --runInBand`

**Regression Verification:**
- [ ] (CODE) Dashboard endpoint parameters continue to accept defaults.
  - Verify: `grep -q "page_size\|sort" backend/app/routers/runs.py`

---

## Phase 6: Alerting

**Goal:** Deliver configurable alerting and notification with persistence and history.
**Depends On:** Phase 5

### Pre-Phase Setup
Human must complete before starting:
- [ ] Configure SMTP placeholders in environment docs/examples.
  - Verify: `grep -q "SMTP_HOST\|SMTP_PORT\|SMTP_USER" plans/greenfield/TECHNICAL_SPEC.md`

### Step 6.1: Alert rule and alert history API
**Depends On:** None

#### Task 6.1.A: Implement alert rule CRUD endpoints

**Description:**
Build API endpoints to create, read, update, and delete alert rules for per-agent and global thresholds.

**Requirement:** REQ-013, REQ-014, REQ-016

**Acceptance Criteria:**
- [ ] (CODE) CRUD routes exist for `/api/v1/alerts/rules` with POST, GET, PUT, DELETE.
  - Verify: `grep -q "alerts/rules" backend/app/routers/alerts.py`
- [ ] (CODE) DB schema includes required fields for failure_rate, p95_latency, and stuck_run metric types.
  - Verify: `grep -q "failure_rate\|p95_latency\|stuck_run" backend/app/models.py backend/app/schemas.py`
- [ ] (TEST) Rule CRUD test covers create and delete flows.
  - Verify: `pytest -q backend/tests/test_alerts.py -k rules`

**Files to Create:**
- `backend/app/routers/alerts.py` — rules CRUD API
- `backend/tests/test_alerts.py` — alert API tests
- `backend/app/schemas.py` — alert rule schemas

**Files to Modify:**
- `backend/app/main.py` — register alerts router

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — alert API and schemas

**Dependencies:**
- Task 2.2.A

**Spec Reference:** Alerts API contracts

**Browser Verification:**
- Criteria IDs: none
- Notes: API tests first

#### Task 6.1.B: Add alert history API

**Description:**
Expose alert history retrieval to support UI display and troubleshooting of fired rules.

**Requirement:** REQ-015

**Acceptance Criteria:**
- [ ] (CODE) Route `GET /api/v1/alerts/history` supports filtering by agent and time window.
  - Verify: `grep -q "alerts/history" backend/app/routers/alerts.py`
- [ ] (TEST) Alert history endpoint returns paginated list and total count.
  - Verify: `pytest -q backend/tests/test_alerts.py -k history`
- [ ] (CODE) Router is mounted in application startup.
  - Verify: `grep -q "alerts" backend/app/main.py`

**Files to Modify:**
- `backend/app/routers/alerts.py` — history endpoint
- `backend/tests/test_alerts.py` — history assertions

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — alert history response format

**Dependencies:**
- Task 6.1.A

**Spec Reference:** Alerts section

**Browser Verification:**
- Criteria IDs: none
- Notes: API contract only

### Step 6.2: Alert evaluation scheduler and notifications
**Depends On:** Step 6.1

#### Task 6.2.A: Implement periodic alert evaluation job

**Description:**
Create APScheduler job that evaluates enabled rules each minute and records trigger events
while respecting dedupe window behavior.

**Requirement:** REQ-013, REQ-014, REQ-020

**Acceptance Criteria:**
- [ ] (CODE) Scheduler runs every minute and invokes alert rule evaluation.
  - Verify: `grep -q "APScheduler\|add_job\|minutes" backend/app/main.py backend/app/tasks/alert_checker.py`
- [ ] (CODE) Evaluation computes failure_rate, p95_latency, and stuck_run with correct inputs.
  - Verify: `grep -q "failure_rate\|p95\|stuck_run" backend/app/services/alerts.py`
- [ ] (CODE) Dedupe check skips repeat alerts within configured window.
  - Verify: `grep -q "dedup\|last\|window" backend/app/services/alerts.py`

**Files to Create:**
- `backend/app/services/alerts.py` — rule evaluation and metric computation
- `backend/app/tasks/alert_checker.py` — scheduler entrypoint

**Files to Modify:**
- `backend/app/main.py` — scheduler startup/shutdown hooks
- `backend/app/models.py` — alert_history writes

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — alert evaluation logic and cadence

**Dependencies:**
- Task 6.1.A, Task 6.1.B

**Spec Reference:** Alert evaluation logic

**Browser Verification:**
- Criteria IDs: none
- Notes: backend scheduler verification via logs or tests

#### Task 6.2.B: Implement email notification fallback behavior

**Description:**
Add SMTP-based sender that degrades gracefully when credentials are missing and still
persists alerts as failed send if SMTP unavailable.

**Requirement:** REQ-015

**Acceptance Criteria:**
- [ ] (CODE) Email send helper exists and reads SMTP environment config.
  - Verify: `grep -q "SMTP_HOST\|SMTP_PORT\|SMTP_USER\|aiosmtplib" backend/app/services/email.py`
- [ ] (CODE) Alert notification includes agent, metric, threshold value, and current value.
  - Verify: `grep -q "agent_name\|metric\|threshold\|current value" backend/app/services/email.py`
- [ ] (TEST) Missing SMTP config path does not crash scheduler and marks send status.
  - Verify: `pytest -q backend/tests/test_alerts.py -k email`

**Files to Create:**
- `backend/app/services/email.py` — SMTP notification helper

**Files to Modify:**
- `backend/app/tasks/alert_checker.py` — invoke sender and write email_sent flag

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — SMTP config and fallback behavior

**Dependencies:**
- Task 6.2.A

**Spec Reference:** SMTP Configuration and Email content

**Browser Verification:**
- Criteria IDs: none
- Notes: backend integration test

### Step 6.3: Build alerts management page
**Depends On:** Step 6.2

#### Task 6.3.A: Implement settings UI for alert rule CRUD ✅ COMPLETE (mock data)

**Description:**
Add page to list, create, edit, and delete alert rules with support for per-agent,
metric, threshold, and window settings.

**Requirement:** REQ-013, REQ-014, REQ-016

**Note:** Built with mock data and local state. Will wire to real API CRUD when backend is ready.

**Acceptance Criteria:**
- [x] (BROWSER:DOM) Route `/alerts` renders list and create/edit controls.
  - Verify: route=`/alerts`, selector=`[data-testid="alert-rules-list"]`
- [x] (BROWSER:DOM) Rule form allows entering failure rate and latency thresholds.
  - Verify: route=`/alerts`, selector=`[data-testid="create-rule-btn"]`
- [ ] (TEST) Frontend rule UI test validates form validation and submission shape.
  - Verify: `cd frontend && npm test -- --runInBand -t AlertRule`

**Files to Create:**
- `frontend/src/pages/AlertsPage.tsx` — alert settings page
- `frontend/src/components/AlertRuleForm.tsx` — form component
- `frontend/src/components/AlertRulesList.tsx` — rules table and actions

**Files to Modify:**
- `frontend/src/App.tsx` — add alerts route
- `frontend/src/api/client.ts` — rule CRUD helper methods

**Existing Code to Reference:**
- `frontend/src/pages/TraceViewerPage.tsx` — data-fetch flow patterns

**Dependencies:**
- Task 6.1.A, Task 6.1.B

**Spec Reference:** Alert rules management page

**Browser Verification:**
- Criteria IDs: 6.3.A
- Notes: UI verification

#### Task 6.3.B: Add alert history display and status indicators ✅ COMPLETE (mock data)

**Description:**
Add alert history section showing trigger times, metric values, and whether email sent,
for quick operator triage.

**Requirement:** REQ-015

**Note:** Built with mock data. Will wire to real API when backend is ready.

**Acceptance Criteria:**
- [x] (BROWSER:DOM) Alerts page shows history table with agent, metric, value, and timestamp.
  - Verify: route=`/alerts`, selector=`table`
- [ ] (CODE) UI fetches `/api/v1/alerts/history` and handles pagination.
  - Verify: `grep -q "alerts/history" frontend/src/api/client.ts`
- [ ] (TEST) Alert history rendering is covered by frontend unit test.
  - Verify: `cd frontend && npm test -- --runInBand -t AlertHistory`

**Files to Create:**
- `frontend/src/components/AlertHistory.tsx` — history list component

**Files to Modify:**
- `frontend/src/pages/AlertsPage.tsx` — integrate history component

**Existing Code to Reference:**
- `backend/app/routers/alerts.py` — response schema

**Dependencies:**
- Task 6.3.A

**Spec Reference:** Alert history API

**Browser Verification:**
- Criteria IDs: 6.3.B
- Notes: Browser check on `/alerts`

### Phase 6 Checkpoint

**Automated Checks:**
- [ ] (TEST) Alert CRUD and history tests pass.
  - Verify: `pytest -q backend/tests/test_alerts.py`
- [ ] (CODE) Alert scheduler task module is imported by app startup.
  - Verify: `grep -q "alert_checker\|APScheduler" backend/app/main.py`
- [ ] (BROWSER:DOM) Alerts route renders successfully.
  - Verify: route=`/alerts`, selector=`[data-testid="alerts-page"]`

**Regression Verification:**
- [ ] (CODE) Existing run APIs continue functioning.
  - Verify: `grep -q "runs/stats\|api/v1/runs" backend/app/routers/runs.py`

---

## Phase 7: Deployment and Hardening

**Goal:** Finalize data retention, operational readiness, and internal-facing polish without adding new feature scope.
**Depends On:** Phase 6

### Pre-Phase Setup
Human must complete before starting:
- [ ] Confirm all environment variable names are documented in technical spec and runtime config.
  - Verify: `grep -q "DATABASE_URL\|SMTP_HOST\|RETENTION_DAYS\|ALERT_RECIPIENTS" plans/greenfield/TECHNICAL_SPEC.md`

### Step 7.1: Data retention and maintenance jobs
**Depends On:** None

#### Task 7.1.A: Add retention scheduling and deletion job

**Description:**
Implement daily job that purges events, runs, and alert history beyond retention window,
with configurable retention days and safe ordering.

**Requirement:** REQ-020

**Acceptance Criteria:**
- [ ] (CODE) Retention task exists and deletes in order: events, runs, alert history.
  - Verify: `grep -q "delete from events\|delete from runs\|delete from alert_history" backend/app/tasks/data_retention.py`
- [ ] (CODE) Retention job is scheduled on startup with configurable interval.
  - Verify: `grep -q "data_retention\|interval" backend/app/tasks/data_retention.py backend/app/main.py`
- [ ] (TEST) Retention task test validates behavior with sample date window.
  - Verify: `pytest -q backend/tests/test_retention.py`

**Files to Create:**
- `backend/app/tasks/data_retention.py` — retention job
- `backend/tests/test_retention.py` — retention job tests

**Files to Modify:**
- `backend/app/main.py` — register retention scheduler task

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — APScheduler retention behavior

**Dependencies:**
- Task 1.2.B

**Spec Reference:** Data Retention section

**Browser Verification:**
- Criteria IDs: none
- Notes: backend periodic task tests

#### Task 7.1.B: Seed and seed-like demo pathway

**Description:**
Add optional seed script and docs to generate local sample agents/runs for manual verification.

**Requirement:** None

**Acceptance Criteria:**
- [ ] (CODE) Seed script exists and is deterministic.
  - Verify: `test -f backend/app/scripts/seed_demo_data.py`
- [ ] (CODE) Seed script includes sample run and alert payloads suitable for smoke checks.
  - Verify: `grep -q "run_id\|agent_name\|alert_rules" backend/app/scripts/seed_demo_data.py`
- [ ] (TEST) Seed smoke command runs without crashing and exits successfully.
  - Verify: `python backend/app/scripts/seed_demo_data.py --dry-run`

**Files to Create:**
- `backend/app/scripts/seed_demo_data.py` — local demo data script

**Files to Modify:**
- `backend/app/scripts/__init__.py` — script package marker

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — sample payload references

**Dependencies:**
- Task 7.1.A

**Spec Reference:** Deployment readiness

**Browser Verification:**
- Criteria IDs: none
- Notes: command-line smoke path

### Step 7.2: Compose, docs, and launch polish
**Depends On:** Step 7.1

#### Task 7.2.A: Finalize production Docker Compose and reverse proxy settings

**Description:**
Ensure compose and frontend server config route API calls through Nginx and expose stable ports.

**Requirement:** None

**Acceptance Criteria:**
- [ ] (CODE) Docker Compose includes db, backend, and frontend services with health/start semantics.
  - Verify: `grep -n "services:\|backend:\|frontend:\|db:" docker-compose.yml`
- [ ] (CODE) Frontend Nginx config proxies `/api` to backend service and serves SPA routes.
  - Verify: `test -f frontend/nginx.conf && grep -q "proxy_pass\|try_files" frontend/nginx.conf`
- [ ] (CODE) README or quickstart notes include run command for end-to-end startup.
  - Verify: `grep -q "docker compose up" README.md`

**Files to Create:**
- `frontend/nginx.conf` — reverse proxy and SPA fallback
- `README.md` — startup, env, and verification instructions

**Files to Modify:**
- `docker-compose.yml` — environment and port wiring

**Existing Code to Reference:**
- `plans/greenfield/TECHNICAL_SPEC.md` — compose sample and URLs

**Dependencies:**
- Task 7.1.B

**Spec Reference:** Docker Compose section

**Browser Verification:**
- Criteria IDs: none
- Notes: manual smoke route checks after compose up

#### Task 7.2.B: Final verification and readiness checks

**Description:**
Deliver final pass of quality gates, verify all feature and acceptance criteria are in plan,
and ensure no missing verification metadata remains in tasks.

**Requirement:** None

**Acceptance Criteria:**
- [ ] (TEST) Backend test suite passes in current environment.
  - Verify: `cd backend && pytest -q`
- [ ] (TEST) Frontend typecheck and build complete.
  - Verify: `cd frontend && npm run build && npm run typecheck`
- [ ] (BROWSER:DOM) Dashboard and alerts pages are reachable with no blocking browser console errors.
  - Verify: route=`/`, selector=`body` and `BROWSER:CONSOLE` via `/`

**Files to Modify:**
- `plans/greenfield/EXECUTION_PLAN.md` — mark completed checkpoints

**Existing Code to Reference:**
- This file and both spec docs

**Dependencies:**
- Task 7.2.A

**Spec Reference:** Final launch readiness

**Browser Verification:**
- Criteria IDs: 7.2.B
- Notes: end-to-end smoke validation

### Phase 7 Checkpoint

**Automated Checks:**
- [ ] All core tests pass.
  - Verify: `pytest -q backend/tests`
- [ ] Frontend build is healthy.
  - Verify: `cd frontend && npm run build`
- [ ] Containerized service boots and responds on expected endpoints.
  - Verify: `docker compose up -d && curl -sf http://localhost:80/`

**Regression Verification:**
- [ ] (CODE) No existing API contracts changed by deployment files.
  - Verify: `grep -q "api/v1/runs\|api/v1/alerts" backend/app/main.py`
- [ ] (CODE) No runbook or plan-critical instruction file overwritten.
  - Verify: `test -f AGENTS.md && test -f plans/greenfield/AGENTS.md`
