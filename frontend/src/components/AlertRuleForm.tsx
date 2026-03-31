import { useState } from 'react'
import type { Agent, AlertMetric } from '../types'
import { X } from 'lucide-react'

interface AlertRuleFormProps {
  agents: Agent[]
  onSubmit: (rule: { agent_name: string | null; metric: AlertMetric; threshold_value: number; window_minutes: number; multiplier: number | null }) => void
  onCancel: () => void
}

export function AlertRuleForm({ agents, onSubmit, onCancel }: AlertRuleFormProps) {
  const [agentName, setAgentName] = useState<string>('')
  const [metric, setMetric] = useState<AlertMetric>('failure_rate')
  const [threshold, setThreshold] = useState<string>('10')
  const [window, setWindow] = useState<string>('60')
  const [multiplier, setMultiplier] = useState<string>('3')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      agent_name: agentName || null,
      metric,
      threshold_value: metric === 'stuck_run' ? 0 : Number(threshold),
      window_minutes: Number(window),
      multiplier: metric === 'stuck_run' ? Number(multiplier) : null,
    })
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">New Alert Rule</h3>
        <button onClick={onCancel} className="rounded p-1 hover:bg-[var(--color-surface-hover)] text-[var(--color-text-dim)]">
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="rule-agent" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Agent</label>
            <select
              id="rule-agent"
              value={agentName}
              onChange={e => setAgentName(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
            >
              <option value="">All agents</option>
              {agents.map(a => (
                <option key={a.name} value={a.name}>{a.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="rule-metric" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Metric</label>
            <select
              id="rule-metric"
              value={metric}
              onChange={e => setMetric(e.target.value as AlertMetric)}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
            >
              <option value="failure_rate">Failure Rate (%)</option>
              <option value="p95_latency">P95 Latency (ms)</option>
              <option value="stuck_run">Stuck Run Detection</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {metric === 'stuck_run' ? (
            <div>
              <label htmlFor="rule-multiplier" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Multiplier (x avg duration)</label>
              <input
                id="rule-multiplier"
                type="number"
                value={multiplier}
                onChange={e => setMultiplier(e.target.value)}
                min="1"
                step="0.5"
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
              />
            </div>
          ) : (
            <div>
              <label htmlFor="rule-threshold" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
                Threshold {metric === 'failure_rate' ? '(%)' : '(ms)'}
              </label>
              <input
                id="rule-threshold"
                type="number"
                value={threshold}
                onChange={e => setThreshold(e.target.value)}
                min="0"
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]"
              />
            </div>
          )}

          <div>
            <label htmlFor="rule-window" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Window (minutes)</label>
            <input
              id="rule-window"
              type="number"
              value={window}
              onChange={e => setWindow(e.target.value)}
              min="1"
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)]"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="rounded-md bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)]"
          >
            Create Rule
          </button>
        </div>
      </form>
    </div>
  )
}
