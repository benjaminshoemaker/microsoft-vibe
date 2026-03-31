# Technical Specification: Agent Observability Dashboard

**Version:** 1.0 (MVP)
**Date:** 2026-03-30
**Source:** PRODUCT_SPEC.md

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.12 + FastAPI | Team already writes Python. FastAPI is async, fast, and has Pydantic for schema validation — perfect for an ingestion API. |
| Frontend | React 18 + TypeScript + Vite | Largest ecosystem for data-heavy dashboards. Vite for fast dev experience. |
| UI Components | shadcn/ui + Tailwind CSS | High-quality, composable components. No runtime CSS overhead. |
| Data Tables | TanStack Table | Best-in-class for sortable, filterable, paginated tables in React. |
| Charts | Recharts | Simple, composable charting for summary stats. Lightweight. |
| Database | PostgreSQL 16 | Handles structured queries + full-text search via `tsvector`. Already decided in product spec. |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic | Mature Python ORM with async support. Alembic for versioned migrations. |
| Schema Validation | Pydantic v2 | FastAPI-native. Validates ingestion payloads with clear error messages. |
| Background Tasks | APScheduler | In-process scheduler for alert evaluation and data retention. No external worker infrastructure. |
| Email | `aiosmtplib` | Async SMTP client. Sends alert emails directly — no external email service needed. |
| HTTP Client | `httpx` | Async HTTP client for any outbound requests (future use). |
| Deployment | Docker Compose | Single `docker-compose.yml` with backend + frontend + PostgreSQL containers. |

### Assumptions (Auto-Decided)

- **Architecture:** Monolith — single FastAPI process serves both the API and runs background tasks. Appropriate for < 100 runs/day.
- **API style:** REST — straightforward CRUD and query patterns. No need for GraphQL.
- **Full-text search:** PostgreSQL `tsvector` with `GIN` index on error messages and log content. No Elasticsearch needed at this volume.
- **State management (frontend):** TanStack Query for server state (caching, refetching). Minimal React state for UI controls (filters, selected run).
- **Data retention:** Scheduled cleanup job (APScheduler) that deletes events and runs older than a configurable threshold (default 30 days).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                     │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │   Frontend    │    │   Backend    │               │
│  │  (React/TS)   │───▶│  (FastAPI)   │               │
│  │  Nginx :80    │    │   :8000      │               │
│  └──────────────┘    └──────┬───────┘               │
│                             │                        │
│                    ┌────────┴────────┐               │
│                    │   PostgreSQL    │               │
│                    │     :5432       │               │
│                    └─────────────────┘               │
│                                                      │
│  Python Agents ──POST /api/v1/ingest──▶ Backend      │
│                                                      │
│  APScheduler (in-process):                           │
│    - Alert evaluation (every 1 min)                  │
│    - Data retention cleanup (daily)                  │
│                                                      │
│  SMTP ◀── Alert emails                               │
└─────────────────────────────────────────────────────┘
```

**Request flow:**
1. Python agents POST JSON events to `/api/v1/ingest`
2. Backend validates events via Pydantic, persists to `events` table
3. On `run_start` / `run_end` events, backend upserts the `runs` table with computed summaries
4. Frontend queries REST APIs to display dashboard, runs, and traces
5. APScheduler evaluates alert rules every minute, sends emails when thresholds are breached

**Frontend routing (React Router):**
- `/` — Run overview dashboard (default)
- `/runs/:runId` — Trace viewer for a specific run
- `/alerts` — Alert rules management

---

## Data Models

### `agents` Table

Auto-populated when the first event for a new agent name is received (REQ-002).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | SERIAL | PK | |
| name | TEXT | UNIQUE, NOT NULL | Agent identifier from log events |
| first_seen_at | TIMESTAMPTZ | NOT NULL | Timestamp of first event received |
| last_seen_at | TIMESTAMPTZ | NOT NULL | Updated on each new event |

### `runs` Table

Materialized from events. Created on `run_start`, updated on subsequent events, finalized on `run_end`.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | Same as `run_id` from events |
| agent_name | TEXT | NOT NULL, INDEX | FK-like reference to agents.name |
| status | TEXT | NOT NULL | `running`, `success`, `failure`, `error` |
| started_at | TIMESTAMPTZ | NOT NULL | From `run_start` event |
| ended_at | TIMESTAMPTZ | | From `run_end` event |
| duration_ms | INTEGER | | Computed: `ended_at - started_at` |
| step_count | INTEGER | NOT NULL, DEFAULT 0 | Incremented on each non-start/end event |
| error_message | TEXT | | Last error message from the run |
| metadata | JSONB | DEFAULT '{}' | Merged metadata from events |
| search_vector | TSVECTOR | GIN INDEX | Generated from agent_name + error_message |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

### `events` Table

Raw log events as received (REQ-001).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| run_id | UUID | NOT NULL, INDEX, FK → runs.id | |
| step_id | UUID | UNIQUE | Client-provided or server-generated |
| parent_step_id | UUID | | FK → events.step_id (nullable) |
| agent_name | TEXT | NOT NULL | Denormalized for query convenience |
| step_type | TEXT | NOT NULL | `tool_call`, `llm_call`, `decision`, `error`, `run_start`, `run_end` |
| step_name | TEXT | | Human-readable step name |
| input | JSONB | DEFAULT '{}' | Step input data |
| output | JSONB | DEFAULT '{}' | Step output data |
| status | TEXT | NOT NULL | `success`, `failure`, `error` |
| error_message | TEXT | | Error details if status is error/failure |
| timestamp | TIMESTAMPTZ | NOT NULL | Client-provided event timestamp |
| metadata | JSONB | DEFAULT '{}' | Arbitrary key-value pairs (REQ-018) |
| search_vector | TSVECTOR | GIN INDEX | Generated from step_name + error_message + output text |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Server receive time |

### `alert_rules` Table

User-configured alert thresholds (REQ-013, REQ-014, REQ-016).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | SERIAL | PK | |
| agent_name | TEXT | | NULL = applies to all agents |
| metric | TEXT | NOT NULL | `failure_rate`, `p95_latency`, `stuck_run` |
| threshold_value | FLOAT | NOT NULL | e.g., 10.0 for 10% failure rate, 30.0 for 30s latency |
| window_minutes | INTEGER | NOT NULL, DEFAULT 60 | Evaluation time window |
| multiplier | FLOAT | | For `stuck_run`: alert if duration > multiplier * avg duration |
| enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

### `alert_history` Table

Log of triggered alerts (supports REQ-015).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | SERIAL | PK | |
| alert_rule_id | INTEGER | NOT NULL, FK → alert_rules.id | |
| agent_name | TEXT | NOT NULL | Which agent triggered it |
| triggered_at | TIMESTAMPTZ | NOT NULL | |
| metric_value | FLOAT | NOT NULL | Actual value that breached threshold |
| email_sent | BOOLEAN | NOT NULL, DEFAULT FALSE | |

### Indexes

```sql
-- Run queries (dashboard, filtering)
CREATE INDEX idx_runs_agent_status ON runs (agent_name, status);
CREATE INDEX idx_runs_started_at ON runs (started_at DESC);
CREATE INDEX idx_runs_search ON runs USING GIN (search_vector);

-- Event queries (trace viewer)
CREATE INDEX idx_events_run_id ON events (run_id, timestamp);
CREATE INDEX idx_events_search ON events USING GIN (search_vector);

-- Alert evaluation
CREATE INDEX idx_runs_alert_eval ON runs (agent_name, started_at, status);
```

---

## API Contracts

### Ingestion

#### `POST /api/v1/ingest` (REQ-001, REQ-017)

Accepts a single event or a batch of events.

**Request (single):**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_name": "support-triage",
  "step_type": "tool_call",
  "step_id": "optional-uuid",
  "step_name": "search_knowledge_base",
  "parent_step_id": null,
  "input": {"query": "password reset"},
  "output": {"results": 3},
  "status": "success",
  "error_message": null,
  "timestamp": "2026-03-30T14:30:00Z",
  "metadata": {"version": "1.2.0", "environment": "production"}
}
```

**Request (batch):**
```json
{
  "events": [ ... ]
}
```

**Response (201 Created):**
```json
{
  "accepted": 1,
  "errors": []
}
```

**Response (400 Bad Request — validation failure):**
```json
{
  "accepted": 0,
  "errors": [
    {"index": 0, "field": "step_type", "message": "Invalid value 'unknown'. Must be one of: tool_call, llm_call, decision, error, run_start, run_end"}
  ]
}
```

**Side effects:**
- If `agent_name` is new → insert into `agents` table (REQ-002)
- If `step_type` is `run_start` → create `runs` row with status `running`
- If `step_type` is `run_end` → update `runs` row: set status, compute duration, finalize step_count
- If `step_type` is `error` → update `runs.error_message`
- Increment `runs.step_count` for non-start/end events
- Generate `search_vector` from text fields

### Dashboard

#### `GET /api/v1/runs` (REQ-003, REQ-006, REQ-007, REQ-008)

**Query parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| agent_name | string | | Filter by agent |
| status | string | | Filter: `success`, `failure`, `error`, `running` |
| time_start | ISO 8601 | 24h ago | Start of time range |
| time_end | ISO 8601 | now | End of time range |
| search | string | | Full-text search across error messages and log content |
| page | integer | 1 | Page number |
| page_size | integer | 50 | Items per page (max 100) |
| sort | string | `-started_at` | Sort field. Prefix `-` for descending |

**Response (200):**
```json
{
  "runs": [
    {
      "id": "550e8400-...",
      "agent_name": "support-triage",
      "status": "failure",
      "started_at": "2026-03-30T14:30:00Z",
      "ended_at": "2026-03-30T14:30:45Z",
      "duration_ms": 45000,
      "step_count": 7,
      "error_message": "Tool 'search_kb' returned empty results",
      "metadata": {"version": "1.2.0"}
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 50
}
```

#### `GET /api/v1/runs/stats` (REQ-005)

**Query parameters:** Same filters as `/runs` (agent_name, status, time_start, time_end).

**Response (200):**
```json
{
  "total_runs": 87,
  "success_count": 74,
  "failure_count": 13,
  "failure_rate": 14.9,
  "avg_duration_ms": 32000,
  "time_window": {"start": "2026-03-30T00:00:00Z", "end": "2026-03-30T23:59:59Z"}
}
```

#### `GET /api/v1/runs/{run_id}` (REQ-009, REQ-010, REQ-011, REQ-012)

Returns the full run with all events for the trace viewer.

**Response (200):**
```json
{
  "run": {
    "id": "550e8400-...",
    "agent_name": "support-triage",
    "status": "failure",
    "started_at": "2026-03-30T14:30:00Z",
    "ended_at": "2026-03-30T14:30:45Z",
    "duration_ms": 45000,
    "step_count": 7,
    "error_message": "Tool 'search_kb' returned empty results",
    "metadata": {"version": "1.2.0"}
  },
  "events": [
    {
      "id": "...",
      "step_id": "step-1",
      "parent_step_id": null,
      "step_type": "llm_call",
      "step_name": "classify_intent",
      "input": {"prompt": "..."},
      "output": {"intent": "password_reset"},
      "status": "success",
      "error_message": null,
      "timestamp": "2026-03-30T14:30:01Z",
      "duration_ms": 1200,
      "metadata": {},
      "children": [
        {
          "id": "...",
          "step_id": "step-2",
          "parent_step_id": "step-1",
          "step_type": "tool_call",
          "step_name": "search_knowledge_base",
          "status": "failure",
          "error_message": "Tool 'search_kb' returned empty results",
          "children": []
        }
      ]
    }
  ]
}
```

Events are returned as a nested tree (built server-side from `parent_step_id` references). REQ-011 nesting and REQ-012 error highlighting are driven by this structure — the frontend renders the tree and highlights `status: error|failure` nodes.

**`duration_ms` computation per event:** Not stored — computed server-side when building the tree. Algorithm: for each event, if it has children, `duration_ms` = last child's timestamp - this event's timestamp. If it has no children but has a next sibling, `duration_ms` = next sibling's timestamp - this event's timestamp. If it is the last event with no children, `duration_ms` = run's `ended_at` - this event's timestamp. If the run has no `ended_at`, `duration_ms` = null.

#### `GET /api/v1/agents` (supports REQ-006 filter options)

**Response (200):**
```json
{
  "agents": [
    {"name": "support-triage", "first_seen_at": "2026-03-15T...", "last_seen_at": "2026-03-30T..."},
    {"name": "data-pipeline", "first_seen_at": "2026-03-20T...", "last_seen_at": "2026-03-30T..."}
  ]
}
```

### Alerts

#### `GET /api/v1/alerts/rules` (REQ-016)

**Response (200):**
```json
{
  "rules": [
    {
      "id": 1,
      "agent_name": "support-triage",
      "metric": "failure_rate",
      "threshold_value": 10.0,
      "window_minutes": 60,
      "multiplier": null,
      "enabled": true,
      "created_at": "2026-03-28T...",
      "updated_at": "2026-03-28T..."
    }
  ]
}
```

#### `POST /api/v1/alerts/rules` (REQ-013, REQ-014)

**Request:**
```json
{
  "agent_name": "support-triage",
  "metric": "failure_rate",
  "threshold_value": 10.0,
  "window_minutes": 60
}
```

For stuck-run detection (REQ-014):
```json
{
  "agent_name": "data-pipeline",
  "metric": "stuck_run",
  "multiplier": 3.0,
  "window_minutes": 60
}
```

**Response (201):** Created rule object.

#### `PUT /api/v1/alerts/rules/{id}` — Update rule

**Request:** Same shape as POST (all fields optional — partial update).
```json
{
  "threshold_value": 15.0,
  "enabled": false
}
```

**Response (200):** Updated rule object (full).
**Response (404):** `{"detail": "Alert rule not found"}`

#### `DELETE /api/v1/alerts/rules/{id}` — Delete rule

**Response (204):** No content.
**Response (404):** `{"detail": "Alert rule not found"}`

Note: Deleting a rule does not delete its `alert_history` rows. History rows for deleted rules will omit `metric` and `threshold_value` in the API response (since the join target is gone).

#### `GET /api/v1/alerts/history`

**Query parameters:** `agent_name`, `time_start`, `time_end`, `page`, `page_size`

**Response (200):**
```json
{
  "alerts": [
    {
      "id": 1,
      "alert_rule_id": 1,
      "agent_name": "support-triage",
      "metric": "failure_rate",
      "threshold_value": 10.0,
      "metric_value": 18.5,
      "triggered_at": "2026-03-30T15:00:00Z",
      "email_sent": true
    }
  ],
  "total": 5
}
```

---

## Alert Evaluation Logic

APScheduler runs alert evaluation every 60 seconds:

1. **Fetch all enabled rules** from `alert_rules`
2. For each rule, compute the metric over `window_minutes`:
   - `failure_rate`: `COUNT(status='failure') / COUNT(*) * 100` for runs in window
   - `p95_latency`: 95th percentile of `duration_ms` for runs in window
   - `stuck_run`: Find any `running` runs where `NOW() - started_at > multiplier * avg_duration` for that agent
3. **Compare to threshold.** If breached:
   - Check `alert_history` — skip if same rule fired within the last `window_minutes` (dedup)
   - Insert into `alert_history`
   - Send email via SMTP (REQ-015)

**Email content:**
```
Subject: [Agent Alert] {agent_name} — {metric} threshold breached

Agent: {agent_name}
Metric: {metric}
Threshold: {threshold_value}
Current Value: {metric_value}
Window: Last {window_minutes} minutes

View dashboard: {base_url}/runs?agent_name={agent_name}
```

---

## SMTP Configuration

Environment variables:
```
SMTP_HOST=smtp.internal.example.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=...
SMTP_FROM=agent-dashboard@example.com
ALERT_RECIPIENTS=team@example.com
```

No SMTP configured → log alert to console, skip email. The system should not fail if email is unavailable.

---

## Data Retention (REQ-020)

APScheduler runs daily at 02:00 UTC:

```sql
DELETE FROM events WHERE created_at < NOW() - INTERVAL '{retention_days} days';
DELETE FROM runs WHERE created_at < NOW() - INTERVAL '{retention_days} days';
DELETE FROM alert_history WHERE triggered_at < NOW() - INTERVAL '{retention_days} days';
```

Environment variable: `RETENTION_DAYS=30` (default).

Cascading deletes: events FK → runs, so delete events first, then orphaned runs.

---

## Search Implementation (REQ-007, REQ-008)

PostgreSQL full-text search using `tsvector` and `tsquery`:

**On event insert**, generate search vector:
```sql
UPDATE events SET search_vector =
  to_tsvector('english', COALESCE(step_name, '') || ' ' || COALESCE(error_message, ''));
```

**On run upsert**, generate search vector:
```sql
UPDATE runs SET search_vector =
  to_tsvector('english', COALESCE(agent_name, '') || ' ' || COALESCE(error_message, ''));
```

**Search query** (when `search` param is provided):
```sql
SELECT * FROM runs
WHERE search_vector @@ plainto_tsquery('english', :search)
  AND agent_name = :agent_name  -- if filter provided
  AND status = :status          -- if filter provided
  AND started_at BETWEEN :time_start AND :time_end
ORDER BY started_at DESC
LIMIT :page_size OFFSET :offset;
```

Filters and search compose via `AND` (REQ-008).

---

## Frontend Architecture

```
src/
├── main.tsx                 # Entry point
├── App.tsx                  # Router setup
├── api/
│   └── client.ts            # API client (fetch wrapper, typed)
├── pages/
│   ├── DashboardPage.tsx     # Run overview + stats + filters
│   ├── TraceViewerPage.tsx   # Single run trace timeline
│   └── AlertsPage.tsx        # Alert rules management
├── components/
│   ├── RunsTable.tsx         # TanStack Table for run list
│   ├── RunFilters.tsx        # Filter controls (agent, status, time, search)
│   ├── StatsBar.tsx          # Summary statistics bar
│   ├── TraceTimeline.tsx     # Vertical timeline of trace steps
│   ├── TraceStep.tsx         # Individual step card (expandable)
│   ├── AlertRuleForm.tsx     # Create/edit alert rule
│   └── AlertRulesList.tsx    # Alert rules table
└── lib/
    └── utils.ts              # Formatting, duration display, etc.
```

**Key patterns:**
- TanStack Query for all data fetching — automatic caching, refetching, loading states
- URL-based filter state (query params) so dashboard links are shareable
- Polling: dashboard refetches every 30 seconds via TanStack Query's `refetchInterval`
- Trace tree rendering: recursive `TraceStep` component handles nesting (REQ-011)
- Error highlighting (REQ-004, REQ-012): conditional red styling on `status === 'failure' || status === 'error'`

---

## Project Structure

```
microsoft_vibe/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml          # Dependencies (FastAPI, SQLAlchemy, etc.)
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/           # Migration files
│   ├── app/
│   │   ├── main.py             # FastAPI app, startup/shutdown, scheduler
│   │   ├── config.py           # Settings from environment variables
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── ingest.py       # POST /api/v1/ingest
│   │   │   ├── runs.py         # GET /api/v1/runs, /runs/{id}, /runs/stats
│   │   │   ├── agents.py       # GET /api/v1/agents
│   │   │   └── alerts.py       # CRUD /api/v1/alerts/*
│   │   ├── services/
│   │   │   ├── ingest.py       # Event processing, run materialization
│   │   │   ├── search.py       # Full-text search query builder
│   │   │   ├── alerts.py       # Alert evaluation logic
│   │   │   └── email.py        # SMTP email sending
│   │   └── tasks/
│   │       ├── alert_checker.py    # Scheduled alert evaluation
│   │       └── data_retention.py   # Scheduled cleanup
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf              # Serves static files, proxies /api to backend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       └── (see Frontend Architecture above)
└── plans/
    └── greenfield/
```

---

## Docker Compose

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: agent_dashboard
      POSTGRES_USER: dashboard
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://dashboard:${DB_PASSWORD}@db:5432/agent_dashboard
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      SMTP_FROM: ${SMTP_FROM:-agent-dashboard@example.com}
      ALERT_RECIPIENTS: ${ALERT_RECIPIENTS}
      RETENTION_DAYS: ${RETENTION_DAYS:-30}
      BASE_URL: ${BASE_URL:-http://localhost}
    depends_on:
      - db
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  pgdata:
```

---

## Implementation Sequence

Build in this order — each phase is independently testable:

### Phase 1: Foundation
1. Project scaffolding (backend + frontend + Docker Compose)
2. Database schema + Alembic migrations
3. SQLAlchemy models + Pydantic schemas

### Phase 2: Ingestion Pipeline
4. `POST /api/v1/ingest` endpoint with validation (REQ-001, REQ-017, REQ-018)
5. Run materialization logic — create/update runs from events (REQ-002)
6. Agent auto-discovery on first event

### Phase 3: Dashboard API + UI
7. `GET /api/v1/runs` with pagination (REQ-003)
8. `GET /api/v1/runs/stats` (REQ-005)
9. `GET /api/v1/agents` (REQ-006 support)
10. Frontend: DashboardPage with RunsTable + StatsBar (REQ-003, REQ-004, REQ-005)

### Phase 4: Trace Viewer
11. `GET /api/v1/runs/{run_id}` with nested event tree (REQ-009, REQ-010, REQ-011)
12. Frontend: TraceViewerPage with TraceTimeline + TraceStep (REQ-009, REQ-010, REQ-011, REQ-012)

### Phase 5: Search & Filtering
13. Search vector generation on insert (REQ-007)
14. Filter + search query composition in `/runs` endpoint (REQ-006, REQ-008)
15. Frontend: RunFilters component with agent dropdown, status toggle, time picker, search box

### Phase 6: Alerts
16. Alert rules CRUD API (REQ-013, REQ-014, REQ-016)
17. Alert evaluation scheduler (APScheduler)
18. Email notification sending (REQ-015)
19. Frontend: AlertsPage with AlertRuleForm + AlertRulesList
20. Alert history API + display

### Phase 7: Deployment & Polish
21. Docker Compose production config
22. Data retention cleanup job (REQ-020)
23. Error handling, loading states, empty states in frontend
24. Seed script for demo data

---

## Key Dependencies

### Backend (`pyproject.toml`)
```
fastapi >= 0.115
uvicorn[standard] >= 0.34
sqlalchemy[asyncio] >= 2.0
asyncpg >= 0.30
alembic >= 1.14
pydantic >= 2.10
apscheduler >= 3.10
aiosmtplib >= 3.0
httpx >= 0.28
```

### Frontend (`package.json`)
```
react >= 18.3
react-dom >= 18.3
react-router-dom >= 7
@tanstack/react-query >= 5
@tanstack/react-table >= 8
recharts >= 2.15
tailwindcss >= 4
date-fns >= 4
```

---

## Edge Cases & Boundary Conditions

| Scenario | Handling |
|----------|----------|
| Events arrive out of order | Use client `timestamp` for ordering, `created_at` for ingestion order. Run duration computed from `run_start`/`run_end` timestamps, not arrival order. |
| `run_end` arrives before all steps | Run is finalized with whatever step_count exists. Late-arriving events still insert but don't update the run summary. |
| `run_start` never received | First event for an unknown `run_id` creates the run with `started_at` = that event's timestamp. |
| `run_end` never received | Run stays in `running` status. Stuck-run alerts (REQ-014) catch these. |
| Duplicate events (same step_id) | `step_id` has UNIQUE constraint. Duplicates return 200 (idempotent) with no side effects. |
| Batch with partial failures | Accept valid events, reject invalid ones. Response includes per-event errors with indexes. |
| SMTP unavailable | Log alert to backend console. Set `email_sent = false` in alert_history. Don't crash. |
| Empty dashboard (no data yet) | Frontend shows an empty state with instructions for sending first events. |
| Very large input/output payloads | Truncate `input`/`output` JSONB display in the frontend (show first 500 chars, expand on click). No backend truncation — store full data. |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | — | PostgreSQL connection string |
| DB_PASSWORD | Yes | — | PostgreSQL password |
| SMTP_HOST | No | — | SMTP server hostname |
| SMTP_PORT | No | 587 | SMTP server port |
| SMTP_USER | No | — | SMTP username |
| SMTP_PASSWORD | No | — | SMTP password |
| SMTP_FROM | No | agent-dashboard@example.com | From address for alert emails |
| ALERT_RECIPIENTS | No | — | Comma-separated email addresses |
| RETENTION_DAYS | No | 30 | Days to retain data |
| BASE_URL | No | http://localhost | Base URL for dashboard links in emails |

---

## Requirements Traceability

Every PRODUCT_SPEC requirement is addressed:

| REQ | Technical Approach |
|-----|-------------------|
| REQ-001 | `POST /api/v1/ingest` endpoint |
| REQ-002 | Auto-insert `agents` row on new agent_name |
| REQ-003 | `GET /api/v1/runs` with pagination |
| REQ-004 | Frontend conditional styling on status field |
| REQ-005 | `GET /api/v1/runs/stats` endpoint |
| REQ-006 | Query params: agent_name, status, time_start, time_end |
| REQ-007 | PostgreSQL tsvector full-text search |
| REQ-008 | AND composition of filters + tsquery in SQL |
| REQ-009 | `GET /api/v1/runs/{run_id}` returns nested event tree |
| REQ-010 | Event fields: step_type, step_name, input, output, duration_ms, status |
| REQ-011 | Server-side tree building from parent_step_id |
| REQ-012 | Error events include error_message; frontend highlights |
| REQ-013 | alert_rules table + CRUD API |
| REQ-014 | stuck_run metric type with multiplier |
| REQ-015 | aiosmtplib email with agent name, metric, value, dashboard link |
| REQ-016 | AlertsPage with CRUD UI |
| REQ-017 | Pydantic validation on ingest endpoint |
| REQ-018 | JSONB metadata field, passed through |
| REQ-019 | PostgreSQL via SQLAlchemy + asyncpg |
| REQ-020 | APScheduler daily cleanup job |
| REQ-021 | Single-instance architecture, no sharding |
| REQ-022 | No auth middleware |
