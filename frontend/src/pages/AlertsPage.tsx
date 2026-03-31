import { useState } from 'react'
import { AlertRulesList } from '../components/AlertRulesList'
import { AlertRuleForm } from '../components/AlertRuleForm'
import { mockAlertRules, mockAgents, mockAlertHistory } from '../data/mock'
import type { AlertRule, AlertMetric, AlertHistoryEntry } from '../types'
import { Plus, History } from 'lucide-react'
import { formatRelativeTime } from '../lib/utils'
import { StatusBadge } from '../components/StatusBadge'

function AlertHistoryTable({ history }: { history: AlertHistoryEntry[] }) {
  if (history.length === 0) return null

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Agent</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Metric</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Value</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Threshold</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Triggered</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Email</th>
          </tr>
        </thead>
        <tbody>
          {history.map(entry => (
            <tr key={entry.id} className="border-b border-[var(--color-border-subtle)]">
              <td className="px-4 py-3 text-sm font-medium">{entry.agent_name}</td>
              <td className="px-4 py-3">
                <span className="rounded bg-[var(--color-bg)] px-2 py-0.5 text-xs font-mono text-[var(--color-text-muted)]">
                  {entry.metric}
                </span>
              </td>
              <td className="px-4 py-3 text-sm tabular-nums text-[var(--color-error)]">
                {entry.metric === 'failure_rate' ? `${entry.metric_value}%` : `${entry.metric_value}ms`}
              </td>
              <td className="px-4 py-3 text-sm tabular-nums text-[var(--color-text-muted)]">
                {entry.metric === 'failure_rate' ? `${entry.threshold_value}%` : `${entry.threshold_value}ms`}
              </td>
              <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{formatRelativeTime(entry.triggered_at)}</td>
              <td className="px-4 py-3">
                <StatusBadge status={entry.email_sent ? 'success' : 'failure'} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>(mockAlertRules)
  const [showForm, setShowForm] = useState(false)

  const handleToggle = (id: number) => {
    setRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r))
  }

  const handleDelete = (id: number) => {
    setRules(prev => prev.filter(r => r.id !== id))
  }

  const handleCreate = (rule: { agent_name: string | null; metric: AlertMetric; threshold_value: number; window_minutes: number; multiplier: number | null }) => {
    const newRule: AlertRule = {
      id: Math.max(...rules.map(r => r.id), 0) + 1,
      ...rule,
      enabled: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setRules(prev => [...prev, newRule])
    setShowForm(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Alert Rules</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Configure thresholds for agent monitoring</p>
        </div>
        <button
          data-testid="create-rule-btn"
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 rounded-md bg-[var(--color-primary)] px-3 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-hover)] transition-colors"
        >
          <Plus className="h-4 w-4" />
          Create Rule
        </button>
      </div>

      {showForm && (
        <AlertRuleForm
          agents={mockAgents}
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      <AlertRulesList
        rules={rules}
        onToggle={handleToggle}
        onDelete={handleDelete}
      />

      <div>
        <div className="flex items-center gap-2 mb-3">
          <History className="h-4 w-4 text-[var(--color-text-dim)]" />
          <h2 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Recent Alerts</h2>
        </div>
        <AlertHistoryTable history={mockAlertHistory} />
      </div>
    </div>
  )
}
