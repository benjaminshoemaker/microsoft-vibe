import { useState, useMemo } from 'react'
import { StatsBar } from '../components/StatsBar'
import { RunsTable } from '../components/RunsTable'
import { RunFilters } from '../components/RunFilters'
import { mockRuns, mockStats, mockAgents } from '../data/mock'
import type { RunStatus } from '../types'

export function DashboardPage() {
  const [selectedAgent, setSelectedAgent] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const filteredRuns = useMemo(() => {
    return mockRuns.filter(run => {
      if (selectedAgent && run.agent_name !== selectedAgent) return false
      if (selectedStatus && run.status !== selectedStatus as RunStatus) return false
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        const matchesAgent = run.agent_name.toLowerCase().includes(q)
        const matchesError = run.error_message?.toLowerCase().includes(q)
        const matchesMeta = JSON.stringify(run.metadata).toLowerCase().includes(q)
        if (!matchesAgent && !matchesError && !matchesMeta) return false
      }
      return true
    })
  }, [selectedAgent, selectedStatus, searchQuery])

  const filteredStats = useMemo(() => {
    if (!selectedAgent && !selectedStatus && !searchQuery) return mockStats
    const runs = filteredRuns.filter(r => r.duration_ms != null)
    const failures = filteredRuns.filter(r => r.status === 'failure' || r.status === 'error')
    return {
      total_runs: filteredRuns.length,
      success_count: filteredRuns.filter(r => r.status === 'success').length,
      failure_count: failures.length,
      failure_rate: filteredRuns.length > 0 ? Math.round((failures.length / filteredRuns.length) * 1000) / 10 : 0,
      avg_duration_ms: runs.length > 0
        ? Math.round(runs.reduce((sum, r) => sum + r.duration_ms!, 0) / runs.length)
        : 0,
    }
  }, [filteredRuns, selectedAgent, selectedStatus, searchQuery])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Agent Runs</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Monitor your agents in production</p>
        </div>
      </div>

      <StatsBar stats={filteredStats} />

      <RunFilters
        agents={mockAgents}
        selectedAgent={selectedAgent}
        selectedStatus={selectedStatus}
        searchQuery={searchQuery}
        onAgentChange={setSelectedAgent}
        onStatusChange={setSelectedStatus}
        onSearchChange={setSearchQuery}
      />

      <RunsTable runs={filteredRuns} />
    </div>
  )
}
