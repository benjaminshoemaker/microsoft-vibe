import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(Text, nullable=False, index=True)
    status = Column(Text, nullable=False, default="running")  # running, success, failure, error
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    step_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    search_vector = Column(Text, nullable=True)  # tsvector populated via trigger/update
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    events = relationship("Event", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_runs_agent_status", "agent_name", "status"),
        Index("idx_runs_started_at", "started_at"),
        Index("idx_runs_alert_eval", "agent_name", "started_at", "status"),
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    parent_step_id = Column(UUID(as_uuid=True), nullable=True)
    agent_name = Column(Text, nullable=False)
    step_type = Column(Text, nullable=False)  # tool_call, llm_call, decision, error, run_start, run_end
    step_name = Column(Text, nullable=True)
    input = Column(JSONB, nullable=False, default=dict)
    output = Column(JSONB, nullable=False, default=dict)
    status = Column(Text, nullable=False)  # success, failure, error
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    search_vector = Column(Text, nullable=True)  # tsvector populated via trigger/update
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    run = relationship("Run", back_populates="events")

    __table_args__ = (
        Index("idx_events_run_id", "run_id", "timestamp"),
    )


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(Text, nullable=True)  # NULL = all agents
    metric = Column(Text, nullable=False)  # failure_rate, p95_latency, stuck_run
    threshold_value = Column(Float, nullable=False)
    window_minutes = Column(Integer, nullable=False, default=60)
    multiplier = Column(Float, nullable=True)  # for stuck_run
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    agent_name = Column(Text, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    metric_value = Column(Float, nullable=False)
    email_sent = Column(Boolean, nullable=False, default=False)
