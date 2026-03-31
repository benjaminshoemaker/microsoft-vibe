# Discovery Notes

Generated: 2026-03-30
Source: /discover conversation

## Idea Summary

An internal observability tool that gives teams instant visibility into their AI agents running in production. The core experience: agents emit structured logs, and this tool ingests them to render a dashboard of agent runs with drill-down trace visualization showing the full execution flow — which tools were called, what the LLM decided, latency per step. The goal is "out of the box" — a new agent should get production observability with minimal setup, just by writing structured logs.

This is not a developer debugging tool. It's production monitoring — understanding what deployed agents are doing across the team, spotting failures, and making agent behavior legible at a glance.

## Key Decisions

- **Problem:** No easy way to see what agents are doing in production — need to understand execution flows, tool calls, and agent behavior without stitching together custom logging
- **Audience:** Internal team/org (no multi-tenancy, no public auth complexity)
- **Platform:** Web application (dashboard + trace viewer)
- **Stack preferences:** Agents are Python-based; frontend is open/flexible
- **MVP scope:** Four capabilities — (1) a run overview dashboard listing all agent runs with status/metadata, (2) a trace viewer showing the full execution timeline for a selected run, (3) alerts on agent failures and anomalies (failure rate thresholds, latency spikes, stuck runs), and (4) search/filtering across runs by agent name, status, time range, and error content
- **Integration model:** Log ingestion — agents write structured logs, the tool collects and displays them (no SDK dependency on the agent side)
- **Exciting part:** Both the trace visualization (making execution flows understandable) and the run overview dashboard (at-a-glance view of all agent activity)
- **Alerts:** Threshold-based alerts per agent (failure rate > X%, latency > Y seconds) plus anomaly detection (sudden spikes in failures, runs exceeding normal duration). Notification channel TBD.
- **Search:** Structured filters (agent name, status, time range) as the foundation, with text search across error messages and log content

## Open Questions

- What structured log format will agents emit? JSON lines? OpenTelemetry spans? A custom schema?
- How are logs transported — file tailing, HTTP POST, message queue, or something else?
- What metadata should each agent run include (agent name, version, user/session ID, environment)?
- How much historical data needs to be retained? What's the expected volume of agent runs?
- Should the trace viewer support real-time streaming (watching a running agent) or only completed runs?
- Any existing logging infrastructure to integrate with (ELK, Datadog, etc.)?
- Deployment target for the observability tool itself — Docker, Kubernetes, bare VM?

## Existing Solutions & Tools

### Use Directly

- **Langfuse** (https://github.com/langfuse/langfuse) — MIT-licensed, self-hostable LLM observability platform with trace waterfall views, cost analytics, and dashboards. Covers tracing, cost tracking, and reliability metrics out of the box. The closest existing solution to what's described — could replace building this entirely, or serve as a foundation with custom views layered on top.

- **Arize Phoenix** (https://github.com/Arize-ai/phoenix) — Source-available (Elastic License 2.0) AI observability platform built on OpenTelemetry. Rich agent trace visualization with span-level detail. OTel foundation makes it interoperable with standard observability infrastructure. Fine for internal use despite the license.

### Leverage

- **OpenLLMetry / Traceloop** (https://github.com/traceloop/openllmetry) — Apache 2.0 auto-instrumentation libraries for LLM applications. Drop-in tracing for OpenAI, Anthropic, LangChain, etc. Emits standard OTel spans with token counts, costs, and tool calls. Handles the tedious instrumentation layer so you can focus on the UI.

- **Helicone** (https://github.com/Helicone/helicone) — Apache 2.0 LLM observability proxy. Excels at cost tracking per request with zero code changes (one-line URL swap). Good for the cost/request-logging layer but doesn't understand multi-step agent traces.

- **W&B Weave** (https://github.com/wandb/weave) — Apache 2.0 SDK for tracing and evaluation. Decorator-based Python tracing, evaluation pipelines. Full dashboard requires W&B platform, but the evaluation framework is reusable.

- **Braintrust** (https://github.com/braintrustdata/braintrust-sdk) — MIT SDK for evaluation-as-observability. Scoring functions and experiment tracking for measuring agent reliability over time.

### Take Inspiration From

- **AgentOps** (https://github.com/AgentOps-AI/agentops) — One of the few tools that thinks in "agent sessions" rather than individual LLM calls. Its data model (sessions containing events with aggregate metrics, success/failure classification, session replay) is the right abstraction for agent monitoring.

- **LangSmith** (https://smith.langchain.com) — Proprietary but represents the gold-standard UX for this problem space. Trace waterfall UI, monitoring dashboards with customizable charts, annotation workflows. Defines what "complete" looks like.

## Raw Context

- The emphasis on "out of the box" suggests the team is frustrated with setup friction — they want new agents to get observability for free (or nearly free) just by following a logging convention.
- "Log ingestion" was chosen over SDK/decorator or OpenTelemetry approaches — the user wants the lightest possible touch on the agent side. This means the observability tool needs to be smart about parsing and structuring incoming logs.
- Both core views (run overview + trace viewer) were flagged as equally exciting — neither should be an afterthought. The trace visualization needs to make agent execution genuinely understandable, not just a wall of log lines.
- Internal tool context means we can skip auth, billing, and multi-tenancy — but should still be easy to deploy and maintain.
- Langfuse is a strong "Use Directly" candidate worth evaluating before building from scratch — it's MIT, self-hostable, and covers the core requirements. The decision to build custom vs. deploy Langfuse is a key fork in the road.
