export type RunStatus = 'success' | 'failure' | 'error' | 'running'
export type StepType = 'tool_call' | 'llm_call' | 'decision' | 'error' | 'run_start' | 'run_end'
export type AlertMetric = 'failure_rate' | 'p95_latency' | 'stuck_run'

export interface Run {
  id: string
  agent_name: string
  status: RunStatus
  started_at: string
  ended_at: string | null
  duration_ms: number | null
  step_count: number
  error_message: string | null
  metadata: Record<string, unknown>
}

export interface RunStats {
  total_runs: number
  success_count: number
  failure_count: number
  failure_rate: number
  avg_duration_ms: number
}

export interface TraceEvent {
  id: string
  step_id: string
  parent_step_id: string | null
  step_type: StepType
  step_name: string
  input: Record<string, unknown>
  output: Record<string, unknown>
  status: RunStatus
  error_message: string | null
  timestamp: string
  duration_ms: number | null
  metadata: Record<string, unknown>
  children: TraceEvent[]
}

export interface RunDetail {
  run: Run
  events: TraceEvent[]
}

export interface Agent {
  name: string
  first_seen_at: string
  last_seen_at: string
}

export interface AlertRule {
  id: number
  agent_name: string | null
  metric: AlertMetric
  threshold_value: number
  window_minutes: number
  multiplier: number | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface AlertHistoryEntry {
  id: number
  alert_rule_id: number
  agent_name: string
  metric: AlertMetric
  threshold_value: number
  metric_value: number
  triggered_at: string
  email_sent: boolean
}
