#!/usr/bin/env python3
"""Generate realistic demo data for the Agent Observatory dashboard.

Each agent has a distinct personality with realistic tool calls,
LLM reasoning steps, and failure modes that tell a coherent story.
"""

import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta

import httpx

BASE_URL = "http://localhost:8000/api/v1"

# ---------------------------------------------------------------------------
# Agent definitions — each has a realistic workflow, tools, and failure modes
# ---------------------------------------------------------------------------

AGENTS = {
    "support-triage": {
        "versions": ["2.4.1", "2.4.2", "2.5.0-beta"],
        "workflows": [
            {  # Happy path: classify → lookup → resolve
                "steps": [
                    ("llm_call", "classify_ticket", {"ticket": "User reports login failure after password reset", "model": "claude-sonnet-4-20250514"}, {"category": "auth", "priority": "high", "sentiment": "frustrated"}),
                    ("tool_call", "query_user_db", {"user_email": "sarah.chen@acme.co", "fields": ["last_login", "password_reset_at", "mfa_status"]}, {"last_login": "2026-03-28T10:00:00Z", "password_reset_at": "2026-03-30T08:15:00Z", "mfa_status": "enabled"}),
                    ("decision", "route_ticket", {"category": "auth", "has_recent_reset": True}, {"action": "assign_to_auth_team", "auto_reply": True}),
                    ("llm_call", "draft_response", {"context": "password reset + login failure", "tone": "empathetic"}, {"response": "Hi Sarah, I can see your password was reset recently. Your MFA settings may need to be re-verified. I've escalated this to our auth team who will reach out within 30 minutes."}),
                    ("tool_call", "send_reply", {"ticket_id": "TKT-4829", "channel": "email"}, {"sent": True, "message_id": "msg-a8f2c"}),
                    ("tool_call", "update_ticket", {"ticket_id": "TKT-4829", "status": "in_progress", "assigned_to": "auth-team"}, {"updated": True}),
                ],
                "fail_at": None,
            },
            {  # Failure: API timeout during user lookup
                "steps": [
                    ("llm_call", "classify_ticket", {"ticket": "Billing discrepancy on invoice #INV-2847", "model": "claude-sonnet-4-20250514"}, {"category": "billing", "priority": "medium", "sentiment": "confused"}),
                    ("tool_call", "query_billing_api", {"invoice_id": "INV-2847", "include_line_items": True}, None),
                ],
                "fail_at": 1,
                "error": "HTTPError: billing-api.internal:8443 — Connection refused (ECONNREFUSED). Service may be down for maintenance.",
            },
            {  # Happy path: escalation flow
                "steps": [
                    ("llm_call", "classify_ticket", {"ticket": "Our team needs SSO configured for the enterprise plan", "model": "claude-sonnet-4-20250514"}, {"category": "enterprise", "priority": "medium", "sentiment": "neutral"}),
                    ("tool_call", "check_account_tier", {"org_id": "org-fintech-42"}, {"tier": "enterprise", "sso_enabled": False, "admin_email": "it-admin@fintech42.com"}),
                    ("decision", "evaluate_escalation", {"requires_manual": True, "category": "enterprise"}, {"action": "escalate_to_solutions_eng", "reason": "SSO config requires manual provisioning"}),
                    ("tool_call", "create_jira_ticket", {"project": "SE", "summary": "SSO setup for fintech42", "priority": "P2"}, {"key": "SE-1847", "url": "https://jira.internal/browse/SE-1847"}),
                    ("tool_call", "send_reply", {"ticket_id": "TKT-4831", "template": "enterprise_escalation"}, {"sent": True}),
                ],
                "fail_at": None,
            },
            {  # Failure: LLM classification confidence too low
                "steps": [
                    ("llm_call", "classify_ticket", {"ticket": "asdf keyboard not working lol", "model": "claude-sonnet-4-20250514"}, {"category": "unknown", "priority": "low", "confidence": 0.23, "sentiment": "unclear"}),
                    ("decision", "check_confidence", {"confidence": 0.23, "threshold": 0.6}, None),
                ],
                "fail_at": 1,
                "error": "ClassificationConfidenceTooLow: Score 0.23 is below threshold 0.6. Cannot auto-route — flagging for human review.",
            },
        ],
    },
    "data-pipeline": {
        "versions": ["1.8.0", "1.8.1", "1.9.0-rc1"],
        "workflows": [
            {  # Happy path: extract → transform → load
                "steps": [
                    ("llm_call", "parse_pipeline_config", {"config_path": "/pipelines/daily_user_sync.yaml", "model": "claude-haiku-4-5-20251001"}, {"source": "postgres-replica-2", "destination": "analytics-warehouse", "tables": ["users", "events", "subscriptions"], "mode": "incremental"}),
                    ("tool_call", "connect_source", {"host": "replica-2.db.internal", "port": 5432, "database": "production"}, {"connected": True, "server_version": "16.2", "latency_ms": 12}),
                    ("tool_call", "extract_users", {"table": "users", "since": "2026-03-29T00:00:00Z", "batch_size": 5000}, {"rows_extracted": 3847, "bytes": 2_150_000, "duration_ms": 4200}),
                    ("tool_call", "extract_events", {"table": "events", "since": "2026-03-29T00:00:00Z", "batch_size": 10000}, {"rows_extracted": 28419, "bytes": 18_700_000, "duration_ms": 12800}),
                    ("tool_call", "transform_and_validate", {"schema_version": "v3", "rules": ["deduplicate", "normalize_emails", "cast_timestamps"]}, {"rows_in": 32266, "rows_out": 31954, "dropped": 312, "validation_errors": 0}),
                    ("tool_call", "load_to_warehouse", {"destination": "analytics.public", "method": "upsert", "conflict_key": "id"}, {"rows_upserted": 31954, "duration_ms": 8400}),
                    ("tool_call", "update_watermark", {"pipeline": "daily_user_sync", "new_watermark": "2026-03-30T00:00:00Z"}, {"previous": "2026-03-29T00:00:00Z", "updated": True}),
                ],
                "fail_at": None,
            },
            {  # Failure: source DB connection timeout
                "steps": [
                    ("llm_call", "parse_pipeline_config", {"config_path": "/pipelines/hourly_metrics.yaml", "model": "claude-haiku-4-5-20251001"}, {"source": "metrics-db.internal", "destination": "analytics-warehouse", "tables": ["page_views", "api_calls"], "mode": "full"}),
                    ("tool_call", "connect_source", {"host": "metrics-db.internal", "port": 5432, "database": "metrics", "timeout_ms": 5000}, None),
                    ("tool_call", "retry_connection", {"host": "metrics-db.internal", "attempt": 2, "backoff_ms": 2000}, None),
                    ("tool_call", "retry_connection", {"host": "metrics-db.internal", "attempt": 3, "backoff_ms": 4000}, None),
                ],
                "fail_at": 1,
                "error": "ConnectionError: ETIMEDOUT after 5000ms connecting to metrics-db.internal:5432. Host unreachable — possible network partition or maintenance window.",
            },
            {  # Failure: schema mismatch during transform
                "steps": [
                    ("llm_call", "parse_pipeline_config", {"config_path": "/pipelines/product_catalog_sync.yaml", "model": "claude-haiku-4-5-20251001"}, {"source": "catalog-api", "destination": "search-index", "mode": "full"}),
                    ("tool_call", "fetch_catalog_api", {"endpoint": "https://catalog-api.internal/v2/products", "page_size": 1000}, {"total_products": 14829, "pages": 15, "fetched_page": 1}),
                    ("tool_call", "transform_and_validate", {"schema_version": "v2", "rules": ["flatten_variants", "extract_pricing"]}, None),
                ],
                "fail_at": 2,
                "error": "SchemaValidationError: Field 'pricing.currency' expected type 'string' but got 'null' in 847 of 14829 records. Source schema may have changed — check catalog-api v2 changelog.",
            },
        ],
    },
    "code-reviewer": {
        "versions": ["0.12.0", "0.12.1", "0.13.0-alpha"],
        "workflows": [
            {  # Happy path: fetch PR → analyze → comment
                "steps": [
                    ("tool_call", "fetch_pull_request", {"repo": "acme/backend-api", "pr_number": 847}, {"title": "Add rate limiting to /api/v2/search", "author": "jpark", "files_changed": 4, "additions": 127, "deletions": 23, "base": "main"}),
                    ("tool_call", "fetch_diff", {"repo": "acme/backend-api", "pr_number": 847, "files": ["src/middleware/rate_limit.py", "src/routes/search.py", "tests/test_rate_limit.py", "config/limits.yaml"]}, {"diff_lines": 150, "hunks": 6}),
                    ("llm_call", "analyze_changes", {"diff_summary": "New rate limiting middleware using sliding window counter in Redis. Applied to search endpoint. Tests cover basic rate limit enforcement.", "model": "claude-sonnet-4-20250514"}, {"risk_level": "medium", "categories": ["security", "performance"], "issues_found": 2, "suggestions": 3}),
                    ("llm_call", "generate_review", {"issues": [{"file": "src/middleware/rate_limit.py", "line": 42, "type": "bug", "message": "Race condition: INCR and EXPIRE are not atomic. Use Redis MULTI/EXEC or a Lua script."}, {"file": "config/limits.yaml", "line": 8, "type": "suggestion", "message": "Consider adding per-user limits in addition to per-IP to prevent abuse from shared IPs."}], "model": "claude-sonnet-4-20250514"}, {"review_body": "Good approach to rate limiting. Two items to address before merge...", "verdict": "changes_requested"}),
                    ("tool_call", "post_review", {"repo": "acme/backend-api", "pr_number": 847, "event": "REQUEST_CHANGES", "comments": 2}, {"review_id": 29481, "posted": True}),
                ],
                "fail_at": None,
            },
            {  # Failure: GitHub API rate limit
                "steps": [
                    ("tool_call", "fetch_pull_request", {"repo": "acme/frontend-app", "pr_number": 1203}, {"title": "Migrate to React 19 Server Components", "author": "amelie", "files_changed": 47, "additions": 2841, "deletions": 1294, "base": "main"}),
                    ("tool_call", "fetch_diff", {"repo": "acme/frontend-app", "pr_number": 1203}, None),
                ],
                "fail_at": 1,
                "error": "GitHubAPIError: 403 Forbidden — API rate limit exceeded. Reset at 2026-03-30T15:00:00Z. Current usage: 5000/5000. Consider using a GitHub App token with higher limits.",
            },
            {  # Happy path: approve clean PR
                "steps": [
                    ("tool_call", "fetch_pull_request", {"repo": "acme/backend-api", "pr_number": 851}, {"title": "Fix typo in error message for /health endpoint", "author": "nwong", "files_changed": 1, "additions": 1, "deletions": 1, "base": "main"}),
                    ("tool_call", "fetch_diff", {"repo": "acme/backend-api", "pr_number": 851, "files": ["src/routes/health.py"]}, {"diff_lines": 4, "hunks": 1}),
                    ("llm_call", "analyze_changes", {"diff_summary": "Single character fix in error message string", "model": "claude-sonnet-4-20250514"}, {"risk_level": "low", "categories": ["docs"], "issues_found": 0, "suggestions": 0}),
                    ("tool_call", "post_review", {"repo": "acme/backend-api", "pr_number": 851, "event": "APPROVE", "comments": 0}, {"review_id": 29483, "posted": True}),
                ],
                "fail_at": None,
            },
        ],
    },
    "doc-generator": {
        "versions": ["1.1.0", "1.1.1", "1.2.0"],
        "workflows": [
            {  # Happy path: scan → generate → publish
                "steps": [
                    ("tool_call", "scan_codebase", {"repo": "acme/backend-api", "branch": "main", "patterns": ["src/**/*.py"]}, {"files_found": 142, "functions": 387, "classes": 64, "undocumented": 23}),
                    ("llm_call", "analyze_api_surface", {"endpoints": 23, "models": 12, "model": "claude-sonnet-4-20250514"}, {"documented": 18, "missing_docs": 5, "outdated_docs": 3}),
                    ("tool_call", "fetch_existing_docs", {"path": "docs/api/", "format": "mdx"}, {"files": 18, "total_size_kb": 245}),
                    ("llm_call", "generate_docs", {"undocumented_endpoints": ["/api/v2/search", "/api/v2/bulk-import", "/api/v2/webhooks/{id}/rotate", "/api/v2/teams/{id}/members", "/api/v2/audit-log"], "model": "claude-sonnet-4-20250514"}, {"generated": 5, "format": "mdx", "total_tokens": 8420}),
                    ("tool_call", "write_docs", {"output_dir": "docs/api/", "files": 5}, {"written": 5, "total_size_kb": 42}),
                    ("tool_call", "create_pull_request", {"repo": "acme/backend-api", "branch": "docs/auto-update-api-ref", "title": "docs: auto-update API reference for 5 endpoints"}, {"pr_number": 853, "url": "https://github.com/acme/backend-api/pull/853"}),
                ],
                "fail_at": None,
            },
            {  # Failure: can't parse complex TypeScript generics
                "steps": [
                    ("tool_call", "scan_codebase", {"repo": "acme/frontend-app", "branch": "main", "patterns": ["src/**/*.tsx", "src/**/*.ts"]}, {"files_found": 284, "components": 89, "hooks": 34, "undocumented": 41}),
                    ("llm_call", "analyze_component_api", {"components": 89, "props_interfaces": 67, "model": "claude-sonnet-4-20250514"}, None),
                ],
                "fail_at": 1,
                "error": "ParseError: Failed to extract prop types from src/components/DataGrid/DataGrid.tsx — nested generic type `Partial<Record<keyof T, ColumnDef<T>>>` exceeds parser depth limit. Consider simplifying the type signature or adding explicit JSDoc annotations.",
            },
        ],
    },
    "incident-responder": {
        "versions": ["0.3.0", "0.3.1"],
        "workflows": [
            {  # Happy path: detect → triage → notify
                "steps": [
                    ("tool_call", "poll_alertmanager", {"endpoint": "https://alertmanager.internal/api/v2/alerts", "filter": "severity=critical"}, {"active_alerts": 1, "alert": {"name": "HighErrorRate", "service": "checkout-api", "value": "12.4%", "threshold": "5%"}}),
                    ("tool_call", "fetch_grafana_snapshot", {"dashboard": "service-health", "panel": "error-rate", "service": "checkout-api", "range": "1h"}, {"snapshot_url": "https://grafana.internal/d/svc-health/snapshot?t=1711838916", "current_error_rate": 12.4, "p95_latency_ms": 890}),
                    ("llm_call", "assess_severity", {"error_rate": 12.4, "threshold": 5.0, "affected_service": "checkout-api", "latency_spike": True, "model": "claude-sonnet-4-20250514"}, {"severity": "SEV-2", "impact": "Payment flow degraded — ~12% of checkout attempts failing", "likely_cause": "upstream payment gateway latency", "recommended_actions": ["page oncall", "check payment gateway status page", "prepare rollback if gateway issue persists"]}),
                    ("tool_call", "check_status_pages", {"services": ["stripe", "adyen"]}, {"stripe": {"status": "operational"}, "adyen": {"status": "degraded", "message": "Increased latency on EU payment processing"}}),
                    ("decision", "determine_response", {"root_cause": "upstream", "provider": "adyen", "severity": "SEV-2"}, {"action": "activate_failover", "notify": ["oncall-payments", "eng-leads"], "create_incident": True}),
                    ("tool_call", "create_incident", {"title": "SEV-2: Checkout errors due to Adyen EU degradation", "channel": "#incident-2026-0330", "severity": "SEV-2"}, {"incident_id": "INC-482", "slack_channel": "#incident-2026-0330"}),
                    ("tool_call", "page_oncall", {"team": "payments", "message": "SEV-2: Adyen EU degraded → checkout error rate 12.4%. Failover recommended. See #incident-2026-0330"}, {"paged": True, "responder": "alex.rivera"}),
                ],
                "fail_at": None,
            },
            {  # Failure: can't reach alertmanager
                "steps": [
                    ("tool_call", "poll_alertmanager", {"endpoint": "https://alertmanager.internal/api/v2/alerts", "filter": "severity=critical"}, None),
                ],
                "fail_at": 0,
                "error": "ConnectionError: Failed to connect to alertmanager.internal:443 — TLS handshake timeout after 10s. Certificate may have expired (last renewal: 2026-02-28).",
            },
        ],
    },
    "onboarding-assistant": {
        "versions": ["1.0.0", "1.0.1"],
        "workflows": [
            {  # Happy path: new user setup
                "steps": [
                    ("tool_call", "lookup_user", {"user_id": "usr_8f2a1b", "include": ["profile", "org", "permissions"]}, {"name": "Jordan Lee", "email": "jordan@startup.io", "org": "Startup.io", "role": "developer", "created_at": "2026-03-30T09:00:00Z"}),
                    ("llm_call", "personalize_onboarding", {"role": "developer", "org_size": "small", "industry": "saas", "model": "claude-haiku-4-5-20251001"}, {"track": "developer_quickstart", "steps": ["install_cli", "create_first_project", "deploy_preview", "invite_team"], "estimated_minutes": 15}),
                    ("tool_call", "provision_resources", {"user_id": "usr_8f2a1b", "track": "developer_quickstart"}, {"api_key": "ak_live_...redacted", "project_id": "proj_default", "preview_url": "https://preview-usr8f2a1b.app.internal"}),
                    ("tool_call", "send_welcome_email", {"user_id": "usr_8f2a1b", "template": "developer_welcome", "variables": {"name": "Jordan", "quickstart_url": "https://docs.internal/quickstart"}}, {"sent": True, "message_id": "msg-w82f1"}),
                    ("tool_call", "track_event", {"event": "onboarding_started", "user_id": "usr_8f2a1b", "properties": {"track": "developer_quickstart"}}, {"tracked": True}),
                ],
                "fail_at": None,
            },
        ],
    },
}


def _jitter(base_seconds: float, variance: float = 0.3) -> float:
    """Add realistic timing jitter."""
    return base_seconds * (1 + random.uniform(-variance, variance))


async def seed_run(client: httpx.AsyncClient, agent_name: str, workflow: dict, version: str, hours_ago: float) -> str:
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    fail_at = workflow.get("fail_at")
    steps = workflow["steps"]

    await client.post(f"{BASE_URL}/ingest", json={
        "run_id": run_id, "agent_name": agent_name, "step_type": "run_start",
        "status": "success", "timestamp": now.isoformat(),
        "metadata": {"version": version, "environment": random.choice(["production", "production", "staging"])},
    })

    elapsed = 0.0
    parent_step_id = None
    last_step_id = None

    for i, (step_type, step_name, input_data, output_data) in enumerate(steps):
        step_id = str(uuid.uuid4())
        is_failure = (fail_at is not None and i >= fail_at)

        # Realistic timing: LLM calls take 1-4s, tool calls 0.2-2s, decisions <0.1s
        if step_type == "llm_call":
            elapsed += _jitter(2.5)
        elif step_type == "tool_call":
            elapsed += _jitter(0.8)
        else:
            elapsed += _jitter(0.05)

        ts = now + timedelta(seconds=elapsed)

        # Nest second-level steps under the first top-level step
        use_parent = None
        if i > 0 and last_step_id and random.random() < 0.25:
            use_parent = parent_step_id

        actual_output = {} if is_failure else (output_data or {})
        actual_status = "failure" if is_failure else "success"
        actual_type = "error" if is_failure else step_type
        error_msg = workflow.get("error") if is_failure else None

        await client.post(f"{BASE_URL}/ingest", json={
            "run_id": run_id, "agent_name": agent_name,
            "step_type": actual_type, "step_id": step_id,
            "step_name": step_name, "parent_step_id": use_parent,
            "status": actual_status, "error_message": error_msg,
            "timestamp": ts.isoformat(),
            "input": input_data or {}, "output": actual_output,
        })

        if use_parent is None:
            parent_step_id = step_id
        last_step_id = step_id

        if is_failure:
            break

    # run_end
    end_ts = now + timedelta(seconds=elapsed + _jitter(0.5))
    final_status = "failure" if fail_at is not None else "success"
    await client.post(f"{BASE_URL}/ingest", json={
        "run_id": run_id, "agent_name": agent_name, "step_type": "run_end",
        "status": final_status, "timestamp": end_ts.isoformat(),
    })

    return run_id


async def seed_alert_rules(client: httpx.AsyncClient) -> None:
    rules = [
        {"agent_name": "support-triage", "metric": "failure_rate", "threshold_value": 15, "window_minutes": 60},
        {"agent_name": "data-pipeline", "metric": "failure_rate", "threshold_value": 10, "window_minutes": 60},
        {"agent_name": "data-pipeline", "metric": "p95_latency", "threshold_value": 120000, "window_minutes": 30},
        {"agent_name": "code-reviewer", "metric": "stuck_run", "multiplier": 3.0, "window_minutes": 60},
        {"agent_name": "incident-responder", "metric": "failure_rate", "threshold_value": 5, "window_minutes": 30},
        {"agent_name": None, "metric": "failure_rate", "threshold_value": 25, "window_minutes": 60},
    ]
    for rule in rules:
        await client.post(f"{BASE_URL}/alerts/rules", json=rule)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        print("Seeding realistic agent runs...\n")

        total_runs = 0
        for agent_name, config in AGENTS.items():
            versions = config["versions"]
            workflows = config["workflows"]

            # Generate runs spread over the last 72 hours
            num_runs = random.randint(8, 16) if agent_name in ("support-triage", "data-pipeline") else random.randint(4, 8)

            for i in range(num_runs):
                workflow = random.choice(workflows)
                version = random.choice(versions)
                hours_ago = random.uniform(0.5, 72)

                rid = await seed_run(client, agent_name, workflow, version, hours_ago)
                status = "FAIL" if workflow.get("fail_at") is not None else "OK"
                steps = len(workflow["steps"]) if status == "OK" else workflow["fail_at"] + 1
                print(f"  {agent_name:<24} {status:<5} {steps} steps  v{version}  ({hours_ago:.1f}h ago)  {rid[:8]}...")
                total_runs += 1

        print(f"\n  Total: {total_runs} runs across {len(AGENTS)} agents")

        print("\nSeeding alert rules...")
        await seed_alert_rules(client)
        print("  6 alert rules created")

        print("\nDone! Visit http://localhost:5173 for the dashboard")


if __name__ == "__main__":
    asyncio.run(main())
