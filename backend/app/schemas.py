import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StepType(str, Enum):
    tool_call = "tool_call"
    llm_call = "llm_call"
    decision = "decision"
    error = "error"
    run_start = "run_start"
    run_end = "run_end"


class EventStatus(str, Enum):
    success = "success"
    failure = "failure"
    error = "error"


class RunStatus(str, Enum):
    running = "running"
    success = "success"
    failure = "failure"
    error = "error"


# --- Ingestion ---

class IngestEvent(BaseModel):
    run_id: uuid.UUID
    agent_name: str
    step_type: StepType
    step_id: uuid.UUID | None = None
    step_name: str | None = None
    parent_step_id: uuid.UUID | None = None
    input: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
    status: EventStatus
    error_message: str | None = None
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)


class IngestBatchRequest(BaseModel):
    events: list[IngestEvent]


class IngestError(BaseModel):
    index: int
    field: str
    message: str


class IngestResponse(BaseModel):
    accepted: int
    errors: list[IngestError] = Field(default_factory=list)


# --- Runs ---

class RunResponse(BaseModel):
    id: uuid.UUID
    agent_name: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int | None
    step_count: int
    error_message: str | None
    metadata: dict

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
    page: int
    page_size: int


class RunStatsResponse(BaseModel):
    total_runs: int
    success_count: int
    failure_count: int
    failure_rate: float
    avg_duration_ms: int
    time_window: dict | None = None


# --- Events / Trace ---

class EventResponse(BaseModel):
    id: uuid.UUID
    step_id: uuid.UUID
    parent_step_id: uuid.UUID | None
    step_type: str
    step_name: str | None
    input: dict
    output: dict
    status: str
    error_message: str | None
    timestamp: datetime
    duration_ms: int | None
    metadata: dict
    children: list["EventResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RunDetailResponse(BaseModel):
    run: RunResponse
    events: list[EventResponse]


# --- Agents ---

class AgentResponse(BaseModel):
    name: str
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


# --- Alerts ---

class AlertMetric(str, Enum):
    failure_rate = "failure_rate"
    p95_latency = "p95_latency"
    stuck_run = "stuck_run"


class AlertRuleCreate(BaseModel):
    agent_name: str | None = None
    metric: AlertMetric
    threshold_value: float = 0
    window_minutes: int = 60
    multiplier: float | None = None


class AlertRuleUpdate(BaseModel):
    agent_name: str | None = None
    metric: AlertMetric | None = None
    threshold_value: float | None = None
    window_minutes: int | None = None
    multiplier: float | None = None
    enabled: bool | None = None


class AlertRuleResponse(BaseModel):
    id: int
    agent_name: str | None
    metric: str
    threshold_value: float
    window_minutes: int
    multiplier: float | None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertHistoryResponse(BaseModel):
    id: int
    alert_rule_id: int
    agent_name: str
    metric: str | None = None
    threshold_value: float | None = None
    metric_value: float
    triggered_at: datetime
    email_sent: bool

    model_config = {"from_attributes": True}
