# Product Specification: Agent Observability Dashboard

**Version:** 1.0 (MVP)
**Date:** 2026-03-30
**Source:** /discover + /product-spec

---

## Problem Statement

There is no easy way for the team to see what AI agents are doing in production. When an agent fails, behaves unexpectedly, or degrades in performance, the only recourse is digging through unstructured logs or asking the agent's developer. The team needs a centralized place to see all agent activity, understand execution flows, and get alerted when things go wrong — without requiring each agent to integrate a complex SDK.

## Target Users

Internal team members who build and operate AI agents. This includes:
- **Agent developers** who need to verify their agents are behaving correctly in production
- **Team leads / ops** who need an at-a-glance view of all agent health across the team

This is an internal tool — no public users, no multi-tenancy, no billing.

## Platform

Web application accessed via browser. Deployed internally via Docker Compose.

## Core User Experience

### Agent Onboarding (Developer)

1. Developer has a Python-based agent they want to monitor
2. Developer configures the agent to POST structured JSON log events to the observability tool's ingestion endpoint
3. Each log event includes: agent name, run ID, step type (tool call, LLM call, decision), inputs/outputs, timestamps, and status
4. Agent runs and automatically appears in the dashboard — no registration, no configuration in the UI

**REQ-001:** The system exposes an HTTP POST ingestion endpoint that accepts structured JSON log events.

**REQ-002:** New agents appear automatically in the dashboard when their first log event is received — no manual registration required.

### Run Overview Dashboard (Monitoring)

5. User opens the dashboard and sees a list of all recent agent runs
6. Each run shows: agent name, start/end time, duration, status (success/failure/error), and step count
7. Runs are sorted by most recent, with failed runs visually highlighted
8. Summary stats at the top: total runs today, failure rate, average duration

**REQ-003:** The dashboard displays a paginated list of agent runs with agent name, timestamps, duration, status, and step count.

**REQ-004:** Failed runs are visually distinguished (color, icon) from successful runs.

**REQ-005:** The dashboard shows summary statistics: total runs, failure rate, and average duration for the selected time window.

### Search & Filtering

9. User filters runs by agent name, status (success/failure), and time range using structured filter controls
10. User searches across error messages and log content using a text search box
11. Filters and search combine (e.g., "failed runs from agent-X in the last 24 hours containing 'timeout'")

**REQ-006:** Users can filter the run list by agent name, status, and time range.

**REQ-007:** Users can perform text search across error messages and log content within runs.

**REQ-008:** Filters and text search compose together for precise queries.

### Trace Viewer (Drill-Down)

12. User clicks a run to open the trace viewer
13. The trace viewer shows a vertical timeline of every step in the agent's execution
14. Each step displays: step type (tool call, LLM call, decision), name/description, inputs, outputs, latency, and status
15. Steps are nested to show parent-child relationships (e.g., an agent decision that triggered a tool call)
16. Errors are highlighted inline with the error message and stack trace visible

**REQ-009:** Clicking a run opens a trace viewer showing the full execution timeline.

**REQ-010:** Each trace step displays type, name, inputs, outputs, latency, and status.

**REQ-011:** Trace steps support nesting to represent parent-child execution relationships.

**REQ-012:** Errors within a trace are highlighted with error messages and stack traces visible inline.

### Alerts

17. User configures alert rules per agent: failure rate exceeding a threshold (e.g., > 10% in the last hour) or latency exceeding a threshold (e.g., p95 > 30 seconds)
18. User can also configure alerts for stuck/long-running detection: runs exceeding N times the agent's average duration
19. When a threshold is breached, the system sends an email notification with the agent name, metric, current value, and a link to the dashboard
20. Alert rules are managed in a simple settings page

**REQ-013:** Users can create alert rules per agent with configurable thresholds for failure rate and latency.

**REQ-014:** The system supports stuck-run detection: alerting when a run exceeds a configurable multiple of the agent's average duration.

**REQ-015:** Alert notifications are delivered via email with agent name, triggered metric, current value, and a dashboard link.

**REQ-016:** Alert rules are managed through a settings page in the UI.

## Log Event Schema

Agents POST JSON events to the ingestion endpoint. Each event contains:

```json
{
  "run_id": "uuid",
  "agent_name": "my-agent",
  "step_type": "tool_call | llm_call | decision | error | run_start | run_end",
  "step_name": "search_database",
  "parent_step_id": "uuid | null",
  "input": {},
  "output": {},
  "status": "success | failure | error",
  "error_message": "optional error details",
  "timestamp": "ISO 8601",
  "metadata": {}
}
```

**REQ-017:** The ingestion endpoint validates incoming events against the defined schema and rejects malformed events with descriptive errors.

**REQ-018:** The `metadata` field accepts arbitrary key-value pairs for agent-specific context (version, environment, user/session ID).

## Data Requirements

**REQ-019:** All log events and computed run summaries are persisted in PostgreSQL.

**REQ-020:** The system retains data for at least 30 days. Older data can be purged via a configurable retention policy.

**REQ-021:** Expected volume is low (< 100 runs/day). No specialized time-series or search infrastructure required.

## User Accounts & Access Control

**REQ-022:** No user authentication for MVP. The tool runs on an internal network and is accessible to anyone with the URL.

## Assumptions (Auto-Decided)

These are implementation choices made based on strong recommendations. Override if needed:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Log format | JSON lines via HTTP POST | Universal, no infrastructure dependencies |
| Database | PostgreSQL | Handles structured queries + full-text search via `tsvector` |
| Deployment | Docker Compose | Right-sized for an internal tool with low volume |
| Real-time | Completed runs only | Simpler to build; covers the monitoring use case. Live streaming is a known future enhancement |
| Existing infra | Greenfield — no integrations | No need to interface with external observability platforms |

## Post-MVP Considerations

These came up during discovery but are out of scope for MVP:

- **Cost analytics:** Token usage and estimated cost per run/agent. Feasible if token counts are included in log events.
- **Run comparison:** Side-by-side diff of two runs to identify where execution diverged.
- **Tagging & annotations:** Let team members flag and annotate runs for investigation.
- **Agent health summary:** Aggregate success/failure rates, p50/p95 latency per agent over configurable time windows.
- **Real-time streaming:** Watch agent execution as it happens via WebSocket.
- **Debugging & recommendations:** Auto-detect failure patterns and suggest fixes.

## Existing Tools Reference

From discovery research — notable tools in this space:

- **Langfuse** (MIT, self-hostable) is the closest existing solution. Worth evaluating before building custom, especially if the team's needs align closely with its feature set.
- **OpenLLMetry** could be leveraged for auto-instrumentation on the agent side if the team later wants richer tracing without manual log instrumentation.
- **AgentOps** data model (session-based grouping, success/failure classification) is a good UX pattern to study for the trace viewer.

---

## Requirements Index

| ID | Requirement | Section |
|----|-------------|---------|
| REQ-001 | HTTP POST ingestion endpoint for JSON log events | Agent Onboarding |
| REQ-002 | Auto-discovery of new agents from first log event | Agent Onboarding |
| REQ-003 | Paginated run list with metadata | Run Overview Dashboard |
| REQ-004 | Visual distinction for failed runs | Run Overview Dashboard |
| REQ-005 | Summary statistics (total runs, failure rate, avg duration) | Run Overview Dashboard |
| REQ-006 | Filter by agent name, status, time range | Search & Filtering |
| REQ-007 | Text search across error messages and log content | Search & Filtering |
| REQ-008 | Composable filters + text search | Search & Filtering |
| REQ-009 | Trace viewer with full execution timeline | Trace Viewer |
| REQ-010 | Step detail: type, name, inputs, outputs, latency, status | Trace Viewer |
| REQ-011 | Nested trace steps (parent-child relationships) | Trace Viewer |
| REQ-012 | Inline error highlighting with stack traces | Trace Viewer |
| REQ-013 | Configurable alert rules per agent (failure rate, latency) | Alerts |
| REQ-014 | Stuck-run detection alerts | Alerts |
| REQ-015 | Email alert notifications with context and dashboard link | Alerts |
| REQ-016 | Alert rule management UI | Alerts |
| REQ-017 | Ingestion endpoint schema validation | Log Event Schema |
| REQ-018 | Arbitrary metadata field support | Log Event Schema |
| REQ-019 | PostgreSQL data persistence | Data Requirements |
| REQ-020 | 30-day data retention with configurable purge | Data Requirements |
| REQ-021 | Designed for < 100 runs/day volume | Data Requirements |
| REQ-022 | No authentication (internal network) | Access Control |
