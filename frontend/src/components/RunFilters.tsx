import { Search } from 'lucide-react'
import type { Agent } from '../types'

interface RunFiltersProps {
  agents: Agent[]
  selectedAgent: string
  selectedStatus: string
  searchQuery: string
  onAgentChange: (agent: string) => void
  onStatusChange: (status: string) => void
  onSearchChange: (query: string) => void
}

const statusOptions: { value: string; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'success', label: 'Success' },
  { value: 'failure', label: 'Failure' },
  { value: 'error', label: 'Error' },
  { value: 'running', label: 'Running' },
]

export function RunFilters({
  agents,
  selectedAgent,
  selectedStatus,
  searchQuery,
  onAgentChange,
  onStatusChange,
  onSearchChange,
}: RunFiltersProps) {
  return (
    <div data-testid="run-filters" className="flex items-center gap-3">
      <select
        data-testid="agent-filter"
        value={selectedAgent}
        onChange={e => onAgentChange(e.target.value)}
        className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)]"
      >
        <option value="">All agents</option>
        {agents.map(a => (
          <option key={a.name} value={a.name}>{a.name}</option>
        ))}
      </select>

      <select
        value={selectedStatus}
        onChange={e => onStatusChange(e.target.value)}
        className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] outline-none focus:border-[var(--color-primary)]"
      >
        {statusOptions.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-dim)]" />
        <input
          data-testid="search-input"
          type="text"
          value={searchQuery}
          onChange={e => onSearchChange(e.target.value)}
          placeholder="Search errors, logs..."
          className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] py-2 pl-9 pr-3 text-sm text-[var(--color-text)] outline-none placeholder:text-[var(--color-text-dim)] focus:border-[var(--color-primary)]"
        />
      </div>
    </div>
  )
}
