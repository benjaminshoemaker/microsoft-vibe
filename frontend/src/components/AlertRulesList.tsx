import type { AlertRule } from '../types'
import { formatDuration } from '../lib/utils'
import { Trash2 } from 'lucide-react'

function metricLabel(metric: string): string {
  switch (metric) {
    case 'failure_rate': return 'Failure Rate'
    case 'p95_latency': return 'P95 Latency'
    case 'stuck_run': return 'Stuck Run'
    default: return metric
  }
}

function thresholdDisplay(rule: AlertRule): string {
  switch (rule.metric) {
    case 'failure_rate': return `> ${rule.threshold_value}%`
    case 'p95_latency': return `> ${formatDuration(rule.threshold_value)}`
    case 'stuck_run': return `> ${rule.multiplier}x avg duration`
    default: return `> ${rule.threshold_value}`
  }
}

interface AlertRulesListProps {
  rules: AlertRule[]
  onToggle: (id: number) => void
  onDelete: (id: number) => void
}

export function AlertRulesList({ rules, onToggle, onDelete }: AlertRulesListProps) {
  if (rules.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
        <p className="text-[var(--color-text-muted)]">No alert rules configured</p>
        <p className="text-sm text-[var(--color-text-dim)] mt-1">Create a rule to start monitoring agent health</p>
      </div>
    )
  }

  return (
    <div data-testid="alert-rules-list" className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Agent</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Metric</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Threshold</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Window</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Enabled</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider"></th>
          </tr>
        </thead>
        <tbody>
          {rules.map(rule => (
            <tr key={rule.id} className="border-b border-[var(--color-border-subtle)] hover:bg-[var(--color-surface-hover)]">
              <td className="px-4 py-3 text-sm font-medium">
                {rule.agent_name ?? <span className="text-[var(--color-text-dim)] italic">All agents</span>}
              </td>
              <td className="px-4 py-3">
                <span className="rounded bg-[var(--color-bg)] px-2 py-0.5 text-xs font-mono text-[var(--color-text-muted)]">
                  {metricLabel(rule.metric)}
                </span>
              </td>
              <td className="px-4 py-3 text-sm tabular-nums">{thresholdDisplay(rule)}</td>
              <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{rule.window_minutes}m</td>
              <td className="px-4 py-3">
                <button
                  data-testid="rule-toggle"
                  onClick={() => onToggle(rule.id)}
                  className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                    rule.enabled ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border)]'
                  }`}
                >
                  <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${
                    rule.enabled ? 'translate-x-4' : 'translate-x-0'
                  }`} />
                </button>
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  data-testid="rule-delete"
                  onClick={() => onDelete(rule.id)}
                  className="rounded p-1 text-[var(--color-text-dim)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-bg)] transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
