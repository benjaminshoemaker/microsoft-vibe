#!/usr/bin/env python3
"""Generate demo data for the Agent Observatory dashboard."""

import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta

import httpx

BASE_URL = "http://localhost:8000/api/v1"

AGENTS = ["support-triage", "data-pipeline", "code-reviewer", "doc-generator"]
TOOL_NAMES = ["search_kb", "lookup_user", "send_email", "run_query", "fetch_api", "parse_doc"]
LLM_STEPS = ["classify_intent", "compose_response", "summarize", "extract_entities"]
ERROR_MESSAGES = [
    "Connection timeout to database replica",
    "Anthropic API rate limit exceeded",
    "GitHub API returned 403: rate limit exceeded",
    "Transformation failed: unexpected null in column 'user_id'",
    "SMTP timeout after 5000ms",
]


async def seed_run(client: httpx.AsyncClient, agent_name: str, fail: bool = False) -> str:
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))
    step_count = random.randint(3, 8)

    # run_start
    await client.post(f"{BASE_URL}/ingest", json={
        "run_id": run_id, "agent_name": agent_name, "step_type": "run_start",
        "status": "success", "timestamp": now.isoformat(),
        "metadata": {"version": f"{random.randint(1,3)}.{random.randint(0,9)}.0", "environment": "production"},
    })

    parent_step_id = None
    for i in range(step_count):
        step_id = str(uuid.uuid4())
        elapsed = timedelta(seconds=random.uniform(0.5, 5.0) * (i + 1))
        ts = now + elapsed

        is_llm = random.random() < 0.3
        step_type = "llm_call" if is_llm else "tool_call"
        step_name = random.choice(LLM_STEPS if is_llm else TOOL_NAMES)

        # Nest some steps under a parent
        use_parent = parent_step_id if random.random() < 0.3 else None

        is_error = fail and i == step_count - 1
        await client.post(f"{BASE_URL}/ingest", json={
            "run_id": run_id, "agent_name": agent_name,
            "step_type": "error" if is_error else step_type,
            "step_id": step_id, "step_name": step_name,
            "parent_step_id": use_parent,
            "status": "failure" if is_error else "success",
            "error_message": random.choice(ERROR_MESSAGES) if is_error else None,
            "timestamp": ts.isoformat(),
            "input": {"query": f"sample input {i}"} if not is_error else {},
            "output": {"result": f"output {i}"} if not is_error else {},
        })

        if use_parent is None:
            parent_step_id = step_id

    # run_end
    end_ts = now + timedelta(seconds=random.uniform(10, 120))
    await client.post(f"{BASE_URL}/ingest", json={
        "run_id": run_id, "agent_name": agent_name, "step_type": "run_end",
        "status": "failure" if fail else "success",
        "timestamp": end_ts.isoformat(),
    })

    return run_id


async def seed_alert_rules(client: httpx.AsyncClient) -> None:
    rules = [
        {"agent_name": "support-triage", "metric": "failure_rate", "threshold_value": 10, "window_minutes": 60},
        {"agent_name": "data-pipeline", "metric": "p95_latency", "threshold_value": 120000, "window_minutes": 30},
        {"agent_name": "data-pipeline", "metric": "stuck_run", "multiplier": 3.0, "window_minutes": 60},
    ]
    for rule in rules:
        await client.post(f"{BASE_URL}/alerts/rules", json=rule)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        print("Seeding agent runs...")
        for agent in AGENTS:
            for _ in range(random.randint(4, 8)):
                fail = random.random() < 0.25
                rid = await seed_run(client, agent, fail=fail)
                status = "failure" if fail else "success"
                print(f"  {agent}: {rid[:8]}... ({status})")

        print("\nSeeding alert rules...")
        await seed_alert_rules(client)
        print("  3 alert rules created")

        print("\nDone! Visit http://localhost:8000/docs for API docs")
        print("or http://localhost:5173 for the dashboard")


if __name__ == "__main__":
    asyncio.run(main())
