import { useState, useEffect, useCallback } from 'react'
import { StatsBar } from '../components/StatsBar'
import { RunsTable } from '../components/RunsTable'
import { RunFilters } from '../components/RunFilters'
import { fetchRuns, fetchRunStats, fetchAgents } from '../api/client'
import type { Run, RunStats, Agent } from '../types'

export function DashboardPage() {
  const [selectedAgent, setSelectedAgent] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [runs, setRuns] = useState<Run[]>([])
  const [stats, setStats] = useState<RunStats>({ total_runs: 0, success_count: 0, failure_count: 0, failure_rate: 0, avg_duration_ms: 0 })
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    try {
      setError(null)
      const filters = {
        agent_name: selectedAgent || undefined,
        status: selectedStatus || undefined,
        search: searchQuery || undefined,
      }
      const [runsData, statsData, agentsData] = await Promise.all([
        fetchRuns(filters),
        fetchRunStats(filters),
        fetchAgents(),
      ])
      setRuns(runsData.runs as unknown as Run[])
      setStats(statsData as unknown as RunStats)
      setAgents(agentsData.agents as unknown as Agent[])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [selectedAgent, selectedStatus, searchQuery])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [loadData])

  if (loading && runs.length === 0) {
    return (
      <div data-testid="loading" className="flex items-center justify-center py-20">
        <div className="text-[var(--color-text-muted)]">Loading dashboard...</div>
      </div>
    )
  }

  if (error && runs.length === 0) {
    return (
      <div data-testid="error-state" className="flex flex-col items-center justify-center py-20">
        <p className="text-[var(--color-error)]">{error}</p>
        <button onClick={loadData} className="mt-3 text-sm text-[var(--color-primary)] hover:underline">
          Retry
        </button>
      </div>
    )
  }

  if (!loading && runs.length === 0 && !selectedAgent && !selectedStatus && !searchQuery) {
    return (
      <div data-testid="empty-state" className="flex flex-col items-center justify-center py-20">
        <p className="text-lg text-[var(--color-text-muted)]">No agent runs yet</p>
        <p className="text-sm text-[var(--color-text-dim)] mt-2 max-w-md text-center">
          Start sending events to <code className="bg-[var(--color-surface)] px-1.5 py-0.5 rounded text-xs">POST /api/v1/ingest</code> and they'll appear here automatically.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Agent Runs</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Monitor your agents in production</p>
        </div>
      </div>

      <StatsBar stats={stats} />

      <RunFilters
        agents={agents}
        selectedAgent={selectedAgent}
        selectedStatus={selectedStatus}
        searchQuery={searchQuery}
        onAgentChange={setSelectedAgent}
        onStatusChange={setSelectedStatus}
        onSearchChange={setSearchQuery}
      />

      <RunsTable runs={runs} />
    </div>
  )
}
