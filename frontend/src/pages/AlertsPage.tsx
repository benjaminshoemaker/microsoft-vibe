import { useState, useEffect, useCallback } from 'react'
import { AlertRulesList } from '../components/AlertRulesList'
import { AlertRuleForm } from '../components/AlertRuleForm'
import { fetchAlertRules, createAlertRule, updateAlertRule, deleteAlertRule, fetchAlertHistory, fetchAgents } from '../api/client'
import type { AlertRule, AlertMetric, AlertHistoryEntry, Agent } from '../types'
import { Plus, History } from 'lucide-react'
import { formatRelativeTime } from '../lib/utils'
import { StatusBadge } from '../components/StatusBadge'

function AlertHistoryTable({ history }: { history: AlertHistoryEntry[] }) {
  if (history.length === 0) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
        <p className="text-[var(--color-text-muted)]">No alerts triggered yet</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Agent</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Value</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Triggered</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Email</th>
          </tr>
        </thead>
        <tbody>
          {history.map(entry => (
            <tr key={entry.id} className="border-b border-[var(--color-border-subtle)]">
              <td className="px-4 py-3 text-sm font-medium">{entry.agent_name}</td>
              <td className="px-4 py-3 text-sm tabular-nums text-[var(--color-error)]">{entry.metric_value}</td>
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
  const [rules, setRules] = useState<AlertRule[]>([])
  const [history, setHistory] = useState<AlertHistoryEntry[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    try {
      const [rulesData, historyData, agentsData] = await Promise.all([
        fetchAlertRules(),
        fetchAlertHistory(),
        fetchAgents(),
      ])
      setRules(rulesData.rules as unknown as AlertRule[])
      setHistory((historyData.alerts || []) as unknown as AlertHistoryEntry[])
      setAgents(agentsData.agents as unknown as Agent[])
    } catch {
      // Silently handle — rules/history may be empty
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleToggle = async (id: number) => {
    const rule = rules.find(r => r.id === id)
    if (!rule) return
    await updateAlertRule(id, { enabled: !rule.enabled })
    setRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r))
  }

  const handleDelete = async (id: number) => {
    await deleteAlertRule(id)
    setRules(prev => prev.filter(r => r.id !== id))
  }

  const handleCreate = async (rule: { agent_name: string | null; metric: AlertMetric; threshold_value: number; window_minutes: number; multiplier: number | null }) => {
    const created = await createAlertRule(rule) as unknown as AlertRule
    setRules(prev => [...prev, created])
    setShowForm(false)
  }

  if (loading) {
    return <div className="flex items-center justify-center py-20 text-[var(--color-text-muted)]">Loading alerts...</div>
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
          agents={agents}
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
        <AlertHistoryTable history={history} />
      </div>
    </div>
  )
}
